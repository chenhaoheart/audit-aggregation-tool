# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QScrollArea, QSizePolicy,
    QProgressBar, QTabWidget, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from ui.pages.check_shp.header import CheckHeader
from ui.pages.check_shp.layer_config import CheckLayerConfig
from ui.pages.check_shp.stats_card import CheckStatsCard
from controllers.check_controller import CheckController

from .summary_tab import SummaryTab
from .duanmian_tab import DuanmianTab
from .fangzhi_tab import FangzhiTab
from .yinhuan_tab import YinhuanTab
from .water_tab import WaterTab

from core.theme_manager import get_theme_manager
from core.effects_manager import ShimmerProgress, StaggerEntrance, TabFadeTransition


class CheckPage(QWidget):

    check_started = Signal()
    check_finished = Signal(dict)
    log_message = Signal(str)
    export_requested = Signal(dict)
    show_log_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.controller = CheckController(parent_widget=self)
        self._connect_controller_signals()

        self.theme_manager = get_theme_manager()

        self._init_ui()
        self._connect_view_signals()

        if self.layer_config.get_folder_path():
            self.controller.set_folder(self.layer_config.get_folder_path())
            self.controller.scan_folder()

    def _connect_controller_signals(self):
        c = self.controller
        c.check_started.connect(self._on_check_started)
        c.check_finished.connect(self._on_check_finished)
        c.check_progress.connect(lambda _: None)
        c.check_error.connect(self._on_check_error)
        c.scan_finished.connect(self._on_scan_finished)
        c.log_message.connect(self.log_message.emit)
        c.export_requested.connect(self.export_requested.emit)

    def _connect_view_signals(self):
        lc = self.layer_config
        lc.folder_selected.connect(self._on_folder_selected)
        lc.rescan_requested.connect(self._on_rescan)
        lc.layer_file_selected.connect(self._on_layer_file_selected)
        lc.start_clicked.connect(self._start_check)
        lc.clear_clicked.connect(self._clear_results)
        lc.gis_map_clicked.connect(self._open_gis_map_dialog)
        lc.export_clicked.connect(self._export_excel)
        lc.log_clicked.connect(lambda: self.show_log_requested.emit())

    def _init_ui(self):
        outer_layout = QVBoxLayout()
        outer_layout.setSpacing(0)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_content.setObjectName("cardInnerPanel")
        scroll_content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        self.header = CheckHeader(self)
        layout.addWidget(self.header)

        self.layer_config = CheckLayerConfig(self)
        layout.addWidget(self.layer_config)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(12)
        layout.addWidget(self.progress_bar)

        theme = self.theme_manager.get_current_theme()
        self._progress_shimmer = ShimmerProgress(self.progress_bar)
        self._progress_shimmer.set_colors(
            theme.get('progress_chunk_start', '#667eea'),
            theme.get('progress_chunk_end', '#764ba2'),
            "#ffffff30"
        )

        self.stats_card = CheckStatsCard(self)
        layout.addWidget(self.stats_card)

        self.tabs = QTabWidget()
        self.tabs.setMinimumHeight(400)

        self.summary_tab = SummaryTab()
        self.tabs.addTab(self.summary_tab, "汇总统计")

        self.duanmian_tab = DuanmianTab()
        self.tabs.addTab(self.duanmian_tab, "断面平面位置")

        self.fangzhi_tab = FangzhiTab()
        self.tabs.addTab(self.fangzhi_tab, "防治对象分布")

        self.yinhuan_tab = YinhuanTab()
        self.tabs.addTab(self.yinhuan_tab, "隐患要素分布")

        self.water_tab = WaterTab()
        self.tabs.addTab(self.water_tab, "水系数据")

        layout.addWidget(self.tabs)

        scroll_area.setWidget(scroll_content)
        outer_layout.addWidget(scroll_area, 1)

        self.setLayout(outer_layout)

        self._tab_fade = TabFadeTransition(self.tabs, duration=180)
        self._tab_fade.attach()

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, '_entrance_played'):
            self._entrance_played = True
            StaggerEntrance.play(self, stagger_ms=60, duration=320)

    # ========== 用户交互 -> 委托给Controller ==========

    def _on_folder_selected(self, path: str):
        self.controller.set_folder(path)
        self.controller.scan_folder()

    def _on_rescan(self):
        self.controller.scan_folder()

    def _on_layer_file_selected(self, layer_key: str, _placeholder: str):
        file = self.controller.select_layer_file(layer_key)
        if file:
            self.layer_config.select_layer_file(layer_key, file)
            if layer_key == 'water':
                self.controller.water_system_shp = file
            self.layer_config.update_start_button(bool(self.controller.folder_path))

    def _start_check(self):
        self.summary_tab.clear_data()
        self.duanmian_tab.clear_data()
        self.fangzhi_tab.clear_data()
        self.yinhuan_tab.clear_data()
        self.water_tab.clear_data()

        self.layer_config.set_start_enabled(False)
        self.layer_config.set_export_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self._progress_shimmer.start()

        water_shp = self.layer_config.get_water_shp()
        spatial_folder = self.controller.spatial_folder or self.controller.folder_path
        self.controller.start_check(spatial_folder, water_shp)

    def _export_excel(self):
        self.controller.export_excel()

    def _clear_results(self):
        self.controller.clear_results()
        self.layer_config.clear()
        self.stats_card.reset()
        self.summary_tab.clear_data()
        self.duanmian_tab.clear_data()
        self.fangzhi_tab.clear_data()
        self.yinhuan_tab.clear_data()
        self.water_tab.clear_data()

    def _open_gis_map_dialog(self):
        from ui.dialogs.gis_map_dialog import GisMapDialog
        if not hasattr(self, '_gis_dialog') or not self._gis_dialog:
            self._gis_dialog = GisMapDialog(self)
        self._gis_dialog.load_shp_from_check(
            self.controller.folder_path,
            self.controller.water_system_shp,
            self.controller.check_results
        )
        self._gis_dialog.show()

    # ========== Controller信号 -> 更新UI ==========

    def _on_scan_finished(self, scan_result: dict):
        self.layer_config.update_layer_table(scan_result)
        self.layer_config.update_start_button(bool(self.controller.folder_path))

    def _on_check_started(self):
        self.check_started.emit()

    def _on_check_finished(self, data: dict):
        self._progress_shimmer.stop()
        self.progress_bar.setVisible(False)

        self.layer_config.set_start_enabled(True)
        self.layer_config.set_export_enabled(True)
        self.layer_config.set_gis_map_enabled(True)

        self.summary_tab.update_data(data.get('results', []))
        self.duanmian_tab.update_data(data.get('duanmian', []))
        self.fangzhi_tab.update_data(data.get('fangzhi', []))
        self.yinhuan_tab.update_data(data.get('yinhuan', []))
        self.water_tab.update_data(data.get('water', []))

        self.stats_card.update_stats(data.get('results', []))

        self.check_finished.emit(data)

        has_water = data.get('has_water_system', True)
        if not has_water:
            QMessageBox.information(self, "完成",
                                    "检查已完成!\n\n⚠️ 缺少水系SHP文件，已跳过水系关联检查，仅执行图层自检。")
        else:
            QMessageBox.information(self, "完成", "检查已完成!")

    def _on_check_error(self, msg: str):
        self._progress_shimmer.stop()
        self.progress_bar.setVisible(False)
        self.layer_config.set_start_enabled(True)

    # ========== 公共接口 ==========

    def navigate_to(self, section: str):
        tab_map = {
            "check_config": 0,
            "check_summary": 0,
            "check_duanmian": 1,
            "check_fangzhi": 2,
            "check_yinhuan": 3,
            "check_water": 4,
        }
        tab_index = tab_map.get(section, 0)
        self.tabs.setCurrentIndex(tab_index)

    def is_checking(self) -> bool:
        return self.controller.is_checking()

    def set_results(self, data: dict):
        self.controller.check_results = data

        self.summary_tab.update_data(data.get('results', []))
        self.duanmian_tab.update_data(data.get('duanmian', []))
        self.fangzhi_tab.update_data(data.get('fangzhi', []))
        self.yinhuan_tab.update_data(data.get('yinhuan', []))
        self.water_tab.update_data(data.get('water', []))

        self.layer_config.set_export_enabled(True)
