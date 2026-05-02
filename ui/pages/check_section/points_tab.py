# -*- coding: utf-8 -*-
import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QComboBox, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from core.theme_manager import get_theme_manager
from ui.dialogs.excel_preview_dialog import ExcelPreviewDialog


class PointsTab(QWidget):
    log_message = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._service = None
        self._current_section_key = None
        self._all_points = []
        self._current_page = 0
        self._page_size = 50
        self._theme_manager = get_theme_manager()
        self._init_ui()
        self._apply_theme_styles()
        self._theme_manager.theme_changed.connect(self._on_theme_changed)

    def set_service(self, service):
        self._service = service

    def _init_ui(self):
        points_outer_layout = QVBoxLayout(self)
        points_outer_layout.setSpacing(8)
        points_outer_layout.setContentsMargins(0, 0, 0, 8)

        info_group = QFrame()
        info_group.setObjectName("card")
        info_group_layout = QVBoxLayout(info_group)
        info_group_layout.setSpacing(4)
        info_group_layout.setContentsMargins(8, 8, 8, 8)
        info_title_layout = QHBoxLayout()
        info_title_layout.setSpacing(8)
        info_title = QLabel("断面属性")
        info_title.setObjectName("sectionHeaderSm")
        info_title_layout.addWidget(info_title)
        self.open_excel_btn = QPushButton("预览Excel")
        self.open_excel_btn.setObjectName("toolbarBtn")
        self.open_excel_btn.setFixedHeight(20)
        self.open_excel_btn.setCursor(Qt.PointingHandCursor)
        self.open_excel_btn.clicked.connect(self._preview_excel)
        info_title_layout.addWidget(self.open_excel_btn)
        info_title_layout.addStretch()
        info_group_layout.addLayout(info_title_layout)

        self.info_grid = QGridLayout()
        self.info_grid.setSpacing(6)
        self.info_grid.setContentsMargins(0, 0, 0, 0)
        self.info_labels = {}
        info_group_layout.addLayout(self.info_grid)
        points_outer_layout.addWidget(info_group)

        points_header = QHBoxLayout()
        points_header.setSpacing(8)
        points_title = QLabel("测量点数据")
        points_title.setObjectName("sectionHeaderSm")
        points_header.addWidget(points_title)
        points_header.addStretch()

        self.page_size_label = QLabel("每页显示:")
        points_header.addWidget(self.page_size_label)

        self.points_page_size_combo = QComboBox()
        self.points_page_size_combo.addItems(["20", "50", "100", "200", "500"])
        self.points_page_size_combo.setCurrentText("50")
        self.points_page_size_combo.setFixedWidth(60)
        self.points_page_size_combo.setFixedHeight(20)
        self.points_page_size_combo.setCursor(Qt.PointingHandCursor)
        self.points_page_size_combo.currentIndexChanged.connect(self._on_page_size_changed)
        points_header.addWidget(self.points_page_size_combo)

        self.points_page_info = QLabel("")
        points_header.addWidget(self.points_page_info)

        self.points_prev_btn = QPushButton("上一页")
        self.points_prev_btn.setObjectName("toolbarBtn")
        self.points_prev_btn.setFixedHeight(20)
        self.points_prev_btn.setFixedWidth(50)
        self.points_prev_btn.setCursor(Qt.PointingHandCursor)
        self.points_prev_btn.clicked.connect(self._on_prev_page)
        points_header.addWidget(self.points_prev_btn)

        self.points_next_btn = QPushButton("下一页")
        self.points_next_btn.setObjectName("toolbarBtn")
        self.points_next_btn.setFixedHeight(20)
        self.points_next_btn.setFixedWidth(50)
        self.points_next_btn.setCursor(Qt.PointingHandCursor)
        self.points_next_btn.clicked.connect(self._on_next_page)
        points_header.addWidget(self.points_next_btn)

        points_outer_layout.addLayout(points_header)

        self.points_table = QTableWidget()
        self.points_table.setColumnCount(8)
        self.points_table.setHorizontalHeaderLabels([
            "序号", "特征描述", "起点距(m)", "高程(m)", "经度(°)", "纬度(°)", "糙率", "特征点"
        ])
        self.points_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.points_table.horizontalHeader().setStretchLastSection(True)
        self.points_table.setColumnWidth(0, 60)
        self.points_table.setColumnWidth(1, 150)
        self.points_table.setColumnWidth(2, 90)
        self.points_table.setColumnWidth(3, 90)
        self.points_table.setColumnWidth(4, 110)
        self.points_table.setColumnWidth(5, 110)
        self.points_table.setColumnWidth(6, 60)
        self.points_table.setColumnWidth(7, 60)
        self.points_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.points_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.points_table.verticalHeader().setVisible(False)
        self.points_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.points_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        default_height = self.points_table.verticalHeader().defaultSectionSize() * 50 + self.points_table.horizontalHeader().height() + self.points_table.frameWidth() * 2 + 51 + 6
        self.points_table.setFixedHeight(default_height)
        points_outer_layout.addWidget(self.points_table)

    def _apply_theme_styles(self):
        theme = self._theme_manager.get_current_theme()
        text_secondary = theme.get('text_secondary', '#6b7d9e')
        text_primary = theme.get('text_primary', '#2c3e50')
        border_subtle = theme.get('border_subtle', theme.get('card_border', '#e0e4e8'))
        accent = theme.get('accent_color', '#6366f1')
        surface_1 = theme.get('surface_1', theme.get('card_bg', '#f8f9fa'))
        surface_2 = theme.get('surface_2', theme.get('card_bg', '#f0f2f5'))
        table_grid = theme.get('table_grid', '#ecedef')
        table_header_bg = theme.get('table_header_bg', '#f8f9fa')
        combo_bg = theme.get('combo_bg', '#ffffff')
        combo_border = theme.get('combo_border', '#dcdde1')
        combo_text = theme.get('combo_text', '#2c3e50')

        small_btn_style = f"""
            QPushButton#toolbarBtn {{
                background: transparent;
                color: {text_secondary};
                border: 1px solid {border_subtle};
                border-radius: 4px;
                padding: 0 4px;
                font-size: 11px;
            }}
            QPushButton#toolbarBtn:hover {{
                background: {surface_2};
                color: {text_primary};
                border-color: {accent};
            }}
        """
        self.open_excel_btn.setStyleSheet(small_btn_style)
        self.points_prev_btn.setStyleSheet(small_btn_style)
        self.points_next_btn.setStyleSheet(small_btn_style)

        self.page_size_label.setStyleSheet(f"color: {text_secondary}; font-size: 12px;")
        self.points_page_info.setStyleSheet(f"color: {text_secondary}; font-size: 12px;")

        self.points_page_size_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 0 4px;
                font-size: 11px;
                background: {combo_bg};
                color: {combo_text};
                border: 1px solid {combo_border};
                border-radius: 4px;
            }}
            QComboBox::drop-down {{
                width: 16px;
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background: {combo_bg};
                color: {combo_text};
                border: 1px solid {combo_border};
                selection-background-color: {surface_2};
            }}
        """)

        self.points_table.setStyleSheet(f"""
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
        if self._current_section_key:
            sec = self._service.get_section_detail(self._current_section_key) if self._service else None
            if sec:
                self.fill_info_table(sec)
                self._render_current_page()

    def fill_points_table(self, sec: dict):
        self._all_points = sec.get("points", [])
        self._current_page = 0
        self._render_current_page()

    def fill_info_table(self, sec: dict):
        while self.info_grid.count():
            item = self.info_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.info_labels.clear()

        theme = self._theme_manager.get_current_theme()
        label_style = f"color: {theme.get('text_secondary', '#6b7d9e')}; font-size: 12px; padding: 2px 4px 2px 0;"
        value_style = f"color: {theme.get('text_primary', '#2c3e50')}; font-size: 12px; font-weight: 500; padding: 2px 8px 2px 0;"

        info_fields = [
            ("断面名称", "name", None),
            ("表格类型", "table_type", lambda v: "成图表" if v == "chengtu" else "规范表" if v == "guifan" else "未知"),
            ("位置", "location", None),
            ("行政区划代码", "district_code", None),
            ("所在沟道", "river_code", None),
            ("断面标识", "is_control_section", None),
            ("断面形态", "section_shape", None),
            ("是否跨县", "is_cross_county", None),
            ("河床底质", "river_bed_material", None),
            ("测量方法", "survey_method", None),
            ("基点经度(°)", "base_lon", lambda v: f"{v:.6f}" if v else ""),
            ("基点纬度(°)", "base_lat", lambda v: f"{v:.6f}" if v else ""),
            ("基点高程(m)", "base_elevation", lambda v: f"{v:.3f}" if v else ""),
            ("方位角(°)", "azimuth", lambda v: f"{v:.2f}" if v else ""),
            ("历史最高水位(m)", "hmz", lambda v: f"{v:.2f}" if v else ""),
            ("成灾水位(m)", "czz", lambda v: f"{v:.2f}" if v else ""),
            ("测量点数", "points", lambda v: str(len(v)) if v else "0"),
            ("分类", "category", None),
            ("来源文件", "source_file", None),
            ("文件名", "file_name", None),
            ("文件路径", "file_path", None),
            ("Sheet名称", "sheet_name", None),
        ]

        wrap_fields = ["source_file", "file_name", "file_path"]

        for i, (label, field, formatter) in enumerate(info_fields):
            raw_val = sec.get(field, "")
            if formatter:
                val = formatter(raw_val)
            else:
                val = str(raw_val) if raw_val else ""

            row = i // 2
            col = (i % 2) * 2

            key_label = QLabel(label)
            key_label.setStyleSheet(label_style)
            val_label = QLabel(val)
            val_label.setStyleSheet(value_style)
            val_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            if field in wrap_fields:
                val_label.setWordWrap(True)
            self.info_grid.addWidget(key_label, row, col)
            self.info_grid.addWidget(val_label, row, col + 1)

        self.info_grid.setColumnStretch(1, 1)
        self.info_grid.setColumnStretch(3, 1)

    def set_current_section_key(self, key: str):
        self._current_section_key = key

    def _render_current_page(self):
        total = len(self._all_points)
        page_size = self._page_size
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        start = self._current_page * page_size
        end = min(start + page_size, total)
        page_points = self._all_points[start:end]

        display_count = len(page_points)
        row_height = self.points_table.verticalHeader().defaultSectionSize()
        header_height = self.points_table.horizontalHeader().height()
        frame_width = self.points_table.frameWidth() * 2
        grid_lines = display_count + 1
        table_height = row_height * display_count + header_height + frame_width + grid_lines + 6
        self.points_table.setFixedHeight(table_height)

        self.points_table.setRowCount(display_count)
        theme = self._theme_manager.get_current_theme()
        for row, p in enumerate(page_points):
            seq_val = p.get("seq", "")
            seq_str = str(int(seq_val)) if seq_val and isinstance(seq_val, (int, float)) else str(seq_val) if seq_val else ""
            items = [
                seq_str,
                str(p.get("feature_desc", "")),
                f"{p.get('distance', 0):.3f}" if p.get("distance") is not None else "",
                f"{p.get('elevation', 0):.3f}" if p.get("elevation") is not None else "",
                f"{p['lon']:.6f}" if p.get("lon") else "",
                f"{p['lat']:.6f}" if p.get("lat") else "",
                str(p.get("roughness", "")),
                "是" if p.get("isFeature") else "",
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                if p.get("isFeature"):
                    item.setBackground(QColor(theme.get('success_bg', '#dcfce7')))
                self.points_table.setItem(row, col, item)

        self.points_page_info.setText(f"{start + 1}-{end}/{total}")
        self.points_prev_btn.setEnabled(self._current_page > 0)
        self.points_next_btn.setEnabled(self._current_page < total_pages - 1)

    def _on_page_size_changed(self):
        self._page_size = int(self.points_page_size_combo.currentText())
        self._current_page = 0
        self._render_current_page()

    def _on_prev_page(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._render_current_page()

    def _on_next_page(self):
        total = len(self._all_points)
        total_pages = (total + self._page_size - 1) // self._page_size if total > 0 else 1
        if self._current_page < total_pages - 1:
            self._current_page += 1
            self._render_current_page()

    def _preview_excel(self):
        if not self._current_section_key:
            QMessageBox.warning(self, "警告", "请先选择一个断面")
            return
        if not self._service:
            return
        info = self._service.get_excel_preview_info(self._current_section_key)
        if not info:
            return
        source_file = info["source_file"]
        sheet_name = info["sheet_name"]
        if not source_file or not os.path.exists(source_file):
            QMessageBox.warning(self, "警告", "原始Excel文件不存在")
            return
        dialog = ExcelPreviewDialog(source_file, sheet_name, self)
        dialog.show()
