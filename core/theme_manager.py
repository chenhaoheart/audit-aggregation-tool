# -*- coding: utf-8 -*-
"""
主题管理模块 - 浅色系/暗色系两大主题组
浅色系: 晨曦、渐变、毛玻璃、森林
暗色系: 极光、系统暗黑
"""

import os
import json
import re
from typing import Dict, Optional, List
from PySide6.QtCore import QObject, Signal, Slot, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QGuiApplication, QColor
from PySide6.QtWidgets import QWidget


def parse_theme_color(color_str: str, fallback: str = '#e5e7eb') -> QColor:
    if not color_str:
        return QColor(fallback)
    c = QColor(color_str)
    if c.isValid():
        return c
    if 'rgba(' in color_str or 'rgb(' in color_str:
        try:
            inner = color_str.replace('rgba(', '').replace('rgb(', '').replace(')', '').strip()
            parts = [float(x.strip()) for x in inner.split(',')]
            r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
            a = int(float(parts[3]) * 255) if len(parts) > 3 else 255
            c = QColor(r, g, b, a)
            if c.isValid():
                return c
        except Exception:
            pass
    return QColor(fallback)


THEME_CONFIG_FILE = "theme.json"


class ThemeMode:
    AUTO = "auto"
    LIGHT = "light"
    DARK = "dark"
    QWEN = "qwen"
    GLASS = "glass"
    AURORA = "aurora"
    FLAME = "flame"
    FOREST = "forest"


class ThemeGroup:
    LIGHT = "light_group"
    DARK = "dark_group"


THEME_GROUP_MAP = {
    ThemeGroup.LIGHT: {
        "name": "浅色系",
        "icon": "\u2600\ufe0f",
        "subtitle": "明亮温暖",
        "modes": [ThemeMode.LIGHT, ThemeMode.FLAME, ThemeMode.QWEN, ThemeMode.GLASS, ThemeMode.FOREST],
    },
    ThemeGroup.DARK: {
        "name": "暗色系",
        "icon": "\U0001f319",
        "subtitle": "深邃沉浸",
        "modes": [ThemeMode.AURORA, ThemeMode.DARK],
    },
}

THEME_DISPLAY_NAMES = {
    ThemeMode.LIGHT: "\U0001f31e 纯净",
    ThemeMode.FLAME: "\U0001f305 晨曦",
    ThemeMode.QWEN: "\u2728 渐变",
    ThemeMode.GLASS: "\U0001fa9f 毛玻璃",
    ThemeMode.FOREST: "\U0001f333 森林",
    ThemeMode.AURORA: "\U0001f30c 极光",
    ThemeMode.DARK: "\U0001f31c 暗黑",
}

# Theme definitions loaded from JSON files
_THEME_DEFINITIONS: Dict[str, Dict[str, str]] = {}

_THEMES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "themes")


def _load_theme_definitions() -> Dict[str, Dict[str, str]]:
    """Load theme definitions from config/themes/*.json files."""
    definitions = {}
    if not os.path.exists(_THEMES_DIR):
        return definitions
    for filename in os.listdir(_THEMES_DIR):
        if filename.endswith(".json"):
            try:
                filepath = os.path.join(_THEMES_DIR, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    theme_name = data.get("name", "").lower()
                    colors = data.get("colors", {})
                    mode_map = {"light": ThemeMode.LIGHT, "dark": ThemeMode.DARK,
                                "qwen": ThemeMode.QWEN, "glass": ThemeMode.GLASS,
                                "aurora": ThemeMode.AURORA, "flame": ThemeMode.FLAME,
                                "forest": ThemeMode.FOREST}
                    mode_key = mode_map.get(theme_name, theme_name)
                    definitions[mode_key] = colors
            except Exception as e:
                print(f"加载主题文件 {filename} 失败: {e}")
    return definitions


def get_theme_dict(mode: str = None):
    """Get a theme dict by mode, or all themes if mode is None."""
    global _THEME_DEFINITIONS
    if not _THEME_DEFINITIONS:
        _THEME_DEFINITIONS = _load_theme_definitions()
    if mode is None:
        return _THEME_DEFINITIONS
    return _THEME_DEFINITIONS.get(mode, {})


def get_theme_group(mode: str) -> Optional[str]:
    """Get which group a theme mode belongs to."""
    for group, config in THEME_GROUP_MAP.items():
        if mode in config["modes"]:
            return group
    return None


def get_group_display_themes(group: str) -> List[str]:
    """Get list of theme modes in a group for display."""
    config = THEME_GROUP_MAP.get(group, THEME_GROUP_MAP[ThemeGroup.LIGHT])
    return config["modes"][:]


class ThemeManager(QObject):
    """主题管理器"""

    theme_changed = Signal(str)
    glass_opacity_changed = Signal(float)
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_dir: str = None):
        if hasattr(self, '_initialized') and self._initialized:
            return

        super().__init__()

        if config_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_dir = os.path.dirname(current_dir)
            config_dir = os.path.join(project_dir, "config")

        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, THEME_CONFIG_FILE)
        self._mode = ThemeMode.FLAME
        self._glass_opacity = 0.60
        self._current_theme = get_theme_dict(ThemeMode.FLAME) or get_theme_dict(ThemeMode.LIGHT) or {}
        self._ensure_config_dir()
        self._load_config()
        self._initialized = True

    def _ensure_config_dir(self):
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, exist_ok=True)

    def _load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    loaded_mode = data.get('mode', ThemeMode.FLAME)
                    if loaded_mode == ThemeMode.AUTO or loaded_mode not in get_theme_dict():
                        loaded_mode = ThemeMode.FLAME
                    self._mode = loaded_mode
                    self._glass_opacity = data.get('glass_opacity', 0.60)
            except Exception:
                self._mode = ThemeMode.FLAME
                self._glass_opacity = 0.60

    def _save_config(self):
        try:
            data = {'mode': self._mode, 'glass_opacity': self._glass_opacity}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存主题配置失败: {e}")

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def current_group(self) -> str:
        return get_theme_group(self._mode) or ThemeGroup.LIGHT

    def get_system_theme(self) -> str:
        try:
            style_hints = QGuiApplication.styleHints()
            if style_hints:
                color_scheme = style_hints.colorScheme()
                if color_scheme.name == "Dark":
                    return ThemeMode.DARK
        except Exception:
            pass
        return ThemeMode.FLAME

    def get_current_theme(self) -> Dict[str, str]:
        theme = get_theme_dict(self._mode) or get_theme_dict(ThemeMode.FLAME) or {}
        if self._mode == ThemeMode.GLASS:
            theme = self._apply_glass_opacity(theme)
        return theme

    def get_available_themes(self) -> list:
        """Return list of available theme modes (for UI display)."""
        return list(get_theme_dict().keys()) or [ThemeMode.FLAME, ThemeMode.DARK]

    def get_display_themes(self) -> List[str]:
        """Return themes organized by group for UI display."""
        result = []
        for group in [ThemeGroup.LIGHT, ThemeGroup.DARK]:
            group_config = THEME_GROUP_MAP[group]
            result.append({
                "group": group,
                "name": group_config["name"],
                "icon": group_config["icon"],
                "subtitle": group_config["subtitle"],
                "themes": group_config["modes"],
            })
        return result

    def set_mode(self, mode: str):
        available = self.get_available_themes()
        if mode in available:
            self._mode = mode
            self._current_theme = self.get_current_theme()
            self._save_config()
            self.theme_changed.emit(mode)

    def set_mode_with_animation(self, mode: str, widget: QWidget) -> None:
        """带动画的主题切换 - 平滑过渡"""
        available = self.get_available_themes()
        if mode not in available:
            return

        self._fade_out_animation = QPropertyAnimation(widget, b"windowOpacity")
        self._fade_out_animation.setDuration(150)
        self._fade_out_animation.setStartValue(1.0)
        self._fade_out_animation.setEndValue(0.92)
        self._fade_out_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._fade_in_animation = QPropertyAnimation(widget, b"windowOpacity")
        self._fade_in_animation.setDuration(200)
        self._fade_in_animation.setStartValue(0.92)
        self._fade_in_animation.setEndValue(1.0)
        self._fade_in_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        def on_fade_out_finished():
            self.set_mode(mode)
            widget.setStyleSheet(self.get_stylesheet())
            self._fade_in_animation.start()

        def on_fade_in_finished():
            self._fade_out_animation.deleteLater()
            self._fade_in_animation.deleteLater()
            self._fade_out_animation = None
            self._fade_in_animation = None

        self._fade_out_animation.finished.connect(on_fade_out_finished)
        self._fade_in_animation.finished.connect(on_fade_in_finished)

        self._fade_out_animation.start()

    def get_stylesheet(self) -> str:
        theme = self.get_current_theme()
        return self._generate_stylesheet(theme)

    def _generate_stylesheet(self, theme: Dict[str, str]) -> str:
        """Generate stylesheet by delegating to the modular stylesheet generator."""
        from core.stylesheet import generate_stylesheet as gen
        return gen(theme)

    def get_inline_style(self, style_type: str) -> str:
        theme = self.get_current_theme()
        styles = {
            'env_success': f"color: {theme['success_text']}; font-weight: bold;",
            'env_error': f"color: {theme['error_text']};",
            'env_warning': f"color: {theme['warning_text']};",
            'env_info': f"color: {theme['info_text']}; font-weight: bold;",
            'success_bg': f"background-color: {theme['success_bg']};",
            'error_bg': f"background-color: {theme['error_bg']};",
            'badge_pass': f"background-color: {theme['badge_pass_bg']}; color: {theme['badge_pass_text']}; border: 1px solid {theme['badge_pass_border']}; border-radius: 12px; padding: 3px 14px; font-size: 12px; font-weight: 600; min-width: 50px;",
            'badge_fail': f"background-color: {theme['badge_fail_bg']}; color: {theme['badge_fail_text']}; border: 1px solid {theme['badge_fail_border']}; border-radius: 12px; padding: 3px 14px; font-size: 12px; font-weight: 600; min-width: 50px;",
        }
        return styles.get(style_type, '')

    def get_color(self, color_name: str) -> str:
        theme = self.get_current_theme()
        return theme.get(color_name, '')

    @property
    def glass_opacity(self) -> float:
        return self._glass_opacity

    def set_glass_opacity(self, opacity: float):
        """设置玻璃主题透明度 (0.1 ~ 1.0)"""
        self._glass_opacity = max(0.1, min(1.0, opacity))
        if self._mode == ThemeMode.GLASS:
            self._current_theme = self._apply_glass_opacity(get_theme_dict(ThemeMode.GLASS))
            self._save_config()
            self.glass_opacity_changed.emit(self._glass_opacity)
            self.theme_changed.emit(ThemeMode.GLASS)

    def _apply_glass_opacity(self, theme: Dict[str, str]) -> Dict[str, str]:
        """根据 glass_opacity 调整玻璃主题中所有 rgba 值的透明度"""
        opacity = self._glass_opacity
        result = {}
        for key, value in theme.items():
            if isinstance(value, str) and 'rgba(' in value:
                result[key] = self._adjust_rgba_opacity(value, opacity)
            else:
                result[key] = value
        return result

    @staticmethod
    def _adjust_rgba_opacity(rgba_str: str, target_opacity: float) -> str:
        """调整 rgba 字符串的透明度

        将原始透明度乘以 target_opacity 系数。
        例如：rgba(255,255,255,0.60) + target_opacity=0.8 => rgba(255,255,255,0.48)
        """
        match = re.match(r'rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([0-9.]+)\s*\)', rgba_str)
        if match:
            r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
            original_alpha = float(match.group(4))
            new_alpha = round(original_alpha * target_opacity, 2)
            new_alpha = max(0.0, min(1.0, new_alpha))
            return f"rgba({r},{g},{b},{new_alpha})"
        return rgba_str


_theme_manager = None


def get_theme_manager() -> ThemeManager:
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager