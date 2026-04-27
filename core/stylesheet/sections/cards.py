# -*- coding: utf-8 -*-
"""Generate QSS for cards with frosted crystal glass effect."""
from typing import Dict


def generate_cards_stylesheet(theme: Dict[str, str]) -> str:
    return f"""
/* ========== 分组框 - 毛玻璃卡片 ========== */
QGroupBox {{
    font-size: 13px;
    font-weight: 600;
    color: {theme['text_secondary']};
    border: 1px solid {theme['card_border']};
    border-radius: 16px;
    margin-top: 18px;
    padding: 24px 20px;
    background: {theme['card_bg']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 14px;
    color: {theme['text_primary']};
    background: transparent;
    font-weight: 600;
    font-size: 14px;
}}

/* ========== 卡片 - 毛玻璃效果 ========== */
QFrame#card {{
    background: {theme['card_bg']};
    border: 1px solid {theme['card_border']};
    border-radius: 16px;
    padding: 0;
}}

/* 卡片内部面板 / Splitter —— 透明背景继承父级 */
QWidget#cardInnerPanel,
QSplitter#cardInnerPanel {{
    background: transparent;
    border: none;
}}

QSplitter#mainSplitter {{
    background: transparent;
    border: none;
    spacing: 0;
}}

QSplitter#mainSplitter::handle {{
    background: transparent;
    width: 0;
}}

/* 结果Tab —— 毛玻璃卡片 */
QTabWidget#resultTabs {{
    background: {theme['card_bg']};
    border: 1px solid {theme['card_border']};
    border-radius: 16px;
}}

QTabWidget#resultTabs::pane {{
    border: none;
    background: transparent;
    margin: 0;
    padding: 0;
}}

QTabWidget#resultTabs QTabBar::tab {{
    background: transparent;
    color: {theme['text_secondary']};
    border: none;
    padding: 12px 28px;
    margin-right: 4px;
    font-size: 14px;
    font-weight: 500;
}}

QTabWidget#resultTabs QTabBar::tab:selected {{
    color: {theme['accent_color']};
    border-bottom: 2px solid {theme['tab_underline_color']};
    font-weight: 600;
}}

QTabWidget#resultTabs QTabBar::tab:hover:!selected {{
    color: {theme['text_primary']};
    border-bottom: 2px solid {theme['tab_hover_bg']};
}}

/* ========== 统计卡片 - 琥珀色顶部条 ========== */
QFrame#statCard {{
    background: {theme['stat_card_bg']};
    border: 1px solid {theme['stat_card_border']};
    border-radius: 12px;
    padding: 14px 16px;
    min-width: 110px;
}}

QLabel#statNumber {{
    font-size: 22px;
    font-weight: 700;
    color: {theme['stat_number_color']};
    font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif;
}}

QLabel#statLabel {{
    font-size: 11px;
    font-weight: 500;
    color: {theme['stat_label_color']};
    letter-spacing: 0.3px;
}}

QLabel#emptyState {{
    color: {theme['empty_state_color']};
    font-size: 14px;
}}
"""
