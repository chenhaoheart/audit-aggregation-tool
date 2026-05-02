# -*- coding: utf-8 -*-
"""
图册管理页面 - UI层

职责:
- 页面UI布局和组件初始化
- 将用户交互委托给Controller处理
- 响应Controller信号更新UI状态

核心特点:
- 树形导航与文件卡片一体化 (展开后文件网格嵌入在节点下方)
- 单一滚动容器包含整个树+文件结构
- 可配置网格列数 (2-10列)
- 支持树形视图和平铺Grid视图切换
- 文件夹统计、删除按钮(hover显示)
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QFrame, QScrollArea, QStackedWidget, QSizePolicy,
    QGridLayout, QCheckBox, QMessageBox, QAbstractItemView, QComboBox,
    QSpinBox, QToolButton, QSlider
)
from PySide6.QtCore import Qt, Signal

from services.photo_gallery_controller import PhotoGalleryController
from ui.components.gis_map_widget import GisMapWidget, HAS_WEB_ENGINE
from ui.components.photo_card import PhotoCard
from ui.components.tree_node_widget import TreeNodeWidget
from core.theme_manager import get_theme_manager
from core.effects_manager import ShimmerProgress, ButtonGlowHelper


class PhotoGalleryPage(QWidget):

    log_message = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.theme_manager = get_theme_manager()
        self._accent_color = self.theme_manager.get_current_theme().get('accent_color', '#6366f1')

        self.controller = PhotoGalleryController(self)
        self._connect_controller_signals()

        self.theme_manager.theme_changed.connect(self._on_theme_changed)

        self._init_ui()

    def _connect_controller_signals(self):
        c = self.controller
        c.scan_started.connect(self._on_scan_started)
        c.scan_finished.connect(self._on_scan_finished)
        c.scan_error.connect(self._on_scan_error)
        c.match_started.connect(self._on_match_started)
        c.match_finished.connect(self._on_match_finished)
        c.match_error.connect(self._on_match_error)
        c.selection_changed.connect(self._on_selection_count_changed)
        c.view_changed.connect(self._on_view_changed)
        c.log_message.connect(self.log_message.emit)
        c.tree_rebuilt.connect(self._on_tree_rebuilt)
        c.results_cleared.connect(self._on_results_cleared)

    def _on_theme_changed(self, mode: str):
        theme = self.theme_manager.get_current_theme()
        self._accent_color = theme.get('accent_color', '#6366f1')

        if hasattr(self, 'badge_photos'):
            self._update_badge_color(self.badge_photos, self._accent_color)
        if hasattr(self, 'badge_videos'):
            self._update_badge_color(self.badge_videos, theme.get('info_text', '#8b5cf6'))
        if hasattr(self, 'badge_size'):
            self._update_badge_color(self.badge_size, theme.get('warning_text', '#f59e0b'))

        self.controller.update_theme_colors()

        if self.controller.current_view == 'map' and hasattr(self, 'map_widget') and self.map_widget:
            self.controller.update_map_view(self.map_widget)

    def _update_badge_color(self, badge: QFrame, color: str):
        if hasattr(badge, '_value_label'):
            badge._value_label.setStyleSheet(f"color: {color}; font-weight: 700; font-size: 14px;")
        if hasattr(badge, '_label_label'):
            badge._label_label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 500;")

    def _init_ui(self):
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

        self._build_header(scroll_layout)
        self._build_toolbar(scroll_layout)
        self._build_content_area(scroll_layout)

        self.main_scroll.setWidget(scroll_content)
        outer_layout.addWidget(self.main_scroll)

    def _build_header(self, parent_layout):
        theme = self.theme_manager.get_current_theme()
        accent = theme.get('accent_color', '#6366f1')

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

        parent_layout.addWidget(self.header_card)

    def _build_toolbar(self, parent_layout):
        theme = self.theme_manager.get_current_theme()

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

        self._build_toolbar_row1(toolbar_layout)
        self._build_toolbar_row2(toolbar_layout)

        parent_layout.addWidget(self.toolbar_card)

    def _build_toolbar_row1(self, parent_layout):
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

        parent_layout.addLayout(toolbar_row1)

    def _build_toolbar_row2(self, parent_layout):
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

        parent_layout.addLayout(toolbar_row2)

    def _build_content_area(self, parent_layout):
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("QStackedWidget { background: transparent; }")

        self._build_tree_container()
        self._build_list_view()
        self._build_map_container()
        self._build_empty_widget()

        parent_layout.addWidget(self.content_stack)

    def _build_tree_container(self):
        self.tree_container = QWidget()
        self.tree_container.setObjectName("treeContainer")
        self.tree_container.setStyleSheet("QWidget#treeContainer { background: transparent; }")
        self.tree_container_layout = QVBoxLayout(self.tree_container)
        self.tree_container_layout.setSpacing(0)
        self.tree_container_layout.setContentsMargins(12, 4, 12, 12)
        self.tree_container_layout.setAlignment(Qt.AlignTop)
        self.content_stack.addWidget(self.tree_container)

    def _build_list_view(self):
        theme = self.theme_manager.get_current_theme()
        card_bg = theme.get('card_bg', '#ffffff')
        border_subtle = theme.get('border_subtle', theme.get('card_border', '#e2e8f0'))
        surface_1 = theme.get('surface_1', '#f8fafc')
        text_primary = theme.get('text_primary', '#334155')
        text_muted = theme.get('text_muted', '#64748b')

        self.list_view = QWidget()
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
        self.content_stack.addWidget(self.list_view)

    def _build_map_container(self):
        if HAS_WEB_ENGINE:
            self.map_container = QWidget()
            map_container_layout = QVBoxLayout(self.map_container)
            map_container_layout.setContentsMargins(8, 4, 8, 8)
            map_container_layout.setSpacing(0)
            map_container_layout.setAlignment(Qt.AlignTop)

            self.map_widget = GisMapWidget(self)
            self.map_widget.setMinimumHeight(400)
            self.map_widget.photo_clicked.connect(self.controller.on_map_photo_clicked)
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

    def _build_empty_widget(self):
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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.controller.current_view == "map":
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
        theme = self.theme_manager.get_current_theme()
        sep = QFrame()
        sep.setStyleSheet(f"background: {theme.get('divider_color', '#e2e8f0')}; margin: 0 8px;")
        sep.setFixedWidth(1)
        sep.setFixedHeight(16)
        return sep

    # ========== 用户交互 -> 委托给Controller ==========

    def _select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.folder_edit.setText(folder)
            self.controller.select_folder(folder)

    def _start_scan(self):
        path = self.folder_edit.text().strip()
        self.controller.start_scan(path)

    def _run_photo_match(self):
        self.controller.run_photo_match()

    def _select_all(self):
        self.controller.select_all()
        self.controller.update_list_selection(self.list_table, select_all=True)

    def _deselect_all(self):
        self.controller.deselect_all()
        self.controller.update_list_selection(self.list_table, select_all=False)

    def _expand_all_tree(self):
        self.controller.expand_all()

    def _collapse_all_tree(self):
        self.controller.collapse_all()

    def _show_rename_dialog(self):
        if self.controller.show_rename_dialog():
            self._start_scan()

    def _show_gps_on_map(self):
        self._switch_view("map")

    def _on_search_changed(self, text: str):
        self.controller.on_search_changed(text)

    def _on_type_filter_changed(self, index: int):
        self.controller.on_type_filter_changed(index)

    def _on_columns_changed(self, columns: int):
        self.controller.set_grid_columns(columns)

    def _on_zoom_changed(self, value):
        self.controller._card_zoom = value
        scale = PhotoCard.ZOOM_SCALES[value - 1]
        PhotoCard._current_scale = scale
        self.zoom_label.setText(f"缩放 {scale:.1f}x")
        root_node = self.controller.get_root_node()
        if root_node:
            root_node.update_zoom(scale)

    def _switch_view(self, view: str):
        self.controller.switch_view(view)

    # ========== Controller信号 -> 更新UI ==========

    def _on_scan_started(self):
        self.scan_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self._progress_shimmer.start()

    def _on_scan_finished(self, result: dict):
        self._progress_shimmer.stop()
        self.progress_bar.setVisible(False)
        self.scan_btn.setEnabled(True)

        self.badge_photos._value_label.setText(str(result['total_photos']))
        self.badge_videos._value_label.setText(str(result['total_videos']))
        self.badge_size._value_label.setText(f"{result['total_size_mb']}MB")

        tree_data = self.controller.service.build_tree_structure(result)
        self._build_tree_view(tree_data)

        self.expand_all_btn.setEnabled(True)
        self.collapse_all_btn.setEnabled(True)
        self.gps_btn.setEnabled(result['total_photos'] > 0)
        self.match_btn.setEnabled(result['total_photos'] > 0)

        if self.controller.current_view == 'map':
            self.controller.update_map_view(self.map_widget)
        else:
            self.content_stack.setCurrentIndex(0)

    def _on_scan_error(self, msg: str):
        self._progress_shimmer.stop()
        self.progress_bar.setVisible(False)
        self.scan_btn.setEnabled(True)

    def _on_match_started(self):
        self.match_btn.setEnabled(False)

    def _on_match_finished(self, result: dict):
        self.match_btn.setEnabled(True)
        if self.controller.current_view == 'map':
            self.controller.update_map_view(self.map_widget)

    def _on_match_error(self, msg: str):
        self.match_btn.setEnabled(True)

    def _on_selection_count_changed(self, count: int):
        self.selected_label.setText(f"已选择 {count} 个" if count > 0 else "")
        has_selection = count > 0
        self.rename_btn.setEnabled(has_selection)
        self.gps_btn.setEnabled(has_selection)

    def _on_view_changed(self, view: str):
        self.tree_btn.setChecked(view == "tree")
        self.list_btn.setChecked(view == "list")
        self.map_btn.setChecked(view == "map")

        self.col_spin.setEnabled(view == "tree")

        if view == "tree":
            self._restore_map_size()
            self.content_stack.setCurrentIndex(0)
        elif view == "list":
            self._restore_map_size()
            self.controller.update_list_view(self.list_table)
            self.content_stack.setCurrentIndex(1)
        elif view == "map":
            self._apply_map_large_height()
            self.controller.update_map_view(self.map_widget)
            self.content_stack.setCurrentIndex(2)

    def _on_tree_rebuilt(self):
        self._update_selected_count()

    def _on_results_cleared(self):
        root_node = self.controller.get_root_node()
        if root_node:
            root_node.deleteLater()
        self.controller.set_root_node(None)

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

    def _build_tree_view(self, tree_data: dict):
        while self.tree_container_layout.count():
            item = self.tree_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        root_node = self.controller.build_tree(tree_data)
        self.tree_container_layout.insertWidget(0, root_node)
        self._update_selected_count()

    def _update_selected_count(self):
        count = self.controller.update_selected_count()
        self.selected_label.setText(f"已选择 {count} 个" if count > 0 else "")
        has_selection = count > 0
        self.rename_btn.setEnabled(has_selection)
        self.gps_btn.setEnabled(has_selection)
