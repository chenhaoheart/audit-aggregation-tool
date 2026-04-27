# -*- coding: utf-8 -*-
"""
主题预览卡片组件 - 浅色系/暗色系主题预览
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt, Signal, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient

from core.theme_manager import ThemeMode, get_theme_manager, get_theme_dict, THEME_DISPLAY_NAMES


THEME_COLORS = {
    ThemeMode.LIGHT: {"accent": "#6366f1", "gradient_start": "#f8f9fa", "gradient_end": "#e9ecef", "bg": "#f0f2f5"},
    ThemeMode.FLAME: {"accent": "#FF7F50", "gradient_start": "#FFB899", "gradient_end": "#FF99AA", "bg": "#FFF8F3"},
    ThemeMode.QWEN: {"accent": "#6366f1", "gradient_start": "#7c83f5", "gradient_end": "#e8e0ff", "bg": "#f0ecff"},
    ThemeMode.GLASS: {"accent": "#e8a838", "gradient_start": "#ffffff", "gradient_end": "#f8f9fa", "bg": "#f8fafc"},
    ThemeMode.FOREST: {"accent": "#43a047", "gradient_start": "#e8f5e9", "gradient_end": "#c8e6c9", "bg": "#f1f8e9"},
    ThemeMode.AURORA: {"accent": "#00d4aa", "gradient_start": "#0a0e27", "gradient_end": "#141b3d", "bg": "#0d1117"},
    ThemeMode.DARK: {"accent": "#818cf8", "gradient_start": "#1a1a2e", "gradient_end": "#16213e", "bg": "#0f1419"},
}


class MiniSidebarPreview(QWidget):
    """迷你侧边栏预览组件"""

    def __init__(self, theme_dict: dict, parent=None):
        super().__init__(parent)
        self.theme = theme_dict
        self.setFixedSize(44, 64)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        sidebar_gradient = QLinearGradient(0, 0, 0, self.height())
        start_color = QColor(self.theme.get('sidebar_bg_start', '#ffffff'))
        end_color = QColor(self.theme.get('sidebar_bg_end', '#f8f9fa'))

        if 'rgba' in self.theme.get('sidebar_bg_start', ''):
            start_color = self._parse_rgba(self.theme['sidebar_bg_start'])
        if 'rgba' in self.theme.get('sidebar_bg_end', ''):
            end_color = self._parse_rgba(self.theme['sidebar_bg_end'])

        sidebar_gradient.setColorAt(0, start_color)
        sidebar_gradient.setColorAt(1, end_color)

        painter.setBrush(QBrush(sidebar_gradient))
        painter.setPen(QPen(Qt.NoPen))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 6, 6)

        accent = QColor(self.theme.get('accent_color', '#6366f1'))
        btn_checked_gradient = QLinearGradient(0, 0, self.width() - 8, 0)
        btn_start = QColor(self.theme.get('sidebar_btn_checked_start', '#6366f1'))
        btn_end = QColor(self.theme.get('sidebar_btn_checked_end', '#8b5cf6'))
        if isinstance(btn_start, QColor) and 'rgba' not in self.theme.get('sidebar_btn_checked_start', ''):
            btn_checked_gradient.setColorAt(0, btn_start)
            btn_checked_gradient.setColorAt(1, btn_end)
        else:
            btn_checked_gradient = QLinearGradient(0, 0, self.width() - 8, 0)
            btn_checked_gradient.setColorAt(0, accent)
            btn_checked_gradient.setColorAt(1, QColor(accent).lighter(130))

        painter.setBrush(QBrush(btn_checked_gradient))
        painter.drawRoundedRect(6, 10, self.width() - 12, 10, 3, 3)

        text_color = QColor(self.theme.get('sidebar_text', '#64748b'))
        painter.setBrush(QBrush(QColor(text_color.red(), text_color.green(), text_color.blue(), 50)))
        painter.drawRoundedRect(6, 24, self.width() - 12, 10, 3, 3)
        painter.drawRoundedRect(6, 38, self.width() - 12, 10, 3, 3)

        painter.end()

    def _parse_rgba(self, rgba_str: str) -> QColor:
        try:
            rgba_str = rgba_str.replace('rgba(', '').replace(')', '')
            parts = rgba_str.split(',')
            r = int(parts[0].strip())
            g = int(parts[1].strip())
            b = int(parts[2].strip())
            a = float(parts[3].strip()) if len(parts) > 3 else 1.0
            return QColor(r, g, b, int(a * 255))
        except Exception:
            return QColor(255, 255, 255, 200)


class MiniContentPreview(QWidget):
    """迷你内容区预览组件"""

    def __init__(self, theme_dict: dict, parent=None):
        super().__init__(parent)
        self.theme = theme_dict
        self.setFixedSize(88, 64)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        content_bg = self.theme.get('content_bg', '#f0f2f5')
        if 'transparent' in content_bg:
            bg_color = QColor(240, 244, 248)
        elif 'rgba' in content_bg:
            bg_color = self._parse_rgba(content_bg)
        else:
            bg_color = QColor(content_bg)

        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(Qt.NoPen))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 6, 6)

        card_bg = self.theme.get('card_bg', '#ffffff')
        if 'rgba' in card_bg:
            card_color = self._parse_rgba(card_bg)
        else:
            card_color = QColor(card_bg)

        card_border = self.theme.get('card_border', '#e0e4e8')
        if 'rgba' in card_border:
            border_color = self._parse_rgba(card_border)
        else:
            border_color = QColor(card_border)

        painter.setBrush(QBrush(card_color))
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(6, 6, self.width() - 12, 32, 4, 4)

        text_color = QColor(self.theme.get('text_primary', '#2c3e50'))
        painter.setPen(QPen(text_color))
        font = QFont()
        font.setPointSize(7)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(10, 16, "Title")

        accent = QColor(self.theme.get('accent_color', '#667eea'))
        painter.setBrush(QBrush(accent))
        painter.setPen(QPen(Qt.NoPen))
        painter.drawRoundedRect(10, 42, 28, 14, 3, 3)
        painter.drawEllipse(self.width() - 14, 8, 6, 6)

        painter.end()

    def _parse_rgba(self, rgba_str: str) -> QColor:
        try:
            rgba_str = rgba_str.replace('rgba(', '').replace(')', '')
            parts = rgba_str.split(',')
            r = int(parts[0].strip())
            g = int(parts[1].strip())
            b = int(parts[2].strip())
            a = float(parts[3].strip()) if len(parts) > 3 else 1.0
            return QColor(r, g, b, int(a * 255))
        except Exception:
            return QColor(255, 255, 255, 200)


class ThemePreviewCard(QFrame):
    """主题预览卡片"""

    clicked = Signal(str)

    def __init__(self, theme_mode: str, parent=None):
        super().__init__(parent)
        self.theme_mode = theme_mode
        self._selected = False
        self._hover_scale = 1.0

        self.theme_name = THEME_DISPLAY_NAMES.get(theme_mode, theme_mode)
        self.theme_dict = get_theme_dict(theme_mode)
        if not self.theme_dict:
            self.theme_dict = get_theme_dict(ThemeMode.FLAME)

        self.setObjectName("themePreviewCard")
        self.setFixedSize(165, 125)
        self.setCursor(Qt.PointingHandCursor)

        self._init_ui()
        self._setup_animation()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        preview_layout = QHBoxLayout()
        preview_layout.setSpacing(6)

        self.sidebar_preview = MiniSidebarPreview(self.theme_dict)
        self.content_preview = MiniContentPreview(self.theme_dict)

        preview_layout.addWidget(self.sidebar_preview)
        preview_layout.addWidget(self.content_preview, 1)
        layout.addLayout(preview_layout)

        name_label = QLabel(self.theme_name)
        name_label.setStyleSheet("font-size: 13px; font-weight: 600; background: transparent; border: none;")
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)

        self.setLayout(layout)

    def _setup_animation(self):
        self._scale_anim = QPropertyAnimation(self, b"hoverScale")
        self._scale_anim.setDuration(150)
        self._scale_anim.setEasingCurve(QEasingCurve.OutCubic)

    def get_hover_scale(self) -> float:
        return self._hover_scale

    def set_hover_scale(self, scale: float):
        self._hover_scale = scale

    hoverScale = Property(float, get_hover_scale, set_hover_scale)

    def enterEvent(self, event):
        self._scale_anim.setStartValue(1.0)
        self._scale_anim.setEndValue(1.05)
        self._scale_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._scale_anim.setStartValue(self._hover_scale)
        self._scale_anim.setEndValue(1.0)
        self._scale_anim.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.theme_mode)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool):
        self._selected = selected
        self._update_style()

    def is_selected(self) -> bool:
        return self._selected

    def _update_style(self):
        theme_manager = get_theme_manager()
        theme = theme_manager.get_current_theme()
        accent = theme.get('accent_color', '#6366f1')
        card_bg = self.theme_dict.get('card_bg', '#ffffff')
        card_border = self.theme_dict.get('card_border', '#e0e4e8')

        if self._selected:
            self.setStyleSheet(f"""
                QFrame#themePreviewCard {{
                    background: {card_bg};
                    border: 2px solid {accent};
                    border-radius: 14px;
                    padding: 2px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame#themePreviewCard {{
                    background: {card_bg};
                    border: 1px solid {card_border};
                    border-radius: 14px;
                }}
                QFrame#themePreviewCard:hover {{
                    border: 2px solid {accent};
                }}
            """)