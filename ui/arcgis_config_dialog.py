# -*- coding: utf-8 -*-
"""
ArcGIS环境配置对话框
简化版：只配置路径和测试连接
"""

import os
import subprocess
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QFileDialog, QMessageBox, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from core.config_manager import ArcGISConfig


class TestConnectionThread(QThread):
    """后台测试连接线程"""
    finished_signal = Signal(bool, str, str)  # 成功, 消息, python路径

    def __init__(self, python_path: str, parent=None):
        super().__init__(parent)
        self.python_path = python_path

    def run(self):
        python_exe = os.path.join(self.python_path, "python.exe")
        if not os.path.exists(python_exe):
            python_exe = os.path.join(self.python_path, "Scripts", "python.exe")
            if not os.path.exists(python_exe):
                self.finished_signal.emit(False, f"未找到 python.exe\n路径: {self.python_path}", "")
                return

        try:
            result = subprocess.run(
                [python_exe, "-c", "import arcpy; print('OK')"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and "OK" in result.stdout:
                self.finished_signal.emit(True, f"ArcGIS Python环境正常!\n\n路径: {python_exe}", python_exe)
            else:
                self.finished_signal.emit(False, f"无法导入arcpy模块。\n\n错误: {result.stderr}", python_exe)
        except subprocess.TimeoutExpired:
            self.finished_signal.emit(False, "测试连接超时（30秒）", python_exe)
        except Exception as e:
            self.finished_signal.emit(False, f"测试失败: {e}", python_exe)


class AutoDetectThread(QThread):
    """后台自动检测线程"""
    progress_signal = Signal(str)  # 进度消息
    finished_signal = Signal(bool, str, str)  # 成功, 消息, 检测到的路径

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        default_paths = [
            r"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3",
            r"C:\Program Files (x86)\ArcGIS\Pro\bin\Python\envs\arcgispro-py3",
            r"C:\Python27\ArcGIS10.8",
        ]

        for p in default_paths:
            self.progress_signal.emit(f"正在检测: {p}")
            python_exe = os.path.join(p, "python.exe")
            if os.path.exists(python_exe):
                try:
                    result = subprocess.run(
                        [python_exe, "-c", "import arcpy; print('OK')"],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode == 0 and "OK" in result.stdout:
                        self.finished_signal.emit(True, f"已找到ArcGIS Python:\n{p}", p)
                        return
                except:
                    pass

        self.finished_signal.emit(False, "未检测到ArcGIS Pro Python环境，请手动配置路径。", "")


class ArcGISConfigDialog(QDialog):
    """ArcGIS环境配置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ArcGIS Python配置")
        self.setMinimumWidth(500)
        self.config = ArcGISConfig()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # 说明文字
        info_label = QLabel(
            "配置ArcGIS Pro的Python环境路径。\n\n"
            "SHP格式化功能需要通过ArcGIS Python执行。"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #7f8c8d; font-size: 14px; padding: 10px; background: #f8f9fa; border-radius: 5px;")
        layout.addWidget(info_label)

        # 配置区域
        config_group = QGroupBox("Python路径配置")
        form_layout = QFormLayout()

        # Python路径
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("例如: C:\\Program Files\\ArcGIS\\Pro\\bin\\Python\\envs\\arcgispro-py3")
        self.path_edit.setText(self.config.python_path or "")

        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.setFixedWidth(80)
        self.browse_btn.clicked.connect(self._browse_path)

        path_layout.addWidget(self.path_edit, 1)
        path_layout.addWidget(self.browse_btn)

        form_layout.addRow("Python目录:", path_layout)

        # 常见路径提示
        hint_label = QLabel(
            "常见路径:\n"
            "C:\\Program Files\\ArcGIS\\Pro\\bin\\Python\\envs\\arcgispro-py3"
        )
        hint_label.setStyleSheet("color: #95a5a6; font-size: 11px;")
        form_layout.addRow("", hint_label)

        config_group.setLayout(form_layout)
        layout.addWidget(config_group)

        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 14px; padding: 5px;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # 按钮
        btn_layout = QHBoxLayout()

        self.test_btn = QPushButton("测试连接")
        self.test_btn.clicked.connect(self._test_connection)
        btn_layout.addWidget(self.test_btn)

        self.auto_btn = QPushButton("自动检测")
        self.auto_btn.clicked.connect(self._auto_detect)
        btn_layout.addWidget(self.auto_btn)

        btn_layout.addStretch()

        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self._save_config)
        btn_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _browse_path(self):
        """浏览选择Python目录"""
        folder = QFileDialog.getExistingDirectory(
            self, "选择ArcGIS Python目录",
            self.path_edit.text() or ""
        )
        if folder:
            # 规范化路径格式
            folder = os.path.normpath(folder)
            self.path_edit.setText(folder)

    def _auto_detect(self):
        """自动检测ArcGIS Python路径（异步版本）"""
        self.test_btn.setEnabled(False)
        self.auto_btn.setEnabled(False)
        self.save_btn.setEnabled(False)

        loading_dots = ["......", "o.....", ".o....", "..o...", "...o..", "....o.", ".....o", "......"]
        self._loading_index = 0
        self._loading_timer = QTimer(self)
        self._loading_timer.timeout.connect(lambda: self._update_auto_loading(loading_dots))
        self._loading_timer.start(150)
        self._current_path = ""

        self.status_label.setText("正在自动检测 " + loading_dots[0])
        self.status_label.setStyleSheet("color: #3498db; font-size: 14px; padding: 5px;")

        self.auto_detect_thread = AutoDetectThread()
        self.auto_detect_thread.progress_signal.connect(self._on_detect_progress)
        self.auto_detect_thread.finished_signal.connect(self._on_detect_finished)
        self.auto_detect_thread.start()

    def _update_auto_loading(self, dots_list):
        self._loading_index = (self._loading_index + 1) % len(dots_list)
        if self._current_path:
            self.status_label.setText(f"正在检测: {self._current_path} {dots_list[self._loading_index]}")
        else:
            self.status_label.setText("正在自动检测 " + dots_list[self._loading_index])

    def _on_detect_progress(self, message: str):
        """自动检测进度回调"""
        self._current_path = message
        self.status_label.setText(f"正在检测: {message}")

    def _on_detect_finished(self, success: bool, message: str, detected_path: str):
        """自动检测完成回调"""
        if hasattr(self, '_loading_timer'):
            self._loading_timer.stop()
        self._current_path = ""

        self.test_btn.setEnabled(True)
        self.auto_btn.setEnabled(True)
        self.save_btn.setEnabled(True)

        if success:
            self.path_edit.setText(detected_path)
            self.status_label.setText("✓ 检测成功")
            self.status_label.setStyleSheet("color: #27ae60; font-size: 14px; padding: 5px;")
            QMessageBox.information(self, "检测成功", message)
        else:
            self.status_label.setText("✗ 未检测到")
            self.status_label.setStyleSheet("color: #e74c3c; font-size: 14px; padding: 5px;")
            QMessageBox.warning(self, "未找到", message)

    def _test_connection(self):
        """测试连接（异步版本）"""
        path = self.path_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "提示", "请先输入Python目录路径")
            return

        path = os.path.normpath(path)
        self.path_edit.setText(path)

        if not os.path.exists(path):
            QMessageBox.warning(self, "错误", f"指定的目录不存在:\n{path}")
            return

        self.test_btn.setEnabled(False)
        self.auto_btn.setEnabled(False)
        self.save_btn.setEnabled(False)

        loading_dots = ["......", "o.....", ".o....", "..o...", "...o..", "....o.", ".....o", "......"]
        self._test_loading_index = 0
        self._test_loading_timer = QTimer(self)
        self._test_loading_timer.timeout.connect(lambda: self._update_test_loading(loading_dots))
        self._test_loading_timer.start(150)

        self.status_label.setText("正在测试连接 " + loading_dots[0])
        self.status_label.setStyleSheet("color: #3498db; font-size: 14px; padding: 5px;")

        self.test_thread = TestConnectionThread(path)
        self.test_thread.finished_signal.connect(self._on_test_finished)
        self.test_thread.start()

    def _update_test_loading(self, dots_list):
        self._test_loading_index = (self._test_loading_index + 1) % len(dots_list)
        self.status_label.setText("正在测试连接 " + dots_list[self._test_loading_index])

    def _on_test_finished(self, success: bool, message: str, python_path: str):
        """测试连接完成回调"""
        if hasattr(self, '_test_loading_timer'):
            self._test_loading_timer.stop()

        self.test_btn.setEnabled(True)
        self.auto_btn.setEnabled(True)
        self.save_btn.setEnabled(True)

        if success:
            self.status_label.setText("✓ 测试成功")
            self.status_label.setStyleSheet("color: #27ae60; font-size: 14px; padding: 5px;")
            QMessageBox.information(self, "成功", message)
        else:
            self.status_label.setText(f"✗ 测试失败")
            self.status_label.setStyleSheet("color: #e74c3c; font-size: 14px; padding: 5px;")
            QMessageBox.warning(self, "测试失败", message)

    def _save_config(self):
        """保存配置"""
        path = self.path_edit.text().strip()

        # 规范化路径格式
        if path:
            path = os.path.normpath(path)
            self.path_edit.setText(path)

        if path and not os.path.exists(path):
            reply = QMessageBox.question(
                self, "确认",
                "指定的目录不存在，是否仍要保存？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        if self.config.save_python_path(path):
            QMessageBox.information(self, "成功", "配置已保存。")
            self.accept()
        else:
            QMessageBox.warning(self, "失败", "保存配置失败")