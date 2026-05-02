# -*- coding: utf-8 -*-
"""
图片预览对话框 - 全屏预览图片/GIF/视频
"""

import os
from datetime import datetime
from enum import Enum

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame,
    QGraphicsOpacityEffect, QStackedWidget, QWidget, QScrollArea,
    QSizePolicy
)
from PySide6.QtCore import (
    Signal, Qt, QPropertyAnimation, QEasingCurve, QTimer, QUrl,
    QSize, QEvent, QPoint
)
from PySide6.QtGui import (
    QPixmap, QImage, QPalette, QColor, QKeyEvent, QMouseEvent,
    QMovie, QWheelEvent
)
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget

from core.theme_manager import get_theme_manager

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.tif'}
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}

ZOOM_MIN = 0.05
ZOOM_MAX = 10.0
ZOOM_STEP = 1.25
ZOOM_SNAP_THRESH = 0.02


class DisplayMode(Enum):
    FIT = "fit"
    FILL = "fill"
    ORIGINAL = "original"


DISPLAY_MODE_LABELS = {
    DisplayMode.FIT: "适应屏幕",
    DisplayMode.FILL: "铺满全屏",
    DisplayMode.ORIGINAL: "1:1",
}

DISPLAY_MODE_ORDER = [DisplayMode.FIT, DisplayMode.FILL, DisplayMode.ORIGINAL]


class PhotoPreviewDialog(QDialog):
    """图片预览对话框 - 支持图片、GIF动画、视频播放"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._files = []
        self._current_index = -1
        self._current_movie = None
        self._media_player = None
        self._audio_output = None
        self._display_mode = DisplayMode.FIT
        self._current_pixmap = None
        self._zoom_factor = 1.0
        self._dragging = False
        self._drag_start_pos = QPoint()
        self._drag_start_h_val = 0
        self._drag_start_v_val = 0

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        self._init_ui()
        self._apply_theme_style()

    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.bg_frame = QFrame()
        self.bg_frame.setObjectName("photoPreviewBg")
        bg_layout = QVBoxLayout()
        bg_layout.setSpacing(0)
        bg_layout.setContentsMargins(0, 0, 0, 0)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(16, 8, 16, 8)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(6)

        self.mode_btn_fit = QPushButton("适应屏幕")
        self.mode_btn_fit.setObjectName("photoPreviewModeBtn")
        self.mode_btn_fit.setCheckable(True)
        self.mode_btn_fit.setChecked(True)
        self.mode_btn_fit.setFixedHeight(32)
        self.mode_btn_fit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mode_btn_fit.setToolTip("适应屏幕 (1)")
        self.mode_btn_fit.clicked.connect(lambda: self._set_display_mode(DisplayMode.FIT))
        top_layout.addWidget(self.mode_btn_fit)

        self.mode_btn_fill = QPushButton("铺满全屏")
        self.mode_btn_fill.setObjectName("photoPreviewModeBtn")
        self.mode_btn_fill.setCheckable(True)
        self.mode_btn_fill.setChecked(False)
        self.mode_btn_fill.setFixedHeight(32)
        self.mode_btn_fill.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mode_btn_fill.setToolTip("铺满全屏 (2)")
        self.mode_btn_fill.clicked.connect(lambda: self._set_display_mode(DisplayMode.FILL))
        top_layout.addWidget(self.mode_btn_fill)

        self.mode_btn_original = QPushButton("1:1")
        self.mode_btn_original.setObjectName("photoPreviewModeBtn")
        self.mode_btn_original.setCheckable(True)
        self.mode_btn_original.setChecked(False)
        self.mode_btn_original.setFixedHeight(32)
        self.mode_btn_original.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mode_btn_original.setToolTip("原始大小 (3)")
        self.mode_btn_original.clicked.connect(lambda: self._set_display_mode(DisplayMode.ORIGINAL))
        top_layout.addWidget(self.mode_btn_original)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setObjectName("photoPreviewZoomLabel")
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_label.setFixedWidth(56)
        top_layout.addWidget(self.zoom_label)

        top_layout.addStretch()

        self.counter_label = QLabel()
        self.counter_label.setObjectName("photoPreviewCounter")
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(self.counter_label)

        top_layout.addStretch()

        self.close_btn = QPushButton("×")
        self.close_btn.setObjectName("photoPreviewCloseBtn")
        self.close_btn.setFixedSize(40, 40)
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        top_layout.addWidget(self.close_btn)

        content_layout.addLayout(top_layout)

        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(8)

        self.left_btn = QPushButton("‹")
        self.left_btn.setObjectName("photoPreviewNavBtn")
        self.left_btn.setFixedSize(48, 48)
        self.left_btn.clicked.connect(self.prev)
        self.left_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.left_btn.setToolTip("上一张 (←)")
        middle_layout.addWidget(self.left_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        self.image_scroll = QScrollArea()
        self.image_scroll.setObjectName("photoPreviewScroll")
        self.image_scroll.setWidgetResizable(True)
        self.image_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.image_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.content_stack = QStackedWidget()

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(False)
        self.image_label.setMinimumSize(1, 1)
        self.image_scroll.setWidget(self.image_label)
        self.image_scroll.viewport().installEventFilter(self)
        self.content_stack.addWidget(self.image_scroll)

        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(1, 1)
        self.content_stack.addWidget(self.video_widget)

        middle_layout.addWidget(self.content_stack, 1)

        self.right_btn = QPushButton("›")
        self.right_btn.setObjectName("photoPreviewNavBtn")
        self.right_btn.setFixedSize(48, 48)
        self.right_btn.clicked.connect(self.next)
        self.right_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.right_btn.setToolTip("下一张 (→)")
        middle_layout.addWidget(self.right_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        content_layout.addLayout(middle_layout, 1)

        self.info_frame = QFrame()
        self.info_frame.setObjectName("photoPreviewInfoFrame")
        info_layout = QHBoxLayout()
        info_layout.setSpacing(16)
        info_layout.setContentsMargins(12, 6, 12, 6)

        self.name_label = QLabel()
        self.name_label.setObjectName("photoPreviewName")
        info_layout.addWidget(self.name_label)

        self.path_label = QLabel()
        self.path_label.setObjectName("photoPreviewPath")
        info_layout.addWidget(self.path_label, 1)

        self.attrs_label = QLabel()
        self.attrs_label.setObjectName("photoPreviewAttrs")
        info_layout.addWidget(self.attrs_label)

        self.info_frame.setLayout(info_layout)
        content_layout.addWidget(self.info_frame)

        bg_layout.addLayout(content_layout)
        self.bg_frame.setLayout(bg_layout)
        main_layout.addWidget(self.bg_frame)

        self.setLayout(main_layout)

    def _calc_base_zoom(self) -> float:
        if not self._current_pixmap or self._current_pixmap.isNull():
            return 1.0
        available = self._get_available_size()
        img_w = self._current_pixmap.width()
        img_h = self._current_pixmap.height()
        if img_w <= 0 or img_h <= 0:
            return 1.0
        if self._display_mode == DisplayMode.FIT:
            return min(available.width() / img_w, available.height() / img_h)
        elif self._display_mode == DisplayMode.FILL:
            return max(available.width() / img_w, available.height() / img_h)
        else:
            return 1.0

    def _set_display_mode(self, mode: DisplayMode):
        self._display_mode = mode
        self.mode_btn_fit.setChecked(mode == DisplayMode.FIT)
        self.mode_btn_fill.setChecked(mode == DisplayMode.FILL)
        self.mode_btn_original.setChecked(mode == DisplayMode.ORIGINAL)
        self._zoom_factor = self._calc_base_zoom()
        self._apply_current_zoom()

    def _cycle_display_mode(self):
        idx = DISPLAY_MODE_ORDER.index(self._display_mode)
        next_idx = (idx + 1) % len(DISPLAY_MODE_ORDER)
        self._set_display_mode(DISPLAY_MODE_ORDER[next_idx])

    def _apply_current_zoom(self):
        if not self._current_pixmap or self._current_pixmap.isNull():
            self._update_zoom_label()
            return

        zoom = self._zoom_factor
        img_w = self._current_pixmap.width()
        img_h = self._current_pixmap.height()
        display_w = max(1, int(img_w * zoom))
        display_h = max(1, int(img_h * zoom))

        scaled = self._current_pixmap.scaled(
            display_w, display_h,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)
        self.image_scroll.setWidgetResizable(False)
        self.image_label.setFixedSize(display_w, display_h)
        self._update_zoom_label()
        self._update_pan_cursor()

    def _update_zoom_label(self):
        pct = int(self._zoom_factor * 100)
        self.zoom_label.setText(f"{pct}%")

    def eventFilter(self, obj, event):
        if obj == self.image_scroll.viewport():
            et = event.type()
            if et == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    self._start_drag(event.position().toPoint())
            elif et == QEvent.Type.MouseMove:
                if self._dragging and event.buttons() & Qt.MouseButton.LeftButton:
                    self._do_drag(event.position().toPoint())
            elif et == QEvent.Type.MouseButtonRelease:
                if event.button() == Qt.MouseButton.LeftButton and self._dragging:
                    self._end_drag()
            elif et == QEvent.Type.MouseButtonDblClick:
                if event.button() == Qt.MouseButton.LeftButton:
                    self._end_drag()
                    if self.content_stack.currentWidget() == self.image_scroll:
                        self._set_display_mode(self._display_mode)
        return super().eventFilter(obj, event)

    def _start_drag(self, pos):
        if self.content_stack.currentWidget() != self.image_scroll:
            return
        self._dragging = True
        self._drag_start_pos = pos
        self._drag_start_h_val = self.image_scroll.horizontalScrollBar().value()
        self._drag_start_v_val = self.image_scroll.verticalScrollBar().value()
        self.image_scroll.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)

    def _do_drag(self, pos):
        delta = pos - self._drag_start_pos
        h_bar = self.image_scroll.horizontalScrollBar()
        v_bar = self.image_scroll.verticalScrollBar()
        h_bar.setValue(self._drag_start_h_val - delta.x())
        v_bar.setValue(self._drag_start_v_val - delta.y())

    def _end_drag(self):
        self._dragging = False
        self._update_pan_cursor()

    def _update_pan_cursor(self):
        QTimer.singleShot(0, self._do_update_pan_cursor)

    def _do_update_pan_cursor(self):
        if self._dragging:
            return
        viewport = self.image_scroll.viewport()
        label_size = self.image_label.size()
        vp_size = viewport.size()
        can_pan = label_size.width() > vp_size.width() or label_size.height() > vp_size.height()
        viewport.setCursor(
            Qt.CursorShape.OpenHandCursor if can_pan else Qt.CursorShape.ArrowCursor
        )

    def _zoom_at_point(self, delta: float, pos: QPoint):
        if not self._current_pixmap or self._current_pixmap.isNull():
            return
        if self.content_stack.currentWidget() != self.image_scroll:
            return

        old_zoom = self._zoom_factor
        if delta > 0:
            new_zoom = old_zoom * ZOOM_STEP
        else:
            new_zoom = old_zoom / ZOOM_STEP

        new_zoom = max(ZOOM_MIN, min(ZOOM_MAX, new_zoom))
        if abs(new_zoom - old_zoom) < 0.001:
            return

        viewport = self.image_scroll.viewport()
        mouse_pos = viewport.mapFromGlobal(pos)

        h_bar = self.image_scroll.horizontalScrollBar()
        v_bar = self.image_scroll.verticalScrollBar()

        old_h_val = h_bar.value()
        old_v_val = v_bar.value()

        self._zoom_factor = new_zoom
        self._apply_current_zoom()

        ratio = new_zoom / old_zoom
        new_h = int((old_h_val + mouse_pos.x()) * ratio - mouse_pos.x())
        new_v = int((old_v_val + mouse_pos.y()) * ratio - mouse_pos.y())

        h_bar.setValue(new_h)
        v_bar.setValue(new_v)

    def _zoom_step(self, direction: int):
        if not self._current_pixmap or self._current_pixmap.isNull():
            return
        old_zoom = self._zoom_factor
        if direction > 0:
            new_zoom = old_zoom * ZOOM_STEP
        else:
            new_zoom = old_zoom / ZOOM_STEP
        new_zoom = max(ZOOM_MIN, min(ZOOM_MAX, new_zoom))
        if abs(new_zoom - old_zoom) < 0.001:
            return
        self._zoom_factor = new_zoom
        self._apply_current_zoom()
        self._center_scroll()

    def _center_scroll(self):
        h_bar = self.image_scroll.horizontalScrollBar()
        v_bar = self.image_scroll.verticalScrollBar()
        h_bar.setValue((h_bar.maximum() + h_bar.minimum()) // 2)
        v_bar.setValue((v_bar.maximum() + v_bar.minimum()) // 2)

    def _refresh_current_image(self):
        if self._current_index < 0 or not self._files:
            return
        file_path = self._files[self._current_index]
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.gif' and self._current_movie:
            scaled_size = self._get_scaled_size_for_zoom()
            self._current_movie.setScaledSize(scaled_size)
            self.image_label.setFixedSize(scaled_size)
            self.image_scroll.setWidgetResizable(False)
            self._update_pan_cursor()
        elif ext in IMAGE_EXTENSIONS:
            if self._current_pixmap and not self._current_pixmap.isNull():
                self._apply_current_zoom()

    def _get_scaled_size_for_zoom(self) -> QSize:
        if not self._current_pixmap or self._current_pixmap.isNull():
            return self._get_available_size()
        w = max(1, int(self._current_pixmap.width() * self._zoom_factor))
        h = max(1, int(self._current_pixmap.height() * self._zoom_factor))
        return QSize(w, h)

    def _apply_theme_style(self):
        theme_manager = get_theme_manager()

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(20, 20, 22))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        self.setStyleSheet("""
            QFrame#photoPreviewBg {
                background-color: rgba(20, 20, 22, 240);
            }
            QScrollArea#photoPreviewScroll {
                background: transparent;
                border: none;
            }
            QPushButton#photoPreviewCloseBtn {
                background-color: rgba(255, 255, 255, 30);
                color: rgba(255, 255, 255, 200);
                border: none;
                border-radius: 20px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton#photoPreviewCloseBtn:hover {
                background-color: rgba(255, 100, 100, 180);
                color: white;
            }
            QPushButton#photoPreviewNavBtn {
                background-color: rgba(255, 255, 255, 30);
                color: rgba(255, 255, 255, 200);
                border: none;
                border-radius: 24px;
                font-size: 28px;
                font-weight: bold;
            }
            QPushButton#photoPreviewNavBtn:hover {
                background-color: rgba(255, 255, 255, 80);
                color: white;
            }
            QPushButton#photoPreviewNavBtn:disabled {
                background-color: rgba(255, 255, 255, 10);
                color: rgba(255, 255, 255, 50);
            }
            QPushButton#photoPreviewModeBtn {
                background-color: rgba(255, 255, 255, 20);
                color: rgba(255, 255, 255, 160);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 6px;
                font-size: 12px;
                padding: 2px 10px;
            }
            QPushButton#photoPreviewModeBtn:hover {
                background-color: rgba(255, 255, 255, 40);
                color: rgba(255, 255, 255, 220);
            }
            QPushButton#photoPreviewModeBtn:checked {
                background-color: rgba(99, 102, 241, 160);
                color: white;
                border-color: rgba(99, 102, 241, 200);
            }
            QLabel#photoPreviewZoomLabel {
                color: rgba(255, 255, 255, 180);
                font-size: 12px;
                font-weight: bold;
                background-color: rgba(255, 255, 255, 15);
                border-radius: 4px;
                padding: 2px 4px;
            }
            QFrame#photoPreviewInfoFrame {
                background-color: rgba(0, 0, 0, 100);
                border-radius: 6px;
            }
            QLabel#photoPreviewName {
                color: white;
                font-size: 13px;
                font-weight: bold;
            }
            QLabel#photoPreviewPath {
                color: rgba(255, 255, 255, 130);
                font-size: 11px;
            }
            QLabel#photoPreviewAttrs {
                color: rgba(255, 255, 255, 110);
                font-size: 11px;
            }
            QLabel#photoPreviewCounter {
                color: rgba(255, 255, 255, 150);
                font-size: 12px;
                padding: 2px 8px;
            }
            QVideoWidget {
                background-color: black;
            }
        """)

    def set_files(self, files: list, current_index: int = 0):
        self._files = files if files else []
        self._current_index = max(0, min(current_index, len(self._files) - 1)) if self._files else -1
        self._load_current()

    def next(self):
        if not self._files or self._current_index >= len(self._files) - 1:
            return
        self._current_index += 1
        self._load_current()

    def prev(self):
        if not self._files or self._current_index <= 0:
            return
        self._current_index -= 1
        self._load_current()

    def _load_current(self):
        self._cleanup_current()

        if not self._files or self._current_index < 0 or self._current_index >= len(self._files):
            self._show_empty()
            return

        file_path = self._files[self._current_index]
        if not os.path.exists(file_path):
            self._show_error(file_path, "文件不存在")
            return

        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.gif':
            self._load_gif(file_path)
        elif ext in VIDEO_EXTENSIONS:
            self._load_video(file_path)
        elif ext in IMAGE_EXTENSIONS:
            self._load_image(file_path)
        else:
            self._show_error(file_path, "不支持的文件格式")

        self._update_info(file_path)
        self._update_nav_buttons()
        self._update_counter()

    def _load_image(self, file_path: str):
        self.content_stack.setCurrentWidget(self.image_scroll)

        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            self._show_error(file_path, "无法加载图片")
            return

        self._current_pixmap = pixmap
        self._zoom_factor = self._calc_base_zoom()
        self._apply_current_zoom()

    def _load_gif(self, file_path: str):
        self.content_stack.setCurrentWidget(self.image_scroll)

        self._current_movie = QMovie(file_path)
        self._zoom_factor = self._calc_base_zoom()
        scaled_size = self._get_scaled_size_for_zoom()
        self._current_movie.setScaledSize(scaled_size)

        self.image_label.setMovie(self._current_movie)
        self.image_label.setFixedSize(scaled_size)
        self.image_scroll.setWidgetResizable(False)
        self._current_movie.start()
        self._update_zoom_label()
        self._update_pan_cursor()

    def _load_video(self, file_path: str):
        self.content_stack.setCurrentWidget(self.video_widget)

        if self._media_player is None:
            self._media_player = QMediaPlayer()
            self._audio_output = None

        self._media_player.setSource(QUrl.fromLocalFile(file_path))
        self._media_player.setVideoOutput(self.video_widget)
        self._media_player.play()

    def _scale_pixmap(self, pixmap: QPixmap) -> QPixmap:
        if pixmap.isNull():
            return pixmap

        available_size = self._get_available_size()
        if available_size.width() <= 0 or available_size.height() <= 0:
            return pixmap

        mode = self._display_mode
        if mode == DisplayMode.FIT:
            if pixmap.width() > available_size.width() or pixmap.height() > available_size.height():
                return pixmap.scaled(
                    available_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            return pixmap
        elif mode == DisplayMode.FILL:
            return pixmap.scaled(
                available_size,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
        return pixmap

    def _get_available_size(self) -> QSize:
        margin_h = 48
        top_h = 48
        info_h = 40
        nav_w = 64
        return QSize(
            max(100, self.width() - margin_h * 2 - nav_w),
            max(100, self.height() - top_h - info_h - margin_h)
        )

    def _cleanup_current(self):
        if self._current_movie:
            self._current_movie.stop()
            self._current_movie.deleteLater()
            self._current_movie = None

        self.image_label.clear()
        self.image_label.setPixmap(QPixmap())
        self._current_pixmap = None
        self.image_scroll.viewport().setCursor(Qt.CursorShape.ArrowCursor)

        if self._media_player:
            self._media_player.stop()
            self._media_player.setSource(QUrl())
            self._media_player.setVideoOutput(None)

    def _show_empty(self):
        self.image_label.setText("没有可预览的文件")
        self.image_label.setStyleSheet("color: rgba(255, 255, 255, 150); font-size: 18px;")
        self.content_stack.setCurrentWidget(self.image_scroll)
        self._clear_info()

    def _show_error(self, file_path: str, message: str):
        self.image_label.setText(f"⚠ {message}\n{os.path.basename(file_path)}")
        self.image_label.setStyleSheet("color: rgba(255, 100, 100, 200); font-size: 16px;")
        self.content_stack.setCurrentWidget(self.image_scroll)

    def _update_info(self, file_path: str):
        try:
            name = os.path.basename(file_path)
            self.name_label.setText(name)

            self.path_label.setText(file_path)

            attrs = []

            size = os.path.getsize(file_path)
            attrs.append(f"大小: {self._format_size(size)}")

            mtime = os.path.getmtime(file_path)
            mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            attrs.append(f"修改时间: {mtime_str}")

            gps_info = self._get_gps_info(file_path)
            if gps_info:
                attrs.append(f"GPS: {gps_info}")

            self.attrs_label.setText("  |  ".join(attrs))

        except Exception:
            self._clear_info()

    def _clear_info(self):
        self.name_label.clear()
        self.path_label.clear()
        self.attrs_label.clear()

    def _format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _get_gps_info(self, file_path: str) -> str:
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS, GPSTAGS

            ext = os.path.splitext(file_path)[1].lower()
            if ext not in {'.jpg', '.jpeg', '.tiff', '.tif'}:
                return ""

            with Image.open(file_path) as img:
                exif = img._getexif()
                if not exif:
                    return ""

                gps_data = {}
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == "GPSInfo":
                        for gps_tag in value:
                            sub_tag = GPSTAGS.get(gps_tag, gps_tag)
                            gps_data[sub_tag] = value[gps_tag]

                if not gps_data:
                    return ""

                lat = self._convert_to_degrees(gps_data.get("GPSLatitude"))
                lat_ref = gps_data.get("GPSLatitudeRef", "N")
                lon = self._convert_to_degrees(gps_data.get("GPSLongitude"))
                lon_ref = gps_data.get("GPSLongitudeRef", "E")

                if lat is not None and lon is not None:
                    lat_str = f"{lat:.6f}°{'N' if lat_ref == 'N' else 'S'}"
                    lon_str = f"{lon:.6f}°{'E' if lon_ref == 'E' else 'W'}"
                    return f"{lat_str}, {lon_str}"

        except Exception:
            pass
        return ""

    def _convert_to_degrees(self, value) -> float:
        if not value or len(value) != 3:
            return None
        try:
            d, m, s = value
            return float(d) + float(m) / 60 + float(s) / 3600
        except (ValueError, TypeError):
            return None

    def _update_nav_buttons(self):
        has_files = bool(self._files)
        self.left_btn.setEnabled(has_files and self._current_index > 0)
        self.right_btn.setEnabled(has_files and self._current_index < len(self._files) - 1)

    def _update_counter(self):
        if self._files:
            self.counter_label.setText(f"{self._current_index + 1} / {len(self._files)}")
        else:
            self.counter_label.clear()

    def showEvent(self, event):
        super().showEvent(event)
        self.showFullScreen()

        if not hasattr(self, '_animated'):
            self._animated = True
            self._animate_entrance()

    def closeEvent(self, event):
        self._cleanup_current()
        if self._media_player:
            self._media_player.deleteLater()
            self._media_player = None
        super().closeEvent(event)

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

    def wheelEvent(self, event: QWheelEvent):
        if self.content_stack.currentWidget() != self.image_scroll:
            super().wheelEvent(event)
            return

        delta = event.angleDelta().y()
        if delta == 0:
            super().wheelEvent(event)
            return

        self._zoom_at_point(delta, event.globalPosition().toPoint())
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.content_stack.currentWidget() == self.image_scroll:
                self._set_display_mode(self._display_mode)
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()

        if key == Qt.Key.Key_Escape:
            self.close()
        elif key == Qt.Key.Key_Left:
            self.prev()
        elif key == Qt.Key.Key_Right:
            self.next()
        elif key == Qt.Key.Key_F:
            self._cycle_display_mode()
        elif key == Qt.Key.Key_1:
            self._set_display_mode(DisplayMode.FIT)
        elif key == Qt.Key.Key_2:
            self._set_display_mode(DisplayMode.FILL)
        elif key == Qt.Key.Key_3:
            self._set_display_mode(DisplayMode.ORIGINAL)
        elif key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self._zoom_step(1)
        elif key == Qt.Key.Key_Minus:
            self._zoom_step(-1)
        elif key == Qt.Key.Key_0:
            self._set_display_mode(DisplayMode.ORIGINAL)
        elif key == Qt.Key.Key_Space:
            if self._media_player:
                if self._media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                    self._media_player.pause()
                else:
                    self._media_player.play()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(event.pos())
            if child is None or isinstance(child, (QFrame, QLabel)):
                pass
        super().mousePressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._current_index >= 0 and self._files:
            if self._display_mode in (DisplayMode.FIT, DisplayMode.FILL):
                self._zoom_factor = self._calc_base_zoom()
            self._refresh_current_image()
