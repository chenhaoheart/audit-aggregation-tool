# -*- coding: utf-8 -*-
"""
Dashboard汇总检查服务
整合4大分项检查 + 交叉校验
"""

import os
import re
import warnings
from typing import Dict, List, Optional
from PySide6.QtCore import QObject, QThread, Signal

warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*gb2312.*UTF-8.*')
warnings.filterwarnings('ignore', message='.*characters couldn\'t be converted correctly.*')

from core.report_reader import find_report_files, load_all_reports
from core.data_validator import DataValidator
from utils.data_checker import DataChecker
from core.checker import WaterSystemChecker
from services.photo_match_service import PhotoMatchService
from services.section_chart_service import SectionChartService


class DashboardCheckThread(QThread):
    progress_signal = Signal(str, str)
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, root_path: str, parent=None):
        super().__init__(parent)
        self.root_path = root_path

    def run(self):
        try:
            result = run_dashboard_check(
                self.root_path,
                progress_callback=lambda section, msg: self.progress_signal.emit(section, msg)
            )
            self.finished_signal.emit(result)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_signal.emit(str(e))


def _find_water_system_shp(root_path: str) -> Optional[str]:
    for root, dirs, files in os.walk(root_path):
        for f in files:
            if f.endswith('.shp') and '水系' in f:
                return os.path.join(root, f)
    return None


def _find_spatial_data_folder(root_path: str) -> Optional[str]:
    for root, dirs, files in os.walk(root_path):
        for f in files:
            if f in ('防治对象分布P.shp', '断面平面位置L.shp'):
                return root
    return None


def _find_subfolder(root_path: str) -> Optional[str]:
    for item in os.listdir(root_path):
        item_path = os.path.join(root_path, item)
        if os.path.isdir(item_path):
            if os.path.exists(os.path.join(item_path, '成果报表')) or os.path.exists(os.path.join(item_path, '电子数据')):
                return item_path
            for sub in os.listdir(item_path):
                sub_path = os.path.join(item_path, sub)
                if os.path.isdir(sub_path):
                    if os.path.exists(os.path.join(sub_path, '成果报表')) or os.path.exists(os.path.join(sub_path, '电子数据')):
                        return sub_path
    return None


def run_dashboard_check(root_path: str, progress_callback=None) -> dict:
    """
    执行Dashboard全部检查

    Args:
        root_path: 示范小流域根目录
        progress_callback: 进度回调 (section, message)

    Returns:
        {
            'fubiao_check': {...},
            'spatial_check': {...},
            'section_check': {...},
            'photo_check': {...},
            'cross_check': {...},
            'summary': {...}
        }
    """
    def emit(section, msg):
        if progress_callback:
            progress_callback(section, msg)

    result = {
        'fubiao_check': {'status': 'pending', 'errors': [], 'warnings': [], 'records': {}},
        'spatial_check': {'status': 'pending', 'errors': [], 'warnings': [], 'results': [], 'all_records': []},
        'section_check': {'status': 'pending', 'errors': [], 'warnings': [], 'stats': {}},
        'photo_check': {'status': 'pending', 'errors': [], 'warnings': [], 'match_result': {}},
        'cross_check': {'status': 'pending', 'errors': [], 'warnings': [], 'items': []},
        'summary': {}
    }

    subfolder = _find_subfolder(root_path)
    if not subfolder:
        subfolder = root_path

    # ========== 1. 附表1/2/3检查 ==========
    emit("fubiao", "开始附表数据检查...")
    try:
        report_data = load_all_reports(subfolder)
        if report_data.get('missing'):
            for m in report_data['missing']:
                result['fubiao_check']['warnings'].append(f"未找到文件: {m}")

        checker = DataChecker(report_data)
        errors = checker.check_all()
        result['fubiao_check']['errors'] = errors
        result['fubiao_check']['records'] = {
            'fubiao1_count': len(report_data.get('fubiao1', {}).get('records', [])),
            'fubiao2_count': len(report_data.get('fubiao2', {}).get('records', [])),
            'fubiao3_count': len(report_data.get('fubiao3', {}).get('records', [])),
            'fubiao1_file': report_data.get('fubiao1', {}).get('file', ''),
            'fubiao2_file': report_data.get('fubiao2', {}).get('file', ''),
            'fubiao3_file': report_data.get('fubiao3', {}).get('file', ''),
            'report_data': report_data,
        }
        error_count = len(errors)
        result['fubiao_check']['status'] = 'pass' if error_count == 0 else 'fail'
        emit("fubiao", f"附表检查完成: 发现 {error_count} 个问题")
    except Exception as e:
        result['fubiao_check']['status'] = 'error'
        result['fubiao_check']['errors'].append(str(e))
        emit("fubiao", f"附表检查异常: {e}")

    # ========== 2. 空间数据检查 ==========
    emit("spatial", "开始空间数据检查...")
    try:
        water_shp = _find_water_system_shp(root_path)
        spatial_folder = _find_spatial_data_folder(subfolder)

        if water_shp and spatial_folder:
            checker = WaterSystemChecker(spatial_folder, water_shp)
            checker.progress_callback = lambda msg: emit("spatial", msg)
            check_results = checker.process_all()

            duanmian = [r for r in checker.all_records if '断面平面位置' in r.get('源文件', '')]
            fangzhi = [r for r in checker.all_records if '防治对象分布' in r.get('源文件', '')]
            yinhuan = [r for r in checker.all_records if '隐患要素分布' in r.get('源文件', '')]

            result['spatial_check']['results'] = check_results
            result['spatial_check']['all_records'] = checker.all_records
            result['spatial_check']['water_records'] = checker.water_records
            result['spatial_check']['water_codes'] = list(checker.water_codes)
            result['spatial_check']['water_code_to_name'] = checker.water_code_to_name
            result['spatial_check']['duanmian'] = duanmian
            result['spatial_check']['fangzhi'] = fangzhi
            result['spatial_check']['yinhuan'] = yinhuan
            result['spatial_check']['water_data'] = checker.water_data

            invalid_count = sum(1 for r in check_results if r.get('status') != '通过')
            result['spatial_check']['status'] = 'pass' if invalid_count == 0 else 'fail'
            emit("spatial", f"空间数据检查完成: {len(check_results)} 个图层, {invalid_count} 个异常")
        else:
            if not water_shp:
                result['spatial_check']['warnings'].append("未找到水系SHP文件")
            if not spatial_folder:
                result['spatial_check']['warnings'].append("未找到空间数据文件夹")
            result['spatial_check']['status'] = 'warn'
            emit("spatial", "空间数据检查跳过: 缺少必要文件")
    except Exception as e:
        result['spatial_check']['status'] = 'error'
        result['spatial_check']['errors'].append(str(e))
        emit("spatial", f"空间数据检查异常: {e}")

    # ========== 3. 断面数据检查 ==========
    emit("section", "开始断面数据检查...")
    try:
        section_service = SectionChartService()
        section_result = section_service.load_from_directory(
            os.path.join(subfolder, '电子数据', '测量数据') if os.path.exists(os.path.join(subfolder, '电子数据', '测量数据')) else subfolder,
            progress_callback=lambda cur, total, name: emit("section", f"({cur}/{total}) {name}")
        )
        stats = section_service.get_stats()
        result['section_check']['stats'] = stats
        result['section_check']['section_service'] = section_service
        result['section_check']['tree_data'] = section_service.get_tree_data()

        error_count = stats.get('validation_error_count', 0)
        anomaly_count = stats.get('anomaly_count', 0)
        result['section_check']['status'] = 'pass' if (error_count == 0 and anomaly_count == 0) else 'fail'
        emit("section", f"断面检查完成: {stats.get('total_sections', 0)} 个断面, {error_count} 个错误, {anomaly_count} 个异常")
    except Exception as e:
        result['section_check']['status'] = 'error'
        result['section_check']['errors'].append(str(e))
        emit("section", f"断面数据检查异常: {e}")

    # ========== 4. 照片检查 ==========
    emit("photo", "开始照片与附表匹配检查...")
    try:
        photo_service = PhotoMatchService()
        match_result = photo_service.run_match(subfolder)
        result['photo_check']['match_result'] = match_result

        f2_unmatched = match_result.get('summary', {}).get('fubiao2_unmatched', 0)
        f3_unmatched = match_result.get('summary', {}).get('fubiao3_unmatched', 0)
        photo_unmatched = match_result.get('summary', {}).get('photo_unmatched_f2', 0) + match_result.get('summary', {}).get('photo_unmatched_f3', 0)

        result['photo_check']['status'] = 'pass' if (f2_unmatched == 0 and f3_unmatched == 0 and photo_unmatched == 0) else 'fail'
        emit("photo", f"照片检查完成: 附表2未匹配{f2_unmatched}, 附表3未匹配{f3_unmatched}, 照片未匹配{photo_unmatched}")
    except Exception as e:
        result['photo_check']['status'] = 'error'
        result['photo_check']['errors'].append(str(e))
        emit("photo", f"照片检查异常: {e}")

    # ========== 5. 交叉检查 ==========
    emit("cross", "开始交叉校验...")
    try:
        cross_items = []

        # 5.1 附表数据与空间数据一致性
        _cross_fubiao_vs_spatial(result, cross_items, emit)

        # 5.2 照片与附表匹配
        _cross_photo_vs_fubiao(result, cross_items, emit)

        # 5.3 断面测量表与空间数据【断面平面位置】图层校验
        _cross_section_vs_spatial(result, cross_items, emit)

        # 5.4 空间数据隐患要素分布与照片匹配
        _cross_yinhuan_vs_photo(result, cross_items, emit)

        result['cross_check']['items'] = cross_items
        error_items = [i for i in cross_items if i.get('level') == 'error']
        warn_items = [i for i in cross_items if i.get('level') == 'warning']
        result['cross_check']['errors'] = error_items
        result['cross_check']['warnings'] = warn_items
        result['cross_check']['status'] = 'pass' if len(error_items) == 0 else 'fail'
        emit("cross", f"交叉校验完成: {len(error_items)} 个错误, {len(warn_items)} 个警告")
    except Exception as e:
        result['cross_check']['status'] = 'error'
        result['cross_check']['errors'].append({'level': 'error', 'desc': str(e)})
        emit("cross", f"交叉校验异常: {e}")

    # ========== 汇总 ==========
    total_errors = (
        len(result['fubiao_check'].get('errors', [])) +
        len([r for r in result['spatial_check'].get('results', []) if r.get('status') != '通过']) +
        result['section_check'].get('stats', {}).get('validation_error_count', 0) +
        len([i for i in result['cross_check'].get('items', []) if i.get('level') == 'error'])
    )
    total_warnings = (
        len(result['fubiao_check'].get('warnings', [])) +
        len(result['spatial_check'].get('warnings', [])) +
        result['section_check'].get('stats', {}).get('anomaly_count', 0) +
        len([i for i in result['cross_check'].get('items', []) if i.get('level') == 'warning'])
    )

    result['summary'] = {
        'total_errors': total_errors,
        'total_warnings': total_warnings,
        'fubiao_status': result['fubiao_check']['status'],
        'spatial_status': result['spatial_check']['status'],
        'section_status': result['section_check']['status'],
        'photo_status': result['photo_check']['status'],
        'cross_status': result['cross_check']['status'],
        'overall_status': 'pass' if total_errors == 0 else ('warn' if total_warnings > 0 else 'fail'),
    }

    emit("summary", f"全部检查完成: 错误 {total_errors}, 警告 {total_warnings}")
    return result


def _cross_fubiao_vs_spatial(result: dict, cross_items: list, emit):
    """交叉检查: 附表数据与空间数据一致性"""
    emit("cross", "检查附表与空间数据一致性...")

    report_data = result['fubiao_check']['records'].get('report_data', {})
    fangzhi_records = result['spatial_check'].get('fangzhi', [])
    yinhuan_records = result['spatial_check'].get('yinhuan', [])

    if not report_data:
        return

    validator = DataValidator()
    validator.progress_callback = lambda msg: emit("cross", msg)
    validator.load_fubiao(report_data)

    fubiao1_records = report_data.get('fubiao1', {}).get('records', [])
    fubiao2_records = report_data.get('fubiao2', {}).get('records', [])
    fubiao3_records = report_data.get('fubiao3', {}).get('records', [])

    fb1_codes = set()
    fb1_names = set()
    for r in fubiao1_records:
        code = str(r.get('6.代码', '')).strip()
        name = str(r.get('5.名称', '')).strip()
        if code:
            fb1_codes.add(code)
        if name:
            fb1_names.add(name)

    fz_codes = set()
    fz_names = set()
    for rec in fangzhi_records:
        code = str(rec.get('代码', '')).strip()
        name = str(rec.get('名称', '')).strip()
        if code:
            fz_codes.add(code)
        if name:
            fz_names.add(name)

    fb1_only_codes = fb1_codes - fz_codes
    if fb1_only_codes:
        cross_items.append({
            'level': 'error',
            'category': '附表1↔防治对象分布',
            'desc': f"附表1有 {len(fb1_only_codes)} 条记录在防治对象分布P.shp中不存在(按代码匹配)",
            'detail': list(fb1_only_codes)[:5]
        })

    fz_only_codes = fz_codes - fb1_codes
    if fz_only_codes:
        cross_items.append({
            'level': 'error',
            'category': '附表1↔防治对象分布',
            'desc': f"防治对象分布P.shp有 {len(fz_only_codes)} 条记录在附表1中不存在(按代码匹配)",
            'detail': list(fz_only_codes)[:5]
        })

    fb2_codes = set()
    fb3_codes = set()
    for r in fubiao2_records:
        code = str(r.get('6.编号', '')).strip()
        if code:
            fb2_codes.add(code)
    for r in fubiao3_records:
        code = str(r.get('6.编号', '')).strip()
        if code:
            fb3_codes.add(code)

    yh_codes = set()
    for rec in yinhuan_records:
        code = str(rec.get('编号', '')).strip()
        if code:
            yh_codes.add(code)

    fb2_only = fb2_codes - yh_codes
    if fb2_only:
        cross_items.append({
            'level': 'error',
            'category': '附表2↔隐患要素分布',
            'desc': f"附表2有 {len(fb2_only)} 条记录在隐患要素分布L.shp中不存在",
            'detail': list(fb2_only)[:5]
        })

    fb3_only = fb3_codes - yh_codes
    if fb3_only:
        cross_items.append({
            'level': 'error',
            'category': '附表3↔隐患要素分布',
            'desc': f"附表3有 {len(fb3_only)} 条记录在隐患要素分布L.shp中不存在",
            'detail': list(fb3_only)[:5]
        })

    yh_only = yh_codes - fb2_codes - fb3_codes
    if yh_only:
        cross_items.append({
            'level': 'warning',
            'category': '隐患要素分布↔附表2/3',
            'desc': f"隐患要素分布L.shp有 {len(yh_only)} 条记录在附表2/3中不存在",
            'detail': list(yh_only)[:5]
        })


def _cross_photo_vs_fubiao(result: dict, cross_items: list, emit):
    """交叉检查: 照片与附表匹配"""
    emit("cross", "检查照片与附表匹配...")

    match_result = result['photo_check'].get('match_result', {})
    if not match_result:
        return

    summary = match_result.get('summary', {})
    f2_unmatched = summary.get('fubiao2_unmatched', 0)
    f3_unmatched = summary.get('fubiao3_unmatched', 0)
    photo_unmatched_f2 = summary.get('photo_unmatched_f2', 0)
    photo_unmatched_f3 = summary.get('photo_unmatched_f3', 0)

    if f2_unmatched > 0:
        cross_items.append({
            'level': 'error',
            'category': '照片↔附表2',
            'desc': f"附表2有 {f2_unmatched} 条记录无对应照片",
        })
    if f3_unmatched > 0:
        cross_items.append({
            'level': 'error',
            'category': '照片↔附表3',
            'desc': f"附表3有 {f3_unmatched} 条记录无对应照片",
        })
    if photo_unmatched_f2 > 0:
        cross_items.append({
            'level': 'warning',
            'category': '照片↔附表2',
            'desc': f"有 {photo_unmatched_f2} 个照片文件夹无对应附表2记录",
        })
    if photo_unmatched_f3 > 0:
        cross_items.append({
            'level': 'warning',
            'category': '照片↔附表3',
            'desc': f"有 {photo_unmatched_f3} 个照片文件夹无对应附表3记录",
        })

    f2_matched = match_result.get('fubiao2', {}).get('matched', [])
    for m in f2_matched:
        if not m.get('river_code_match', True):
            cross_items.append({
                'level': 'error',
                'category': '照片↔附表2',
                'desc': f"桥涵[{m.get('name', '')}]编码{m.get('code', '')}的河流代码与照片文件夹不一致",
            })
        if not m.get('name_match', True):
            cross_items.append({
                'level': 'warning',
                'category': '照片↔附表2',
                'desc': f"桥涵[{m.get('name', '')}]编码{m.get('code', '')}的照片文件名前缀与编码后5位不一致",
            })

    f3_matched = match_result.get('fubiao3', {}).get('matched', [])
    for m in f3_matched:
        if not m.get('river_code_match', True):
            cross_items.append({
                'level': 'error',
                'category': '照片↔附表3',
                'desc': f"沟滩占地[{m.get('name', '')}]编号{m.get('code', '')}的河流代码与照片文件夹不一致",
            })
        if not m.get('name_match', True):
            cross_items.append({
                'level': 'warning',
                'category': '照片↔附表3',
                'desc': f"沟滩占地[{m.get('name', '')}]编号{m.get('code', '')}的照片文件名前缀与编号后5位不一致",
            })


def _cross_section_vs_spatial(result: dict, cross_items: list, emit):
    """交叉检查: 断面测量表数据与空间数据【断面平面位置】图层校验"""
    emit("cross", "检查断面测量表与断面平面位置图层...")

    section_service = result['section_check'].get('section_service')
    duanmian_records = result['spatial_check'].get('duanmian', [])

    if not section_service or not duanmian_records:
        return

    try:
        all_sections = section_service.get_all_sections()
    except Exception:
        all_sections = {}

    section_cs_in_db = {}
    for key, sec in all_sections.items():
        name = sec.get('name', '')
        sheet_name = sec.get('sheet_name', '')
        cs_match = re.search(r'(CS\d{3})', name.upper())
        if cs_match:
            cs_code = cs_match.group(1)
            river_code = ''
            rc_match = re.match(r'^([A-Za-z]+\d+l\d+)', sheet_name)
            if rc_match:
                river_code = rc_match.group(1)
            section_cs_in_db[cs_code] = {
                'name': name,
                'sheet_name': sheet_name,
                'river_code': river_code,
            }

    duanmian_cs_in_shp = {}
    for rec in duanmian_records:
        name = str(rec.get('名称', '')).strip()
        rc = str(rec.get('河流代码', '')).strip()
        cs_match = re.search(r'(CS\d{3})', name.upper())
        if cs_match:
            cs_code = cs_match.group(1)
            duanmian_cs_in_shp[cs_code] = {
                'name': name,
                'river_code': rc,
            }

    db_cs_set = set(section_cs_in_db.keys())
    shp_cs_set = set(duanmian_cs_in_shp.keys())

    only_in_db = db_cs_set - shp_cs_set
    if only_in_db:
        cross_items.append({
            'level': 'warning',
            'category': '断面测量↔断面平面位置',
            'desc': f"断面测量表中有 {len(only_in_db)} 个断面(CS编号)在断面平面位置L.shp中不存在",
            'detail': list(only_in_db)[:5]
        })

    only_in_shp = shp_cs_set - db_cs_set
    if only_in_shp:
        cross_items.append({
            'level': 'warning',
            'category': '断面测量↔断面平面位置',
            'desc': f"断面平面位置L.shp中有 {len(only_in_shp)} 个断面(CS编号)在测量表中不存在",
            'detail': list(only_in_shp)[:5]
        })

    common_cs = db_cs_set & shp_cs_set
    code_mismatch = []
    for cs_code in common_cs:
        db_rc = section_cs_in_db[cs_code].get('river_code', '')
        shp_rc = duanmian_cs_in_shp[cs_code].get('river_code', '')
        if db_rc and shp_rc and db_rc.upper() != shp_rc.upper():
            code_mismatch.append(cs_code)
    if code_mismatch:
        cross_items.append({
            'level': 'error',
            'category': '断面测量↔断面平面位置',
            'desc': f"有 {len(code_mismatch)} 个断面的河流代码在测量表与空间数据中不一致",
            'detail': code_mismatch[:5]
        })

    emit("cross", f"断面交叉检查: 测量表{len(db_cs_set)}个CS, SHP{len(shp_cs_set)}个CS, 共同{len(common_cs)}个")


def _cross_yinhuan_vs_photo(result: dict, cross_items: list, emit):
    """交叉检查: 空间数据隐患要素分布与照片匹配"""
    emit("cross", "检查隐患要素分布与照片匹配...")

    yinhuan_records = result['spatial_check'].get('yinhuan', [])
    match_result = result['photo_check'].get('match_result', {})

    if not yinhuan_records or not match_result:
        return

    yinhuan_codes = set()
    for rec in yinhuan_records:
        bh = str(rec.get('编号', '')).strip()
        if bh:
            yinhuan_codes.add(bh.upper())

    photo_folders_f2 = match_result.get('photo_folders', {}).get('fubiao2_type', {})
    photo_folders_f3 = match_result.get('photo_folders', {}).get('fubiao3_type', {})

    all_photo_codes = set()
    for code in list(photo_folders_f2.keys()) + list(photo_folders_f3.keys()):
        all_photo_codes.add(code.upper())

    yinhuan_no_photo = []
    for code in yinhuan_codes:
        found = False
        for photo_code in all_photo_codes:
            if code in photo_code or photo_code in code:
                found = True
                break
            if len(code) > 6 and len(photo_code) > 6:
                if code[6:] == photo_code[6:]:
                    found = True
                    break
        if not found:
            yinhuan_no_photo.append(code)

    if yinhuan_no_photo:
        cross_items.append({
            'level': 'warning',
            'category': '隐患要素分布↔照片',
            'desc': f"隐患要素分布L.shp中有 {len(yinhuan_no_photo)} 条记录无对应照片",
            'detail': yinhuan_no_photo[:5]
        })

    yinhuan_river_codes = set()
    for rec in yinhuan_records:
        rc = str(rec.get('河流代码', '')).strip()
        if rc:
            yinhuan_river_codes.add(rc.upper())

    photo_river_codes = set()
    for folder_info in list(photo_folders_f2.values()) + list(photo_folders_f3.values()):
        rc = folder_info.get('river_code', '')
        if rc:
            photo_river_codes.add(rc.upper())

    river_mismatch = yinhuan_river_codes - photo_river_codes
    if river_mismatch and photo_river_codes:
        cross_items.append({
            'level': 'warning',
            'category': '隐患要素分布↔照片',
            'desc': f"隐患要素分布中有 {len(river_mismatch)} 个河流代码在照片文件夹中不存在",
        })

    emit("cross", f"隐患要素↔照片交叉检查: 隐患{len(yinhuan_codes)}条, 照片{len(all_photo_codes)}个编码, 无照片{len(yinhuan_no_photo)}条")


class DashboardService(QObject):
    """Dashboard汇总检查服务"""

    progress = Signal(str, str)
    finished = Signal(dict)
    error = Signal(str)
    state_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = None
        self._state = "idle"
        self._results = None

    @property
    def state(self) -> str:
        return self._state

    @property
    def results(self) -> dict:
        return self._results

    @property
    def is_running(self) -> bool:
        return self._state == "running"

    def start_check(self, root_path: str) -> bool:
        if self.is_running:
            return False

        self._state = "running"
        self.state_changed.emit(self._state)

        self._thread = DashboardCheckThread(root_path)
        self._thread.progress_signal.connect(self._on_progress)
        self._thread.finished_signal.connect(self._on_finished)
        self._thread.error_signal.connect(self._on_error)
        self._thread.start()
        return True

    def cancel_check(self):
        if self._thread and self._thread.isRunning():
            self._thread.terminate()
            self._thread.wait()
        self._state = "idle"
        self.state_changed.emit(self._state)

    def clear_results(self):
        self._results = None
        self._state = "idle"
        self.state_changed.emit(self._state)

    def _on_progress(self, section: str, msg: str):
        self.progress.emit(section, msg)

    def _on_finished(self, data: dict):
        self._results = data
        self._state = "finished"
        self.state_changed.emit(self._state)
        self.finished.emit(data)

    def _on_error(self, msg: str):
        self._state = "error"
        self.state_changed.emit(self._state)
        self.error.emit(msg)
