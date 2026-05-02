# -*- coding: utf-8 -*-
import os
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QFrame, QScrollArea, QSizePolicy, QCheckBox, QMessageBox,
    QTabWidget, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal

from services.check_service import CheckService, scan_shp_files, LAYER_TYPES
from core.theme_manager import get_theme_manager
from core.effects_manager import ShimmerProgress, StaggerEntrance, TabFadeTransition, ButtonGlowHelper

from .summary_tab import SummaryTab
from .duanmian_tab import DuanmianTab
from .fangzhi_tab import FangzhiTab
from .yinhuan_tab import YinhuanTab
from .water_tab import WaterTab


class CheckPage(QWidget):

    check_started = Signal()
    check_finished = Signal(dict)
    log_message = Signal(str)
    export_requested = Signal(dict)
    show_log_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.folder_path = ""
        self.water_system_shp = None
        self.spatial_folder = None
        self.check_results = None
        self.layer_paths = {}

        self.check_service = CheckService(self)
        self.theme_manager = get_theme_manager()

        self.check_service.progress.connect(self._on_progress)
        self.check_service.finished.connect(self._on_finished)
        self.check_service.error.connect(self._on_error)
        self.check_service.state_changed.connect(self._on_state_changed)

        self._init_ui()
        self._update_start_button()

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

        # ========== 页面标题区 ==========
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

        page_title = QLabel("空间数据检查")
        page_title.setObjectName("sectionHeaderLg")
        title_layout.addWidget(page_title)

        page_subtitle = QLabel("选择目标文件夹，自动识别SHP图层，执行数据质量检查与验证")
        page_subtitle.setObjectName("pageSubtitle")
        title_layout.addWidget(page_subtitle)

        header_layout.addLayout(title_layout, 1)
        layout.addWidget(header_card)

        # ========== 检查配置卡片 ==========
        card = QFrame()
        card.setObjectName("card")
        config_layout = QVBoxLayout(card)
        config_layout.setSpacing(12)
        config_layout.setContentsMargins(16, 16, 16, 16)

        # 文件夹选择
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(10)
        folder_label = QLabel("目标文件夹:")
        folder_label.setFixedWidth(100)
        folder_label.setObjectName("boldLabel")
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("选择要检查的文件夹...")
        self.folder_edit.setReadOnly(True)
        default_folder = r"D:\github\空间数据检查桌面版-主题-design\青海24示范小流域-药草沟-20260313\630121_大通"
        if os.path.exists(default_folder):
            self.folder_edit.setText(default_folder)
            self.folder_path = default_folder
        folder_btn = QPushButton("浏览...")
        folder_btn.setFixedWidth(80)
        folder_btn.clicked.connect(self._select_folder)
        rescan_btn = QPushButton("重新扫描")
        rescan_btn.setFixedWidth(80)
        rescan_btn.setObjectName("clearBtn")
        rescan_btn.clicked.connect(self._rescan_folder)
        folder_layout.addWidget(folder_label, 0, Qt.AlignLeft)
        folder_layout.addWidget(self.folder_edit, 1)
        folder_layout.addWidget(rescan_btn, 0, Qt.AlignRight)
        folder_layout.addWidget(folder_btn, 0, Qt.AlignRight)
        config_layout.addLayout(folder_layout)

        # ========== SHP图层匹配清单（可折叠） ==========
        self._layer_collapsed = False
        collapse_header = QHBoxLayout()
        self._layer_collapse_btn = QPushButton("▼ SHP图层匹配清单")
        self._layer_collapse_btn.setObjectName("collapseSectionBtn")
        self._layer_collapse_btn.setFlat(True)
        self._layer_collapse_btn.setCursor(Qt.PointingHandCursor)
        self._layer_collapse_btn.clicked.connect(self._toggle_layer_section)
        collapse_header.addWidget(self._layer_collapse_btn)
        collapse_header.addStretch()
        config_layout.addLayout(collapse_header)

        self.layer_table = QTableWidget()
        self.layer_table.setObjectName("layerTable")
        self.layer_table.setColumnCount(5)
        self.layer_table.setHorizontalHeaderLabels([
            "图层类型", "匹配状态", "SHP文件路径", "启用", "操作"
        ])
        self.layer_table.horizontalHeader().setStretchLastSection(False)
        self.layer_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.layer_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.layer_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.layer_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.layer_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.layer_table.setColumnWidth(0, 130)
        self.layer_table.setColumnWidth(3, 55)
        self.layer_table.setColumnWidth(4, 90)
        self.layer_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.layer_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.layer_table.setAlternatingRowColors(False)
        self.layer_table.verticalHeader().setVisible(False)
        row_height = 36
        self.layer_table.verticalHeader().setDefaultSectionSize(row_height)
        config_layout.addWidget(self.layer_table)

        self._init_layer_table()

        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        self.start_btn = QPushButton("开始检查")
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.clicked.connect(self._start_check)
        self.start_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)

        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setFrameShadow(QFrame.Sunken)
        btn_layout.addWidget(separator1)

        self.clear_btn = QPushButton("清空")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setObjectName("clearBtn")
        self.clear_btn.clicked.connect(self.clear_results)
        btn_layout.addWidget(self.clear_btn)

        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        btn_layout.addWidget(separator2)

        self.gis_map_btn = QPushButton("打开GIS地图")
        self.gis_map_btn.setCursor(Qt.PointingHandCursor)
        self.gis_map_btn.setEnabled(False)
        self.gis_map_btn.clicked.connect(self._open_gis_map_dialog)
        btn_layout.addWidget(self.gis_map_btn)

        self.export_btn = QPushButton("导出Excel")
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setObjectName("exportBtn")
        self.export_btn.clicked.connect(self._export_excel)
        self.export_btn.setEnabled(False)
        btn_layout.addWidget(self.export_btn)

        separator3 = QFrame()
        separator3.setFrameShape(QFrame.VLine)
        separator3.setFrameShadow(QFrame.Sunken)
        btn_layout.addWidget(separator3)

        self.log_btn = QPushButton("显示日志")
        self.log_btn.setCursor(Qt.PointingHandCursor)
        self.log_btn.setObjectName("logToggleBtn")
        self.log_btn.clicked.connect(self._toggle_log_request)
        btn_layout.addWidget(self.log_btn)

        btn_layout.addStretch()
        config_layout.addLayout(btn_layout)

        layout.addWidget(card)

        # ========== 进度条 ==========
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(12)
        layout.addWidget(self.progress_bar)

        self._progress_shimmer = ShimmerProgress(self.progress_bar)
        theme = self.theme_manager.get_current_theme()
        self._progress_shimmer.set_colors(
            theme.get('progress_chunk_start', '#667eea'),
            theme.get('progress_chunk_end', '#764ba2'),
            "#ffffff30"
        )

        # ========== 统计卡片 ==========
        stats_card = QFrame()
        stats_card.setObjectName("card")
        stats_layout = QHBoxLayout(stats_card)
        stats_layout.setSpacing(20)
        stats_layout.setContentsMargins(18, 10, 18, 10)
        self.stats_labels = {}
        for key, label_text in [("total_files", "文件数"), ("passed", "通过"),
                                 ("failed", "不通过"), ("pass_rate", "通过率")]:
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

        # ========== 结果Tab区域 ==========
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

        for btn in self.findChildren(QPushButton):
            if btn.objectName() in ('startBtn',):
                ButtonGlowHelper.install(btn)

        if self.folder_path:
            self._do_scan()

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, '_entrance_played'):
            self._entrance_played = True
            StaggerEntrance.play(self, stagger_ms=60, duration=320)

    # ========== 图层匹配清单 ==========
    def _toggle_layer_section(self):
        self._layer_collapsed = not self._layer_collapsed
        if self._layer_collapsed:
            self.layer_table.setVisible(False)
            self._layer_collapse_btn.setText("▶ SHP图层匹配清单")
        else:
            self.layer_table.setVisible(True)
            self._layer_collapse_btn.setText("▼ SHP图层匹配清单")

    def _init_layer_table(self):
        self.layer_table.setRowCount(len(LAYER_TYPES))
        row_height = self.layer_table.verticalHeader().defaultSectionSize()
        header_height = self.layer_table.horizontalHeader().height()
        self.layer_table.setFixedHeight(
            len(LAYER_TYPES) * row_height + header_height + 2
        )
        self.layer_checkboxes = {}
        self.layer_path_edits = {}
        self.layer_select_btns = {}

        for row, lt in enumerate(LAYER_TYPES):
            key = lt['key']
            name_item = QTableWidgetItem(lt['name'])
            name_item.setTextAlignment(Qt.AlignCenter)
            self.layer_table.setItem(row, 0, name_item)

            status_label = QLabel("未匹配")
            status_label.setObjectName("layerBadgeFail")
            status_label.setAlignment(Qt.AlignCenter)
            status_label.setFixedHeight(22)
            self.layer_table.setCellWidget(row, 1, status_label)

            path_edit = QLineEdit()
            path_edit.setReadOnly(True)
            path_edit.setPlaceholderText("未找到匹配文件...")
            path_edit.setObjectName("layerPathEdit")
            self.layer_table.setCellWidget(row, 2, path_edit)
            self.layer_path_edits[key] = path_edit

            checkbox = QCheckBox()
            checkbox.setChecked(True)
            self.layer_table.setCellWidget(row, 3, checkbox)
            self.layer_checkboxes[key] = checkbox

            select_btn = QPushButton("选择文件")
            select_btn.setFixedWidth(80)
            select_btn.clicked.connect(lambda checked, k=key: self._select_layer_file(k))
            self.layer_table.setCellWidget(row, 4, select_btn)
            self.layer_select_btns[key] = select_btn

            self.layer_paths[key] = ''

    def _update_layer_table(self, scan_result: dict):
        layers = scan_result.get('layers', {})
        self.spatial_folder = scan_result.get('spatial_folder')

        for key, info in layers.items():
            path = info.get('path', '')
            matched = info.get('matched', False)
            self.layer_paths[key] = path

            if key in self.layer_path_edits:
                self.layer_path_edits[key].setText(path if matched else '')
                self.layer_path_edits[key].setPlaceholderText(
                    path if matched else '未找到匹配文件...'
                )

            if key in self.layer_checkboxes:
                self.layer_checkboxes[key].setChecked(matched)

            row = self._get_layer_row(key)
            if row is not None:
                status_label = self.layer_table.cellWidget(row, 1)
                if status_label:
                    if matched:
                        status_label.setText("已匹配")
                        status_label.setObjectName("layerBadgePass")
                    else:
                        status_label.setText("未匹配")
                        status_label.setObjectName("layerBadgeFail")
                    status_label.setStyle(status_label.style())

        self.water_system_shp = self.layer_paths.get('water', '') or None
        self._update_start_button()

    def _get_layer_row(self, key: str):
        for row, lt in enumerate(LAYER_TYPES):
            if lt['key'] == key:
                return row
        return None

    def _select_layer_file(self, layer_key: str):
        file, _ = QFileDialog.getOpenFileName(
            self, f"选择{dict((lt['key'], lt['name']) for lt in LAYER_TYPES).get(layer_key, '')}文件", "", "Shp Files (*.shp)"
        )
        if file:
            self.layer_paths[layer_key] = file
            if layer_key in self.layer_path_edits:
                self.layer_path_edits[layer_key].setText(file)

            row = self._get_layer_row(layer_key)
            if row is not None:
                status_label = self.layer_table.cellWidget(row, 1)
                if status_label:
                    status_label.setText("已匹配")
                    status_label.setObjectName("layerBadgePass")
                    status_label.setStyle(status_label.style())

            if layer_key in self.layer_checkboxes:
                self.layer_checkboxes[layer_key].setChecked(True)

            if layer_key == 'water':
                self.water_system_shp = file

            self._update_start_button()

    def _do_scan(self):
        if not self.folder_path:
            return
        scan_result = scan_shp_files(self.folder_path)
        self._update_layer_table(scan_result)
        matched_count = sum(1 for v in self.layer_paths.values() if v)
        self._log(f"扫描完成: 发现 {matched_count} 个匹配图层")

    def _rescan_folder(self):
        self._do_scan()

    # ========== 导航 ==========
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

        if section == "check_config":
            for child in self.children():
                if isinstance(child, QFrame):
                    child.setFocus()
                    break

    # ========== 文件选择 ==========
    def _select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.folder_path = folder
            self.folder_edit.setText(folder)
            self._do_scan()

    def _update_start_button(self):
        has_folder = bool(self.folder_path)
        self.start_btn.setEnabled(has_folder)
        if hasattr(self, 'gis_map_btn'):
            self.gis_map_btn.setEnabled(has_folder and self.check_results is not None)

    # ========== 检查操作 ==========
    def _start_check(self):
        if not self.folder_path:
            QMessageBox.warning(self, "警告", "请选择目标文件夹")
            return

        if not self.spatial_folder:
            self.spatial_folder = self.folder_path

        self.summary_tab.clear_data()
        self.duanmian_tab.clear_data()
        self.fangzhi_tab.clear_data()
        self.yinhuan_tab.clear_data()
        self.water_tab.clear_data()

        self.start_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self._progress_shimmer.start()

        self.check_started.emit()
        self._log("开始检查...")

        water_shp = self.layer_paths.get('water', '') or None
        if water_shp and not self.layer_checkboxes.get('water', QCheckBox()).isChecked():
            water_shp = None

        self.water_system_shp = water_shp
        self.check_service.start_check(self.spatial_folder, water_shp)

    def _on_progress(self, msg: str):
        self._log(msg)

    def _on_finished(self, data: dict):
        self.check_results = data

        self._progress_shimmer.stop()
        self.progress_bar.setVisible(False)

        self.start_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        if hasattr(self, 'gis_map_btn'):
            self.gis_map_btn.setEnabled(True)

        self.summary_tab.update_data(data.get('results', []))
        self.duanmian_tab.update_data(data.get('duanmian', []))
        self.fangzhi_tab.update_data(data.get('fangzhi', []))
        self.yinhuan_tab.update_data(data.get('yinhuan', []))
        self.water_tab.update_data(data.get('water', []))

        results = data.get('results', [])
        passed = sum(1 for r in results if r['status'] == '通过')
        failed = sum(1 for r in results if r['status'] != '通过')
        total = len(results)
        rate = f"{passed / total * 100:.1f}%" if total > 0 else "--"
        self._log(f"检查完成! 通过: {passed}/{total}")

        self.stats_labels["total_files"].setText(str(total))
        self.stats_labels["passed"].setText(str(passed))
        self.stats_labels["failed"].setText(str(failed))
        self.stats_labels["pass_rate"].setText(rate)

        self.check_finished.emit(data)

        has_water = data.get('has_water_system', True)
        if not has_water:
            QMessageBox.information(self, "完成", "检查已完成!\n\n⚠️ 缺少水系SHP文件，已跳过水系关联检查，仅执行图层自检。")
        else:
            QMessageBox.information(self, "完成", "检查已完成!")

    def _on_error(self, msg: str):
        self._progress_shimmer.stop()
        self.progress_bar.setVisible(False)
        self.start_btn.setEnabled(True)

        self._log(f"错误: {msg}")
        QMessageBox.critical(self, "错误", f"检查失败:\n{msg}")

    def _on_state_changed(self, state: str):
        pass

    # ========== 导出功能 ==========
    def _export_excel(self):
        if not self.check_results:
            QMessageBox.warning(self, "警告", "没有可导出的结果")
            return

        file, _ = QFileDialog.getSaveFileName(
            self, "导出Excel", "检查结果.xlsx", "Excel Files (*.xlsx)"
        )

        if file:
            self.export_requested.emit({
                'file_path': file,
                'results': self.check_results
            })

    # ========== 清空功能 ==========
    def clear_results(self):
        self.folder_path = ""
        self.water_system_shp = None
        self.spatial_folder = None
        self.check_results = None
        self.folder_edit.clear()
        self.layer_paths = {}

        for key in self.layer_path_edits:
            self.layer_path_edits[key].setText('')
            self.layer_path_edits[key].setPlaceholderText('未找到匹配文件...')
            self.layer_checkboxes[key].setChecked(True)
            self.layer_paths[key] = ''

            row = self._get_layer_row(key)
            if row is not None:
                status_label = self.layer_table.cellWidget(row, 1)
                if status_label:
                    status_label.setText("未匹配")
                    status_label.setObjectName("layerBadgeFail")
                    status_label.setStyle(status_label.style())

        self.summary_tab.clear_data()
        self.duanmian_tab.clear_data()
        self.fangzhi_tab.clear_data()
        self.yinhuan_tab.clear_data()
        self.water_tab.clear_data()

        self.start_btn.setEnabled(False)
        self.export_btn.setEnabled(False)

        for key in self.stats_labels:
            self.stats_labels[key].setText("0")

        self.check_service.clear_results()

    # ========== 其他功能 ==========
    def is_checking(self) -> bool:
        return self.check_service.is_running

    def _log(self, msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {msg}"
        self.log_message.emit(log_entry)

    def _toggle_log_request(self):
        self.show_log_requested.emit()

    def set_results(self, data: dict):
        self.check_results = data

        self.summary_tab.update_data(data.get('results', []))
        self.duanmian_tab.update_data(data.get('duanmian', []))
        self.fangzhi_tab.update_data(data.get('fangzhi', []))
        self.yinhuan_tab.update_data(data.get('yinhuan', []))
        self.water_tab.update_data(data.get('water', []))

        self.export_btn.setEnabled(True)

    def _open_gis_map_dialog(self):
        from ui.dialogs.gis_map_dialog import GisMapDialog
        if not hasattr(self, '_gis_dialog') or not self._gis_dialog:
            self._gis_dialog = GisMapDialog(self)
        self._gis_dialog.load_shp_from_check(
            self.folder_path, self.water_system_shp, self.check_results
        )
        self._gis_dialog.show()
