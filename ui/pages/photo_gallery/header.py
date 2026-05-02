# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from core.theme_manager import get_theme_manager


class GalleryHeader(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("pageHeader")
        self.theme_manager = get_theme_manager()
        self._init_ui()

    def _init_ui(self):
        theme = self.theme_manager.get_current_theme()
        accent = theme.get('accent_color', '#6366f1')

        layout = QHBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 16, 20, 16)

        accent_bar = QFrame()
        accent_bar.setObjectName("accentBar")
        accent_bar.setFixedWidth(4)
        accent_bar.setMinimumHeight(20)
        layout.addWidget(accent_bar)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        page_title = QLabel("照片检查")
        page_title.setObjectName("sectionHeaderLg")
        title_layout.addWidget(page_title)
        page_subtitle = QLabel("扫描文件夹，管理照片和视频文件")
        page_subtitle.setObjectName("pageSubtitle")
        title_layout.addWidget(page_subtitle)
        layout.addLayout(title_layout, 1)

        self.badge_photos = self._create_badge("照片", "--", accent)
        layout.addWidget(self.badge_photos)
        layout.addWidget(self._create_separator())

        self.badge_videos = self._create_badge("视频", "--", theme.get('info_text', '#8b5cf6'))
        layout.addWidget(self.badge_videos)
        layout.addWidget(self._create_separator())

        self.badge_size = self._create_badge("大小", "--", theme.get('warning_text', '#f59e0b'))
        layout.addWidget(self.badge_size)

    def update_stats(self, photos: str, videos: str, size: str):
        self.badge_photos._value_label.setText(photos)
        self.badge_videos._value_label.setText(videos)
        self.badge_size._value_label.setText(size)

    def reset_stats(self):
        self.badge_photos._value_label.setText("--")
        self.badge_videos._value_label.setText("--")
        self.badge_size._value_label.setText("--")

    def update_theme_colors(self):
        theme = self.theme_manager.get_current_theme()
        accent = theme.get('accent_color', '#6366f1')
        self._update_badge_color(self.badge_photos, accent)
        self._update_badge_color(self.badge_videos, theme.get('info_text', '#8b5cf6'))
        self._update_badge_color(self.badge_size, theme.get('warning_text', '#f59e0b'))

    def _update_badge_color(self, badge: QFrame, color: str):
        if hasattr(badge, '_value_label'):
            badge._value_label.setStyleSheet(f"color: {color}; font-weight: 700; font-size: 14px;")
        if hasattr(badge, '_label_label'):
            badge._label_label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 500;")

    def _create_badge(self, label: str, value: str, color: str) -> QFrame:
        theme = self.theme_manager.get_current_theme()
        badge = QFrame()
        badge.setStyleSheet("QFrame { background: transparent; border: none; }")
        badge_layout = QHBoxLayout(badge)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        badge_layout.setSpacing(4)

        val = QLabel(value)
        val.setStyleSheet(f"color: {color}; font-weight: 700; font-size: 16px;")
        badge_layout.addWidget(val)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {theme.get('text_secondary', '#64748b')}; font-size: 13px;")
        badge_layout.addWidget(lbl)

        badge._value_label = val
        badge._label_label = lbl
        return badge

    def _create_separator(self) -> QFrame:
        theme = self.theme_manager.get_current_theme()
        sep = QFrame()
        sep.setStyleSheet(f"background: {theme.get('divider_color', '#e2e8f0')}; margin: 0 8px;")
        sep.setFixedWidth(1)
        sep.setFixedHeight(16)
        return sep
