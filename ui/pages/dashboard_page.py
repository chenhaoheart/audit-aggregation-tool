# -*- coding: utf-8 -*-
"""
Dashboard汇总检查页面 - Data Observatory风格
一键扫描示范小流域根目录，执行全部4项检查 + 交叉校验
使用自定义绘制组件实现图表化、卡片化展示
所有样式通过QSS主题令牌控制，不在代码中硬编码颜色
"""

import os
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QFrame, QScrollArea, QAbstractItemView, QMessageBox,
    QGridLayout, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer, QPoint

from services.dashboard_service import DashboardService
from services.report_generator import build_report_html
from ui.components.dashboard_widgets import (
    StatNumberCard, StatMetricCard, HealthScoreGauge,
    CheckStatusPanel, CrossCheckTimeline,
    CollapsibleCard, CollapsibleCardsContainer, CheckProgressPanel,
    SpatialResultGrid, PhotoMatchDashboard, CrossCheckListPanel
)
from core.theme_manager import get_theme_manager
from core.effects_manager import ShimmerProgress, StaggerEntrance, ButtonGlowHelper


class DashboardPage(QWidget):
    """
    Dashboard汇总检查页面 - 现代化UI

    信号:
        log_message: 日志消息信号
    """

    log_message = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.root_path = ""
        self.check_result = None

        self.dashboard_service = DashboardService(self)
        self.theme_manager = get_theme_manager()

        self.dashboard_service.progress.connect(self._on_progress)
        self.dashboard_service.finished.connect(self._on_finished)
        self.dashboard_service.error.connect(self._on_error)
        self.dashboard_service.state_changed.connect(self._on_state_changed)

        self.theme_manager.theme_changed.connect(self._on_theme_changed)

        self._init_ui()

    def _init_ui(self):
        outer_layout = QVBoxLayout()
        outer_layout.setSpacing(0)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setObjectName("dashboardScrollArea")

        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("cardInnerPanel")

        main_layout = QVBoxLayout(self.scroll_content)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(0, 0, 0, 0)

        header = self._build_header()
        main_layout.addWidget(header)

        config_bar = self._build_config_bar()
        main_layout.addWidget(config_bar)

        self.progress_panel = CheckProgressPanel()
        self.progress_panel.setVisible(False)
        self.progress_panel.cancelled.connect(self._cancel_check)
        main_layout.addWidget(self.progress_panel)

        stats_row = self._build_stats_row()
        main_layout.addWidget(stats_row)

        checks_grid = self._build_checks_grid()
        main_layout.addWidget(checks_grid)

        tabs_container = self._build_results_tabs()
        main_layout.addWidget(tabs_container, 1)

        self.scroll_area.setWidget(self.scroll_content)
        outer_layout.addWidget(self.scroll_area, 1)
        self.setLayout(outer_layout)

    def _build_header(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QHBoxLayout(card)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 16, 20, 16)

        accent = QFrame()
        accent.setObjectName("accentBar")
        accent.setFixedWidth(4)
        layout.addWidget(accent)

        left = QVBoxLayout()
        left.setSpacing(4)
        title = QLabel("Dashboard 汇总检查")
        title.setObjectName("sectionHeaderLg")
        left.addWidget(title)
        sub = QLabel("选择示范小流域根目录，一键执行全部检查与交叉校验，生成可视化报告")
        sub.setObjectName("pageSubtitle")
        left.addWidget(sub)
        layout.addLayout(left, 1)

        right_btns = QHBoxLayout()
        right_btns.setSpacing(8)
        self.report_btn = QPushButton("  生成报告  ")
        self.report_btn.setCursor(Qt.PointingHandCursor)
        self.report_btn.setEnabled(False)
        self.report_btn.clicked.connect(self._generate_report)
        ButtonGlowHelper.install(self.report_btn)
        right_btns.addWidget(self.report_btn)
        layout.addLayout(right_btns)

        return card

    def _build_config_bar(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 16, 12, 16)

        row = QHBoxLayout()
        row.setSpacing(12)

        lbl = QLabel("根目录:")
        lbl.setObjectName("boldLabel")
        row.addWidget(lbl, 0, Qt.AlignVCenter)

        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("选择示范小流域根目录...")
        self.folder_edit.setReadOnly(True)
        default_root = r"D:\github\空间数据检查桌面版-主题-design-2026\青海24示范小流域-药草沟-20260313"
        if os.path.exists(default_root):
            self.folder_edit.setText(default_root)
            self.root_path = default_root
        row.addWidget(self.folder_edit, 1)

        browse_btn = QPushButton("浏览")
        browse_btn.setFixedWidth(64)
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.clicked.connect(self._select_folder)
        row.addWidget(browse_btn)

        self.start_btn = QPushButton("  一键检查  ")
        self.start_btn.setFixedWidth(110)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.clicked.connect(self._start_check)
        self.start_btn.setEnabled(bool(self.root_path))
        ButtonGlowHelper.install(self.start_btn)
        row.addWidget(self.start_btn)

        self.clear_btn = QPushButton("清空")
        self.clear_btn.setFixedWidth(56)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setObjectName("clearBtn")
        self.clear_btn.clicked.connect(self._clear_results)
        row.addWidget(self.clear_btn)

        self.log_btn = QPushButton("日志")
        self.log_btn.setFixedWidth(50)
        self.log_btn.setCursor(Qt.PointingHandCursor)
        self.log_btn.setObjectName("logToggleBtn")
        self.log_btn.clicked.connect(lambda: self.log_message.emit("[LOG] 日志窗口"))
        row.addWidget(self.log_btn)

        layout.addLayout(row)
        return card

    def _build_stats_row(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QHBoxLayout(card)
        layout.setSpacing(16)
        layout.setContentsMargins(12, 18, 12, 18)

        self.stat_cards = {}

        errors_card = StatMetricCard("总错误", "\u274c", "error_text")
        errors_card.set_value("0", "\u4e25\u91cd\u95ee\u9898", "error_text")
        layout.addWidget(errors_card)
        self.stat_cards["errors"] = errors_card

        warnings_card = StatMetricCard("总警告", "\u26a0\ufe0f", "warning_text")
        warnings_card.set_value("0", "\u9700\u8981\u5173\u6ce8", "warning_text")
        layout.addWidget(warnings_card)
        self.stat_cards["warnings"] = warnings_card

        overall_card = StatMetricCard("综合评定", "\U0001f4ca", "text_primary")
        overall_card.set_value("--", "", None)
        layout.addWidget(overall_card)
        self.stat_cards["overall"] = overall_card

        self.health_gauge = HealthScoreGauge(110)
        self.health_gauge.setObjectName("healthGaugeContainer")
        layout.addWidget(self.health_gauge)
        self.stat_cards["score"] = self.health_gauge

        return card

    def _build_checks_grid(self):
        container = QFrame()
        container.setObjectName("card")
        layout = QVBoxLayout(container)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 18, 12, 18)

        section_title = QLabel("\U0001f50d 检查概览")
        section_title.setObjectName("sectionHeaderSm")
        layout.addWidget(section_title)

        grid = QFrame()
        grid.setObjectName("cardInnerPanel")
        grid_layout = QHBoxLayout(grid)
        grid_layout.setSpacing(10)
        grid_layout.setContentsMargins(2, 4, 2, 4)

        self.category_cards = {}
        categories = [
            ("fubiao", "\ud83d\udccb", "附表检查", "字段完整性校验"),
            ("spatial", "\ud83d\uddfa\ufe0f", "空间数据", "SHP图层属性校验"),
            ("section", "\ud83d\udcd0", "断面数据", "测量数据格式校验"),
            ("photo", "\ud83d\udcf7", "照片匹配", "照片与附表一致性"),
            ("cross", "\ud83d\udd17", "交叉校验", "多源数据一致性验证"),
        ]

        for key, icon, title, sub in categories:
            panel = CheckStatusPanel(key, f"{icon} {title}", sub)
            panel.clicked.connect(self._on_check_card_clicked)
            grid_layout.addWidget(panel)
            self.category_cards[key] = panel

        self._key_to_card_map = {
            'fubiao': 'fubiao_card',
            'spatial': 'spatial_card',
            'section': 'section_card',
            'photo': 'photo_card',
            'cross': 'cross_card',
        }

        layout.addWidget(grid)

        self.cross_timeline = CrossCheckTimeline()
        self.cross_timeline.setVisible(False)
        layout.addWidget(self.cross_timeline)

        return container

    def _build_results_tabs(self):
        container = QFrame()
        container.setObjectName("resultsContainer")
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(12)
        container_layout.setContentsMargins(0, 0, 0, 0)

        section_header = QLabel("\U0001f4ca 结果详情")
        section_header.setObjectName("sectionHeaderSm")
        container_layout.addWidget(section_header)

        self.cards_container = CollapsibleCardsContainer()

        card_configs = [
            ("fubiao_card", "\ud83d\udccb", "附表1/2/3详情", "_setup_fubiao_content"),
            ("spatial_card", "\ud83d\uddfa\ufe0f", "空间数据详情", "_setup_spatial_content"),
            ("section_card", "\ud83d\udcd0", "断面数据详情", "_setup_section_content"),
            ("photo_card", "\ud83d\udcf7", "照片匹配详情", "_setup_photo_content"),
            ("cross_card", "\ud83d\udd17", "交叉校验详情", "_setup_cross_content"),
        ]

        self.result_cards = {}
        for attr_name, icon, title, setup_method in card_configs:
            card = CollapsibleCard(title, icon)
            content_widget = QWidget()
            getattr(self, setup_method)(content_widget)
            card.set_content_widget(content_widget)
            self.cards_container.add_card(card)
            self.result_cards[attr_name] = card
            setattr(self, attr_name.replace('_card', '_content'), content_widget)

        container_layout.addWidget(self.cards_container, 1)
        return container

    def _setup_fubiao_content(self, widget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.fubiao_table = QTableWidget()
        self.fubiao_table.setObjectName("minimalResultTable")
        self.fubiao_table.setColumnCount(6)
        self.fubiao_table.setHorizontalHeaderLabels(["序号", "表名", "字段名", "错误类型", "错误描述", "当前值"])
        self.fubiao_table.horizontalHeader().setStretchLastSection(True)
        self.fubiao_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        for i, w in enumerate([45, 55, 110, 75, 280]):
            self.fubiao_table.setColumnWidth(i, w)
        self.fubiao_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.fubiao_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.fubiao_table.verticalHeader().setVisible(False)
        self.fubiao_table.setAlternatingRowColors(True)
        layout.addWidget(self.fubiao_table)

    def _setup_spatial_content(self, widget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.spatial_grid = SpatialResultGrid()
        self.spatial_grid.setMinimumHeight(200)
        layout.addWidget(self.spatial_grid)

    def _setup_section_content(self, widget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.section_table = QTableWidget()
        self.section_table.setObjectName("minimalResultTable")
        self.section_table.setColumnCount(3)
        self.section_table.setHorizontalHeaderLabels(["指标", "数值", "说明"])
        self.section_table.horizontalHeader().setStretchLastSection(True)
        self.section_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.section_table.setColumnWidth(0, 140)
        self.section_table.setColumnWidth(1, 80)
        self.section_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.section_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.section_table.verticalHeader().setVisible(False)
        self.section_table.setAlternatingRowColors(True)
        layout.addWidget(self.section_table)

    def _setup_photo_content(self, widget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.photo_dashboard = PhotoMatchDashboard()
        self.photo_dashboard.setMinimumHeight(280)
        layout.addWidget(self.photo_dashboard)

    def _setup_cross_content(self, widget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.cross_list = CrossCheckListPanel()
        self.cross_list.setMinimumHeight(400)
        layout.addWidget(self.cross_list)

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, '_entrance_played'):
            self._entrance_played = True
            StaggerEntrance.play(self, stagger_ms=50, duration=300)

    def _on_theme_changed(self, mode: str):
        pass

    def _select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择示范小流域根目录")
        if folder:
            self.root_path = folder
            self.folder_edit.setText(folder)
            self.start_btn.setEnabled(True)

    def _start_check(self):
        if not self.root_path:
            QMessageBox.warning(self, "警告", "请选择示范小流域根目录")
            return
        self._clear_tables()
        self._reset_status()
        self.start_btn.setEnabled(False)
        self.progress_panel.setVisible(True)
        self.progress_panel.set_indeterminate("正在初始化检查...")
        self._log("开始Dashboard汇总检查...")
        self.dashboard_service.start_check(self.root_path)

    def _on_check_card_clicked(self, key: str):
        card_key = self._key_to_card_map.get(key)
        if not card_key or card_key not in self.result_cards:
            return
        card = self.result_cards[card_key]
        if card.is_expanded():
            self._scroll_to_widget(card)
        else:
            def _on_expand_done():
                card.expand_finished.disconnect(_on_expand_done)
                self._scroll_to_widget(card)
            card.expand_finished.connect(_on_expand_done)
            card.expand()

    def _scroll_to_widget(self, widget):
        target_y = widget.mapTo(self.scroll_content, QPoint(0, 0)).y()
        current = self.scroll_area.verticalScrollBar().value()
        viewport_h = self.scroll_area.viewport().height()
        offset = min(80, viewport_h // 5)
        scroll_to = max(0, target_y - offset)
        anim = QPropertyAnimation(self.scroll_area.verticalScrollBar(), b"value")
        anim.setDuration(350)
        anim.setStartValue(current)
        anim.setEndValue(int(scroll_to))
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()

    def _cancel_check(self):
        self.dashboard_service.cancel_check()
        self.progress_panel.setVisible(False)
        self.start_btn.setEnabled(True)
        self._log("检查已取消")

    def _on_progress(self, section, msg):
        key_map = {'fubiao': 'fubiao', 'spatial': 'spatial', 'section': 'section',
                   'photo': 'photo', 'cross': 'cross'}
        key = key_map.get(section)
        if key and key in self.category_cards:
            self.category_cards[key].update_status('running')
        self.progress_panel.set_progress(0, msg)
        self._log(f"[{section}] {msg}")

    def _on_finished(self, data):
        self.check_result = data
        self.progress_panel.setVisible(False)
        self.start_btn.setEnabled(True)
        self.report_btn.setEnabled(True)

        self._update_all_views(data)
        summary = data.get('summary', {})
        self._log(f"检查完成! 错误: {summary.get('total_errors', 0)}, 警告: {summary.get('total_warnings', 0)}")
        QMessageBox.information(self, "完成",
                                f"Dashboard汇总检查完成!\n\n"
                                f"总错误: {summary.get('total_errors', 0)}\n"
                                f"总警告: {summary.get('total_warnings', 0)}\n"
                                f"综合评定: {summary.get('overall_status', '--')}")

    def _on_error(self, msg):
        self.progress_panel.setVisible(False)
        self.start_btn.setEnabled(True)
        self._log(f"错误: {msg}")
        QMessageBox.critical(self, "错误", f"检查失败:\n{msg}")

    def _on_state_changed(self, state):
        pass

    def _update_all_views(self, data):
        self._update_stats(data)
        self._update_category_cards(data)
        self._update_fubiao(data)
        self._update_spatial(data)
        self._update_section(data)
        self._update_photo(data)
        self._update_cross(data)

    def _update_stats(self, data):
        summary = data.get('summary', {})
        errors = summary.get('total_errors', 0)
        warnings = summary.get('total_warnings', 0)
        overall = summary.get('overall_status', 'pending')

        err_color_key = "error_text" if errors > 0 else "success_text"
        self.stat_cards["errors"].set_value(
            str(errors),
            "\u4e25\u91cd\u95ee\u9898" if errors > 0 else "\u6570\u636e\u6b63\u5e38",
            err_color_key
        )

        warn_color_key = "warning_text" if warnings > 0 else "success_text"
        self.stat_cards["warnings"].set_value(
            str(warnings),
            "\u9700\u8981\u5173\u6ce8" if warnings > 0 else "\u65e0\u8b66\u544a",
            warn_color_key
        )

        overall_map = {
            'pass': ('\u2705 \u5168\u901a\u8fc7', '', 'success_text'),
            'warn': ('\u6709\u8b66\u544a', f'{warnings}\u9879\u8b66\u544a', 'warning_text'),
            'fail': ('\u274c \u6709\u9519\u8bef', f'{errors}\u9879\u9519\u8bef', 'error_text'),
        }
        val, sub, color_key = overall_map.get(overall, ('--', '', None))
        self.stat_cards["overall"].set_value(val, sub, color_key)

        score = max(0, 100 - errors * 5 - warnings * 2)
        self.health_gauge.set_score(score)

    def _update_category_cards(self, data):
        fb = data.get('fubiao_check', {})
        sp = data.get('spatial_check', {})
        sec = data.get('section_check', {})
        ph = data.get('photo_check', {})
        cr = data.get('cross_check', {})

        fb_err = len(fb.get('errors', []))
        fb_status = fb.get('status', 'pending')
        self.category_cards["fubiao"].update_status(
            fb_status,
            f"{fb_err} \u4e2a\u95ee\u9898" if fb_err > 0 else "\u6821\u9a8c\u901a\u8fc7")
        if "fubiao_card" in self.result_cards:
            self.result_cards["fubiao_card"].set_status(fb_status)

        sp_invalid = sum(1 for r in sp.get('results', []) if r.get('status') != '\u901a\u8fc7')
        sp_status = sp.get('status', 'pending')
        self.category_cards["spatial"].update_status(
            sp_status,
            f"{sp_invalid}/{len(sp.get('results', []))} \u56fe\u5c42\u5f02\u5e38" if sp_invalid > 0 else "\u6821\u9a8c\u901a\u8fc7")
        if "spatial_card" in self.result_cards:
            self.result_cards["spatial_card"].set_status(sp_status)

        sec_stats = sec.get('stats', {})
        sec_err = sec_stats.get('validation_error_count', 0)
        sec_anom = sec_stats.get('anomaly_count', 0)
        sec_detail = f"\u9519\u8bef{sec_err} \u5f02\u5e38{sec_anom}" if (sec_err or sec_anom) else "\u6821\u9a8c\u901a\u8fc7"
        sec_status = sec.get('status', 'pending')
        self.category_cards["section"].update_status(sec_status, sec_detail)
        if "section_card" in self.result_cards:
            self.result_cards["section_card"].set_status(sec_status)

        ph_summary = ph.get('match_result', {}).get('summary', {})
        ph_unmatched = ph_summary.get('fubiao2_unmatched', 0) + ph_summary.get('fubiao3_unmatched', 0)
        ph_status = ph.get('status', 'pending')
        self.category_cards["photo"].update_status(
            ph_status,
            f"{ph_unmatched}\u9879\u672a\u5339\u914d" if ph_unmatched > 0 else "\u5168\u90e8\u5339\u914d")
        if "photo_card" in self.result_cards:
            self.result_cards["photo_card"].set_status(ph_status)

        cr_err = len(cr.get('errors', []))
        cr_warn = len(cr.get('warnings', []))
        cr_detail = f"\u9519\u8bef{cr_err} \u8b66\u544a{cr_warn}" if (cr_err or cr_warn) else "\u6821\u9a8c\u901a\u8fc7"
        cr_status = cr.get('status', 'pending')
        self.category_cards["cross"].update_status(cr_status, cr_detail)
        if "cross_card" in self.result_cards:
            self.result_cards["cross_card"].set_status(cr_status)

        cross_items = cr.get('items', [])
        if cross_items:
            self.cross_timeline.set_items(cross_items)
            self.cross_timeline.setVisible(True)

    def _update_fubiao(self, data):
        errors = data.get('fubiao_check', {}).get('errors', [])
        self.fubiao_table.setRowCount(len(errors))
        for row, err in enumerate(errors):
            for col, key in enumerate(['表名', '字段名', '错误类型', '错误描述', '当前值']):
                self.fubiao_table.setItem(row, col + 1, QTableWidgetItem(str(err.get(key, '')))
                                        if col > 0 else QTableWidgetItem(str(row + 1)))

    def _update_spatial(self, data):
        results = data.get('spatial_check', {}).get('results', [])
        self.spatial_grid.set_data(results)

    def _update_section(self, data):
        stats = data.get('section_check', {}).get('stats', {})
        rows = [
            ("\u603b\u65ad\u9762\u6570", stats.get('total_sections', 0), "\u6240\u6709\u52a0\u8f7d\u7684\u65ad\u9762\u6570\u636e"),
            ("\u603b\u6d4b\u70b9\u6570", stats.get('total_points', 0), "\u6240\u6709\u65ad\u9762\u7684\u6d4b\u91cf\u70b9"),
            ("\u5f02\u5e38\u65ad\u9762\u6570", stats.get('anomaly_count', 0), "\u7a7a\u95f4\u8fde\u7eed\u6027\u5f02\u5e38"),
            ("\u6821\u9a8c\u9519\u8bef\u6570", stats.get('validation_error_count', 0), "\u6570\u636e\u683c\u5f0f/\u903b\u8f91\u9519\u8bef"),
            ("\u6709\u5750\u6807\u70b9\u6570", stats.get('coords_count', 0), "\u5305\u542b\u7ecf\u7eac\u5ea6\u5750\u6807\u7684\u6d4b\u70b9"),
            ("\u5206\u7c7b\u6570", stats.get('category_count', 0), "\u4e0d\u540c\u6d4b\u91cf\u7c7b\u522b"),
        ]
        self.section_table.setRowCount(len(rows))
        for row, (name, count, desc) in enumerate(rows):
            self.section_table.setItem(row, 0, QTableWidgetItem(name))
            self.section_table.setItem(row, 1, QTableWidgetItem(str(count)))
            self.section_table.setItem(row, 2, QTableWidgetItem(desc))

    def _update_photo(self, data):
        mr = data.get('photo_check', {}).get('match_result', {}).get('summary', {})
        self.photo_dashboard.set_data(mr)

    def _update_cross(self, data):
        items = data.get('cross_check', {}).get('items', [])
        self.cross_list.set_items(items)

    def _generate_report(self):
        if not self.check_result:
            QMessageBox.warning(self, "提示", "请先执行检查操作")
            return
        try:
            report_html = build_report_html(self.check_result, self.root_path)
        except Exception as e:
            QMessageBox.critical(self, "失败", f"生成报告内容失败:\n{e}")
            self._log(f"报告生成失败: {e}")
            return
        save_path, _ = QFileDialog.getSaveFileName(
            self, "保存检查报告", f"Dashboard检查报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            "HTML 文件 (*.html);;所有文件 (*)"
        )
        if save_path:
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(report_html)
                QMessageBox.information(self, "成功", f"报告已保存至:\n{save_path}")
                self._log(f"报告已生成: {save_path}")
            except Exception as e:
                QMessageBox.critical(self, "失败", f"保存报告失败:\n{e}")

    def _reset_status(self):
        for card in self.category_cards.values():
            card.update_status('pending')
        for card in self.result_cards.values():
            card.set_status('pending')
            card.collapse()
        self.cross_timeline.setVisible(False)

        self.stat_cards["errors"].set_value("--", "", None)
        self.stat_cards["warnings"].set_value("--", "", None)
        self.stat_cards["overall"].set_value("--", "", None)
        self.health_gauge.set_score(0)

    def _clear_tables(self):
        self.fubiao_table.setRowCount(0)
        self.spatial_grid.set_data([])
        self.section_table.setRowCount(0)
        self.cross_list.set_items([])

    def _clear_results(self):
        self.check_result = None
        self._clear_tables()
        self._reset_status()
        self.report_btn.setEnabled(False)
        self.dashboard_service.clear_results()

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_message.emit(f"[{ts}] {msg}")
