# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt


class Fubiao3Tab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_data = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 4, 0, 4)

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        filter_label = QLabel("筛选:")
        filter_label.setObjectName("boldLabel")

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索名称...")
        self.search_edit.setFixedWidth(200)
        self.search_edit.textChanged.connect(self.apply_filter)

        clear_btn = QPushButton("清除筛选")
        clear_btn.setFixedWidth(80)
        clear_btn.clicked.connect(self.clear_filter)

        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.search_edit)
        filter_layout.addWidget(clear_btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def update_table(self, records, headers):
        self.table.clear()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(records))

        for row, record in enumerate(records):
            for col, header in enumerate(headers):
                value = record.get(header, '')
                item = QTableWidgetItem(str(value) if value else '')
                self.table.setItem(row, col, item)

        self.table.resizeColumnsToContents()

    def set_original_data(self, data):
        self.original_data = data

    def apply_filter(self):
        search_text = self.search_edit.text().strip().lower()
        if not search_text:
            return
        filtered = []
        for record in self.original_data:
            name = str(record.get('5.名称', '')).lower()
            if search_text in name:
                filtered.append(record)
        self.search_edit.blockSignals(True)
        self.update_table(filtered)
        self.search_edit.blockSignals(False)

    def clear_filter(self):
        self.search_edit.clear()

    def clear_data(self):
        self.original_data = []
        self.table.clear()
        self.table.setRowCount(0)
