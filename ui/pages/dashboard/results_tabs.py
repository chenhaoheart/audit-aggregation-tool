# -*- coding: utf-8 -*-
import csv
import os
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFileDialog, QApplication
)
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QFont, QKeySequence
from ui.components.dashboard_widgets import (
    HorizontalSwipeCards, SpatialResultGrid,
    PhotoMatchDashboard, CrossCheckListPanel, StatMetricCard
)


class DashboardResultsTabs(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("resultsContainer")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        header_widget = QWidget()
        header_row = QHBoxLayout(header_widget)
        header_row.setSpacing(12)
        header_row.setContentsMargins(0, 0, 0, 0)
        section_header = QLabel("\U0001f4ca 结果详情")
        section_header.setObjectName("sectionHeaderSm")
        header_row.addWidget(section_header)
        header_row.addStretch()
        self.swipe_cards = HorizontalSwipeCards()
        header_row.addWidget(self.swipe_cards.dots_container)
        layout.addWidget(header_widget)

        card_configs = [
            ("fubiao_card", "\ud83d\udccb", "附表1/2/3详情", "_setup_fubiao_content"),
            ("spatial_card", "\ud83d\uddfa\ufe0f", "空间数据详情", "_setup_spatial_content"),
            ("section_card", "\ud83d\udcd0", "断面数据详情", "_setup_section_content"),
            ("photo_card", "\ud83d\udcf7", "照片匹配详情", "_setup_photo_content"),
            ("cross_card", "\ud83d\udd17", "交叉校验详情", "_setup_cross_content"),
        ]

        self.result_cards = {}
        self._card_index_map = {}

        for i, (attr_name, icon, title, setup_method) in enumerate(card_configs):
            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            content_layout.setContentsMargins(16, 16, 16, 16)
            content_layout.setSpacing(8)
            content_inner = QWidget()
            getattr(self, setup_method)(content_inner)
            content_layout.addWidget(content_inner, 1)
            self.swipe_cards.add_card(title, icon, content_widget)
            self.result_cards[attr_name] = i
            self._card_index_map[attr_name] = i
            setattr(self, attr_name.replace('_card', '_content'), content_inner)

        layout.addWidget(self.swipe_cards, 1)

    def _setup_fubiao_content(self, widget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.fubiao_table = QTableWidget()
        self.fubiao_table.setObjectName("minimalResultTable")
        self.fubiao_table.setColumnCount(6)
        self.fubiao_table.setHorizontalHeaderLabels(["序号", "表名", "字段名", "错误类型", "错误描述", "当前值"])
        self.fubiao_table.horizontalHeader().setStretchLastSection(True)
        self.fubiao_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        for i, w in enumerate([45, 55, 110, 75, 280]):
            self.fubiao_table.setColumnWidth(i, w)
        self.fubiao_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.fubiao_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.fubiao_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.fubiao_table.verticalHeader().setVisible(False)
        self.fubiao_table.setAlternatingRowColors(True)
        self._enable_table_copy(self.fubiao_table)
        layout.addWidget(self.fubiao_table)

    def _setup_spatial_content(self, widget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.spatial_grid = SpatialResultGrid()
        self.spatial_grid.setMinimumHeight(200)
        layout.addWidget(self.spatial_grid)

    def _setup_section_content(self, widget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        stats_grid = QWidget()
        stats_layout = QHBoxLayout(stats_grid)
        stats_layout.setSpacing(10)
        stats_layout.setContentsMargins(0, 0, 0, 0)

        stat_defs = [
            ("\u603b\u65ad\u9762\u6570", "\U0001f4d0", "text_primary"),
            ("\u603b\u6d4b\u70b9\u6570", "\U0001f4cf", "text_primary"),
            ("\u5f02\u5e38\u65ad\u9762\u6570", "\u26a0\ufe0f", "error_text"),
            ("\u6821\u9a8c\u9519\u8bef\u6570", "\u274c", "error_text"),
            ("\u6709\u5750\u6807\u70b9\u6570", "\U0001f310", "text_primary"),
            ("\u5206\u7c7b\u6570", "\U0001f3f7\ufe0f", "text_primary"),
        ]

        self.section_stat_cards = {}
        for label, icon, accent in stat_defs:
            card = StatMetricCard(label, icon, accent)
            card.set_value("--", "", None)
            card.setMinimumWidth(100)
            font = card.value_label.font()
            font.setPointSize(12)
            card.value_label.setFont(font)
            self.section_stat_cards[label] = card
            stats_layout.addWidget(card)

        layout.addWidget(stats_grid)

        detail_row = QWidget()
        detail_layout = QHBoxLayout(detail_row)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_label = QLabel("\u65ad\u9762\u6d4b\u91cf\u8868\u8be6\u60c5")
        detail_label.setObjectName("sectionSubTitle")
        detail_layout.addWidget(detail_label)
        self.export_section_btn = QPushButton("\u5bfc\u51fa")
        self.export_section_btn.setObjectName("sectionExportBtn")
        self.export_section_btn.setCursor(Qt.PointingHandCursor)
        self.export_section_btn.clicked.connect(self._export_section_detail)
        detail_layout.addWidget(self.export_section_btn)
        layout.addWidget(detail_row)

        self.section_detail_table = QTableWidget()
        self.section_detail_table.setObjectName("minimalResultTable")
        self.section_detail_table.setColumnCount(5)
        self.section_detail_table.setHorizontalHeaderLabels(["\u5e8f\u53f7", "\u65ad\u9762\u7f16\u7801", "\u65ad\u9762\u540d\u79f0", "\u6240\u5c5e\u6587\u4ef6", "\u65ad\u9762\u7c7b\u578b"])
        self.section_detail_table.horizontalHeader().setStretchLastSection(True)
        self.section_detail_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.section_detail_table.setColumnWidth(0, 40)
        self.section_detail_table.setColumnWidth(1, 140)
        self.section_detail_table.setColumnWidth(2, 160)
        self.section_detail_table.setColumnWidth(3, 160)
        self.section_detail_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.section_detail_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.section_detail_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.section_detail_table.verticalHeader().setVisible(False)
        self.section_detail_table.setAlternatingRowColors(True)
        self._enable_table_copy(self.section_detail_table)
        layout.addWidget(self.section_detail_table, 1)

    def _setup_photo_content(self, widget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.photo_dashboard = PhotoMatchDashboard()
        self.photo_dashboard.setMinimumHeight(280)
        layout.addWidget(self.photo_dashboard)

    def _setup_cross_content(self, widget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.cross_list = CrossCheckListPanel()
        self.cross_list.setMinimumHeight(500)
        layout.addWidget(self.cross_list, 1)

    def show_card(self, card_key: str):
        if card_key in self.result_cards:
            self.swipe_cards.set_current_index(self.result_cards[card_key])

    def update_fubiao(self, data: dict):
        errors = data.get('fubiao_check', {}).get('errors', [])
        self.fubiao_table.setRowCount(len(errors))
        for row, err in enumerate(errors):
            self.fubiao_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            for col, key in enumerate(['表名', '字段名', '错误类型', '错误描述', '当前值']):
                self.fubiao_table.setItem(row, col + 1, QTableWidgetItem(str(err.get(key, ''))))

    def update_spatial(self, data: dict):
        results = data.get('spatial_check', {}).get('results', [])
        self.spatial_grid.set_data(results)

    def update_section(self, data: dict):
        stats = data.get('section_check', {}).get('stats', {})
        anomaly_count = stats.get('anomaly_count', 0)
        validation_error_count = stats.get('validation_error_count', 0)

        card_updates = [
            ("\u603b\u65ad\u9762\u6570", str(stats.get('total_sections', 0)),
             "\u6240\u6709\u52a0\u8f7d\u7684\u65ad\u9762\u6570\u636e", "text_primary"),
            ("\u603b\u6d4b\u70b9\u6570", str(stats.get('total_points', 0)),
             "\u6240\u6709\u65ad\u9762\u7684\u6d4b\u91cf\u70b9", "text_primary"),
            ("\u5f02\u5e38\u65ad\u9762\u6570", str(anomaly_count),
             "\u7a7a\u95f4\u8fde\u7eed\u6027\u5f02\u5e38",
             "success_text" if anomaly_count == 0 else "error_text"),
            ("\u6821\u9a8c\u9519\u8bef\u6570", str(validation_error_count),
             "\u6570\u636e\u683c\u5f0f/\u903b\u8f91\u9519\u8bef",
             "success_text" if validation_error_count == 0 else "error_text"),
            ("\u6709\u5750\u6807\u70b9\u6570", str(stats.get('coords_count', 0)),
             "\u5305\u542b\u7ecf\u7eac\u5ea6\u5750\u6807\u7684\u6d4b\u70b9", "text_primary"),
            ("\u5206\u7c7b\u6570", str(stats.get('category_count', 0)),
             "\u4e0d\u540c\u6d4b\u91cf\u7c7b\u522b", "text_primary"),
        ]
        for label, value, sub_text, accent in card_updates:
            if label in self.section_stat_cards:
                self.section_stat_cards[label].set_value(value, sub_text, accent)

        tree_data = data.get('section_check', {}).get('tree_data', {})
        detail_rows = []
        for file_path, files in tree_data.items():
            for file_name, sections in files.items():
                for sec in sections:
                    section_key = sec.get('key', '')
                    section_name = sec.get('name', '')
                    parts = section_key.split('|') if section_key else []
                    section_code = parts[-1] if parts else section_key
                    section_type = parts[0] if len(parts) >= 3 else ""
                    detail_rows.append((section_code, section_name, file_name, section_type))
        self.section_detail_table.setRowCount(len(detail_rows))
        for row, (section_code, section_name, file_name, section_type) in enumerate(detail_rows):
            self.section_detail_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.section_detail_table.setItem(row, 1, QTableWidgetItem(section_code))
            self.section_detail_table.setItem(row, 2, QTableWidgetItem(section_name))
            self.section_detail_table.setItem(row, 3, QTableWidgetItem(file_name))
            self.section_detail_table.setItem(row, 4, QTableWidgetItem(section_type))

    def update_photo(self, data: dict):
        mr = data.get('photo_check', {}).get('match_result', {}).get('summary', {})
        self.photo_dashboard.set_data(mr)

    def update_cross(self, data: dict):
        items = data.get('cross_check', {}).get('items', [])
        self.cross_list.set_items(items)

    def update_card_status(self, card_key: str, status: str):
        if card_key in self.result_cards:
            self.swipe_cards.set_card_status(self.result_cards[card_key], status)

    def clear_all(self):
        self.fubiao_table.setRowCount(0)
        self.spatial_grid.set_data([])
        for card in self.section_stat_cards.values():
            card.set_value("--", "", None)
        self.section_detail_table.setRowCount(0)
        self.cross_list.set_items([])

    def reset(self):
        self.clear_all()
        for card_key, index in self.result_cards.items():
            self.swipe_cards.set_card_status(index, 'pending')
        self.swipe_cards.set_current_index(0)

    def _enable_table_copy(self, table):
        table.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and event.matches(QKeySequence.Copy):
            from PySide6.QtWidgets import QTableWidget
            if isinstance(obj, QTableWidget):
                self._copy_table_selection(obj)
                return True
        return super().eventFilter(obj, event)

    def _copy_table_selection(self, table):
        selected = table.selectedRanges()
        if not selected:
            return
        rows = set()
        for r in selected:
            for row in range(r.topRow(), r.bottomRow() + 1):
                rows.add(row)
        lines = []
        headers = []
        for col in range(table.columnCount()):
            header_item = table.horizontalHeaderItem(col)
            headers.append(header_item.text() if header_item else "")
        lines.append("\t".join(headers))
        for row in sorted(rows):
            cols = []
            for col in range(table.columnCount()):
                item = table.item(row, col)
                cols.append(item.text() if item else "")
            lines.append("\t".join(cols))
        QApplication.clipboard().setText("\n".join(lines))

    def _export_section_detail(self):
        if self.section_detail_table.rowCount() == 0:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "\u5bfc\u51fa\u65ad\u9762\u6d4b\u91cf\u8868\u8be6\u60c5",
            "\u65ad\u9762\u6d4b\u91cf\u8868\u8be6\u60c5.csv",
            "CSV \u6587\u4ef6 (*.csv);;\u6240\u6709\u6587\u4ef6 (*)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                headers = []
                for col in range(self.section_detail_table.columnCount()):
                    header_item = self.section_detail_table.horizontalHeaderItem(col)
                    headers.append(header_item.text() if header_item else "")
                writer.writerow(headers)
                for row in range(self.section_detail_table.rowCount()):
                    row_data = []
                    for col in range(self.section_detail_table.columnCount()):
                        item = self.section_detail_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
        except Exception:
            pass
