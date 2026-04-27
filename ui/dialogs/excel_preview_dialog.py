# -*- coding: utf-8 -*-
"""
Excel预览对话框 - 在弹出页面直接预览Excel内容
"""

import os
import pandas as pd
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTabWidget, QWidget, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from core.theme_manager import get_theme_manager

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    HAS_WEB_ENGINE = True
except ImportError:
    HAS_WEB_ENGINE = False


class ExcelPreviewDialog(QDialog):
    """Excel预览对话框"""

    def __init__(self, file_path: str, sheet_name: str = None, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.theme_manager = get_theme_manager()
        self.setWindowTitle(f"Excel预览 - {os.path.basename(file_path)}")
        self.setMinimumSize(900, 600)
        self.resize(1200, 800)
        self.setStyleSheet(self.theme_manager.get_stylesheet())
        self._init_ui()
        self._load_excel()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        header_layout = QHBoxLayout()
        file_label = QLabel(f"文件: {self.file_path}")
        file_label.setObjectName("pageSubtitle")
        header_layout.addWidget(file_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("resultTabs")
        layout.addWidget(self.tab_widget, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _load_excel(self):
        try:
            xl = pd.ExcelFile(self.file_path)
            sheet_names = xl.sheet_names
            
            target_sheet = self.sheet_name
            if target_sheet and target_sheet in sheet_names:
                sheet_names = [target_sheet] + [s for s in sheet_names if s != target_sheet]
            
            for sheet in sheet_names[:10]:
                df = pd.read_excel(self.file_path, sheet_name=sheet, header=None)
                self._add_sheet_tab(sheet, df)
                
        except Exception as e:
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel(f"加载Excel失败: {str(e)}")
            error_label.setAlignment(Qt.AlignCenter)
            error_layout.addWidget(error_label)
            self.tab_widget.addTab(error_widget, "错误")

    def _add_sheet_tab(self, sheet_name: str, df: pd.DataFrame):
        if HAS_WEB_ENGINE and len(df) > 50:
            web_view = QWebEngineView()
            html = self._generate_table_html(df, sheet_name)
            web_view.setHtml(html)
            self.tab_widget.addTab(web_view, sheet_name)
        else:
            table_widget = QTableWidget()
            table_widget.setRowCount(len(df))
            table_widget.setColumnCount(len(df.columns))
            
            theme = self.theme_manager.get_current_theme()
            
            for row in range(min(len(df), 200)):
                for col in range(len(df.columns)):
                    val = df.iloc[row, col]
                    text = str(val) if val is not None and str(val) != 'nan' else ""
                    item = QTableWidgetItem(text)
                    if row == 0:
                        item.setBackground(QColor(theme.get('success_bg', '#dcfce7')))
                    table_widget.setItem(row, col, item)
            
            table_widget.setHorizontalHeaderLabels([str(i) for i in range(len(df.columns))])
            table_widget.verticalHeader().setVisible(False)
            table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
            table_widget.setStyleSheet("QTableWidget { gridline-color: rgba(200,200,200,0.30); } QTableWidget::item { padding: 2px; }")
            
            for col in range(len(df.columns)):
                table_widget.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)
            
            self.tab_widget.addTab(table_widget, sheet_name)

    def _generate_table_html(self, df: pd.DataFrame, sheet_name: str) -> str:
        theme = self.theme_manager.get_current_theme()
        bg_color = theme.get('content_bg', '#ffffff')
        text_color = theme.get('text_primary', '#1f2937')
        border_color = theme.get('border_color', '#e5e7eb')
        header_bg = theme.get('success_bg', '#dcfce7')
        
        html_parts = []
        html_parts.append(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
body {{ font-family: sans-serif; background: {bg_color}; color: {text_color}; margin: 0; padding: 8px; }}
h2 {{ margin: 0 0 8px 0; font-size: 14px; }}
table {{ border-collapse: collapse; width: 100%; font-size: 12px; }}
th, td {{ border: 1px solid {border_color}; padding: 4px 8px; text-align: left; white-space: nowrap; }}
th {{ background: {header_bg}; font-weight: bold; }}
tr:nth-child(even) td {{ background: rgba(0,0,0,0.03); }}
</style>
</head>
<body>
<h2>{sheet_name}</h2>
<table>
""")
        
        html_parts.append("<thead><tr>")
        for col in range(len(df.columns)):
            val = df.iloc[0, col] if len(df) > 0 else ""
            html_parts.append(f"<th>{str(val) if val is not None else ''}</th>")
        html_parts.append("</tr></thead>")
        
        html_parts.append("<tbody>")
        for row in range(1, min(len(df), 500)):
            html_parts.append("<tr>")
            for col in range(len(df.columns)):
                val = df.iloc[row, col]
                text = str(val) if val is not None and str(val) != 'nan' else ""
                html_parts.append(f"<td>{text}</td>")
            html_parts.append("</tr>")
        html_parts.append("</tbody>")
        
        html_parts.append("</table></body></html>")
        return '\n'.join(html_parts)