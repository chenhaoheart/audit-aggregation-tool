# -*- coding: utf-8 -*-
"""Generate QSS for content with frosted crystal glass effect."""
from typing import Dict


def generate_content_stylesheet(theme: Dict[str, str]) -> str:
    return f"""
/* ========== 内容区 — 深海极光底色 ========== */
QFrame#contentFrame {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {theme['content_bg_start']}, stop:1 {theme['content_bg_end']});
    border: none;
}}

/* ========== 页面标题区 - 毛玻璃卡片 ========== */
QFrame#pageHeader {{
    background: {theme['card_bg']};
    border: 1px solid {theme['card_border']};
    border-radius: 16px;
    padding: 0;
}}

QFrame#accentBar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {theme['accent_color']}, stop:1 {theme['btn_primary_end']});
    border-radius: 3px;
}}

QLabel#pageSubtitle {{
    font-size: 13px;
    font-weight: 400;
    color: {theme['text_secondary']};
    line-height: 20px;
}}

/* ========== 分组标题 ========== */
QLabel#sectionHeaderLg {{
    font-size: 26px;
    font-weight: 700;
    color: {theme['header_text_primary']};
    padding: 0;
    font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif;
}}

QLabel#sectionHeaderMd {{
    font-size: 15px;
    font-weight: 600;
    color: {theme['header_text_primary']};
    padding: 0;
}}

QLabel#sectionHeaderSm {{
    font-size: 11px;
    font-weight: 600;
    color: {theme['text_secondary']};
    letter-spacing: 0.5px;
    padding: 4px 0;
    text-transform: uppercase;
}}

/* ========== 对话框背景 ========== */
QDialog {{
    background-color: {theme['content_bg']};
}}
"""
