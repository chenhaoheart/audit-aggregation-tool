# -*- coding: utf-8 -*-
"""
Modern Navigation Sidebar

Clean, minimal sidebar with:
- Smooth hover/active animations
- Collapsible with icon-only mode
- Theme switcher integrated at bottom
- Active indicator with accent color bar
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget,
    QGraphicsOpacityEffect, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QTimer
from PySide6.QtGui import QKeyEvent

from core.theme_manager import get_theme_manager


MENU_CONFIG = [
    {"id": "dashboard", "icon": "\U0001f4ca", "text": "Dashboard\u6c47\u603b\u68c0\u67e5"},
    {"id": "check_config", "icon": "\U0001f50d", "text": "\u7a7a\u95f4\u6570\u636e\u68c0\u67e5"},
    {"id": "report", "icon": "\U0001f4c8", "text": "\u6210\u679c\u62a5\u8868\u5c55\u793a"},
    {"id": "section_check", "icon": "\U0001f4d0", "text": "\u65ad\u9762\u6570\u636e\u68c0\u67e5"},
    {"id": "photo_gallery", "icon": "\U0001f4f7", "text": "\u7167\u7247\u68c0\u67e5"},
    {"id": "shp_format", "icon": "\U0001f6e0\ufe0f", "text": "SHP\u5c5e\u6027\u683c\u5f0f\u5316"},
]

ITEM_TO_PAGE = {
    "dashboard": 0,
    "check_config": 1,
    "check_summary": 1,
    "check_duanmian": 1,
    "check_fangzhi": 1,
    "check_yinhuan": 1,
    "check_water": 1,
    "check_map": 1,
    "report": 2,
    "section_check": 3,
    "photo_gallery": 4,
    "shp_format": 5,
}

WIDTH_EXPANDED = 220
WIDTH_COLLAPSED = 68
ANIMATION_DURATION = 220


class _NavItem(QPushButton):
    """Navigation item with active indicator bar"""

    def __init__(self, icon: str, text: str, item_id: str, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self._icon = icon
        self._text = text
        self.setObjectName("navItem")
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.setMinimumHeight(42)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._update_display(False)

    def _update_display(self, collapsed: bool):
        if collapsed:
            self.setText(f"  {self._icon}")
            self.setToolTip(self._text)
        else:
            self.setText(f"  {self._icon}   {self._text}")
            self.setToolTip("")


class _NavIndicator(QFrame):
    """Active indicator bar - thin accent line on left"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("navIndicator")
        self.setFixedWidth(3)
        self.setFixedHeight(24)
        self.hide()


class ModernSidebar(QFrame):
    """Modern navigation sidebar with clean design"""

    item_selected = Signal(str)
    theme_changed = Signal(str)
    collapse_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_manager = get_theme_manager()
        self._collapsed = False
        self._animating = False
        self._current_item_id = "check_config"

        self.setObjectName("modernSidebar")
        self.setFixedWidth(WIDTH_EXPANDED)
        self.setFocusPolicy(Qt.StrongFocus)

        self._nav_items: list[_NavItem] = []
        self._indicators: list[_NavIndicator] = []
        self._collapsed_btns: list[QPushButton] = []

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # ========== Header ==========
        self._header = QWidget()
        self._header.setObjectName("sidebarHeader")
        header_layout = QVBoxLayout(self._header)
        header_layout.setSpacing(4)
        header_layout.setContentsMargins(16, 20, 16, 16)

        self.title_label = QLabel("\U0001f30f \u5ba1\u6838\u6c47\u96c6")
        self.title_label.setObjectName("sidebarTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("\u98ce\u9669\u9690\u60a3\u8c03\u67e5\u5ba1\u6838\u5de5\u5177")
        self.subtitle_label.setObjectName("sidebarSubtitle")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.subtitle_label)

        self.version_label = QLabel("V1.4.0")
        self.version_label.setObjectName("sidebarVersion")
        self.version_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.version_label)

        layout.addWidget(self._header)

        # ========== Separator ==========
        sep = QFrame()
        sep.setObjectName("sidebarSeparator")
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # ========== Expanded Nav Items ==========
        self._nav_container = QWidget()
        self._nav_container.setObjectName("navContainer")
        nav_layout = QVBoxLayout(self._nav_container)
        nav_layout.setSpacing(2)
        nav_layout.setContentsMargins(4, 8, 4, 8)

        for cfg in MENU_CONFIG:
            item_row = QWidget()
            item_row.setObjectName("navItemRow")
            row_layout = QHBoxLayout(item_row)
            row_layout.setSpacing(0)
            row_layout.setContentsMargins(0, 0, 0, 0)

            indicator = _NavIndicator()
            row_layout.addWidget(indicator)
            self._indicators.append(indicator)

            btn = _NavItem(cfg["icon"], cfg["text"], cfg["id"])
            btn.clicked.connect(lambda checked, bid=cfg["id"]: self._on_item_clicked(bid))
            row_layout.addWidget(btn, 1)
            self._nav_items.append(btn)

            nav_layout.addWidget(item_row)

        nav_layout.addStretch()
        layout.addWidget(self._nav_container, 1)

        # ========== Collapsed Icon Nav ==========
        self._icon_container = QWidget()
        self._icon_container.setObjectName("iconContainer")
        icon_layout = QVBoxLayout(self._icon_container)
        icon_layout.setSpacing(4)
        icon_layout.setContentsMargins(10, 12, 10, 12)

        collapsed_title = QLabel("\U0001f30f")
        collapsed_title.setObjectName("sidebarCollapsedTitle")
        collapsed_title.setAlignment(Qt.AlignCenter)
        collapsed_title.setFixedHeight(36)
        icon_layout.addWidget(collapsed_title)

        collapsed_sep = QFrame()
        collapsed_sep.setObjectName("sidebarSeparator")
        collapsed_sep.setFrameShape(QFrame.HLine)
        collapsed_sep.setFixedHeight(1)
        icon_layout.addWidget(collapsed_sep)

        for cfg in MENU_CONFIG:
            btn = QPushButton(cfg["icon"])
            btn.setObjectName("navIconBtn")
            btn.setToolTip(cfg["text"])
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True)
            btn.setFixedSize(48, 48)
            btn.clicked.connect(lambda checked, bid=cfg["id"]: self._on_item_clicked(bid))
            icon_layout.addWidget(btn, 0, Qt.AlignHCenter)
            self._collapsed_btns.append(btn)

        icon_layout.addStretch()
        self._icon_container.hide()
        layout.addWidget(self._icon_container, 1)

        # ========== Bottom ==========
        self._bottom = QWidget()
        self._bottom.setObjectName("sidebarBottom")
        bottom_layout = QVBoxLayout(self._bottom)
        bottom_layout.setContentsMargins(12, 8, 12, 12)
        bottom_layout.setSpacing(8)

        self.theme_btn = QPushButton("\u2699 \u7cfb\u7edf\u53c2\u6570\u914d\u7f6e")
        self.theme_btn.setObjectName("sidebarThemeBtn")
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.setFixedHeight(36)
        self.theme_btn.clicked.connect(self._show_theme_dialog)
        bottom_layout.addWidget(self.theme_btn)

        self.collapse_btn = QPushButton("\u25c0 \u6298\u53e0")
        self.collapse_btn.setObjectName("sidebarCollapseBtn")
        self.collapse_btn.setCursor(Qt.PointingHandCursor)
        self.collapse_btn.setFixedHeight(32)
        self.collapse_btn.clicked.connect(self.toggle_collapse)
        bottom_layout.addWidget(self.collapse_btn)

        layout.addWidget(self._bottom)

        self._on_item_clicked("dashboard")

    def _on_item_clicked(self, item_id: str):
        self._current_item_id = item_id

        for btn in self._nav_items:
            is_active = btn.item_id == item_id
            btn.setChecked(is_active)

        for i, btn in enumerate(self._nav_items):
            if btn.item_id == item_id:
                self._indicators[i].show()
            else:
                self._indicators[i].hide()

        for btn in self._collapsed_btns:
            cfg = MENU_CONFIG[self._collapsed_btns.index(btn)]
            btn.setChecked(cfg["id"] == item_id)

        self.item_selected.emit(item_id)

    def _show_theme_dialog(self):
        from ui.dialogs.system_settings_dialog import SystemSettingsDialog
        dialog = SystemSettingsDialog(self)
        dialog.theme_changed.connect(self.theme_changed.emit)
        dialog.config_changed.connect(lambda: None)
        dialog.exec()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Up, Qt.Key_Down):
            current_idx = next(
                (i for i, c in enumerate(MENU_CONFIG) if c["id"] == self._current_item_id), 0
            )
            if event.key() == Qt.Key_Up:
                new_idx = (current_idx - 1) % len(MENU_CONFIG)
            else:
                new_idx = (current_idx + 1) % len(MENU_CONFIG)
            self._on_item_clicked(MENU_CONFIG[new_idx]["id"])
            event.accept()
        elif event.key() in (Qt.Key_Enter, Qt.Key_Return):
            event.accept()
        else:
            super().keyPressEvent(event)

    @property
    def collapsed(self) -> bool:
        return self._collapsed

    def toggle_collapse(self):
        if self._animating:
            return

        self._collapsed = not self._collapsed
        self._animating = True

        start_w = self.width()
        target_w = WIDTH_COLLAPSED if self._collapsed else WIDTH_EXPANDED

        self._min_anim = QPropertyAnimation(self, b"minimumWidth")
        self._min_anim.setDuration(ANIMATION_DURATION)
        self._min_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._min_anim.setStartValue(start_w)
        self._min_anim.setEndValue(target_w)

        self._max_anim = QPropertyAnimation(self, b"maximumWidth")
        self._max_anim.setDuration(ANIMATION_DURATION)
        self._max_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._max_anim.setStartValue(start_w)
        self._max_anim.setEndValue(target_w)

        self._anim_group = QParallelAnimationGroup()
        self._anim_group.addAnimation(self._min_anim)
        self._anim_group.addAnimation(self._max_anim)

        def on_finished():
            self._animating = False
            self.collapse_toggled.emit(self._collapsed)

        self._anim_group.finished.connect(on_finished)
        self._anim_group.start()

        if self._collapsed:
            self._header.hide()
            self._nav_container.hide()
            self._icon_container.show()
            self.collapse_btn.setText("\u25b6")
            self.collapse_btn.setFixedWidth(48)
            self.theme_btn.setText("\u2699\ufe0f")
            self.theme_btn.setFixedWidth(48)
        else:
            self._header.show()
            self._nav_container.show()
            self._icon_container.hide()
            self.collapse_btn.setText("\u25c0 \u6298\u53e0")
            self.collapse_btn.setFixedWidth(196)
            self.theme_btn.setText("\u2699 \u7cfb\u7edf\u53c2\u6570\u914d\u7f6e")
            self.theme_btn.setFixedWidth(196)

    def select_item(self, item_id: str):
        self._on_item_clicked(item_id)


AntSidebar = ModernSidebar
