# -*- coding: utf-8 -*-
"""
图册管理页面控制器

职责:
- 扫描流程控制（启动扫描、进度回调、完成/错误处理）
- 附表校验流程控制（启动校验、线程管理、结果处理）
- 选择状态管理（全选/取消/选中计数）
- 视图切换逻辑（树形/列表/地图）
- 过滤逻辑（搜索/类型过滤）
- 主题变更时UI更新协调
- 批量操作（重命名/删除）
- 地图视图数据构建
"""

import os
from datetime import datetime
from typing import Set, Optional, List

from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import QMessageBox, QCheckBox

from services.photo_gallery_service import PhotoGalleryService
from services.photo_match_service import PhotoMatchService, MatchWorker
from ui.components.gis_map_widget import HAS_WEB_ENGINE
from ui.components.photo_card import PhotoCard
from ui.components.tree_node_widget import TreeNodeWidget
from ui.dialogs.photo_preview_dialog import PhotoPreviewDialog
from ui.dialogs.batch_rename_dialog import BatchRenameDialog
from ui.dialogs.delete_confirm_dialog import DeleteConfirmDialog
from ui.dialogs.photo_match_report_dialog import PhotoMatchReportDialog
from core.theme_manager import get_theme_manager


class PhotoGalleryController(QObject):

    scan_started = Signal()
    scan_finished = Signal(dict)
    scan_progress = Signal(str)
    scan_error = Signal(str)
    match_started = Signal()
    match_finished = Signal(dict)
    match_progress = Signal(str)
    match_error = Signal(str)
    selection_changed = Signal(int)
    view_changed = Signal(str)
    log_message = Signal(str)
    tree_rebuilt = Signal()
    results_cleared = Signal()

    def __init__(self, page: 'PhotoGalleryPage', parent=None):
        super().__init__(parent)
        self._page = page
        self.service = PhotoGalleryService(self)
        self.match_service = PhotoMatchService(self)
        self.theme_manager = get_theme_manager()

        self.folder_path = ""
        self.scan_result = None
        self.selected_files: Set[str] = set()
        self.current_view = "tree"
        self.grid_columns = 4
        self.search_query = ""
        self.filter_type = "all"
        self._card_zoom = 5
        self._match_result = None
        self._match_thread = None
        self._match_worker = None
        self._root_node: Optional[TreeNodeWidget] = None

        self.service.scan_finished.connect(self._on_scan_finished)
        self.service.scan_progress.connect(self._on_scan_progress)
        self.service.error_occurred.connect(self._on_error)

        self.match_service.match_progress.connect(self._on_match_progress)
        self.match_service.match_error.connect(self._on_match_error)

    def _log(self, msg: str):
        self.log_message.emit(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def start_scan(self, path: str):
        if not path:
            QMessageBox.warning(self._page, "警告", "请输入或选择文件夹路径")
            return

        self.folder_path = path
        self.clear_results()

        self.scan_started.emit()
        self._log("开始扫描...")
        self.service.scan_folder(path, recursive=True)

    def _on_scan_progress(self, msg: str):
        self._log(msg)
        self.scan_progress.emit(msg)

    def _on_scan_finished(self, result: dict):
        self.scan_result = result
        self.scan_finished.emit(result)
        self._log(f"扫描完成: {result['total_photos']} 照片, {result['total_videos']} 视频")

    def _on_error(self, msg: str):
        self.scan_error.emit(msg)
        self._log(f"错误: {msg}")
        QMessageBox.critical(self._page, "错误", f"扫描失败:\n{msg}")

    def build_tree(self, tree_data: dict) -> TreeNodeWidget:
        accent = self.theme_manager.get_current_theme().get('accent_color', '#6366f1')
        root_node = TreeNodeWidget(tree_data, depth=0, grid_columns=self.grid_columns, accent=accent, parent=self._page)
        root_node.expand_changed.connect(lambda: None)
        root_node.delete_requested.connect(self._on_delete_folder_requested)

        for card in root_node.get_all_cards():
            card.clicked.connect(self._on_card_clicked)
            card.selection_changed.connect(self._on_card_selection_changed)

        self._root_node = root_node
        self.tree_rebuilt.emit()
        return root_node

    def get_root_node(self) -> Optional[TreeNodeWidget]:
        return self._root_node

    def set_root_node(self, node: Optional[TreeNodeWidget]):
        self._root_node = node

    def select_folder(self, folder: str):
        self.folder_path = folder

    def expand_all(self):
        if self._root_node:
            self._root_node.expand_all()

    def collapse_all(self):
        if self._root_node:
            self._root_node.collapse_all()

    def set_grid_columns(self, columns: int):
        self.grid_columns = columns
        if self._root_node:
            self._root_node.set_grid_columns(columns)

    def on_search_changed(self, text: str):
        self.search_query = text.lower()
        self.apply_filters()

    def on_type_filter_changed(self, index: int):
        self.filter_type = ["all", "photo", "video"][index]
        self.apply_filters()

    def apply_filters(self):
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

    def switch_view(self, view: str):
        self.current_view = view
        self.view_changed.emit(view)

    def select_all(self):
        if not self._root_node:
            return

        all_files = [c.file_path for c in self._root_node.get_all_cards() if c.isVisible()]
        self.selected_files = set(all_files)

        for card in self._root_node.get_all_cards():
            if card.isVisible():
                card.set_selected(True)

        self.selection_changed.emit(len(self.selected_files))

    def deselect_all(self):
        self.selected_files.clear()

        if self._root_node:
            for card in self._root_node.get_all_cards():
                card.set_selected(False)

        self.selection_changed.emit(0)

    def _on_card_clicked(self, file_path: str):
        if not self._root_node:
            return

        all_files = self._root_node.get_all_files()
        previewable = [f['path'] for f in all_files if f['type'] == 'photo']
        index = previewable.index(file_path) if file_path in previewable else 0

        dialog = PhotoPreviewDialog(self._page)
        dialog.set_files(previewable, index)
        dialog.exec()

    def _on_card_selection_changed(self, file_path: str, selected: bool):
        if selected:
            self.selected_files.add(file_path)
        else:
            self.selected_files.discard(file_path)
        self.selection_changed.emit(len(self.selected_files))

    def on_list_selection_changed(self, file_path: str, state, list_table):
        from PySide6.QtCore import Qt
        selected = state == Qt.Checked
        if selected:
            self.selected_files.add(file_path)
        else:
            self.selected_files.discard(file_path)

        if self._root_node:
            for card in self._root_node.get_all_cards():
                if card.file_path == file_path:
                    card.set_selected(selected)

        self.selection_changed.emit(len(self.selected_files))

    def update_list_selection(self, list_table, select_all: bool = True):
        for row in range(list_table.rowCount()):
            check_widget = list_table.cellWidget(row, 0)
            if check_widget:
                checkbox = check_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(select_all)

    def update_selected_count(self) -> int:
        return len(self.selected_files)

    def has_selection(self) -> bool:
        return len(self.selected_files) > 0

    def show_rename_dialog(self):
        if not self.selected_files:
            return

        dialog = BatchRenameDialog(len(self.selected_files), self._page)
        if dialog.exec():
            pattern = dialog.get_pattern()
            start_index = dialog.get_start_index()
            result = self.service.batch_rename(list(self.selected_files), pattern, start_index)
            self._log(f"重命名完成: 成功 {result['success']}")
            return True
        return False

    def _on_delete_folder_requested(self, folder_path: str):
        dialog = DeleteConfirmDialog(folder_path, self._page)
        if dialog.exec():
            if self.service.delete_folder(folder_path):
                self._log(f"已删除: {folder_path}")
                return True
        return False

    def run_photo_match(self):
        if not self.folder_path:
            QMessageBox.warning(self._page, "警告", "请先扫描文件夹")
            return

        self.match_started.emit()
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
        self.match_progress.emit(msg)

    def _on_match_error(self, msg: str):
        self._log(f"校验错误: {msg}")
        self.match_error.emit(msg)

    def _on_match_worker_finished(self, result: dict):
        if self._match_thread and self._match_thread:
            self._match_thread.quit()
            self._match_thread.wait()
        if result:
            self._match_result = result
            self._show_match_report(result)
            self.match_finished.emit(result)

    def _show_match_report(self, result: dict):
        summary = result.get('summary', {})
        f2_unmatched = summary.get('fubiao2_unmatched', 0)
        f3_unmatched = summary.get('fubiao3_unmatched', 0)
        photo_unmatched = summary.get('photo_unmatched_f2', 0) + summary.get('photo_unmatched_f3', 0)

        if f2_unmatched == 0 and f3_unmatched == 0 and photo_unmatched == 0:
            self._log("✅ 附表与照片匹配校验通过：所有记录均已匹配")

        dialog = PhotoMatchReportDialog(result, self._page)
        dialog.exec()

    def on_map_photo_clicked(self, photo_path: str):
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

        dialog = PhotoPreviewDialog(self._page)
        dialog.set_files(photos, index)
        dialog.exec()

    def update_map_view(self, map_widget):
        if not HAS_WEB_ENGINE or not map_widget or not self._root_node:
            return

        map_widget.clear_all()

        all_files = self._root_node.get_all_files()
        photo_geojson = self.service.build_photo_geojson(all_files)
        theme = self.theme_manager.get_current_theme()
        accent = theme.get('accent_color', '#6366f1')
        success_color = theme.get('success_color', '#10b981')
        if photo_geojson['features']:
            map_widget.load_geojson('photos', photo_geojson, accent)

        if self._match_result:
            f2_matched = self._match_result.get('fubiao2', {}).get('matched', [])
            if f2_matched:
                f2_features = self.service.build_fubiao_geojson(f2_matched, '附表2-桥涵')
                if f2_features['features']:
                    map_widget.load_geojson('fubiao2_markers', f2_features, accent)

            f3_matched = self._match_result.get('fubiao3', {}).get('matched', [])
            if f3_matched:
                f3_features = self.service.build_fubiao_geojson(f3_matched, '附表3-沟滩占地')
                if f3_features['features']:
                    map_widget.load_geojson('fubiao3_markers', f3_features, success_color)

        map_widget.fit_bounds()

    def update_list_view(self, list_table):
        if not self._root_node:
            return

        all_files = self._root_node.get_all_files()
        filtered = [f for f in all_files if self.service.file_matches_filter(f, self.search_query, self.filter_type)]

        list_table.setRowCount(len(filtered))

        for row, file_info in enumerate(filtered):
            check_widget, checkbox = self._create_check_widget(file_info)
            list_table.setCellWidget(row, 0, check_widget)

            from PySide6.QtWidgets import QTableWidgetItem
            list_table.setItem(row, 1, QTableWidgetItem(file_info['name']))
            list_table.setItem(row, 2, QTableWidgetItem("照片" if file_info['type'] == 'photo' else "视频"))
            list_table.setItem(row, 3, QTableWidgetItem(self.service.format_size(file_info['size'])))
            list_table.setItem(row, 4, QTableWidgetItem(file_info['modified']))
            list_table.setItem(row, 5, QTableWidgetItem("有" if file_info['has_gps'] else "无"))
            list_table.setItem(row, 6, QTableWidgetItem(file_info['path']))

        header_h = list_table.horizontalHeader().height() + 4
        row_h = list_table.rowHeight(0) if filtered else 30
        total_h = header_h + len(filtered) * row_h + 4
        list_table.setMinimumHeight(total_h)
        list_table.setMaximumHeight(total_h)

    def _create_check_widget(self, file_info: dict):
        from PySide6.QtWidgets import QWidget, QHBoxLayout
        from PySide6.QtCore import Qt

        check_widget = QWidget()
        check_layout = QHBoxLayout(check_widget)
        checkbox = QCheckBox()
        checkbox.setChecked(file_info['path'] in self.selected_files)
        checkbox.stateChanged.connect(lambda s, p=file_info['path']: self.on_list_selection_changed(p, s, None))
        check_layout.addWidget(checkbox)
        check_layout.setAlignment(Qt.AlignCenter)
        return check_widget, checkbox

    def update_theme_colors(self):
        theme = self.theme_manager.get_current_theme()
        accent = theme.get('accent_color', '#6366f1')

        if self._root_node:
            self._update_tree_colors(self._root_node, accent)

    def _update_tree_colors(self, node: TreeNodeWidget, accent: str):
        node._accent = accent
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
        if hasattr(node, '_update_arrow'):
            node._update_arrow()
        for card in node._card_widgets:
            card._accent = accent
            card._apply_scale(PhotoCard._current_scale)
        for child in node._child_widgets:
            self._update_tree_colors(child, accent)

    def clear_results(self):
        self.scan_result = None
        self.selected_files.clear()
        self._root_node = None
        self.results_cleared.emit()

    def get_match_result(self):
        return self._match_result
