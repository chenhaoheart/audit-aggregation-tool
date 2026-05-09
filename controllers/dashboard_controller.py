# -*- coding: utf-8 -*-
from datetime import datetime
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget, QMessageBox, QFileDialog
from services.dashboard_service import DashboardService
from services.report_generator import build_report_html


class DashboardController(QObject):

    check_started = Signal()
    check_finished = Signal(dict)
    check_progress = Signal(str, str)
    check_error = Signal(str)
    check_cancelled = Signal()
    log_message = Signal(str)
    report_generated = Signal(str)

    def __init__(self, parent_widget: QWidget = None, parent=None):
        super().__init__(parent)
        self._parent_widget = parent_widget
        self.service = DashboardService(self)
        self.root_path = ""
        self.check_result = None

        self.service.progress.connect(self._on_progress)
        self.service.finished.connect(self._on_finished)
        self.service.error.connect(self._on_error)
        self.service.state_changed.connect(self._on_state_changed)

    def _log(self, msg: str):
        self.log_message.emit(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def set_root_path(self, path: str):
        self.root_path = path

    def start_check(self):
        if not self.root_path:
            QMessageBox.warning(self._parent_widget, "警告", "请选择示范小流域根目录")
            return
        self.check_result = None
        self.check_started.emit()
        self._log("开始Dashboard汇总检查...")
        self.service.start_check(self.root_path)

    def cancel_check(self):
        self.service.cancel_check()
        self.check_cancelled.emit()
        self._log("检查已取消")

    def clear_results(self):
        self.check_result = None
        self.service.clear_results()

    def generate_report(self):
        if not self.check_result:
            QMessageBox.warning(self._parent_widget, "提示", "请先执行检查操作")
            return
        try:
            report_html = build_report_html(self.check_result, self.root_path)
        except Exception as e:
            QMessageBox.critical(self._parent_widget, "失败", f"生成报告内容失败:\n{e}")
            self._log(f"报告生成失败: {e}")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self._parent_widget, "保存检查报告",
            f"Dashboard检查报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            "HTML 文件 (*.html);;所有文件 (*)"
        )
        if save_path:
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(report_html)
                QMessageBox.information(self._parent_widget, "成功", f"报告已保存至:\n{save_path}")
                self._log(f"报告已生成: {save_path}")
                import os
                os.startfile(save_path)
                self.report_generated.emit(save_path)
            except Exception as e:
                QMessageBox.critical(self._parent_widget, "失败", f"保存报告失败:\n{e}")

    def _on_progress(self, section, msg):
        self.check_progress.emit(section, msg)
        self._log(f"[{section}] {msg}")

    def _on_finished(self, data):
        self.check_result = data
        self.check_finished.emit(data)
        summary = data.get('summary', {})
        self._log(f"检查完成! 错误: {summary.get('total_errors', 0)}, 警告: {summary.get('total_warnings', 0)}")

    def _on_error(self, msg):
        self.check_error.emit(msg)
        self._log(f"错误: {msg}")
        QMessageBox.critical(self._parent_widget, "错误", f"检查失败:\n{msg}")

    def _on_state_changed(self, state):
        pass
