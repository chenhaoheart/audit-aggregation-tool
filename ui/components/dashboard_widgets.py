# -*- coding: utf-8 -*-
"""
Dashboard页面专用组件 - Data Observatory风格
包含状态指示器、统计卡片、可折叠卡片等自定义绘制组件
全面重设计版本：玻璃态效果、渐变背景、动态动画
所有样式通过QSS主题令牌控制，不在代码中硬编码颜色
"""

import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
    QSizePolicy, QGraphicsDropShadowEffect, QPushButton, QProgressBar,
    QGridLayout, QStackedWidget
)
from PySide6.QtCore import Qt, Signal, QRectF, QTimer, QPropertyAnimation, QEasingCurve, QPointF, QPoint, QSize, Property
from PySide6.QtGui import (
    QColor, QPainter, QPainterPath, QPen, QBrush, QFont,
    QConicalGradient, QLinearGradient, QPolygonF, QRadialGradient
)

from core.theme_manager import get_theme_manager, parse_theme_color


STATUS_BADGE_MAP = {
    'pass': 'statusBadgePass',
    'fail': 'statusBadgeFail',
    'warn': 'statusBadgeWarn',
    'error': 'statusBadgeFail',
    'pending': 'statusBadgePending',
    'running': 'statusBadgeRunning',
}

CHECK_CARD_BADGE_MAP = {
    'pass': 'checkCardBadgePass',
    'fail': 'checkCardBadgeFail',
    'warn': 'checkCardBadgeWarn',
    'error': 'checkCardBadgeFail',
    'pending': 'checkCardBadgePending',
    'running': 'checkCardBadgeRunning',
}

STATUS_RING_COLORS = {
    'pass': 'success_text',
    'fail': 'error_text',
    'warn': 'warning_text',
    'error': 'error_text',
    'pending': 'text_muted',
    'running': 'accent_color',
}

STATUS_ICONS = {
    'pass': '\u2705',
    'fail': '\u274c',
    'warn': '\u26a0\ufe0f',
    'error': '\ud83d\udd34',
    'pending': '\u23f3',
    'running': '\U0001f504',
}

STATUS_TEXTS = {
    'pass': '\u2705 通过',
    'fail': '\u274c 不通过',
    'warn': '\u26a0\ufe0f 警告',
    'error': '\ud83d\udd34 异常',
    'pending': '\u23f3 待检查',
    'running': '\U0001f504 检查中...',
}


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


class CollapsibleCard(QFrame):
    toggled = Signal(bool)
    expand_finished = Signal()

    def __init__(self, title: str, icon: str, status_key: str = 'pending', parent=None):
        super().__init__(parent)
        self._title = title
        self._icon = icon
        self._status_key = status_key
        self._is_expanded = False
        self._content_height = 0
        self._target_height = 0
        self._height_anim = None
        self.setObjectName("collapsibleCard")
        self._setup_ui()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.header = ClickableHeader()
        self.header.setObjectName("cardHeader")
        self.header.setFixedHeight(52)
        self.header.clicked.connect(self.toggle)

        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(16, 0, 16, 0)
        header_layout.setSpacing(12)

        self.chevron = ChevronIcon()
        header_layout.addWidget(self.chevron)

        icon_label = QLabel(self._icon)
        icon_label.setObjectName("cardIcon")
        icon_label.setFixedWidth(28)
        header_layout.addWidget(icon_label)

        self.title_label = QLabel(self._title)
        self.title_label.setObjectName("cardTitle")
        header_layout.addWidget(self.title_label, 1)

        self.status_badge = QLabel("\u23f3 待检查")
        self.status_badge.setObjectName("statusBadgePending")
        self.status_badge.setAlignment(Qt.AlignCenter)
        self.status_badge.setFixedHeight(26)
        header_layout.addWidget(self.status_badge)

        self.content_wrapper = QWidget()
        self.content_wrapper.setObjectName("cardContentWrapper")
        self.content_layout = QVBoxLayout(self.content_wrapper)
        self.content_layout.setContentsMargins(16, 12, 16, 16)
        self.content_layout.setSpacing(8)

        self.content_area = QScrollArea()
        self.content_area.setWidgetResizable(True)
        self.content_area.setFrameShape(QFrame.NoFrame)
        self.content_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.content_area.setObjectName("cardContentScrollArea")
        self.content_widget = QWidget()
        self.content_widget.setObjectName("cardContent")
        self.inner_layout = QVBoxLayout(self.content_widget)
        self.inner_layout.setContentsMargins(0, 0, 0, 0)
        self.content_area.setWidget(self.content_widget)
        self.content_layout.addWidget(self.content_area)

        self.content_wrapper.setMaximumHeight(0)
        self.content_wrapper.setMinimumHeight(0)
        self.main_layout.addWidget(self.header)
        self.main_layout.addWidget(self.content_wrapper)

    def set_status(self, status: str):
        self._status_key = status
        badge_obj_name = STATUS_BADGE_MAP.get(status, 'statusBadgePending')
        self.status_badge.setObjectName(badge_obj_name)
        self.status_badge.setStyle(self.status_badge.style())
        icon = STATUS_ICONS.get(status, '\u23f3')
        text = STATUS_TEXTS.get(status, '\u23f3 待检查')
        self.status_badge.setText(f"{icon} {text.removeprefix(icon + ' ')}")

    def set_content_widget(self, widget: QWidget):
        self.inner_layout.addWidget(widget)

    def toggle(self):
        self._is_expanded = not self._is_expanded
        self.toggled.emit(self._is_expanded)

        if self._is_expanded:
            self.chevron.animate_to(180)
            self._animate_expand()
        else:
            self.chevron.animate_to(0)
            self._animate_collapse()

    def _animate_expand(self):
        self.content_widget.adjustSize()
        content_hint = self.content_widget.sizeHint().height()
        scroll_margin = 40
        target = max(400, content_hint + scroll_margin)

        if self._height_anim:
            self._height_anim.stop()

        self.content_wrapper.setMinimumHeight(0)
        self.content_wrapper.setMaximumHeight(16777215)
        self._height_anim = QPropertyAnimation(self.content_wrapper, b"minimumHeight")
        self._height_anim.setDuration(350)
        self._height_anim.setStartValue(0)
        self._height_anim.setEndValue(target)
        self._height_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._height_anim.finished.connect(lambda: self.expand_finished.emit())
        self._height_anim.start()

    def _animate_collapse(self):
        if self._height_anim:
            self._height_anim.stop()
        self._height_anim = QPropertyAnimation(self.content_wrapper, b"minimumHeight")
        self._height_anim.setDuration(250)
        self._height_anim.setStartValue(self.content_wrapper.height())
        self._height_anim.setEndValue(0)
        self._height_anim.setEasingCurve(QEasingCurve.InCubic)
        self._height_anim.start()
        self.content_wrapper.setMaximumHeight(0)

    def expand(self):
        if not self._is_expanded:
            self.toggle()

    def collapse(self):
        if self._is_expanded:
            self.toggle()

    def is_expanded(self):
        return self._is_expanded


class CollapsibleCardsContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards = []
        self._setup_ui()

    def _setup_ui(self):
        self.cards_layout = QVBoxLayout(self)
        self.cards_layout.setSpacing(12)
        self.cards_layout.setContentsMargins(0, 8, 0, 8)

    def add_card(self, card: CollapsibleCard):
        self._cards.append(card)
        self.cards_layout.addWidget(card)
        card.toggled.connect(self._on_card_toggled)

    def _on_card_toggled(self, expanded: bool):
        pass

    def get_card(self, index: int):
        if 0 <= index < len(self._cards):
            return self._cards[index]
        return None

    def cards(self):
        return self._cards


class DotIndicator(QWidget):
    clicked = Signal(int)

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self._index = index
        self._is_active = False
        self.setFixedSize(12, 12)
        self.setCursor(Qt.PointingHandCursor)

    def set_active(self, active: bool):
        self._is_active = active
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

            line_width = 16
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


class HorizontalSwipeCards(QWidget):
    current_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards = []
        self._current_index = -1
        self._dots = []
        self._slide_anim = None
        self.setObjectName("horizontalSwipeCards")
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.dots_container = QWidget()
        self.dots_layout = QHBoxLayout(self.dots_container)
        self.dots_layout.setSpacing(8)
        self.dots_layout.setContentsMargins(0, 8, 0, 8)
        content_container = QFrame()
        content_container.setObjectName("swipeContentContainer")
        content_layout = QHBoxLayout(content_container)
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(40, 12, 40, 12)
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("swipeContentStack")
        content_layout.addWidget(self.content_stack, 1)

        self.prev_btn = QPushButton("\u25c0")
        self.prev_btn.setObjectName("swipeNavBtn")
        self.prev_btn.setFixedSize(36, 36)
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.clicked.connect(self.prev_card)
        self.prev_btn.setParent(content_container)
        self.prev_btn.raise_()

        self.next_btn = QPushButton("\u25b6")
        self.next_btn.setObjectName("swipeNavBtn")
        self.next_btn.setFixedSize(36, 36)
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.clicked.connect(self.next_card)
        self.next_btn.setParent(content_container)
        self.next_btn.raise_()

        main_layout.addWidget(content_container, 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_nav_buttons()

    def _position_nav_buttons(self):
        parent = self.prev_btn.parentWidget()
        if not parent:
            return
        btn_y = parent.height() // 2 - 18
        self.prev_btn.move(6, btn_y)
        self.next_btn.move(parent.width() - 42, btn_y)

    def add_card(self, title: str, icon: str, content_widget: QWidget = None):
        index = len(self._cards)
        card_info = {
            'title': title,
            'icon': icon,
            'status': 'pending',
            'content': content_widget,
        }
        self._cards.append(card_info)

        dot = DotIndicator(index)
        dot.clicked.connect(self.set_current_index)
        self._dots.append(dot)
        self.dots_layout.addWidget(dot)

        if content_widget:
            content_widget.setObjectName("swipeCardContent")
            self.content_stack.addWidget(content_widget)

        if self._current_index < 0:
            self._current_index = 0
            dot.set_active(True)
            self.content_stack.setCurrentIndex(0)

        self._update_nav_buttons()

    def set_card_status(self, index: int, status: str):
        if 0 <= index < len(self._cards):
            self._cards[index]['status'] = status

    def set_current_index(self, index: int):
        if index < 0 or index >= len(self._cards) or index == self._current_index:
            return

        old_index = self._current_index
        self._current_index = index

        for i, dot in enumerate(self._dots):
            dot.set_active(i == index)

        direction = 1 if index > old_index else -1
        self._animate_slide(old_index, index, direction)

        self._update_nav_buttons()
        self.current_changed.emit(index)

    def _animate_slide(self, old_index: int, new_index: int, direction: int):
        old_widget = self.content_stack.widget(old_index)
        new_widget = self.content_stack.widget(new_index)
        if not old_widget or not new_widget:
            self.content_stack.setCurrentIndex(new_index)
            return

        self.content_stack.setCurrentIndex(new_index)

        width = self.content_stack.width()
        if width <= 0:
            return

        new_widget.move(direction * width, 0)
        new_widget.show()

        if self._slide_anim:
            self._slide_anim.stop()

        self._slide_anim = QPropertyAnimation(new_widget, b"pos")
        self._slide_anim.setDuration(300)
        self._slide_anim.setStartValue(QPoint(direction * width, 0))
        self._slide_anim.setEndValue(QPoint(0, 0))
        self._slide_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._slide_anim.start()

    def _update_nav_buttons(self):
        pass

    def prev_card(self):
        if len(self._cards) == 0:
            return
        new_index = (self._current_index - 1) % len(self._cards)
        self.set_current_index(new_index)

    def next_card(self):
        if len(self._cards) == 0:
            return
        new_index = (self._current_index + 1) % len(self._cards)
        self.set_current_index(new_index)

    def current_index(self):
        return self._current_index

    def get_card_count(self):
        return len(self._cards)


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


class CheckCategoryCard(QFrame):
    def __init__(self, key: str, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self._key = key
        self._title = title
        self._subtitle = subtitle
        self._status = 'pending'
        self._detail_text = ""
        self.setObjectName("checkCategoryCard")
        self.setFixedHeight(130)
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        self.ring = StatusRingWidget(52, self)
        layout.addWidget(self.ring, 0, Qt.AlignVCenter | Qt.AlignLeft)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        self.title_label = QLabel(self._title)
        self.title_label.setObjectName("checkCardTitle")
        text_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel(self._subtitle)
        self.subtitle_label.setObjectName("pageSubtitle")
        text_layout.addWidget(self.subtitle_label)

        self.detail_label = QLabel("")
        self.detail_label.setObjectName("checkCardDetail")
        text_layout.addWidget(self.detail_label)

        self.status_badge = QLabel("\u23f3 \u5f85\u68c0\u67e5")
        self.status_badge.setObjectName("checkCardBadgePending")
        self.status_badge.setAlignment(Qt.AlignCenter)
        self.status_badge.setFixedHeight(24)
        text_layout.addWidget(self.status_badge)

        layout.addLayout(text_layout, 1)

    def update_status(self, status: str, detail: str = ""):
        self._status = status
        self.ring.set_status(status)
        badge_obj_name = CHECK_CARD_BADGE_MAP.get(status, 'checkCardBadgePending')
        self.status_badge.setObjectName(badge_obj_name)
        self.status_badge.setStyle(self.status_badge.style())
        icon = STATUS_ICONS.get(status, '\u23f3')
        text = STATUS_TEXTS.get(status, '\u23f3 待检查')
        self.status_badge.setText(f"{icon} {text.removeprefix(icon + ' ')}")
        if detail:
            self.detail_label.setText(detail)
            self.detail_label.setVisible(True)
        else:
            self.detail_label.setVisible(False)


class CheckStatusPanel(QFrame):
    clicked = Signal(str)

    def __init__(self, key: str, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self._key = key
        self._title = title
        self._subtitle = subtitle
        self._status = 'pending'
        self._detail_text = ""
        self.setObjectName("checkStatusPanel")
        self.setFixedHeight(100)
        self.setMinimumWidth(160)
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self.ring = StatusRingWidget(48, self)
        layout.addWidget(self.ring, 0, Qt.AlignVCenter)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        self.title_label = QLabel(self._title)
        self.title_label.setObjectName("panelTitle")
        info_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel(self._subtitle)
        self.subtitle_label.setObjectName("panelSubtitle")
        info_layout.addWidget(self.subtitle_label)

        self.detail_label = QLabel("")
        self.detail_label.setObjectName("panelDetail")
        self.detail_label.setVisible(False)
        info_layout.addWidget(self.detail_label)

        layout.addLayout(info_layout, 1)

    def mousePressEvent(self, event):
        self.clicked.emit(self._key)
        super().mousePressEvent(event)

    def update_status(self, status: str, detail: str = ""):
        self._status = status
        self.ring.set_status(status)

        if detail:
            self.detail_label.setText(detail)
            self.detail_label.setVisible(True)
        else:
            self.detail_label.setVisible(False)


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


class CrossCheckTimeline(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self.setFixedHeight(200)

    def set_items(self, items: list):
        self._items = items
        h = min(200, max(60, len(items) * 46 + 20))
        self.setFixedHeight(h)
        self.update()

    def paintEvent(self, event):
        if not self._items:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        theme = get_theme_manager().get_current_theme()

        line_x = 32
        line_top = 20
        line_bottom = self.height() - 20

        pen = QPen(QColor(theme.get('border_subtle', '#e5e7eb')), 2)
        painter.setPen(pen)
        painter.drawLine(line_x, line_top, line_x, line_bottom)

        error_color = QColor(theme.get('error_text', '#ef4444'))
        warn_color = QColor(theme.get('warning_text', '#f59e0b'))

        y = line_top
        for item in self._items[:8]:
            level = item.get('level', '')
            is_error = level == 'error'
            dot_color = error_color if is_error else warn_color

            painter.setBrush(dot_color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(line_x, y), 6, 6)

            cat_text = item.get('category', '')
            desc_text = item.get('desc', '')

            font_cat = QFont("Microsoft YaHei UI", 10, QFont.Bold)
            painter.setFont(font_cat)
            cat_color = error_color if is_error else warn_color
            painter.setPen(cat_color)
            painter.drawText(line_x + 18, y - 4, cat_text)

            font_desc = QFont("Microsoft YaHei UI", 9)
            painter.setFont(font_desc)
            desc_color = QColor(theme.get('text_secondary', '#64748b'))
            painter.setPen(desc_color)
            max_w = self.width() - line_x - 24
            elided_desc = painter.fontMetrics().elidedText(desc_text, Qt.ElideRight, max_w)
            painter.drawText(line_x + 18, y + 14, elided_desc)

            y += 46

        if len(self._items) > 8:
            more_font = QFont("Microsoft YaHei UI", 9)
            painter.setFont(more_font)
            painter.setPen(QColor(theme.get('text_muted', '#94a3b8')))
            painter.drawText(line_x + 18, y + 4, f"... \u8fd8\u6709 {len(self._items) - 8} \u9879")

        painter.end()


class CheckProgressPanel(QFrame):
    cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_section = ""
        self._progress_value = 0
        self.setObjectName("checkProgressPanel")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(20, 12, 20, 12)

        self.progress_container = QWidget()
        progress_layout = QHBoxLayout(self.progress_container)
        progress_layout.setSpacing(12)
        progress_layout.setContentsMargins(0, 0, 0, 0)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("dashboardProgress")
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        progress_layout.addWidget(self.progress_bar, 1)

        self.cancel_btn = QPushButton("\u2716")
        self.cancel_btn.setFixedSize(28, 28)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.cancelled.emit)
        self.cancel_btn.setObjectName("cancelProgressBtn")
        progress_layout.addWidget(self.cancel_btn)

        layout.addWidget(self.progress_container)

        status_layout = QHBoxLayout()
        status_layout.setSpacing(8)

        self.section_label = QLabel("\U0001f504 正在检查...")
        self.section_label.setObjectName("progressSection")
        status_layout.addWidget(self.section_label, 1)

        self.percent_label = QLabel("0%")
        self.percent_label.setObjectName("progressPercent")
        self.percent_label.setAlignment(Qt.AlignRight)
        status_layout.addWidget(self.percent_label)

        layout.addLayout(status_layout)

    def set_progress(self, value: int, section: str = ""):
        self._progress_value = min(100, max(0, value))
        self.progress_bar.setValue(self._progress_value)
        self.percent_label.setText(f"{self._progress_value}%")

        if section:
            self._current_section = section
            self.section_label.setText(f"\U0001f504 {section}")

    def set_indeterminate(self, section: str = ""):
        self.progress_bar.setRange(0, 0)
        self.percent_label.setText("...")
        if section:
            self.section_label.setText(f"\U0001f504 {section}")

    def reset(self):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.percent_label.setText("0%")
        self.section_label.setText("\u23f3 准备检查...")


class SpatialLayerCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("spatialLayerCard")
        self.setFixedHeight(120)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.file_name = QLabel("...")
        self.file_name.setObjectName("layerCardName")
        top_row.addWidget(self.file_name, 1)

        self.status_badge = QLabel("")
        self.status_badge.setObjectName("statusBadge")
        self.status_badge.setFixedHeight(22)
        top_row.addWidget(self.status_badge, 0, Qt.AlignVCenter)

        layout.addLayout(top_row)

        self.folder_label = QLabel("")
        self.folder_label.setObjectName("folderLabel")
        layout.addWidget(self.folder_label)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        stat1 = QHBoxLayout()
        stat1.setSpacing(4)
        self.total_label = QLabel("")
        self.total_label.setObjectName("layerStatText")
        stat1.addWidget(self.total_label)
        stats_row.addLayout(stat1, 1)

        stat2 = QHBoxLayout()
        stat2.setSpacing(4)
        self.valid_label = QLabel("")
        self.valid_label.setObjectName("layerStatValid")
        stat2.addWidget(self.valid_label)
        stats_row.addLayout(stat2, 1)

        stat3 = QHBoxLayout()
        stat3.setSpacing(4)
        self.invalid_label = QLabel("")
        self.invalid_label.setObjectName("layerStatInvalid")
        stat3.addWidget(self.invalid_label)
        stats_row.addLayout(stat3, 1)

        stat4 = QHBoxLayout()
        stat4.setSpacing(4)
        self.duplicate_label = QLabel("")
        self.duplicate_label.setObjectName("layerStatDup")
        stat4.addWidget(self.duplicate_label)
        stats_row.addLayout(stat4, 1)

        layout.addLayout(stats_row)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)

        self.error_preview = QLabel("")
        self.error_preview.setObjectName("errorPreviewLabel")
        self.error_preview.setWordWrap(True)
        bottom_row.addWidget(self.error_preview, 1)

        right = QVBoxLayout()
        right.setSpacing(2)
        right.setAlignment(Qt.AlignCenter)
        self.efficiency_label = QLabel("--%")
        self.efficiency_label.setObjectName("efficiencyLabel")
        self.efficiency_label.setAlignment(Qt.AlignCenter)
        right.addWidget(self.efficiency_label, 0, Qt.AlignCenter)
        bottom_row.addLayout(right, 0)

        layout.addLayout(bottom_row)

    def set_data(self, file_name: str, status: str, total: int, valid: int, invalid: int,
                 folder_name: str = "", duplicate_records: int = 0, errors: list = None):
        self.file_name.setText(file_name)

        status_config = {
            '通过': ('✅ 通过', 'spatialBadgePass'),
            '存在错误': ('❌ 异常', 'spatialBadgeFail'),
            '文件未找到': ('⚠️ 未找到', 'spatialBadgeWarn'),
            '读取失败': ('💥 失败', 'spatialBadgeFail'),
        }
        status_text, badge_obj = status_config.get(status, (status, 'spatialBadgePending'))
        self.status_badge.setText(f"  {status_text}  ")
        self.status_badge.setObjectName(badge_obj)
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)

        if folder_name:
            self.folder_label.setText(f"📁 {folder_name}")
            self.folder_label.setVisible(True)
        else:
            self.folder_label.setVisible(False)

        self.total_label.setText(f"📋 总计 {total}")
        self.valid_label.setText(f"✅ 有效 {valid}")
        self.invalid_label.setText(f"❌ 无效 {invalid}")
        if duplicate_records > 0:
            self.duplicate_label.setText(f"🔄 重复 {duplicate_records}")
            self.duplicate_label.setVisible(True)
        else:
            self.duplicate_label.setVisible(False)

        pct = f"{valid / max(total, 1) * 100:.1f}%"
        self.efficiency_label.setText(pct)

        is_pass = status == '通过'
        eff_obj = 'efficiencyLabelPass' if is_pass else 'efficiencyLabelFail'
        self.efficiency_label.setObjectName(eff_obj)
        self.efficiency_label.style().unpolish(self.efficiency_label)
        self.efficiency_label.style().polish(self.efficiency_label)

        if errors and len(errors) > 0:
            error_text = "⚠️ " + "; ".join(errors[:2])
            if len(errors) > 2:
                error_text += f" 等{len(errors)}项"
            self.error_preview.setText(error_text)
            self.error_preview.setVisible(True)
        else:
            self.error_preview.setVisible(False)


class SpatialResultGrid(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("spatialResultGrid")
        self._cards = []
        self._setup_ui()

    def _setup_ui(self):
        self.main_layout = QGridLayout(self)
        self.main_layout.setSpacing(12)
        self.main_layout.setContentsMargins(4, 4, 4, 4)

    def set_data(self, results: list):
        for card in self._cards:
            card.deleteLater()
        self._cards.clear()
        while item := self.main_layout.takeAt(0):
            if item.widget():
                item.widget().deleteLater()

        if not results:
            empty = QLabel("\ud83d\udccd \u6682\u65e0\u7a7a\u95f4\u6570\u636e")
            empty.setObjectName("emptyState")
            empty.setAlignment(Qt.AlignCenter)
            self.main_layout.addWidget(empty, 0, 0, 1, -1)
            return

        for i, r in enumerate(results):
            card = SpatialLayerCard()
            card.set_data(
                r.get('file_name', 'Unknown'),
                r.get('status', ''),
                r.get('total_records', 0),
                r.get('valid_records', 0),
                r.get('invalid_records', 0),
                folder_name=r.get('folder_name', ''),
                duplicate_records=r.get('duplicate_records', 0),
                errors=r.get('errors', [])
            )
            col = i % 2
            row = i // 2
            self.main_layout.addWidget(card, row, col)
            self._cards.append(card)


class PhotoMatchDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("photoMatchDashboard")
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(16)

        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        self.fubiao2_card = StatMetricCard("附表2匹配", "\ud83d\udccb", "text_primary")
        self.fubiao2_card.setMinimumHeight(80)
        top_row.addWidget(self.fubiao2_card, 1)

        self.fubiao3_card = StatMetricCard("附表3匹配", "\ud83d\udcf7", "text_primary")
        self.fubiao3_card.setMinimumHeight(80)
        top_row.addWidget(self.fubiao3_card, 1)

        self.photo_status_card = StatMetricCard("照片状态", "\U0001f4f8", "text_primary")
        self.photo_status_card.setMinimumHeight(80)
        top_row.addWidget(self.photo_status_card, 1)

        main_layout.addLayout(top_row)

        donut_row = QHBoxLayout()
        donut_row.setSpacing(24)
        donut_row.setAlignment(Qt.AlignCenter)

        f2_container = QWidget()
        f2_layout = QVBoxLayout(f2_container)
        f2_layout.setAlignment(Qt.AlignCenter)
        f2_title = QLabel("附表2 匹配率")
        f2_title.setObjectName("pageSubtitle")
        f2_title.setAlignment(Qt.AlignCenter)
        f2_layout.addWidget(f2_title)
        self.donut_f2 = MiniDonutWidget(72)
        f2_layout.addWidget(self.donut_f2, 0, Qt.AlignHCenter)
        donut_row.addWidget(f2_container)

        f3_container = QWidget()
        f3_layout = QVBoxLayout(f3_container)
        f3_layout.setAlignment(Qt.AlignCenter)
        f3_title = QLabel("附表3 匹配率")
        f3_title.setObjectName("pageSubtitle")
        f3_title.setAlignment(Qt.AlignCenter)
        f3_layout.addWidget(f3_title)
        self.donut_f3 = MiniDonutWidget(72)
        f3_layout.addWidget(self.donut_f3, 0, Qt.AlignHCenter)
        donut_row.addWidget(f3_container)

        main_layout.addLayout(donut_row)

        bar_section = QWidget()
        bar_section.setObjectName("cardInnerPanel")
        bar_layout = QHBoxLayout(bar_section)
        bar_layout.setContentsMargins(16, 8, 16, 8)
        bar_layout.setSpacing(20)

        self.bar_f2 = HorizontalBarChart()
        self.bar_f2.setFixedHeight(40)
        bar_layout.addWidget(self.bar_f2, 1)

        self.bar_f3 = HorizontalBarChart()
        self.bar_f3.setFixedHeight(40)
        bar_layout.addWidget(self.bar_f3, 1)

        main_layout.addWidget(bar_section)

    def set_data(self, summary: dict):
        f2_total = summary.get('fubiao2_total', 0)
        f2_matched = summary.get('fubiao2_matched', 0)
        f2_unmatched = summary.get('fubiao2_unmatched', 0)
        f3_total = summary.get('fubiao3_total', 0)
        f3_matched = summary.get('fubiao3_matched', 0)
        f3_unmatched = summary.get('fubiao3_unmatched', 0)
        photo_umatched = summary.get('photo_unmatched_f2', 0) + summary.get('photo_unmatched_f3', 0)

        f2_rate = f"{f2_matched / max(f2_total, 1) * 100:.0f}%"
        f3_rate = f"{f3_matched / max(f3_total, 1) * 100:.0f}%"

        f2_color = 'success_text' if f2_unmatched == 0 else ('warning_text' if f2_unmatched < 5 else 'error_text')
        f3_color = 'success_text' if f3_unmatched == 0 else ('warning_text' if f3_unmatched < 5 else 'error_text')
        p_color = 'success_text' if photo_umatched == 0 else ('warning_text' if photo_umatched < 5 else 'error_text')

        self.fubiao2_card.set_value(f2_rate, f"匹配{f2_matched}/{f2_total}", f2_color)
        self.fubiao3_card.set_value(f3_rate, f"匹配{f3_matched}/{f3_total}", f3_color)
        self.photo_status_card.set_value(str(photo_umatched), "张未匹配照片", p_color)

        self.donut_f2.set_data(f2_matched, max(f2_total, 1))
        self.donut_f3.set_data(f3_matched, max(f3_total, 1))

        theme = get_theme_manager().get_current_theme()
        success_c = theme.get('success_text', '#22c55e')
        warn_c = theme.get('warning_text', '#f59e0b')
        error_c = theme.get('error_text', '#ef4444')

        self.bar_f2.set_data([
            {'label': '', 'value': f2_matched, 'color': success_c},
            {'label': '', 'value': f2_unmatched, 'color': error_c},
        ])
        self.bar_f3.set_data([
            {'label': '', 'value': f3_matched, 'color': success_c},
            {'label': '', 'value': f3_unmatched, 'color': error_c},
        ])


class CrossIssueItem(QFrame):
    clicked = Signal(dict)

    def __init__(self, item_data: dict, parent=None):
        super().__init__(parent)
        self._data = item_data
        self.setObjectName("crossIssueItem")
        self.setCursor(Qt.PointingHandCursor)
        self._base_height = 90
        self._expanded_height_add = 50
        self.setFixedHeight(self._base_height)
        self._expanded = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        level = self._data.get('level', '')
        is_error = level == 'error'

        indicator = QFrame()
        indicator.setObjectName("issueIndicator")
        indicator.setFixedWidth(4)
        layout.addWidget(indicator)

        info_col = QVBoxLayout()
        info_col.setSpacing(3)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        cat_badge = QLabel(self._data.get('category', ''))
        cat_badge.setObjectName("issueCategoryBadge")
        header_row.addWidget(cat_badge)

        level_badge = QLabel('\u274c \u9519\u8bef' if is_error else '\u26a0 \u8b66\u544a')
        level_badge.setObjectName("statusBadgeFail" if is_error else "statusBadgeWarn")
        header_row.addWidget(level_badge)
        header_row.addStretch()
        info_col.addLayout(header_row)

        desc_label = QLabel(self._data.get('desc', ''))
        desc_label.setObjectName("issueDescText")
        desc_label.setWordWrap(True)
        info_col.addWidget(desc_label)

        detail = self._data.get('detail', [])
        if detail and isinstance(detail, list):
            det_str = '; '.join(str(d) for d in detail[:3])
            if len(detail) > 3:
                det_str += f" ... (+{len(detail)-3})"
            self.detail_label = QLabel(det_str)
            self.detail_label.setObjectName("issueDetailText")
            self.detail_label.setVisible(False)
            self.detail_label.setWordWrap(True)
            info_col.addWidget(self.detail_label)
        else:
            self.detail_label = None

        layout.addLayout(info_col, 1)

        self.chevron_btn = QPushButton("\u25bc")
        self.chevron_btn.setObjectName("issueChevronBtn")
        self.chevron_btn.setFixedSize(28, 28)
        self.chevron_btn.setCursor(Qt.PointingHandCursor)
        self.chevron_btn.clicked.connect(self._toggle_detail)
        layout.addWidget(self.chevron_btn, 0, Qt.AlignVCenter | Qt.AlignRight)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            child = self.childAt(event.pos())
            if child != self.chevron_btn:
                self._toggle_detail()
            self.clicked.emit(self._data)
        super().mousePressEvent(event)

    def _toggle_detail(self):
        self._expanded = not self._expanded
        if self.detail_label:
            self.detail_label.setVisible(self._expanded)
            target_h = self._base_height + (self._expanded_height_add if self._expanded else 0)

            rotation = 180 if self._expanded else 0
            self._animate_chevron(rotation)

            anim = QPropertyAnimation(self, b"minimumHeight")
            anim.setDuration(200)
            anim.setStartValue(self.height())
            anim.setEndValue(target_h)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.start()

            anim2 = QPropertyAnimation(self, b"maximumHeight")
            anim2.setDuration(200)
            anim2.setStartValue(self.height())
            anim2.setEndValue(target_h)
            anim2.setEasingCurve(QEasingCurve.OutCubic)
            anim2.start()

    def expand(self, animate: bool = False):
        if not self._expanded and self.detail_label:
            self._expanded = True
            self.detail_label.setVisible(True)
            target_h = self._base_height + self._expanded_height_add

            if animate:
                rotation = 180
                self._animate_chevron(rotation)

                anim = QPropertyAnimation(self, b"minimumHeight")
                anim.setDuration(200)
                anim.setStartValue(self.height())
                anim.setEndValue(target_h)
                anim.setEasingCurve(QEasingCurve.OutCubic)
                anim.start()

                anim2 = QPropertyAnimation(self, b"maximumHeight")
                anim2.setDuration(200)
                anim2.setStartValue(self.height())
                anim2.setEndValue(target_h)
                anim2.setEasingCurve(QEasingCurve.OutCubic)
                anim2.start()
            else:
                self.setFixedHeight(target_h)
                self.chevron_btn.setText('\u25b2')

    def _animate_chevron(self, angle: int):
        icon = '\u25b2' if angle == 180 else '\u25bc'
        self.chevron_btn.setText(icon)


class CrossCheckListPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("crossCheckListPanel")
        self._items = []
        self._setup_ui()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        self.header_widget = QWidget()
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(4, 0, 4, 0)
        self.error_count = QLabel("\u274c 错误: 0")
        self.error_count.setObjectName("crossErrorCount")
        header_layout.addWidget(self.error_count)
        self.warn_count = QLabel("\u26a0 警告: 0")
        self.warn_count.setObjectName("crossWarnCount")
        header_layout.addWidget(self.warn_count)
        header_layout.addStretch()
        main_layout.addWidget(self.header_widget)

        self.items_scroll = QScrollArea()
        self.items_scroll.setWidgetResizable(True)
        self.items_scroll.setFrameShape(QFrame.NoFrame)
        self.items_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.items_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.items_scroll.setObjectName("crossItemsScrollArea")

        items_content = QWidget()
        self.items_layout = QVBoxLayout(items_content)
        self.items_layout.setContentsMargins(4, 4, 4, 4)
        self.items_layout.setSpacing(8)
        self.items_layout.addStretch()
        self.items_scroll.setWidget(items_content)
        main_layout.addWidget(self.items_scroll, 1)

    def set_items(self, items: list):
        for item in self._items:
            item.deleteLater()
        self._items.clear()
        while i := self.items_layout.takeAt(0):
            if i.widget():
                i.widget().deleteLater()
        self.items_layout.addStretch()

        errors = sum(1 for i in items if i.get('level') == 'error')
        warnings = sum(1 for i in items if i.get('level') == 'warn')
        self.error_count.setText(f"\u274c 错误: {errors}")
        self.warn_count.setText(f"\u26a0 警告: {warnings}")

        if not items:
            empty = QLabel("\u2705 \u65e0\u4ea4\u53c9\u6821\u9a8c\u95ee\u9898")
            empty.setObjectName("emptyState")
            empty.setAlignment(Qt.AlignCenter)
            empty.setMinimumHeight(100)
            self.items_layout.insertWidget(0, empty)
            return

        for item in items:
            issue_item = CrossIssueItem(item)
            self.items_layout.insertWidget(len(self._items), issue_item)
            self._items.append(issue_item)

        for item in self._items:
            item.expand(animate=False)
