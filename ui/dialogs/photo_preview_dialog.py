# -*- coding: utf-8 -*-
"""
图片预览对话框 - 全屏预览图片/GIF/视频
"""

import os
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame,
    QGraphicsOpacityEffect, QStackedWidget, QWidget
)
from PySide6.QtCore import (
    Signal, Qt, QPropertyAnimation, QEasingCurve, QTimer, QUrl,
    QSize, QEvent
)
from PySide6.QtGui import (
    QPixmap, QImage, QPalette, QColor, QKeyEvent, QMouseEvent,
    QMovie
)
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget

from core.theme_manager import get_theme_manager

# 支持的图片格式
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.tif'}
# 支持的视频格式
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}


class PhotoPreviewDialog(QDialog):
    """图片预览对话框 - 支持图片、GIF动画、视频播放"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._files = []  # 文件列表
        self._current_index = -1  # 当前索引
        self._current_movie = None  # 当前QMovie对象
        self._media_player = None  # 视频播放器
        self._audio_output = None  # 音频输出

        # 设置全屏无边框窗口
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        self._init_ui()
        self._apply_theme_style()

    def _init_ui(self):
        """初始化界面"""
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 背景遮罩（深色背景）
        self.bg_frame = QFrame()
        self.bg_frame.setObjectName("photoPreviewBg")
        bg_layout = QVBoxLayout()
        bg_layout.setSpacing(0)
        bg_layout.setContentsMargins(0, 0, 0, 0)

        # 内容区域
        content_layout = QVBoxLayout()
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(60, 40, 60, 20)

        # 顶部区域（关闭按钮）
        top_layout = QHBoxLayout()
        top_layout.addStretch()

        self.close_btn = QPushButton("×")
        self.close_btn.setObjectName("photoPreviewCloseBtn")
        self.close_btn.setFixedSize(48, 48)
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        top_layout.addWidget(self.close_btn)

        content_layout.addLayout(top_layout)

        # 中间区域（图片/视频显示 + 导航按钮）
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(20)

        # 左箭头
        self.left_btn = QPushButton("‹")
        self.left_btn.setObjectName("photoPreviewNavBtn")
        self.left_btn.setFixedSize(56, 56)
        self.left_btn.clicked.connect(self.prev)
        self.left_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.left_btn.setToolTip("上一张 (←)")
        middle_layout.addWidget(self.left_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        # 内容显示区域（使用QStackedWidget切换图片/视频）
        self.content_stack = QStackedWidget()

        # 图片显示标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(False)
        self.image_label.setMinimumSize(1, 1)
        self.content_stack.addWidget(self.image_label)

        # 视频播放区域
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(1, 1)
        self.content_stack.addWidget(self.video_widget)

        middle_layout.addWidget(self.content_stack, 1)

        # 右箭头
        self.right_btn = QPushButton("›")
        self.right_btn.setObjectName("photoPreviewNavBtn")
        self.right_btn.setFixedSize(56, 56)
        self.right_btn.clicked.connect(self.next)
        self.right_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.right_btn.setToolTip("下一张 (→)")
        middle_layout.addWidget(self.right_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        content_layout.addLayout(middle_layout, 1)

        # 底部区域（文件信息）
        self.info_frame = QFrame()
        self.info_frame.setObjectName("photoPreviewInfoFrame")
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)
        info_layout.setContentsMargins(20, 15, 20, 15)

        # 文件名
        self.name_label = QLabel()
        self.name_label.setObjectName("photoPreviewName")
        info_layout.addWidget(self.name_label)

        # 文件路径
        self.path_label = QLabel()
        self.path_label.setObjectName("photoPreviewPath")
        info_layout.addWidget(self.path_label)

        # 文件属性（大小、修改时间、GPS）
        self.attrs_label = QLabel()
        self.attrs_label.setObjectName("photoPreviewAttrs")
        info_layout.addWidget(self.attrs_label)

        self.info_frame.setLayout(info_layout)
        content_layout.addWidget(self.info_frame)

        # 计数器标签
        self.counter_label = QLabel()
        self.counter_label.setObjectName("photoPreviewCounter")
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.counter_label)

        bg_layout.addLayout(content_layout)
        self.bg_frame.setLayout(bg_layout)
        main_layout.addWidget(self.bg_frame)

        self.setLayout(main_layout)

    def _apply_theme_style(self):
        """应用主题样式"""
        theme_manager = get_theme_manager()

        # 设置背景色
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(20, 20, 22))  # 深色背景
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # 样式表
        self.setStyleSheet("""
            QFrame#photoPreviewBg {
                background-color: rgba(20, 20, 22, 240);
            }
            QPushButton#photoPreviewCloseBtn {
                background-color: rgba(255, 255, 255, 30);
                color: rgba(255, 255, 255, 200);
                border: none;
                border-radius: 24px;
                font-size: 28px;
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
                border-radius: 28px;
                font-size: 32px;
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
            QFrame#photoPreviewInfoFrame {
                background-color: rgba(0, 0, 0, 100);
                border-radius: 8px;
            }
            QLabel#photoPreviewName {
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QLabel#photoPreviewPath {
                color: rgba(255, 255, 255, 150);
                font-size: 12px;
            }
            QLabel#photoPreviewAttrs {
                color: rgba(255, 255, 255, 130);
                font-size: 12px;
            }
            QLabel#photoPreviewCounter {
                color: rgba(255, 255, 255, 150);
                font-size: 13px;
                padding: 5px;
            }
            QVideoWidget {
                background-color: black;
            }
        """)

    def set_files(self, files: list, current_index: int = 0):
        """设置文件列表和当前索引"""
        self._files = files if files else []
        self._current_index = max(0, min(current_index, len(self._files) - 1)) if self._files else -1
        self._load_current()

    def next(self):
        """显示下一张"""
        if not self._files or self._current_index >= len(self._files) - 1:
            return
        self._current_index += 1
        self._load_current()

    def prev(self):
        """显示上一张"""
        if not self._files or self._current_index <= 0:
            return
        self._current_index -= 1
        self._load_current()

    def _load_current(self):
        """加载当前文件"""
        # 清理之前的资源
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
        """加载静态图片"""
        self.content_stack.setCurrentWidget(self.image_label)

        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            self._show_error(file_path, "无法加载图片")
            return

        # 缩放以适应窗口
        scaled_pixmap = self._scale_pixmap(pixmap)
        self.image_label.setPixmap(scaled_pixmap)

    def _load_gif(self, file_path: str):
        """加载GIF动画"""
        self.content_stack.setCurrentWidget(self.image_label)

        # 使用QMovie播放GIF
        self._current_movie = QMovie(file_path)
        self._current_movie.setScaledSize(self._get_scaled_size())

        self.image_label.setMovie(self._current_movie)
        self._current_movie.start()

    def _load_video(self, file_path: str):
        """加载视频"""
        self.content_stack.setCurrentWidget(self.video_widget)

        # 初始化媒体播放器
        if self._media_player is None:
            self._media_player = QMediaPlayer()
            self._audio_output = None  # 简单处理，不添加音频输出

        self._media_player.setSource(QUrl.fromLocalFile(file_path))
        self._media_player.setVideoOutput(self.video_widget)
        self._media_player.play()

    def _scale_pixmap(self, pixmap: QPixmap) -> QPixmap:
        """缩放图片以适应窗口"""
        if pixmap.isNull():
            return pixmap

        available_size = self._get_available_size()
        if available_size.width() <= 0 or available_size.height() <= 0:
            return pixmap

        if pixmap.width() > available_size.width() or pixmap.height() > available_size.height():
            return pixmap.scaled(
                available_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        return pixmap

    def _get_scaled_size(self) -> QSize:
        """获取缩放后的尺寸"""
        available = self._get_available_size()
        return available

    def _get_available_size(self) -> QSize:
        """获取可用的显示区域大小"""
        # 预留边距和底部信息区域
        margin = 120
        info_height = 120
        return QSize(
            max(100, self.width() - margin * 2),
            max(100, self.height() - margin - info_height - 60)
        )

    def _cleanup_current(self):
        """清理当前资源"""
        # 停止并清理GIF
        if self._current_movie:
            self._current_movie.stop()
            self._current_movie.deleteLater()
            self._current_movie = None

        # 清理图片
        self.image_label.clear()
        self.image_label.setPixmap(QPixmap())

        # 停止并清理视频
        if self._media_player:
            self._media_player.stop()
            self._media_player.setSource(QUrl())
            self._media_player.setVideoOutput(None)

    def _show_empty(self):
        """显示空状态"""
        self.image_label.setText("没有可预览的文件")
        self.image_label.setStyleSheet("color: rgba(255, 255, 255, 150); font-size: 18px;")
        self.content_stack.setCurrentWidget(self.image_label)
        self._clear_info()

    def _show_error(self, file_path: str, message: str):
        """显示错误信息"""
        self.image_label.setText(f"⚠ {message}\n{os.path.basename(file_path)}")
        self.image_label.setStyleSheet("color: rgba(255, 100, 100, 200); font-size: 16px;")
        self.content_stack.setCurrentWidget(self.image_label)

    def _update_info(self, file_path: str):
        """更新文件信息"""
        try:
            # 文件名
            name = os.path.basename(file_path)
            self.name_label.setText(name)

            # 文件路径
            self.path_label.setText(file_path)

            # 文件属性
            attrs = []

            # 文件大小
            size = os.path.getsize(file_path)
            attrs.append(f"大小: {self._format_size(size)}")

            # 修改时间
            mtime = os.path.getmtime(file_path)
            mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            attrs.append(f"修改时间: {mtime_str}")

            # 尝试读取GPS信息（简化处理）
            gps_info = self._get_gps_info(file_path)
            if gps_info:
                attrs.append(f"GPS: {gps_info}")

            self.attrs_label.setText("  |  ".join(attrs))

        except Exception as e:
            self._clear_info()

    def _clear_info(self):
        """清空文件信息"""
        self.name_label.clear()
        self.path_label.clear()
        self.attrs_label.clear()

    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _get_gps_info(self, file_path: str) -> str:
        """获取GPS信息（从图片EXIF）"""
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

                # 解析GPS坐标
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
        """将GPS坐标转换为度数"""
        if not value or len(value) != 3:
            return None
        try:
            d, m, s = value
            return float(d) + float(m) / 60 + float(s) / 3600
        except (ValueError, TypeError):
            return None

    def _update_nav_buttons(self):
        """更新导航按钮状态"""
        has_files = bool(self._files)
        self.left_btn.setEnabled(has_files and self._current_index > 0)
        self.right_btn.setEnabled(has_files and self._current_index < len(self._files) - 1)

    def _update_counter(self):
        """更新计数器"""
        if self._files:
            self.counter_label.setText(f"{self._current_index + 1} / {len(self._files)}")
        else:
            self.counter_label.clear()

    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)
        # 全屏显示
        self.showFullScreen()

        # 入场动画
        if not hasattr(self, '_animated'):
            self._animated = True
            self._animate_entrance()

    def closeEvent(self, event):
        """关闭事件"""
        self._cleanup_current()
        if self._media_player:
            self._media_player.deleteLater()
            self._media_player = None
        super().closeEvent(event)

    def _animate_entrance(self):
        """淡入入场动画"""
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
        self._entrance_anim = anim  # 保持引用防止被GC

    def keyPressEvent(self, event: QKeyEvent):
        """键盘事件处理"""
        key = event.key()

        if key == Qt.Key.Key_Escape:
            self.close()
        elif key == Qt.Key.Key_Left:
            self.prev()
        elif key == Qt.Key.Key_Right:
            self.next()
        elif key == Qt.Key.Key_Space:
            # 空格键暂停/播放视频
            if self._media_player:
                if self._media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                    self._media_player.pause()
                else:
                    self._media_player.play()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        """鼠标点击事件"""
        # 点击非控件区域关闭
        if event.button() == Qt.MouseButton.LeftButton:
            # 检查是否点击在控件上
            child = self.childAt(event.pos())
            if child is None or isinstance(child, (QFrame, QLabel)):
                # 点击在背景或标签上，关闭对话框
                # 但不关闭，让用户通过X按钮或ESC关闭
                pass
        super().mousePressEvent(event)

    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        # 重新调整图片大小
        if self._current_index >= 0 and self._files:
            file_path = self._files[self._current_index]
            ext = os.path.splitext(file_path)[1].lower()

            if ext == '.gif' and self._current_movie:
                self._current_movie.setScaledSize(self._get_scaled_size())
            elif ext in IMAGE_EXTENSIONS:
                pixmap = self.image_label.pixmap()
                if pixmap and not pixmap.isNull():
                    # 重新加载原始图片并缩放
                    original = QPixmap(file_path)
                    if not original.isNull():
                        self.image_label.setPixmap(self._scale_pixmap(original))