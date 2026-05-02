# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QStackedWidget, QWidget, QVBoxLayout, QLabel,
    QTableWidget, QAbstractItemView, QCheckBox, QHBoxLayout,
    QSizePolicy, QFrame, QTableWidgetItem
)
from PySide6.QtCore import Qt, Signal
from ui.components.gis_map_widget import GisMapWidget, HAS_WEB_ENGINE
from core.theme_manager import get_theme_manager


class GalleryContentArea(QStackedWidget):

    photo_clicked_on_map = Signal(str)
    list_selection_changed = Signal(str, bool)

    IDX_TREE = 0
    IDX_LIST = 1
    IDX_MAP = 2
    IDX_EMPTY = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QStackedWidget { background: transparent; }")
        self.theme_manager = get_theme_manager()
        self._root_node = None
        self._init_ui()

    def _init_ui(self):
        self._build_tree_container()
        self._build_list_view()
        self._build_map_container()
        self._build_empty_widget()
        self.setCurrentIndex(self.IDX_EMPTY)

    def _build_tree_container(self):
        self.tree_container = QWidget()
        self.tree_container.setObjectName("treeContainer")
        self.tree_container.setStyleSheet("QWidget#treeContainer { background: transparent; }")
        self.tree_container_layout = QVBoxLayout(self.tree_container)
        self.tree_container_layout.setSpacing(0)
        self.tree_container_layout.setContentsMargins(12, 4, 12, 12)
        self.tree_container_layout.setAlignment(Qt.AlignTop)
        self.addWidget(self.tree_container)

    def _build_list_view(self):
        theme = self.theme_manager.get_current_theme()
        card_bg = theme.get('card_bg', '#ffffff')
        border_subtle = theme.get('border_subtle', theme.get('card_border', '#e2e8f0'))
        surface_1 = theme.get('surface_1', '#f8fafc')
        text_primary = theme.get('text_primary', '#334155')
        text_muted = theme.get('text_muted', '#64748b')

        self.list_view = QWidget()
        content_bg = theme.get('content_bg', '#f0f2f5')
        self.list_view.setStyleSheet(f"QWidget {{ background: {content_bg}; }}")
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
        self.addWidget(self.list_view)

    def _build_map_container(self):
        if HAS_WEB_ENGINE:
            self.map_container = QWidget()
            map_container_layout = QVBoxLayout(self.map_container)
            map_container_layout.setContentsMargins(8, 4, 8, 8)
            map_container_layout.setSpacing(0)
            map_container_layout.setAlignment(Qt.AlignTop)

            self.map_widget = GisMapWidget(self)
            self.map_widget.setMinimumHeight(400)
            self.map_widget.photo_clicked.connect(self.photo_clicked_on_map.emit)
            map_container_layout.addWidget(self.map_widget, 1)
            self.addWidget(self.map_container)
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

            self.addWidget(fallback)
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

        self.addWidget(self.empty_widget)

    def show_tree(self):
        self.setCurrentIndex(self.IDX_TREE)

    def show_list(self):
        self.setCurrentIndex(self.IDX_LIST)

    def show_map(self):
        self.setCurrentIndex(self.IDX_MAP)

    def show_empty(self):
        self.setCurrentIndex(self.IDX_EMPTY)

    def set_tree_widget(self, root_node):
        while self.tree_container_layout.count():
            item = self.tree_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._root_node = root_node
        if root_node:
            self.tree_container_layout.insertWidget(0, root_node)

    def clear_tree(self):
        if self._root_node:
            self._root_node.deleteLater()
            self._root_node = None
        while self.tree_container_layout.count():
            item = self.tree_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def clear_list(self):
        self.list_table.setRowCount(0)

    def update_list_theme(self):
        theme = self.theme_manager.get_current_theme()
        card_bg = theme.get('card_bg', '#ffffff')
        border_subtle = theme.get('border_subtle', theme.get('card_border', '#e2e8f0'))
        surface_1 = theme.get('surface_1', '#f8fafc')
        text_primary = theme.get('text_primary', '#334155')
        text_muted = theme.get('text_muted', '#64748b')
        content_bg = theme.get('content_bg', '#f0f2f5')

        self.list_view.setStyleSheet(f"QWidget {{ background: {content_bg}; }}")
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

    def clear_map(self):
        if HAS_WEB_ENGINE and self.map_widget:
            self.map_widget.clear_all()

    def clear_all(self):
        self.clear_tree()
        self.clear_list()
        self.clear_map()

    def populate_list(self, files: list, selected_files: set, format_size_func):
        self.list_table.setRowCount(len(files))

        for row, file_info in enumerate(files):
            check_widget = self._create_check_widget(file_info, selected_files)
            self.list_table.setCellWidget(row, 0, check_widget)

            self.list_table.setItem(row, 1, QTableWidgetItem(file_info['name']))
            self.list_table.setItem(row, 2, QTableWidgetItem("照片" if file_info['type'] == 'photo' else "视频"))
            self.list_table.setItem(row, 3, QTableWidgetItem(format_size_func(file_info['size'])))
            self.list_table.setItem(row, 4, QTableWidgetItem(file_info['modified']))
            self.list_table.setItem(row, 5, QTableWidgetItem("有" if file_info['has_gps'] else "无"))
            self.list_table.setItem(row, 6, QTableWidgetItem(file_info['path']))

        header_h = self.list_table.horizontalHeader().height() + 4
        row_h = self.list_table.rowHeight(0) if files else 30
        total_h = header_h + len(files) * row_h + 4
        self.list_table.setMinimumHeight(total_h)
        self.list_table.setMaximumHeight(total_h)

    def _create_check_widget(self, file_info: dict, selected_files: set):
        check_widget = QWidget()
        check_layout = QHBoxLayout(check_widget)
        checkbox = QCheckBox()
        checkbox.setChecked(file_info['path'] in selected_files)
        file_path = file_info['path']
        checkbox.stateChanged.connect(
            lambda state, p=file_path: self.list_selection_changed.emit(p, state == Qt.Checked)
        )
        check_layout.addWidget(checkbox)
        check_layout.setAlignment(Qt.AlignCenter)
        check_widget._checkbox = checkbox
        return check_widget

    def set_all_list_checkboxes(self, checked: bool):
        for row in range(self.list_table.rowCount()):
            check_widget = self.list_table.cellWidget(row, 0)
            if check_widget and hasattr(check_widget, '_checkbox'):
                check_widget._checkbox.setChecked(checked)

    def sync_list_selection(self, selected_files: set):
        for row in range(self.list_table.rowCount()):
            check_widget = self.list_table.cellWidget(row, 0)
            if check_widget and hasattr(check_widget, '_checkbox'):
                path_item = self.list_table.item(row, 6)
                if path_item:
                    check_widget._checkbox.setChecked(path_item.text() in selected_files)

    def update_map(self, photo_geojson: dict, fubiao2_geojson: dict = None,
                   fubiao3_geojson: dict = None, accent: str = '#6366f1',
                   success_color: str = '#10b981'):
        if not HAS_WEB_ENGINE or not self.map_widget:
            return

        self.map_widget.clear_all()

        if photo_geojson and photo_geojson.get('features'):
            self.map_widget.load_geojson('photos', photo_geojson, accent)

        if fubiao2_geojson and fubiao2_geojson.get('features'):
            self.map_widget.load_geojson('fubiao2_markers', fubiao2_geojson, accent)

        if fubiao3_geojson and fubiao3_geojson.get('features'):
            self.map_widget.load_geojson('fubiao3_markers', fubiao3_geojson, success_color)

        self.map_widget.fit_bounds()

    def set_map_large_height(self, header_height: int, toolbar_height: int):
        if not HAS_WEB_ENGINE or not self.map_widget:
            return
        window_h = self.window().height() if self.window() else 800
        top_h = header_height + toolbar_height
        available = int((window_h - top_h) * 0.95)
        map_h = max(600, available)
        self.map_widget.setMinimumHeight(map_h)
        self.map_widget.setMaximumHeight(map_h)

    def restore_map_size(self):
        if HAS_WEB_ENGINE and self.map_widget:
            self.map_widget.setMinimumHeight(400)
            self.map_widget.setMaximumHeight(16777215)

    def get_root_node(self):
        return self._root_node

    def set_root_node(self, node):
        self._root_node = node
