# -*- coding: utf-8 -*-
"""Generate QSS for buttons with outline or filled style based on theme."""
from typing import Dict


def generate_buttons_stylesheet(theme: Dict[str, str]) -> str:
    btn_style = theme.get('btn_style', 'filled')
    
    if btn_style == 'outline':
        return _generate_outline_buttons(theme)
    else:
        return _generate_filled_buttons(theme)


def _generate_outline_buttons(theme: Dict[str, str]) -> str:
    return f"""
/* ========== 按钮 - 边框风格 ========== */
QPushButton {{
    background: transparent;
    color: {theme.get('btn_primary_text', theme.get('accent_color', '#6366f1'))};
    border: 1.5px solid {theme.get('btn_primary_border', theme.get('accent_color', '#6366f1'))};
    border-radius: 10px;
    padding: 4px 8px;
    font-size: 14px;
    font-weight: 600;
}}

QPushButton:hover {{
    background: {theme.get('btn_primary_hover_bg', theme.get('accent_color', '#6366f1'))};
    color: {theme.get('btn_primary_hover_text', '#ffffff')};
    border-color: transparent;
}}

QPushButton:pressed {{
    background: {theme.get('btn_primary_pressed_bg', '#4f46e5')};
    color: {theme.get('btn_primary_hover_text', '#ffffff')};
    border-color: transparent;
}}

QPushButton:disabled {{
    background: {theme.get('btn_disabled_bg', 'transparent')};
    color: {theme.get('btn_disabled_text', '#94a3b8')};
    border: 1.5px solid {theme.get('btn_disabled_border', '#cbd5e1')};
}}

/* ========== 导出按钮 - 绿色边框 ========== */
QPushButton#exportBtn {{
    background: transparent;
    color: {theme.get('btn_success_text', '#22c55e')};
    border: 1.5px solid {theme.get('btn_success_border', '#22c55e')};
    border-radius: 10px;
    padding: 4px 8px;
}}

QPushButton#exportBtn:hover {{
    background: {theme.get('btn_success_hover_bg', '#22c55e')};
    color: {theme.get('btn_success_hover_text', '#ffffff')};
    border-color: transparent;
}}

QPushButton#exportBtn:disabled {{
    background: transparent;
    color: {theme.get('btn_disabled_text', '#94a3b8')};
    border: 1.5px solid {theme.get('btn_disabled_border', '#cbd5e1')};
}}

/* ========== 校验按钮 - 青色边框 ========== */
QPushButton#validateBtn {{
    background: transparent;
    color: {theme.get('btn_info_text', '#0ea5e9')};
    border: 1.5px solid {theme.get('btn_info_border', '#0ea5e9')};
    border-radius: 10px;
    padding: 4px 8px;
    font-weight: 600;
}}

QPushButton#validateBtn:hover {{
    background: {theme.get('btn_info_hover_bg', '#0ea5e9')};
    color: {theme.get('btn_info_hover_text', '#ffffff')};
    border-color: transparent;
}}

QPushButton#validateBtn:disabled {{
    background: transparent;
    color: {theme.get('btn_disabled_text', '#94a3b8')};
    border: 1.5px solid {theme.get('btn_disabled_border', '#cbd5e1')};
}}

/* ========== 清空按钮 - 红色边框 ========== */
QPushButton#clearBtn {{
    background: transparent;
    color: {theme.get('btn_danger_text', '#ef4444')};
    border: 1.5px solid {theme.get('btn_danger_border', '#ef4444')};
    border-radius: 10px;
    padding: 4px 8px;
    font-weight: 600;
}}

QPushButton#clearBtn:hover {{
    background: {theme.get('btn_danger_hover_bg', '#ef4444')};
    color: {theme.get('btn_danger_hover_text', '#ffffff')};
    border-color: transparent;
}}

/* ========== 日志切换按钮 - 次要边框 ========== */
QPushButton#logToggleBtn {{
    background: transparent;
    color: {theme.get('btn_secondary_text', '#64748b')};
    border: 1px solid {theme.get('btn_secondary_border', '#94a3b8')};
    font-size: 13px;
    padding: 4px 8px;
    border-radius: 8px;
}}

QPushButton#logToggleBtn:hover {{
    background: {theme.get('btn_secondary_hover_bg', '#f1f5f9')};
    color: {theme.get('text_primary', '#2c3e50')};
    border-color: {theme.get('btn_secondary_hover_border', '#64748b')};
}}

/* ========== 确定按钮 ========== */
QPushButton#confirmBtn {{
    background: transparent;
    color: {theme.get('confirm_btn_text', theme.get('btn_primary_text', '#6366f1'))};
    border: 1.5px solid {theme.get('confirm_btn_border', theme.get('btn_primary_border', '#6366f1'))};
    border-radius: 10px;
    padding: 4px 8px;
    font-weight: 600;
}}

QPushButton#confirmBtn:hover {{
    background: {theme.get('confirm_btn_hover_bg', theme.get('btn_primary_hover_bg', '#6366f1'))};
    color: {theme.get('btn_primary_hover_text', '#ffffff')};
    border-color: transparent;
}}

/* ========== 取消按钮 ========== */
QPushButton#cancelBtn {{
    background: transparent;
    color: {theme.get('cancel_btn_text', theme.get('btn_secondary_text', '#64748b'))};
    border: 1px solid {theme.get('cancel_btn_border', theme.get('btn_secondary_border', '#94a3b8'))};
    border-radius: 10px;
    padding: 4px 8px;
}}

QPushButton#cancelBtn:hover {{
    background: {theme.get('cancel_btn_hover_bg', theme.get('btn_secondary_hover_bg', '#f1f5f9'))};
    border-color: {theme.get('btn_secondary_hover_border', '#64748b')};
}}

/* ========== 刷新按钮 ========== */
QPushButton#refreshBtn {{
    background: transparent;
    color: {theme.get('btn_info_text', '#0ea5e9')};
    border: 1.5px solid {theme.get('btn_info_border', '#0ea5e9')};
    border-radius: 10px;
    padding: 4px 8px;
}}

QPushButton#refreshBtn:hover {{
    background: {theme.get('btn_info_hover_bg', '#0ea5e9')};
    color: {theme.get('btn_info_hover_text', '#ffffff')};
    border-color: transparent;
}}

/* ========== 选择目录按钮 ========== */
QPushButton#selectDirBtn {{
    background: transparent;
    color: {theme.get('btn_primary_text', '#6366f1')};
    border: 1.5px solid {theme.get('btn_primary_border', '#6366f1')};
    border-radius: 10px;
    padding: 4px 8px;
}}

QPushButton#selectDirBtn:hover {{
    background: {theme.get('btn_primary_hover_bg', '#6366f1')};
    color: {theme.get('btn_primary_hover_text', '#ffffff')};
    border-color: transparent;
}}
"""


def _generate_filled_buttons(theme: Dict[str, str]) -> str:
    return f"""
/* ========== 按钮 - 填充风格 ========== */
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme.get('btn_primary_start', '#667eea')}, stop:1 {theme.get('btn_primary_end', '#764ba2')});
    color: white;
    border: none;
    border-radius: 10px;
    padding: 4px 8px;
    font-size: 14px;
    font-weight: 600;
}}

QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme.get('btn_primary_hover_start', '#5a6fd6')}, stop:1 {theme.get('btn_primary_hover_end', '#6a4190')});
}}

QPushButton:pressed {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme.get('btn_primary_pressed_start', '#4a5fc6')}, stop:1 {theme.get('btn_primary_pressed_end', '#5a3180')});
}}

QPushButton:disabled {{
    background: {theme.get('btn_disabled_bg', '#bdc3c7')};
    color: {theme.get('btn_disabled_text', '#7f8c8d')};
}}

/* ========== 导出按钮 - 翡翠绿 ========== */
QPushButton#exportBtn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme.get('btn_success_start', '#2ecc71')}, stop:1 {theme.get('btn_success_end', '#27ae60')});
    border-radius: 10px;
    padding: 4px 8px;
}}

QPushButton#exportBtn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme.get('btn_success_hover_start', '#27ae60')}, stop:1 {theme.get('btn_success_hover_end', '#1e8449')});
}}

QPushButton#exportBtn:disabled {{
    background: {theme.get('btn_success_disabled_start', '#a9dfbf')};
    color: {theme.get('btn_disabled_text', '#7f8c8d')};
}}

/* ========== 校验按钮 - 青色描边 ========== */
QPushButton#validateBtn {{
    background: transparent;
    color: {theme.get('info_text', '#3498db')};
    border: 1.5px solid {theme.get('btn_info_start', '#3498db')};
    border-radius: 10px;
    padding: 4px 8px;
    font-weight: 600;
}}

QPushButton#validateBtn:hover {{
    background: {theme.get('btn_info_hover_start', '#2980b9')};
    color: white;
    border-color: transparent;
}}

QPushButton#validateBtn:disabled {{
    background: transparent;
    color: {theme.get('btn_info_disabled_start', '#aed6f1')};
    border-color: {theme.get('btn_info_disabled_end', '#85c1e9')};
}}

/* ========== 清空按钮 - 玫红描边 ========== */
QPushButton#clearBtn {{
    background: transparent;
    color: {theme.get('btn_danger_start', '#e74c3c')};
    border: 1.5px solid {theme.get('btn_danger_start', '#e74c3c')};
    border-radius: 10px;
    padding: 4px 8px;
    font-weight: 600;
}}

QPushButton#clearBtn:hover {{
    background: {theme.get('btn_danger_hover_start', '#c0392b')};
    color: white;
    border-color: transparent;
}}

/* ========== 日志切换按钮 - 次要描边 ========== */
QPushButton#logToggleBtn {{
    background: transparent;
    color: {theme.get('text_secondary', '#6b7d9e')};
    border: 1px solid {theme.get('card_border', '#e0e4e8')};
    font-size: 13px;
    padding: 4px 8px;
    border-radius: 8px;
}}

QPushButton#logToggleBtn:hover {{
    background: {theme.get('hover_glow', 'rgba(102,126,234,0.15)')};
    color: {theme.get('text_primary', '#2c3e50')};
    border-color: {theme.get('accent_color', '#667eea')};
}}

/* ========== 确定按钮 ========== */
QPushButton#confirmBtn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme.get('btn_primary_start', '#667eea')}, stop:1 {theme.get('btn_primary_end', '#764ba2')});
    color: white;
    border: none;
    border-radius: 10px;
    padding: 4px 8px;
}}

QPushButton#confirmBtn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme.get('btn_primary_hover_start', '#5a6fd6')}, stop:1 {theme.get('btn_primary_hover_end', '#6a4190')});
}}

/* ========== 取消按钮 ========== */
QPushButton#cancelBtn {{
    background: transparent;
    color: {theme.get('text_secondary', '#6b7d9e')};
    border: 1px solid {theme.get('card_border', '#e0e4e8')};
    border-radius: 10px;
    padding: 4px 8px;
}}

QPushButton#cancelBtn:hover {{
    background: {theme.get('hover_glow', 'rgba(102,126,234,0.15)')};
    border-color: {theme.get('accent_color', '#667eea')};
}}
"""