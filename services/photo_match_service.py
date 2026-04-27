# -*- coding: utf-8 -*-
"""
附表2/3与照片匹配校验服务

匹配逻辑:
1. 读取附表2(跨沟道路、桥涵)获取桥涵名称、编码、河流名称、河流代码、经纬度
2. 读取附表3(沟滩占地)获取名称、编号、河流名称、河流代码、经纬度
3. 用编码/编号查找照片文件夹，验证河流代码一致性
4. 生成双向检查报告: 哪些附表记录无照片、哪些照片无附表记录
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PySide6.QtCore import QObject, Signal, QThread

import pandas as pd
from openpyxl import load_workbook

from core.report_reader import find_report_files


PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}


class PhotoMatchService(QObject):
    """附表2/3与照片匹配校验服务"""

    match_finished = Signal(dict)
    match_progress = Signal(str)
    match_error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run_match(self, folder_path: str) -> dict:
        """
        执行附表2/3与照片的匹配校验

        Args:
            folder_path: 项目根目录（包含成果报表和电子数据子目录）

        Returns:
            {
                'fubiao2': {
                    'file': str,
                    'records': [...],
                    'matched': [...],
                    'unmatched_records': [...],
                    'match_count': int,
                    'unmatched_count': int
                },
                'fubiao3': {...},
                'unmatched_photos': {
                    'fubiao2_type': [...],
                    'fubiao3_type': [...]
                },
                'photo_folders': {
                    'fubiao2_type': {...},
                    'fubiao3_type': {...}
                },
                'summary': {...}
            }
        """
        result = {
            'fubiao2': {'file': '', 'records': [], 'matched': [], 'unmatched_records': [], 'match_count': 0, 'unmatched_count': 0},
            'fubiao3': {'file': '', 'records': [], 'matched': [], 'unmatched_records': [], 'match_count': 0, 'unmatched_count': 0},
            'unmatched_photos': {'fubiao2_type': [], 'fubiao3_type': []},
            'photo_folders': {'fubiao2_type': {}, 'fubiao3_type': {}},
            'summary': {}
        }

        try:
            self.match_progress.emit("正在查找附表文件...")
            report_files = find_report_files(folder_path)

            fubiao2_path = report_files.get('fubiao2')
            fubiao3_path = report_files.get('fubiao3')

            if not fubiao2_path and not fubiao3_path:
                self.match_error.emit("未找到附表2或附表3文件")
                return result

            self.match_progress.emit("正在扫描照片文件夹...")
            photo_folders_f2 = self._scan_photo_folders(folder_path, 'fubiao2')
            photo_folders_f3 = self._scan_photo_folders(folder_path, 'fubiao3')
            result['photo_folders']['fubiao2_type'] = photo_folders_f2
            result['photo_folders']['fubiao3_type'] = photo_folders_f3

            if fubiao2_path:
                self.match_progress.emit("正在匹配附表2（跨沟道路、桥涵）...")
                f2_result = self._match_fubiao2(fubiao2_path, photo_folders_f2)
                result['fubiao2'] = f2_result

            if fubiao3_path:
                self.match_progress.emit("正在匹配附表3（沟滩占地）...")
                f3_result = self._match_fubiao3(fubiao3_path, photo_folders_f3)
                result['fubiao3'] = f3_result

            self.match_progress.emit("正在检查未匹配的照片...")
            matched_codes_f2 = {m['code'] for m in result['fubiao2']['matched']}
            matched_codes_f3 = {m['code'] for m in result['fubiao3']['matched']}

            for code, folder_info in photo_folders_f2.items():
                if code not in matched_codes_f2:
                    result['unmatched_photos']['fubiao2_type'].append(folder_info)

            for code, folder_info in photo_folders_f3.items():
                if code not in matched_codes_f3:
                    result['unmatched_photos']['fubiao3_type'].append(folder_info)

            result['summary'] = {
                'fubiao2_total': len(result['fubiao2']['records']),
                'fubiao2_matched': result['fubiao2']['match_count'],
                'fubiao2_unmatched': result['fubiao2']['unmatched_count'],
                'fubiao3_total': len(result['fubiao3']['records']),
                'fubiao3_matched': result['fubiao3']['match_count'],
                'fubiao3_unmatched': result['fubiao3']['unmatched_count'],
                'photo_unmatched_f2': len(result['unmatched_photos']['fubiao2_type']),
                'photo_unmatched_f3': len(result['unmatched_photos']['fubiao3_type']),
                'fubiao2_file': fubiao2_path or '',
                'fubiao3_file': fubiao3_path or ''
            }

            self.match_progress.emit("匹配校验完成")
            self.match_finished.emit(result)
            return result

        except Exception as e:
            self.match_error.emit(str(e))
            return result

    def _scan_photo_folders(self, folder_path: str, fubiao_type: str) -> Dict[str, dict]:
        """
        扫描照片文件夹，建立编码->文件夹信息的映射

        照片文件夹结构:
        - 跨沟道路和桥涵: 电子数据/照片/跨沟道路和桥涵/{河流代码}/{编码}/
        - 沟滩占地对象: 电子数据/照片/沟滩占地对象/{河流代码}/{编码}/
        """
        photo_folders = {}

        search_names = []
        if fubiao_type == 'fubiao2':
            search_names = ['跨沟道路和桥涵', '跨沟道路', '桥涵']
        elif fubiao_type == 'fubiao3':
            search_names = ['沟滩占地对象', '沟滩占地']

        for root, dirs, files in os.walk(folder_path):
            full_path = root.replace('\\', '/')

            is_target = False
            for name in search_names:
                if name in full_path:
                    is_target = True
                    break

            if not is_target:
                continue

            photos = [f for f in files if os.path.splitext(f)[1].lower() in PHOTO_EXTENSIONS]
            if not photos:
                continue

            root_name = os.path.basename(root).strip()
            parent_name = os.path.basename(os.path.dirname(root)).strip()

            code = root_name

            if self._is_valid_code(code):
                river_code = parent_name if self._is_valid_code(parent_name) else ''
                photo_files = []
                for p in photos:
                    photo_files.append({
                        'name': p,
                        'path': os.path.join(root, p)
                    })

                photo_folders[code] = {
                    'code': code,
                    'river_code': river_code,
                    'folder_path': root,
                    'photo_count': len(photos),
                    'photos': photo_files
                }

        return photo_folders

    def _is_valid_code(self, name: str) -> bool:
        if not name:
            return False
        has_digit = any(c.isdigit() for c in name)
        has_alpha = any(c.isalpha() for c in name)
        return has_digit and has_alpha

    def _check_photo_name_match(self, photo_names: List[str], code_suffix: str) -> List[dict]:
        """
        校验照片文件名前5位是否与编码后5位一致

        Args:
            photo_names: 照片文件名列表
            code_suffix: 编码后5位

        Returns:
            [{'name': 文件名, 'prefix': 前5位, 'match': 是否一致}]
        """
        results = []
        for name in photo_names:
            name_without_ext = os.path.splitext(name)[0]
            prefix = name_without_ext[:5] if len(name_without_ext) >= 5 else name_without_ext
            match = prefix.upper() == code_suffix.upper()
            results.append({
                'name': name,
                'prefix': prefix,
                'match': match
            })
        return results

    def _match_fubiao2(self, file_path: str, photo_folders: Dict[str, dict]) -> dict:
        """
        匹配附表2（跨沟道路、桥涵）与照片

        附表2关键字段:
        - 5.名称: 桥涵名称
        - 6.编码: 桥涵编码
        - 15.河流名称: 河流名称
        - 16.河流代码: 河流代码
        - 7.经度, 8.纬度
        """
        result = {
            'file': file_path,
            'records': [],
            'matched': [],
            'unmatched_records': [],
            'match_count': 0,
            'unmatched_count': 0
        }

        records = self._load_fubiao2(file_path)
        result['records'] = records

        for rec in records:
            code = str(rec.get('6.编码', '')).strip()
            name = str(rec.get('5.名称', '')).strip()
            river_name = str(rec.get('15.河流名称', '')).strip()
            river_code = str(rec.get('16.河流代码', '')).strip()
            longitude = rec.get('7.经度', '')
            latitude = rec.get('8.纬度', '')

            if not code:
                result['unmatched_records'].append({
                    **rec,
                    '_match_reason': '编码为空'
                })
                continue

            matched_folder = self._find_photo_folder(code, river_code, photo_folders)

            if matched_folder:
                river_code_match = True
                if river_code and matched_folder.get('river_code'):
                    river_code_match = river_code.upper() == matched_folder['river_code'].upper()

                photo_names = [p['name'] for p in matched_folder['photos']]
                code_suffix = code[-5:] if len(code) >= 5 else code
                name_match_results = self._check_photo_name_match(photo_names, code_suffix)
                name_match = all(r['match'] for r in name_match_results)
                name_match_detail = '; '.join(
                    f"{r['name']}({'✓' if r['match'] else '✗'})" for r in name_match_results
                )

                result['matched'].append({
                    'name': name,
                    'code': code,
                    'river_name': river_name,
                    'river_code': river_code,
                    'longitude': longitude,
                    'latitude': latitude,
                    'photo_folder': matched_folder['folder_path'],
                    'photo_count': matched_folder['photo_count'],
                    'photo_names': ', '.join(photo_names),
                    'name_match': name_match,
                    'name_match_detail': name_match_detail,
                    'photos': matched_folder['photos'],
                    'river_code_match': river_code_match,
                    'record': rec
                })
            else:
                result['unmatched_records'].append({
                    **rec,
                    '_match_reason': '未找到对应照片文件夹'
                })

        result['match_count'] = len(result['matched'])
        result['unmatched_count'] = len(result['unmatched_records'])

        return result

    def _match_fubiao3(self, file_path: str, photo_folders: Dict[str, dict]) -> dict:
        """
        匹配附表3（沟滩占地）与照片

        附表3关键字段:
        - 5.名称: 名称
        - 6.编号: 编号
        - 14. 河流名称: 河流名称
        - 15. 河流代码: 河流代码
        - 7.经度, 8.纬度
        """
        result = {
            'file': file_path,
            'records': [],
            'matched': [],
            'unmatched_records': [],
            'match_count': 0,
            'unmatched_count': 0
        }

        records = self._load_fubiao3(file_path)
        result['records'] = records

        for rec in records:
            code = str(rec.get('6.编号', '')).strip()
            name = str(rec.get('5.名称', '')).strip()
            river_name = str(rec.get('14. 河流名称', '')).strip()
            river_code = str(rec.get('15. 河流代码', '')).strip()
            longitude = rec.get('7.经度', '')
            latitude = rec.get('8.纬度', '')

            if not code:
                result['unmatched_records'].append({
                    **rec,
                    '_match_reason': '编号为空'
                })
                continue

            matched_folder = self._find_photo_folder(code, river_code, photo_folders)

            if matched_folder:
                river_code_match = True
                if river_code and matched_folder.get('river_code'):
                    river_code_match = river_code.upper() == matched_folder['river_code'].upper()

                photo_names = [p['name'] for p in matched_folder['photos']]
                code_suffix = code[-5:] if len(code) >= 5 else code
                name_match_results = self._check_photo_name_match(photo_names, code_suffix)
                name_match = all(r['match'] for r in name_match_results)
                name_match_detail = '; '.join(
                    f"{r['name']}({'✓' if r['match'] else '✗'})" for r in name_match_results
                )

                result['matched'].append({
                    'name': name,
                    'code': code,
                    'river_name': river_name,
                    'river_code': river_code,
                    'longitude': longitude,
                    'latitude': latitude,
                    'photo_folder': matched_folder['folder_path'],
                    'photo_count': matched_folder['photo_count'],
                    'photo_names': ', '.join(photo_names),
                    'name_match': name_match,
                    'name_match_detail': name_match_detail,
                    'photos': matched_folder['photos'],
                    'river_code_match': river_code_match,
                    'record': rec
                })
            else:
                result['unmatched_records'].append({
                    **rec,
                    '_match_reason': '未找到对应照片文件夹'
                })

        result['match_count'] = len(result['matched'])
        result['unmatched_count'] = len(result['unmatched_records'])

        return result

    def _find_photo_folder(self, code: str, river_code: str, photo_folders: Dict[str, dict]) -> Optional[dict]:
        """
        在照片文件夹映射中查找匹配的文件夹

        匹配策略:
        1. 精确匹配编码
        2. 编码去掉县代码前缀后匹配（照片文件夹名可能省略6位县代码）
        """
        if code in photo_folders:
            return photo_folders[code]

        code_upper = code.upper()
        for folder_code, folder_info in photo_folders.items():
            if folder_code.upper() == code_upper:
                return folder_info

        if len(code) > 6:
            short_code = code[6:]
            for folder_code, folder_info in photo_folders.items():
                if folder_code.upper() == short_code.upper():
                    return folder_info
                if len(folder_code) > 6 and folder_code[6:].upper() == short_code.upper():
                    return folder_info

        for folder_code, folder_info in photo_folders.items():
            if code in folder_code or folder_code in code:
                return folder_info

        return None

    def _load_fubiao2(self, file_path: str) -> List[Dict]:
        """读取附表2数据"""
        if not file_path or not os.path.exists(file_path):
            return []

        df_header = pd.read_excel(file_path, header=None, nrows=1)
        headers = [str(df_header.iloc[0, i]) if pd.notna(df_header.iloc[0, i]) else f'列{i}'
                   for i in range(len(df_header.columns))]

        df = pd.read_excel(file_path)

        records = []
        for _, row in df.iterrows():
            record = {}
            for i, col in enumerate(df.columns):
                val = row[col]
                if pd.notna(val):
                    record[headers[i]] = val
                else:
                    record[headers[i]] = ''
            if any(v for k, v in record.items() if k != '序号' and v):
                records.append(record)

        return records

    def _load_fubiao3(self, file_path: str) -> List[Dict]:
        """读取附表3数据"""
        if not file_path or not os.path.exists(file_path):
            return []

        df_header = pd.read_excel(file_path, header=None, nrows=1)
        headers = [str(df_header.iloc[0, i]) if pd.notna(df_header.iloc[0, i]) else f'列{i}'
                   for i in range(len(df_header.columns))]

        df = pd.read_excel(file_path)

        records = []
        for _, row in df.iterrows():
            record = {}
            for i, col in enumerate(df.columns):
                val = row[col]
                if pd.notna(val):
                    record[headers[i]] = val
                else:
                    record[headers[i]] = ''
            if any(v for k, v in record.items() if k != '序号' and v):
                records.append(record)

        return records

    @staticmethod
    def export_to_excel(result: dict, output_path: str) -> bool:
        """
        将匹配结果导出为Excel文件

        Args:
            result: run_match()返回的结果
            output_path: 输出文件路径

        Returns:
            是否导出成功
        """
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                summary_data = {
                    '检查项': [
                        '附表2（跨沟道路、桥涵）总记录数',
                        '附表2匹配照片成功数',
                        '附表2未匹配照片数',
                        '附表3（沟滩占地）总记录数',
                        '附表3匹配照片成功数',
                        '附表3未匹配照片数',
                        '照片未匹配附表2数',
                        '照片未匹配附表3数'
                    ],
                    '数量': [
                        result['summary'].get('fubiao2_total', 0),
                        result['summary'].get('fubiao2_matched', 0),
                        result['summary'].get('fubiao2_unmatched', 0),
                        result['summary'].get('fubiao3_total', 0),
                        result['summary'].get('fubiao3_matched', 0),
                        result['summary'].get('fubiao3_unmatched', 0),
                        result['summary'].get('photo_unmatched_f2', 0),
                        result['summary'].get('photo_unmatched_f3', 0)
                    ]
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='汇总', index=False)

                if result['fubiao2']['matched']:
                    f2_matched_data = []
                    for m in result['fubiao2']['matched']:
                        f2_matched_data.append({
                            '名称': m['name'],
                            '编码': m['code'],
                            '河流名称': m['river_name'],
                            '河流代码': m['river_code'],
                            '经度': m['longitude'],
                            '纬度': m['latitude'],
                            '照片数量': m['photo_count'],
                            '照片文件名': m.get('photo_names', ''),
                            '命名校验': '通过' if m.get('name_match', True) else '不通过',
                            '照片文件夹': m['photo_folder'],
                            '河流代码一致': '是' if m['river_code_match'] else '否'
                        })
                    pd.DataFrame(f2_matched_data).to_excel(writer, sheet_name='附表2-已匹配', index=False)

                if result['fubiao2']['unmatched_records']:
                    f2_unmatched_data = []
                    for r in result['fubiao2']['unmatched_records']:
                        f2_unmatched_data.append({
                            '名称': str(r.get('5.名称', '')),
                            '编码': str(r.get('6.编码', '')),
                            '河流名称': str(r.get('15.河流名称', '')),
                            '河流代码': str(r.get('16.河流代码', '')),
                            '经度': r.get('7.经度', ''),
                            '纬度': r.get('8.纬度', ''),
                            '未匹配原因': r.get('_match_reason', '')
                        })
                    pd.DataFrame(f2_unmatched_data).to_excel(writer, sheet_name='附表2-未匹配照片', index=False)

                if result['fubiao3']['matched']:
                    f3_matched_data = []
                    for m in result['fubiao3']['matched']:
                        f3_matched_data.append({
                            '名称': m['name'],
                            '编号': m['code'],
                            '河流名称': m['river_name'],
                            '河流代码': m['river_code'],
                            '经度': m['longitude'],
                            '纬度': m['latitude'],
                            '照片数量': m['photo_count'],
                            '照片文件名': m.get('photo_names', ''),
                            '命名校验': '通过' if m.get('name_match', True) else '不通过',
                            '照片文件夹': m['photo_folder'],
                            '河流代码一致': '是' if m['river_code_match'] else '否'
                        })
                    pd.DataFrame(f3_matched_data).to_excel(writer, sheet_name='附表3-已匹配', index=False)

                if result['fubiao3']['unmatched_records']:
                    f3_unmatched_data = []
                    for r in result['fubiao3']['unmatched_records']:
                        f3_unmatched_data.append({
                            '名称': str(r.get('5.名称', '')),
                            '编号': str(r.get('6.编号', '')),
                            '河流名称': str(r.get('14. 河流名称', '')),
                            '河流代码': str(r.get('15. 河流代码', '')),
                            '经度': r.get('7.经度', ''),
                            '纬度': r.get('8.纬度', ''),
                            '未匹配原因': r.get('_match_reason', '')
                        })
                    pd.DataFrame(f3_unmatched_data).to_excel(writer, sheet_name='附表3-未匹配照片', index=False)

                all_unmatched = []
                for p in result['unmatched_photos']['fubiao2_type']:
                    all_unmatched.append({
                        '照片编码': p['code'],
                        '河流代码': p['river_code'],
                        '照片数量': p['photo_count'],
                        '照片文件夹': p['folder_path'],
                        '类型': '跨沟道路和桥涵'
                    })
                for p in result['unmatched_photos']['fubiao3_type']:
                    all_unmatched.append({
                        '照片编码': p['code'],
                        '河流代码': p['river_code'],
                        '照片数量': p['photo_count'],
                        '照片文件夹': p['folder_path'],
                        '类型': '沟滩占地对象'
                    })
                if all_unmatched:
                    pd.DataFrame(all_unmatched).to_excel(writer, sheet_name='照片-未匹配附表', index=False)

            return True
        except Exception as e:
            return False


class MatchWorker(QObject):
    """匹配校验工作线程"""

    finished = Signal(dict)
    progress = Signal(str)
    error = Signal(str)

    def __init__(self, service: PhotoMatchService, folder_path: str):
        super().__init__()
        self.service = service
        self.folder_path = folder_path

    def run(self):
        try:
            self.service.match_progress.connect(self.progress.emit)
            result = self.service.run_match(self.folder_path)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
