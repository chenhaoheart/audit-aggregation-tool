# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame, QMessageBox
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QPoint

from ui.pages.dashboard.header import DashboardHeader
from ui.pages.dashboard.config_bar import DashboardConfigBar
from ui.pages.dashboard.stats_row import DashboardStatsRow
from ui.pages.dashboard.checks_grid import DashboardChecksGrid
from ui.pages.dashboard.results_tabs import DashboardResultsTabs
from controllers.dashboard_controller import DashboardController
from ui.components.dashboard_widgets import CheckProgressPanel
from core.effects_manager import StaggerEntrance


class DashboardPage(QWidget):

    log_message = Signal(str)
    show_log_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.controller = DashboardController(parent_widget=self)
        self._connect_controller_signals()

        self._init_ui()
        self._connect_view_signals()

    def _connect_controller_signals(self):
        c = self.controller
        c.check_started.connect(self._on_check_started)
        c.check_finished.connect(self._on_check_finished)
        c.check_progress.connect(self._on_check_progress)
        c.check_error.connect(self._on_check_error)
        c.check_cancelled.connect(self._on_check_cancelled)
        c.log_message.connect(self.log_message.emit)

    def _connect_view_signals(self):
        self.header.report_clicked.connect(self._generate_report)
        self.config_bar.folder_selected.connect(self._on_folder_selected)
        self.config_bar.start_clicked.connect(self._start_check)
        self.config_bar.clear_clicked.connect(self._clear_results)
        self.config_bar.log_clicked.connect(lambda: self.show_log_requested.emit())
        self.progress_panel.cancelled.connect(self._cancel_check)
        self.checks_grid.check_card_clicked.connect(self._on_check_card_clicked)

    def _init_ui(self):
        outer_layout = QVBoxLayout()
        outer_layout.setSpacing(0)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QFrame()
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        from PySide6.QtWidgets import QScrollArea, QSizePolicy
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setObjectName("dashboardScrollArea")

        scroll_content = QWidget()
        scroll_content.setObjectName("cardInnerPanel")

        main_layout = QVBoxLayout(scroll_content)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.header = DashboardHeader(self)
        main_layout.addWidget(self.header)

        self.config_bar = DashboardConfigBar(self)
        main_layout.addWidget(self.config_bar)

        self.progress_panel = CheckProgressPanel()
        self.progress_panel.setVisible(False)
        main_layout.addWidget(self.progress_panel)

        self.stats_row = DashboardStatsRow(self)
        main_layout.addWidget(self.stats_row)

        self.checks_grid = DashboardChecksGrid(self)
        main_layout.addWidget(self.checks_grid)

        self.results_tabs = DashboardResultsTabs(self)
        main_layout.addWidget(self.results_tabs, 1)

        scroll.setWidget(scroll_content)
        outer_layout.addWidget(scroll, 1)
        self.setLayout(outer_layout)

        if self.config_bar.get_folder_path():
            self.controller.set_root_path(self.config_bar.get_folder_path())

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, '_entrance_played'):
            self._entrance_played = True
            StaggerEntrance.play(self, stagger_ms=50, duration=300)

    def _on_folder_selected(self, path: str):
        self.controller.set_root_path(path)

    def _start_check(self):
        self.controller.start_check()

    def _cancel_check(self):
        self.controller.cancel_check()

    def _generate_report(self):
        self.controller.generate_report()

    def _on_check_started(self):
        self.config_bar.set_start_enabled(False)
        self.progress_panel.setVisible(True)
        self.progress_panel.set_indeterminate("正在初始化检查...")

    def _on_check_progress(self, section, msg):
        key_map = {'fubiao': 'fubiao', 'spatial': 'spatial', 'section': 'section',
                   'photo': 'photo', 'cross': 'cross'}
        key = key_map.get(section)
        if key and key in self.checks_grid.category_cards:
            self.checks_grid.category_cards[key].update_status('running')
        self.progress_panel.set_progress(0, msg)

    def _on_check_finished(self, data):
        self.progress_panel.setVisible(False)
        self.config_bar.set_start_enabled(True)
        self.header.set_report_enabled(True)

        self._update_all_views(data)

        summary = data.get('summary', {})
        QMessageBox.information(self, "完成",
                                f"Dashboard汇总检查完成!\n\n"
                                f"总错误: {summary.get('total_errors', 0)}\n"
                                f"总警告: {summary.get('total_warnings', 0)}\n"
                                f"综合评定: {summary.get('overall_status', '--')}")

    def _on_check_error(self, msg):
        self.progress_panel.setVisible(False)
        self.config_bar.set_start_enabled(True)

    def _on_check_cancelled(self):
        self.progress_panel.setVisible(False)
        self.config_bar.set_start_enabled(True)

    def _on_check_card_clicked(self, key: str):
        card_key_map = {
            'fubiao': 'fubiao_card',
            'spatial': 'spatial_card',
            'section': 'section_card',
            'photo': 'photo_card',
            'cross': 'cross_card',
        }
        card_key = card_key_map.get(key)
        if card_key:
            self.results_tabs.show_card(card_key)

    def _update_all_views(self, data):
        self.stats_row.update_stats(data)
        self.checks_grid.update_category_cards(data)
        self.results_tabs.update_fubiao(data)
        self.results_tabs.update_spatial(data)
        self.results_tabs.update_section(data)
        self.results_tabs.update_photo(data)
        self.results_tabs.update_cross(data)

        for key in ['fubiao', 'spatial', 'section', 'photo', 'cross']:
            status = data.get(f'{key}_check', {}).get('status', 'pending')
            card_key = f'{key}_card'
            self.results_tabs.update_card_status(card_key, status)

    def _clear_results(self):
        self.controller.clear_results()
        self.config_bar.clear()
        self.stats_row.reset()
        self.checks_grid.reset()
        self.results_tabs.reset()
        self.header.set_report_enabled(False)
