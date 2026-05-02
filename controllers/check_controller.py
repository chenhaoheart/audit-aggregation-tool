# -*- coding: utf-8 -*-
import os
from datetime import datetime
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget, QMessageBox, QFileDialog

from services.check_service import CheckService, scan_shp_files
from core.theme_manager import get_theme_manager


class CheckController(QObject):

    check_started = Signal()
    check_finished = Signal(dict)
    check_progress = Signal(str)
    check_error = Signal(str)
    scan_finished = Signal(dict)
    log_message = Signal(str)
    export_requested = Signal(dict)

    def __init__(self, parent_widget: QWidget = None, parent=None):
        super().__init__(parent)
        self._parent_widget = parent_widget
        self.service = CheckService(self)
        self.theme_manager = get_theme_manager()

        self.folder_path = ""
        self.water_system_shp = None
        self.spatial_folder = None
        self.check_results = None

        self.service.progress.connect(self._on_progress)
        self.service.finished.connect(self._on_finished)
        self.service.error.connect(self._on_error)
        self.service.state_changed.connect(self._on_state_changed)

    def _log(self, msg: str):
        self.log_message.emit(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def set_folder(self, path: str):
        self.folder_path = path

    def scan_folder(self, folder_path: str = None):
        path = folder_path or self.folder_path
        if not path:
            return
        self.folder_path = path
        scan_result = scan_shp_files(path)
        self.spatial_folder = scan_result.get('spatial_folder')
        self.scan_finished.emit(scan_result)
        matched_count = sum(1 for v in scan_result.get('layers', {}).values() if v.get('matched'))
        self._log(f"扫描完成: 发现 {matched_count} 个匹配图层")

    def start_check(self, spatial_folder: str, water_shp: str = None):
        if not spatial_folder:
            QMessageBox.warning(self._parent_widget, "警告", "请选择目标文件夹")
            return

        if not self.spatial_folder:
            self.spatial_folder = spatial_folder

        self.check_started.emit()
        self._log("开始检查...")

        self.water_system_shp = water_shp
        self.service.start_check(self.spatial_folder, water_shp)

    def cancel_check(self):
        self.service.cancel_check()

    def clear_results(self):
        self.folder_path = ""
        self.water_system_shp = None
        self.spatial_folder = None
        self.check_results = None
        self.service.clear_results()

    def select_layer_file(self, layer_key: str):
        from services.check_service import LAYER_TYPES
        layer_names = {lt['key']: lt['name'] for lt in LAYER_TYPES}
        file, _ = QFileDialog.getOpenFileName(
            self._parent_widget,
            f"选择{layer_names.get(layer_key, '')}文件",
            "", "Shp Files (*.shp)"
        )
        return file

    def export_excel(self):
        if not self.check_results:
            QMessageBox.warning(self._parent_widget, "警告", "没有可导出的结果")
            return None

        file, _ = QFileDialog.getSaveFileName(
            self._parent_widget, "导出Excel", "检查结果.xlsx", "Excel Files (*.xlsx)"
        )
        if file:
            self.export_requested.emit({
                'file_path': file,
                'results': self.check_results
            })
            return file
        return None

    def is_checking(self) -> bool:
        return self.service.is_running

    def _on_progress(self, msg: str):
        self._log(msg)
        self.check_progress.emit(msg)

    def _on_finished(self, data: dict):
        self.check_results = data
        self.check_finished.emit(data)

        results = data.get('results', [])
        passed = sum(1 for r in results if r['status'] == '通过')
        total = len(results)
        self._log(f"检查完成! 通过: {passed}/{total}")

    def _on_error(self, msg: str):
        self.check_error.emit(msg)
        self._log(f"错误: {msg}")
        QMessageBox.critical(self._parent_widget, "错误", f"检查失败:\n{msg}")

    def _on_state_changed(self, state: str):
        pass
