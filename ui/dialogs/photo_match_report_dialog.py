# -*- coding: utf-8 -*-
"""
照片匹配校验报告对话框

展示附表2/3与照片的匹配校验结果，支持页面查看和导出Excel
"""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTabWidget, QWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QFileDialog, QMessageBox, QAbstractItemView,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont, QPalette

from core.theme_manager import get_theme_manager
from services.photo_match_service import PhotoMatchService


class PhotoMatchReportDialog(QDialog):
    """照片匹配校验报告对话框"""

    def __init__(self, match_result: dict, parent=None):
        super().__init__(parent)
        self.match_result = match_result
        self.theme_manager = get_theme_manager()

        self.setWindowTitle("附表与照片匹配校验报告")
        self.setMinimumSize(1000, 650)
        self.resize(1200, 800)

        self._init_ui()
        self._apply_theme_style()

    def _init_ui(self):
        theme = self.theme_manager.get_current_theme()
        self.setStyleSheet(f"""
            QDialog {{
                background: {theme.get('content_bg', '#f8fafc')};
            }}
        """)

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        header_card = QFrame()
        accent_color = theme.get('accent_color', '#FF7F50')
        info_color = theme.get('info_text', '#1565C0')
        header_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {accent_color}, stop:1 {info_color});
                border-radius: 0px;
            }}
        """)
        header_layout = QVBoxLayout(header_card)
        header_layout.setSpacing(8)
        header_layout.setContentsMargins(24, 20, 24, 16)

        title_row = QHBoxLayout()
        title_row.setSpacing(12)

        title_text_layout = QVBoxLayout()
        title_text_layout.setSpacing(2)

        title = QLabel("附表与照片匹配校验报告")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: white;")
        title_text_layout.addWidget(title)

        summary = self.match_result.get('summary', {})
        subtitle_text = (
            f"附表2: {summary.get('fubiao2_total', 0)}条记录，"
            f"匹配{summary.get('fubiao2_matched', 0)}条  |  "
            f"附表3: {summary.get('fubiao3_total', 0)}条记录，"
            f"匹配{summary.get('fubiao3_matched', 0)}条"
        )
        subtitle = QLabel(subtitle_text)
        subtitle.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.8);")
        title_text_layout.addWidget(subtitle)

        title_row.addLayout(title_text_layout, 1)
        header_layout.addLayout(title_row)

        badges_row = QHBoxLayout()
        badges_row.setSpacing(12)

        f2_matched = summary.get('fubiao2_matched', 0)
        f2_total = summary.get('fubiao2_total', 0)
        f3_matched = summary.get('fubiao3_matched', 0)
        f3_total = summary.get('fubiao3_total', 0)
        photo_unmatched = summary.get('photo_unmatched_f2', 0) + summary.get('photo_unmatched_f3', 0)

        success_color = theme.get('success_text', '#2E7D32')
        warning_color = theme.get('warning_text', '#FF8F00')
        error_color = theme.get('error_text', '#D32F2F')

        badge_items = [
            ("附表2", f2_matched, f2_total, accent_color),
            ("附表3", f3_matched, f3_total, info_color),
            ("未匹配照片", photo_unmatched, None, warning_color),
        ]

        for label, matched, total, badge_color in badge_items:
            badge = QFrame()
            is_complete = (matched == total) if total is not None else (matched == 0)
            is_warning = not is_complete and matched > 0

            indicator_color = success_color if is_complete else (warning_color if is_warning else error_color)

            badge.setStyleSheet(f"""
                QFrame {{
                    background: rgba(255,255,255,0.15);
                    border: none;
                    border-radius: 12px;
                }}
            """)
            badge.setFixedHeight(36)

            bl = QHBoxLayout(badge)
            bl.setContentsMargins(12, 6, 12, 6)
            bl.setSpacing(8)

            status_bar = QFrame()
            status_bar.setStyleSheet(f"""
                QFrame {{
                    background: {indicator_color};
                    border-radius: 2px;
                }}
            """)
            status_bar.setFixedSize(3, 24)
            bl.addWidget(status_bar)

            lbl_text = QLabel(label)
            lbl_text.setStyleSheet("""
                color: rgba(255,255,255,0.85);
                font-size: 13px;
                font-weight: 500;
            """)
            bl.addWidget(lbl_text)

            if total is not None and total > 0:
                percentage = int((matched / total) * 100)
                stat_text = QLabel(f"{matched}/{total}")
                stat_text.setStyleSheet(f"""
                    color: white;
                    font-size: 14px;
                    font-weight: 700;
                """)
                bl.addWidget(stat_text)

                pct_label = QLabel(f"{percentage}%")
                pct_color = success_color if is_complete else (warning_color if is_warning else error_color)
                pct_label.setStyleSheet(f"color: {pct_color}; font-size: 12px; font-weight: 600;")
                bl.addWidget(pct_label)
            else:
                stat_text = QLabel(str(matched))
                stat_color = success_color if matched == 0 else warning_color
                stat_text.setStyleSheet(f"""
                    color: {stat_color};
                    font-size: 14px;
                    font-weight: 700;
                """)
                bl.addWidget(stat_text)

                unit_label = QLabel("项")
                unit_label.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 12px;")
                bl.addWidget(unit_label)

            bl.addStretch()

            badges_row.addWidget(badge)

        badges_row.addStretch()
        header_layout.addLayout(badges_row)

        layout.addWidget(header_card)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setSpacing(0)
        body_layout.setContentsMargins(20, 16, 20, 16)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {theme.get('card_border', '#e2e8f0')};
                border-radius: 8px;
                background: {theme.get('card_bg', '#ffffff')};
                top: -1px;
            }}
            QTabBar::tab {{
                background: {theme.get('content_bg', '#f8fafc')};
                border: 1px solid {theme.get('card_border', '#e2e8f0')};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 8px 16px;
                margin-right: 2px;
                font-size: 13px;
                color: {theme.get('text_secondary', '#475569')};
            }}
            QTabBar::tab:selected {{
                background: {theme.get('card_bg', '#ffffff')};
                color: {theme.get('accent_color', '#FF7F50')};
                font-weight: 600;
                border-bottom: 2px solid {theme.get('accent_color', '#FF7F50')};
            }}
            QTabBar::tab:hover {{
                background: {theme.get('surface_1', '#f1f5f9')};
            }}
        """)
        body_layout.addWidget(self.tab_widget, 1)

        self._build_tabs()

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setContentsMargins(0, 12, 0, 0)

        self.export_btn = QPushButton("导出Excel")
        self.export_btn.setStyleSheet(f"""
            QPushButton {{
                background: {theme.get('accent_color', '#FF7F50')}; color: white; border: none;
                border-radius: 8px; padding: 10px 24px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {theme.get('btn_primary_hover_start', '#FF9977')}; }}
            QPushButton:pressed {{ background: {theme.get('btn_primary_pressed_start', '#E65100')}; }}
        """)
        self.export_btn.clicked.connect(self._on_export)
        btn_layout.addWidget(self.export_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {theme.get('text_secondary', '#475569')};
                border: 1px solid {theme.get('card_border', '#e2e8f0')}; border-radius: 8px;
                padding: 10px 24px; font-size: 13px;
            }}
            QPushButton:hover {{ background: {theme.get('surface_1', '#f1f5f9')}; }}
        """)
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)

        body_layout.addLayout(btn_layout)
        layout.addWidget(body, 1)

        self.setLayout(layout)

    def _build_tabs(self):
        self._add_summary_tab()
        self._add_fubiao2_matched_tab()
        self._add_fubiao2_unmatched_tab()
        self._add_fubiao3_matched_tab()
        self._add_fubiao3_unmatched_tab()
        self._add_photo_unmatched_tab()

    def _theme_color(self, key: str, fallback: str) -> str:
        return self.theme_manager.get_current_theme().get(key, fallback)

    def _make_empty_tab(self, text: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {self._theme_color('success_text', '#2E7D32')}; font-size: 14px; font-weight: 500;")
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)
        return widget

    def _add_summary_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        theme = self.theme_manager.get_current_theme()
        summary = self.match_result.get('summary', {})

        accent_color = theme.get('accent_color', '#FF7F50')
        info_color = theme.get('info_text', '#1565C0')
        success_color = theme.get('success_text', '#2E7D32')
        warning_color = theme.get('warning_text', '#FF8F00')
        error_color = theme.get('error_text', '#D32F2F')

        items = [
            ("附表2（跨沟道路、桥涵）", accent_color, [
                ("总记录数", summary.get('fubiao2_total', 0), accent_color),
                ("匹配照片成功", summary.get('fubiao2_matched', 0), success_color),
                ("未匹配照片", summary.get('fubiao2_unmatched', 0), error_color),
            ]),
            ("附表3（沟滩占地）", info_color, [
                ("总记录数", summary.get('fubiao3_total', 0), info_color),
                ("匹配照片成功", summary.get('fubiao3_matched', 0), success_color),
                ("未匹配照片", summary.get('fubiao3_unmatched', 0), error_color),
            ]),
            ("照片未匹配附表", warning_color, [
                ("跨沟道路/桥涵照片", summary.get('photo_unmatched_f2', 0), warning_color),
                ("沟滩占地照片", summary.get('photo_unmatched_f3', 0), warning_color),
            ])
        ]

        for group_title, group_color, group_items in items:
            group_frame = QFrame()
            group_frame.setStyleSheet(f"""
                QFrame {{
                    background: {theme.get('card_bg', '#ffffff')};
                    border: 1px solid {theme.get('card_border', '#e2e8f0')};
                    border-radius: 12px;
                }}
            """)

            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(12)
            shadow.setColor(QColor(0, 0, 0, 25))
            shadow.setOffset(0, 4)
            group_frame.setGraphicsEffect(shadow)

            group_layout = QVBoxLayout(group_frame)
            group_layout.setSpacing(12)
            group_layout.setContentsMargins(18, 16, 18, 16)

            title_row = QHBoxLayout()
            title_row.setSpacing(10)

            color_bar = QFrame()
            color_bar.setStyleSheet(f"""
                QFrame {{
                    background: {group_color};
                    border-radius: 3px;
                }}
            """)
            color_bar.setFixedSize(4, 20)
            title_row.addWidget(color_bar)

            title_lbl = QLabel(group_title)
            title_lbl.setStyleSheet(f"""
                font-size: 14px;
                font-weight: 600;
                color: {theme.get('text_primary', '#1e293b')};
            """)
            title_row.addWidget(title_lbl)
            title_row.addStretch()
            group_layout.addLayout(title_row)

            row_layout = QHBoxLayout()
            row_layout.setSpacing(12)
            for label, value, color in group_items:
                card = QFrame()
                card.setStyleSheet(f"""
                    QFrame {{
                        background: {theme.get('content_bg', '#f8fafc')};
                        border: 1px solid {theme.get('card_border', '#f1f5f9')};
                        border-radius: 10px;
                    }}
                """)
                card.setMinimumWidth(120)

                card_layout = QHBoxLayout(card)
                card_layout.setSpacing(8)
                card_layout.setContentsMargins(12, 8, 12, 8)

                color_indicator = QFrame()
                color_indicator.setStyleSheet(f"""
                    QFrame {{
                        background: {color};
                        border-radius: 3px;
                    }}
                """)
                color_indicator.setFixedSize(4, 20)
                card_layout.addWidget(color_indicator)

                val_lbl = QLabel(str(value))
                val_lbl.setStyleSheet(f"""
                    color: {color};
                    font-size: 20px;
                    font-weight: 700;
                """)
                card_layout.addWidget(val_lbl)

                name_lbl = QLabel(label)
                name_lbl.setStyleSheet(f"""
                    color: {theme.get('text_secondary', '#475569')};
                    font-size: 12px;
                """)
                card_layout.addWidget(name_lbl)

                card_layout.addStretch()

                row_layout.addWidget(card)

            group_layout.addLayout(row_layout)
            layout.addWidget(group_frame)

        layout.addStretch()
        self.tab_widget.addTab(widget, "汇总")

    def _add_fubiao2_matched_tab(self):
        matched = self.match_result.get('fubiao2', {}).get('matched', [])
        if not matched:
            self.tab_widget.addTab(self._make_empty_tab("附表2所有记录均已匹配照片"), "附表2-已匹配")
            return

        headers = ['名称', '编码', '河流名称', '河流代码', '经度', '纬度', '照片数量', '照片文件名', '命名校验', '照片文件夹', '河流代码一致']
        table = self._create_table(matched, headers, self._fubiao2_matched_row)
        self.tab_widget.addTab(table, f"附表2-已匹配 ({len(matched)})")

    def _add_fubiao2_unmatched_tab(self):
        unmatched = self.match_result.get('fubiao2', {}).get('unmatched_records', [])
        if not unmatched:
            self.tab_widget.addTab(self._make_empty_tab("附表2所有记录均已匹配照片，无未匹配项"), "附表2-未匹配")
            return

        headers = ['名称', '编码', '河流名称', '河流代码', '经度', '纬度', '未匹配原因']
        table = self._create_table(unmatched, headers, self._fubiao2_unmatched_row)
        self.tab_widget.addTab(table, f"附表2-未匹配 ({len(unmatched)})")

    def _add_fubiao3_matched_tab(self):
        matched = self.match_result.get('fubiao3', {}).get('matched', [])
        if not matched:
            self.tab_widget.addTab(self._make_empty_tab("附表3所有记录均已匹配照片"), "附表3-已匹配")
            return

        headers = ['名称', '编号', '河流名称', '河流代码', '经度', '纬度', '照片数量', '照片文件名', '命名校验', '照片文件夹', '河流代码一致']
        table = self._create_table(matched, headers, self._fubiao3_matched_row)
        self.tab_widget.addTab(table, f"附表3-已匹配 ({len(matched)})")

    def _add_fubiao3_unmatched_tab(self):
        unmatched = self.match_result.get('fubiao3', {}).get('unmatched_records', [])
        if not unmatched:
            self.tab_widget.addTab(self._make_empty_tab("附表3所有记录均已匹配照片，无未匹配项"), "附表3-未匹配")
            return

        headers = ['名称', '编号', '河流名称', '河流代码', '经度', '纬度', '未匹配原因']
        table = self._create_table(unmatched, headers, self._fubiao3_unmatched_row)
        self.tab_widget.addTab(table, f"附表3-未匹配 ({len(unmatched)})")

    def _add_photo_unmatched_tab(self):
        unmatched_f2 = self.match_result.get('unmatched_photos', {}).get('fubiao2_type', [])
        unmatched_f3 = self.match_result.get('unmatched_photos', {}).get('fubiao3_type', [])
        all_unmatched = []

        for p in unmatched_f2:
            all_unmatched.append({
                'code': p['code'],
                'river_code': p['river_code'],
                'photo_count': p['photo_count'],
                'folder_path': p['folder_path'],
                'type': '跨沟道路和桥涵'
            })
        for p in unmatched_f3:
            all_unmatched.append({
                'code': p['code'],
                'river_code': p['river_code'],
                'photo_count': p['photo_count'],
                'folder_path': p['folder_path'],
                'type': '沟滩占地对象'
            })

        if not all_unmatched:
            self.tab_widget.addTab(self._make_empty_tab("所有照片文件夹均已匹配附表记录"), "照片-未匹配附表")
            return

        headers = ['照片编码', '河流代码', '照片数量', '照片文件夹', '类型']
        table = self._create_table(all_unmatched, headers, self._photo_unmatched_row)
        self.tab_widget.addTab(table, f"照片-未匹配附表 ({len(all_unmatched)})")

    def _create_table(self, data: list, headers: list, row_builder) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        theme = self.theme_manager.get_current_theme()
        accent_color = theme.get('accent_color', '#FF7F50')
        table = QTableWidget()
        table.setRowCount(len(data))
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)
        table.setStyleSheet(f"""
            QTableWidget {{
                gridline-color: {theme.get('card_border', '#f1f5f9')};
                alternate-background-color: {theme.get('content_bg', '#f8fafc')};
                background: {theme.get('card_bg', '#ffffff')};
                border: none;
                font-size: 12px;
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                border-bottom: 1px solid {theme.get('card_border', '#f1f5f9')};
                color: {theme.get('text_primary', '#1e293b')};
            }}
            QTableWidget::item:selected {{
                background: {theme.get('table_selection_bg', 'rgba(255,183,150,0.30)')};
                color: {accent_color};
            }}
            QHeaderView::section {{
                background: {theme.get('content_bg', '#f8fafc')};
                padding: 8px 10px;
                border: none;
                border-bottom: 2px solid {accent_color}30;
                font-weight: 600;
                font-size: 12px;
                color: {theme.get('text_secondary', '#475569')};
            }}
        """)

        for row_idx, item in enumerate(data):
            row_data = row_builder(item)
            for col_idx, (text, color) in enumerate(row_data):
                cell = QTableWidgetItem(str(text) if text is not None else '')
                if color:
                    cell.setForeground(QColor(color))
                table.setItem(row_idx, col_idx, cell)

        table.horizontalHeader().setStretchLastSection(True)
        for col in range(len(headers) - 1):
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)

        layout.addWidget(table)
        return widget

    def _get_row_colors(self) -> dict:
        theme = self.theme_manager.get_current_theme()
        return {
            'accent': theme.get('accent_color', '#FF7F50'),
            'info': theme.get('info_text', '#1565C0'),
            'success': theme.get('success_text', '#2E7D32'),
            'warning': theme.get('warning_text', '#FF8F00'),
            'error': theme.get('error_text', '#D32F2F'),
            'text_secondary': theme.get('text_secondary', '#475569'),
            'text_muted': theme.get('text_muted', '#94a3b8'),
        }

    def _fubiao2_matched_row(self, m: dict) -> list:
        colors = self._get_row_colors()
        river_code_match = m.get('river_code_match', True)
        name_match = m.get('name_match', True)
        return [
            (m.get('name', ''), None),
            (m.get('code', ''), colors['accent']),
            (m.get('river_name', ''), None),
            (m.get('river_code', ''), None),
            (m.get('longitude', ''), None),
            (m.get('latitude', ''), None),
            (m.get('photo_count', 0), None),
            (m.get('photo_names', ''), colors['text_secondary']),
            ('通过' if name_match else '不通过', colors['success'] if name_match else colors['error']),
            (m.get('photo_folder', ''), colors['text_muted']),
            ('是' if river_code_match else '否', colors['success'] if river_code_match else colors['error']),
        ]

    def _fubiao2_unmatched_row(self, r: dict) -> list:
        colors = self._get_row_colors()
        return [
            (str(r.get('5.名称', '')), None),
            (str(r.get('6.编码', '')), colors['error']),
            (str(r.get('15.河流名称', '')), None),
            (str(r.get('16.河流代码', '')), None),
            (r.get('7.经度', ''), None),
            (r.get('8.纬度', ''), None),
            (r.get('_match_reason', ''), colors['error']),
        ]

    def _fubiao3_matched_row(self, m: dict) -> list:
        colors = self._get_row_colors()
        river_code_match = m.get('river_code_match', True)
        name_match = m.get('name_match', True)
        return [
            (m.get('name', ''), None),
            (m.get('code', ''), colors['info']),
            (m.get('river_name', ''), None),
            (m.get('river_code', ''), None),
            (m.get('longitude', ''), None),
            (m.get('latitude', ''), None),
            (m.get('photo_count', 0), None),
            (m.get('photo_names', ''), colors['text_secondary']),
            ('通过' if name_match else '不通过', colors['success'] if name_match else colors['error']),
            (m.get('photo_folder', ''), colors['text_muted']),
            ('是' if river_code_match else '否', colors['success'] if river_code_match else colors['error']),
        ]

    def _fubiao3_unmatched_row(self, r: dict) -> list:
        colors = self._get_row_colors()
        return [
            (str(r.get('5.名称', '')), None),
            (str(r.get('6.编号', '')), colors['error']),
            (str(r.get('14. 河流名称', '')), None),
            (str(r.get('15. 河流代码', '')), None),
            (r.get('7.经度', ''), None),
            (r.get('8.纬度', ''), None),
            (r.get('_match_reason', ''), colors['error']),
        ]

    def _photo_unmatched_row(self, p: dict) -> list:
        colors = self._get_row_colors()
        return [
            (p.get('code', ''), colors['warning']),
            (p.get('river_code', ''), None),
            (p.get('photo_count', 0), None),
            (p.get('folder_path', ''), colors['text_muted']),
            (p.get('type', ''), None),
        ]

    def _on_export(self):
        default_name = "附表照片匹配校验报告.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出校验报告", default_name, "Excel文件 (*.xlsx)"
        )
        if not file_path:
            return

        success = PhotoMatchService.export_to_excel(self.match_result, file_path)
        if success:
            QMessageBox.information(self, "导出成功", f"校验报告已导出至:\n{file_path}")
        else:
            QMessageBox.critical(self, "导出失败", "导出Excel文件时发生错误，请检查文件是否被占用。")

    def _apply_theme_style(self):
        theme = self.theme_manager.get_current_theme()
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(theme.get('content_bg', '#f8fafc')))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
