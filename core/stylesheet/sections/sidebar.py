# -*- coding: utf-8 -*-
"""Generate QSS for Modern Navigation Sidebar."""
from typing import Dict


def generate_sidebar_stylesheet(theme: Dict[str, str]) -> str:
    return f"""
/* ========== Modern Navigation Sidebar ========== */
QFrame#modernSidebar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {theme['sidebar_bg_start']}, stop:1 {theme['sidebar_bg_end']});
    border-right: 1px solid {theme['sidebar_separator']};
}}

QWidget#sidebarHeader {{
    background: transparent;
    border: none;
}}

QLabel#sidebarTitle {{
    font-size: 18px;
    font-weight: 700;
    color: {theme['sidebar_title']};
}}

QLabel#sidebarSubtitle {{
    font-size: 11px;
    color: {theme['sidebar_subtitle']};
}}

QLabel#sidebarCollapsedTitle {{
    font-size: 28px;
    color: {theme['sidebar_title']};
}}

QFrame#sidebarSeparator {{
    background-color: {theme['sidebar_separator']};
    max-height: 1px;
    margin: 4px 12px;
}}

QWidget#navContainer {{
    background: transparent;
    border: none;
}}

QWidget#navItemRow {{
    background: transparent;
    border: none;
}}

QFrame#navIndicator {{
    background: {theme['accent_color']};
    border-radius: 1.5px;
}}

QPushButton#navItem {{
    background: transparent;
    color: {theme['sidebar_text']};
    border: none;
    border-radius: 8px;
    text-align: left;
    font-size: 14px;
    font-weight: 400;
    padding: 10px 14px;
    margin: 1px 4px;
    min-height: 36px;
}}

QPushButton#navItem:hover {{
    background: {theme['hover_glow']};
    color: {theme['sidebar_text_hover']};
}}

QPushButton#navItem:checked {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme['sidebar_btn_checked_start']}, stop:1 {theme['sidebar_btn_checked_end']});
    color: {theme['sidebar_text_checked']};
    font-weight: 600;
}}

QPushButton#navIconBtn {{
    background: transparent;
    color: {theme['sidebar_text']};
    border: none;
    border-radius: 10px;
    padding: 2px;
    margin: 1px;
    font-size: 20px;
    min-width: 48px;
    max-width: 48px;
    min-height: 48px;
    max-height: 48px;
}}

QPushButton#navIconBtn:hover {{
    background: {theme['hover_glow']};
    color: {theme['sidebar_text_hover']};
}}

QPushButton#navIconBtn:checked {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme['sidebar_btn_checked_start']}, stop:1 {theme['sidebar_btn_checked_end']});
    color: {theme['sidebar_text_checked']};
}}

QWidget#iconContainer {{
    background: transparent;
    border: none;
    margin: 0;
    padding: 0;
}}

QWidget#sidebarBottom {{
    background: transparent;
    border: none;
}}

QPushButton#sidebarCollapseBtn {{
    background: transparent;
    color: {theme['collapse_btn_text']};
    border: 1px solid {theme['collapse_btn_border']};
    border-radius: 6px;
    font-size: 12px;
    padding: 6px 8px;
}}

QPushButton#sidebarCollapseBtn:hover {{
    background: {theme['collapse_btn_hover_bg']};
    color: {theme['collapse_btn_hover_text']};
    border-color: {theme['accent_color']};
}}

QPushButton#sidebarThemeBtn {{
    background: transparent;
    color: {theme['sidebar_text']};
    border: none;
    border-radius: 8px;
    padding: 6px 10px;
    margin: 0;
    font-size: 13px;
}}

QPushButton#sidebarThemeBtn:hover {{
    background: {theme['hover_glow']};
    color: {theme['sidebar_text_hover']};
}}

/* ========== Legacy Sidebar (kept for compatibility) ========== */
QFrame#sidebar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {theme['sidebar_bg_start']}, stop:1 {theme['sidebar_bg_end']});
    border: none;
}}

QFrame#sidebarSeparator {{
    background-color: {theme['sidebar_separator']};
    max-height: 1px;
}}

QLabel#sidebarLabel {{
    color: {theme['sidebar_text']};
    font-size: 12px;
}}

QPushButton#sidebarBtn {{
    background: transparent;
    color: {theme['sidebar_text']};
    border: none;
    border-radius: 8px;
    padding: 15px 20px;
    font-size: 14px;
    text-align: left;
    margin: 2px 10px;
}}

QPushButton#sidebarBtn:hover {{
    background: {theme['hover_glow']};
    color: {theme['sidebar_text_hover']};
}}

QPushButton#sidebarBtn:checked {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme['sidebar_btn_checked_start']}, stop:1 {theme['sidebar_btn_checked_end']});
    color: {theme['sidebar_text_checked']};
    font-weight: bold;
}}

QPushButton#sidebarBtnIcon {{
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 0;
    margin: 4px 6px;
    font-size: 20px;
    min-height: 40px;
    max-height: 40px;
}}

QPushButton#sidebarBtnIcon:hover {{
    background: {theme['hover_glow']};
}}

QPushButton#sidebarBtnIcon:checked {{
    background: {theme['glow_primary']};
}}

QLabel#sidebarVersion {{
    font-size: 10px;
    color: {theme['sidebar_version']};
    padding: 2px 8px;
}}

QSlider#zoomSlider {{
    background: transparent;
    border: none;
}}

QSlider#zoomSlider::groove:horizontal {{
    border: none;
    height: 4px;
    background: {theme['slider_groove_bg']};
    border-radius: 2px;
}}

QSlider#zoomSlider::handle:horizontal {{
    background: {theme['accent_color']};
    border: none;
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}

QSlider#zoomSlider::handle:horizontal:hover {{
    background: {theme['accent_color']};
}}

QPushButton#collapseBtn {{
    background: transparent;
    color: {theme['collapse_btn_text']};
    border: 1px solid {theme['collapse_btn_border']};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 12px;
    margin: 0 10px;
}}

QPushButton#collapseBtn:hover {{
    background: {theme['collapse_btn_hover_bg']};
    color: {theme['collapse_btn_hover_text']};
    border-color: {theme['accent_color']};
}}

QPushButton#collapseBtnCollapsed {{
    background: transparent;
    color: {theme['sidebar_text']};
    border: 1px solid {theme['collapse_btn_border']};
    border-radius: 8px;
    padding: 0;
    margin: 4px;
    font-size: 20px;
    min-height: 44px;
    max-height: 44px;
}}

QPushButton#collapseBtnCollapsed:hover {{
    background: {theme['hover_glow']};
    border-color: {theme['accent_color']};
}}

QComboBox#themeCombo {{
    background: transparent;
    color: {theme['sidebar_text']};
    border: 1px solid {theme['collapse_btn_border']};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
    margin: 0 10px;
}}

QComboBox#themeCombo:hover {{
    background: rgba(232,168,56,0.06);
    color: {theme['sidebar_text_hover']};
    border-color: {theme['accent_color']};
}}

QComboBox#themeCombo QAbstractItemView {{
    background: {theme['card_bg']};
    color: {theme['text_primary']};
    border: 1px solid {theme['card_border']};
    selection-background-color: {theme['table_selection_bg']};
}}

/* ========== Ant Design Legacy ========== */
QFrame#antSidebar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {theme['sidebar_bg_start']}, stop:1 {theme['sidebar_bg_end']});
    border-right: 1px solid {theme['sidebar_separator']};
}}

QFrame#sidebarHeader {{
    background: transparent;
    border: none;
}}

QFrame#sidebarFooter {{
    background: transparent;
    border: none;
}}

QWidget#menuGroupTitle {{
    background: transparent;
    border: none;
    min-height: 38px;
}}

QLabel#menuGroupIcon {{
    font-size: 16px;
}}

QLabel#menuGroupText {{
    font-size: 13px;
    font-weight: 600;
    color: {theme['sidebar_text']};
}}

QLabel#menuGroupArrow {{
    font-size: 10px;
    color: {theme['sidebar_text']};
}}

QWidget#menuGroupTitle:hover {{
    background: {theme['hover_glow']};
}}

QPushButton#subMenuItem {{
    background: transparent;
    color: {theme['sidebar_text']};
    border: none;
    border-left: 3px solid transparent;
    text-align: left;
    font-size: 13px;
    font-weight: 400;
    border-radius: 6px;
    margin: 0 8px;
}}

QPushButton#subMenuItem:hover {{
    background: {theme['hover_glow']};
    color: {theme['sidebar_text_hover']};
}}

QPushButton#subMenuItem:checked {{
    background: {theme['hover_glow']};
    color: {theme['sidebar_text_checked']};
    border-left: 3px solid {theme['accent_color']};
    font-weight: 600;
}}

QPushButton#subMenuItemCollapsed {{
    background: transparent;
    color: {theme['sidebar_text']};
    border: none;
    border-radius: 10px;
    padding: 0;
    margin: 2px 4px;
    font-size: 22px;
    min-height: 40px;
    max-height: 40px;
}}

QPushButton#subMenuItemCollapsed:hover {{
    background: {theme['hover_glow']};
    color: {theme['sidebar_text_hover']};
}}

QPushButton#subMenuItemCollapsed:checked {{
    background: {theme['glow_primary']};
    color: white;
}}

QWidget#submenuContainer {{
    background: transparent;
    border: none;
}}

QPushButton#antCollapseBtn {{
    background: transparent;
    color: {theme['collapse_btn_text']};
    border: 1px solid {theme['collapse_btn_border']};
    border-radius: 8px;
    font-size: 12px;
}}

QPushButton#antCollapseBtn:hover {{
    background: {theme['collapse_btn_hover_bg']};
    color: {theme['collapse_btn_hover_text']};
    border-color: {theme['accent_color']};
}}

QPushButton#antThemeBtn {{
    background: transparent;
    color: {theme['collapse_btn_text']};
    border: 1px solid {theme['collapse_btn_border']};
    border-radius: 8px;
    font-size: 16px;
}}

QPushButton#antThemeBtn:hover {{
    background: {theme['collapse_btn_hover_bg']};
    color: {theme['collapse_btn_hover_text']};
    border-color: {theme['accent_color']};
}}

/* ========== macOS Finder Legacy ========== */
QFrame#finderSidebar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {theme['sidebar_bg_start']}, stop:1 {theme['sidebar_bg_end']});
    border-right: 1px solid {theme['sidebar_separator']};
}}

QFrame#finderHeader {{
    background: transparent;
    border: none;
}}

QLabel#finderTitle {{
    font-size: 18px;
    font-weight: 700;
    color: {theme['sidebar_title']};
}}

QLabel#finderSubtitle {{
    font-size: 11px;
    color: {theme['sidebar_subtitle']};
}}

QLabel#finderCollapsedTitle {{
    font-size: 28px;
    color: {theme['sidebar_title']};
}}

QFrame#finderSeparator {{
    background-color: {theme['sidebar_separator']};
    max-height: 1px;
    margin: 4px 12px;
}}

QFrame#finderCollapsedSeparator {{
    background-color: {theme['sidebar_separator']};
    max-height: 1px;
    margin: 6px 12px;
}}

QLabel#finderSection {{
    font-size: 11px;
    font-weight: 600;
    color: {theme['sidebar_text']};
    padding-left: 12px;
    opacity: 0.6;
}}

QPushButton#finderExpander {{
    background: transparent;
    color: {theme['sidebar_text']};
    border: none;
    border-radius: 8px;
    text-align: left;
    font-size: 14px;
    font-weight: 600;
    min-height: 36px;
    padding: 8px 12px;
}}

QPushButton#finderExpander:hover {{
    background: {theme['hover_glow']};
    color: {theme['sidebar_text_hover']};
}}

QPushButton#finderItem {{
    background: transparent;
    color: {theme['sidebar_text']};
    border: none;
    border-radius: 8px;
    text-align: left;
    font-size: 14px;
    font-weight: 400;
    padding: 10px 14px;
    margin: 1px 6px;
    min-height: 36px;
}}

QPushButton#finderItem:hover {{
    background: {theme['hover_glow']};
    color: {theme['sidebar_text_hover']};
}}

QPushButton#finderItem:checked {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme['sidebar_btn_checked_start']}, stop:1 {theme['sidebar_btn_checked_end']});
    color: {theme['sidebar_text_checked']};
    font-weight: 600;
    border-left: 3px solid {theme['accent_color']};
    padding-left: 11px;
    margin-left: 6px;
}}

QPushButton#finderIconBtn {{
    background: transparent;
    color: {theme['sidebar_text']};
    border: none;
    border-radius: 8px;
    padding: 2px;
    margin: 1px;
    font-size: 20px;
    min-width: 48px;
    max-width: 48px;
    min-height: 48px;
    max-height: 48px;
}}

QPushButton#finderIconBtn:hover {{
    background: {theme['hover_glow']};
    color: {theme['sidebar_text_hover']};
}}

QPushButton#finderIconBtn:checked {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme['sidebar_btn_checked_start']}, stop:1 {theme['sidebar_btn_checked_end']});
    color: {theme['sidebar_text_checked']};
}}

QFrame#finderBottom {{
    background: transparent;
    border: none;
}}

QPushButton#finderCollapseBtn {{
    background: transparent;
    color: {theme['collapse_btn_text']};
    border: 1px solid {theme['collapse_btn_border']};
    border-radius: 6px;
    font-size: 12px;
    padding: 6px 8px;
}}

QPushButton#finderCollapseBtn:hover {{
    background: {theme['collapse_btn_hover_bg']};
    color: {theme['collapse_btn_hover_text']};
    border-color: {theme['accent_color']};
}}

QPushButton#finderThemeBtn {{
    background: transparent;
    color: {theme['sidebar_text']};
    border: none;
    border-radius: 8px;
    padding: 4px 8px;
    margin: 0;
    font-size: 13px;
    min-width: 44px;
    max-width: 180px;
}}

QPushButton#finderThemeBtn:hover {{
    background: {theme['hover_glow']};
    color: {theme['sidebar_text_hover']};
}}

QPushButton#finderThemeBtn:checked {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme['sidebar_btn_checked_start']}, stop:1 {theme['sidebar_btn_checked_end']});
    color: {theme['sidebar_text_checked']};
}}

QWidget#finderMenuScroll {{
    background: transparent;
    border: none;
}}
"""
