# -*- coding: utf-8 -*-
"""
成果报表展示页面
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QMessageBox, QAbstractItemView,
    QGroupBox, QTextEdit, QScrollArea, QFrame, QSplitter, QDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from core.report_reader import load_all_reports
from core.data_validator import DataValidator


class ReportPage(QWidget):
    """成果报表展示页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.report_data = None
        self.validator = None
        self.validation_results = None
        self.result_dialog = None  # 校验结果弹窗
        self.original_data = {
            'fubiao1': [],
            'fubiao2': [],
            'fubiao3': []
        }
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        # 文件选择区域
        file_group = QGroupBox("数据加载")
        group_layout = QVBoxLayout()
        group_layout.setSpacing(10)

        # 第一行：文件夹选择
        file_row = QHBoxLayout()
        file_row.setSpacing(10)

        folder_label = QLabel("成果报表文件夹:")
        folder_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("选择包含附表Excel文件的文件夹...")
        self.folder_edit.setReadOnly(True)

        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.setFixedWidth(80)
        self.browse_btn.clicked.connect(self.select_folder)

        file_row.addWidget(folder_label)
        file_row.addWidget(self.folder_edit, 1)
        file_row.addWidget(self.browse_btn)
        group_layout.addLayout(file_row)

        # 第二行：按钮
        btn_row = QHBoxLayout()
        btn_row.setSpacing(15)
        btn_row.addStretch()

        self.load_btn = QPushButton("加载数据")
        self.load_btn.setFixedWidth(100)
        self.load_btn.clicked.connect(self.load_data)
        self.load_btn.setEnabled(False)

        self.export_btn = QPushButton("导出Excel")
        self.export_btn.setObjectName("exportBtn")
        self.export_btn.setFixedWidth(100)
        self.export_btn.clicked.connect(self.export_excel)
        self.export_btn.setEnabled(False)

        self.validate_btn = QPushButton("空间数据校验")
        self.validate_btn.setObjectName("validateBtn")
        self.validate_btn.setFixedWidth(120)
        self.validate_btn.clicked.connect(self.show_validation_dialog)
        self.validate_btn.setEnabled(False)

        self.clear_btn = QPushButton("清空")
        self.clear_btn.setObjectName("clearBtn")
        self.clear_btn.setFixedWidth(80)
        self.clear_btn.clicked.connect(self.clear_data)

        btn_row.addWidget(self.load_btn)
        btn_row.addWidget(self.export_btn)
        btn_row.addWidget(self.validate_btn)
        btn_row.addWidget(self.clear_btn)
        btn_row.addStretch()
        group_layout.addLayout(btn_row)

        file_group.setLayout(group_layout)
        layout.addWidget(file_group)

        # Tab区域
        self.tabs = QTabWidget()

        # 附表1 Tab
        self.fubiao1_tab = QWidget()
        self.setup_fubiao1_tab()
        self.tabs.addTab(self.fubiao1_tab, "附表1-防治对象名录")

        # 附表2 Tab
        self.fubiao2_tab = QWidget()
        self.setup_fubiao2_tab()
        self.tabs.addTab(self.fubiao2_tab, "附表2-跨沟道路桥涵")

        # 附表3 Tab
        self.fubiao3_tab = QWidget()
        self.setup_fubiao3_tab()
        self.tabs.addTab(self.fubiao3_tab, "附表3-沟滩占地")

        layout.addWidget(self.tabs, 1)

        # 底部状态
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def setup_fubiao1_tab(self):
        """设置附表1 Tab"""
        layout = QVBoxLayout()

        # 筛选区域
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        filter_label = QLabel("筛选:")
        filter_label.setStyleSheet("font-weight: bold; color: #2c3e50;")

        self.fubiao1_search_edit = QLineEdit()
        self.fubiao1_search_edit.setPlaceholderText("搜索名称...")
        self.fubiao1_search_edit.setFixedWidth(200)
        self.fubiao1_search_edit.textChanged.connect(self.apply_fubiao1_filter)

        clear_btn = QPushButton("清除筛选")
        clear_btn.setFixedWidth(80)
        clear_btn.clicked.connect(self.clear_fubiao1_filter)

        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.fubiao1_search_edit)
        filter_layout.addWidget(clear_btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # 表格
        self.fubiao1_table = QTableWidget()
        self.fubiao1_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.fubiao1_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.fubiao1_table.setAlternatingRowColors(True)
        self.fubiao1_table.horizontalHeader().setStretchLastSection(False)
        self.fubiao1_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        layout.addWidget(self.fubiao1_table)

        self.fubiao1_tab.setLayout(layout)

    def setup_fubiao2_tab(self):
        """设置附表2 Tab"""
        layout = QVBoxLayout()

        # 筛选区域
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        filter_label = QLabel("筛选:")
        filter_label.setStyleSheet("font-weight: bold; color: #2c3e50;")

        self.fubiao2_search_edit = QLineEdit()
        self.fubiao2_search_edit.setPlaceholderText("搜索名称...")
        self.fubiao2_search_edit.setFixedWidth(200)
        self.fubiao2_search_edit.textChanged.connect(self.apply_fubiao2_filter)

        clear_btn = QPushButton("清除筛选")
        clear_btn.setFixedWidth(80)
        clear_btn.clicked.connect(self.clear_fubiao2_filter)

        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.fubiao2_search_edit)
        filter_layout.addWidget(clear_btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # 表格
        self.fubiao2_table = QTableWidget()
        self.fubiao2_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.fubiao2_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.fubiao2_table.setAlternatingRowColors(True)
        self.fubiao2_table.horizontalHeader().setStretchLastSection(False)
        self.fubiao2_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        layout.addWidget(self.fubiao2_table)

        self.fubiao2_tab.setLayout(layout)

    def setup_fubiao3_tab(self):
        """设置附表3 Tab"""
        layout = QVBoxLayout()

        # 筛选区域
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        filter_label = QLabel("筛选:")
        filter_label.setStyleSheet("font-weight: bold; color: #2c3e50;")

        self.fubiao3_search_edit = QLineEdit()
        self.fubiao3_search_edit.setPlaceholderText("搜索名称...")
        self.fubiao3_search_edit.setFixedWidth(200)
        self.fubiao3_search_edit.textChanged.connect(self.apply_fubiao3_filter)

        clear_btn = QPushButton("清除筛选")
        clear_btn.setFixedWidth(80)
        clear_btn.clicked.connect(self.clear_fubiao3_filter)

        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.fubiao3_search_edit)
        filter_layout.addWidget(clear_btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # 表格
        self.fubiao3_table = QTableWidget()
        self.fubiao3_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.fubiao3_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.fubiao3_table.setAlternatingRowColors(True)
        self.fubiao3_table.horizontalHeader().setStretchLastSection(False)
        self.fubiao3_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        layout.addWidget(self.fubiao3_table)

        self.fubiao3_tab.setLayout(layout)

    def select_folder(self):
        """选择文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择成果报表文件夹")
        if folder:
            self.folder_edit.setText(folder)
            self.load_btn.setEnabled(True)

    def clear_data(self):
        """清空数据"""
        self.folder_edit.clear()
        self.report_data = None
        self.original_data = {'fubiao1': [], 'fubiao2': [], 'fubiao3': []}
        self.validation_results = None

        # 清空表格
        self.fubiao1_table.clear()
        self.fubiao1_table.setRowCount(0)
        self.fubiao2_table.clear()
        self.fubiao2_table.setRowCount(0)
        self.fubiao3_table.clear()
        self.fubiao3_table.setRowCount(0)

        # 重置按钮状态
        self.load_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.validate_btn.setEnabled(False)
        self.status_label.setText("")

    def load_data(self):
        """加载数据"""
        folder = self.folder_edit.text()
        if not folder:
            QMessageBox.warning(self, "警告", "请先选择文件夹")
            return

        if not os.path.exists(folder):
            QMessageBox.warning(self, "警告", "文件夹不存在")
            return

        # 加载数据
        self.report_data = load_all_reports(folder)

        # 检查是否有数据
        if self.report_data['missing']:
            QMessageBox.warning(
                self, "警告",
                f"以下文件未找到:\n" + "\n".join(self.report_data['missing'])
            )

        # 更新表格
        self.update_fubiao1_table()
        self.update_fubiao2_table()
        self.update_fubiao3_table()

        # 保存原始数据用于筛选
        self.original_data['fubiao1'] = self.report_data['fubiao1']['records']
        self.original_data['fubiao2'] = self.report_data['fubiao2']['records']
        self.original_data['fubiao3'] = self.report_data['fubiao3']['records']

        # 更新状态
        total = (
            len(self.report_data['fubiao1']['records']) +
            len(self.report_data['fubiao2']['records']) +
            len(self.report_data['fubiao3']['records'])
        )
        self.status_label.setText(f"共 {total} 条记录")
        self.load_btn.setEnabled(False)
        self.export_btn.setEnabled(total > 0)
        self.validate_btn.setEnabled(total > 0)

        QMessageBox.information(self, "完成", f"数据加载完成，共 {total} 条记录")

    def update_fubiao1_table(self, records=None):
        """更新附表1表格 - 支持3行合并表头和数据行合并"""
        if records is None:
            records = self.report_data['fubiao1']['records']

        # 获取数据行合并信息
        merge_cells = self.report_data['fubiao1'].get('merge_info', {}).get('merge_cells', [])

        # 总列数 29列
        col_count = 29

        # 第一行表头（按原始Excel结构）
        header_row1 = [
            '序号', '1.县（区、市、旗）名称', '2.县（区、市、旗）代码',
            '3.乡镇名称', '4.乡镇代码', '5.名称', '6.代码',
            '7.类型', '8.人口', '9.河流名称', '10.河流代码',
            '风险隐患要素类别', '', '', '', '', '', '', '', '', '', '', '',  # 列11-22，共12列
            '风险隐患影响类型', '', '', '', '',  # 列23-27，共5列
            '28.备注'  # 列28
        ]

        # 第二行表头
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

        # 第三行表头
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

        # 数据列名
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

        self.fubiao1_table.clear()
        self.fubiao1_table.setColumnCount(col_count)
        self.fubiao1_table.setRowCount(len(records) + 3)

        # 设置三行表头内容
        for col in range(col_count):
            item1 = QTableWidgetItem(header_row1[col] if col < len(header_row1) else '')
            item1.setBackground(QColor(240, 240, 240))
            item1.setTextAlignment(Qt.AlignCenter)
            item1.setFlags(item1.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
            self.fubiao1_table.setItem(0, col, item1)

            item2 = QTableWidgetItem(header_row2[col] if col < len(header_row2) else '')
            item2.setBackground(QColor(240, 240, 240))
            item2.setTextAlignment(Qt.AlignCenter)
            item2.setFlags(item2.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
            self.fubiao1_table.setItem(1, col, item2)

            item3 = QTableWidgetItem(header_row3[col] if col < len(header_row3) else '')
            item3.setBackground(QColor(240, 240, 240))
            item3.setTextAlignment(Qt.AlignCenter)
            item3.setFlags(item3.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
            self.fubiao1_table.setItem(2, col, item3)

        # ========== 合并第一行表头 ==========
        for col in range(11):
            self.fubiao1_table.setSpan(0, col, 3, 1)
        self.fubiao1_table.setSpan(0, 11, 1, 12)
        self.fubiao1_table.setSpan(0, 23, 1, 5)
        self.fubiao1_table.setSpan(0, 28, 3, 1)

        # ========== 合并第二行表头 ==========
        self.fubiao1_table.setSpan(1, 11, 1, 2)
        self.fubiao1_table.setSpan(1, 13, 1, 2)
        self.fubiao1_table.setSpan(1, 15, 1, 2)
        self.fubiao1_table.setSpan(1, 17, 1, 5)
        for col in range(22, 28):
            self.fubiao1_table.setSpan(1, col, 2, 1)

        # 设置数据行
        for row, record in enumerate(records):
            for col, header in enumerate(data_headers):
                value = record.get(header, '')
                item = QTableWidgetItem(str(value) if value else '')

                # 勾选列居中显示
                if value == '☑' or value == '☒':
                    item.setTextAlignment(Qt.AlignCenter)

                self.fubiao1_table.setItem(row + 3, col, item)

        # ========== 合并数据行单元格 ==========
        for merge_info in merge_cells:
            start_row, start_col, row_span, col_span = merge_info
            # 数据行从第4行开始（索引3）
            self.fubiao1_table.setSpan(start_row + 3, start_col, row_span, col_span)

        # 隐藏默认表头
        self.fubiao1_table.horizontalHeader().hide()
        self.fubiao1_table.verticalHeader().hide()

        # 设置表头行高度
        self.fubiao1_table.setRowHeight(0, 30)
        self.fubiao1_table.setRowHeight(1, 30)
        self.fubiao1_table.setRowHeight(2, 30)

    def update_fubiao2_table(self, records=None):
        """更新附表2表格"""
        if records is None:
            records = self.report_data['fubiao2']['records']
        headers = self.report_data['fubiao2']['headers']

        self.fubiao2_table.clear()
        self.fubiao2_table.setColumnCount(len(headers))
        self.fubiao2_table.setHorizontalHeaderLabels(headers)
        self.fubiao2_table.setRowCount(len(records))

        for row, record in enumerate(records):
            for col, header in enumerate(headers):
                value = record.get(header, '')
                item = QTableWidgetItem(str(value) if value else '')
                self.fubiao2_table.setItem(row, col, item)

        self.fubiao2_table.resizeColumnsToContents()

    def update_fubiao3_table(self, records=None):
        """更新附表3表格"""
        if records is None:
            records = self.report_data['fubiao3']['records']
        headers = self.report_data['fubiao3']['headers']

        self.fubiao3_table.clear()
        self.fubiao3_table.setColumnCount(len(headers))
        self.fubiao3_table.setHorizontalHeaderLabels(headers)
        self.fubiao3_table.setRowCount(len(records))

        for row, record in enumerate(records):
            for col, header in enumerate(headers):
                value = record.get(header, '')
                item = QTableWidgetItem(str(value) if value else '')
                self.fubiao3_table.setItem(row, col, item)

        self.fubiao3_table.resizeColumnsToContents()

    def apply_fubiao1_filter(self):
        """应用附表1筛选"""
        search_text = self.fubiao1_search_edit.text().strip().lower()
        if not search_text:
            self.update_fubiao1_table(self.original_data['fubiao1'])
            return

        filtered = []
        for record in self.original_data['fubiao1']:
            # 搜索名称列
            name = str(record.get('5.名称', '')).lower()
            if search_text in name:
                filtered.append(record)

        self.update_fubiao1_table(filtered)

    def clear_fubiao1_filter(self):
        """清除附表1筛选"""
        self.fubiao1_search_edit.clear()
        self.update_fubiao1_table(self.original_data['fubiao1'])

    def apply_fubiao2_filter(self):
        """应用附表2筛选"""
        search_text = self.fubiao2_search_edit.text().strip().lower()
        if not search_text:
            self.update_fubiao2_table(self.original_data['fubiao2'])
            return

        filtered = []
        for record in self.original_data['fubiao2']:
            name = str(record.get('5.名称', '')).lower()
            if search_text in name:
                filtered.append(record)

        self.update_fubiao2_table(filtered)

    def clear_fubiao2_filter(self):
        """清除附表2筛选"""
        self.fubiao2_search_edit.clear()
        self.update_fubiao2_table(self.original_data['fubiao2'])

    def apply_fubiao3_filter(self):
        """应用附表3筛选"""
        search_text = self.fubiao3_search_edit.text().strip().lower()
        if not search_text:
            self.update_fubiao3_table(self.original_data['fubiao3'])
            return

        filtered = []
        for record in self.original_data['fubiao3']:
            name = str(record.get('5.名称', '')).lower()
            if search_text in name:
                filtered.append(record)

        self.update_fubiao3_table(filtered)

    def clear_fubiao3_filter(self):
        """清除附表3筛选"""
        self.fubiao3_search_edit.clear()
        self.update_fubiao3_table(self.original_data['fubiao3'])

    def export_excel(self):
        """导出Excel - 保持原始格式（3行表头、合并单元格）"""
        if not self.report_data:
            QMessageBox.warning(self, "警告", "没有可导出的数据")
            return

        file, _ = QFileDialog.getSaveFileName(
            self, "导出Excel", "成果报表.xlsx", "Excel Files (*.xlsx)"
        )

        if file:
            try:
                import pandas as pd
                from openpyxl import Workbook
                from openpyxl.styles import Alignment, Font, Border, Side
                from openpyxl.utils import get_column_letter

                wb = Workbook()

                # ========== 导出附表1 ==========
                ws1 = wb.active
                ws1.title = '附表1-防治对象名录'

                records = self.report_data['fubiao1']['records']
                merge_cells = self.report_data['fubiao1'].get('merge_info', {}).get('merge_cells', [])

                # 第一行表头
                header_row1 = [
                    '序号', '1.县（区、市、旗）名称', '2.县（区、市、旗）代码',
                    '3.乡镇名称', '4.乡镇代码', '5.名称', '6.代码',
                    '7.类型', '8.人口', '9.河流名称', '10.河流代码',
                    '风险隐患要素类别', '', '', '', '', '', '', '', '', '', '', '',
                    '风险隐患影响类型', '', '', '', '',
                    '28.备注'
                ]

                # 第二行表头
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

                # 第三行表头
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

                # 数据列名
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

                # 写入表头
                ws1.append(header_row1)
                ws1.append(header_row2)
                ws1.append(header_row3)

                # 写入数据
                for record in records:
                    row_data = []
                    for header in data_headers:
                        val = record.get(header, '')
                        # 转换为Wingdings 2字体的字符
                        if val == '☑':
                            val = 'R'  # Wingdings 2 的 R 是带方框对号
                        elif val == '☒':
                            val = 'S'  # Wingdings 2 的 S 是带方框叉号
                        row_data.append(val)
                    ws1.append(row_data)

                # 合并第一行表头
                for col in range(1, 12):  # A1-K1 (列1-11)
                    ws1.merge_cells(start_row=1, start_column=col, end_row=3, end_column=col)
                ws1.merge_cells(start_row=1, start_column=12, end_row=1, end_column=23)  # L1-W1
                ws1.merge_cells(start_row=1, start_column=24, end_row=1, end_column=28)  # X1-AB1
                ws1.merge_cells(start_row=1, start_column=29, end_row=3, end_column=29)  # AC1-AC3

                # 合并第二行表头
                ws1.merge_cells(start_row=2, start_column=12, end_row=2, end_column=13)  # L2-M2
                ws1.merge_cells(start_row=2, start_column=14, end_row=2, end_column=15)  # N2-O2
                ws1.merge_cells(start_row=2, start_column=16, end_row=2, end_column=17)  # P2-Q2
                ws1.merge_cells(start_row=2, start_column=18, end_row=2, end_column=22)  # R2-V2
                for col in range(23, 29):  # W2-AB2
                    ws1.merge_cells(start_row=2, start_column=col, end_row=3, end_column=col)

                # 合并数据行单元格
                for merge_info in merge_cells:
                    start_row, start_col, row_span, col_span = merge_info
                    # 数据行从第4行开始（Excel行号为start_row + 4）
                    ws1.merge_cells(
                        start_row=start_row + 4,
                        start_column=start_col + 1,
                        end_row=start_row + 4 + row_span - 1,
                        end_column=start_col + col_span
                    )

                # 设置表头样式
                header_font = Font(bold=True)
                header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                thin_border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )

                for row in ws1.iter_rows(min_row=1, max_row=3, max_col=29):
                    for cell in row:
                        cell.font = header_font
                        cell.alignment = header_alignment
                        cell.border = thin_border

                # 设置数据行边框和勾选列字体
                wingdings2_font = Font(name='Wingdings 2')
                # 勾选列 (Excel列号17-27): 束窄、急弯、低洼地、临河滑坡、泥石流、沟滩占地、溃决、壅水、顶托、改道、漫流
                checkbox_cols = list(range(17, 28))  # Excel 1-based 列号

                for row in ws1.iter_rows(min_row=4, max_row=3 + len(records), max_col=29):
                    for cell in row:
                        cell.border = thin_border
                        cell.alignment = Alignment(vertical='center')
                        # 勾选列设置Wingdings 2字体
                        if cell.column in checkbox_cols:
                            cell.font = wingdings2_font
                            cell.alignment = Alignment(horizontal='center', vertical='center')

                # ========== 导出附表2 ==========
                ws2 = wb.create_sheet('附表2-跨沟道路桥涵')
                records2 = self.report_data['fubiao2']['records']
                headers2 = self.report_data['fubiao2']['headers']

                ws2.append(headers2)
                for record in records2:
                    row_data = [record.get(h, '') for h in headers2]
                    ws2.append(row_data)

                # 设置边框
                for row in ws2.iter_rows(min_row=1, max_row=1 + len(records2), max_col=len(headers2)):
                    for cell in row:
                        cell.border = thin_border
                        if cell.row == 1:
                            cell.font = header_font
                            cell.alignment = header_alignment

                # ========== 导出附表3 ==========
                ws3 = wb.create_sheet('附表3-沟滩占地')
                records3 = self.report_data['fubiao3']['records']
                headers3 = self.report_data['fubiao3']['headers']

                ws3.append(headers3)
                for record in records3:
                    row_data = [record.get(h, '') for h in headers3]
                    ws3.append(row_data)

                # 设置边框
                for row in ws3.iter_rows(min_row=1, max_row=1 + len(records3), max_col=len(headers3)):
                    for cell in row:
                        cell.border = thin_border
                        if cell.row == 1:
                            cell.font = header_font
                            cell.alignment = header_alignment

                wb.save(file)
                QMessageBox.information(self, "完成", f"已导出到:\n{file}")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")

    def show_validation_dialog(self):
        """显示空间数据校验弹窗"""
        if not self.report_data:
            QMessageBox.warning(self, "警告", "请先加载附表数据")
            return

        # 创建弹窗
        dialog = ValidationDialog(self)
        dialog.set_report_data(self.report_data)
        dialog.exec()


class ValidationDialog(QDialog):
    """空间数据校验弹窗"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("空间数据校验")
        self.setMinimumSize(800, 500)
        self.report_data = None
        self.validator = None
        self.validation_results = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 文件选择区域
        file_layout = QHBoxLayout()
        shp_label = QLabel("空间数据文件夹:")
        shp_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        self.shp_folder_edit = QLineEdit()
        self.shp_folder_edit.setPlaceholderText("选择包含shp文件的文件夹...")
        self.shp_folder_edit.setReadOnly(True)
        shp_browse_btn = QPushButton("浏览...")
        shp_browse_btn.setFixedWidth(80)
        shp_browse_btn.clicked.connect(self.select_shp_folder)

        self.validate_btn = QPushButton("开始校验")
        self.validate_btn.setFixedWidth(100)
        self.validate_btn.clicked.connect(self.start_validation)

        file_layout.addWidget(shp_label)
        file_layout.addWidget(self.shp_folder_edit, 1)
        file_layout.addWidget(shp_browse_btn)
        file_layout.addWidget(self.validate_btn)
        layout.addLayout(file_layout)

        # 进度/日志区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas, Monaco, monospace;
                font-size: 12px;
                border: 1px solid #3c3c3c;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.log_text)

        # 结果Tab区域
        self.result_tabs = QTabWidget()

        # 附表1对比结果Tab
        self.fubiao1_result_tab = QWidget()
        self.setup_fubiao1_result_tab()
        self.result_tabs.addTab(self.fubiao1_result_tab, "附表1 ↔ 防治对象分布P")

        # 附表2/3对比结果Tab
        self.fubiao23_result_tab = QWidget()
        self.setup_fubiao23_result_tab()
        self.result_tabs.addTab(self.fubiao23_result_tab, "附表2/3 ↔ 隐患要素分布L")

        layout.addWidget(self.result_tabs, 1)

        # 底部按钮
        btn_layout = QHBoxLayout()
        self.export_btn = QPushButton("导出报告")
        self.export_btn.clicked.connect(self.export_report)
        self.export_btn.setEnabled(False)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        btn_layout.addStretch()
        btn_layout.addWidget(self.export_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def setup_fubiao1_result_tab(self):
        """设置附表1对比结果Tab"""
        layout = QVBoxLayout()

        self.fubiao1_stats_label = QLabel("等待校验...")
        self.fubiao1_stats_label.setStyleSheet("font-weight: bold; color: #2c3e50; padding: 10px;")
        layout.addWidget(self.fubiao1_stats_label)

        self.fubiao1_result_table = QTableWidget()
        self.fubiao1_result_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.fubiao1_result_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.fubiao1_result_table.setAlternatingRowColors(True)
        self.fubiao1_result_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.fubiao1_result_table)

        self.fubiao1_result_tab.setLayout(layout)

    def setup_fubiao23_result_tab(self):
        """设置附表2/3对比结果Tab"""
        layout = QVBoxLayout()

        self.fubiao23_stats_label = QLabel("等待校验...")
        self.fubiao23_stats_label.setStyleSheet("font-weight: bold; color: #2c3e50; padding: 10px;")
        layout.addWidget(self.fubiao23_stats_label)

        self.fubiao23_result_table = QTableWidget()
        self.fubiao23_result_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.fubiao23_result_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.fubiao23_result_table.setAlternatingRowColors(True)
        self.fubiao23_result_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.fubiao23_result_table)

        self.fubiao23_result_tab.setLayout(layout)

    def set_report_data(self, report_data):
        """设置附表数据"""
        self.report_data = report_data

    def select_shp_folder(self):
        """选择空间数据文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择空间数据文件夹")
        if folder:
            self.shp_folder_edit.setText(folder)

    def append_log(self, msg):
        """追加日志"""
        self.log_text.append(msg)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def start_validation(self):
        """开始校验"""
        shp_folder = self.shp_folder_edit.text()
        if not shp_folder:
            QMessageBox.warning(self, "警告", "请先选择空间数据文件夹")
            return

        if not os.path.exists(shp_folder):
            QMessageBox.warning(self, "警告", "空间数据文件夹不存在")
            return

        # 清空
        self.log_text.clear()
        self.validation_results = None

        # 创建校验器
        self.validator = DataValidator()
        self.validator.progress_callback = self.append_log

        # 加载附表数据
        self.validator.load_fubiao(self.report_data)

        # 加载空间数据
        if not self.validator.load_shp_data(shp_folder):
            QMessageBox.warning(self, "警告", "空间数据加载失败")
            return

        # 执行校验
        self.validation_results = self.validator.validate_all()

        # 更新结果显示
        self.update_fubiao1_result()
        self.update_fubiao23_result()

        # 启用导出按钮
        self.export_btn.setEnabled(True)

    def update_fubiao1_result(self):
        """更新附表1对比结果"""
        r = self.validation_results.get('fubiao1_vs_fangzhi', {})

        stats_text = f"✓ 匹配成功: {r.get('match_count', 0)} 条   |   " \
                     f"⚠ 仅附表有: {r.get('fubiao_only_count', 0)} 条   |   " \
                     f"⚠ 仅shp有: {r.get('shp_only_count', 0)} 条"
        self.fubiao1_stats_label.setText(stats_text)

        headers = ['状态', '名称', '代码', '来源', '备注']
        all_records = []

        for item in r.get('matched', []):
            fubiao_rec = item.get('fubiao_record', {})
            all_records.append({
                '状态': '✓ 匹配',
                '名称': fubiao_rec.get('5.名称', ''),
                '代码': fubiao_rec.get('6.代码', ''),
                '来源': '附表+shp',
                '备注': ''
            })

        for rec in r.get('fubiao_only', []):
            all_records.append({
                '状态': '⚠ 仅附表',
                '名称': rec.get('5.名称', ''),
                '代码': rec.get('6.代码', ''),
                '来源': '附表',
                '备注': 'shp中未找到'
            })

        for rec in r.get('shp_only', []):
            all_records.append({
                '状态': '⚠ 仅shp',
                '名称': rec.get('名称', ''),
                '代码': rec.get('代码', ''),
                '来源': f"shp ({rec.get('_source_folder', '')})",
                '备注': '附表中未找到'
            })

        self.fubiao1_result_table.clear()
        self.fubiao1_result_table.setColumnCount(len(headers))
        self.fubiao1_result_table.setHorizontalHeaderLabels(headers)
        self.fubiao1_result_table.setRowCount(len(all_records))

        for row, rec in enumerate(all_records):
            for col, header in enumerate(headers):
                value = rec.get(header, '')
                item = QTableWidgetItem(str(value))
                if header == '状态':
                    if '✓' in value:
                        item.setForeground(QColor('#27ae60'))
                    elif '⚠' in value:
                        item.setForeground(QColor('#e74c3c'))
                self.fubiao1_result_table.setItem(row, col, item)

        self.fubiao1_result_table.resizeColumnsToContents()

    def update_fubiao23_result(self):
        """更新附表2/3对比结果"""
        r = self.validation_results.get('fubiao23_vs_yinhuan', {})

        stats_text = f"✓ 匹配成功: {r.get('match_count', 0)} 条   |   " \
                     f"⚠ 仅附表有: {r.get('fubiao_only_count', 0)} 条   |   " \
                     f"⚠ 仅shp有: {r.get('shp_only_count', 0)} 条"
        self.fubiao23_stats_label.setText(stats_text)

        headers = ['状态', '名称', '编码', '来源表', '来源', '备注']
        all_records = []

        for item in r.get('matched', []):
            fubiao_rec = item.get('fubiao_record', {})
            code = fubiao_rec.get('编码', fubiao_rec.get('编号', ''))
            all_records.append({
                '状态': '✓ 匹配',
                '名称': fubiao_rec.get('名称', ''),
                '编码': code,
                '来源表': fubiao_rec.get('_source_table', ''),
                '来源': '附表+shp',
                '备注': ''
            })

        for rec in r.get('fubiao_only', []):
            code = rec.get('编码', rec.get('编号', ''))
            all_records.append({
                '状态': '⚠ 仅附表',
                '名称': rec.get('名称', ''),
                '编码': code,
                '来源表': rec.get('_source_table', ''),
                '来源': '附表',
                '备注': 'shp中未找到'
            })

        for rec in r.get('shp_only', []):
            all_records.append({
                '状态': '⚠ 仅shp',
                '名称': rec.get('名称', ''),
                '编码': rec.get('编号', ''),
                '来源表': '',
                '来源': f"shp ({rec.get('_source_folder', '')})",
                '备注': '附表中未找到'
            })

        self.fubiao23_result_table.clear()
        self.fubiao23_result_table.setColumnCount(len(headers))
        self.fubiao23_result_table.setHorizontalHeaderLabels(headers)
        self.fubiao23_result_table.setRowCount(len(all_records))

        for row, rec in enumerate(all_records):
            for col, header in enumerate(headers):
                value = rec.get(header, '')
                item = QTableWidgetItem(str(value))
                if header == '状态':
                    if '✓' in value:
                        item.setForeground(QColor('#27ae60'))
                    elif '⚠' in value:
                        item.setForeground(QColor('#e74c3c'))
                self.fubiao23_result_table.setItem(row, col, item)

        self.fubiao23_result_table.resizeColumnsToContents()

    def export_report(self):
        """导出校验报告"""
        if not self.validation_results:
            QMessageBox.warning(self, "警告", "没有校验结果可导出")
            return

        file, _ = QFileDialog.getSaveFileName(
            self, "导出校验报告", "附表校验报告.xlsx", "Excel Files (*.xlsx)"
        )

        if file:
            try:
                from openpyxl import Workbook
                from openpyxl.styles import Font, PatternFill, Border, Side

                wb = Workbook()
                header_font = Font(bold=True)
                header_fill = PatternFill(start_color="E0E0E0", end_color="E0E0E0", fill_type="solid")
                thin_border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )

                # 附表1结果
                ws1 = wb.active
                ws1.title = "附表1对比结果"
                r1 = self.validation_results.get('fubiao1_vs_fangzhi', {})

                headers = ['状态', '名称', '代码', '来源', '备注']
                ws1.append(headers)
                for cell in ws1[1]:
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.border = thin_border

                for item in r1.get('matched', []):
                    rec = item.get('fubiao_record', {})
                    ws1.append(['匹配', rec.get('5.名称', ''), rec.get('6.代码', ''), '附表+shp', ''])

                for rec in r1.get('fubiao_only', []):
                    ws1.append(['仅附表', rec.get('5.名称', ''), rec.get('6.代码', ''), '附表', 'shp中未找到'])

                for rec in r1.get('shp_only', []):
                    ws1.append(['仅shp', rec.get('名称', ''), rec.get('代码', ''), rec.get('_source_folder', ''), '附表中未找到'])

                # 附表2/3结果
                ws2 = wb.create_sheet("附表23对比结果")
                r2 = self.validation_results.get('fubiao23_vs_yinhuan', {})

                headers2 = ['状态', '名称', '编码', '来源表', '来源', '备注']
                ws2.append(headers2)
                for cell in ws2[1]:
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.border = thin_border

                for item in r2.get('matched', []):
                    rec = item.get('fubiao_record', {})
                    code = rec.get('编码', rec.get('编号', ''))
                    ws2.append(['匹配', rec.get('名称', ''), code, rec.get('_source_table', ''), '附表+shp', ''])

                for rec in r2.get('fubiao_only', []):
                    code = rec.get('编码', rec.get('编号', ''))
                    ws2.append(['仅附表', rec.get('名称', ''), code, rec.get('_source_table', ''), '附表', 'shp中未找到'])

                for rec in r2.get('shp_only', []):
                    ws2.append(['仅shp', rec.get('名称', ''), rec.get('编号', ''), '', rec.get('_source_folder', ''), '附表中未找到'])

                wb.save(file)
                QMessageBox.information(self, "完成", f"已导出到:\n{file}")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")
                if fubiao1_only:
                    df = pd.DataFrame(fubiao1_only)
                    # 选择关键列
                    key_cols = ['5.名称', '6.代码', '1.县（区、市、旗）名称', '3.乡镇名称']
                    cols_to_export = [c for c in key_cols if c in df.columns]
                    if cols_to_export:
                        df = df[cols_to_export]
                    for r_idx, row in enumerate(df.values, 1):
                        for c_idx, val in enumerate(row, 1):
                            cell = ws_fubiao1_only.cell(row=r_idx + 1, column=c_idx, value=val)
                            cell.border = thin_border
                    for c_idx, col_name in enumerate(df.columns, 1):
                        cell = ws_fubiao1_only.cell(row=1, column=c_idx, value=col_name)
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.border = thin_border
                else:
                    ws_fubiao1_only['A1'] = "无记录"

                # 仅shp有的记录 - 防治对象分布P.shp
                ws_shp1_only = wb.create_sheet("防治对象仅shp有")
                shp1_only = r1.get('shp_only', [])
                if shp1_only:
                    df = pd.DataFrame(shp1_only)
                    # 选择关键列
                    key_cols = ['名称', '代码', '_source_folder']
                    cols_to_export = [c for c in key_cols if c in df.columns]
                    if cols_to_export:
                        df = df[cols_to_export]
                    for r_idx, row in enumerate(df.values, 1):
                        for c_idx, val in enumerate(row, 1):
                            cell = ws_shp1_only.cell(row=r_idx + 1, column=c_idx, value=val)
                            cell.border = thin_border
                    for c_idx, col_name in enumerate(df.columns, 1):
                        cell = ws_shp1_only.cell(row=1, column=c_idx, value=col_name)
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.border = thin_border
                else:
                    ws_shp1_only['A1'] = "无记录"

                # 仅附表有的记录 - 附表2/3
                ws_fubiao23_only = wb.create_sheet("附表23仅附表有")
                fubiao23_only = r2.get('fubiao_only', [])
                if fubiao23_only:
                    df = pd.DataFrame(fubiao23_only)
                    key_cols = ['名称', '编码', '编号', '_source_table']
                    cols_to_export = [c for c in key_cols if c in df.columns]
                    if cols_to_export:
                        df = df[cols_to_export]
                    for r_idx, row in enumerate(df.values, 1):
                        for c_idx, val in enumerate(row, 1):
                            cell = ws_fubiao23_only.cell(row=r_idx + 1, column=c_idx, value=val)
                            cell.border = thin_border
                    for c_idx, col_name in enumerate(df.columns, 1):
                        cell = ws_fubiao23_only.cell(row=1, column=c_idx, value=col_name)
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.border = thin_border
                else:
                    ws_fubiao23_only['A1'] = "无记录"

                # 仅shp有的记录 - 隐患要素分布L.shp
                ws_shp2_only = wb.create_sheet("隐患要素仅shp有")
                shp2_only = r2.get('shp_only', [])
                if shp2_only:
                    df = pd.DataFrame(shp2_only)
                    key_cols = ['名称', '编号', '_source_folder']
                    cols_to_export = [c for c in key_cols if c in df.columns]
                    if cols_to_export:
                        df = df[cols_to_export]
                    for r_idx, row in enumerate(df.values, 1):
                        for c_idx, val in enumerate(row, 1):
                            cell = ws_shp2_only.cell(row=r_idx + 1, column=c_idx, value=val)
                            cell.border = thin_border
                    for c_idx, col_name in enumerate(df.columns, 1):
                        cell = ws_shp2_only.cell(row=1, column=c_idx, value=col_name)
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.border = thin_border
                else:
                    ws_shp2_only['A1'] = "无记录"

                wb.save(file)
                QMessageBox.information(self, "完成", f"已导出到:\n{file}")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")