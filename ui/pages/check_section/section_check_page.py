# -*- coding: utf-8 -*-
import os
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QFileDialog, QProgressBar, QMessageBox, QFrame, QTabWidget,
    QSplitter, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal

from services.section_check_service import SectionCheckService
from core.theme_manager import get_theme_manager
from core.effects_manager import StaggerEntrance, TabFadeTransition, ButtonGlowHelper
from ui.dialogs.log_dialog import LogDialog
from ui.dialogs.feature_keywords_dialog import FeatureKeywordsDialog

from .section_tree_card import SectionTreeCard
from .chart_tab import ChartTab
from .points_tab import PointsTab
from .issues_tab import IssuesTab


class SectionCheckPage(QWidget):
    log_message = Signal(str)
    show_log_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = SectionCheckService()
        self.theme_manager = get_theme_manager()
        self._current_section_key = None
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

        self.tree_card = SectionTreeCard()
        self.tree_card.set_service(self.service)
        self.tree_card.section_clicked.connect(self._on_section_clicked)
        splitter.addWidget(self.tree_card)

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

        self.chart_tab = ChartTab()
        self.chart_tab.set_service(self.service)
        self.chart_tab.log_message.connect(self.log_message.emit)
        self.detail_tabs.addTab(self.chart_tab, "断面成图")

        self.points_tab = PointsTab()
        self.points_tab.set_service(self.service)
        self.points_tab.log_message.connect(self.log_message.emit)
        self.detail_tabs.addTab(self.points_tab, "数据详情")

        self.issues_tab = IssuesTab()
        self.detail_tabs.addTab(self.issues_tab, "校验问题")

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
        self.tree_card.refresh_tree()
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
        theme = self.theme_manager.get_current_theme()
        error_color = theme.get('error_text', '#fb7185')
        for key, label in self.stats_labels.items():
            val = stats.get(key, 0)
            label.setText(str(val))
            if key in ("anomaly_count", "validation_error_count") and val > 0:
                label.setStyleSheet(f"color: {error_color}; font-weight: bold; font-size: 18px;")
            else:
                label.setStyleSheet("")

    def _on_section_clicked(self, key: str):
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
        self.chart_tab.render_chart(section_key, sec)
        self.points_tab.set_current_section_key(section_key)
        self.points_tab.fill_points_table(sec)
        self.issues_tab.fill_issues_table(sec)
        self.points_tab.fill_info_table(sec)

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
        self.tree_card.refresh_tree()
        self._update_stats(self.service.get_stats())
        if self._current_section_key:
            self._load_section_detail(self._current_section_key)
