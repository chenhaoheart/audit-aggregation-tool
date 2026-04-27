# -*- coding: utf-8 -*-
"""
筛选栏组件
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton
from PySide6.QtCore import Signal
from core.theme_manager import get_theme_manager


class FilterBar(QWidget):
    """筛选栏组件"""

    filter_changed = Signal(dict)  # 筛选条件变化
    clear_requested = Signal()  # 清除筛选

    def __init__(self, show_name_filter: bool = True, parent=None):
        super().__init__(parent)
        self._show_name_filter = show_name_filter
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout()
        layout.setSpacing(8)

        # 菱形前缀图标
        theme = get_theme_manager().get_current_theme()
        prefix = QLabel("\u25c7")
        prefix.setStyleSheet(f"font-size: 14px; color: {theme['text_secondary']};")
        layout.addWidget(prefix)

        # 状态筛选
        self.status_combo = QComboBox()
        self.status_combo.addItems(["全部", "通过", "不通过"])
        self.status_combo.setFixedWidth(90)
        self.status_combo.setObjectName("statusFilterCombo")
        self.status_combo.currentTextChanged.connect(self._emit_filter)
        layout.addWidget(self.status_combo)

        # 代码筛选
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("河流代码...")
        self.code_edit.setFixedWidth(140)
        self.code_edit.setObjectName("codeFilterEdit")
        self.code_edit.textChanged.connect(self._emit_filter)
        layout.addWidget(self.code_edit)

        # 名称筛选（可选）
        if self._show_name_filter:
            self.name_edit = QLineEdit()
            self.name_edit.setPlaceholderText("河流名称...")
            self.name_edit.setFixedWidth(140)
            self.name_edit.setObjectName("nameFilterEdit")
            self.name_edit.textChanged.connect(self._emit_filter)
            layout.addWidget(self.name_edit)
        else:
            self.name_edit = None

        # 清除按钮
        clear_btn = QPushButton("清除")
        clear_btn.setFixedWidth(70)
        clear_btn.setObjectName("clearFilterBtn")
        clear_btn.setStyleSheet("font-size: 12px;")
        clear_btn.clicked.connect(self._clear_filter)
        layout.addWidget(clear_btn)

        layout.addStretch()
        self.setLayout(layout)

    def _emit_filter(self):
        conditions = {
            'status': self.status_combo.currentText(),
            'code': self.code_edit.text().strip()
        }
        if self.name_edit:
            conditions['name'] = self.name_edit.text().strip()
        self.filter_changed.emit(conditions)

    def _clear_filter(self):
        self.status_combo.setCurrentText("全部")
        self.code_edit.clear()
        if self.name_edit:
            self.name_edit.clear()
        self.clear_requested.emit()

    def get_filter_conditions(self) -> dict:
        conditions = {
            'status': self.status_combo.currentText(),
            'code': self.code_edit.text().strip()
        }
        if self.name_edit:
            conditions['name'] = self.name_edit.text().strip()
        return conditions
