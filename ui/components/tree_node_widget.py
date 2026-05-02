# -*- coding: utf-8 -*-
"""
树节点组件 - 可展开/折叠，展开后显示子节点和文件网格

职责:
- 文件夹节点的展开/折叠交互
- 子节点和文件网格的布局管理
- 展开/折叠动画
- 缩放和列数调整
"""

from typing import List

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QWidget, QGridLayout,
    QLabel, QToolButton, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor

from core.theme_manager import get_theme_manager, ThemeGroup
from ui.components.photo_card import PhotoCard


class TreeNodeWidget(QFrame):

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

        if self.depth <= 1:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(8)
            shadow.setColor(QColor(0, 0, 0, 15))
            shadow.setOffset(0, 2)
            self.header.setGraphicsEffect(shadow)

        header_layout = QHBoxLayout(self.header)
        header_layout.setSpacing(10)

        color_bar = QFrame()
        color_bar.setStyleSheet(f"""
            QFrame {{
                background: {self._accent};
                border-radius: 2px;
            }}
        """)
        color_bar.setFixedSize(3, 16)
        header_layout.addWidget(color_bar, 0, Qt.AlignVCenter)

        self.arrow_btn = QToolButton()
        self.arrow_btn.setFixedSize(18, 18)
        self.arrow_btn.setCursor(Qt.PointingHandCursor)
        self._update_arrow()
        self.arrow_btn.clicked.connect(self.toggle_expand)
        header_layout.addWidget(self.arrow_btn, 0, Qt.AlignVCenter)

        folder_icon = QLabel("📁")
        folder_icon.setStyleSheet(f"font-size: 16px;")
        header_layout.addWidget(folder_icon, 0, Qt.AlignVCenter)

        name = self.node_data.get('name', '')
        path = self.node_data.get('path', '')
        is_root = self.node_data.get('isRoot', False)

        self.name_label = QLabel(path if is_root else name)
        self.name_label.setObjectName("treeNodeName")
        self._update_name_color()
        self.name_label.setToolTip(path)
        header_layout.addWidget(self.name_label, 1, Qt.AlignVCenter)

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

        self.children_container = QWidget()
        self.children_container.setObjectName("treeChildren")
        children_layout = QVBoxLayout(self.children_container)
        children_layout.setSpacing(2)
        children_layout.setContentsMargins(0, 4, 0, 4)

        children = self.node_data.get('children', {})
        for child_name, child_data in sorted(children.items()):
            child_widget = TreeNodeWidget(child_data, self.depth + 1, self.grid_columns, self._accent, self)
            child_widget.expand_changed.connect(self.expand_changed)
            child_widget.delete_requested.connect(self.delete_requested)
            children_layout.addWidget(child_widget)
            self._child_widgets.append(child_widget)

        files = self.node_data.get('files', [])
        if files:
            self.files_grid = QWidget()
            grid_layout = QGridLayout(self.files_grid)
            grid_layout.setSpacing(8)
            grid_layout.setContentsMargins(0, 8, 0, 8)

            for i, file_info in enumerate(files):
                card = PhotoCard(file_info, self._accent, self)
                card.clicked.connect(lambda path: None)
                card.selection_changed.connect(lambda path, sel: None)
                row = i // self.grid_columns
                col = i % self.grid_columns
                grid_layout.addWidget(card, row, col)
                self._card_widgets.append(card)

            children_layout.addWidget(self.files_grid)

        self.children_container.setVisible(self._expanded)
        layout.addWidget(self.children_container)

    def _update_arrow(self):
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

    def _update_name_color(self):
        if not hasattr(self, 'name_label'):
            return
        theme = self._theme_manager.get_current_theme()
        text_color = theme.get('text_primary', '#334155')
        self.name_label.setStyleSheet(f"""
            QLabel#treeNodeName {{
                font-weight: 600;
                font-size: 13px;
                color: {text_color};
            }}
        """)

    def toggle_expand(self):
        self._expanded = not self._expanded
        self._update_arrow()

        self.children_container.setVisible(True)

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
            self.children_container.setMaximumHeight(16777215)
            target_height = self.children_container.sizeHint().height()
            self.children_container.setMaximumHeight(0)
            self._animation.setStartValue(0)
            self._animation.setEndValue(max(target_height, 100))
            self._animation.finished.connect(self._on_expand_finished)
        else:
            current_height = self.children_container.height()
            self._animation.setStartValue(current_height)
            self._animation.setEndValue(0)
            self._animation.finished.connect(self._on_collapse_finished)

        self._animation.start()
        self.expand_changed.emit()

    def _on_expand_finished(self):
        self.children_container.setMaximumHeight(16777215)
        self._notify_parent_layout_update()

    def _on_collapse_finished(self):
        self.children_container.setVisible(False)
        self.children_container.setMaximumHeight(0)
        self._notify_parent_layout_update()

    def _notify_parent_layout_update(self):
        self.updateGeometry()
        parent = self.parentWidget()
        while parent:
            parent.updateGeometry()
            if parent.objectName() == "treeContainer":
                break
            parent = parent.parentWidget()

    def expand_all(self):
        self._expanded = True
        self._update_arrow()
        self.children_container.setVisible(True)
        self.children_container.setMaximumHeight(16777215)
        for child in self._child_widgets:
            child.expand_all()

    def collapse_all(self):
        if self.depth > 0:
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
        cards = self._card_widgets.copy()
        for child in self._child_widgets:
            cards.extend(child.get_all_cards())
        return cards

    def get_all_files(self) -> List[dict]:
        files = [c.file_info for c in self._card_widgets]
        for child in self._child_widgets:
            files.extend(child.get_all_files())
        return files
