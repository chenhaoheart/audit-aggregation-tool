# -*- coding: utf-8 -*-
"""
图册管理页面 - 完整复刻React版本设计

核心特点:
- 树形导航与文件卡片一体化 (展开后文件网格嵌入在节点下方)
- 单一滚动容器包含整个树+文件结构
- 可配置网格列数 (2-10列)
- 支持树形视图和平铺Grid视图切换
- 文件夹统计、删除按钮(hover显示)
"""

import os
from datetime import datetime
from typing import List, Dict, Optional, Set
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QFrame, QScrollArea, QStackedWidget, QSizePolicy,
    QGridLayout, QCheckBox, QMessageBox, QAbstractItemView, QComboBox,
    QSpinBox, QToolButton, QSlider, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QThread, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QPixmap, QImage, QColor

from services.photo_gallery_service import PhotoGalleryService
from services.photo_match_service import PhotoMatchService, MatchWorker
from ui.components.gis_map_widget import GisMapWidget, HAS_WEB_ENGINE
from ui.dialogs.photo_preview_dialog import PhotoPreviewDialog
from ui.dialogs.batch_rename_dialog import BatchRenameDialog
from ui.dialogs.delete_confirm_dialog import DeleteConfirmDialog
from ui.dialogs.photo_match_report_dialog import PhotoMatchReportDialog
from core.theme_manager import get_theme_manager
from core.effects_manager import ShimmerProgress, ButtonGlowHelper

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


# ============================================
# 图片卡片组件
# ============================================

class PhotoCard(QFrame):
    """图片卡片 - 嵌入在树节点下方"""

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

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        base = max(60, int(PhotoCard.BASE_SIZE * PhotoCard._current_scale))
        self.image_label.setMinimumSize(base, base)
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
        self.image_label.setText(icon)
        self.image_label.setStyleSheet(f"""
            font-size: 32px;
            color: {theme.get('text_muted', '#94a3b8')};
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


# ============================================
# 树节点组件 (文件夹 + 可展开文件网格)
# ============================================

class TreeNodeWidget(QFrame):
    """树节点 - 可展开/折叠，展开后显示子节点和文件网格"""

    expand_changed = Signal()
    delete_requested = Signal(str)

    def __init__(self, node_data: dict, depth: int = 0, grid_columns: int = 4, accent: str = '#6366f1', parent=None):
        super().__init__(parent)
        self.node_data = node_data
        self.depth = depth
        self.grid_columns = grid_columns
        self._accent = accent
        self._expanded = True if depth == 0 else False
        self._theme_manager = get_theme_manager()

        self.setObjectName("treeNode")
        self.setStyleSheet("QFrame#treeNode { background: transparent; }")

        self._child_widgets: List['TreeNodeWidget'] = []
        self._card_widgets: List[PhotoCard] = []
        self._animation = None

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # ========== 节点头部 (文件夹行) ==========
        self.header = QFrame()
        self.header.setObjectName("treeNodeHeader")
        self.header.setCursor(Qt.PointingHandCursor)
        indent = self.depth * 16

        theme = self._theme_manager.get_current_theme()
        hover_bg = theme.get('surface_1', theme.get('content_bg', '#f8fafc'))
        hover_border = theme.get('border_subtle', theme.get('card_border', '#e2e8f0'))
        self.header.setStyleSheet(f"""
            QFrame#treeNodeHeader {{
                padding: 8px 12px; margin-left: {indent}px;
                border-radius: 10px; background: transparent;
                border: 1px solid transparent;
            }}
            QFrame#treeNodeHeader:hover {{
                background: {hover_bg};
                border-color: {hover_border};
            }}
        """)

        # 添加阴影效果（仅根节点和第一级）
        if self.depth <= 1:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(8)
            shadow.setColor(QColor(0, 0, 0, 15))
            shadow.setOffset(0, 2)
            self.header.setGraphicsEffect(shadow)

        header_layout = QHBoxLayout(self.header)
        header_layout.setSpacing(10)

        # 颜色指示条
        color_bar = QFrame()
        color_bar.setStyleSheet(f"""
            QFrame {{
                background: {self._accent};
                border-radius: 2px;
            }}
        """)
        color_bar.setFixedSize(3, 16)
        header_layout.addWidget(color_bar, 0, Qt.AlignVCenter)

        # 展开/折叠箭头
        self.arrow_btn = QToolButton()
        self.arrow_btn.setFixedSize(18, 18)
        self.arrow_btn.setCursor(Qt.PointingHandCursor)
        self._update_arrow()
        self.arrow_btn.clicked.connect(self.toggle_expand)
        header_layout.addWidget(self.arrow_btn, 0, Qt.AlignVCenter)

        folder_icon = QLabel("📁")
        folder_icon.setStyleSheet(f"font-size: 16px;")
        header_layout.addWidget(folder_icon, 0, Qt.AlignVCenter)

        # 文件夹名称
        name = self.node_data.get('name', '')
        path = self.node_data.get('path', '')
        is_root = self.node_data.get('isRoot', False)

        self.name_label = QLabel(path if is_root else name)
        self.name_label.setObjectName("treeNodeName")
        text_primary = theme.get('text_primary', '#1e293b')
        self.name_label.setStyleSheet(f"""
            font-weight: 600;
            font-size: 13px;
            color: {text_primary};
        """)
        self.name_label.setToolTip(path)
        header_layout.addWidget(self.name_label, 1, Qt.AlignVCenter)

        # 照片/视频统计徽章 - 简洁文字样式
        photos = self.node_data.get('photo_count', 0)
        videos = self.node_data.get('video_count', 0)
        if photos > 0 or videos > 0:
            stats_layout = QHBoxLayout()
            stats_layout.setSpacing(6)

            photo_count = QLabel(f"📷 {photos}")
            photo_count.setStyleSheet(f"color: {theme.get('accent_color', '#6366f1')}; font-size: 12px; font-weight: 600;")
            stats_layout.addWidget(photo_count)

            if videos > 0:
                video_count = QLabel(f"🎬 {videos}")
                video_count.setStyleSheet(f"color: {theme.get('info_text', '#8b5cf6')}; font-size: 12px; font-weight: 600;")
                stats_layout.addWidget(video_count)

            header_layout.addLayout(stats_layout)

        if not is_root:
            self.delete_btn = QToolButton()
            self.delete_btn.setText("🗑")
            self.delete_btn.setFixedSize(24, 24)
            self.delete_btn.setCursor(Qt.PointingHandCursor)
            text_muted = theme.get('text_muted', '#cbd5e1')
            danger_bg = theme.get('error_bg', 'rgba(239,68,68,0.12)')
            danger_text = theme.get('btn_danger_text', theme.get('error_text', '#ef4444'))
            self.delete_btn.setStyleSheet(f"""
                QToolButton {{ background: transparent; color: {text_muted}; border-radius: 6px; border: none; }}
                QToolButton:hover {{ background: {danger_bg}; color: {danger_text}; }}
            """)
            self.delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.node_data['path']))
            header_layout.addWidget(self.delete_btn, 0, Qt.AlignVCenter)

        layout.addWidget(self.header)

        # ========== 子节点容器 (可展开/折叠) ==========
        self.children_container = QWidget()
        self.children_container.setObjectName("treeChildren")
        children_layout = QVBoxLayout(self.children_container)
        children_layout.setSpacing(2)
        children_layout.setContentsMargins(0, 4, 0, 4)

        # 子文件夹节点
        children = self.node_data.get('children', {})
        for child_name, child_data in sorted(children.items()):
            child_widget = TreeNodeWidget(child_data, self.depth + 1, self.grid_columns, self._accent, self)
            child_widget.expand_changed.connect(self.expand_changed)
            child_widget.delete_requested.connect(self.delete_requested)
            children_layout.addWidget(child_widget)
            self._child_widgets.append(child_widget)

        # 当前文件夹的文件网格
        files = self.node_data.get('files', [])
        if files:
            self.files_grid = QWidget()
            grid_layout = QGridLayout(self.files_grid)
            grid_layout.setSpacing(8)
            grid_layout.setContentsMargins(0, 8, 0, 8)

            for i, file_info in enumerate(files):
                card = PhotoCard(file_info, self._accent, self)
                card.clicked.connect(lambda path: None)  # 外部连接
                card.selection_changed.connect(lambda path, sel: None)  # 外部连接
                row = i // self.grid_columns
                col = i % self.grid_columns
                grid_layout.addWidget(card, row, col)
                self._card_widgets.append(card)

            children_layout.addWidget(self.files_grid)

        self.children_container.setVisible(self._expanded)
        layout.addWidget(self.children_container)

    def _update_arrow(self):
        """更新箭头显示"""
        theme = self._theme_manager.get_current_theme()
        has_children = bool(self.node_data.get('children', {})) or bool(self.node_data.get('files', []))
        text_muted = theme.get('text_muted', '#94a3b8')
        accent = theme.get('accent_color', '#6366f1')
        hover_bg = theme.get('surface_1', theme.get('content_bg', '#f1f5f9'))
        if has_children:
            arrow = "▼" if self._expanded else "▶"
            self.arrow_btn.setStyleSheet(f"""
                QToolButton {{
                    color: {text_muted};
                    font-size: 11px;
                    border: none;
                    font-weight: 600;
                    background: transparent;
                }}
                QToolButton:hover {{
                    color: {accent};
                    background: {hover_bg};
                    border-radius: 4px;
                }}
            """)
            self.arrow_btn.setText(arrow)
        else:
            self.arrow_btn.setText("")
            self.arrow_btn.setDisabled(True)

    def toggle_expand(self):
        """切换展开/折叠 - 带动画"""
        self._expanded = not self._expanded
        self._update_arrow()

        # 先设置可见性
        self.children_container.setVisible(True)

        # 使用动画效果
        if self._animation:
            self._animation.stop()
            try:
                self._animation.finished.disconnect()
            except RuntimeError:
                pass

        self._animation = QPropertyAnimation(self.children_container, b"maximumHeight")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        if self._expanded:
            # 展开：从0到实际高度
            self.children_container.setMaximumHeight(0)
            target_height = self.children_container.sizeHint().height()
            self._animation.setStartValue(0)
            self._animation.setEndValue(max(target_height, 100))
            self._animation.finished.connect(self._on_expand_finished)
        else:
            # 折叠：从当前高度到0
            current_height = self.children_container.height()
            self._animation.setStartValue(current_height)
            self._animation.setEndValue(0)
            self._animation.finished.connect(self._on_collapse_finished)

        self._animation.start()
        self.expand_changed.emit()

    def _on_expand_finished(self):
        """展开动画完成"""
        self.children_container.setMaximumHeight(16777215)
        self._notify_parent_layout_update()

    def _on_collapse_finished(self):
        """折叠动画完成"""
        self.children_container.setVisible(False)
        self.children_container.setMaximumHeight(0)
        self._notify_parent_layout_update()

    def _notify_parent_layout_update(self):
        """通知父级布局更新大小"""
        self.updateGeometry()
        parent = self.parentWidget()
        while parent:
            parent.updateGeometry()
            if parent.objectName() == "treeContainer":
                break
            parent = parent.parentWidget()

    def expand_all(self):
        """展开所有"""
        self._expanded = True
        self._update_arrow()
        self.children_container.setVisible(True)
        self.children_container.setMaximumHeight(16777215)
        for child in self._child_widgets:
            child.expand_all()

    def collapse_all(self):
        """折叠所有"""
        if self.depth > 0:  # 根节点始终展开
            self._expanded = False
            self._update_arrow()
            self.children_container.setVisible(False)
        for child in self._child_widgets:
            child.collapse_all()

    def set_grid_columns(self, columns: int):
        self.grid_columns = columns
        for child in self._child_widgets:
            child.set_grid_columns(columns)

        if hasattr(self, 'files_grid') and self._card_widgets:
            grid_layout = self.files_grid.layout()
            for i, card in enumerate(self._card_widgets):
                row = i // columns
                col = i % columns
                grid_layout.addWidget(card, row, col)

    def update_zoom(self, scale):
        for card in self._card_widgets:
            card.update_zoom(scale)
        for child in self._child_widgets:
            child.update_zoom(scale)

    def get_all_cards(self) -> List[PhotoCard]:
        """获取所有图片卡片"""
        cards = self._card_widgets.copy()
        for child in self._child_widgets:
            cards.extend(child.get_all_cards())
        return cards

    def get_all_files(self) -> List[dict]:
        """获取所有文件信息"""
        files = [c.file_info for c in self._card_widgets]
        for child in self._child_widgets:
            files.extend(child.get_all_files())
        return files


# ============================================
# 图册管理主页面
# ============================================

class PhotoGalleryPage(QWidget):
    """图册管理页面 - 完整复刻React版本"""

    log_message = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.folder_path = ""
        self.scan_result = None
        self.selected_files: Set[str] = set()
        self.current_view = "tree"  # tree / list / map
        self.grid_columns = 4
        self.search_query = ""
        self.filter_type = "all"  # all / photo / video
        self._card_zoom = 5
        self._match_result = None

        self.service = PhotoGalleryService(self)
        self.match_service = PhotoMatchService(self)
        self.theme_manager = get_theme_manager()
        self._accent_color = self.theme_manager.get_current_theme().get('accent_color', '#6366f1')

        self.service.scan_finished.connect(self._on_scan_finished)
        self.service.scan_progress.connect(self._on_scan_progress)
        self.service.error_occurred.connect(self._on_error)

        self.match_service.match_progress.connect(self._on_match_progress)
        self.match_service.match_error.connect(self._on_match_error)

        self.theme_manager.theme_changed.connect(self._on_theme_changed)

        self._init_ui()

    def _on_theme_changed(self, mode: str):
        """响应主题切换，更新页面颜色"""
        theme = self.theme_manager.get_current_theme()
        self._accent_color = theme.get('accent_color', '#6366f1')
        
        # 更新统计徽章颜色
        if hasattr(self, 'badge_photos'):
            self._update_badge_color(self.badge_photos, self._accent_color)
        if hasattr(self, 'badge_videos'):
            self._update_badge_color(self.badge_videos, theme.get('info_text', '#8b5cf6'))
        if hasattr(self, 'badge_size'):
            self._update_badge_color(self.badge_size, theme.get('warning_text', '#f59e0b'))
        
        # 更新树节点颜色
        if self._root_node:
            self._update_tree_colors(self._root_node, self._accent_color)
        
        # 更新地图颜色
        if self.current_view == 'map' and hasattr(self, 'map_widget') and self.map_widget:
            self._update_map_view()

    def _update_badge_color(self, badge: QFrame, color: str):
        """更新徽章颜色"""
        if hasattr(badge, '_value_label'):
            badge._value_label.setStyleSheet(f"color: {color}; font-weight: 700; font-size: 14px;")
        if hasattr(badge, '_label_label'):
            badge._label_label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 500;")

    def _update_tree_colors(self, node: TreeNodeWidget, accent: str):
        """递归更新树节点颜色"""
        node._accent = accent
        # 更新节点头部样式
        if hasattr(node, 'header'):
            theme = self.theme_manager.get_current_theme()
            hover_bg = theme.get('surface_1', theme.get('content_bg', '#f8fafc'))
            hover_border = theme.get('border_subtle', theme.get('card_border', '#e2e8f0'))
            indent = node.depth * 16
            node.header.setStyleSheet(f"""
                QFrame#treeNodeHeader {{
                    padding: 8px 12px; margin-left: {indent}px;
                    border-radius: 10px; background: transparent;
                    border: 1px solid transparent;
                }}
                QFrame#treeNodeHeader:hover {{
                    background: {hover_bg};
                    border-color: {hover_border};
                }}
            """)
        # 更新箭头样式
        if hasattr(node, '_update_arrow'):
            node._update_arrow()
        # 更新卡片颜色
        for card in node._card_widgets:
            card._accent = accent
            card._apply_scale(PhotoCard._current_scale)
        # 递归更新子节点
        for child in node._child_widgets:
            self._update_tree_colors(child, accent)

    def _init_ui(self):
        """初始化UI - 整页可滚动，优化布局和配色"""
        theme = self.theme_manager.get_current_theme()
        self._accent_color = theme.get('accent_color', '#6366f1')

        outer_layout = QVBoxLayout(self)
        outer_layout.setSpacing(0)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        self.main_scroll = QScrollArea()
        self.main_scroll.setWidgetResizable(True)
        self.main_scroll.setFrameShape(QFrame.NoFrame)
        self.main_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_content.setObjectName("cardInnerPanel")
        scroll_content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        toolbar_bg = theme.get('toolbar_bg', theme.get('card_bg', '#f8fafc'))
        toolbar_border = theme.get('toolbar_border', theme.get('card_border', '#e2e8f0'))
        surface_1 = theme.get('surface_1', '#f8fafc')
        text_primary = theme.get('text_primary', '#1e293b')
        text_muted = theme.get('text_muted', '#94a3b8')
        text_hint = theme.get('text_hint', '#cbd5e1')
        accent = theme.get('accent_color', '#6366f1')
        border_subtle = theme.get('border_subtle', '#e2e8f0')
        card_bg = theme.get('card_bg', '#ffffff')
        input_bg = theme.get('input_bg', card_bg)
        input_border = theme.get('input_border', border_subtle)
        input_text = theme.get('text_primary', '#334155')

        self.header_card = QFrame()
        self.header_card.setObjectName("pageHeader")
        header_layout = QHBoxLayout(self.header_card)
        header_layout.setSpacing(16)
        header_layout.setContentsMargins(20, 16, 20, 16)
        accent_bar = QFrame()
        accent_bar.setObjectName("accentBar")
        accent_bar.setFixedWidth(4)
        accent_bar.setMinimumHeight(20)
        header_layout.addWidget(accent_bar)
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        page_title = QLabel("照片检查")
        page_title.setObjectName("sectionHeaderLg")
        title_layout.addWidget(page_title)
        page_subtitle = QLabel("扫描文件夹，管理照片和视频文件")
        page_subtitle.setObjectName("pageSubtitle")
        title_layout.addWidget(page_subtitle)
        header_layout.addLayout(title_layout, 1)

        self.badge_photos = self._create_badge("照片", "--", accent)
        header_layout.addWidget(self.badge_photos)
        header_layout.addWidget(self._create_separator())

        self.badge_videos = self._create_badge("视频", "--", theme.get('info_text', '#8b5cf6'))
        header_layout.addWidget(self.badge_videos)
        header_layout.addWidget(self._create_separator())

        self.badge_size = self._create_badge("大小", "--", theme.get('warning_text', '#f59e0b'))
        header_layout.addWidget(self.badge_size)

        scroll_layout.addWidget(self.header_card)

        self.toolbar_card = QFrame()
        self.toolbar_card.setObjectName("card")
        toolbar_layout = QVBoxLayout(self.toolbar_card)
        toolbar_layout.setSpacing(12)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)

        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(8)

        self.folder_edit = QLineEdit()
        self.folder_edit.setObjectName("filterEdit")
        self.folder_edit.setPlaceholderText("输入文件夹路径或点击浏览选择...")
        self.folder_edit.returnPressed.connect(self._start_scan)
        folder_layout.addWidget(self.folder_edit, 1)

        self.browse_btn = QPushButton("浏览")
        self.browse_btn.setObjectName("toolbarBtn")
        self.browse_btn.clicked.connect(self._select_folder)
        folder_layout.addWidget(self.browse_btn)

        self.scan_btn = QPushButton("扫描")
        self.scan_btn.setObjectName("toolbarBtnPrimary")
        self.scan_btn.clicked.connect(self._start_scan)
        ButtonGlowHelper.install(self.scan_btn)
        folder_layout.addWidget(self.scan_btn)

        self.match_btn = QPushButton("附表校验")
        self.match_btn.setObjectName("toolbarBtn")
        self.match_btn.clicked.connect(self._run_photo_match)
        self.match_btn.setEnabled(False)
        folder_layout.addWidget(self.match_btn)

        toolbar_layout.addLayout(folder_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(4)
        toolbar_layout.addWidget(self.progress_bar)
        self._progress_shimmer = ShimmerProgress(self.progress_bar)

        toolbar_row1 = QHBoxLayout()
        toolbar_row1.setSpacing(6)

        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.setObjectName("toolbarBtn")
        self.select_all_btn.clicked.connect(self._select_all)
        toolbar_row1.addWidget(self.select_all_btn)

        self.deselect_btn = QPushButton("取消")
        self.deselect_btn.setObjectName("toolbarBtn")
        self.deselect_btn.clicked.connect(self._deselect_all)
        toolbar_row1.addWidget(self.deselect_btn)

        toolbar_row1.addWidget(self._create_separator())

        self.expand_all_btn = QPushButton("展开全部")
        self.expand_all_btn.setObjectName("toolbarBtn")
        self.expand_all_btn.clicked.connect(self._expand_all_tree)
        self.expand_all_btn.setEnabled(False)
        toolbar_row1.addWidget(self.expand_all_btn)

        self.collapse_all_btn = QPushButton("折叠全部")
        self.collapse_all_btn.setObjectName("toolbarBtn")
        self.collapse_all_btn.clicked.connect(self._collapse_all_tree)
        self.collapse_all_btn.setEnabled(False)
        toolbar_row1.addWidget(self.collapse_all_btn)

        toolbar_row1.addWidget(self._create_separator())

        self.rename_btn = QPushButton("重命名")
        self.rename_btn.setObjectName("toolbarBtn")
        self.rename_btn.clicked.connect(self._show_rename_dialog)
        self.rename_btn.setEnabled(False)
        toolbar_row1.addWidget(self.rename_btn)

        toolbar_row1.addWidget(self._create_separator())

        self.gps_btn = QPushButton("显示GPS")
        self.gps_btn.setObjectName("toolbarBtn")
        self.gps_btn.clicked.connect(self._show_gps_on_map)
        self.gps_btn.setEnabled(False)
        toolbar_row1.addWidget(self.gps_btn)

        toolbar_row1.addWidget(self._create_separator())

        self.selected_label = QLabel()
        toolbar_row1.addWidget(self.selected_label)

        toolbar_row1.addStretch()

        toolbar_layout.addLayout(toolbar_row1)

        toolbar_row2 = QHBoxLayout()
        toolbar_row2.setSpacing(8)

        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("filterEdit")
        self.search_edit.setPlaceholderText("搜索文件名...")
        self.search_edit.textChanged.connect(self._on_search_changed)
        toolbar_row2.addWidget(self.search_edit, 1)

        self.filter_label = QLabel("类型:")
        toolbar_row2.addWidget(self.filter_label)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["全部", "照片", "视频"])
        self.type_combo.currentIndexChanged.connect(self._on_type_filter_changed)
        toolbar_row2.addWidget(self.type_combo)

        toolbar_row2.addWidget(self._create_separator())

        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setObjectName("zoomSlider")
        self.zoom_slider.setRange(1, 10)
        self.zoom_slider.setValue(5)
        self.zoom_slider.setFixedWidth(80)
        self.zoom_slider.valueChanged.connect(self._on_zoom_changed)
        toolbar_row2.addWidget(self.zoom_slider)

        self.zoom_label = QLabel("缩放 1.0x")
        self.zoom_label.setObjectName("toolbarSubtitle")
        toolbar_row2.addWidget(self.zoom_label)

        toolbar_row2.addWidget(self._create_separator())

        self.col_label = QLabel("列数:")
        self.col_label.setObjectName("toolbarSubtitle")
        toolbar_row2.addWidget(self.col_label)

        self.col_spin = QSpinBox()
        self.col_spin.setRange(2, 10)
        self.col_spin.setValue(4)
        self.col_spin.valueChanged.connect(self._on_columns_changed)
        toolbar_row2.addWidget(self.col_spin)

        toolbar_row2.addWidget(self._create_separator())

        self.view_label = QLabel("视图:")
        self.view_label.setObjectName("toolbarSubtitle")
        toolbar_row2.addWidget(self.view_label)

        self.tree_btn = QPushButton("树形")
        self.tree_btn.setObjectName("photoViewBtn")
        self.tree_btn.setCheckable(True)
        self.tree_btn.setChecked(True)
        self.tree_btn.clicked.connect(lambda: self._switch_view("tree"))
        toolbar_row2.addWidget(self.tree_btn)

        self.list_btn = QPushButton("列表")
        self.list_btn.setObjectName("photoViewBtn")
        self.list_btn.setCheckable(True)
        self.list_btn.clicked.connect(lambda: self._switch_view("list"))
        toolbar_row2.addWidget(self.list_btn)

        self.map_btn = QPushButton("地图")
        self.map_btn.setObjectName("photoViewBtn")
        self.map_btn.setCheckable(True)
        self.map_btn.clicked.connect(lambda: self._switch_view("map"))
        toolbar_row2.addWidget(self.map_btn)

        toolbar_layout.addLayout(toolbar_row2)

        scroll_layout.addWidget(self.toolbar_card)

        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("QStackedWidget { background: transparent; }")

        self.tree_container = QWidget()
        self.tree_container.setObjectName("treeContainer")
        self.tree_container.setStyleSheet("QWidget#treeContainer { background: transparent; }")
        self.tree_container_layout = QVBoxLayout(self.tree_container)
        self.tree_container_layout.setSpacing(0)
        self.tree_container_layout.setContentsMargins(12, 4, 12, 12)
        self.tree_container_layout.setAlignment(Qt.AlignTop)
        self.content_stack.addWidget(self.tree_container)

        self.list_view = QWidget()
        self._setup_list_view()
        self.content_stack.addWidget(self.list_view)

        if HAS_WEB_ENGINE:
            self.map_container = QWidget()
            map_container_layout = QVBoxLayout(self.map_container)
            map_container_layout.setContentsMargins(8, 4, 8, 8)
            map_container_layout.setSpacing(0)
            map_container_layout.setAlignment(Qt.AlignTop)

            self.map_widget = GisMapWidget(self)
            self.map_widget.setMinimumHeight(400)
            self.map_widget.photo_clicked.connect(self._on_map_photo_clicked)
            map_container_layout.addWidget(self.map_widget, 1)
            self.content_stack.addWidget(self.map_container)
        else:
            fallback = QWidget()
            fl = QVBoxLayout(fallback)
            fl.setAlignment(Qt.AlignCenter)

            self.map_fallback_icon = QLabel("🗺️")
            self.map_fallback_icon.setObjectName("galleryEmptyIcon")
            fl.addWidget(self.map_fallback_icon)

            self.map_fallback_msg = QLabel("地图需要 PySide6-WebEngine\npip install PySide6-WebEngine")
            self.map_fallback_msg.setObjectName("galleryEmpty")
            fl.addWidget(self.map_fallback_msg)

            self.content_stack.addWidget(fallback)
            self.map_widget = None

        self.empty_widget = QWidget()
        self.empty_widget.setMinimumHeight(400)
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setSpacing(16)
        empty_layout.setAlignment(Qt.AlignCenter)

        self.empty_icon = QLabel("📂")
        self.empty_icon.setObjectName("galleryEmptyIcon")
        self.empty_icon.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(self.empty_icon)

        self.empty_text = QLabel("选择文件夹开始扫描")
        self.empty_text.setObjectName("galleryEmpty")
        self.empty_text.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(self.empty_text)

        self.empty_sub = QLabel("支持 JPG、PNG、MP4 等照片和视频文件")
        self.empty_sub.setObjectName("galleryEmpty")
        self.empty_sub.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(self.empty_sub)

        self.content_stack.addWidget(self.empty_widget)
        self.content_stack.setCurrentIndex(3)

        scroll_layout.addWidget(self.content_stack)

        self.main_scroll.setWidget(scroll_content)
        outer_layout.addWidget(self.main_scroll)

        self._root_node: Optional[TreeNodeWidget] = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_view == "map":
            self._apply_map_large_height()

    def _apply_map_large_height(self):
        if not HAS_WEB_ENGINE or not self.map_widget:
            return
        window_h = self.window().height() if self.window() else 800
        header_h = self.header_card.height() if self.header_card else 60
        toolbar_h = self.toolbar_card.height() if self.toolbar_card else 140
        top_h = header_h + toolbar_h
        available = int((window_h - top_h) * 0.95)
        map_h = max(600, available)
        self.map_widget.setMinimumHeight(map_h)
        self.map_widget.setMaximumHeight(map_h)

    def _restore_map_size(self):
        if HAS_WEB_ENGINE and self.map_widget:
            self.map_widget.setMinimumHeight(400)
            self.map_widget.setMaximumHeight(16777215)

    def _create_badge(self, label: str, value: str, color: str) -> QFrame:
        """创建统计徽章 - 简洁文字样式"""
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
        return badge

    def _create_separator(self) -> QFrame:
        """创建分隔线"""
        theme = self.theme_manager.get_current_theme()
        sep = QFrame()
        sep.setStyleSheet(f"background: {theme.get('divider_color', '#e2e8f0')}; margin: 0 8px;")
        sep.setFixedWidth(1)
        sep.setFixedHeight(16)
        return sep

    def _setup_list_view(self):
        """设置列表视图 - 无内部滚动条，随页面滚动"""
        theme = self.theme_manager.get_current_theme()
        card_bg = theme.get('card_bg', '#ffffff')
        border_subtle = theme.get('border_subtle', theme.get('card_border', '#e2e8f0'))
        surface_1 = theme.get('surface_1', '#f8fafc')
        text_primary = theme.get('text_primary', '#334155')
        text_muted = theme.get('text_muted', '#64748b')

        layout = QVBoxLayout(self.list_view)
        layout.setSpacing(0)
        layout.setContentsMargins(8, 0, 8, 8)
        layout.setAlignment(Qt.AlignTop)

        self.list_table = QTableWidget()
        self.list_table.setColumnCount(7)
        self.list_table.setHorizontalHeaderLabels(["选择", "文件名", "类型", "大小", "修改时间", "GPS", "路径"])
        self.list_table.horizontalHeader().setStretchLastSection(True)
        self.list_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.list_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.list_table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.list_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_table.setStyleSheet(f"""
            QTableWidget {{
                background: {card_bg}; border: 1px solid {border_subtle}; border-radius: 8px;
                gridline-color: {surface_1}; font-size: 13px; color: {text_primary};
            }}
            QTableWidget::item {{ padding: 6px 10px; }}
            QHeaderView::section {{
                background: {surface_1}; border: none; border-bottom: 2px solid {border_subtle};
                padding: 8px 10px; font-size: 12px; font-weight: 600; color: {text_muted};
            }}
        """)
        layout.addWidget(self.list_table)

    # ========== 文件选择和扫描 ==========

    def _select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.folder_edit.setText(folder)
            self.folder_path = folder

    def _start_scan(self):
        path = self.folder_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "警告", "请输入或选择文件夹路径")
            return

        self.folder_path = path
        self._clear_results()

        self.scan_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self._progress_shimmer.start()
        self._log("开始扫描...")

        self.service.scan_folder(path, recursive=True)

    def _on_scan_progress(self, msg: str):
        self._log(msg)

    def _on_scan_finished(self, result: dict):
        self.scan_result = result

        self._progress_shimmer.stop()
        self.progress_bar.setVisible(False)
        self.scan_btn.setEnabled(True)

        # 更新统计徽章
        self.badge_photos._value_label.setText(str(result['total_photos']))
        self.badge_videos._value_label.setText(str(result['total_videos']))
        self.badge_size._value_label.setText(f"{result['total_size_mb']}MB")

        # 构建树形结构
        tree_data = self.service.build_tree_structure(result)
        self._build_tree_view(tree_data)

        self.expand_all_btn.setEnabled(True)
        self.collapse_all_btn.setEnabled(True)
        self.gps_btn.setEnabled(result['total_photos'] > 0)
        self.match_btn.setEnabled(result['total_photos'] > 0)

        self._log(f"扫描完成: {result['total_photos']} 照片, {result['total_videos']} 视频")

        # 如果当前视图是地图视图，更新地图显示
        if self.current_view == 'map':
            self._update_map_view()
        else:
            self.content_stack.setCurrentIndex(0)

    def _on_error(self, msg: str):
        self._progress_shimmer.stop()
        self.progress_bar.setVisible(False)
        self.scan_btn.setEnabled(True)
        self._log(f"错误: {msg}")
        QMessageBox.critical(self, "错误", f"扫描失败:\n{msg}")

    def _build_tree_view(self, tree_data: dict):
        """构建树形视图"""
        # 清空现有树
        while self.tree_container_layout.count():
            item = self.tree_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 创建根节点
        self._root_node = TreeNodeWidget(tree_data, depth=0, grid_columns=self.grid_columns, accent=self._accent_color, parent=self)
        self._root_node.expand_changed.connect(self._on_tree_expand_changed)
        self._root_node.delete_requested.connect(self._on_delete_folder_requested)

        # 连接所有卡片信号
        for card in self._root_node.get_all_cards():
            card.clicked.connect(self._on_card_clicked)
            card.selection_changed.connect(self._on_card_selection_changed)

        self.tree_container_layout.insertWidget(0, self._root_node)
        self._update_selected_count()

    # ========== 树操作 ==========

    def _expand_all_tree(self):
        if self._root_node:
            self._root_node.expand_all()

    def _collapse_all_tree(self):
        if self._root_node:
            self._root_node.collapse_all()

    def _on_tree_expand_changed(self):
        pass

    def _on_columns_changed(self, columns: int):
        self.grid_columns = columns
        if self._root_node:
            self._root_node.set_grid_columns(columns)

    def _on_search_changed(self, text: str):
        self.search_query = text.lower()
        self._apply_filters()

    def _on_type_filter_changed(self, index: int):
        self.filter_type = ["all", "photo", "video"][index]
        self._apply_filters()

    def _apply_filters(self):
        """应用搜索和类型过滤"""
        if not self._root_node:
            return

        for card in self._root_node.get_all_cards():
            file_info = card.file_info
            name = file_info['name'].lower()
            type_ = file_info['type']

            visible = True
            if self.search_query and self.search_query not in name:
                visible = False
            if self.filter_type == "photo" and type_ != "photo":
                visible = False
            if self.filter_type == "video" and type_ != "video":
                visible = False

            card.setVisible(visible)

    # ========== 视图切换 ==========

    def _switch_view(self, view: str):
        self.current_view = view

        self.tree_btn.setChecked(view == "tree")
        self.list_btn.setChecked(view == "list")
        self.map_btn.setChecked(view == "map")

        self.col_spin.setEnabled(view == "tree")

        if view == "tree":
            self._restore_map_size()
            self.content_stack.setCurrentIndex(0)
        elif view == "list":
            self._restore_map_size()
            self._update_list_view()
            self.content_stack.setCurrentIndex(1)
        elif view == "map":
            self._apply_map_large_height()
            self._update_map_view()
            self.content_stack.setCurrentIndex(2)

    def _update_list_view(self):
        """更新列表视图"""
        if not self._root_node:
            return

        all_files = self._root_node.get_all_files()
        filtered = [f for f in all_files if self.service.file_matches_filter(f, self.search_query, self.filter_type)]

        self.list_table.setRowCount(len(filtered))

        for row, file_info in enumerate(filtered):
            check_widget = QWidget()
            check_layout = QHBoxLayout(check_widget)
            checkbox = QCheckBox()
            checkbox.setChecked(file_info['path'] in self.selected_files)
            checkbox.stateChanged.connect(lambda s, p=file_info['path']: self._on_list_selection_changed(p, s))
            check_layout.addWidget(checkbox)
            check_layout.setAlignment(Qt.AlignCenter)
            self.list_table.setCellWidget(row, 0, check_widget)

            self.list_table.setItem(row, 1, QTableWidgetItem(file_info['name']))
            self.list_table.setItem(row, 2, QTableWidgetItem("照片" if file_info['type'] == 'photo' else "视频"))
            self.list_table.setItem(row, 3, QTableWidgetItem(self.service.format_size(file_info['size'])))
            self.list_table.setItem(row, 4, QTableWidgetItem(file_info['modified']))
            self.list_table.setItem(row, 5, QTableWidgetItem("有" if file_info['has_gps'] else "无"))
            self.list_table.setItem(row, 6, QTableWidgetItem(file_info['path']))

        header_h = self.list_table.horizontalHeader().height() + 4
        row_h = self.list_table.rowHeight(0) if filtered else 30
        total_h = header_h + len(filtered) * row_h + 4
        self.list_table.setMinimumHeight(total_h)
        self.list_table.setMaximumHeight(total_h)

    def _update_map_view(self):
        if not HAS_WEB_ENGINE or not self.map_widget or not self._root_node:
            return

        self.map_widget.clear_all()

        all_files = self._root_node.get_all_files()
        photo_geojson = self.service.build_photo_geojson(all_files)
        theme = self.theme_manager.get_current_theme()
        accent = theme.get('accent_color', '#6366f1')
        success_color = theme.get('success_color', '#10b981')
        if photo_geojson['features']:
            self.map_widget.load_geojson('photos', photo_geojson, accent)

        if self._match_result:
            f2_matched = self._match_result.get('fubiao2', {}).get('matched', [])
            if f2_matched:
                f2_features = self.service.build_fubiao_geojson(f2_matched, '附表2-桥涵')
                if f2_features['features']:
                    self.map_widget.load_geojson('fubiao2_markers', f2_features, accent)

            f3_matched = self._match_result.get('fubiao3', {}).get('matched', [])
            if f3_matched:
                f3_features = self.service.build_fubiao_geojson(f3_matched, '附表3-沟滩占地')
                if f3_features['features']:
                    self.map_widget.load_geojson('fubiao3_markers', f3_features, success_color)

        self.map_widget.fit_bounds()

    # ========== 选择操作 ==========

    def _select_all(self):
        """全选"""
        if not self._root_node:
            return

        all_files = [c.file_path for c in self._root_node.get_all_cards() if c.isVisible()]
        self.selected_files = set(all_files)

        for card in self._root_node.get_all_cards():
            if card.isVisible():
                card.set_selected(True)

        for row in range(self.list_table.rowCount()):
            check_widget = self.list_table.cellWidget(row, 0)
            if check_widget:
                checkbox = check_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(True)

        self._update_selected_count()
        self._update_batch_buttons()

    def _deselect_all(self):
        """取消全选"""
        self.selected_files.clear()

        if self._root_node:
            for card in self._root_node.get_all_cards():
                card.set_selected(False)

        for row in range(self.list_table.rowCount()):
            check_widget = self.list_table.cellWidget(row, 0)
            if check_widget:
                checkbox = check_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(False)

        self._update_selected_count()
        self._update_batch_buttons()

    def _on_card_clicked(self, file_path: str):
        """点击卡片 - 打开预览"""
        if not self._root_node:
            return

        all_files = self._root_node.get_all_files()
        previewable = [f['path'] for f in all_files if f['type'] == 'photo']
        index = previewable.index(file_path) if file_path in previewable else 0

        dialog = PhotoPreviewDialog(self)
        dialog.set_files(previewable, index)
        dialog.exec()

    def _on_card_selection_changed(self, file_path: str, selected: bool):
        if selected:
            self.selected_files.add(file_path)
        else:
            self.selected_files.discard(file_path)
        self._update_selected_count()
        self._update_batch_buttons()

    def _on_list_selection_changed(self, file_path: str, state: int):
        selected = state == Qt.Checked
        if selected:
            self.selected_files.add(file_path)
        else:
            self.selected_files.discard(file_path)

        if self._root_node:
            for card in self._root_node.get_all_cards():
                if card.file_path == file_path:
                    card.set_selected(selected)

        self._update_selected_count()
        self._update_batch_buttons()

    def _update_selected_count(self):
        count = len(self.selected_files)
        self.selected_label.setText(f"已选择 {count} 个" if count > 0 else "")

    def _update_batch_buttons(self):
        has_selection = len(self.selected_files) > 0
        self.rename_btn.setEnabled(has_selection)
        self.gps_btn.setEnabled(has_selection)

    # ========== 批量操作 ==========

    def _show_rename_dialog(self):
        if not self.selected_files:
            return

        dialog = BatchRenameDialog(len(self.selected_files), self)
        if dialog.exec():
            pattern = dialog.get_pattern()
            start_index = dialog.get_start_index()
            result = self.service.batch_rename(list(self.selected_files), pattern, start_index)
            self._log(f"重命名完成: 成功 {result['success']}")
            self._start_scan()

    def _on_zoom_changed(self, value):
        self._card_zoom = value
        scale = PhotoCard.ZOOM_SCALES[value - 1]
        PhotoCard._current_scale = scale
        self.zoom_label.setText(f"缩放 {scale:.1f}x")
        if self._root_node:
            self._root_node.update_zoom(scale)

    def _show_gps_on_map(self):
        self._switch_view("map")

    def _on_delete_folder_requested(self, folder_path: str):
        """删除文件夹请求"""
        dialog = DeleteConfirmDialog(folder_path, self)
        if dialog.exec():
            if self.service.delete_folder(folder_path):
                self._log(f"已删除: {folder_path}")
                self._start_scan()

    # ========== 清空 ==========

    def _clear_results(self):
        self.scan_result = None
        self.selected_files.clear()

        if self._root_node:
            self._root_node.deleteLater()
            self._root_node = None

        self.list_table.setRowCount(0)

        if HAS_WEB_ENGINE and self.map_widget:
            self.map_widget.clear_all()

        self.badge_photos._value_label.setText("--")
        self.badge_videos._value_label.setText("--")
        self.badge_size._value_label.setText("--")

        self.expand_all_btn.setEnabled(False)
        self.collapse_all_btn.setEnabled(False)
        self.gps_btn.setEnabled(False)
        self.match_btn.setEnabled(False)
        self._update_selected_count()
        self._update_batch_buttons()

    def _log(self, msg: str):
        self.log_message.emit(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    # ========== 附表校验 ==========

    def _run_photo_match(self):
        if not self.folder_path:
            QMessageBox.warning(self, "警告", "请先扫描文件夹")
            return

        self.match_btn.setEnabled(False)
        self._log("开始附表与照片匹配校验...")

        self._match_thread = QThread()
        self._match_worker = MatchWorker(self.match_service, self.folder_path)
        self._match_worker.moveToThread(self._match_thread)
        self._match_thread.started.connect(self._match_worker.run)
        self._match_worker.finished.connect(self._on_match_worker_finished)
        self._match_worker.progress.connect(self._on_match_progress)
        self._match_worker.error.connect(self._on_match_error)
        self._match_thread.start()

    def _on_match_progress(self, msg: str):
        self._log(msg)

    def _on_match_error(self, msg: str):
        self._log(f"校验错误: {msg}")
        self.match_btn.setEnabled(True)

    def _on_match_worker_finished(self, result: dict):
        if hasattr(self, '_match_thread') and self._match_thread:
            self._match_thread.quit()
            self._match_thread.wait()
        self.match_btn.setEnabled(True)
        if result:
            self._match_result = result
            self._show_match_report(result)
            if self.current_view == 'map':
                self._update_map_view()

    def _on_map_photo_clicked(self, photo_path: str):
        if not photo_path or not os.path.exists(photo_path):
            return

        folder = os.path.dirname(photo_path)
        photos = self.service.get_folder_photos(folder)

        if not photos:
            photos = [photo_path]

        try:
            index = photos.index(photo_path)
        except ValueError:
            index = 0

        dialog = PhotoPreviewDialog(self)
        dialog.set_files(photos, index)
        dialog.exec()

    def _show_match_report(self, result: dict):
        summary = result.get('summary', {})
        f2_unmatched = summary.get('fubiao2_unmatched', 0)
        f3_unmatched = summary.get('fubiao3_unmatched', 0)
        photo_unmatched = summary.get('photo_unmatched_f2', 0) + summary.get('photo_unmatched_f3', 0)

        if f2_unmatched == 0 and f3_unmatched == 0 and photo_unmatched == 0:
            self._log("✅ 附表与照片匹配校验通过：所有记录均已匹配")

        dialog = PhotoMatchReportDialog(result, self)
        dialog.exec()