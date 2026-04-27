# -*- coding: utf-8 -*-
"""
空间数据检查页面
"""

import os
import json
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QGroupBox, QMessageBox, QTabWidget, QAbstractItemView,
    QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal

from services.check_service import CheckService
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
    """

    # 信号定义
    check_started = Signal()
    check_finished = Signal(dict)
    log_message = Signal(str)
    export_requested = Signal(dict)
    show_log_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # 状态变量
        self.folder_path = ""
        self.water_system_shp = ""
        self.check_results = None

        # 原始数据（用于筛选）
        self.original_summary_data = []
        self.original_duanmian_data = []
        self.original_fangzhi_data = []
        self.original_yinhuan_data = []
        self.original_water_data = []

        # 服务
        self.check_service = CheckService(self)
        self.filter_service = FilterService()

        # 主题管理器
        self.theme_manager = get_theme_manager()

        # 连接服务信号
        self.check_service.progress.connect(self._on_progress)
        self.check_service.finished.connect(self._on_finished)
        self.check_service.error.connect(self._on_error)
        self.check_service.state_changed.connect(self._on_state_changed)

        # 初始化UI
        self._init_ui()
        
        # 初始化按钮状态（如果有默认路径则启用按钮）
        self._update_start_button()

    def _init_ui(self):
        """初始化UI"""
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

        # 左侧图标装饰条
        accent_bar = QFrame()
        accent_bar.setObjectName("accentBar")
        accent_bar.setFixedWidth(4)
        header_layout.addWidget(accent_bar)

        # 标题文字
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        page_title = QLabel("空间数据检查")
        page_title.setObjectName("sectionHeaderLg")
        title_layout.addWidget(page_title)

        page_subtitle = QLabel("选择目标文件夹和水系文件，执行数据质量检查与验证")
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
        # 默认路径
        default_folder = r"D:\github\空间数据检查桌面版-主题-design\青海24示范小流域-药草沟-20260313\630121_大通"
        if os.path.exists(default_folder):
            self.folder_edit.setText(default_folder)
            self.folder_path = default_folder
        folder_btn = QPushButton("浏览...")
        folder_btn.setFixedWidth(80)
        folder_btn.clicked.connect(self._select_folder)
        folder_layout.addWidget(folder_label, 0, Qt.AlignLeft)
        folder_layout.addWidget(self.folder_edit, 1)
        folder_layout.addWidget(folder_btn, 0, Qt.AlignRight)
        config_layout.addLayout(folder_layout)

        # 水系文件选择
        water_layout = QHBoxLayout()
        water_layout.setSpacing(10)
        water_label = QLabel("水系文件:")
        water_label.setFixedWidth(100)
        water_label.setObjectName("boldLabel")
        self.water_edit = QLineEdit()
        self.water_edit.setPlaceholderText("选择水系Shp文件...")
        self.water_edit.setReadOnly(True)
        # 默认水系路径
        default_water = r"C:\Users\chenh\Desktop\青海24示范小流域-药草沟-20260313\大通县最新水系\大通水系.shp"
        if os.path.exists(default_water):
            self.water_edit.setText(default_water)
            self.water_system_shp = default_water
        water_btn = QPushButton("浏览...")
        water_btn.setFixedWidth(80)
        water_btn.clicked.connect(self._select_water_file)
        water_layout.addWidget(water_label, 0, Qt.AlignLeft)
        water_layout.addWidget(self.water_edit, 1)
        water_layout.addWidget(water_btn, 0, Qt.AlignRight)
        config_layout.addLayout(water_layout)

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

        # 进度条 shimmer 动画
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

        # 汇总统计Tab
        self.summary_tab = QWidget()
        self._setup_summary_tab()
        self.tabs.addTab(self.summary_tab, "汇总统计")

        # 断面平面位置Tab
        self.duanmian_tab = QWidget()
        self._setup_duanmian_tab()
        self.tabs.addTab(self.duanmian_tab, "断面平面位置")

        # 防治对象分布Tab
        self.fangzhi_tab = QWidget()
        self._setup_fangzhi_tab()
        self.tabs.addTab(self.fangzhi_tab, "防治对象分布")

        # 隐患要素分布Tab
        self.yinhuan_tab = QWidget()
        self._setup_yinhuan_tab()
        self.tabs.addTab(self.yinhuan_tab, "隐患要素分布")

        # 水系数据Tab
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

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, '_entrance_played'):
            self._entrance_played = True
            StaggerEntrance.play(self, stagger_ms=60, duration=320)

    def _setup_summary_tab(self):
        """设置汇总统计Tab"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 4, 0, 4)

        # 筛选栏
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
        layout.addWidget(self.summary_table)
        self.summary_tab.setLayout(layout)

    def _setup_duanmian_tab(self):
        """设置断面平面位置Tab"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 4, 0, 4)

        # 筛选栏
        self.duanmian_filter_bar = FilterBar(show_name_filter=True)
        self.duanmian_filter_bar.filter_changed.connect(self._apply_duanmian_filter)
        self.duanmian_filter_bar.clear_requested.connect(self._clear_duanmian_filter)
        layout.addWidget(self.duanmian_filter_bar)

        # 表格
        self.duanmian_table = QTableWidget()
        self.duanmian_table.horizontalHeader().setStretchLastSection(False)
        self.duanmian_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.duanmian_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.duanmian_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.duanmian_table.setAlternatingRowColors(False)
        layout.addWidget(self.duanmian_table)

        self.duanmian_tab.setLayout(layout)

    def _setup_fangzhi_tab(self):
        """设置防治对象分布Tab"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 4, 0, 4)

        # 筛选栏
        self.fangzhi_filter_bar = FilterBar(show_name_filter=True)
        self.fangzhi_filter_bar.filter_changed.connect(self._apply_fangzhi_filter)
        self.fangzhi_filter_bar.clear_requested.connect(self._clear_fangzhi_filter)
        layout.addWidget(self.fangzhi_filter_bar)

        # 表格
        self.fangzhi_table = QTableWidget()
        self.fangzhi_table.horizontalHeader().setStretchLastSection(False)
        self.fangzhi_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.fangzhi_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.fangzhi_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.fangzhi_table.setAlternatingRowColors(False)
        layout.addWidget(self.fangzhi_table)

        self.fangzhi_tab.setLayout(layout)

    def _setup_yinhuan_tab(self):
        """设置隐患要素分布Tab"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 4, 0, 4)

        # 筛选栏
        self.yinhuan_filter_bar = FilterBar(show_name_filter=True)
        self.yinhuan_filter_bar.filter_changed.connect(self._apply_yinhuan_filter)
        self.yinhuan_filter_bar.clear_requested.connect(self._clear_yinhuan_filter)
        layout.addWidget(self.yinhuan_filter_bar)

        # 表格
        self.yinhuan_table = QTableWidget()
        self.yinhuan_table.horizontalHeader().setStretchLastSection(False)
        self.yinhuan_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.yinhuan_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.yinhuan_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.yinhuan_table.setAlternatingRowColors(False)
        layout.addWidget(self.yinhuan_table)

        self.yinhuan_tab.setLayout(layout)

    def _setup_water_tab(self):
        """设置水系数据Tab"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 4, 0, 4)

        # 筛选栏（水系数据只需要代码筛选）
        self.water_filter_bar = FilterBar(show_name_filter=False)
        self.water_filter_bar.filter_changed.connect(self._apply_water_filter)
        self.water_filter_bar.clear_requested.connect(self._clear_water_filter)
        layout.addWidget(self.water_filter_bar)

        # 表格
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
        layout.addWidget(self.water_table)

        self.water_tab.setLayout(layout)

    # ========== 导航 ==========
    def navigate_to(self, section: str):
        """根据菜单项切换到对应子视图"""
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

        # 检查配置项：滚动到顶部显示配置区域
        if section == "check_config":
            for child in self.children():
                if isinstance(child, QGroupBox):
                    child.setFocus()
                    break

    # ========== 文件选择 ==========
    def _select_folder(self):
        """选择文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.folder_path = folder
            self.folder_edit.setText(folder)
            self._update_start_button()

    def _select_water_file(self):
        """选择水系文件"""
        file, _ = QFileDialog.getOpenFileName(
            self, "选择水系文件", "", "Shp Files (*.shp)"
        )
        if file:
            self.water_system_shp = file
            self.water_edit.setText(file)
            self._update_start_button()

    def _update_start_button(self):
        has_data = bool(self.folder_path and self.water_system_shp)
        self.start_btn.setEnabled(has_data)
        if hasattr(self, 'gis_map_btn'):
            self.gis_map_btn.setEnabled(has_data)

    # ========== 检查操作 ==========
    def _start_check(self):
        """开始检查"""
        if not self.folder_path or not self.water_system_shp:
            QMessageBox.warning(self, "警告", "请选择文件夹和水系文件")
            return

        # 清空之前的结果
        self._clear_tables()

        # 更新UI状态
        self.start_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        # 启动 shimmer 动画
        self._progress_shimmer.start()

        # 发出信号
        self.check_started.emit()
        self._log("开始检查...")

        # 启动检查服务
        self.check_service.start_check(self.folder_path, self.water_system_shp)

    def _on_progress(self, msg: str):
        """进度回调"""
        self._log(msg)

    def _on_finished(self, data: dict):
        """检查完成回调"""
        self.check_results = data

        # 停止 shimmer 动画
        self._progress_shimmer.stop()
        self.progress_bar.setVisible(False)

        # 更新按钮状态
        self.start_btn.setEnabled(True)
        self.export_btn.setEnabled(True)

        # 保存原始数据
        self.original_summary_data = data.get('results', [])
        self.original_duanmian_data = data.get('duanmian', [])
        self.original_fangzhi_data = data.get('fangzhi', [])
        self.original_yinhuan_data = data.get('yinhuan', [])
        self.original_water_data = data.get('water', [])

        # 更新表格
        self._update_summary_table(data.get('results', []))
        self._update_duanmian_table(self.original_duanmian_data)
        self._update_fangzhi_table(self.original_fangzhi_data)
        self._update_yinhuan_table(self.original_yinhuan_data)
        self._update_water_table(self.original_water_data)

        # 统计
        results = data.get('results', [])
        passed = sum(1 for r in results if r['status'] == '通过')
        failed = sum(1 for r in results if r['status'] == '不通过')
        total = len(results)
        rate = f"{passed / total * 100:.1f}%" if total > 0 else "--"
        self._log(f"检查完成! 通过: {passed}/{total}")

        # 更新统计卡片
        self.stats_labels["total_files"].setText(str(total))
        self.stats_labels["passed"].setText(str(passed))
        self.stats_labels["failed"].setText(str(failed))
        self.stats_labels["pass_rate"].setText(rate)

        # 发出完成信号
        self.check_finished.emit(data)

        QMessageBox.information(self, "完成", "检查已完成!")

    def _on_error(self, msg: str):
        """检查错误回调"""
        self._progress_shimmer.stop()
        self.progress_bar.setVisible(False)
        self.start_btn.setEnabled(True)

        self._log(f"错误: {msg}")
        QMessageBox.critical(self, "错误", f"检查失败:\n{msg}")

    def _on_state_changed(self, state: str):
        """状态变化回调"""
        pass

    # ========== 筛选功能 ==========
    def _apply_summary_filter(self, conditions: dict):
        """应用汇总统计筛选"""
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
        """清除汇总统计筛选"""
        self._update_summary_table(self.original_summary_data)

    def _apply_duanmian_filter(self, conditions: dict):
        """应用断面筛选"""
        filtered = self.filter_service.filter_records(
            self.original_duanmian_data,
            status=conditions.get('status'),
            code=conditions.get('code'),
            name=conditions.get('name')
        )
        self._update_duanmian_table(filtered)

    def _clear_duanmian_filter(self):
        """清除断面筛选"""
        self._update_duanmian_table(self.original_duanmian_data)

    def _apply_fangzhi_filter(self, conditions: dict):
        """应用防治筛选"""
        filtered = self.filter_service.filter_records(
            self.original_fangzhi_data,
            status=conditions.get('status'),
            code=conditions.get('code'),
            name=conditions.get('name')
        )
        self._update_fangzhi_table(filtered)

    def _clear_fangzhi_filter(self):
        """清除防治筛选"""
        self._update_fangzhi_table(self.original_fangzhi_data)

    def _apply_yinhuan_filter(self, conditions: dict):
        """应用隐患筛选"""
        filtered = self.filter_service.filter_records(
            self.original_yinhuan_data,
            status=conditions.get('status'),
            code=conditions.get('code'),
            name=conditions.get('name')
        )
        self._update_yinhuan_table(filtered)

    def _clear_yinhuan_filter(self):
        """清除隐患筛选"""
        self._update_yinhuan_table(self.original_yinhuan_data)

    def _apply_water_filter(self, conditions: dict):
        """应用水系筛选"""
        filtered = self.filter_service.filter_records(
            self.original_water_data,
            status=conditions.get('status'),
            code=conditions.get('code')
        )
        self._update_water_table(filtered)

    def _clear_water_filter(self):
        """清除水系筛选"""
        self._update_water_table(self.original_water_data)

    # ========== 表格更新 ==========
    def _update_summary_table(self, results: list):
        """更新汇总表格"""
        self.summary_table.setRowCount(len(results))

        for row, result in enumerate(results):
            items = [
                str(row + 1),
                result['file_name'],
                result['status'],
                str(result['total_records']),
                str(result['valid_records']),
                str(result['invalid_records']),
                str(result.get('duplicate_records', 0)),
                f"{result['valid_records'] / result['total_records'] * 100:.1f}%" if result['total_records'] > 0 else "N/A"
            ]
            for col, text in enumerate(items):
                if col == 2:  # 状态列使用徽章
                    badge = QLabel("通过" if result['status'] == '通过' else "不通过")
                    badge.setObjectName("badgePass" if result['status'] == '通过' else "badgeFail")
                    badge.setAlignment(Qt.AlignCenter)
                    badge.setFixedHeight(22)
                    self.summary_table.setCellWidget(row, col, badge)
                else:
                    item = QTableWidgetItem(text)
                    self.summary_table.setItem(row, col, item)

    def _update_duanmian_table(self, records: list):
        """更新断面表格"""
        if not records:
            self.duanmian_table.setRowCount(0)
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
        self.duanmian_table.setRowCount(len(records))

        # Find the status column index
        status_col = header_labels.index('验证状态') if '验证状态' in header_labels else -1

        for row, record in enumerate(records):
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
        """更新防治表格"""
        if not records:
            self.fangzhi_table.setRowCount(0)
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
        self.fangzhi_table.setRowCount(len(records))

        status_col = header_labels.index('验证状态') if '验证状态' in header_labels else -1

        for row, record in enumerate(records):
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
        """更新隐患表格"""
        if not records:
            self.yinhuan_table.setRowCount(0)
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
        self.yinhuan_table.setRowCount(len(records))

        status_col = header_labels.index('验证状态') if '验证状态' in header_labels else -1

        for row, record in enumerate(records):
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
        """更新水系表格"""
        self.water_table.setRowCount(len(records))

        for row, record in enumerate(records):
            items = [
                str(record.get('记录序号', '')),
                record.get('河流代码', ''),
                record.get('河流名称', ''),
                record.get('河流代码是否为17位', ''),
                record.get('错误信息', ''),
                record.get('验证状态', '')
            ]
            for col, text in enumerate(items):
                if col == 5:  # 验证状态列使用徽章
                    status = record.get('验证状态', '')
                    badge = QLabel("通过" if status == '通过' else "不通过")
                    badge.setObjectName("badgePass" if status == '通过' else "badgeFail")
                    badge.setAlignment(Qt.AlignCenter)
                    badge.setFixedHeight(22)
                    self.water_table.setCellWidget(row, col, badge)
                else:
                    item = QTableWidgetItem(str(text))
                    self.water_table.setItem(row, col, item)

    # ========== 导出功能 ==========
    def _export_excel(self):
        """导出Excel"""
        if not self.check_results:
            QMessageBox.warning(self, "警告", "没有可导出的结果")
            return

        file, _ = QFileDialog.getSaveFileName(
            self, "导出Excel", "检查结果.xlsx", "Excel Files (*.xlsx)"
        )

        if file:
            # 发出导出请求信号，由主窗口处理实际导出
            self.export_requested.emit({
                'file_path': file,
                'results': self.check_results
            })

    # ========== 清空功能 ==========
    def clear_results(self):
        """清空结果"""
        self.folder_path = ""
        self.water_system_shp = ""
        self.folder_edit.clear()
        self.water_edit.clear()
        self.check_results = None

        # 清空原始数据
        self.original_summary_data = []
        self.original_duanmian_data = []
        self.original_fangzhi_data = []
        self.original_yinhuan_data = []
        self.original_water_data = []

        # 清空表格
        self._clear_tables()

        # 清空筛选栏
        self.summary_filter_bar._clear_filter()
        self.duanmian_filter_bar._clear_filter()
        self.fangzhi_filter_bar._clear_filter()
        self.yinhuan_filter_bar._clear_filter()
        self.water_filter_bar._clear_filter()

        # 更新按钮状态
        self.start_btn.setEnabled(False)
        self.export_btn.setEnabled(False)

        # 重置统计卡片
        for key in self.stats_labels:
            self.stats_labels[key].setText("0")

        # 清空服务结果
        self.check_service.clear_results()

    def _clear_tables(self):
        """清空所有表格"""
        self.summary_table.setRowCount(0)
        self.duanmian_table.setRowCount(0)
        self.fangzhi_table.setRowCount(0)
        self.yinhuan_table.setRowCount(0)
        self.water_table.setRowCount(0)

    # ========== 其他功能 ==========
    def is_checking(self) -> bool:
        """是否正在检查"""
        return self.check_service.is_running

    def _log(self, msg: str):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {msg}"
        self.log_message.emit(log_entry)

    def _toggle_log_request(self):
        """请求切换日志显示"""
        self.show_log_requested.emit()

    def set_results(self, data: dict):
        """设置检查结果（外部设置）"""
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