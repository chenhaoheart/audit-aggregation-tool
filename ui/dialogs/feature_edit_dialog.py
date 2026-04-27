# -*- coding: utf-8 -*-
"""
要素属性编辑对话框
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QScrollArea, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor


class FeatureEditDialog(QDialog):
    """要素属性编辑对话框"""

    properties_updated = Signal(dict)

    def __init__(self, layer_id: str, properties: dict, parent=None):
        super().__init__(parent)
        self.layer_id = layer_id
        self.original_properties = properties.copy()
        self.edited_properties = properties.copy()
        self._skip_keys = ['_original_columns', '_status', 'geometry']
        self._feature_id = properties.get('id', None)

        self.setWindowTitle(f"编辑要素属性 - {layer_id}")
        self.setMinimumSize(600, 500)
        self.setWindowFlags(self.windowFlags() | Qt.Dialog)

        self._init_ui()

    def _init_ui(self):
        """初始化界面"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 20, 20, 20)

        header = QFrame()
        header.setObjectName("card")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)

        title = QLabel(f"图层: {self.layer_id}")
        title.setObjectName("sectionHeaderMd")
        header_layout.addWidget(title)

        count_label = QLabel(f"共 {len([k for k in self.original_properties.keys() if k not in self._skip_keys])} 个属性")
        count_label.setObjectName("pageSubtitle")
        header_layout.addStretch()
        header_layout.addWidget(count_label)

        main_layout.addWidget(header)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        scroll_content = QWidget()
        scroll_content.setObjectName("cardInnerPanel")
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["属性名", "属性值"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setDefaultSectionSize(22)
        self.table.verticalHeader().setMinimumSectionSize(18)
        self.table.verticalHeader().setVisible(False)
        self.table.setContentsMargins(0, 0, 0, 0)

        filtered_props = {k: v for k, v in self.original_properties.items() if k not in self._skip_keys}
        self.table.setRowCount(len(filtered_props))

        for row, (key, value) in enumerate(filtered_props.items()):
            key_item = QTableWidgetItem(str(key))
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
            key_item.setToolTip(str(key))
            self.table.setItem(row, 0, key_item)

            value_str = str(value) if value is not None else ''
            value_item = QTableWidgetItem(value_str)
            value_item.setToolTip(value_str)
            self.table.setItem(row, 1, value_item)

        layout.addWidget(self.table)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        save_btn = QPushButton("保存")
        save_btn.setFixedWidth(100)
        save_btn.clicked.connect(self._on_save)

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedWidth(100)
        cancel_btn.setObjectName("clearBtn")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()

        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def _on_save(self):
        """保存编辑"""
        self.edited_properties = {}

        for row in range(self.table.rowCount()):
            key_item = self.table.item(row, 0)
            value_item = self.table.item(row, 1)

            if key_item and value_item:
                key = key_item.text()
                value = value_item.text()
                self.edited_properties[key] = value

        for key in self._skip_keys:
            if key in self.original_properties:
                self.edited_properties[key] = self.original_properties[key]

        if self._feature_id is not None:
            self.edited_properties['id'] = self._feature_id

        self.properties_updated.emit(self.edited_properties)
        self.accept()

    def get_edited_properties(self) -> dict:
        """获取编辑后的属性"""
        return self.edited_properties
