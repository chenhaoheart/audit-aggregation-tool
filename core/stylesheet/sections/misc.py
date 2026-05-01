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

QPushButton#collapseSectionBtn {{
    text-align: left;
    border: none;
    padding: 4px 0;
    font-weight: 600;
    font-size: 13px;
    background: transparent;
    color: {theme['text_label']};
}}

QPushButton#collapseSectionBtn:hover {{
    color: {theme['accent_color']};
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

/* ========== 图层匹配清单 - 紧凑徽章 ========== */
QLabel#layerBadgePass {{
    background: {theme['badge_pass_bg']};
    color: {theme['badge_pass_text']};
    border: 1px solid {theme['badge_pass_border']};
    border-radius: 10px;
    padding: 2px 4px;
    font-size: 11px;
    font-weight: 600;
}}

QLabel#layerBadgeFail {{
    background: {theme['badge_fail_bg']};
    color: {theme['badge_fail_text']};
    border: 1px solid {theme['badge_fail_border']};
    border-radius: 10px;
    padding: 2px 4px;
    font-size: 11px;
    font-weight: 600;
}}

/* ========== 系统设置对话框 ========== */
QFrame#settingsSidebar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {theme['sidebar_bg_start']}, stop:1 {theme['sidebar_bg_end']});
    border-right: 1px solid {theme['sidebar_separator']};
}}

QLabel#settingsSidebarHeader {{
    color: {theme['sidebar_title']};
    font-size: 15px;
    font-weight: 600;
    padding-left: 16px;
    padding-top: 12px;
    background: transparent;
    border: none;
}}

QPushButton#settingsNavItem {{
    background: transparent;
    color: {theme['sidebar_text']};
    border: none;
    border-radius: 8px;
    text-align: left;
    font-size: 13px;
    font-weight: 400;
    padding: 10px 16px;
    margin: 2px 8px;
}}

QPushButton#settingsNavItem:hover {{
    background: {theme['hover_glow']};
    color: {theme['sidebar_text_hover']};
}}

QPushButton#settingsNavItem:checked {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme['sidebar_btn_checked_start']}, stop:1 {theme['sidebar_btn_checked_end']});
    color: {theme['sidebar_text_checked']};
    font-weight: 600;
}}

QPushButton#settingsCloseBtn {{
    background: transparent;
    color: {theme['text_secondary']};
    border: none;
    border-radius: 6px;
    font-size: 13px;
    padding: 8px 16px;
    margin: 4px 8px;
}}

QPushButton#settingsCloseBtn:hover {{
    background: {theme['hover_glow']};
    color: #ef4444;
}}

QWidget#settingsContent {{
    background: {theme['content_bg']};
    border: none;
}}

QFrame#pageHeader {{
    background: {theme['card_bg']};
    border: 1px solid {theme['card_border']};
    border-radius: 10px;
}}

QFrame#accentBar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {theme['accent_color']}, stop:1 {theme['accent_color']});
    border-radius: 2px;
}}

QLabel#sectionHeaderLg {{
    font-size: 18px;
    font-weight: 700;
    color: {theme['text_primary']};
    background: transparent;
    border: none;
}}

QLabel#sectionHeaderMd {{
    font-size: 14px;
    font-weight: 600;
    color: {theme['text_primary']};
    background: transparent;
    border: none;
}}

QFrame#card {{
    background: {theme['card_bg']};
    border: 1px solid {theme['card_border']};
    border-radius: 10px;
}}

QPushButton#clearBtn {{
    background: transparent;
    color: {theme['text_secondary']};
    border: 1px solid {theme['card_border']};
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 13px;
}}

QPushButton#clearBtn:hover {{
    background: {theme['hover_glow']};
    color: {theme['text_primary']};
    border-color: {theme['accent_color']};
}}
"""
