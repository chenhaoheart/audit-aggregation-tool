# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLabel, QComboBox, QPushButton
)
from PySide6.QtCore import Qt
from ui.components.filter_bar import FilterBar
from services.filter_service import FilterService


class FangzhiTab(QWidget):

    TAB_KEY = 'fangzhi'
    CHECK_FIELDS = [
        '河流代码', '河流名称',
        '河流代码长度17位', '河流代码在水系中', '河流名称与水系一致',
        '错误信息', '验证状态'
    ]
    EXCLUDE_FIELDS = {'源文件', '记录序号', '_original_columns'}
    OVERLAP_FIELDS = {'河流代码', '河流名称'}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._original_data = []
        self._display_data = []
        self._pagination = {'page': 1, 'page_size': 20}
        self._page_widgets = {}
        self.filter_service = FilterService()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 4, 0, 4)

        self.filter_bar = FilterBar(show_name_filter=True)
        self.filter_bar.filter_changed.connect(self._apply_filter)
        self.filter_bar.clear_requested.connect(self._clear_filter)
        layout.addWidget(self.filter_bar)

        self.table = QTableWidget()
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        layout.addWidget(self.table, 1)

        layout.addWidget(self._create_pagination_bar())
        self.setLayout(layout)

    def _create_pagination_bar(self):
        bar = QWidget()
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(0, 6, 0, 0)
        bar_layout.setSpacing(6)

        size_label = QLabel("每页:")
        size_label.setFixedWidth(36)
        size_combo = QComboBox()
        size_combo.addItems(["10", "20", "50", "100"])
        size_combo.setCurrentText(str(self._pagination['page_size']))
        size_combo.setFixedWidth(80)
        size_combo.setStyleSheet("QComboBox { padding: 0 2px; }")
        size_combo.currentTextChanged.connect(
            lambda text: self._change_page_size(int(text))
        )

        bar_layout.addWidget(size_label)
        bar_layout.addWidget(size_combo)
        bar_layout.addStretch()

        prev_btn = QPushButton("◀ 上一页")
        prev_btn.setFixedWidth(90)
        prev_btn.clicked.connect(self._prev_page)

        page_label = QLabel("第1页/共1页")
        page_label.setAlignment(Qt.AlignCenter)
        page_label.setMinimumWidth(120)

        next_btn = QPushButton("下一页 ▶")
        next_btn.setFixedWidth(90)
        next_btn.clicked.connect(self._next_page)

        bar_layout.addWidget(prev_btn)
        bar_layout.addWidget(page_label)
        bar_layout.addWidget(next_btn)

        self._page_widgets = {
            'combo': size_combo,
            'label': page_label,
            'prev': prev_btn,
            'next': next_btn,
        }
        return bar

    def _paginate(self, data: list):
        pg = self._pagination
        page_size = pg['page_size']
        total = len(data)
        total_pages = max(1, (total + page_size - 1) // page_size)
        current_page = max(1, min(pg['page'], total_pages))
        pg['page'] = current_page
        start = (current_page - 1) * page_size
        end = start + page_size
        self._update_pagination_widgets(current_page, total_pages, total)
        return data[start:end]

    def _update_pagination_widgets(self, current_page: int, total_pages: int, total_count: int = 0):
        w = self._page_widgets
        if not w:
            return
        w['label'].setText(f"第{current_page}页/共{total_pages}页" + (f" ({total_count}条)" if total_count else ""))
        w['prev'].setEnabled(current_page > 1)
        w['next'].setEnabled(current_page < total_pages)

    def _change_page_size(self, size: int):
        self._pagination['page_size'] = size
        self._pagination['page'] = 1
        self._render_page()

    def _prev_page(self):
        pg = self._pagination
        if pg['page'] > 1:
            pg['page'] -= 1
            self._render_page()

    def _next_page(self):
        pg = self._pagination
        total = len(self._display_data)
        total_pages = max(1, (total + pg['page_size'] - 1) // pg['page_size'])
        if pg['page'] < total_pages:
            pg['page'] += 1
            self._render_page()

    def update_data(self, records: list):
        self._original_data = records
        self._display_data = records
        self._pagination['page'] = 1
        self._render_page()

    def _build_header_labels(self, records: list) -> list:
        if not records:
            return self.CHECK_FIELDS
        first_record = records[0]
        original_cols = first_record.get('_original_columns', [])
        if not original_cols:
            original_cols = [
                k for k in first_record.keys()
                if k not in self.CHECK_FIELDS and k not in self.EXCLUDE_FIELDS
            ]
            original_cols = [c for c in original_cols if c not in self.OVERLAP_FIELDS]
        return list(original_cols) + self.CHECK_FIELDS

    def _render_page(self):
        records = self._display_data
        if not records:
            self.table.setRowCount(0)
            self._update_pagination_widgets(1, 1, 0)
            return

        header_labels = self._build_header_labels(records)
        self.table.setColumnCount(len(header_labels))
        self.table.setHorizontalHeaderLabels(header_labels)

        page_data = self._paginate(records)
        self.table.setRowCount(len(page_data))

        status_col = header_labels.index('验证状态') if '验证状态' in header_labels else -1

        for row, record in enumerate(page_data):
            for col, field in enumerate(header_labels):
                text = str(record.get(field, ''))
                if col == status_col:
                    status = record.get('验证状态', '')
                    badge = QLabel("通过" if status == '通过' else "不通过")
                    badge.setObjectName("badgePass" if status == '通过' else "badgeFail")
                    badge.setAlignment(Qt.AlignCenter)
                    badge.setFixedHeight(22)
                    self.table.setCellWidget(row, col, badge)
                else:
                    item = QTableWidgetItem(text)
                    self.table.setItem(row, col, item)

    def _apply_filter(self, conditions: dict):
        filtered = self.filter_service.filter_records(
            self._original_data,
            status=conditions.get('status'),
            code=conditions.get('code'),
            name=conditions.get('name')
        )
        self._display_data = filtered
        self._pagination['page'] = 1
        self._render_page()

    def _clear_filter(self):
        self._display_data = self._original_data
        self._pagination['page'] = 1
        self._render_page()

    def clear_data(self):
        self._original_data = []
        self._display_data = []
        self._pagination['page'] = 1
        self.table.setRowCount(0)
        self._update_pagination_widgets(1, 1, 0)
        self.filter_bar._clear_filter()
