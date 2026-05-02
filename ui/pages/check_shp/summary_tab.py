# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLabel, QComboBox, QPushButton
)
from PySide6.QtCore import Qt
from ui.components.filter_bar import FilterBar


class SummaryTab(QWidget):

    TAB_KEY = 'summary'

    def __init__(self, parent=None):
        super().__init__(parent)
        self._original_data = []
        self._display_data = []
        self._pagination = {'page': 1, 'page_size': 20}
        self._page_widgets = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 4, 0, 4)

        self.filter_bar = FilterBar(show_name_filter=True)
        self.filter_bar.filter_changed.connect(self._apply_filter)
        self.filter_bar.clear_requested.connect(self._clear_filter)
        layout.addWidget(self.filter_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "序号", "文件名", "状态", "总记录", "有效", "无效", "重复", "有效率"
        ])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 80)
        self.table.setColumnWidth(7, 80)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)
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

    def update_data(self, results: list):
        self._original_data = results
        self._display_data = results
        self._pagination['page'] = 1
        self._render_page()

    def _render_page(self):
        data = self._display_data
        page_data = self._paginate(data)
        self.table.setRowCount(len(page_data))

        for row, result in enumerate(page_data):
            global_idx = self._pagination['page_size'] * (self._pagination['page'] - 1) + row
            items = [
                str(global_idx + 1),
                result['file_name'],
                result['status'],
                str(result['total_records']),
                str(result['valid_records']),
                str(result['invalid_records']),
                str(result.get('duplicate_records', 0)),
                f"{result['valid_records'] / result['total_records'] * 100:.1f}%" if result['total_records'] > 0 else "N/A"
            ]
            for col, text in enumerate(items):
                if col == 2:
                    badge = QLabel("通过" if result['status'] == '通过' else "不通过")
                    badge.setObjectName("badgePass" if result['status'] == '通过' else "badgeFail")
                    badge.setAlignment(Qt.AlignCenter)
                    badge.setFixedHeight(22)
                    self.table.setCellWidget(row, col, badge)
                else:
                    item = QTableWidgetItem(text)
                    self.table.setItem(row, col, item)

    def _apply_filter(self, conditions: dict):
        status = conditions.get('status', '全部')
        name = conditions.get('name', '').strip()

        filtered = []
        for record in self._original_data:
            if status != '全部' and record.get('status') != status:
                continue
            if name and name.upper() not in str(record.get('file_name', '')).upper():
                continue
            filtered.append(record)
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
