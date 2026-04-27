# -*- coding: utf-8 -*-
"""Generate QSS for scrollbars with frosted glass effect."""
from typing import Dict


def generate_scrollbars_stylesheet(theme: Dict[str, str]) -> str:
    return f"""
/* ========== 全局滚动条 ========== */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0;
    border-radius: 5px;
}}

QScrollBar::handle:vertical {{
    background: rgba(180,180,180,0.35);
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: rgba(232,168,56,0.40);
}}

QScrollBar::handle:vertical:pressed {{
    background: rgba(232,168,56,0.55);
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
    border: none;
    background: none;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 0;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal {{
    background: rgba(180,180,180,0.35);
    border-radius: 5px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background: rgba(232,168,56,0.40);
}}

QScrollBar::handle:horizontal:pressed {{
    background: rgba(232,168,56,0.55);
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
    border: none;
    background: none;
}}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background: transparent;
}}

/* ========== QScrollArea 滚动条 ========== */
QScrollArea > QScrollBar:vertical {{
    background: transparent;
    width: 10px;
}}

QScrollArea > QScrollBar::handle:vertical {{
    background: rgba(160,160,160,0.50);
    border-radius: 5px;
    min-height: 30px;
}}

QScrollArea > QScrollBar::handle:vertical:hover {{
    background: rgba(232,168,56,0.60);
}}

QScrollArea > QScrollBar::handle:vertical:pressed {{
    background: rgba(232,168,56,0.75);
}}

QScrollArea > QScrollBar::add-line:vertical,
QScrollArea > QScrollBar::sub-line:vertical {{
    height: 0;
    border: none;
    background: none;
}}

QScrollArea > QScrollBar::add-page:vertical,
QScrollArea > QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QScrollArea > QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
}}

QScrollArea > QScrollBar::handle:horizontal {{
    background: rgba(160,160,160,0.50);
    border-radius: 5px;
    min-width: 30px;
}}

QScrollArea > QScrollBar::handle:horizontal:hover {{
    background: rgba(232,168,56,0.60);
}}

QScrollArea > QScrollBar::handle:horizontal:pressed {{
    background: rgba(232,168,56,0.75);
}}

QScrollArea > QScrollBar::add-line:horizontal,
QScrollArea > QScrollBar::sub-line:horizontal {{
    width: 0;
    border: none;
    background: none;
}}

QScrollArea > QScrollBar::add-page:horizontal,
QScrollArea > QScrollBar::sub-page:horizontal {{
    background: transparent;
}}
"""