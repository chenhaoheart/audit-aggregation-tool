# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFileDialog, QFrame, QSizePolicy, QScrollArea
from PySide6.QtCore import Qt, Signal

from ui.pages.photo_gallery.header import GalleryHeader
from ui.pages.photo_gallery.toolbar import GalleryToolbar
from ui.pages.photo_gallery.content_area import GalleryContentArea
from controllers.photo_gallery_controller import PhotoGalleryController
from ui.components.photo_card import PhotoCard
from ui.components.gis_map_widget import HAS_WEB_ENGINE
from core.theme_manager import get_theme_manager


class PhotoGalleryPage(QWidget):

    log_message = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.theme_manager = get_theme_manager()
        self._accent_color = self.theme_manager.get_current_theme().get('accent_color', '#6366f1')

        self.controller = PhotoGalleryController(parent_widget=self)
        self._connect_controller_signals()

        self.theme_manager.theme_changed.connect(self._on_theme_changed)

        self._init_ui()
        self._connect_view_signals()

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

    def _connect_view_signals(self):
        tb = self.toolbar
        tb.browse_clicked.connect(self._select_folder)
        tb.scan_clicked.connect(self._start_scan)
        tb.match_clicked.connect(self._run_photo_match)
        tb.select_all_clicked.connect(self._select_all)
        tb.deselect_all_clicked.connect(self._deselect_all)
        tb.expand_all_clicked.connect(self.controller.expand_all)
        tb.collapse_all_clicked.connect(self.controller.collapse_all)
        tb.rename_clicked.connect(self._show_rename_dialog)
        tb.gps_clicked.connect(self._show_gps_on_map)
        tb.search_changed.connect(self.controller.on_search_changed)
        tb.type_filter_changed.connect(self.controller.on_type_filter_changed)
        tb.zoom_changed.connect(self._on_zoom_changed)
        tb.columns_changed.connect(self.controller.set_grid_columns)
        tb.view_switched.connect(self.controller.switch_view)

        self.content_area.list_selection_changed.connect(self.controller.on_list_selection_changed)
        self.content_area.photo_clicked_on_map.connect(self.controller.on_map_photo_clicked)

    def _on_theme_changed(self, mode: str):
        theme = self.theme_manager.get_current_theme()
        self._accent_color = theme.get('accent_color', '#6366f1')
        self.header.update_theme_colors()
        self._update_tree_theme_colors()
        self.content_area.update_list_theme()

        if self.controller.current_view == 'map' and HAS_WEB_ENGINE and self.content_area.map_widget:
            self._refresh_map_view()

    def _update_tree_theme_colors(self):
        root_node = self.controller.get_root_node()
        if root_node:
            self._apply_tree_colors(root_node, self._accent_color)

    def _apply_tree_colors(self, node, accent: str):
        if node is None:
            return
        theme = self.theme_manager.get_current_theme()
        hover_bg = theme.get('surface_1', theme.get('content_bg', '#f8f9fa'))
        hover_border = theme.get('border_subtle', theme.get('card_border', '#e2e8f0'))
        indent = node.depth * 16
        if hasattr(node, 'header'):
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
        if hasattr(node, '_update_arrow'):
            node._update_arrow()
        if hasattr(node, '_update_name_color'):
            node._update_name_color()
        for card in node._card_widgets:
            card._accent = accent
            card._apply_scale(PhotoCard._current_scale)
        for child in node._child_widgets:
            self._apply_tree_colors(child, accent)

    def _init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setSpacing(0)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setObjectName("photoGalleryScrollArea")
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        scroll_content = QWidget()
        scroll_content.setObjectName("cardInnerPanel")

        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        self.header = GalleryHeader(self)
        scroll_layout.addWidget(self.header)

        self.toolbar = GalleryToolbar(self)
        default_folder = r"D:\github\空间数据检查桌面版-主题-design-2026\青海24示范小流域-药草沟-20260313\630121_大通"
        self.toolbar.set_folder_path(default_folder)
        scroll_layout.addWidget(self.toolbar)

        self.content_area = GalleryContentArea(self)
        self.content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        scroll_layout.addWidget(self.content_area)

        scroll.setWidget(scroll_content)
        outer_layout.addWidget(scroll, 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.controller.current_view == "map":
            self._apply_map_large_height()

    def _apply_map_large_height(self):
        header_h = self.header.height() if self.header else 60
        toolbar_h = self.toolbar.height() if self.toolbar else 140
        self.content_area.set_map_large_height(header_h, toolbar_h)

    def _restore_map_size(self):
        self.content_area.restore_map_size()

    # ========== 用户交互 -> 委托给Controller ==========

    def _select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.toolbar.set_folder_path(folder)
            self.controller.select_folder(folder)

    def _start_scan(self):
        path = self.toolbar.get_folder_path()
        self.controller.start_scan(path)

    def _run_photo_match(self):
        self.controller.run_photo_match()

    def _select_all(self):
        self.controller.select_all()
        self.content_area.set_all_list_checkboxes(True)

    def _deselect_all(self):
        self.controller.deselect_all()
        self.content_area.set_all_list_checkboxes(False)

    def _show_rename_dialog(self):
        if self.controller.show_rename_dialog():
            self._start_scan()

    def _show_gps_on_map(self):
        self.controller.switch_view("map")

    def _on_zoom_changed(self, value):
        self.controller._card_zoom = value
        scale = PhotoCard.ZOOM_SCALES[value - 1]
        PhotoCard._current_scale = scale
        self.toolbar.update_zoom_label(scale)
        root_node = self.controller.get_root_node()
        if root_node:
            root_node.update_zoom(scale)

    # ========== Controller信号 -> 更新UI ==========

    def _on_scan_started(self):
        self.toolbar.set_scan_loading(True)

    def _on_scan_finished(self, result: dict):
        self.toolbar.set_scan_loading(False)

        self.header.update_stats(
            str(result['total_photos']),
            str(result['total_videos']),
            f"{result['total_size_mb']}MB"
        )

        tree_data = self.controller.get_tree_data(result)
        root_node = self.controller.build_tree(tree_data)
        self.content_area.set_tree_widget(root_node)

        self.toolbar.set_expand_collapse_enabled(True)
        self.toolbar.set_gps_enabled(result['total_photos'] > 0)
        self.toolbar.set_match_enabled(result['total_photos'] > 0)

        if self.controller.current_view == 'map':
            self._refresh_map_view()
        else:
            self.content_area.show_tree()

    def _on_scan_error(self, msg: str):
        self.toolbar.set_scan_loading(False)

    def _on_match_started(self):
        self.toolbar.set_match_enabled(False)

    def _on_match_finished(self, result: dict):
        self.toolbar.set_match_enabled(True)
        if self.controller.current_view == 'map':
            self._refresh_map_view()

    def _on_match_error(self, msg: str):
        self.toolbar.set_match_enabled(True)

    def _on_selection_count_changed(self, count: int):
        self.toolbar.update_selection_label(count)
        has_selection = count > 0
        self.toolbar.set_rename_enabled(has_selection)
        self.toolbar.set_gps_enabled(has_selection)

    def _on_view_changed(self, view: str):
        self.toolbar.set_view_buttons(view)

        if view == "tree":
            self._restore_map_size()
            self.content_area.show_tree()
        elif view == "list":
            self._restore_map_size()
            self._refresh_list_view()
            self.content_area.show_list()
        elif view == "map":
            self._apply_map_large_height()
            self._refresh_map_view()
            self.content_area.show_map()

    def _on_tree_rebuilt(self):
        self._update_selected_count()

    def _on_results_cleared(self):
        self.content_area.clear_all()
        self.header.reset_stats()
        self.toolbar.set_expand_collapse_enabled(False)
        self.toolbar.set_gps_enabled(False)
        self.toolbar.set_match_enabled(False)
        self._update_selected_count()

    def _update_selected_count(self):
        count = self.controller.update_selected_count()
        self.toolbar.update_selection_label(count)
        has_selection = count > 0
        self.toolbar.set_rename_enabled(has_selection)
        self.toolbar.set_gps_enabled(has_selection)

    def _refresh_list_view(self):
        files = self.controller.get_filtered_files()
        self.content_area.populate_list(
            files,
            self.controller.selected_files,
            self.controller.format_file_size
        )

    def _refresh_map_view(self):
        map_data = self.controller.get_map_data()
        if map_data:
            self.content_area.update_map(
                photo_geojson=map_data.get('photo_geojson'),
                fubiao2_geojson=map_data.get('fubiao2_geojson'),
                fubiao3_geojson=map_data.get('fubiao3_geojson'),
                accent=map_data.get('accent', '#6366f1'),
                success_color=map_data.get('success_color', '#10b981')
            )
