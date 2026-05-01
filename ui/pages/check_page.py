# -*- coding: utf-8 -*-
"""
空间数据检查页面
"""

import os
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QGroupBox, QMessageBox, QTabWidget, QAbstractItemView,
    QFrame, QScrollArea, QSizePolicy, QCheckBox, QComboBox
)
from PySide6.QtCore import Qt, Signal

from services.check_service import CheckService, scan_shp_files, LAYER_TYPES
from services.filter_service import FilterService
from ui.components.filter_bar import FilterBar
from core.theme_manager import get_theme_manager
from core.effects_manager import ShimmerProgress, StaggerEntrance, TabFadeTransition, ButtonGlowHelper


class CheckPage(QWidget):
    """
    空间数据检查页面

    信号:
        check_started: 检查开始时发出
        check_finished: 检查完成时发出，携带结果数据
        log_message: 日志消息信号
        export_requested: 导出请求信号，携带结果数据
        show_log_requested: 日志显示请求信号
    """

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

        self.original_summary_data = []
        self.original_duanmian_data = []
        self.original_fangzhi_data = []
        self.original_yinhuan_data = []
        self.original_water_data = []

        self._display_summary_data = []
        self._display_duanmian_data = []
        self._display_fangzhi_data = []
        self._display_yinhuan_data = []
        self._display_water_data = []
        self._pagination = {
            'summary': {'page': 1, 'page_size': 20},
            'duanmian': {'page': 1, 'page_size': 20},
            'fangzhi': {'page': 1, 'page_size': 20},
            'yinhuan': {'page': 1, 'page_size': 20},
            'water': {'page': 1, 'page_size': 20},
        }
        self._page_widgets = {}

        self.check_service = CheckService(self)
        self.filter_service = FilterService()

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
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

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

        self.summary_tab = QWidget()
        self._setup_summary_tab()
        self.tabs.addTab(self.summary_tab, "汇总统计")

        self.duanmian_tab = QWidget()
        self._setup_duanmian_tab()
        self.tabs.addTab(self.duanmian_tab, "断面平面位置")

        self.fangzhi_tab = QWidget()
        self._setup_fangzhi_tab()
        self.tabs.addTab(self.fangzhi_tab, "防治对象分布")

        self.yinhuan_tab = QWidget()
        self._setup_yinhuan_tab()
        self.tabs.addTab(self.yinhuan_tab, "隐患要素分布")

        self.water_tab = QWidget()
        self._setup_water_tab()
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
                if isinstance(child, QGroupBox):
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

        self._clear_tables()

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

        self.original_summary_data = data.get('results', [])
        self.original_duanmian_data = data.get('duanmian', [])
        self.original_fangzhi_data = data.get('fangzhi', [])
        self.original_yinhuan_data = data.get('yinhuan', [])
        self.original_water_data = data.get('water', [])

        self._update_summary_table(data.get('results', []))
        self._update_duanmian_table(self.original_duanmian_data)
        self._update_fangzhi_table(self.original_fangzhi_data)
        self._update_yinhuan_table(self.original_yinhuan_data)
        self._update_water_table(self.original_water_data)

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

    # ========== 筛选功能 ==========
    def _apply_summary_filter(self, conditions: dict):
        status = conditions.get('status', '全部')
        name = conditions.get('name', '').strip()

        filtered = []
        for record in self.original_summary_data:
            if status != '全部' and record.get('status') != status:
                continue
            if name and name.upper() not in str(record.get('file_name', '')).upper():
                continue
            filtered.append(record)
        self._update_summary_table(filtered)

    def _clear_summary_filter(self):
        self._update_summary_table(self.original_summary_data)

    def _apply_duanmian_filter(self, conditions: dict):
        filtered = self.filter_service.filter_records(
            self.original_duanmian_data,
            status=conditions.get('status'),
            code=conditions.get('code'),
            name=conditions.get('name')
        )
        self._update_duanmian_table(filtered)

    def _clear_duanmian_filter(self):
        self._update_duanmian_table(self.original_duanmian_data)

    def _apply_fangzhi_filter(self, conditions: dict):
        filtered = self.filter_service.filter_records(
            self.original_fangzhi_data,
            status=conditions.get('status'),
            code=conditions.get('code'),
            name=conditions.get('name')
        )
        self._update_fangzhi_table(filtered)

    def _clear_fangzhi_filter(self):
        self._update_fangzhi_table(self.original_fangzhi_data)

    def _apply_yinhuan_filter(self, conditions: dict):
        filtered = self.filter_service.filter_records(
            self.original_yinhuan_data,
            status=conditions.get('status'),
            code=conditions.get('code'),
            name=conditions.get('name')
        )
        self._update_yinhuan_table(filtered)

    def _clear_yinhuan_filter(self):
        self._update_yinhuan_table(self.original_yinhuan_data)

    def _apply_water_filter(self, conditions: dict):
        filtered = self.filter_service.filter_records(
            self.original_water_data,
            status=conditions.get('status'),
            code=conditions.get('code')
        )
        self._update_water_table(filtered)

    def _clear_water_filter(self):
        self._update_water_table(self.original_water_data)

    # ========== 表格更新 ==========
    def _paginate(self, tab_key: str, data: list):
        pg = self._pagination[tab_key]
        page_size = pg['page_size']
        total = len(data)
        total_pages = max(1, (total + page_size - 1) // page_size)
        current_page = max(1, min(pg['page'], total_pages))
        pg['page'] = current_page
        start = (current_page - 1) * page_size
        end = start + page_size
        self._update_pagination_widgets(tab_key, current_page, total_pages, total)
        return data[start:end]

    def _update_summary_table(self, results: list):
        self._display_summary_data = results
        self._pagination['summary']['page'] = 1
        self._render_summary_page()

    def _render_summary_page(self):
        data = self._display_summary_data
        page_data = self._paginate('summary', data)
        self.summary_table.setRowCount(len(page_data))

        for row, result in enumerate(page_data):
            global_idx = self._pagination['summary']['page_size'] * (self._pagination['summary']['page'] - 1) + row
            items = [
                str(global_idx + 1),
                result['file_name'],
                result['status'],
                str(result['total_records']),
                str(result['valid_records']),
                str(result['invalid_records']),
                str(result.get('duplicate_records', 0)),
                f"{result['valid_records'] / result['total_records'] * 100:.1f}%" if result['total_records'] > 0 else "N/A"
            ]
            for col, text in enumerate(items):
                if col == 2:
                    badge = QLabel("通过" if result['status'] == '通过' else "不通过")
                    badge.setObjectName("badgePass" if result['status'] == '通过' else "badgeFail")
                    badge.setAlignment(Qt.AlignCenter)
                    badge.setFixedHeight(22)
                    self.summary_table.setCellWidget(row, col, badge)
                else:
                    item = QTableWidgetItem(text)
                    self.summary_table.setItem(row, col, item)

    def _update_duanmian_table(self, records: list):
        self._display_duanmian_data = records
        self._pagination['duanmian']['page'] = 1
        self._render_duanmian_page()

    def _render_duanmian_page(self):
        records = self._display_duanmian_data
        if not records:
            self.duanmian_table.setRowCount(0)
            self._update_pagination_widgets('duanmian', 1, 1, 0)
            return

        duanmian_check_fields = [
            '河流代码', '河流名称', '编号', '名称',
            '河流代码长度17位', '河流代码在水系中', '河流名称与水系一致',
            '编号长度23位', '编号前17位=河流代码', '编号后5位=名称后5位',
            '断面名称CS格式', 'CS后河流名称', '断面名称与河流名称一致',
            '错误信息', '验证状态'
        ]

        first_record = records[0]
        original_cols = first_record.get('_original_columns', [])
        if not original_cols:
            original_cols = [k for k in first_record.keys() if k not in duanmian_check_fields and k not in ['源文件', '记录序号', '_original_columns']]
            original_cols = [c for c in original_cols if c not in ['河流代码', '河流名称', '编号', '名称']]
        header_labels = list(original_cols) + duanmian_check_fields

        self.duanmian_table.setColumnCount(len(header_labels))
        self.duanmian_table.setHorizontalHeaderLabels(header_labels)

        page_data = self._paginate('duanmian', records)
        self.duanmian_table.setRowCount(len(page_data))

        status_col = header_labels.index('验证状态') if '验证状态' in header_labels else -1

        for row, record in enumerate(page_data):
            for col, field in enumerate(header_labels):
                text = str(record.get(field, ''))
                if col == status_col:
                    status = record.get('验证状态', '')
                    badge = QLabel("通过" if status == '通过' else "不通过")
                    badge.setObjectName("badgePass" if status == '通过' else "badgeFail")
                    badge.setAlignment(Qt.AlignCenter)
                    badge.setFixedHeight(22)
                    self.duanmian_table.setCellWidget(row, col, badge)
                else:
                    item = QTableWidgetItem(text)
                    self.duanmian_table.setItem(row, col, item)

    def _update_fangzhi_table(self, records: list):
        self._display_fangzhi_data = records
        self._pagination['fangzhi']['page'] = 1
        self._render_fangzhi_page()

    def _render_fangzhi_page(self):
        records = self._display_fangzhi_data
        if not records:
            self.fangzhi_table.setRowCount(0)
            self._update_pagination_widgets('fangzhi', 1, 1, 0)
            return

        fangzhi_check_fields = [
            '河流代码', '河流名称',
            '河流代码长度17位', '河流代码在水系中', '河流名称与水系一致',
            '错误信息', '验证状态'
        ]

        first_record = records[0]
        original_cols = first_record.get('_original_columns', [])
        if not original_cols:
            original_cols = [k for k in first_record.keys() if k not in fangzhi_check_fields and k not in ['源文件', '记录序号', '_original_columns']]
            original_cols = [c for c in original_cols if c not in ['河流代码', '河流名称']]
        header_labels = list(original_cols) + fangzhi_check_fields

        self.fangzhi_table.setColumnCount(len(header_labels))
        self.fangzhi_table.setHorizontalHeaderLabels(header_labels)

        page_data = self._paginate('fangzhi', records)
        self.fangzhi_table.setRowCount(len(page_data))

        status_col = header_labels.index('验证状态') if '验证状态' in header_labels else -1

        for row, record in enumerate(page_data):
            for col, field in enumerate(header_labels):
                text = str(record.get(field, ''))
                if col == status_col:
                    status = record.get('验证状态', '')
                    badge = QLabel("通过" if status == '通过' else "不通过")
                    badge.setObjectName("badgePass" if status == '通过' else "badgeFail")
                    badge.setAlignment(Qt.AlignCenter)
                    badge.setFixedHeight(22)
                    self.fangzhi_table.setCellWidget(row, col, badge)
                else:
                    item = QTableWidgetItem(text)
                    self.fangzhi_table.setItem(row, col, item)

    def _update_yinhuan_table(self, records: list):
        self._display_yinhuan_data = records
        self._pagination['yinhuan']['page'] = 1
        self._render_yinhuan_page()

    def _render_yinhuan_page(self):
        records = self._display_yinhuan_data
        if not records:
            self.yinhuan_table.setRowCount(0)
            self._update_pagination_widgets('yinhuan', 1, 1, 0)
            return

        yinhuan_check_fields = [
            '河流代码', '河流名称', '编号',
            '河流代码长度17位', '河流代码在水系中', '河流名称与水系一致',
            '编号长度28位', '编号开头6位为数字', '编号7-23位=河流代码',
            '错误信息', '验证状态'
        ]

        first_record = records[0]
        original_cols = first_record.get('_original_columns', [])
        if not original_cols:
            original_cols = [k for k in first_record.keys() if k not in yinhuan_check_fields and k not in ['源文件', '记录序号', '_original_columns']]
            original_cols = [c for c in original_cols if c not in ['河流代码', '河流名称', '编号']]
        header_labels = list(original_cols) + yinhuan_check_fields

        self.yinhuan_table.setColumnCount(len(header_labels))
        self.yinhuan_table.setHorizontalHeaderLabels(header_labels)

        page_data = self._paginate('yinhuan', records)
        self.yinhuan_table.setRowCount(len(page_data))

        status_col = header_labels.index('验证状态') if '验证状态' in header_labels else -1

        for row, record in enumerate(page_data):
            for col, field in enumerate(header_labels):
                text = str(record.get(field, ''))
                if col == status_col:
                    status = record.get('验证状态', '')
                    badge = QLabel("通过" if status == '通过' else "不通过")
                    badge.setObjectName("badgePass" if status == '通过' else "badgeFail")
                    badge.setAlignment(Qt.AlignCenter)
                    badge.setFixedHeight(22)
                    self.yinhuan_table.setCellWidget(row, col, badge)
                else:
                    item = QTableWidgetItem(text)
                    self.yinhuan_table.setItem(row, col, item)

    def _update_water_table(self, records: list):
        self._display_water_data = records
        self._pagination['water']['page'] = 1
        self._render_water_page()

    def _render_water_page(self):
        records = self._display_water_data
        page_data = self._paginate('water', records)
        self.water_table.setRowCount(len(page_data))

        for row, record in enumerate(page_data):
            items = [
                str(record.get('记录序号', '')),
                record.get('河流代码', ''),
                record.get('河流名称', ''),
                record.get('河流代码是否为17位', ''),
                record.get('错误信息', ''),
                record.get('验证状态', '')
            ]
            for col, text in enumerate(items):
                if col == 5:
                    status = record.get('验证状态', '')
                    badge = QLabel("通过" if status == '通过' else "不通过")
                    badge.setObjectName("badgePass" if status == '通过' else "badgeFail")
                    badge.setAlignment(Qt.AlignCenter)
                    badge.setFixedHeight(22)
                    self.water_table.setCellWidget(row, col, badge)
                else:
                    item = QTableWidgetItem(str(text))
                    self.water_table.setItem(row, col, item)

    # ========== Tab设置 ==========
    def _create_pagination_bar(self, tab_key: str):
        bar = QWidget()
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(0, 6, 0, 0)
        bar_layout.setSpacing(8)

        size_label = QLabel("每页:")
        size_label.setFixedWidth(36)
        size_combo = QComboBox()
        size_combo.addItems(["10", "20", "50", "100"])
        size_combo.setCurrentText(str(self._pagination[tab_key]['page_size']))
        size_combo.setFixedWidth(72)
        size_combo.currentTextChanged.connect(
            lambda text, k=tab_key: self._change_page_size(k, int(text))
        )

        bar_layout.addWidget(size_label)
        bar_layout.addWidget(size_combo)
        bar_layout.addStretch()

        prev_btn = QPushButton("◀ 上一页")
        prev_btn.setFixedWidth(90)
        prev_btn.clicked.connect(lambda _, k=tab_key: self._prev_page(k))

        page_label = QLabel("第1页/共1页")
        page_label.setAlignment(Qt.AlignCenter)
        page_label.setMinimumWidth(120)

        next_btn = QPushButton("下一页 ▶")
        next_btn.setFixedWidth(90)
        next_btn.clicked.connect(lambda _, k=tab_key: self._next_page(k))

        bar_layout.addWidget(prev_btn)
        bar_layout.addWidget(page_label)
        bar_layout.addWidget(next_btn)

        self._page_widgets[tab_key] = {
            'combo': size_combo,
            'label': page_label,
            'prev': prev_btn,
            'next': next_btn,
        }
        return bar

    def _update_pagination_widgets(self, tab_key: str, current_page: int, total_pages: int, total_count: int = 0):
        widgets = self._page_widgets.get(tab_key)
        if not widgets:
            return
        widgets['label'].setText(f"第{current_page}页/共{total_pages}页" + (f" ({total_count}条)" if total_count else ""))
        widgets['prev'].setEnabled(current_page > 1)
        widgets['next'].setEnabled(current_page < total_pages)

    def _change_page_size(self, tab_key: str, size: int):
        self._pagination[tab_key]['page_size'] = size
        self._pagination[tab_key]['page'] = 1
        self._render_tab_page(tab_key)

    def _prev_page(self, tab_key: str):
        pg = self._pagination[tab_key]
        if pg['page'] > 1:
            pg['page'] -= 1
            self._render_tab_page(tab_key)

    def _next_page(self, tab_key: str):
        pg = self._pagination[tab_key]
        total = len(self._get_display_data(tab_key))
        total_pages = max(1, (total + pg['page_size'] - 1) // pg['page_size'])
        if pg['page'] < total_pages:
            pg['page'] += 1
            self._render_tab_page(tab_key)

    def _get_display_data(self, tab_key: str) -> list:
        return getattr(self, f'_display_{tab_key}_data', [])

    def _render_tab_page(self, tab_key: str):
        render_map = {
            'summary': self._render_summary_page,
            'duanmian': self._render_duanmian_page,
            'fangzhi': self._render_fangzhi_page,
            'yinhuan': self._render_yinhuan_page,
            'water': self._render_water_page,
        }
        render_fn = render_map.get(tab_key)
        if render_fn:
            render_fn()

    def _setup_summary_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 4, 0, 4)

        self.summary_filter_bar = FilterBar(show_name_filter=True)
        self.summary_filter_bar.filter_changed.connect(self._apply_summary_filter)
        self.summary_filter_bar.clear_requested.connect(self._clear_summary_filter)
        layout.addWidget(self.summary_filter_bar)

        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(8)
        self.summary_table.setHorizontalHeaderLabels([
            "序号", "文件名", "状态", "总记录", "有效", "无效", "重复", "有效率"
        ])
        self.summary_table.horizontalHeader().setStretchLastSection(False)
        self.summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.summary_table.setColumnWidth(0, 60)
        self.summary_table.setColumnWidth(1, 200)
        self.summary_table.setColumnWidth(2, 80)
        self.summary_table.setColumnWidth(3, 80)
        self.summary_table.setColumnWidth(4, 80)
        self.summary_table.setColumnWidth(5, 80)
        self.summary_table.setColumnWidth(6, 80)
        self.summary_table.setColumnWidth(7, 80)
        self.summary_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.summary_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.summary_table.setAlternatingRowColors(False)
        self.summary_table.verticalHeader().setVisible(False)
        layout.addWidget(self.summary_table, 1)

        layout.addWidget(self._create_pagination_bar('summary'))
        self.summary_tab.setLayout(layout)

    def _setup_duanmian_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 4, 0, 4)

        self.duanmian_filter_bar = FilterBar(show_name_filter=True)
        self.duanmian_filter_bar.filter_changed.connect(self._apply_duanmian_filter)
        self.duanmian_filter_bar.clear_requested.connect(self._clear_duanmian_filter)
        layout.addWidget(self.duanmian_filter_bar)

        self.duanmian_table = QTableWidget()
        self.duanmian_table.horizontalHeader().setStretchLastSection(False)
        self.duanmian_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.duanmian_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.duanmian_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.duanmian_table.setAlternatingRowColors(False)
        self.duanmian_table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        layout.addWidget(self.duanmian_table, 1)

        layout.addWidget(self._create_pagination_bar('duanmian'))
        self.duanmian_tab.setLayout(layout)

    def _setup_fangzhi_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 4, 0, 4)

        self.fangzhi_filter_bar = FilterBar(show_name_filter=True)
        self.fangzhi_filter_bar.filter_changed.connect(self._apply_fangzhi_filter)
        self.fangzhi_filter_bar.clear_requested.connect(self._clear_fangzhi_filter)
        layout.addWidget(self.fangzhi_filter_bar)

        self.fangzhi_table = QTableWidget()
        self.fangzhi_table.horizontalHeader().setStretchLastSection(False)
        self.fangzhi_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.fangzhi_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.fangzhi_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.fangzhi_table.setAlternatingRowColors(False)
        self.fangzhi_table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        layout.addWidget(self.fangzhi_table, 1)

        layout.addWidget(self._create_pagination_bar('fangzhi'))
        self.fangzhi_tab.setLayout(layout)

    def _setup_yinhuan_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 4, 0, 4)

        self.yinhuan_filter_bar = FilterBar(show_name_filter=True)
        self.yinhuan_filter_bar.filter_changed.connect(self._apply_yinhuan_filter)
        self.yinhuan_filter_bar.clear_requested.connect(self._clear_yinhuan_filter)
        layout.addWidget(self.yinhuan_filter_bar)

        self.yinhuan_table = QTableWidget()
        self.yinhuan_table.horizontalHeader().setStretchLastSection(False)
        self.yinhuan_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.yinhuan_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.yinhuan_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.yinhuan_table.setAlternatingRowColors(False)
        self.yinhuan_table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        layout.addWidget(self.yinhuan_table, 1)

        layout.addWidget(self._create_pagination_bar('yinhuan'))
        self.yinhuan_tab.setLayout(layout)

    def _setup_water_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 4, 0, 4)

        self.water_filter_bar = FilterBar(show_name_filter=False)
        self.water_filter_bar.filter_changed.connect(self._apply_water_filter)
        self.water_filter_bar.clear_requested.connect(self._clear_water_filter)
        layout.addWidget(self.water_filter_bar)

        self.water_table = QTableWidget()
        self.water_table.setColumnCount(6)
        self.water_table.setHorizontalHeaderLabels([
            "记录序号", "河流代码", "河流名称", "河流代码是否为17位",
            "错误信息", "验证状态"
        ])
        self.water_table.horizontalHeader().setStretchLastSection(False)
        self.water_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.water_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.water_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.water_table.setAlternatingRowColors(False)
        self.water_table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        layout.addWidget(self.water_table, 1)

        layout.addWidget(self._create_pagination_bar('water'))
        self.water_tab.setLayout(layout)

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

        self.original_summary_data = []
        self.original_duanmian_data = []
        self.original_fangzhi_data = []
        self.original_yinhuan_data = []
        self.original_water_data = []

        self._display_summary_data = []
        self._display_duanmian_data = []
        self._display_fangzhi_data = []
        self._display_yinhuan_data = []
        self._display_water_data = []
        for tab_key in self._pagination:
            self._pagination[tab_key]['page'] = 1

        self._clear_tables()

        for tab_key in self._page_widgets:
            self._update_pagination_widgets(tab_key, 1, 1, 0)

        self.summary_filter_bar._clear_filter()
        self.duanmian_filter_bar._clear_filter()
        self.fangzhi_filter_bar._clear_filter()
        self.yinhuan_filter_bar._clear_filter()
        self.water_filter_bar._clear_filter()

        self.start_btn.setEnabled(False)
        self.export_btn.setEnabled(False)

        for key in self.stats_labels:
            self.stats_labels[key].setText("0")

        self.check_service.clear_results()

    def _clear_tables(self):
        self.summary_table.setRowCount(0)
        self.duanmian_table.setRowCount(0)
        self.fangzhi_table.setRowCount(0)
        self.yinhuan_table.setRowCount(0)
        self.water_table.setRowCount(0)

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
        self.original_duanmian_data = data.get('duanmian', [])
        self.original_fangzhi_data = data.get('fangzhi', [])
        self.original_yinhuan_data = data.get('yinhuan', [])
        self.original_water_data = data.get('water', [])

        self._update_summary_table(data.get('results', []))
        self._update_duanmian_table(self.original_duanmian_data)
        self._update_fangzhi_table(self.original_fangzhi_data)
        self._update_yinhuan_table(self.original_yinhuan_data)
        self._update_water_table(self.original_water_data)

        self.export_btn.setEnabled(True)

    def _open_gis_map_dialog(self):
        from ui.dialogs.gis_map_dialog import GisMapDialog
        if not hasattr(self, '_gis_dialog') or not self._gis_dialog:
            self._gis_dialog = GisMapDialog(self)
        self._gis_dialog.load_shp_from_check(
            self.folder_path, self.water_system_shp, self.check_results
        )
        self._gis_dialog.show()
        self._gis_dialog.raise_()
        self._gis_dialog.activateWindow()
