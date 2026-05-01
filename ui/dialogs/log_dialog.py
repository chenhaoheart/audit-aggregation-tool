# -*- coding: utf-8 -*-
"""
日志对话框
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QGraphicsOpacityEffect
from PySide6.QtCore import Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPalette, QColor
from core.theme_manager import get_theme_manager


class LogDialog(QDialog):
    """日志输出对话框"""

    log_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("日志输出")
        self.setMinimumSize(700, 400)

        # 设置主题样式（支持暗黑主题）
        self.theme_manager = get_theme_manager()
        theme = self.theme_manager.get_current_theme()
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(theme['content_bg']))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        self.setStyleSheet(self.theme_manager.get_stylesheet())

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setObjectName("logText")
        layout.addWidget(self.log_text)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self.log_text.clear)
        btn_layout.addWidget(clear_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def append_log(self, msg: str):
        self.log_text.append(msg)

    def clear(self):
        self.log_text.clear()

    def closeEvent(self, event):
        if hasattr(self, '_entrance_anim') and self._entrance_anim:
            self._entrance_anim.stop()
            self._entrance_anim = None
        self.setGraphicsEffect(None)
        event.accept()

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