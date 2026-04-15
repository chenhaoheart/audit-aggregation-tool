# -*- coding: utf-8 -*-
"""
附表与空间数据对比校验模块
实现附表数据与shp图层属性表的双向匹配检查
"""

import os
import geopandas as gpd
import pandas as pd
from typing import Dict, List, Tuple, Optional
from openpyxl import load_workbook
from difflib import SequenceMatcher


def fuzzy_match(s1: str, s2: str) -> float:
    """模糊匹配相似度"""
    # 去除数字前缀如 "5.名称" -> "名称"
    def clean(s):
        import re
        return re.sub(r'^\d+[\.\、\s]*', '', s).strip()
    return SequenceMatcher(None, clean(s1), clean(s2)).ratio()


class DataValidator:
    """附表与空间数据对比校验器"""

    # 默认字段映射配置 - 新格式：{shp字段: 附表字段}
    DEFAULT_FIELD_MAPPING = {
        'fubiao1_vs_fangzhi': {
            # shp字段 -> 附表字段
            'match_fields': {
                '名称': '5.名称',
                '代码': '6.代码'
            },
            'detail_fields': {
                '类型': '7.类型',
                '人口': '8.人口',
                '河流名称': '9.河流名称',
                '河流代码': '10.河流代码'
            }
        },
        'fubiao2_vs_yinhuan': {
            'match_fields': {
                '名称': '名称',
                '编号': '编码'
            },
            'detail_fields': {
                '类型': '类型',
                '河流名称': '河流名称',
                '河流代码': '河流代码'
            }
        },
        'fubiao3_vs_yinhuan': {
            'match_fields': {
                '名称': '名称',
                '编号': '编码'
            },
            'detail_fields': {
                '类型': '类型',
                '河流名称': '河流名称',
                '河流代码': '河流代码'
            }
        }
    }

    def __init__(self):
        self.fubiao_data = {}  # 附表数据
        self.shp_data = {}  # 空间数据
        self.validation_results = {}  # 校验结果
        self.progress_callback = None
        self.field_mapping = self.DEFAULT_FIELD_MAPPING.copy()  # 字段映射

    def set_field_mapping(self, mapping: dict):
        """设置字段映射"""
        self.field_mapping = mapping

    def get_field_mapping(self) -> dict:
        """获取当前字段映射"""
        return self.field_mapping

    @staticmethod
    def auto_match_fields(fubiao_fields: list, shp_fields: list, threshold: float = 0.6) -> dict:
        """
        自动模糊匹配字段

        Args:
            fubiao_fields: 附表字段列表
            shp_fields: shp字段列表
            threshold: 相似度阈值

        Returns:
            映射字典 {附表字段: shp字段}
        """
        mapping = {}
        used_shp = set()

        # 常见映射规则
        common_mappings = {
            '名称': '名称',
            '代码': '代码',
            '编码': '编号',
            '编号': '编号',
            '类型': '类型',
            '人口': '人口',
            '河流名称': '河流名称',
            '河流代码': '河流代码',
            '经度': '经度',
            '纬度': '纬度'
        }

        for fb_field in fubiao_fields:
            # 跳过内部字段
            if fb_field.startswith('_'):
                continue

            # 清理字段名（去除数字前缀）
            import re
            clean_fb = re.sub(r'^\d+[\.\、\s]*', '', fb_field).strip()

            matched = None

            # 1. 先尝试常见映射
            if clean_fb in common_mappings:
                target = common_mappings[clean_fb]
                if target in shp_fields and target not in used_shp:
                    matched = target

            # 2. 再尝试精确匹配
            if not matched:
                for shp_field in shp_fields:
                    if shp_field in used_shp:
                        continue
                    if shp_field == clean_fb or shp_field == fb_field:
                        matched = shp_field
                        break

            # 3. 最后尝试模糊匹配
            if not matched:
                best_match = None
                best_score = threshold
                for shp_field in shp_fields:
                    if shp_field in used_shp:
                        continue
                    score = fuzzy_match(clean_fb, shp_field)
                    if score > best_score:
                        best_score = score
                        best_match = shp_field

                if best_match:
                    matched = best_match

            if matched:
                mapping[fb_field] = matched
                used_shp.add(matched)

        return mapping

    def emit_progress(self, msg):
        """发送进度消息"""
        if self.progress_callback:
            self.progress_callback(msg)

    def load_fubiao(self, report_data: dict):
        """
        加载附表数据

        Args:
            report_data: load_all_reports() 返回的数据结构
        """
        self.fubiao_data = {
            'fubiao1': report_data.get('fubiao1', {}).get('records', []),
            'fubiao2': report_data.get('fubiao2', {}).get('records', []),
            'fubiao3': report_data.get('fubiao3', {}).get('records', [])
        }
        self.emit_progress(f"附表1记录数: {len(self.fubiao_data['fubiao1'])}")
        self.emit_progress(f"附表2记录数: {len(self.fubiao_data['fubiao2'])}")
        self.emit_progress(f"附表3记录数: {len(self.fubiao_data['fubiao3'])}")

    def get_fubiao_fields(self, table: str) -> list:
        """获取附表字段列表"""
        records = self.fubiao_data.get(table, [])
        if records:
            return [k for k in records[0].keys() if not k.startswith('_')]
        return []

    def get_shp_fields(self, shp_type: str) -> list:
        """获取shp字段列表"""
        records = self.shp_data.get(shp_type, [])
        if records:
            return [k for k in records[0].keys() if not k.startswith('_')]
        return []

    def _read_shp_with_encoding(self, shp_path: str) -> Optional[gpd.GeoDataFrame]:
        """尝试多种编码读取shp文件"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'cp936', 'latin1']

        for encoding in encodings:
            try:
                gdf = gpd.read_file(shp_path, encoding=encoding)
                gdf.columns = [str(col) for col in gdf.columns]
                return gdf
            except Exception:
                continue

        try:
            gdf = gpd.read_file(shp_path)
            gdf.columns = [str(col) for col in gdf.columns]
            return gdf
        except Exception:
            return None

    def load_shp_data(self, folder_path: str) -> bool:
        """
        加载空间数据（防治对象P.shp、隐患要素L.shp）

        Args:
            folder_path: 包含多个子文件夹的根目录

        Returns:
            是否成功加载
        """
        if not folder_path or not os.path.exists(folder_path):
            self.emit_progress("空间数据文件夹不存在")
            return False

        self.shp_data = {
            'fangzhi': [],  # 防治对象分布P.shp
            'yinhuan': []   # 隐患要素分布L.shp
        }

        # 遍历子文件夹
        subfolders = []
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                subfolders.append(item_path)

        self.emit_progress(f"发现 {len(subfolders)} 个子文件夹")

        for subfolder in subfolders:
            subfolder_name = os.path.basename(subfolder)

            # 查找防治对象分布P.shp
            for root, dirs, files in os.walk(subfolder):
                for file in files:
                    if file == '防治对象分布P.shp':
                        shp_path = os.path.join(root, file)
                        self.emit_progress(f"加载: {subfolder_name}/{file}")
                        gdf = self._read_shp_with_encoding(shp_path)
                        if gdf is not None:
                            for idx, row in gdf.iterrows():
                                record = row.to_dict()
                                record['_source_folder'] = subfolder_name
                                record['_source_file'] = shp_path
                                self.shp_data['fangzhi'].append(record)
                            self.emit_progress(f"  记录数: {len(gdf)}")
                        else:
                            self.emit_progress(f"  读取失败")

                    elif file == '隐患要素分布L.shp':
                        shp_path = os.path.join(root, file)
                        self.emit_progress(f"加载: {subfolder_name}/{file}")
                        gdf = self._read_shp_with_encoding(shp_path)
                        if gdf is not None:
                            for idx, row in gdf.iterrows():
                                record = row.to_dict()
                                record['_source_folder'] = subfolder_name
                                record['_source_file'] = shp_path
                                self.shp_data['yinhuan'].append(record)
                            self.emit_progress(f"  记录数: {len(gdf)}")
                        else:
                            self.emit_progress(f"  读取失败")

        self.emit_progress(f"防治对象分布P.shp 总记录数: {len(self.shp_data['fangzhi'])}")
        self.emit_progress(f"隐患要素分布L.shp 总记录数: {len(self.shp_data['yinhuan'])}")

        return True

    def validate_fubiao1_vs_fangzhi(self) -> dict:
        """
        附表1 ↔ 防治对象分布P.shp 双向匹配
        使用字段映射配置进行匹配
        映射格式：{shp字段: 附表字段}
        """
        result = {
            'matched': [],
            'fubiao_only': [],
            'shp_only': [],
            'match_count': 0,
            'fubiao_only_count': 0,
            'shp_only_count': 0
        }

        fubiao_records = self.fubiao_data.get('fubiao1', [])
        shp_records = self.shp_data.get('fangzhi', [])

        self.emit_progress("开始附表1与防治对象分布P.shp对比...")

        # 获取映射配置 - 新格式：{shp字段: 附表字段}
        mapping = self.field_mapping.get('fubiao1_vs_fangzhi', {})
        match_fields = mapping.get('match_fields', {'名称': '5.名称', '代码': '6.代码'})

        # 获取匹配字段 - keys是shp字段，values是附表字段
        shp_match_fields = list(match_fields.keys())
        fubiao_match_fields = list(match_fields.values())

        self.emit_progress(f"匹配字段: shp[{', '.join(shp_match_fields)}] <-> 附表[{', '.join(fubiao_match_fields)}]")

        # 构建shp索引
        shp_index = {}
        for rec in shp_records:
            key_parts = []
            for shp_field in shp_match_fields:
                val = str(rec.get(shp_field, '')).strip().upper()
                key_parts.append(val)
            key = '|'.join(key_parts)
            if key not in shp_index:
                shp_index[key] = []
            shp_index[key].append(rec)

        # 构建附表索引
        fubiao_index = {}
        for rec in fubiao_records:
            key_parts = []
            for fb_field in fubiao_match_fields:
                val = str(rec.get(fb_field, '')).strip().upper()
                key_parts.append(val)
            key = '|'.join(key_parts)
            if key not in fubiao_index:
                fubiao_index[key] = []
            fubiao_index[key].append(rec)

        # 匹配
        for key, recs in fubiao_index.items():
            if key in shp_index:
                for rec in recs:
                    result['matched'].append({
                        'type': 'fubiao1',
                        'fubiao_record': rec,
                        'shp_records': shp_index[key]
                    })
            else:
                for rec in recs:
                    result['fubiao_only'].append(rec)

        for key, recs in shp_index.items():
            if key not in fubiao_index:
                for rec in recs:
                    result['shp_only'].append(rec)

        result['match_count'] = len(result['matched'])
        result['fubiao_only_count'] = len(result['fubiao_only'])
        result['shp_only_count'] = len(result['shp_only'])

        self.emit_progress(f"匹配成功: {result['match_count']} 条")
        self.emit_progress(f"仅附表有: {result['fubiao_only_count']} 条")
        self.emit_progress(f"仅shp有: {result['shp_only_count']} 条")

        return result

    def validate_fubiao23_vs_yinhuan(self) -> dict:
        """
        附表2/3 ↔ 隐患要素分布L.shp 双向匹配
        分别使用附表2和附表3的映射配置进行匹配
        映射格式：{shp字段: 附表字段}
        """
        result = {
            'fubiao2_matched': [],
            'fubiao2_only': [],
            'fubiao3_matched': [],
            'fubiao3_only': [],
            'shp_only': [],
            'fubiao2_match_count': 0,
            'fubiao2_only_count': 0,
            'fubiao3_match_count': 0,
            'fubiao3_only_count': 0,
            'shp_only_count': 0
        }

        fubiao2_records = self.fubiao_data.get('fubiao2', [])
        fubiao3_records = self.fubiao_data.get('fubiao3', [])
        shp_records = self.shp_data.get('yinhuan', [])

        self.emit_progress("开始附表2/3与隐患要素分布L.shp对比...")

        # 获取附表2映射配置
        mapping2 = self.field_mapping.get('fubiao2_vs_yinhuan', {})
        match_fields2 = mapping2.get('match_fields', {'名称': '名称', '编号': '编码'})

        # 获取附表3映射配置
        mapping3 = self.field_mapping.get('fubiao3_vs_yinhuan', {})
        match_fields3 = mapping3.get('match_fields', {'名称': '名称', '编号': '编码'})

        # 构建shp索引
        shp_index = {}
        shp_matched_keys = set()  # 记录已被附表匹配的shp记录
        for rec in shp_records:
            # 使用附表2的匹配字段构建索引
            key_parts = []
            for shp_field in match_fields2.keys():
                val = str(rec.get(shp_field, '')).strip().upper()
                key_parts.append(val)
            key = '|'.join(key_parts)
            if key not in shp_index:
                shp_index[key] = []
            shp_index[key].append(rec)

        # 附表2匹配
        if fubiao2_records and match_fields2:
            shp_match_fields2 = list(match_fields2.keys())
            fubiao_match_fields2 = list(match_fields2.values())
            self.emit_progress(f"附表2匹配字段: shp[{', '.join(shp_match_fields2)}] <-> 附表[{', '.join(fubiao_match_fields2)}]")

            for rec in fubiao2_records:
                key_parts = []
                for fb_field in fubiao_match_fields2:
                    val = self._get_field_value(rec, fb_field)
                    key_parts.append(val)
                key = '|'.join(key_parts)

                if key in shp_index:
                    result['fubiao2_matched'].append({
                        'type': '附表2',
                        'fubiao_record': rec,
                        'shp_records': shp_index[key]
                    })
                    shp_matched_keys.add(key)
                else:
                    result['fubiao2_only'].append(rec)

        # 附表3匹配
        if fubiao3_records and match_fields3:
            shp_match_fields3 = list(match_fields3.keys())
            fubiao_match_fields3 = list(match_fields3.values())
            self.emit_progress(f"附表3匹配字段: shp[{', '.join(shp_match_fields3)}] <-> 附表[{', '.join(fubiao_match_fields3)}]")

            for rec in fubiao3_records:
                key_parts = []
                for fb_field in fubiao_match_fields3:
                    val = self._get_field_value(rec, fb_field)
                    key_parts.append(val)
                key = '|'.join(key_parts)

                if key in shp_index:
                    result['fubiao3_matched'].append({
                        'type': '附表3',
                        'fubiao_record': rec,
                        'shp_records': shp_index[key]
                    })
                    shp_matched_keys.add(key)
                else:
                    result['fubiao3_only'].append(rec)

        # 找出未被任何附表匹配的shp记录
        for key in shp_index.keys():
            if key not in shp_matched_keys:
                for rec in shp_index[key]:
                    result['shp_only'].append(rec)

        result['fubiao2_match_count'] = len(result['fubiao2_matched'])
        result['fubiao2_only_count'] = len(result['fubiao2_only'])
        result['fubiao3_match_count'] = len(result['fubiao3_matched'])
        result['fubiao3_only_count'] = len(result['fubiao3_only'])
        result['shp_only_count'] = len(result['shp_only'])

        self.emit_progress(f"附表2匹配成功: {result['fubiao2_match_count']} 条, 仅附表2有: {result['fubiao2_only_count']} 条")
        self.emit_progress(f"附表3匹配成功: {result['fubiao3_match_count']} 条, 仅附表3有: {result['fubiao3_only_count']} 条")
        self.emit_progress(f"仅shp有: {result['shp_only_count']} 条")

        return result

    def _get_field_value(self, rec, field_name):
        """获取记录中字段的值，支持模糊匹配"""
        if field_name in rec:
            return str(rec.get(field_name, '')).strip().upper()
        # 尝试模糊匹配
        for k in rec.keys():
            if field_name in k or k in field_name:
                return str(rec.get(k, '')).strip().upper()
        return ''

    def validate_all(self) -> dict:
        """执行全部校验"""
        self.emit_progress("=" * 50)
        self.emit_progress("开始附表与空间数据对比校验...")
        self.emit_progress("=" * 50)

        self.validation_results = {
            'fubiao1_vs_fangzhi': self.validate_fubiao1_vs_fangzhi(),
            'fubiao23_vs_yinhuan': self.validate_fubiao23_vs_yinhuan()
        }

        self.emit_progress("=" * 50)
        self.emit_progress("校验完成")
        self.emit_progress("=" * 50)

        return self.validation_results

    def get_validation_result(self) -> dict:
        """获取校验结果"""
        return self.validation_results