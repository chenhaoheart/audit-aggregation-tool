# -*- coding: utf-8 -*-
import json
import os
import time
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QMessageBox, QAbstractItemView, QFrame, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QSplitter, QCheckBox, QToolButton, QGridLayout, QScrollArea, QSizePolicy,
    QComboBox
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QColor

from services.section_check_service import SectionCheckService
from core.theme_manager import get_theme_manager
from core.effects_manager import StaggerEntrance, TabFadeTransition, ButtonGlowHelper
from ui.dialogs.log_dialog import LogDialog
from ui.dialogs.excel_preview_dialog import ExcelPreviewDialog
from ui.dialogs.feature_keywords_dialog import FeatureKeywordsDialog

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    HAS_WEB_ENGINE = True
except ImportError:
    HAS_WEB_ENGINE = False


class SectionCheckPage(QWidget):
    log_message = Signal(str)
    show_log_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = SectionCheckService()
        self.theme_manager = get_theme_manager()
        self._current_section_key = None
        self._all_points = []
        self._current_page = 0
        self._page_size = 50
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

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

        header_card = QFrame()
        header_card.setObjectName("pageHeader")
        header_layout = QHBoxLayout(header_card)
        header_layout.setSpacing(16)
        header_layout.setContentsMargins(20, 16, 20, 16)
        accent_bar = QFrame()
        accent_bar.setObjectName("accentBar")
        accent_bar.setFixedWidth(4)
        header_layout.addWidget(accent_bar)
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        page_title = QLabel("断面数据检查")
        page_title.setObjectName("sectionHeaderLg")
        title_layout.addWidget(page_title)
        page_subtitle = QLabel("读取测量数据断面Excel，校验经纬度、起点距、高程等数据质量，支持断面成图可视化")
        page_subtitle.setObjectName("pageSubtitle")
        title_layout.addWidget(page_subtitle)
        header_layout.addLayout(title_layout, 1)
        layout.addWidget(header_card)

        config_card = QFrame()
        config_card.setObjectName("card")
        config_layout = QVBoxLayout(config_card)
        config_layout.setSpacing(12)
        config_layout.setContentsMargins(16, 16, 16, 16)

        dir_layout = QHBoxLayout()
        dir_layout.setSpacing(10)
        dir_label = QLabel("测量数据目录:")
        dir_label.setFixedWidth(110)
        dir_label.setObjectName("boldLabel")
        self.dir_edit = QLineEdit()
        self.dir_edit.setPlaceholderText("选择包含测量数据(防治对象/沟滩占地对象/跨沟道路和桥涵)的目录...")
        self.dir_edit.setReadOnly(True)
        default_dir = "D:/github/空间数据检查桌面版-主题-design/青海24示范小流域-药草沟-20260313/630121_大通/电子数据/测量数据"
        if os.path.exists(default_dir):
            self.dir_edit.setText(default_dir)
        dir_btn = QPushButton("浏览...")
        dir_btn.setFixedWidth(80)
        dir_btn.clicked.connect(self._select_directory)
        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.dir_edit, 1)
        dir_layout.addWidget(dir_btn)
        config_layout.addLayout(dir_layout)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        self.load_btn = QPushButton("加载数据")
        self.load_btn.setCursor(Qt.PointingHandCursor)
        self.load_btn.clicked.connect(self._start_load)
        btn_layout.addWidget(self.load_btn)

        self.log_btn = QPushButton("查看日志")
        self.log_btn.setCursor(Qt.PointingHandCursor)
        self.log_btn.clicked.connect(self._on_log_btn_clicked)
        btn_layout.addWidget(self.log_btn)

        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setFrameShadow(QFrame.Sunken)
        btn_layout.addWidget(separator1)

        self.export_btn = QPushButton("导出校验报告")
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setObjectName("validateBtn")
        self.export_btn.clicked.connect(self._export_report)
        self.export_btn.setEnabled(False)
        btn_layout.addWidget(self.export_btn)

        self.export_html_btn = QPushButton("导出异常断面HTML")
        self.export_html_btn.setCursor(Qt.PointingHandCursor)
        self.export_html_btn.clicked.connect(self._export_anomaly_html)
        self.export_html_btn.setEnabled(False)
        btn_layout.addWidget(self.export_html_btn)

        self.export_all_html_btn = QPushButton("导出全部断面成图")
        self.export_all_html_btn.setCursor(Qt.PointingHandCursor)
        self.export_all_html_btn.clicked.connect(self._export_all_html)
        self.export_all_html_btn.setEnabled(False)
        btn_layout.addWidget(self.export_all_html_btn)

        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        btn_layout.addWidget(separator2)

        self.feature_config_btn = QPushButton("特征点配置")
        self.feature_config_btn.setCursor(Qt.PointingHandCursor)
        self.feature_config_btn.clicked.connect(self._on_feature_config_clicked)
        btn_layout.addWidget(self.feature_config_btn)

        btn_layout.addStretch()
        config_layout.addLayout(btn_layout)
        layout.addWidget(config_card)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(12)
        layout.addWidget(self.progress_bar)

        stats_card = QFrame()
        stats_card.setObjectName("card")
        stats_layout = QHBoxLayout(stats_card)
        stats_layout.setSpacing(20)
        stats_layout.setContentsMargins(18, 10, 18, 10)
        self.stats_labels = {}
        for key, label_text in [("total_sections", "断面数"), ("total_points", "测量点"),
                                 ("coords_count", "含坐标点"), ("anomaly_count", "异常断面"),
                                 ("validation_error_count", "校验错误")]:
            item_layout = QVBoxLayout()
            item_layout.setSpacing(2)
            val_label = QLabel("0")
            val_label.setObjectName("statValue")
            val_label.setAlignment(Qt.AlignCenter)
            name_label = QLabel(label_text)
            name_label.setObjectName("statName")
            name_label.setAlignment(Qt.AlignCenter)
            item_layout.addWidget(val_label)
            item_layout.addWidget(name_label)
            stats_layout.addLayout(item_layout)
            self.stats_labels[key] = val_label
        layout.addWidget(stats_card)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("mainSplitter")

        left_widget = QFrame()
        left_widget.setObjectName("card")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(8)
        left_layout.setContentsMargins(8, 8, 8, 8)

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索断面名称...")
        self.search_edit.textChanged.connect(self._on_search)
        filter_layout.addWidget(self.search_edit, 1)
        self.anomaly_filter_cb = QCheckBox("仅异常")
        self.anomaly_filter_cb.stateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.anomaly_filter_cb)
        self.error_filter_cb = QCheckBox("仅错误")
        self.error_filter_cb.stateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.error_filter_cb)
        left_layout.addLayout(filter_layout)

        self.section_tree = QTreeWidget()
        self.section_tree.setHeaderLabels(["断面名称", "点数", "状态"])
        self.section_tree.setColumnWidth(0, 220)
        self.section_tree.setColumnWidth(1, 50)
        self.section_tree.setColumnWidth(2, 80)
        self.section_tree.itemClicked.connect(self._on_section_clicked)

        tree_toolbar = QHBoxLayout()
        tree_toolbar.setSpacing(4)
        self.expand_all_btn = QToolButton()
        self.expand_all_btn.setText("全部展开")
        self.expand_all_btn.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.expand_all_btn.setFixedHeight(26)
        self.expand_all_btn.setCursor(Qt.PointingHandCursor)
        self.expand_all_btn.clicked.connect(self.section_tree.expandAll)
        tree_toolbar.addWidget(self.expand_all_btn)
        self.collapse_all_btn = QToolButton()
        self.collapse_all_btn.setText("全部折叠")
        self.collapse_all_btn.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.collapse_all_btn.setFixedHeight(26)
        self.collapse_all_btn.setCursor(Qt.PointingHandCursor)
        self.collapse_all_btn.clicked.connect(self.section_tree.collapseAll)
        tree_toolbar.addWidget(self.collapse_all_btn)
        self.chengtu_filter_cb = QCheckBox("成图表")
        self.chengtu_filter_cb.setChecked(True)
        self.chengtu_filter_cb.stateChanged.connect(self._on_filter_changed)
        tree_toolbar.addWidget(self.chengtu_filter_cb)
        self.guifan_filter_cb = QCheckBox("规范表")
        self.guifan_filter_cb.setChecked(True)
        self.guifan_filter_cb.stateChanged.connect(self._on_filter_changed)
        tree_toolbar.addWidget(self.guifan_filter_cb)
        tree_toolbar.addStretch()
        left_layout.addLayout(tree_toolbar)
        left_layout.addWidget(self.section_tree, 1)
        splitter.addWidget(left_widget)

        right_widget = QFrame()
        right_widget.setObjectName("card")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(8)
        right_layout.setContentsMargins(8, 8, 8, 8)

        self.detail_title = QLabel("请选择断面查看详情")
        self.detail_title.setObjectName("sectionHeaderMd")
        right_layout.addWidget(self.detail_title)

        self.detail_tabs = QTabWidget()
        self.detail_tabs.setObjectName("resultTabs")

        chart_tab = QWidget()
        chart_layout = QVBoxLayout(chart_tab)
        chart_layout.setSpacing(0)
        chart_layout.setContentsMargins(0, 8, 0, 8)
        chart_toolbar = QHBoxLayout()
        chart_toolbar.setContentsMargins(8, 0, 8, 0)
        self.export_chart_btn = QPushButton("导出断面成图")
        self.export_chart_btn.setFixedHeight(24)
        self.export_chart_btn.setCursor(Qt.PointingHandCursor)
        self.export_chart_btn.setStyleSheet("QPushButton { padding: 0 8px; font-size: 12px; }")
        self.export_chart_btn.clicked.connect(self._open_chart_external)
        chart_toolbar.addWidget(self.export_chart_btn)
        chart_toolbar.addStretch()
        chart_layout.addLayout(chart_toolbar)
        if HAS_WEB_ENGINE:
            self.chart_web = QWebEngineView()
            self.chart_web.setMinimumHeight(500)
            self.chart_web.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            chart_layout.addWidget(self.chart_web, 1)
        else:
            chart_placeholder = QLabel("成图功能需要 QWebEngineView 支持\n请安装 PySide6-WebEngine")
            chart_placeholder.setAlignment(Qt.AlignCenter)
            chart_placeholder.setStyleSheet("color: #64748b; font-size: 14px;")
            chart_layout.addWidget(chart_placeholder)
        self.detail_tabs.addTab(chart_tab, "断面成图")

        points_tab = QWidget()
        points_outer_layout = QVBoxLayout(points_tab)
        points_outer_layout.setSpacing(8)
        points_outer_layout.setContentsMargins(0, 0, 0, 8)

        info_group = QFrame()
        info_group.setObjectName("card")
        info_group_layout = QVBoxLayout(info_group)
        info_group_layout.setSpacing(4)
        info_group_layout.setContentsMargins(8, 8, 8, 8)
        info_title_layout = QHBoxLayout()
        info_title_layout.setSpacing(8)
        info_title = QLabel("断面属性")
        info_title.setObjectName("sectionHeaderSm")
        info_title_layout.addWidget(info_title)
        self.open_excel_btn = QPushButton("预览Excel")
        self.open_excel_btn.setFixedHeight(20)
        self.open_excel_btn.setCursor(Qt.PointingHandCursor)
        self.open_excel_btn.setStyleSheet("QPushButton { padding: 0 6px; font-size: 11px; }")
        self.open_excel_btn.clicked.connect(self._preview_excel)
        info_title_layout.addWidget(self.open_excel_btn)
        info_title_layout.addStretch()
        info_group_layout.addLayout(info_title_layout)
        
        self.info_grid = QGridLayout()
        self.info_grid.setSpacing(6)
        self.info_grid.setContentsMargins(0, 0, 0, 0)
        self.info_labels = {}
        info_group_layout.addLayout(self.info_grid)
        points_outer_layout.addWidget(info_group)

        points_header = QHBoxLayout()
        points_header.setSpacing(8)
        points_title = QLabel("测量点数据")
        points_title.setObjectName("sectionHeaderSm")
        points_header.addWidget(points_title)
        points_header.addStretch()
        
        page_size_label = QLabel("每页显示:")
        page_size_label.setStyleSheet("color: #64748b; font-size: 12px;")
        points_header.addWidget(page_size_label)
        
        self.points_page_size_combo = QComboBox()
        self.points_page_size_combo.addItems(["20", "50", "100", "200", "500"])
        self.points_page_size_combo.setCurrentText("50")
        self.points_page_size_combo.setFixedWidth(60)
        self.points_page_size_combo.setFixedHeight(20)
        self.points_page_size_combo.setCursor(Qt.PointingHandCursor)
        self.points_page_size_combo.setStyleSheet("QComboBox { padding: 0 4px; font-size: 11px; } QComboBox::drop-down { width: 16px; }")
        self.points_page_size_combo.currentIndexChanged.connect(self._on_page_size_changed)
        points_header.addWidget(self.points_page_size_combo)
        
        self.points_page_info = QLabel("")
        self.points_page_info.setStyleSheet("color: #64748b; font-size: 12px;")
        points_header.addWidget(self.points_page_info)
        
        self.points_prev_btn = QPushButton("上一页")
        self.points_prev_btn.setFixedHeight(20)
        self.points_prev_btn.setFixedWidth(50)
        self.points_prev_btn.setCursor(Qt.PointingHandCursor)
        self.points_prev_btn.setStyleSheet("QPushButton { padding: 0 4px; font-size: 11px; }")
        self.points_prev_btn.clicked.connect(self._on_prev_page)
        points_header.addWidget(self.points_prev_btn)
        
        self.points_next_btn = QPushButton("下一页")
        self.points_next_btn.setFixedHeight(20)
        self.points_next_btn.setFixedWidth(50)
        self.points_next_btn.setCursor(Qt.PointingHandCursor)
        self.points_next_btn.setStyleSheet("QPushButton { padding: 0 4px; font-size: 11px; }")
        self.points_next_btn.clicked.connect(self._on_next_page)
        points_header.addWidget(self.points_next_btn)
        
        points_outer_layout.addLayout(points_header)
        
        self.points_table = QTableWidget()
        self.points_table.setColumnCount(8)
        self.points_table.setHorizontalHeaderLabels([
            "序号", "特征描述", "起点距(m)", "高程(m)", "经度(°)", "纬度(°)", "糙率", "特征点"
        ])
        self.points_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.points_table.horizontalHeader().setStretchLastSection(True)
        self.points_table.setColumnWidth(0, 60)
        self.points_table.setColumnWidth(1, 150)
        self.points_table.setColumnWidth(2, 90)
        self.points_table.setColumnWidth(3, 90)
        self.points_table.setColumnWidth(4, 110)
        self.points_table.setColumnWidth(5, 110)
        self.points_table.setColumnWidth(6, 60)
        self.points_table.setColumnWidth(7, 60)
        self.points_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.points_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.points_table.verticalHeader().setVisible(False)
        self.points_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.points_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.points_table.setStyleSheet("QTableWidget { gridline-color: rgba(200,200,200,0.30); border: 1px solid rgba(200,200,200,0.30); } QTableWidget::item { padding: 4px; border: none; } QHeaderView::section { padding: 4px; border: 1px solid rgba(200,200,200,0.30); background: rgba(240,240,240,0.50); }")
        default_height = self.points_table.verticalHeader().defaultSectionSize() * 50 + self.points_table.horizontalHeader().height() + self.points_table.frameWidth() * 2 + 51 + 6
        self.points_table.setFixedHeight(default_height)
        points_outer_layout.addWidget(self.points_table)
        
        self.detail_tabs.addTab(points_tab, "数据详情")

        issues_tab = QWidget()
        issues_layout = QVBoxLayout(issues_tab)
        issues_layout.setSpacing(0)
        issues_layout.setContentsMargins(0, 4, 0, 4)
        self.issues_table = QTableWidget()
        self.issues_table.setColumnCount(4)
        self.issues_table.setHorizontalHeaderLabels(["级别", "规则", "描述", "详情"])
        self.issues_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.issues_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.issues_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.issues_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.issues_table.setColumnWidth(0, 60)
        self.issues_table.setColumnWidth(1, 120)
        self.issues_table.setColumnWidth(2, 120)
        self.issues_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.issues_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        issues_layout.addWidget(self.issues_table)
        self.detail_tabs.addTab(issues_tab, "校验问题")

        right_layout.addWidget(self.detail_tabs, 1)
        splitter.addWidget(right_widget)

        splitter.setSizes([300, 700])
        layout.addWidget(splitter, 1)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)

        self._tab_fade = TabFadeTransition(self.detail_tabs, duration=180)
        self._tab_fade.attach()

        for btn in self.findChildren(QPushButton):
            if btn.objectName() in ('loadBtn',):
                ButtonGlowHelper.install(btn)

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, '_entrance_played'):
            self._entrance_played = True
            StaggerEntrance.play(self, stagger_ms=60, duration=320)

    def _select_directory(self):
        folder = QFileDialog.getExistingDirectory(self, "选择测量数据目录")
        if folder:
            self.dir_edit.setText(folder)

    def _start_load(self):
        directory = self.dir_edit.text()
        if not directory:
            QMessageBox.warning(self, "警告", "请先选择测量数据目录")
            return
        if not os.path.exists(directory):
            QMessageBox.warning(self, "警告", "目录不存在")
            return
        self.load_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.export_html_btn.setEnabled(False)
        self.export_all_html_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.service.start_load(
            directory,
            on_progress=self._on_load_progress,
            on_finished=self._on_load_finished,
            on_error=self._on_load_error,
            parent=self,
        )

    def _on_load_progress(self, current, total, name):
        if total > 0:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(current)

    def _on_load_finished(self, result):
        self.progress_bar.setVisible(False)
        self.load_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.export_html_btn.setEnabled(True)
        self.export_all_html_btn.setEnabled(True)
        stats = self.service.get_stats()
        self._update_stats(stats)
        self._refresh_tree()
        msg = f"加载完成: {result['total_sections']}个断面, {result['total_points']}个测量点"
        if result['anomaly_count'] > 0:
            msg += f", {result['anomaly_count']}个异常"
        if result['validation_error_count'] > 0:
            msg += f", {result['validation_error_count']}个校验错误"
        self.log_message.emit(msg)

    def _on_load_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.load_btn.setEnabled(True)
        QMessageBox.critical(self, "错误", f"加载数据失败:\n{error_msg}")

    def _update_stats(self, stats: dict):
        for key, label in self.stats_labels.items():
            val = stats.get(key, 0)
            label.setText(str(val))
            if key in ("anomaly_count", "validation_error_count") and val > 0:
                label.setStyleSheet("color: #fb7185; font-weight: bold; font-size: 18px;")
            else:
                label.setStyleSheet("")

    def _refresh_tree(self):
        self.section_tree.clear()
        tree_data = self.service.get_tree_data()
        search_text = self.search_edit.text().strip()
        anomaly_only = self.anomaly_filter_cb.isChecked()
        error_only = self.error_filter_cb.isChecked()
        chengtu_checked = self.chengtu_filter_cb.isChecked()
        guifan_checked = self.guifan_filter_cb.isChecked()
        for file_path, files in tree_data.items():
            display_path = os.path.basename(file_path) if file_path != "未知路径" else file_path
            path_item = QTreeWidgetItem(self.section_tree, [display_path, "", ""])
            path_item.setExpanded(True)
            path_item.setData(0, Qt.UserRole, "file_path")
            path_item.setData(0, Qt.UserRole + 1, file_path)
            for file_name, sections in files.items():
                file_item = QTreeWidgetItem(path_item, [file_name, "", ""])
                file_item.setData(0, Qt.UserRole, "file_name")
                for sec in sections:
                    if search_text and search_text not in sec["name"] and search_text not in file_name:
                        continue
                    if anomaly_only and not sec["anomaly"]:
                        continue
                    if error_only and not sec["validation_error"]:
                        continue
                    table_type = sec.get("table_type", "")
                    if not chengtu_checked and table_type == "chengtu":
                        continue
                    if not guifan_checked and table_type == "guifan":
                        continue
                    status_parts = []
                    if sec["anomaly"]:
                        status_parts.append("异常")
                    if sec["validation_error"]:
                        status_parts.append("错误")
                    elif sec["validation_warning"]:
                        status_parts.append("警告")
                    status_str = "/".join(status_parts) if status_parts else "正常"
                    table_type_str = ""
                    if sec.get("table_type") == "chengtu":
                        table_type_str = "[成图表]"
                    elif sec.get("table_type") == "guifan":
                        table_type_str = "[规范表]"
                    display_name = f"{table_type_str}{sec['name']}"
                    sec_item = QTreeWidgetItem(file_item, [
                        display_name,
                        str(sec["points"]),
                        status_str
                    ])
                    sec_item.setData(0, Qt.UserRole, sec["key"])
                    if sec["anomaly"]:
                        sec_item.setForeground(2, QColor("#fbbf24"))
                    elif sec["validation_error"]:
                        sec_item.setForeground(2, QColor("#fb7185"))
                    elif sec["validation_warning"]:
                        sec_item.setForeground(2, QColor("#fbbf24"))
                    else:
                        sec_item.setForeground(2, QColor("#34d399"))

    def _on_section_clicked(self, item: QTreeWidgetItem, column: int):
        key = item.data(0, Qt.UserRole)
        if not key or key in ("file_path", "file_name"):
            return
        self._current_section_key = key
        self._load_section_detail(key)

    def _load_section_detail(self, section_key: str):
        sec = self.service.get_section_detail(section_key)
        if not sec:
            self.detail_title.setText("断面数据未找到")
            return
        table_type_display = "成图表" if sec.get("table_type") == "chengtu" else "规范表" if sec.get("table_type") == "guifan" else ""
        title_parts = [sec["name"]]
        if table_type_display:
            title_parts.insert(0, f"[{table_type_display}]")
        if sec.get("file_name"):
            title_parts.append(sec.get("file_name"))
        self.detail_title.setText(" - ".join(title_parts))
        self._render_chart(sec)
        self._fill_points_table(sec)
        self._fill_issues_table(sec)
        self._fill_info_table(sec)

    def _render_chart(self, sec: dict):
        if not HAS_WEB_ENGINE:
            return
        tmp_path = self.service.render_chart_to_temp(self._current_section_key, sec)
        url = QUrl.fromLocalFile(tmp_path)
        url.setQuery(f"t={int(time.time() * 1000)}")
        self.chart_web.load(url)

    def _open_chart_external(self):
        if not self._current_section_key:
            QMessageBox.warning(self, "警告", "请先选择一个断面")
            return
        sec = self.service.get_section_detail(self._current_section_key)
        if not sec:
            return
        output_path = self.service.open_chart_external(self._current_section_key, sec)
        self.log_message.emit(f"已打开断面成图: {output_path}")

    def _fill_points_table(self, sec: dict):
        self._all_points = sec.get("points", [])
        self._current_page = 0
        self._render_current_page()

    def _render_current_page(self):
        total = len(self._all_points)
        page_size = self._page_size
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        start = self._current_page * page_size
        end = min(start + page_size, total)
        page_points = self._all_points[start:end]
        
        display_count = len(page_points)
        row_height = self.points_table.verticalHeader().defaultSectionSize()
        header_height = self.points_table.horizontalHeader().height()
        frame_width = self.points_table.frameWidth() * 2
        grid_lines = display_count + 1
        table_height = row_height * display_count + header_height + frame_width + grid_lines + 6
        self.points_table.setFixedHeight(table_height)
        
        self.points_table.setRowCount(display_count)
        theme = self.theme_manager.get_current_theme()
        for row, p in enumerate(page_points):
            seq_val = p.get("seq", "")
            seq_str = str(int(seq_val)) if seq_val and isinstance(seq_val, (int, float)) else str(seq_val) if seq_val else ""
            items = [
                seq_str,
                str(p.get("feature_desc", "")),
                f"{p.get('distance', 0):.3f}" if p.get("distance") is not None else "",
                f"{p.get('elevation', 0):.3f}" if p.get("elevation") is not None else "",
                f"{p['lon']:.6f}" if p.get("lon") else "",
                f"{p['lat']:.6f}" if p.get("lat") else "",
                str(p.get("roughness", "")),
                "是" if p.get("isFeature") else "",
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                if p.get("isFeature"):
                    item.setBackground(QColor(theme.get('success_bg', '#dcfce7')))
                self.points_table.setItem(row, col, item)
        
        self.points_page_info.setText(f"{start + 1}-{end}/{total}")
        self.points_prev_btn.setEnabled(self._current_page > 0)
        self.points_next_btn.setEnabled(self._current_page < total_pages - 1)

    def _fill_issues_table(self, sec: dict):
        issues = sec.get("validation_issues", [])
        anomaly_details = sec.get("anomaly_details", [])
        all_items = []
        for iss in issues:
            all_items.append({
                "level": iss.get("level", ""),
                "rule": iss.get("desc", iss.get("rule", "")),
                "desc": iss.get("rule", ""),
                "details": iss.get("details", ""),
            })
        for ad in anomaly_details:
            all_items.append({
                "level": "error",
                "rule": ad.get("desc", ad.get("type", "")),
                "desc": ad.get("type", ""),
                "details": ad.get("detail", json.dumps(ad, ensure_ascii=False)),
            })
        self.issues_table.setRowCount(len(all_items))
        for row, item_data in enumerate(all_items):
            level = item_data["level"]
            level_item = QTableWidgetItem("错误" if level == "error" else "警告")
            if level == "error":
                level_item.setForeground(QColor("#fb7185"))
            else:
                level_item.setForeground(QColor("#fbbf24"))
            self.issues_table.setItem(row, 0, level_item)
            self.issues_table.setItem(row, 1, QTableWidgetItem(item_data["rule"]))
            self.issues_table.setItem(row, 2, QTableWidgetItem(item_data["desc"]))
            self.issues_table.setItem(row, 3, QTableWidgetItem(item_data["details"]))

    def _fill_info_table(self, sec: dict):
        while self.info_grid.count():
            item = self.info_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.info_labels.clear()
        
        info_fields = [
            ("断面名称", "name", None),
            ("表格类型", "table_type", lambda v: "成图表" if v == "chengtu" else "规范表" if v == "guifan" else "未知"),
            ("位置", "location", None),
            ("行政区划代码", "district_code", None),
            ("所在沟道", "river_code", None),
            ("断面标识", "is_control_section", None),
            ("断面形态", "section_shape", None),
            ("是否跨县", "is_cross_county", None),
            ("河床底质", "river_bed_material", None),
            ("测量方法", "survey_method", None),
            ("基点经度(°)", "base_lon", lambda v: f"{v:.6f}" if v else ""),
            ("基点纬度(°)", "base_lat", lambda v: f"{v:.6f}" if v else ""),
            ("基点高程(m)", "base_elevation", lambda v: f"{v:.3f}" if v else ""),
            ("方位角(°)", "azimuth", lambda v: f"{v:.2f}" if v else ""),
            ("历史最高水位(m)", "hmz", lambda v: f"{v:.2f}" if v else ""),
            ("成灾水位(m)", "czz", lambda v: f"{v:.2f}" if v else ""),
            ("测量点数", "points", lambda v: str(len(v)) if v else "0"),
            ("分类", "category", None),
            ("来源文件", "source_file", None),
            ("文件名", "file_name", None),
            ("文件路径", "file_path", None),
            ("Sheet名称", "sheet_name", None),
        ]
        
        label_style = "color: #64748b; font-size: 12px; padding: 2px 4px 2px 0;"
        value_style = "color: #1e293b; font-size: 12px; font-weight: 500; padding: 2px 8px 2px 0;"
        
        wrap_fields = ["source_file", "file_name", "file_path"]
        
        for i, (label, field, formatter) in enumerate(info_fields):
            raw_val = sec.get(field, "")
            if formatter:
                val = formatter(raw_val)
            else:
                val = str(raw_val) if raw_val else ""
            
            row = i // 2
            col = (i % 2) * 2
            
            key_label = QLabel(label)
            key_label.setStyleSheet(label_style)
            val_label = QLabel(val)
            val_label.setStyleSheet(value_style)
            val_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            if field in wrap_fields:
                val_label.setWordWrap(True)
            self.info_grid.addWidget(key_label, row, col)
            self.info_grid.addWidget(val_label, row, col + 1)
        
        self.info_grid.setColumnStretch(1, 1)
        self.info_grid.setColumnStretch(3, 1)

    def _on_search(self):
        self._refresh_tree()

    def _on_filter_changed(self):
        self._refresh_tree()

    def _export_report(self):
        output_path, _ = QFileDialog.getSaveFileName(
            self, "导出校验报告", f"断面校验报告_{datetime.now().strftime('%Y%m%d')}.xlsx",
            "Excel文件 (*.xlsx)"
        )
        if output_path:
            try:
                self.service.export_report(output_path)
                QMessageBox.information(self, "完成", f"校验报告已导出到:\n{output_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")

    def _export_anomaly_html(self):
        stats = self.service.get_stats()
        anomaly_count = stats.get("anomaly_count", 0)
        error_count = stats.get("validation_error_count", 0)
        if anomaly_count == 0 and error_count == 0:
            QMessageBox.information(self, "提示", "当前没有异常断面或校验错误断面")
            return
        output_path, _ = QFileDialog.getSaveFileName(
            self, "导出异常断面HTML", f"异常断面汇总_{datetime.now().strftime('%Y%m%d')}.html",
            "HTML文件 (*.html)"
        )
        if output_path:
            try:
                result = self.service.export_anomaly_html(output_path)
                if result:
                    QMessageBox.information(self, "完成", f"异常断面HTML已导出到:\n{output_path}")
                    os.startfile(output_path)
                else:
                    QMessageBox.information(self, "提示", "没有异常断面数据")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")

    def _export_all_html(self):
        stats = self.service.get_stats()
        total_count = stats.get("total_sections", 0)
        if total_count == 0:
            QMessageBox.information(self, "提示", "当前没有断面数据")
            return
        output_path, _ = QFileDialog.getSaveFileName(
            self, "导出全部断面成图", f"全部断面成图_{datetime.now().strftime('%Y%m%d')}.html",
            "HTML文件 (*.html)"
        )
        if output_path:
            try:
                result = self.service.export_all_html(output_path)
                if result:
                    QMessageBox.information(self, "完成", f"全部断面成图已导出到:\n{output_path}")
                    os.startfile(output_path)
                else:
                    QMessageBox.information(self, "提示", "没有断面数据")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")

    def _on_log_btn_clicked(self):
        self.show_log_requested.emit()

    def _on_feature_config_clicked(self):
        dialog = FeatureKeywordsDialog(self)
        dialog.keywords_changed.connect(self._on_keywords_changed)
        dialog.exec()

    def _on_keywords_changed(self, keywords):
        self.log_message.emit(f"特征点关键词已更新: {', '.join(keywords)}")
        self.service.recalculate_sections()
        self._refresh_tree()
        self._update_stats(self.service.get_stats())
        if self._current_section_key:
            self._load_section_detail(self._current_section_key)

    def _preview_excel(self):
        if not self._current_section_key:
            QMessageBox.warning(self, "警告", "请先选择一个断面")
            return
        info = self.service.get_excel_preview_info(self._current_section_key)
        if not info:
            return
        source_file = info["source_file"]
        sheet_name = info["sheet_name"]
        if not source_file or not os.path.exists(source_file):
            QMessageBox.warning(self, "警告", "原始Excel文件不存在")
            return
        dialog = ExcelPreviewDialog(source_file, sheet_name, self)
        dialog.show()

    def _on_page_size_changed(self):
        self._page_size = int(self.points_page_size_combo.currentText())
        self._current_page = 0
        self._render_current_page()

    def _on_prev_page(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._render_current_page()

    def _on_next_page(self):
        total = len(self._all_points)
        total_pages = (total + self._page_size - 1) // self._page_size if total > 0 else 1
        if self._current_page < total_pages - 1:
            self._current_page += 1
            self._render_current_page()
