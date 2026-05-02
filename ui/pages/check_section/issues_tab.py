# -*- coding: utf-8 -*-
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from core.theme_manager import get_theme_manager


class IssuesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme_manager = get_theme_manager()
        self._init_ui()
        self._apply_theme_styles()
        self._theme_manager.theme_changed.connect(self._on_theme_changed)

    def _init_ui(self):
        issues_layout = QVBoxLayout(self)
        issues_layout.setSpacing(0)
        issues_layout.setContentsMargins(0, 4, 0, 4)
        self.issues_table = QTableWidget()
        self.issues_table.setColumnCount(4)
        self.issues_table.setHorizontalHeaderLabels(["级别", "规则", "描述", "详情"])
        self.issues_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.issues_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.issues_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.issues_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.issues_table.setColumnWidth(0, 60)
        self.issues_table.setColumnWidth(1, 120)
        self.issues_table.setColumnWidth(2, 120)
        self.issues_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.issues_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.issues_table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        issues_layout.addWidget(self.issues_table)

    def _apply_theme_styles(self):
        theme = self._theme_manager.get_current_theme()
        table_grid = theme.get('table_grid', '#ecedef')
        table_header_bg = theme.get('table_header_bg', '#f8f9fa')
        self.issues_table.setStyleSheet(f"""
            QTableWidget {{
                gridline-color: {table_grid};
                border: 1px solid {table_grid};
            }}
            QTableWidget::item {{
                padding: 4px;
                border: none;
            }}
            QHeaderView::section {{
                padding: 4px;
                border: 1px solid {table_grid};
                background: {table_header_bg};
            }}
        """)

    def _on_theme_changed(self, mode: str):
        self._apply_theme_styles()

    def fill_issues_table(self, sec: dict):
        theme = self._theme_manager.get_current_theme()
        error_color = theme.get('error_text', '#fb7185')
        warning_color = theme.get('warning_text', '#fbbf24')

        issues = sec.get("validation_issues", [])
        anomaly_details = sec.get("anomaly_details", [])
        all_items = []
        for iss in issues:
            all_items.append({
                "level": iss.get("level", ""),
                "rule": iss.get("desc", iss.get("rule", "")),
                "desc": iss.get("rule", ""),
                "details": iss.get("details", ""),
            })
        for ad in anomaly_details:
            all_items.append({
                "level": "error",
                "rule": ad.get("desc", ad.get("type", "")),
                "desc": ad.get("type", ""),
                "details": ad.get("detail", json.dumps(ad, ensure_ascii=False)),
            })
        self.issues_table.setRowCount(len(all_items))
        for row, item_data in enumerate(all_items):
            level = item_data["level"]
            level_item = QTableWidgetItem("错误" if level == "error" else "警告")
            if level == "error":
                level_item.setForeground(QColor(error_color))
            else:
                level_item.setForeground(QColor(warning_color))
            self.issues_table.setItem(row, 0, level_item)
            self.issues_table.setItem(row, 1, QTableWidgetItem(item_data["rule"]))
            self.issues_table.setItem(row, 2, QTableWidgetItem(item_data["desc"]))
            self.issues_table.setItem(row, 3, QTableWidgetItem(item_data["details"]))
