# -*- coding: utf-8 -*-
"""
空间数据检查核心模块
从现有脚本迁移的检查逻辑
"""

import os
import re
import geopandas as gpd
import pandas as pd
from datetime import datetime


def _detect_dbf_encoding(shp_path):
    """
    通过读取 DBF 文件的 LDID (Language Driver ID) 检测编码

    LDID 位于 DBF 文件头部的第 29 字节:
    - 0x64 (100): GBK/CP936 (简体中文)
    - 0x65 (101): Big5 (繁体中文)
    - 0x78 (120): UTF-8
    - 0x00: 未指定/ANSI (需启发式检测)

    Args:
        shp_path: SHP 文件路径

    Returns:
        str: 'gb18030', 'utf-8', 或 None (无法确定时)
    """
    dbf_path = shp_path.replace('.shp', '.dbf')
    if not os.path.exists(dbf_path):
        return None

    try:
        with open(dbf_path, 'rb') as f:
            f.seek(29)  # LDID 在 DBF 文件第 29 字节
            ldid_byte = f.read(1)
            if not ldid_byte:
                return None
            ldid = ord(ldid_byte)

            # LDID 解析
            if ldid == 0x64:  # 100 = GBK/CP936 (简体中文)
                return 'gb18030'  # gb18030 兼容 gbk
            elif ldid == 0x78:  # 120 = UTF-8
                return 'utf-8'
            elif ldid == 0x00:  # 未指定，可能是 UTF-8 或 ANSI
                return None  # 需要启发式检测
            else:
                return None
    except Exception:
        return None


class WaterSystemChecker:
    def __init__(self, folder_path, water_system_shp):
        self.folder_path = folder_path
        self.water_system_shp = water_system_shp

        self.water_codes = set()
        self.water_names = set()
        self.water_code_to_name = {}
        self.water_data = []
        self.water_records = []
        self.water_original_columns = []

        self.results = []
        self.all_records = []
        self.start_time = None
        self.end_time = None
        self.progress_callback = None

    def emit_progress(self, msg):
        if self.progress_callback:
            self.progress_callback(msg)

    def load_water_system(self):
        self.emit_progress("加载水系数据...")

        if not os.path.exists(self.water_system_shp):
            self.emit_progress(f"❌ 水系文件不存在：{self.water_system_shp}")
            return False

        try:
            gdf = None
            used_encoding = None

            # 步骤1: 先通过 LDID 检测编码
            detected_encoding = _detect_dbf_encoding(self.water_system_shp)

            if detected_encoding:
                self.emit_progress(f"检测到 DBF 编码: {detected_encoding} (来自 LDID)")
                try:
                    gdf = gpd.read_file(self.water_system_shp, encoding=detected_encoding)
                    gdf.columns = [str(col) for col in gdf.columns]
                    used_encoding = detected_encoding
                    self.emit_progress(f"✓ 使用 LDID 检测的编码: {used_encoding}")
                except Exception as e:
                    self.emit_progress(f"  LDID 检测的编码读取失败: {str(e)[:50]}，尝试启发式检测...")
                    gdf = None
                    used_encoding = None

            # 步骤2: 如果 LDID 检测失败或无法确定，使用启发式检测
            if gdf is None:
                # 尝试所有常见编码，选择能读取最多有效数据的编码
                encodings_to_try = ['utf-8', 'gb18030', 'gbk', 'cp936', 'gb2312', 'latin1']

                self.emit_progress("使用启发式方法检测编码...")

                best_encoding = None
                best_non_none_count = -1
                best_gdf = None
                rvnm_col_name = None

                for encoding in encodings_to_try:
                    try:
                        test_gdf = gpd.read_file(self.water_system_shp, encoding=encoding)
                        test_gdf.columns = [str(col) for col in test_gdf.columns]

                        # 查找 RVNM 字段
                        rvnm_col = None
                        for col in test_gdf.columns:
                            if col.lower() in ['rvnm', 'rvname', '河流名称']:
                                rvnm_col = col
                                break

                        if rvnm_col:
                            non_none_count = test_gdf[rvnm_col].notna().sum()
                            self.emit_progress(f"  编码 {encoding}: RVNM 非空记录数 = {non_none_count}")

                            # 选择非空数最多的编码
                            if non_none_count > best_non_none_count:
                                best_non_none_count = non_none_count
                                best_encoding = encoding
                                best_gdf = test_gdf
                                rvnm_col_name = rvnm_col
                        else:
                            self.emit_progress(f"  编码 {encoding}: 未找到 RVNM 字段")
                    except Exception as e:
                        self.emit_progress(f"  编码 {encoding} 读取失败: {str(e)[:50]}")

                # 使用最佳编码的结果
                if best_gdf is not None and best_non_none_count >= 0:
                    gdf = best_gdf
                    used_encoding = best_encoding
                    self.emit_progress(f"✓ 启发式检测使用编码: {used_encoding} (RVNM 非空数: {best_non_none_count})")
                else:
                    # 兜底：不指定编码
                    self.emit_progress("  使用默认编码...")
                    gdf = gpd.read_file(self.water_system_shp)
                    gdf.columns = [str(col) for col in gdf.columns]
                    used_encoding = 'default'

            self.emit_progress(f"水系记录数：{len(gdf)}")

            original_water_columns = [str(col) for col in gdf.columns]
            self.water_original_columns = original_water_columns

            # 查找 RVCD 和 RVNM 字段

            rvcd_field = None
            rvnm_field = None
            # 河流代码可能的字段名
            rvcd_candidates = ['rvcd', 'rvcd_', '河流代码', '河流编码']
            # 河流名称可能的字段名
            rvnm_candidates = ['rvnm', 'rvname', 'ravnme', 'rvnavb', '河流名称', '河流名']
            for col in gdf.columns:
                col_lower = col.lower()
                if col_lower in rvcd_candidates and rvcd_field is None:
                    rvcd_field = col
                if col_lower in rvnm_candidates and rvnm_field is None:
                    rvnm_field = col

            self.emit_progress(f"匹配到的河流代码字段: {rvcd_field}")
            self.emit_progress(f"匹配到的河流名称字段: {rvnm_field}")

            if not rvcd_field or not rvnm_field:
                self.emit_progress("❌ 水系文件缺少必要字段 rvcd/rvnm")
                return False

            # 检查 RVNM 字段是否全为空
            rvnm_empty_count = gdf[rvnm_field].isna().sum()
            if rvnm_empty_count == len(gdf):
                self.emit_progress(f"⚠️ 警告: 水系文件中 [{rvnm_field}] 字段全为空，将无法进行河流名称匹配校验！")
                self.emit_progress("⚠️ 请检查水系数据是否完整，或使用其他包含河流名称的数据源")

            rvcd_count = {}
            for idx, row in gdf.iterrows():
                # 直接访问字段值
                rvcd_val = row[rvcd_field]
                rvnm_val = row[rvnm_field]

                # 使用 pd.isna() 正确检测 NaN 值
                if pd.isna(rvcd_val):
                    rvcd = ''
                else:
                    rvcd = str(rvcd_val).strip()

                if pd.isna(rvnm_val):
                    rvnm = ''
                else:
                    rvnm = str(rvnm_val).strip()

                record = row[original_water_columns].to_dict()
                record['河流代码'] = rvcd
                record['河流名称'] = rvnm
                record['记录序号'] = idx
                record['河流代码长度'] = len(rvcd) if rvcd else 0
                record['河流代码是否为17位'] = '是' if len(rvcd) == 17 else '否'
                record['验证状态'] = '通过'
                record['错误信息'] = ''

                error_msgs = []

                if not rvcd:
                    error_msgs.append('河流代码为空')
                elif len(rvcd) != 17:
                    error_msgs.append(f'河流代码[{rvcd}]长度{len(rvcd)}位(应为17位)')
                    record['验证状态'] = '不通过'

                if rvcd:
                    if rvcd not in rvcd_count:
                        rvcd_count[rvcd] = []
                    rvcd_count[rvcd].append(idx)

                # 检查河流名称是否有效
                if rvnm:
                    self.water_names.add(rvnm.upper())

                record['错误信息'] = '; '.join(error_msgs) if error_msgs else ''
                self.water_records.append(record)

            duplicate_rvcd = {k: v for k, v in rvcd_count.items() if len(v) > 1}
            if duplicate_rvcd:
                for rvcd, indices in duplicate_rvcd.items():
                    for rec in self.water_records:
                        if rec['河流代码'] == rvcd:
                            rec['验证状态'] = '不通过'
                            existing_error = rec['错误信息']
                            new_error = f'河流代码[{rvcd}]重复出现{len(indices)}次(出现在记录{indices})'
                            rec['错误信息'] = f'{existing_error}; {new_error}' if existing_error else new_error

            for rvcd in rvcd_count.keys():
                self.water_codes.add(rvcd.upper())

            for rec in self.water_records:
                code = rec.get('河流代码', '')
                name = rec.get('河流名称', '')
                # 只有当代码和名称都有效时才存入映射
                if code and name:
                    self.water_code_to_name[code.upper()] = name

            invalid_code_count = sum(1 for r in self.water_records if r['河流代码是否为17位'] == '否')
            duplicate_count = len(duplicate_rvcd)

            self.emit_progress(f"河流代码数量：{len(self.water_codes)}")
            self.emit_progress(f"河流名称数量：{len(self.water_names)}")
            self.emit_progress(f"河流代码不为17位数量：{invalid_code_count}")
            self.emit_progress(f"河流代码重复数量：{duplicate_count}")

            self.water_data = [{'河流代码': r['河流代码'], '河流名称': r['河流名称']} for r in self.water_records]

            return True

        except Exception as e:
            self.emit_progress(f"❌ 加载水系文件失败：{str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def find_shp_file_in_folder(self, folder, filename):
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file == filename:
                    return os.path.join(root, file)
        return None

    def find_shp_files_by_keyword(self, folder, keyword):
        """查找包含关键词的所有shp文件，支持模糊匹配"""
        results = []
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith('.shp') and keyword in file:
                    results.append(os.path.join(root, file))
        return results

    def find_folders_with_shp(self, root_folder):
        """递归查找所有包含目标shp文件的文件夹

        Args:
            root_folder: 根目录路径

        Returns:
            list: 包含目标shp文件的文件夹路径列表
        """
        # 目标文件列表
        target_files = ['断面平面位置L.shp', '防治对象分布P.shp']
        target_keywords = ['隐患要素分布', '隐患要素分布L']

        folders_with_shp = set()

        self.emit_progress(f"递归搜索目录: {root_folder}")

        for root, dirs, files in os.walk(root_folder):
            # 检查是否有目标shp文件
            for f in files:
                if f in target_files:
                    folders_with_shp.add(root)
                    self.emit_progress(f"  发现目标文件夹: {root} (包含 {f})")
                elif f.endswith('.shp') and any(kw in f for kw in target_keywords):
                    folders_with_shp.add(root)
                    self.emit_progress(f"  发现目标文件夹: {root} (包含 {f})")

        return list(folders_with_shp)

    def validate_duanmian(self, row):
        """断面平面位置L.shp 校验规则"""
        error_msgs = []
        rvcd_val = row.get('河流代码')
        rvnm_val = row.get('河流名称')
        bh_val = row.get('编号')
        mc_val = row.get('名称')
        rvcd = str(rvcd_val).strip() if rvcd_val is not None else ''
        rvnm = str(rvnm_val).strip() if rvnm_val is not None else ''
        bh = str(bh_val).strip() if bh_val is not None else ''
        mc = str(mc_val).strip() if mc_val is not None else ''

        code_len_valid = '是' if len(rvcd) == 17 else '否'
        code_in_water = '是' if rvcd.upper() in self.water_codes else '否'

        water_name = self.water_code_to_name.get(rvcd.upper(), '')
        name_match_water = '是' if water_name and rvnm.upper() == water_name.upper() else '否'
        name_in_water = '是' if rvnm.upper() in self.water_names else '否'

        bh_len_valid = '是' if len(bh) == 23 else '否'
        bh_code_match = '是' if len(bh) >= 17 and bh[:17].upper() == rvcd.upper() else '否'
        bh_name_match = '是' if len(bh) >= 23 and len(mc) >= 5 and bh[-5:] == mc[-5:] else '否'

        cs_pattern = re.match(r'^(.*)(CS\d{3})$', mc.upper())
        if cs_pattern:
            extracted_rvnm = cs_pattern.group(1).strip()
            cs_part = cs_pattern.group(2)
            cs_format_valid = '是'
            if extracted_rvnm:
                dm_name_match_rvnm = '是' if rvnm.upper() == extracted_rvnm.upper() else '否'
            else:
                dm_name_match_rvnm = '否'
                error_msgs.append(f'断面名称[{mc}]中CS前提取的河流名称为空')
        else:
            cs_format_valid = '否'
            cs_part = ''
            extracted_rvnm = ''
            dm_name_match_rvnm = '否'
            error_msgs.append(f'断面名称[{mc}]不符合河流名称+CS+3位数字格式')

        if code_len_valid == '否':
            error_msgs.append(f'河流代码长度{len(rvcd)}位(应为17位)')

        if rvcd:
            if code_in_water == '否':
                error_msgs.append(f'河流代码[{rvcd}]不在水系中')
                if rvnm:
                    error_msgs.append(f'河流名称[{rvnm}]不在水系中')
            else:
                if name_match_water == '否':
                    if not water_name:
                        error_msgs.append(f'河流代码[{rvcd}]在水系中对应的河流名称为空')
                    else:
                        error_msgs.append(f'河流名称[{rvnm}]与水系中河流代码[{rvcd}]对应的名称[{water_name}]不一致')
                elif name_in_water == '否' and rvnm:
                    error_msgs.append(f'河流名称[{rvnm}]不在水系中')

        if bh_len_valid == '否':
            error_msgs.append(f'编号长度{len(bh)}位(应为23位)')
        if bh_code_match == '否' and len(bh) >= 17:
            error_msgs.append(f'编号前17位与河流代码不一致')
        if bh_name_match == '否' and len(bh) >= 23 and len(mc) >= 5:
            error_msgs.append(f'编号后5位与名称后5位不一致')
        if cs_format_valid == '否':
            error_msgs.append(f'断面名称[{mc}]不符合河流名称+CS+3位数字格式')
        if dm_name_match_rvnm == '否' and cs_format_valid == '是' and extracted_rvnm:
            error_msgs.append(f'断面名称[{mc}]中CS前河流名称[{extracted_rvnm}]与河流名称[{rvnm}]不一致')

        is_valid = all([code_len_valid == '是', code_in_water == '是', name_match_water == '是',
                        bh_len_valid == '是', bh_code_match == '是', bh_name_match == '是',
                        cs_format_valid == '是', dm_name_match_rvnm == '是'])

        return {
            '河流代码': rvcd,
            '河流名称': rvnm,
            '编号': bh,
            '名称': mc,
            '河流代码长度17位': code_len_valid,
            '河流代码在水系中': code_in_water,
            '河流名称与水系一致': name_match_water,
            '编号长度23位': bh_len_valid,
            '编号前17位=河流代码': bh_code_match,
            '编号后5位=名称后5位': bh_name_match,
            '断面名称CS格式': cs_format_valid,
            'CS后河流名称': extracted_rvnm,
            '断面名称与河流名称一致': dm_name_match_rvnm,
            '验证状态': '通过' if is_valid else '不通过',
            '错误信息': '; '.join(error_msgs)
        }, is_valid

    def validate_fangzhi(self, row):
        """防治对象分布P.shp 校验规则"""
        error_msgs = []
        rvcd_val = row.get('河流代码')
        rvnm_val = row.get('河流名称')
        rvcd = str(rvcd_val).strip() if rvcd_val is not None else ''
        rvnm = str(rvnm_val).strip() if rvnm_val is not None else ''

        code_len_valid = '是' if len(rvcd) == 17 else '否'
        code_in_water = '是' if rvcd.upper() in self.water_codes else '否'

        water_name = self.water_code_to_name.get(rvcd.upper(), '')
        name_match_water = '是' if water_name and rvnm.upper() == water_name.upper() else '否'
        name_in_water = '是' if rvnm.upper() in self.water_names else '否'

        if code_len_valid == '否':
            error_msgs.append(f'河流代码长度{len(rvcd)}位(应为17位)')

        if rvcd:
            if code_in_water == '否':
                error_msgs.append(f'河流代码[{rvcd}]不在水系中')
                if rvnm:
                    error_msgs.append(f'河流名称[{rvnm}]不在水系中')
            else:
                if name_match_water == '否':
                    if not water_name:
                        error_msgs.append(f'河流代码[{rvcd}]在水系中对应的河流名称为空')
                    else:
                        error_msgs.append(f'河流名称[{rvnm}]与水系中河流代码[{rvcd}]对应的名称[{water_name}]不一致')
                elif name_in_water == '否' and rvnm:
                    error_msgs.append(f'河流名称[{rvnm}]不在水系中')

        is_valid = all([code_len_valid == '是', code_in_water == '是', name_match_water == '是'])

        return {
            '河流代码': rvcd,
            '河流名称': rvnm,
            '河流代码长度17位': code_len_valid,
            '河流代码在水系中': code_in_water,
            '河流名称与水系一致': name_match_water,
            '验证状态': '通过' if is_valid else '不通过',
            '错误信息': '; '.join(error_msgs)
        }, is_valid

    def validate_yinhuan(self, row):
        """隐患要素分布L.shp 校验规则"""
        error_msgs = []
        rvcd_val = row.get('河流代码')
        rvnm_val = row.get('河流名称')
        bh_val = row.get('编号')
        rvcd = str(rvcd_val).strip() if rvcd_val is not None else ''
        rvnm = str(rvnm_val).strip() if rvnm_val is not None else ''
        bh = str(bh_val).strip() if bh_val is not None else ''

        code_len_valid = '是' if len(rvcd) == 17 else '否'
        code_in_water = '是' if rvcd.upper() in self.water_codes else '否'

        water_name = self.water_code_to_name.get(rvcd.upper(), '')
        name_match_water = '是' if water_name and rvnm.upper() == water_name.upper() else '否'
        name_in_water = '是' if rvnm.upper() in self.water_names else '否'

        bh_len_valid = '是' if len(bh) == 28 else '否'
        bh_district_valid = '是' if len(bh) >= 6 and bh[:6].isdigit() else '否'
        bh_code_match = '是' if len(bh) >= 23 and bh[6:23].upper() == rvcd.upper() else '否'

        if code_len_valid == '否':
            error_msgs.append(f'河流代码长度{len(rvcd)}位(应为17位)')

        if rvcd:
            if code_in_water == '否':
                error_msgs.append(f'河流代码[{rvcd}]不在水系中')
                if rvnm:
                    error_msgs.append(f'河流名称[{rvnm}]不在水系中')
            else:
                if name_match_water == '否':
                    if not water_name:
                        error_msgs.append(f'河流代码[{rvcd}]在水系中对应的河流名称为空')
                    else:
                        error_msgs.append(f'河流名称[{rvnm}]与水系中河流代码[{rvcd}]对应的名称[{water_name}]不一致')
                elif name_in_water == '否' and rvnm:
                    error_msgs.append(f'河流名称[{rvnm}]不在水系中')

        if bh_len_valid == '否':
            error_msgs.append(f'编号长度{len(bh)}位(应为28位)')
        if bh_district_valid == '否' and len(bh) >= 6:
            error_msgs.append(f'编号开头6位[{bh[:6]}]非数字')
        if bh_code_match == '否' and len(bh) >= 23:
            error_msgs.append(f'编号7-23位与河流代码不一致')

        is_valid = all([code_len_valid == '是', code_in_water == '是', name_match_water == '是',
                        bh_len_valid == '是', bh_district_valid == '是', bh_code_match == '是'])

        return {
            '河流代码': rvcd,
            '河流名称': rvnm,
            '编号': bh,
            '河流代码长度17位': code_len_valid,
            '河流代码在水系中': code_in_water,
            '河流名称与水系一致': name_match_water,
            '编号长度28位': bh_len_valid,
            '编号开头6位为数字': bh_district_valid,
            '编号7-23位=河流代码': bh_code_match,
            '验证状态': '通过' if is_valid else '不通过',
            '错误信息': '; '.join(error_msgs)
        }, is_valid

    def process_single_shp(self, shp_path, shp_name, validate_func, required_fields):
        result = {
            'file_name': shp_name,
            'file_path': shp_path,
            'folder_name': '',
            'total_records': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'duplicate_records': 0,
            'status': '成功',
            'errors': [],
            'original_columns': []
        }

        try:
            gdf = None
            used_encoding = None

            # 步骤1: 先通过 LDID 检测编码
            detected_encoding = _detect_dbf_encoding(shp_path)
            if detected_encoding:
                try:
                    gdf = gpd.read_file(shp_path, encoding=detected_encoding)
                    gdf.columns = [str(col) for col in gdf.columns]
                    used_encoding = detected_encoding
                except Exception:
                    gdf = None

            # 步骤2: 如果 LDID 检测失败，使用启发式检测
            if gdf is None:
                encodings_to_try = ['utf-8', 'gb18030', 'gbk', 'gb2312', 'cp936', 'latin1', 'iso-8859-1']
                for encoding in encodings_to_try:
                    try:
                        gdf = gpd.read_file(shp_path, encoding=encoding)
                        gdf.columns = [str(col) for col in gdf.columns]
                        used_encoding = encoding
                        break
                    except:
                        continue

            if gdf is None:
                gdf = gpd.read_file(shp_path)
                used_encoding = 'default'

            result['total_records'] = len(gdf)

            original_columns = [str(col) for col in gdf.columns]
            result['original_columns'] = original_columns

            missing_fields = [f for f in required_fields if f not in gdf.columns]
            if missing_fields:
                result['status'] = '字段缺失'
                result['errors'].append(f"缺少字段：{missing_fields}")
                for idx, row in gdf.iterrows():
                    record = row[original_columns].to_dict()
                    record['源文件'] = shp_path
                    record['验证状态'] = '字段缺失'
                    record['错误信息'] = f"缺少字段：{missing_fields}"
                    self.all_records.append(record)
                return result

            file_records = []
            for idx, row in gdf.iterrows():
                check_result, is_valid = validate_func(row)
                record = row[original_columns].to_dict()
                record['_original_columns'] = original_columns
                for key in check_result:
                    if key not in record:
                        record[key] = check_result[key]
                record['源文件'] = shp_path
                record['记录序号'] = idx

                file_records.append(record)
                self.all_records.append(record)

                if is_valid:
                    result['valid_records'] += 1
                else:
                    result['invalid_records'] += 1

            uniqueness_field = None
            if '断面平面位置' in shp_name:
                uniqueness_field = '编号'
            elif '防治对象分布' in shp_name:
                uniqueness_field = '代码'
            elif '隐患要素分布' in shp_name:
                uniqueness_field = '编号'

            result['duplicate_records'] = 0
            if uniqueness_field:
                field_count = {}
                for rec in file_records:
                    field_val = rec.get(uniqueness_field, '')
                    if field_val:
                        if field_val not in field_count:
                            field_count[field_val] = []
                        field_count[field_val].append(rec['记录序号'])

                duplicate_fields = {k: v for k, v in field_count.items() if len(v) > 1}
                if duplicate_fields:
                    duplicate_count = sum(len(indices) - 1 for indices in duplicate_fields.values())
                    result['duplicate_records'] = len(duplicate_fields)
                    result['invalid_records'] += duplicate_count
                    for field_val, indices in duplicate_fields.items():
                        dup_error = f'{uniqueness_field}[{field_val}]重复出现{len(indices)}次(出现在记录{indices})'
                        for rec in file_records:
                            if str(rec.get(uniqueness_field, '')) == str(field_val):
                                existing_error = rec.get('错误信息', '') or ''
                                if dup_error not in existing_error:
                                    rec['错误信息'] = f'{existing_error}; {dup_error}' if existing_error else dup_error
                                rec['验证状态'] = '不通过'
                        for all_rec in self.all_records:
                            if str(all_rec.get(uniqueness_field, '')) == str(field_val) and all_rec.get('源文件', '') == shp_path:
                                existing_error = all_rec.get('错误信息', '') or ''
                                if dup_error not in existing_error:
                                    all_rec['错误信息'] = f'{existing_error}; {dup_error}' if existing_error else dup_error
                                all_rec['验证状态'] = '不通过'
                    result['status'] = '存在错误'

            result['status'] = '通过' if result['invalid_records'] == 0 else '存在错误'
            return result

        except Exception as e:
            result['status'] = '读取失败'
            result['errors'].append(str(e))
            return result

    def process_all(self):
        self.start_time = datetime.now()

        self.emit_progress("=" * 60)
        self.emit_progress("开始检查...")
        self.emit_progress("=" * 60)

        if not self.load_water_system():
            self.emit_progress("❌ 水系数据加载失败，程序退出")
            return []

        self.emit_progress("开始检查各图层...")

        layer_configs = [
            ('断面平面位置L.shp', self.validate_duanmian, ['河流代码', '河流名称', '编号', '名称'], False),
            ('防治对象分布P.shp', self.validate_fangzhi, ['河流代码', '河流名称'], False),
            ('隐患要素分布', self.validate_yinhuan, ['河流代码', '河流名称', '编号'], True)
        ]

        # 查找待检查的文件夹列表 - 使用递归搜索
        folders_to_check = []
        if os.path.exists(self.folder_path):
            # 递归搜索所有包含目标shp文件的文件夹
            folders_to_check = self.find_folders_with_shp(self.folder_path)

            if folders_to_check:
                self.emit_progress(f"发现 {len(folders_to_check)} 个包含图层文件的文件夹")
            else:
                self.emit_progress(f"⚠ 在目录树中未发现任何包含目标图层文件的文件夹")
                self.emit_progress(f"  目标文件: 断面平面位置L.shp, 防治对象分布P.shp, 隐患要素分布*.shp")

        for folder in folders_to_check:
            folder_name = os.path.basename(folder) if folder != self.folder_path else "(当前文件夹)"
            self.emit_progress(f"处理文件夹：{folder_name}")

            for filename, validate_func, required_fields, use_keyword in layer_configs:
                if use_keyword:
                    shp_paths = self.find_shp_files_by_keyword(folder, filename)
                    if not shp_paths:
                        self.emit_progress(f"检查：{filename}* (模糊匹配)")
                        self.emit_progress(f"⚠ 未找到包含 '{filename}' 的图层")
                        result = {
                            'file_name': f'{filename}* (模糊匹配)',
                            'file_path': '',
                            'folder_name': folder_name,
                            'total_records': 0,
                            'valid_records': 0,
                            'invalid_records': 0,
                            'duplicate_records': 0,
                            'status': '文件未找到',
                            'errors': ['文件未找到']
                        }
                        self.results.append(result)
                    else:
                        for shp_path in shp_paths:
                            actual_filename = os.path.basename(shp_path)
                            self.emit_progress(f"检查：{actual_filename} (匹配关键词 '{filename}')")
                            self.emit_progress(f"文件路径：{shp_path}")
                            result = self.process_single_shp(shp_path, actual_filename, validate_func, required_fields)
                            result['folder_name'] = folder_name

                            if result['status'] == '通过':
                                self.emit_progress(f"✅ 状态：通过 | 记录：{result['total_records']} | 有效：{result['valid_records']}")
                            else:
                                self.emit_progress(f"❌ 状态：{result['status']} | 记录：{result['total_records']} | "
                                                  f"有效：{result['valid_records']} | 无效：{result['invalid_records']}")

                            self.results.append(result)
                else:
                    self.emit_progress(f"检查：{filename}")

                    shp_path = self.find_shp_file_in_folder(folder, filename)

                    if not shp_path:
                        self.emit_progress(f"⚠ 文件未找到")
                        result = {
                            'file_name': filename,
                            'file_path': '',
                            'folder_name': folder_name,
                            'total_records': 0,
                            'valid_records': 0,
                            'invalid_records': 0,
                            'duplicate_records': 0,
                            'status': '文件未找到',
                            'errors': ['文件未找到']
                        }
                    else:
                        self.emit_progress(f"文件路径：{shp_path}")
                        result = self.process_single_shp(shp_path, filename, validate_func, required_fields)
                        result['folder_name'] = folder_name

                        if result['status'] == '通过':
                            self.emit_progress(f"✅ 状态：通过 | 记录：{result['total_records']} | 有效：{result['valid_records']}")
                        else:
                            self.emit_progress(f"❌ 状态：{result['status']} | 记录：{result['total_records']} | "
                                              f"有效：{result['valid_records']} | 无效：{result['invalid_records']}")

                    self.results.append(result)

        self.end_time = datetime.now()

        used_codes = {}
        for record in self.all_records:
            code_val = record.get('河流代码')
            code = str(code_val).strip().upper() if code_val is not None else ''
            if code:
                if code not in used_codes:
                    used_codes[code] = set()
                used_codes[code].add(record.get('源文件', ''))

        for water_rec in self.water_records:
            code_val = water_rec.get('河流代码')
            code = str(code_val).strip().upper() if code_val is not None else ''
            if code in used_codes:
                used_files = used_codes[code]
                water_rec['被使用图层数'] = len(used_files)
                water_rec['被使用图层'] = '; '.join([os.path.basename(f) for f in used_files])
            else:
                water_rec['被使用图层数'] = 0
                water_rec['被使用图层'] = '未被使用'

        self.emit_progress("检查完成")

        return self.results