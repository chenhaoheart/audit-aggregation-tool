# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QWidget, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from ui.components.dashboard_widgets import (
    HorizontalSwipeCards, SpatialResultGrid,
    PhotoMatchDashboard, CrossCheckListPanel
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
        self.fubiao_table.verticalHeader().setVisible(False)
        self.fubiao_table.setAlternatingRowColors(True)
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
        layout.setSpacing(4)
        self.section_table = QTableWidget()
        self.section_table.setObjectName("minimalResultTable")
        self.section_table.setColumnCount(3)
        self.section_table.setHorizontalHeaderLabels(["指标", "数值", "说明"])
        self.section_table.horizontalHeader().setStretchLastSection(True)
        self.section_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.section_table.setColumnWidth(0, 140)
        self.section_table.setColumnWidth(1, 80)
        self.section_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.section_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.section_table.verticalHeader().setVisible(False)
        self.section_table.setAlternatingRowColors(True)
        layout.addWidget(self.section_table)

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
        rows = [
            ("\u603b\u65ad\u9762\u6570", stats.get('total_sections', 0), "\u6240\u6709\u52a0\u8f7d\u7684\u65ad\u9762\u6570\u636e"),
            ("\u603b\u6d4b\u70b9\u6570", stats.get('total_points', 0), "\u6240\u6709\u65ad\u9762\u7684\u6d4b\u91cf\u70b9"),
            ("\u5f02\u5e38\u65ad\u9762\u6570", stats.get('anomaly_count', 0), "\u7a7a\u95f4\u8fde\u7eed\u6027\u5f02\u5e38"),
            ("\u6821\u9a8c\u9519\u8bef\u6570", stats.get('validation_error_count', 0), "\u6570\u636e\u683c\u5f0f/\u903b\u8f91\u9519\u8bef"),
            ("\u6709\u5750\u6807\u70b9\u6570", stats.get('coords_count', 0), "\u5305\u542b\u7ecf\u7eac\u5ea6\u5750\u6807\u7684\u6d4b\u70b9"),
            ("\u5206\u7c7b\u6570", stats.get('category_count', 0), "\u4e0d\u540c\u6d4b\u91cf\u7c7b\u522b"),
        ]
        self.section_table.setRowCount(len(rows))
        for row, (name, count, desc) in enumerate(rows):
            self.section_table.setItem(row, 0, QTableWidgetItem(name))
            self.section_table.setItem(row, 1, QTableWidgetItem(str(count)))
            self.section_table.setItem(row, 2, QTableWidgetItem(desc))

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
        self.section_table.setRowCount(0)
        self.cross_list.set_items([])

    def reset(self):
        self.clear_all()
        for card_key, index in self.result_cards.items():
            self.swipe_cards.set_card_status(index, 'pending')
        self.swipe_cards.set_current_index(0)
