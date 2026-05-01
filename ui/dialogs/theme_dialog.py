# -*- coding: utf-8 -*-
"""
主题选择对话框 - 浅色系/暗色系分组选择
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QGraphicsOpacityEffect, QSlider, QWidget
)
from PySide6.QtCore import Signal, Qt, QPropertyAnimation, QEasingCurve, QTimer, QRectF
from PySide6.QtGui import QPalette, QColor, QPainter, QPainterPath, QBrush, QPen, QLinearGradient, QFont

from core.theme_manager import get_theme_manager, ThemeMode, ThemeGroup, THEME_GROUP_MAP, THEME_DISPLAY_NAMES, get_theme_group
from ui.components.theme_preview_card import ThemePreviewCard, THEME_COLORS


class _GroupSelectorCard(QPushButton):
    """主题组选择器卡片 - 带渐变背景的大按钮"""

    clicked_group = Signal(str)

    def __init__(self, group: str, parent=None):
        super().__init__(parent)
        self._group = group
        self._active = False
        self._hover_state = False
        config = THEME_GROUP_MAP[group]
        self._icon = config["icon"]
        self._name = config["name"]
        self._subtitle = config["subtitle"]

        self.setObjectName("groupSelectorCard")
        self.setFixedSize(210, 100)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)

        self.clicked.connect(lambda: self.clicked_group.emit(group))

    def set_active(self, active: bool):
        self._active = active
        self.update()

    def enterEvent(self, event):
        self._hover_state = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover_state = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(0, 0, self.width(), self.height())
        path = QPainterPath()
        path.addRoundedRect(rect.adjusted(1, 1, -1, -1), 16, 16)

        if self._group == ThemeGroup.LIGHT:
            if self._active:
                grad = QLinearGradient(0, 0, 0, self.height())
                grad.setColorAt(0, QColor("#fff3e0"))
                grad.setColorAt(0.4, QColor("#ffe0b2"))
                grad.setColorAt(0.7, QColor("#ffccbc"))
                grad.setColorAt(1, QColor("#ffab91"))
            else:
                grad = QLinearGradient(0, 0, 0, self.height())
                grad.setColorAt(0, QColor("#fdfaf6"))
                grad.setColorAt(0.5, QColor("#faf3eb"))
                grad.setColorAt(1, QColor("#f5e6d8"))
        else:
            if self._active:
                grad = QLinearGradient(0, 0, 0, self.height())
                grad.setColorAt(0, QColor("#1a1a2e"))
                grad.setColorAt(0.4, QColor("#141b3d"))
                grad.setColorAt(0.7, QColor("#0a0e27"))
                grad.setColorAt(1, QColor("#0d1117"))
            else:
                grad = QLinearGradient(0, 0, 0, self.height())
                grad.setColorAt(0, QColor("#1e1f35"))
                grad.setColorAt(0.5, QColor("#1a1c30"))
                grad.setColorAt(1, QColor("#131525"))

        painter.fillPath(path, QBrush(grad))

        if self._active:
            border_color = QColor("#FF7F50") if self._group == ThemeGroup.LIGHT else QColor("#00d4aa")
            painter.setPen(QPen(border_color, 2.5))
            painter.drawPath(path)
        elif self._hover_state:
            painter.setPen(QPen(QColor(180, 180, 180, 100), 1))
            painter.drawPath(path)

        text_color = QColor("#5D4037") if self._group == ThemeGroup.LIGHT else QColor("#e8eaf6")
        subtitle_color = QColor("#8D6E63") if self._group == ThemeGroup.LIGHT else QColor("#7986cb")

        fn_icon = QFont()
        fn_icon.setPointSize(20)
        painter.setFont(fn_icon)
        painter.setPen(QPen(text_color))
        painter.drawText(QRectF(0, 8, self.width(), 32), Qt.AlignCenter, self._icon)

        fn_name = QFont()
        fn_name.setPointSize(12)
        fn_name.setBold(True)
        painter.setFont(fn_name)
        painter.setPen(QPen(text_color))
        painter.drawText(QRectF(0, 38, self.width(), 24), Qt.AlignCenter, self._name)

        fn_sub = QFont()
        fn_sub.setPointSize(9)
        painter.setFont(fn_sub)
        painter.setPen(QPen(subtitle_color))
        painter.drawText(QRectF(0, 62, self.width(), 22), Qt.AlignCenter, self._subtitle)

        painter.end()


class ThemeDialog(QDialog):
    """主题选择对话框 - 浅色系/暗色系分组"""

    theme_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_theme = None
        self._original_theme = None
        self._current_group = ThemeGroup.LIGHT
        self._theme_cards = {}

        self.setWindowTitle("选择主题")
        self.setMinimumSize(940, 420)
        self.setWindowFlags(self.windowFlags() | Qt.Dialog | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)

        self._init_ui()
        self._load_current()

    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(18)
        main_layout.setContentsMargins(24, 24, 24, 24)

        title_label = QLabel("选择主题")
        title_label.setStyleSheet("font-size: 18px; font-weight: 700; border: none; background: transparent;")
        main_layout.addWidget(title_label)

        group_frame = QWidget()
        group_layout = QHBoxLayout(group_frame)
        group_layout.setSpacing(16)
        group_layout.setContentsMargins(0, 0, 0, 0)

        self.light_card = _GroupSelectorCard(ThemeGroup.LIGHT)
        self.dark_card = _GroupSelectorCard(ThemeGroup.DARK)

        self.light_card.clicked_group.connect(self._on_group_selected)
        self.dark_card.clicked_group.connect(self._on_group_selected)

        group_layout.addStretch()
        group_layout.addWidget(self.light_card)
        group_layout.addWidget(self.dark_card)
        group_layout.addStretch()

        main_layout.addWidget(group_frame)

        self.subthemes_container = QWidget()
        self.subthemes_layout = QHBoxLayout(self.subthemes_container)
        self.subthemes_layout.setSpacing(14)
        self.subthemes_layout.setContentsMargins(0, 4, 0, 0)
        self.subthemes_layout.addStretch()
        main_layout.addWidget(self.subthemes_container)

        self.opacity_frame = QFrame()
        opacity_layout = QHBoxLayout(self.opacity_frame)
        opacity_layout.setContentsMargins(0, 0, 0, 0)
        opacity_layout.setSpacing(12)

        opacity_label = QLabel("透明度")
        opacity_label.setStyleSheet("font-size: 13px; font-weight: 500; border: none; background: transparent;")
        opacity_layout.addWidget(opacity_label)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(10)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setSingleStep(5)
        self.opacity_slider.setPageStep(10)
        tm = get_theme_manager()
        slider_val = int(tm.glass_opacity * 100)
        self.opacity_slider.setValue(min(100, max(10, slider_val)))
        self.opacity_slider.setFixedWidth(180)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        opacity_layout.addWidget(self.opacity_slider)

        display_pct = min(100, max(10, slider_val))
        self.opacity_value_label = QLabel(f"{display_pct}%")
        self.opacity_value_label.setStyleSheet("font-size: 13px; font-weight: 500; border: none; background: transparent; min-width: 40px;")
        opacity_layout.addWidget(self.opacity_value_label)
        opacity_layout.addStretch()
        main_layout.addWidget(self.opacity_frame)
        self.opacity_frame.hide()

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background: rgba(128,128,128,0.15); max-height: 1px;")
        main_layout.addWidget(separator)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.close_btn = QPushButton("关闭")
        self.close_btn.setObjectName("cancelBtn")
        self.close_btn.setMinimumWidth(100)
        self.close_btn.clicked.connect(self.accept)

        btn_layout.addWidget(self.close_btn)

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

        self._apply_dialog_theme()

    def _load_current(self):
        theme_manager = get_theme_manager()
        current_mode = theme_manager.mode
        self._original_theme = current_mode
        self._selected_theme = current_mode

        group = get_theme_group(current_mode) or ThemeGroup.LIGHT
        self._current_group = group
        self.light_card.set_active(group == ThemeGroup.LIGHT)
        self.dark_card.set_active(group == ThemeGroup.DARK)

        self._populate_subthemes(group)

        if current_mode in self._theme_cards:
            self._theme_cards[current_mode].set_selected(True)

        self._update_opacity_visibility()

    def _on_group_selected(self, group: str):
        if self._current_group == group:
            return

        self._current_group = group
        self.light_card.set_active(group == ThemeGroup.LIGHT)
        self.dark_card.set_active(group == ThemeGroup.DARK)

        group_themes = THEME_GROUP_MAP[group]["modes"]
        if group_themes:
            self._selected_theme = group_themes[0]
        else:
            self._selected_theme = None

        self._animate_subthemes_switch(group)

    def _populate_subthemes(self, group: str):
        for card in list(self._theme_cards.values()):
            card.setParent(None)
            card.deleteLater()
        self._theme_cards.clear()

        while self.subthemes_layout.count():
            item = self.subthemes_layout.takeAt(0)
            if item.widget():
                item.widget().hide()

        self.subthemes_layout.addStretch()

        group_themes = THEME_GROUP_MAP[group]["modes"]
        for mode in group_themes:
            card = ThemePreviewCard(mode)
            card.clicked.connect(self._on_theme_clicked)
            self._theme_cards[mode] = card
            self.subthemes_layout.addWidget(card)

        self.subthemes_layout.addStretch()

    def _animate_subthemes_switch(self, group: str):
        for mode, card in list(self._theme_cards.items()):
            effect = QGraphicsOpacityEffect(card)
            card.setGraphicsEffect(effect)
            effect.setOpacity(1.0)

            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(100)
            anim.setStartValue(1.0)
            anim.setEndValue(0.0)
            anim.setEasingCurve(QEasingCurve.InCubic)
            anim.start(QPropertyAnimation.DeleteWhenStopped)
            card._fade_anim = anim

        def on_fade_done():
            self._populate_subthemes(group)

            if self._selected_theme and self._selected_theme in self._theme_cards:
                self._theme_cards[self._selected_theme].set_selected(True)

            self._update_opacity_visibility()

            for i, (mode, card) in enumerate(self._theme_cards.items()):
                effect = QGraphicsOpacityEffect(card)
                card.setGraphicsEffect(effect)
                effect.setOpacity(0.0)

                anim = QPropertyAnimation(effect, b"opacity")
                anim.setDuration(180)
                anim.setStartValue(0.0)
                anim.setEndValue(1.0)
                anim.setEasingCurve(QEasingCurve.OutCubic)

                def cleanup(eff=effect, c=card):
                    if c.graphicsEffect() is eff:
                        c.setGraphicsEffect(None)

                anim.finished.connect(cleanup)
                QTimer.singleShot(i * 40, anim.start)
                card._fade_in_anim = anim

        QTimer.singleShot(120, on_fade_done)

    def _on_theme_clicked(self, theme_mode: str):
        for mode, card in self._theme_cards.items():
            card.set_selected(False)

        if theme_mode in self._theme_cards:
            self._theme_cards[theme_mode].set_selected(True)
            self._selected_theme = theme_mode

        self._update_opacity_visibility()

        theme_manager = get_theme_manager()
        theme_manager.set_mode(self._selected_theme)

    def _update_opacity_visibility(self):
        is_glass = self._selected_theme == ThemeMode.GLASS
        self.opacity_frame.setVisible(is_glass)

    def _on_opacity_changed(self, value: int):
        self.opacity_value_label.setText(f"{value}%")
        opacity = value / 100.0
        theme_manager = get_theme_manager()
        theme_manager.set_glass_opacity(opacity)

    def get_selected_theme(self) -> str:
        return self._selected_theme

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, '_animated'):
            self._animated = True
            self._animate_entrance()

    def _animate_entrance(self):
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        effect.setOpacity(0.0)

        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(200)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(lambda: self.setGraphicsEffect(None))
        anim.start()
        self._entrance_anim = anim

    def _apply_dialog_theme(self):
        theme_manager = get_theme_manager()
        theme = theme_manager.get_current_theme()

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(theme.get('content_bg', '#f0f2f5')))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        self.setStyleSheet(theme_manager.get_stylesheet())
