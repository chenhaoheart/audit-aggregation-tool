# -*- coding: utf-8 -*-
"""
Dashboard状态指示器基础组件
包含：ClickableHeader, ChevronIcon, DotIndicator, StatusRingWidget
"""

import math
from PySide6.QtWidgets import QWidget, QFrame, QLabel
from PySide6.QtCore import Qt, Signal, QRectF, QTimer, QPropertyAnimation, QEasingCurve, QPointF, Property
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QBrush, QFont, QConicalGradient, QPolygonF

from core.theme_manager import get_theme_manager, parse_theme_color
from .dashboard_constants import STATUS_RING_COLORS, STATUS_ICONS


class ClickableHeader(QFrame):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ChevronIcon(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self._rotation = 0
        self._anim = None

    def set_rotation(self, angle: int):
        self._rotation = angle
        self.update()

    def get_rotation(self):
        return self._rotation

    rotation = Property(int, get_rotation, set_rotation)

    def animate_to(self, target: int):
        if self._anim:
            self._anim.stop()
        self._anim = QPropertyAnimation(self, b"rotation")
        self._anim.setDuration(250)
        self._anim.setStartValue(self._rotation)
        self._anim.setEndValue(target)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._rotation)

        theme = get_theme_manager().get_current_theme()
        color = QColor(theme.get('text_secondary', '#64748b'))
        pen = QPen(color, 2)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)

        arrow = QPolygonF([
            QPointF(-5, -2),
            QPointF(0, 3),
            QPointF(5, -2)
        ])
        painter.drawPolyline(arrow)
        painter.end()


class DotIndicator(QWidget):
    clicked = Signal(int)

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self._index = index
        self._is_active = False
        self.setFixedSize(12, 12)
        self.setCursor(Qt.PointingHandCursor)
        self._theme_manager = get_theme_manager()
        self._theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, mode: str):
        self.update()

    def set_active(self, active: bool):
        self._is_active = active
        if active:
            self.setFixedSize(40, 16)
        else:
            self.setFixedSize(12, 12)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._index)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        theme = get_theme_manager().get_current_theme()

        cx, cy = self.width() / 2, self.height() / 2

        if self._is_active:
            color = QColor(theme.get('accent_color', '#3b82f6'))

            line_width = 32
            line_height = 3
            x = cx - line_width / 2
            y = cy + 4

            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(int(x), int(y), int(line_width), int(line_height), 1.5, 1.5)

            glow_color = QColor(color)
            glow_color.setAlpha(60)
            painter.setBrush(glow_color)
            painter.drawRoundedRect(int(x - 2), int(y - 1), int(line_width + 4), int(line_height + 2), 2.5, 2.5)
        else:
            radius = 3
            bg_color = QColor(theme.get('text_muted', '#94a3b8'))
            bg_color.setAlpha(120)
            painter.setBrush(bg_color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(cx, cy - 1), radius, radius)

        painter.end()


class StatusRingWidget(QWidget):
    def __init__(self, size=60, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size + 16, size + 16)
        self._status = 'pending'
        self._progress = 0.0
        self._animated_progress = 0.0
        self._anim = None
        self._pulse_phase = 0.0
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._update_pulse)
        self._is_running = False

    def set_status(self, status: str):
        self._status = status
        self._is_running = (status == 'running')
        if self._is_running:
            self._pulse_timer.start(50)
        else:
            self._pulse_timer.stop()
            target = 1.0 if status == 'pass' else (0.75 if status == 'warn' else 0.25)
            self._animate_to(target)
        self.update()

    def _animate_to(self, target: float):
        if self._anim:
            self._anim.stop()
        self._anim = QPropertyAnimation(self, b"animated_progress")
        self._anim.setDuration(700)
        self._anim.setStartValue(self._animated_progress)
        self._anim.setEndValue(target)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()

    def _get_animated_progress(self):
        return self._animated_progress

    def _set_animated_progress(self, v):
        self._animated_progress = v
        self.update()

    animated_progress = Property(float, _get_animated_progress, _set_animated_progress)

    def _update_pulse(self):
        self._pulse_phase = (self._pulse_phase + 0.06) % (2 * math.pi)
        self.update()

    def _get_ring_color(self) -> QColor:
        theme = get_theme_manager().get_current_theme()
        color_key = STATUS_RING_COLORS.get(self._status, 'text_muted')
        return QColor(theme.get(color_key, '#64748b'))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        theme = get_theme_manager().get_current_theme()

        cx, cy = self.width() / 2, self.height() / 2
        outer_r = self._size / 2
        inner_r = outer_r - 7
        ring_width = 7
        ring_color = self._get_ring_color()

        bg_color = parse_theme_color(theme.get('border_subtle', '#e5e7eb'))
        bg_pen = QPen(bg_color, ring_width)
        bg_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(bg_pen)
        painter.drawEllipse(QPointF(cx, cy), inner_r, inner_r)

        if self._is_running:
            start_angle = int((self._pulse_phase * 180 / math.pi) * 16) % 57600
            span_angle = 57600 // 3

            gradient = QConicalGradient(cx, cy, self._pulse_phase * 180 / math.pi)
            gradient.setColorAt(0, ring_color)
            gradient.setColorAt(0.35, ring_color.lighter(150))
            gradient.setColorAt(0.5, ring_color.lighter(170))
            gradient.setColorAt(0.65, ring_color.lighter(150))
            gradient.setColorAt(1, ring_color)

            pen = QPen(QBrush(gradient), ring_width)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawArc(QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2),
                           start_angle, span_angle)

            glow_alpha = int(50 + 30 * math.sin(self._pulse_phase))
            glow_color = QColor(ring_color.red(), ring_color.green(), ring_color.blue(), glow_alpha)
            glow_pen = QPen(glow_color, ring_width + 3)
            glow_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(glow_pen)
            painter.drawArc(QRectF(cx - inner_r - 1.5, cy - inner_r - 1.5, inner_r * 2 + 3, inner_r * 2 + 3),
                           start_angle, span_angle)

        elif self._status != 'pending':
            progress = self._animated_progress
            span_angle = int(-progress * 360 * 16)

            gradient = QConicalGradient(cx, cy, 90)
            gradient.setColorAt(0, ring_color)
            gradient.setColorAt(progress * 0.35, ring_color.lighter(130))
            gradient.setColorAt(progress * 0.7, ring_color.lighter(160))
            gradient.setColorAt(1.0, ring_color.darker(105))

            pen = QPen(QBrush(gradient), ring_width)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawArc(QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2),
                           90 * 16, span_angle)

        icon_text = STATUS_ICONS.get(self._status, '\u23f3')
        text_color_key = STATUS_RING_COLORS.get(self._status, 'text_muted')
        text_color = QColor(theme.get(text_color_key, '#64748b'))
        font = QFont("Segoe UI Emoji", 12)
        painter.setFont(font)
        painter.setPen(text_color)
        text_rect = QRectF(cx - 10, cy - 8, 20, 16)
        painter.drawText(text_rect, Qt.AlignCenter, icon_text)

        painter.end()
