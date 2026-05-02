# -*- coding: utf-8 -*-
"""
图片卡片组件 - 嵌入在树节点下方

职责:
- 图片缩略图加载与显示
- 选中/取消选中交互
- 缩放适配
- GPS标识显示
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QToolButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage

from core.theme_manager import get_theme_manager

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


class PhotoCard(QFrame):

    clicked = Signal(str)
    selection_changed = Signal(str, bool)

    BASE_SIZE = 240
    THUMB_LOAD_SIZE = 480
    ZOOM_SCALES = [0.5, 0.6, 0.7, 0.85, 1.0, 1.15, 1.3, 1.5, 1.75, 2.0]
    _current_scale = 1.0

    def __init__(self, file_info: dict, accent_color: str = '#6366f1', parent=None):
        super().__init__(parent)
        self.file_info = file_info
        self.file_path = file_info['path']
        self._selected = False
        self._accent = accent_color
        self._original_pixmap = None
        self._theme_manager = get_theme_manager()

        self.setObjectName("photoCard")
        self.setCursor(Qt.PointingHandCursor)

        self._apply_scale(PhotoCard._current_scale)
        self._init_ui()
        self._load_thumbnail()

    def _apply_scale(self, scale):
        theme = self._theme_manager.get_current_theme()
        base = max(60, int(PhotoCard.BASE_SIZE * scale))
        self.setMinimumSize(base, base)
        self.setMaximumSize(base, base)
        card_bg = theme.get('photo_card_bg', theme.get('card_bg', '#ffffff'))
        card_border = theme.get('photo_card_border', theme.get('card_border', '#e5e7eb'))
        hover_border = theme.get('photo_card_hover_border', theme.get('accent_color', '#6366f1'))
        hover_bg = theme.get('surface_1', theme.get('content_bg', '#f8fafc'))
        self.setStyleSheet(f"""
            QFrame#photoCard {{
                background: {card_bg};
                border: 2px solid {card_border};
                border-radius: 8px; padding: 0;
            }}
            QFrame#photoCard:hover {{
                border-color: {hover_border};
                background: {hover_bg};
            }}
        """)

    def _init_ui(self):
        theme = self._theme_manager.get_current_theme()
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        base = max(60, int(PhotoCard.BASE_SIZE * PhotoCard._current_scale))

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(base, base)
        self.image_label.setMaximumSize(base, base)
        self.image_label.setContentsMargins(0, 0, 0, 0)
        self.image_label.setStyleSheet("margin: 0; padding: 0;")
        layout.addWidget(self.image_label, 1)

        self.info_bar = QFrame()
        self.info_bar.setObjectName("photoOverlayBar")
        overlay_bg = theme.get('overlay_bg', 'rgba(0,0,0,0.6)')
        self.info_bar.setStyleSheet(f"""
            QFrame#photoOverlayBar {{
                background: {overlay_bg};
                border-radius: 0 0 6px 6px;
            }}
        """)
        info_layout = QHBoxLayout(self.info_bar)
        info_layout.setContentsMargins(6, 3, 6, 3)
        info_layout.setSpacing(4)

        self.name_label = QLabel(self.file_info['name'])
        self.name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        overlay_text = theme.get('tab_selected_text', '#ffffff')
        self.name_label.setStyleSheet(f"""
            font-size: 10px; color: {overlay_text};
            background: transparent;
        """)
        info_layout.addWidget(self.name_label, 1)

        self.info_bar.setParent(self)
        self.info_bar.setGeometry(0, base - 22, base, 22)

        self.select_btn = QToolButton()
        self.select_btn.setFixedSize(18, 18)
        self.select_btn.setCheckable(True)
        self.select_btn.clicked.connect(self._on_select_clicked)
        self._update_select_btn_style()
        self.select_btn.setParent(self)
        self.select_btn.move(base - 20, 4)

        if self.file_info['has_gps']:
            success_color = theme.get('success_color', theme.get('success_text', '#10b981'))
            success_bg = theme.get('success_bg', 'rgba(16,185,129,0.9)')
            self.gps_label = QLabel("📍")
            self.gps_label.setStyleSheet(f"""
                color: {success_color};
                font-size: 12px;
                background: {success_bg};
                border-radius: 4px;
                padding: 1px 3px;
            """)
            self.gps_label.setAlignment(Qt.AlignCenter)
            self.gps_label.setParent(self)
            self.gps_label.move(4, 4)
        else:
            self.gps_label = None

    def _load_thumbnail(self):
        if HAS_PILLOW and self.file_info['type'] == 'photo':
            try:
                with Image.open(self.file_path) as img:
                    img.load()
                    img.thumbnail((PhotoCard.THUMB_LOAD_SIZE, PhotoCard.THUMB_LOAD_SIZE), Image.LANCZOS)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    data = img.tobytes('raw', 'RGB')
                    qimg = QImage(data, img.width, img.height, img.width * 3, QImage.Format_RGB888).copy()
                    self._original_pixmap = QPixmap.fromImage(qimg)
                self._update_thumbnail_display()
                self._update_overlay_positions()
                return
            except Exception:
                pass

        icon = "🎬" if self.file_info['type'] == 'video' else "📷"
        theme = self._theme_manager.get_current_theme()
        base = max(60, int(PhotoCard.BASE_SIZE * PhotoCard._current_scale))
        self.image_label.setText(icon)
        self.image_label.setMinimumSize(base, base)
        self.image_label.setMaximumSize(base, base)
        self.image_label.setStyleSheet(f"""
            font-size: 32px;
            color: {theme.get('text_muted', '#94a3b8')};
            min-width: {base}px;
            min-height: {base}px;
        """)
        self._update_overlay_positions()

    def _update_thumbnail_display(self):
        if self._original_pixmap:
            base = max(60, int(PhotoCard.BASE_SIZE * PhotoCard._current_scale))
            scaled = self._original_pixmap.scaled(
                base, base,
                Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            if scaled.width() > base or scaled.height() > base:
                x = (scaled.width() - base) // 2
                y = (scaled.height() - base) // 2
                scaled = scaled.copy(x, y, base, base)
            self.image_label.setPixmap(scaled)

    def update_zoom(self, scale):
        self._apply_scale(scale)
        base = max(60, int(PhotoCard.BASE_SIZE * scale))
        self.image_label.setMinimumSize(base, base)
        self.image_label.setMaximumSize(base, base)
        self._update_thumbnail_display()
        self._update_overlay_positions()

    def _update_overlay_positions(self):
        w = self.width()
        h = self.height()
        self.info_bar.setGeometry(0, h - 22, w, 22)
        self.select_btn.move(w - 20, 4)
        if self.gps_label:
            self.gps_label.move(4, 4)

    def _on_select_clicked(self):
        self._selected = self.select_btn.isChecked()
        self._update_select_btn_style()
        self.selection_changed.emit(self.file_path, self._selected)

    def _update_select_btn_style(self):
        theme = self._theme_manager.get_current_theme()
        accent = theme.get('accent_color', '#6366f1')
        btn_text_on_accent = theme.get('btn_primary_hover_text', '#ffffff')
        glass_bg = theme.get('glass_bg', 'rgba(255,255,255,0.7)')
        glass_border = theme.get('glass_border', 'rgba(255,255,255,0.3)')
        if self._selected:
            self.select_btn.setStyleSheet(f"""
                background: {accent};
                border-radius: 5px;
                margin: 0; padding: 0;
                border: none;
                color: {btn_text_on_accent};
                font-size: 11px;
                font-weight: bold;
            """)
            self.select_btn.setText("✓")
        else:
            card_bg = theme.get('photo_card_bg', theme.get('card_bg', '#ffffff'))
            self.select_btn.setStyleSheet(f"""
                background: {glass_bg};
                border-radius: 5px;
                margin: 0; padding: 0;
                border: 1px solid {glass_border};
                color: {theme.get('text_muted', '#64748b')};
            """)
            self.select_btn.setText("")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.select_btn.geometry().contains(event.pos()):
            self.clicked.emit(self.file_path)

    def set_selected(self, selected: bool):
        self._selected = selected
        self.select_btn.setChecked(selected)
        self._update_select_btn_style()

    def is_selected(self) -> bool:
        return self._selected
