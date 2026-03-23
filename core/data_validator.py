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


class DataValidator:
    """附表与空间数据对比校验器"""

    def __init__(self):
        self.fubiao_data = {}  # 附表数据
        self.shp_data = {}  # 空间数据
        self.validation_results = {}  # 校验结果
        self.progress_callback = None

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

    def _read_shp_with_encoding(self, shp_path: str) -> Optional[gpd.GeoDataFrame]:
        """尝试多种编码读取shp文件"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'cp936', 'latin1']

        for encoding in encodings:
            try:
                gdf = gpd.read_file(shp_path, encoding=encoding)
                gdf.columns = [str(col) for col in gdf.columns]
                return gdf
            except:
                continue

        # 最后尝试默认方式
        try:
            gdf = gpd.read_file(shp_path)
            gdf.columns = [str(col) for col in gdf.columns]
            return gdf
        except:
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
        匹配字段：代码（6.代码）+ 名称（5.名称）
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

        # 构建shp索引：代码+名称 -> 记录
        shp_index = {}
        for rec in shp_records:
            code = str(rec.get('代码', '')).strip().upper()
            name = str(rec.get('名称', '')).strip().upper()
            key = f"{code}|{name}"
            if key not in shp_index:
                shp_index[key] = []
            shp_index[key].append(rec)

        # 构建附表索引
        fubiao_index = {}
        for rec in fubiao_records:
            code = str(rec.get('6.代码', '')).strip().upper()
            name = str(rec.get('5.名称', '')).strip().upper()
            key = f"{code}|{name}"
            if key not in fubiao_index:
                fubiao_index[key] = []
            fubiao_index[key].append(rec)

        # 匹配成功的key
        matched_keys = set()

        # 检查附表记录是否在shp中
        for key, recs in fubiao_index.items():
            if key in shp_index:
                matched_keys.add(key)
                for rec in recs:
                    result['matched'].append({
                        'type': 'fubiao1',
                        'fubiao_record': rec,
                        'shp_records': shp_index[key]
                    })
            else:
                for rec in recs:
                    result['fubiao_only'].append(rec)

        # 检查shp记录是否在附表中
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
        匹配字段：编码/编号 + 名称
        """
        result = {
            'matched': [],
            'fubiao_only': [],
            'shp_only': [],
            'match_count': 0,
            'fubiao_only_count': 0,
            'shp_only_count': 0
        }

        fubiao2_records = self.fubiao_data.get('fubiao2', [])
        fubiao3_records = self.fubiao_data.get('fubiao3', [])
        shp_records = self.shp_data.get('yinhuan', [])

        self.emit_progress("开始附表2/3与隐患要素分布L.shp对比...")

        # 合并附表2和附表3
        all_fubiao_records = []
        for rec in fubiao2_records:
            rec['_source_table'] = '附表2'
            all_fubiao_records.append(rec)
        for rec in fubiao3_records:
            rec['_source_table'] = '附表3'
            all_fubiao_records.append(rec)

        # 构建shp索引：编号+名称 -> 记录
        shp_index = {}
        for rec in shp_records:
            code = str(rec.get('编号', '')).strip().upper()
            name = str(rec.get('名称', '')).strip().upper()
            key = f"{code}|{name}"
            if key not in shp_index:
                shp_index[key] = []
            shp_index[key].append(rec)

        # 构建附表索引（尝试多种字段名）
        fubiao_index = {}
        for rec in all_fubiao_records:
            # 尝试不同的编码字段名
            code = ''
            for field in ['编码', '编号', '代码']:
                if field in rec:
                    code = str(rec.get(field, '')).strip().upper()
                    break

            name = ''
            for field in ['名称', '隐患名称']:
                if field in rec:
                    name = str(rec.get(field, '')).strip().upper()
                    break

            key = f"{code}|{name}"
            if key not in fubiao_index:
                fubiao_index[key] = []
            fubiao_index[key].append(rec)

        # 匹配成功的key
        matched_keys = set()

        # 检查附表记录是否在shp中
        for key, recs in fubiao_index.items():
            if key in shp_index:
                matched_keys.add(key)
                for rec in recs:
                    result['matched'].append({
                        'type': rec.get('_source_table', '附表2/3'),
                        'fubiao_record': rec,
                        'shp_records': shp_index[key]
                    })
            else:
                for rec in recs:
                    result['fubiao_only'].append(rec)

        # 检查shp记录是否在附表中
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