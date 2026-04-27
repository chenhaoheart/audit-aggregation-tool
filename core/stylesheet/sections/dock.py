# -*- coding: utf-8 -*-
"""Generate QSS for dock with frosted crystal glass effect."""
from typing import Dict


def generate_dock_stylesheet(theme: Dict[str, str]) -> str:
    return f"""
/* ========== 主窗口 ========== */
QWidget#mainWidget {{
    background-color: {theme['content_bg']};
}}

/* ========== Dock 栏 - 深色毛玻璃 ========== */
QFrame#dockBar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {theme['sidebar_bg_start']}, stop:1 {theme['sidebar_bg_end']});
    border-right: 1px solid {theme['sidebar_separator']};
}}

QLabel#dockTitle {{
    font-size: 17px;
    font-weight: 700;
    color: {theme['sidebar_title']};
    padding: 16px 8px 2px 8px;
}}

QLabel#dockSubtitle {{
    font-size: 10px;
    color: {theme['sidebar_subtitle']};
    padding: 0 8px 4px 8px;
}}

QFrame#dockSeparator {{
    background-color: {theme['sidebar_separator']};
    max-height: 1px;
    margin: 4px 12px;
}}

QPushButton#dockBtn {{
    background: transparent;
    color: {theme['sidebar_text']};
    border: none;
    border-radius: 16px;
    padding: 0;
    margin: 2px 0;
    font-size: 24px;
    min-width: 56px;
    max-width: 56px;
    min-height: 56px;
    max-height: 56px;
}}

QPushButton#dockBtn:hover {{
    background: {theme['hover_glow']};
    color: {theme['sidebar_text_hover']};
}}

QPushButton#dockBtn:checked {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme['sidebar_btn_checked_start']}, stop:1 {theme['sidebar_btn_checked_end']});
    color: {theme['sidebar_text_checked']};
    border-left: 3px solid {theme['accent_color']};
}}

QPushButton#dockCollapseBtn {{
    background: transparent;
    color: {theme['collapse_btn_text']};
    border: 1px solid {theme['collapse_btn_border']};
    border-radius: 12px;
    padding: 8px 0;
    font-size: 12px;
    margin: 2px 0;
    min-width: 56px;
    max-width: 56px;
    min-height: 34px;
}}

QPushButton#dockCollapseBtn:hover {{
    background: {theme['collapse_btn_hover_bg']};
    color: {theme['collapse_btn_hover_text']};
    border-color: {theme['accent_color']};
}}
"""
