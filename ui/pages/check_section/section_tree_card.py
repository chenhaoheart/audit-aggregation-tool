# -*- coding: utf-8 -*-
import os
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLineEdit, QCheckBox,
    QTreeWidget, QTreeWidgetItem, QToolButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from core.theme_manager import get_theme_manager


class SectionTreeCard(QFrame):
    section_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._service = None
        self._theme_manager = get_theme_manager()
        self._init_ui()
        self._apply_theme_styles()
        self._theme_manager.theme_changed.connect(self._on_theme_changed)

    def set_service(self, service):
        self._service = service

    def _init_ui(self):
        self.setObjectName("card")
        left_layout = QVBoxLayout(self)
        left_layout.setSpacing(8)
        left_layout.setContentsMargins(8, 8, 8, 8)

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)
        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("filterEdit")
        self.search_edit.setPlaceholderText("搜索断面名称...")
        self.search_edit.textChanged.connect(self._on_search)
        filter_layout.addWidget(self.search_edit, 1)
        self.anomaly_filter_cb = QCheckBox("仅异常")
        self.anomaly_filter_cb.stateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.anomaly_filter_cb)
        self.error_filter_cb = QCheckBox("仅错误")
        self.error_filter_cb.stateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.error_filter_cb)
        left_layout.addLayout(filter_layout)

        self.section_tree = QTreeWidget()
        self.section_tree.setObjectName("sectionTree")
        self.section_tree.setIndentation(14)
        self.section_tree.setHeaderLabels(["断面名称", "点数", "状态"])
        self.section_tree.setColumnWidth(0, 220)
        self.section_tree.setColumnWidth(1, 50)
        self.section_tree.setColumnWidth(2, 80)
        self.section_tree.itemClicked.connect(self._on_section_clicked)

        tree_toolbar = QHBoxLayout()
        tree_toolbar.setSpacing(4)
        self.expand_all_btn = QToolButton()
        self.expand_all_btn.setText("全部展开")
        self.expand_all_btn.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.expand_all_btn.setFixedHeight(26)
        self.expand_all_btn.setCursor(Qt.PointingHandCursor)
        self.expand_all_btn.clicked.connect(self.section_tree.expandAll)
        tree_toolbar.addWidget(self.expand_all_btn)
        self.collapse_all_btn = QToolButton()
        self.collapse_all_btn.setText("全部折叠")
        self.collapse_all_btn.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.collapse_all_btn.setFixedHeight(26)
        self.collapse_all_btn.setCursor(Qt.PointingHandCursor)
        self.collapse_all_btn.clicked.connect(self.section_tree.collapseAll)
        tree_toolbar.addWidget(self.collapse_all_btn)
        self.chengtu_filter_cb = QCheckBox("成图表")
        self.chengtu_filter_cb.setChecked(True)
        self.chengtu_filter_cb.stateChanged.connect(self._on_filter_changed)
        tree_toolbar.addWidget(self.chengtu_filter_cb)
        self.guifan_filter_cb = QCheckBox("规范表")
        self.guifan_filter_cb.setChecked(True)
        self.guifan_filter_cb.stateChanged.connect(self._on_filter_changed)
        tree_toolbar.addWidget(self.guifan_filter_cb)
        tree_toolbar.addStretch()
        left_layout.addLayout(tree_toolbar)
        left_layout.addWidget(self.section_tree, 1)

    def _apply_theme_styles(self):
        theme = self._theme_manager.get_current_theme()
        card_bg = theme.get('card_bg', '#ffffff')
        card_border = theme.get('card_border', '#e0e4e8')
        text_primary = theme.get('text_primary', '#2c3e50')
        text_secondary = theme.get('text_secondary', '#6b7d9e')
        input_bg = theme.get('input_bg', '#ffffff')
        input_border = theme.get('input_border', '#dcdde1')
        table_grid = theme.get('table_grid', '#ecedef')
        table_header_bg = theme.get('table_header_bg', '#f8f9fa')
        table_header_text = theme.get('table_header_text', '#2c3e50')
        warning_text = theme.get('warning_text', '#f39c12')
        error_text = theme.get('error_text', '#e74c3c')
        success_text = theme.get('success_text', '#27ae60')
        combo_bg = theme.get('combo_bg', '#ffffff')
        combo_border = theme.get('combo_border', '#dcdde1')
        combo_text = theme.get('combo_text', '#2c3e50')
        hover_glow = theme.get('hover_glow', 'rgba(102,126,234,0.15)')

        self.section_tree.setStyleSheet(f"""
            QTreeWidget#sectionTree {{
                background: {card_bg};
                border: 1px solid {card_border};
                border-radius: 8px;
                color: {text_primary};
                font-size: 13px;
                outline: none;
                padding: 0;
            }}
            QTreeWidget#sectionTree::item {{
                padding: 4px 6px;
                border-bottom: 1px solid {table_grid};
                margin-left: 0;
            }}
            QTreeWidget#sectionTree::item:hover {{
                background: {hover_glow};
            }}
            QTreeWidget#sectionTree::item:selected {{
                background: {hover_glow};
            }}
            QTreeWidget#sectionTree::header {{
                background: {table_header_bg};
                border-bottom: 1px solid {card_border};
            }}
            QTreeWidget#sectionTree::header::section {{
                background: {table_header_bg};
                color: {table_header_text};
                padding: 6px 6px;
                border: none;
                border-right: 1px solid {table_grid};
                font-weight: 600;
                font-size: 12px;
            }}
            QTreeWidget#sectionTree::branch {{
                background: transparent;
                margin-left: 0;
            }}
        """)

        cb_style = f"""
            QCheckBox {{
                color: {text_secondary};
                font-size: 12px;
                spacing: 6px;
            }}
        """
        self.anomaly_filter_cb.setStyleSheet(cb_style)
        self.error_filter_cb.setStyleSheet(cb_style)
        self.chengtu_filter_cb.setStyleSheet(cb_style)
        self.guifan_filter_cb.setStyleSheet(cb_style)

        tool_btn_style = f"""
            QToolButton {{
                color: {text_secondary};
                background: transparent;
                border: 1px solid {card_border};
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 11px;
            }}
            QToolButton:hover {{
                color: {theme.get('accent_color', '#6366f1')};
                border-color: {theme.get('accent_color', '#6366f1')};
                background: {hover_glow};
            }}
        """
        self.expand_all_btn.setStyleSheet(tool_btn_style)
        self.collapse_all_btn.setStyleSheet(tool_btn_style)

    def _on_theme_changed(self, mode: str):
        self._apply_theme_styles()
        self.refresh_tree()

    def refresh_tree(self):
        if not self._service:
            return
        self.section_tree.clear()
        tree_data = self._service.get_tree_data()
        search_text = self.search_edit.text().strip()
        anomaly_only = self.anomaly_filter_cb.isChecked()
        error_only = self.error_filter_cb.isChecked()
        chengtu_checked = self.chengtu_filter_cb.isChecked()
        guifan_checked = self.guifan_filter_cb.isChecked()
        theme = self._theme_manager.get_current_theme()
        warning_color = theme.get('warning_text', '#fbbf24')
        error_color = theme.get('error_text', '#fb7185')
        success_color = theme.get('success_text', '#34d399')
        for file_path, files in tree_data.items():
            display_path = os.path.basename(file_path) if file_path != "未知路径" else file_path
            path_item = QTreeWidgetItem(self.section_tree, [display_path, "", ""])
            path_item.setExpanded(True)
            path_item.setData(0, Qt.UserRole, "file_path")
            path_item.setData(0, Qt.UserRole + 1, file_path)
            for file_name, sections in files.items():
                file_item = QTreeWidgetItem(path_item, [file_name, "", ""])
                file_item.setData(0, Qt.UserRole, "file_name")
                for sec in sections:
                    if search_text and search_text not in sec["name"] and search_text not in file_name:
                        continue
                    if anomaly_only and not sec["anomaly"]:
                        continue
                    if error_only and not sec["validation_error"]:
                        continue
                    table_type = sec.get("table_type", "")
                    if not chengtu_checked and table_type == "chengtu":
                        continue
                    if not guifan_checked and table_type == "guifan":
                        continue
                    status_parts = []
                    if sec["anomaly"]:
                        status_parts.append("异常")
                    if sec["validation_error"]:
                        status_parts.append("错误")
                    elif sec["validation_warning"]:
                        status_parts.append("警告")
                    status_str = "/".join(status_parts) if status_parts else "正常"
                    table_type_str = ""
                    if sec.get("table_type") == "chengtu":
                        table_type_str = "[成图表]"
                    elif sec.get("table_type") == "guifan":
                        table_type_str = "[规范表]"
                    display_name = f"{table_type_str}{sec['name']}"
                    sec_item = QTreeWidgetItem(file_item, [
                        display_name,
                        str(sec["points"]),
                        status_str
                    ])
                    sec_item.setData(0, Qt.UserRole, sec["key"])
                    if sec["anomaly"]:
                        sec_item.setForeground(2, QColor(warning_color))
                    elif sec["validation_error"]:
                        sec_item.setForeground(2, QColor(error_color))
                    elif sec["validation_warning"]:
                        sec_item.setForeground(2, QColor(warning_color))
                    else:
                        sec_item.setForeground(2, QColor(success_color))
        self.section_tree.expandAll()

    def clear_tree(self):
        self.section_tree.clear()

    def _on_section_clicked(self, item: QTreeWidgetItem, column: int):
        key = item.data(0, Qt.UserRole)
        if not key or key in ("file_path", "file_name"):
            return
        self.section_clicked.emit(key)

    def _on_search(self):
        self.refresh_tree()

    def _on_filter_changed(self):
        self.refresh_tree()
