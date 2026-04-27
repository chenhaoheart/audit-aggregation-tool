# -*- coding: utf-8 -*-
"""Generate QSS for tables with frosted crystal glass effect."""
from typing import Dict


def generate_tables_stylesheet(theme: Dict[str, str]) -> str:
    return f"""
/* ========== 表格 - 毛玻璃效果 ========== */
QTableWidget {{
    border: 1px solid {theme['card_border']};
    border-radius: 12px;
    background: {theme['table_bg']};
    gridline-color: {theme['table_grid']};
    font-size: 13px;
    selection-background-color: {theme['table_selection_bg']};
    color: {theme['text_primary']};
    alternate-background-color: {theme['table_alt_bg']};
}}

/* 表头样式 - 仅底部边框 */
QHeaderView {{
    background: {theme['table_header_bg']};
}}

QHeaderView::section {{
    background: {theme['table_header_bg']};
    color: {theme['table_header_text']};
    padding: 12px 14px;
    border: none;
    border-bottom: 2px solid {theme['card_border']};
    font-weight: 600;
    font-size: 12px;
    letter-spacing: 0.3px;
}}

QHeaderView::section:first {{
    border-top-left-radius: 12px;
}}

QHeaderView::section:last {{
    border-top-right-radius: 12px;
    border-right: none;
}}

QTableWidget QHeaderView::section:vertical {{
    background: {theme['table_alt_bg']};
    color: {theme['text_secondary']};
    border-right: 1px solid {theme['table_grid']};
    border-bottom: 1px solid {theme['table_grid']};
    font-weight: 500;
    font-size: 11px;
    min-width: 40px;
    padding: 4px 2px;
    text-align: center;
}}

QTableWidget QTableCornerButton::section {{
    background: {theme['table_header_bg']};
    border: none;
    border-right: 1px solid {theme['table_grid']};
    border-bottom: 1px solid {theme['table_grid']};
}}

QTableWidget QScrollBar:vertical {{
    background: transparent;
    border: none;
    width: 8px;
    margin: 0;
}}

QTableWidget QScrollBar:horizontal {{
    background: transparent;
    border: none;
    height: 8px;
    margin: 0;
}}

QTableWidget::item {{
    padding: 2px 8px;
    border-bottom: 1px solid {theme['table_item_border']};
    border-left: 3px solid transparent;
    background: transparent;
}}

QTableWidget::item:hover {{
    background: {theme['table_hover_bg']};
    border-left: 3px solid {theme['accent_color']};
}}

QTableWidget::item:selected {{
    background: {theme['table_selection_bg']};
    border-left: 3px solid {theme['accent_color']};
}}
"""
