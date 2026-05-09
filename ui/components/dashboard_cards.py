# -*- coding: utf-8 -*-
"""
Dashboard检查卡片与面板组件
包含：CollapsibleCard, CollapsibleCardsContainer, CheckCategoryCard,
     CheckStatusPanel, CheckProgressPanel, HorizontalSwipeCards
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
    QSizePolicy, QPushButton, QProgressBar, QStackedWidget
)
from PySide6.QtCore import Qt, Signal, QPoint, QPropertyAnimation, QEasingCurve

from core.theme_manager import get_theme_manager
from .dashboard_constants import STATUS_BADGE_MAP, CHECK_CARD_BADGE_MAP, STATUS_ICONS, STATUS_TEXTS
from .dashboard_indicators import ClickableHeader, ChevronIcon, DotIndicator, StatusRingWidget


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
