# -*- coding: utf-8 -*-
"""
Dashboard统计图表组件
包含：StatNumberCard, StatMetricCard, HealthScoreGauge, HorizontalBarChart, MiniDonutWidget
"""

import math
from PySide6.QtWidgets import QWidget, QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QRectF, QTimer, QPropertyAnimation, QEasingCurve, QPointF, Property
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QBrush, QFont, QConicalGradient

from core.theme_manager import get_theme_manager, parse_theme_color


class StatNumberCard(QWidget):
    def __init__(self, label: str, icon: str = "", parent=None):
        super().__init__(parent)
        self._label = label
        self._icon = icon
        self._value = "--"
        self._sub_text = ""
        self._color_key = "text_primary"
        self._bg_color = None
        self.setMinimumSize(140, 90)
        self.setMaximumHeight(100)

    def set_value(self, value: str, sub_text: str = "", color_key: str = "text_primary"):
        self._value = value
        self._sub_text = sub_text
        self._color_key = color_key
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        theme = get_theme_manager().get_current_theme()

        card_bg = parse_theme_color(theme.get('card_bg', '#ffffff'))
        border_color = parse_theme_color(theme.get('card_border', '#e5e7eb'))

        path = QPainterPath()
        r = 14
        path.addRoundedRect(4, 4, self.width() - 8, self.height() - 8, r, r)
        painter.fillPath(path, card_bg)
        painter.setPen(QPen(border_color, 1))
        painter.drawPath(path)

        value_color = parse_theme_color(theme.get(self._color_key, '#1e293b'))
        font_value = QFont("SF Pro Display", 28, QFont.Bold)
        painter.setFont(font_value)
        painter.setPen(value_color)
        painter.drawText(18, 42, self._value)

        font_label = QFont("Microsoft YaHei UI", 11)
        painter.setFont(font_label)
        label_color = parse_theme_color(theme.get('text_secondary', '#64748b'))
        painter.setPen(label_color)
        painter.drawText(18, 66, self._label)

        if self._sub_text:
            font_sub = QFont("Microsoft YaHei UI", 9)
            painter.setFont(font_sub)
            sub_color = parse_theme_color(theme.get('text_muted', '#94a3b8'))
            painter.setPen(sub_color)
            painter.drawText(18, 82, self._sub_text)

        painter.end()


class StatMetricCard(QFrame):
    def __init__(self, label: str, icon: str = "", accent_color_key: str = "text_primary", parent=None):
        super().__init__(parent)
        self._label = label
        self._icon = icon
        self._accent_color_key = accent_color_key
        self._value = "--"
        self._sub_text = ""
        self._status_bar_color = None
        self.setObjectName("statMetricCard")
        self.setMinimumSize(160, 100)
        self.setMaximumHeight(110)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(16, 14, 16, 14)

        self.value_label = QLabel("--")
        self.value_label.setObjectName("statMetricValue")
        layout.addWidget(self.value_label)

        self.label_label = QLabel(self._label)
        self.label_label.setObjectName("statMetricLabel")
        layout.addWidget(self.label_label)

        self.sub_label = QLabel("")
        self.sub_label.setObjectName("statMetricSub")
        self.sub_label.setVisible(False)
        layout.addWidget(self.sub_label)

        self.status_bar = QFrame()
        self.status_bar.setObjectName("statStatusBar")
        self.status_bar.setFixedHeight(4)
        self.status_bar.setVisible(False)
        layout.addWidget(self.status_bar)

    def set_value(self, value: str, sub_text: str = "", status_color_key: str = None):
        self._value = value
        self._sub_text = sub_text
        self._status_color_key = status_color_key

        self.value_label.setText(value)
        theme = get_theme_manager().get_current_theme()

        if status_color_key:
            color = theme.get(status_color_key, theme.get('text_primary', '#1e293b'))
            self.value_label.setStyleSheet(f"color: {color};")
            self.sub_label.setStyleSheet(f"color: {color};")

        if sub_text:
            self.sub_label.setText(sub_text)
            self.sub_label.setVisible(True)

        if status_color_key:
            bar_color = theme.get(status_color_key, '#22c55e')
            self.status_bar.setStyleSheet(f"background: {bar_color};")
            self.status_bar.setVisible(True)


class HealthScoreGauge(QWidget):
    def __init__(self, size=110, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self._score = 0
        self._animated_score = 0.0
        self._anim = None
        self._glow_phase = 0.0
        self._glow_timer = QTimer(self)
        self._glow_timer.timeout.connect(self._update_glow)
        self._show_glow = False

    def set_score(self, score: int):
        self._score = min(100, max(0, score))
        self._show_glow = True
        self._glow_timer.stop()
        self._glow_timer.start(40)

        if self._anim:
            self._anim.stop()
        self._anim = QPropertyAnimation(self, b"animated_score")
        self._anim.setDuration(1200)
        self._anim.setStartValue(self._animated_score)
        self._anim.setEndValue(self._score)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()

    def _get_animated_score(self):
        return self._animated_score

    def _set_animated_score(self, v):
        self._animated_score = v
        self.update()

    animated_score = Property(float, _get_animated_score, _set_animated_score)

    def _update_glow(self):
        self._glow_phase = (self._glow_phase + 0.08) % (2 * math.pi)
        self.update()
        if self._animated_score >= self._score - 0.5:
            self._glow_phase = 0
            self._glow_timer.stop()
            self._show_glow = False

    def _get_score_color(self, score: float) -> QColor:
        theme = get_theme_manager().get_current_theme()
        if score >= 80:
            return QColor(theme.get('gauge_score_high', '#22c55e'))
        elif score >= 60:
            return QColor(theme.get('gauge_score_mid', '#f59e0b'))
        else:
            return QColor(theme.get('gauge_score_low', '#ef4444'))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        theme = get_theme_manager().get_current_theme()

        cx, cy = self._size / 2, self._size / 2
        outer_r = self._size / 2 - 4
        inner_r = outer_r - 12
        ring_width = 12

        bg_color = parse_theme_color(theme.get('border_subtle', '#e5e7eb'))
        bg_pen = QPen(bg_color, ring_width)
        bg_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(bg_pen)
        painter.drawEllipse(QPointF(cx, cy), inner_r, inner_r)

        score = self._animated_score
        if score > 0:
            progress = score / 100.0
            span_angle = int(-progress * 360 * 16)

            main_color = self._get_score_color(score)

            gradient = QConicalGradient(cx, cy, 90)
            gradient.setColorAt(0, main_color)
            gradient.setColorAt(progress * 0.85, main_color.lighter(115))
            gradient.setColorAt(progress * 0.95, main_color.lighter(130))
            gradient.setColorAt(1.0, main_color.darker(105))

            pen = QPen(QBrush(gradient), ring_width)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawArc(QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2),
                           90 * 16, span_angle)

            if self._show_glow and progress > 0.5:
                glow_alpha = int(60 + 40 * math.sin(self._glow_phase))
                glow_color = QColor(main_color.red(), main_color.green(), main_color.blue(), glow_alpha)
                glow_pen = QPen(glow_color, ring_width + 4)
                glow_pen.setCapStyle(Qt.RoundCap)
                painter.setPen(glow_pen)
                painter.drawArc(QRectF(cx - inner_r - 2, cy - inner_r - 2, inner_r * 2 + 4, inner_r * 2 + 4),
                               90 * 16, span_angle)

        display_score = int(round(score))
        score_color = self._get_score_color(score)

        font = QFont("SF Pro Display", 24, QFont.Bold)
        painter.setFont(font)
        painter.setPen(score_color)
        painter.drawText(QRectF(0, 0, self._size, self._size), Qt.AlignCenter, str(display_score))

        painter.end()


class HorizontalBarChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._bars = []
        self._max_value = 100
        self.setFixedHeight(36)

    def set_data(self, bars: list):
        self._bars = bars
        if bars:
            self._max_value = max(max(b.get('value', 0), 1) for b in bars)
        self.update()

    def paintEvent(self, event):
        if not self._bars:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        theme = get_theme_manager().get_current_theme()

        bar_height = 22
        y_offset = (self.height() - bar_height) // 2
        spacing = max(4, (self.width() - 40) // (len(self._bars) + 1))
        x_start = 16

        for i, bar in enumerate(self._bars):
            x = x_start + i * spacing
            value = bar.get('value', 0)
            color_str = bar.get('color', theme.get('accent_color', '#3b82f6'))
            label = bar.get('label', '')
            max_w = spacing - 8
            w = max(4, int((value / max(self._max_value, 1)) * max_w))

            color = QColor(color_str)
            if not color.isValid():
                color = QColor(color_str)

            rect = QRectF(x, y_offset, w, bar_height)
            path = QPainterPath()
            path.addRoundedRect(rect, bar_height / 2, bar_height / 2)
            painter.fillPath(path, color)

            if w > 30:
                text_color = QColor(theme.get('text_primary', '#ffffff'))
                painter.setPen(text_color.lighter(250))
                font = QFont("Arial", 8, QFont.Bold)
                painter.setFont(font)
                painter.drawText(rect, Qt.AlignCenter, str(value))

        painter.end()


class MiniDonutWidget(QWidget):
    def __init__(self, size=56, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self._pass_rate = 0.0
        self._pass_count = 0
        self._total = 0
        self._animated = 0.0

    def set_data(self, pass_count: int, total: int):
        self._pass_count = pass_count
        self._total = total
        self._pass_rate = pass_count / max(total, 1)
        self._anim = QPropertyAnimation(self, b"animated")
        self._anim.setDuration(800)
        self._anim.setStartValue(self._animated)
        self._anim.setEndValue(self._pass_rate)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()

    def _get_animated(self):
        return self._animated

    def _set_animated(self, v):
        self._animated = v
        self.update()

    animated = Property(float, _get_animated, _set_animated)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        theme = get_theme_manager().get_current_theme()
        cx, cy = self._size / 2, self._size / 2
        outer_r = self._size / 2 - 2
        inner_r = outer_r - 5

        bg_color = QColor(theme.get('border_subtle', '#e5e7eb'))
        bg_pen = QPen(bg_color, 5)
        bg_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(bg_pen)
        painter.drawEllipse(QPointF(cx, cy), inner_r, inner_r)

        if self._total > 0 and self._animated > 0:
            success_color = QColor(theme.get('success_text', '#22c55e'))
            span = int(-self._animated * 360 * 16)
            grad = QConicalGradient(cx, cy, 90)
            grad.setColorAt(0, success_color)
            grad.setColorAt(self._animated * 0.95, success_color)
            grad.setColorAt(1.0, success_color.lighter(140))
            pen = QPen(QBrush(grad), 5)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawArc(QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2),
                           90 * 16, span)

        font = QFont("SF Pro Display", 11, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(theme.get('text_primary', '#1e293b')))
        rate_text = f"{int(self._animated * 100)}%"
        painter.drawText(QRectF(0, 0, self._size, self._size), Qt.AlignCenter, rate_text)

        painter.end()
