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

/* ========== Dashboard 滚动区域 ========== */
QScrollArea#dashboardScrollArea {{
    background: transparent;
    border: none;
}}

QScrollArea#dashboardScrollArea > QScrollBar:vertical {{
    background: rgba(148,163,184,0.08);
    width: 12px;
    border-radius: 6px;
    margin: 4px 2px;
}}

QScrollArea#dashboardScrollArea > QScrollBar::handle:vertical {{
    background: rgba(100,116,139,0.35);
    border-radius: 6px;
    min-height: 30px;
}}

QScrollArea#dashboardScrollArea > QScrollBar::handle:vertical:hover {{
    background: rgba(100,116,139,0.55);
}}

QScrollArea#dashboardScrollArea > QScrollBar::handle:vertical:pressed {{
    background: rgba(100,116,139,0.70);
}}

QScrollArea#dashboardScrollArea > QScrollBar::add-line:vertical,
QScrollArea#dashboardScrollArea > QScrollBar::sub-line:vertical {{
    height: 0;
    border: none;
    background: none;
}}

QScrollArea#dashboardScrollArea > QScrollBar::add-page:vertical,
QScrollArea#dashboardScrollArea > QScrollBar::sub-page:vertical {{
    background: transparent;
}}

/* ========== 折叠卡片内容滚动条 ========== */
QScrollArea#cardContentScrollArea {{
    background: transparent;
    border: none;
}}

QScrollArea#cardContentScrollArea > QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    border-radius: 3px;
    margin: 2px 0;
}}

QScrollArea#cardContentScrollArea > QScrollBar::handle:vertical {{
    background: rgba(148,163,184,0.25);
    border-radius: 3px;
    min-height: 20px;
}}

QScrollArea#cardContentScrollArea > QScrollBar::handle:vertical:hover {{
    background: rgba(148,163,184,0.45);
}}

QScrollArea#cardContentScrollArea > QScrollBar::add-line:vertical,
QScrollArea#cardContentScrollArea > QScrollBar::sub-line:vertical {{
    height: 0;
    border: none;
    background: none;
}}

QScrollArea#cardContentScrollArea > QScrollBar::add-page:vertical,
QScrollArea#cardContentScrollArea > QScrollBar::sub-page:vertical {{
    background: transparent;
}}

/* ========== 照片画廊滚动区域 ========== */
QScrollArea#photoGalleryScrollArea {{
    background: transparent;
    border: none;
}}

QScrollArea#photoGalleryScrollArea > QScrollBar:vertical {{
    background: rgba(148,163,184,0.08);
    width: 12px;
    border-radius: 6px;
    margin: 4px 2px;
}}

QScrollArea#photoGalleryScrollArea > QScrollBar::handle:vertical {{
    background: rgba(100,116,139,0.35);
    border-radius: 6px;
    min-height: 30px;
}}

QScrollArea#photoGalleryScrollArea > QScrollBar::handle:vertical:hover {{
    background: rgba(100,116,139,0.55);
}}

QScrollArea#photoGalleryScrollArea > QScrollBar::handle:vertical:pressed {{
    background: rgba(100,116,139,0.70);
}}

QScrollArea#photoGalleryScrollArea > QScrollBar::add-line:vertical,
QScrollArea#photoGalleryScrollArea > QScrollBar::sub-line:vertical {{
    height: 0;
    border: none;
    background: none;
}}

QScrollArea#photoGalleryScrollArea > QScrollBar::add-page:vertical,
QScrollArea#photoGalleryScrollArea > QScrollBar::sub-page:vertical {{
    background: transparent;
}}
"""