# -*- coding: utf-8 -*-
"""
数据检查业务服务
"""

from PySide6.QtCore import QObject, QThread, Signal, Slot
from core.checker import WaterSystemChecker


class CheckThread(QThread):
    """检查线程"""
    progress_signal = Signal(str)
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, folder_path, water_system_shp, parent=None):
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
                'water_original_columns': checker.water_original_columns
            })
        except Exception as e:
            self.error_signal.emit(str(e))


class CheckService(QObject):
    """检查业务服务"""
    progress = Signal(str)
    finished = Signal(dict)
    error = Signal(str)
    state_changed = Signal(str)  # idle, running, finished, error

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = None
        self._folder_path = ""
        self._water_system_shp = ""
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

    def start_check(self, folder_path: str, water_system_shp: str) -> bool:
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

        # 分离数据
        results = data['results']
        all_records = data['all_records']
        water_records = data['water_records']

        duanmian = [r for r in all_records if '断面平面位置' in r.get('源文件', '')]
        fangzhi = [r for r in all_records if '防治对象分布' in r.get('源文件', '')]
        yinhuan = [r for r in all_records if '隐患要素分布' in r.get('源文件', '')]

        self.finished.emit({
            'results': results,
            'duanmian': duanmian,
            'fangzhi': fangzhi,
            'yinhuan': yinhuan,
            'water': water_records
        })

    @Slot(str)
    def _on_error(self, msg: str):
        self._state = "error"
        self.state_changed.emit(self._state)
        self.error.emit(msg)