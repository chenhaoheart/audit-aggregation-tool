# -*- coding: utf-8 -*-
"""Generate QSS for misc (labels, badges, progress bar) with frosted crystal glass effect."""
from typing import Dict


def generate_misc_stylesheet(theme: Dict[str, str]) -> str:
    return f"""
/* ========== 进度条 - 琥珀到青色渐变 ========== */
QProgressBar {{
    border: 1px solid {theme['progress_border']};
    border-radius: 8px;
    text-align: center;
    background: {theme['progress_bg']};
    height: 14px;
    color: {theme['text_primary']};
    font-size: 11px;
    font-weight: 600;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme['progress_chunk_start']}, stop:1 {theme['progress_chunk_end']});
    border-radius: 7px;
}}

/* ========== 标签 ========== */
QLabel {{
    color: {theme['text_primary']};
}}

QLabel#boldLabel {{
    font-weight: 600;
    color: {theme['text_label']};
    font-size: 13px;
}}

QLabel#secondaryLabel {{
    color: {theme['text_secondary']};
    font-size: 12px;
}}

/* ========== 页面标题 ========== */
QLabel#pageTitle {{
    font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif;
    font-size: 26px;
    font-weight: 700;
    color: {theme['header_text_primary']};
}}

QLabel#pageSubtitle {{
    font-size: 13px;
    color: {theme['text_secondary']};
    margin-top: 2px;
}}

/* ========== 状态徽章 - 毛玻璃效果 ========== */
QLabel#badgePass {{
    background: {theme['badge_pass_bg']};
    color: {theme['badge_pass_text']};
    border: 1px solid {theme['badge_pass_border']};
    border-radius: 14px;
    padding: 4px 16px;
    font-size: 12px;
    font-weight: 600;
    min-width: 50px;
}}

QLabel#badgeFail {{
    background: {theme['badge_fail_bg']};
    color: {theme['badge_fail_text']};
    border: 1px solid {theme['badge_fail_border']};
    border-radius: 14px;
    padding: 4px 16px;
    font-size: 12px;
    font-weight: 600;
    min-width: 50px;
}}
"""
