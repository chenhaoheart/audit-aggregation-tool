# -*- coding: utf-8 -*-
"""
ArcGIS环境配置对话框
简化版：只配置路径和测试连接
"""

import os
import subprocess
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QFileDialog, QMessageBox, QFrame, QFormLayout, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPalette, QColor
from core.config_manager import ArcGISConfig
from core.theme_manager import get_theme_manager


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
                except Exception:
                    pass

        self.finished_signal.emit(False, "未检测到ArcGIS Pro Python环境，请手动配置路径。", "")


class ArcGISConfigDialog(QDialog):
    """ArcGIS环境配置对话框"""

    _test_success = False

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ArcGIS Python配置")
        self.setMinimumSize(550, 420)
        self.config = ArcGISConfig()
        self._test_success = False
        self.theme_manager = get_theme_manager()
        self._init_ui()

    def _init_ui(self):
        # 应用主题样式（支持暗黑主题）
        self.setStyleSheet(self.theme_manager.get_stylesheet())

        # 设置对话框背景色（QSS 无法控制 QDialog 原生背景，需用调色板）
        theme = self.theme_manager.get_current_theme()
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(theme['content_bg']))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # ========== 页面标题区 ==========
        header_card = QFrame()
        header_card.setObjectName("pageHeader")
        header_layout = QHBoxLayout(header_card)
        header_layout.setSpacing(16)
        header_layout.setContentsMargins(20, 16, 20, 16)

        accent_bar = QFrame()
        accent_bar.setObjectName("accentBar")
        accent_bar.setFixedWidth(4)
        header_layout.addWidget(accent_bar)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        page_title = QLabel("ArcGIS Python 配置")
        page_title.setObjectName("sectionHeaderLg")
        title_layout.addWidget(page_title)

        page_subtitle = QLabel("配置 ArcGIS Pro 的 Python 环境路径，用于 SHP 格式化功能")
        page_subtitle.setObjectName("pageSubtitle")
        title_layout.addWidget(page_subtitle)

        header_layout.addLayout(title_layout, 1)
        layout.addWidget(header_card)

        # ========== 配置卡片 ==========
        config_card = QFrame()
        config_card.setObjectName("card")
        config_inner = QVBoxLayout(config_card)
        config_inner.setSpacing(12)

        # 卡片标题
        card_title_layout = QHBoxLayout()
        card_title_layout.setSpacing(8)
        card_title = QLabel("Python 路径配置")
        card_title.setObjectName("sectionHeaderMd")
        card_title_layout.addWidget(card_title)
        card_title_layout.addStretch()
        config_inner.addLayout(card_title_layout)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

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

        hint_label = QLabel(
            "常见路径:\n"
            "C:\\Program Files\\ArcGIS\\Pro\\bin\\Python\\envs\\arcgispro-py3"
        )
        hint_label.setObjectName("secondaryLabel")
        form_layout.addRow("", hint_label)

        config_inner.addLayout(form_layout)
        layout.addWidget(config_card)

        # ========== 状态标签 ==========
        self.status_label = QLabel("")
        self.status_label.setObjectName("secondaryLabel")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # ========== 底部按钮 ==========
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

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
        self.cancel_btn.setObjectName("clearBtn")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _browse_path(self):
        folder = QFileDialog.getExistingDirectory(
            self, "选择ArcGIS Python目录",
            self.path_edit.text() or ""
        )
        if folder:
            folder = os.path.normpath(folder)
            self.path_edit.setText(folder)

    def _auto_detect(self):
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
        self.status_label.setStyleSheet(self.theme_manager.get_inline_style('env_info'))

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
        self._current_path = message
        self.status_label.setText(f"正在检测: {message}")

    def _on_detect_finished(self, success: bool, message: str, detected_path: str):
        if hasattr(self, '_loading_timer'):
            self._loading_timer.stop()
        self._current_path = ""

        self.test_btn.setEnabled(True)
        self.auto_btn.setEnabled(True)
        self.save_btn.setEnabled(True)

        if success:
            self._test_success = True
            self.path_edit.setText(detected_path)
            self.status_label.setText("✓ 检测成功")
            self.status_label.setStyleSheet(self.theme_manager.get_inline_style('env_success'))
            QMessageBox.information(self, "检测成功", message)
        else:
            self._test_success = False
            self.status_label.setText("✗ 未检测到")
            self.status_label.setStyleSheet(self.theme_manager.get_inline_style('env_error'))
            QMessageBox.warning(self, "未找到", message)

    def _test_connection(self):
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
        self.status_label.setStyleSheet(self.theme_manager.get_inline_style('env_info'))

        self.test_thread = TestConnectionThread(path)
        self.test_thread.finished_signal.connect(self._on_test_finished)
        self.test_thread.start()

    def _update_test_loading(self, dots_list):
        self._test_loading_index = (self._test_loading_index + 1) % len(dots_list)
        self.status_label.setText("正在测试连接 " + dots_list[self._test_loading_index])

    def _on_test_finished(self, success: bool, message: str, python_path: str):
        if hasattr(self, '_test_loading_timer'):
            self._test_loading_timer.stop()

        self.test_btn.setEnabled(True)
        self.auto_btn.setEnabled(True)
        self.save_btn.setEnabled(True)

        if success:
            self._test_success = True
            self.status_label.setText("✓ 测试成功")
            self.status_label.setStyleSheet(self.theme_manager.get_inline_style('env_success'))
            QMessageBox.information(self, "成功", message)
        else:
            self._test_success = False
            self.status_label.setText("✗ 测试失败")
            self.status_label.setStyleSheet(self.theme_manager.get_inline_style('env_error'))
            QMessageBox.warning(self, "测试失败", message)

    def _save_config(self):
        path = self.path_edit.text().strip()

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

        if self.config.save_python_path(path, verified=self._test_success):
            if self._test_success:
                QMessageBox.information(self, "成功", "配置已保存，环境已验证。")
            else:
                QMessageBox.information(self, "成功", "配置已保存。\n提示：建议先测试连接确认环境可用。")
            self.accept()
        else:
            QMessageBox.warning(self, "失败", "保存配置失败")

    def showEvent(self, event):
        """对话框显示事件——首次显示时播放入场动画"""
        super().showEvent(event)
        if not hasattr(self, '_animated'):
            self._animated = True
            self._animate_entrance()

    def _animate_entrance(self):
        """淡入入场动画：200ms, OutCubic"""
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        effect.setOpacity(0.0)

        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(200)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(lambda: self.setGraphicsEffect(None))
        anim.start()
        self._entrance_anim = anim  # 保持引用防止被 GC
