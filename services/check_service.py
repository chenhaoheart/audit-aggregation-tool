# -*- coding: utf-8 -*-
"""
数据检查业务服务
"""

import os
from PySide6.QtCore import QObject, QThread, Signal, Slot
from core.checker import WaterSystemChecker
from core.config_manager import get_shp_match_config


LAYER_TYPES = [
    {'key': 'water', 'name': '水系', 'required': False},
    {'key': 'duanmian', 'name': '断面平面位置', 'required': False},
    {'key': 'fangzhi', 'name': '防治对象分布', 'required': False},
    {'key': 'yinhuan', 'name': '隐患要素分布', 'required': False},
    {'key': 'liuyu', 'name': '流域', 'required': False},
]


def scan_shp_files(root_path: str) -> dict:
    """
    扫描目录下的SHP文件，自动匹配到各图层类型

    Args:
        root_path: 根目录路径

    Returns:
        dict: {
            'layers': {
                'water': {'name': '水系', 'path': '/path/to/file.shp', 'matched': True},
                'duanmian': {'name': '断面平面位置', 'path': '', 'matched': False},
                ...
            },
            'spatial_folder': '/path/to/spatial/data/folder' or None,
            'all_shp_files': ['/path/to/file1.shp', ...]
        }
    """
    shp_cfg = get_shp_match_config()
    layer_keywords = shp_cfg.layer_keywords
    water_keywords = shp_cfg.water_system_keywords

    layers = {}
    for lt in LAYER_TYPES:
        layers[lt['key']] = {
            'name': lt['name'],
            'path': '',
            'matched': False,
            'required': lt['required']
        }

    all_shp_files = []
    spatial_folder = None

    if not root_path or not os.path.exists(root_path):
        return {'layers': layers, 'spatial_folder': None, 'all_shp_files': []}

    for root, dirs, files in os.walk(root_path):
        for f in files:
            if f.endswith('.shp'):
                full_path = os.path.join(root, f)
                all_shp_files.append(full_path)

                if shp_cfg.match_water_system(f) and not layers['water']['matched']:
                    layers['water']['path'] = full_path
                    layers['water']['matched'] = True

                if shp_cfg.match_spatial_data_file(f) and spatial_folder is None:
                    spatial_folder = root

                for layer_key, keyword in layer_keywords.items():
                    if layer_key in layers and not layers[layer_key]['matched']:
                        if keyword in f:
                            layers[layer_key]['path'] = full_path
                            layers[layer_key]['matched'] = True

    return {
        'layers': layers,
        'spatial_folder': spatial_folder,
        'all_shp_files': all_shp_files
    }


class CheckThread(QThread):
    """检查线程"""
    progress_signal = Signal(str)
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, folder_path, water_system_shp=None, parent=None):
        super().__init__(parent)
        self.folder_path = folder_path
        self.water_system_shp = water_system_shp

    def run(self):
        try:
            checker = WaterSystemChecker(
                folder_path=self.folder_path,
                water_system_shp=self.water_system_shp
            )
            checker.progress_callback = lambda msg: self.progress_signal.emit(msg)
            results = checker.process_all()
            self.finished_signal.emit({
                'results': results,
                'water_records': checker.water_records,
                'all_records': checker.all_records,
                'water_codes': checker.water_codes,
                'water_names': checker.water_names,
                'water_code_to_name': checker.water_code_to_name,
                'water_original_columns': checker.water_original_columns,
                'has_water_system': checker.has_water_system
            })
        except Exception as e:
            self.error_signal.emit(str(e))


class CheckService(QObject):
    """检查业务服务"""
    progress = Signal(str)
    finished = Signal(dict)
    error = Signal(str)
    state_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = None
        self._folder_path = ""
        self._water_system_shp = None
        self._results = None
        self._state = "idle"

    @property
    def state(self) -> str:
        return self._state

    @property
    def results(self) -> dict:
        return self._results

    @property
    def is_running(self) -> bool:
        return self._state == "running"

    def start_check(self, folder_path: str, water_system_shp: str = None) -> bool:
        if self.is_running:
            return False

        self._folder_path = folder_path
        self._water_system_shp = water_system_shp

        self._state = "running"
        self.state_changed.emit(self._state)

        self._thread = CheckThread(folder_path, water_system_shp)
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

    @Slot(str)
    def _on_progress(self, msg: str):
        self.progress.emit(msg)

    @Slot(dict)
    def _on_finished(self, data: dict):
        self._results = data
        self._state = "finished"
        self.state_changed.emit(self._state)

        results = data['results']
        all_records = data['all_records']
        water_records = data['water_records']

        shp_cfg = get_shp_match_config()
        duanmian = [r for r in all_records if shp_cfg.get_layer_keyword('duanmian') in r.get('源文件', '')]
        fangzhi = [r for r in all_records if shp_cfg.get_layer_keyword('fangzhi') in r.get('源文件', '')]
        yinhuan = [r for r in all_records if shp_cfg.get_layer_keyword('yinhuan') in r.get('源文件', '')]

        self.finished.emit({
            'results': results,
            'duanmian': duanmian,
            'fangzhi': fangzhi,
            'yinhuan': yinhuan,
            'water': water_records,
            'has_water_system': data.get('has_water_system', True)
        })

    @Slot(str)
    def _on_error(self, msg: str):
        self._state = "error"
        self.state_changed.emit(self._state)
        self.error.emit(msg)
