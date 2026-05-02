# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class Fubiao1Tab(QWidget):
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

    def update_table(self, records, merge_cells=None):
        if merge_cells is None:
            merge_cells = []

        col_count = 29

        header_row1 = [
            '序号', '1.县（区、市、旗）名称', '2.县（区、市、旗）代码',
            '3.乡镇名称', '4.乡镇代码', '5.名称', '6.代码',
            '7.类型', '8.人口', '9.河流名称', '10.河流代码',
            '风险隐患要素类别', '', '', '', '', '', '', '', '', '', '', '',
            '风险隐患影响类型', '', '', '', '',
            '28.备注'
        ]

        header_row2 = [
            '', '', '', '', '', '', '', '', '', '', '',
            '跨沟道路、桥涵', '',
            '塘（堰）坝', '',
            '多支齐汇', '',
            '局地河势与微地形', '', '', '', '',
            '22.沟滩占地',
            '23.溃决', '24.壅水', '25.顶托', '26.改道', '27.漫流',
            ''
        ]

        header_row3 = [
            '', '', '', '', '', '', '', '', '', '', '',
            '11.名称', '12.编码',
            '13.名称', '14.编码',
            '15.河流名称', '16.河流代码',
            '17.束窄', '18.急弯', '19.低洼地', '20.临河滑坡', '21.泥石流',
            '',
            '', '', '', '', '',
            ''
        ]

        data_headers = [
            '序号', '1.县（区、市、旗）名称', '2.县（区、市、旗）代码',
            '3.乡镇名称', '4.乡镇代码', '5.名称', '6.代码',
            '7.类型', '8.人口', '9.河流名称', '10.河流代码',
            '11.名称', '12.编码', '13.名称', '14.编码',
            '15.河流名称', '16.河流代码',
            '17.束窄', '18.急弯', '19.低洼地', '20.临河滑坡', '21.泥石流',
            '22.沟滩占地', '23.溃决', '24.壅水', '25.顶托', '26.改道', '27.漫流',
            '28.备注'
        ]

        self.table.clear()
        self.table.setColumnCount(col_count)
        self.table.setRowCount(len(records) + 3)

        for col in range(col_count):
            item1 = QTableWidgetItem(header_row1[col] if col < len(header_row1) else '')
            item1.setBackground(QColor(240, 240, 240))
            item1.setTextAlignment(Qt.AlignCenter)
            item1.setFlags(item1.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
            self.table.setItem(0, col, item1)

            item2 = QTableWidgetItem(header_row2[col] if col < len(header_row2) else '')
            item2.setBackground(QColor(240, 240, 240))
            item2.setTextAlignment(Qt.AlignCenter)
            item2.setFlags(item2.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
            self.table.setItem(1, col, item2)

            item3 = QTableWidgetItem(header_row3[col] if col < len(header_row3) else '')
            item3.setBackground(QColor(240, 240, 240))
            item3.setTextAlignment(Qt.AlignCenter)
            item3.setFlags(item3.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
            self.table.setItem(2, col, item3)

        for col in range(11):
            self.table.setSpan(0, col, 3, 1)
        self.table.setSpan(0, 11, 1, 12)
        self.table.setSpan(0, 23, 1, 5)
        self.table.setSpan(0, 28, 3, 1)

        self.table.setSpan(1, 11, 1, 2)
        self.table.setSpan(1, 13, 1, 2)
        self.table.setSpan(1, 15, 1, 2)
        self.table.setSpan(1, 17, 1, 5)
        for col in range(22, 28):
            self.table.setSpan(1, col, 2, 1)

        for row, record in enumerate(records):
            for col, header in enumerate(data_headers):
                value = record.get(header, '')
                if value == 'þ':
                    value = '☑'
                elif value == 'ý':
                    value = '☒'
                item = QTableWidgetItem(str(value) if value else '')
                if value == '☑' or value == '☒':
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row + 3, col, item)

        for merge_info in merge_cells:
            start_row, start_col, row_span, col_span = merge_info
            self.table.setSpan(start_row + 3, start_col, row_span, col_span)

        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()

        self.table.setRowHeight(0, 30)
        self.table.setRowHeight(1, 30)
        self.table.setRowHeight(2, 30)

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
        self.update_table(self.original_data)

    def clear_data(self):
        self.original_data = []
        self.table.clear()
        self.table.setRowCount(0)
