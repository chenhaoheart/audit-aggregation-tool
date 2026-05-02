# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal, Qt
from core.effects_manager import ButtonGlowHelper


class DashboardHeader(QFrame):

    report_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 16, 20, 16)

        accent = QFrame()
        accent.setObjectName("accentBar")
        accent.setFixedWidth(4)
        layout.addWidget(accent)

        left = QVBoxLayout()
        left.setSpacing(4)
        title = QLabel("Dashboard 汇总检查")
        title.setObjectName("sectionHeaderLg")
        left.addWidget(title)
        sub = QLabel("选择示范小流域根目录，一键执行全部检查与交叉校验，生成可视化报告")
        sub.setObjectName("pageSubtitle")
        left.addWidget(sub)
        layout.addLayout(left, 1)

        right_btns = QHBoxLayout()
        right_btns.setSpacing(8)
        self.report_btn = QPushButton("  生成报告  ")
        self.report_btn.setCursor(Qt.PointingHandCursor)
        self.report_btn.setEnabled(False)
        self.report_btn.clicked.connect(self.report_clicked.emit)
        ButtonGlowHelper.install(self.report_btn)
        right_btns.addWidget(self.report_btn)
        layout.addLayout(right_btns)

    def set_report_enabled(self, enabled: bool):
        self.report_btn.setEnabled(enabled)
