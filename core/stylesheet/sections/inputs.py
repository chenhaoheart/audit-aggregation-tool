# -*- coding: utf-8 -*-
"""Generate QSS for inputs with frosted crystal glass effect."""
from typing import Dict


def generate_inputs_stylesheet(theme: Dict[str, str]) -> str:
    return f"""
/* ========== 输入框 - 毛玻璃效果 ========== */
QLineEdit {{
    border: 1px solid {theme['input_border']};
    border-radius: 10px;
    padding: 11px 16px;
    font-size: 13px;
    background: {theme['input_bg']};
    color: {theme['input_text']};
    selection-background-color: {theme['accent_color']};
    selection-color: white;
}}

QLineEdit:hover {{
    border-color: {theme['input_focus_border']};
}}

QLineEdit:focus {{
    border: 1.5px solid {theme['input_focus_border']};
    background: {theme['input_bg']};
}}

QLineEdit:disabled {{
    background: {theme['card_bg']};
    color: {theme['text_secondary']};
    border-color: {theme['input_border']};
}}

QLineEdit#filterEdit {{
    border-radius: 8px;
    padding: 9px 14px;
    font-size: 12px;
}}

/* ========== 文本编辑 ========== */
QTextEdit {{
    border: 1px solid {theme['input_border']};
    border-radius: 10px;
    background: {theme['log_bg']};
    color: {theme['log_text']};
    font-family: 'Cascadia Code', 'JetBrains Mono', 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    padding: 12px;
    selection-background-color: {theme['accent_color']};
    selection-color: white;
}}

QTextEdit#logText {{
    color: {theme['log_green']};
}}

/* ========== 下拉框 - 毛玻璃效果 ========== */
QComboBox {{
    border: 1px solid {theme['combo_border']};
    border-radius: 8px;
    padding: 9px 14px;
    background: {theme['combo_bg']};
    color: {theme['combo_text']};
    min-height: 18px;
}}

QComboBox:hover {{
    border-color: {theme['combo_hover_border']};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 10px;
    width: 24px;
}}

QComboBox::down-arrow {{
    image: none;
    border: none;
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {theme['text_secondary']};
    margin-right: 4px;
}}

QComboBox QAbstractItemView {{
    background-color: {theme['card_bg']};
    color: {theme['text_primary']};
    border: 1px solid {theme['card_border']};
    border-radius: 8px;
    selection-background-color: {theme['table_selection_bg']};
    selection-color: {theme['text_primary']};
    padding: 4px;
    outline: none;
}}
"""
