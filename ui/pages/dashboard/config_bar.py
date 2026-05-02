# -*- coding: utf-8 -*-
import os
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PySide6.QtCore import Signal, Qt
from core.effects_manager import ButtonGlowHelper


class DashboardConfigBar(QFrame):

    folder_selected = Signal(str)
    start_clicked = Signal()
    clear_clicked = Signal()
    log_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 16, 12, 16)

        row = QHBoxLayout()
        row.setSpacing(12)

        lbl = QLabel("根目录:")
        lbl.setObjectName("boldLabel")
        row.addWidget(lbl, 0, Qt.AlignVCenter)

        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("选择示范小流域根目录...")
        self.folder_edit.setReadOnly(True)
        default_root = r"D:\github\空间数据检查桌面版-主题-design-2026\青海24示范小流域-药草沟-20260313"
        if os.path.exists(default_root):
            self.folder_edit.setText(default_root)
        row.addWidget(self.folder_edit, 1)

        browse_btn = QPushButton("浏览")
        browse_btn.setFixedWidth(64)
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.clicked.connect(self._on_browse)
        row.addWidget(browse_btn)

        self.start_btn = QPushButton("  一键检查  ")
        self.start_btn.setFixedWidth(110)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.clicked.connect(self.start_clicked.emit)
        self.start_btn.setEnabled(bool(self.folder_edit.text()))
        ButtonGlowHelper.install(self.start_btn)
        row.addWidget(self.start_btn)

        self.clear_btn = QPushButton("清空")
        self.clear_btn.setFixedWidth(56)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setObjectName("clearBtn")
        self.clear_btn.clicked.connect(self.clear_clicked.emit)
        row.addWidget(self.clear_btn)

        self.log_btn = QPushButton("日志")
        self.log_btn.setFixedWidth(50)
        self.log_btn.setCursor(Qt.PointingHandCursor)
        self.log_btn.setObjectName("logToggleBtn")
        self.log_btn.clicked.connect(self.log_clicked.emit)
        row.addWidget(self.log_btn)

        layout.addLayout(row)

    def _on_browse(self):
        from PySide6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "选择示范小流域根目录")
        if folder:
            self.folder_edit.setText(folder)
            self.start_btn.setEnabled(True)
            self.folder_selected.emit(folder)

    def get_folder_path(self) -> str:
        return self.folder_edit.text()

    def set_folder_path(self, path: str):
        self.folder_edit.setText(path)
        self.start_btn.setEnabled(bool(path))

    def set_start_enabled(self, enabled: bool):
        self.start_btn.setEnabled(enabled)

    def clear(self):
        self.folder_edit.clear()
        self.start_btn.setEnabled(False)
