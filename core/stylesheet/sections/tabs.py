# -*- coding: utf-8 -*-
"""Generate QSS for tabs with frosted crystal glass effect."""
from typing import Dict


def generate_tabs_stylesheet(theme: Dict[str, str]) -> str:
    return f"""
/* ========== Tab控件 - 琥珀金下划线风格 ========== */
QTabWidget::pane {{
    border: none;
    border-top: 1px solid transparent;
    top: -1px;
    background: transparent;
}}

QTabBar::tab {{
    background: {theme['tab_bg']};
    color: {theme['tab_text']};
    border: none;
    border-bottom: 2px solid transparent;
    padding: 10px 12px;
    font-size: 13px;
    font-weight: 500;
    margin-right: 3px;
    border-radius: 6px 6px 0 0;
    min-width: 80px;
}}

QTabBar::tab:selected {{
    color: {theme['accent_color']};
    border-bottom: 2.5px solid {theme['tab_underline_color']};
    font-weight: 600;
    background: transparent;
}}

QTabBar::tab:hover:!selected {{
    color: {theme['tab_hover_text']};
    background: {theme['tab_hover_bg']};
    border-bottom: 2px solid {theme['tab_hover_bg']};
}}

/* Tab 页面内表格 —— 去边框/圆角 */
QTabWidget QTableWidget {{
    border: none;
    border-radius: 0;
}}
"""
