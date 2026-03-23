# -*- coding: utf-8 -*-
"""
主窗口模块
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFileDialog, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QGroupBox, QMessageBox, QTabWidget, QAbstractItemView,
    QComboBox, QCheckBox, QScrollArea, QSizePolicy, QDialog, QStackedWidget,
    QFrame, QSpacerItem
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QSize
from PySide6.QtGui import QColor, QFont, QIcon
from core.checker import WaterSystemChecker
from ui.report_page import ReportPage
from datetime import datetime


STYLE_SHEET = """
/* ========== 主窗口 ========== */
QWidget#mainWidget {
    background-color: #f0f2f5;
}

/* ========== 侧边栏 ========== */
QFrame#sidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2c3e50, stop:1 #1a252f);
    border: none;
    min-width: 200px;
    max-width: 200px;
}

QLabel#sidebarTitle {
    font-size: 16px;
    font-weight: bold;
    color: white;
    padding: 20px 15px 10px 15px;
}

QLabel#sidebarSubtitle {
    font-size: 11px;
    color: #95a5a6;
    padding: 0 15px 20px 15px;
}

/* 侧边栏导航按钮 */
QPushButton#sidebarBtn {
    background: transparent;
    color: #bdc3c7;
    border: none;
    border-radius: 0;
    padding: 15px 20px;
    font-size: 14px;
    font-weight: normal;
    text-align: left;
    min-width: 0;
}

QPushButton#sidebarBtn:hover {
    background: rgba(255, 255, 255, 0.08);
    color: white;
}

QPushButton#sidebarBtn:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    color: white;
    font-weight: bold;
}

QPushButton#sidebarBtn:checked:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5a6fd6, stop:1 #6a4190);
}

/* 侧边栏底部版本信息 */
QLabel#sidebarVersion {
    font-size: 10px;
    color: #5d6d7e;
    padding: 15px;
}

/* 侧边栏折叠按钮 */
QPushButton#collapseBtn {
    background: transparent;
    color: #7f8c8d;
    border: 1px solid #34495e;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 12px;
    margin: 0 10px;
    min-width: 0;
}

QPushButton#collapseBtn:hover {
    background: rgba(255, 255, 255, 0.1);
    color: white;
    border-color: #5d6d7e;
}

/* 折叠状态下的侧边栏 */
QFrame#sidebarCollapsed {
    min-width: 60px;
    max-width: 60px;
}

/* 折叠状态下的导航按钮 */
QPushButton#sidebarBtnCollapsed {
    padding: 15px;
    text-align: center;
}

/* ========== 内容区 ========== */
QFrame#contentFrame {
    background-color: #f0f2f5;
    border: none;
}

/* ========== 分组框 ========== */
QGroupBox {
    font-size: 14px;
    font-weight: bold;
    color: #34495e;
    border: 1px solid #e0e4e8;
    border-radius: 10px;
    margin-top: 12px;
    padding: 15px;
    background-color: white;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 10px;
    color: #6b7d9e;
}

/* ========== 输入框 ========== */
QLineEdit {
    border: 1px solid #dcdde1;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px;
    background-color: white;
    color: #2c3e50;
}

QLineEdit:focus {
    border: 2px solid #667eea;
    background-color: white;
}

/* ========== 按钮 ========== */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: bold;
    min-width: 100px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5a6fd6, stop:1 #6a4190);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4a5fc6, stop:1 #5a3180);
}

QPushButton:disabled {
    background: #bdc3c7;
    color: #7f8c8d;
}

QPushButton#exportBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2ecc71, stop:1 #27ae60);
    color: white;
}

QPushButton#exportBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #27ae60, stop:1 #1e8449);
}

QPushButton#exportBtn:disabled {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a9dfbf, stop:1 #82c99a);
    color: #1e8449;
}

QPushButton#validateBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3498db, stop:1 #2980b9);
    color: white;
}

QPushButton#validateBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2980b9, stop:1 #1f6dad);
}

QPushButton#validateBtn:disabled {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #aed6f1, stop:1 #85c1e9);
    color: #1a5276;
}

QPushButton#clearBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e74c3c, stop:1 #c0392b);
}

QPushButton#clearBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #c0392b, stop:1 #a93226);
}

QPushButton#logToggleBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #95a5a6, stop:1 #7f8c8d);
    padding: 5px 15px;
    font-size: 12px;
    min-width: 80px;
}

/* ========== 进度条 ========== */
QProgressBar {
    border: 1px solid #e0e4e8;
    border-radius: 8px;
    text-align: center;
    background-color: #ecf0f1;
    height: 25px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    border-radius: 6px;
}

/* ========== Tab控件 ========== */
QTabWidget::pane {
    border: 1px solid #e0e4e8;
    border-radius: 10px;
    background-color: white;
    padding: 10px;
}

QTabBar::tab {
    background: #f8f9fa;
    color: #7f8c8d;
    border: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: bold;
    min-width: 100px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    color: white;
}

QTabBar::tab:hover:!selected {
    background: #e8eaed;
    color: #2c3e50;
}

/* ========== 表格 ========== */
QTableWidget {
    border: 1px solid #e0e4e8;
    border-radius: 8px;
    background-color: white;
    alternate-background-color: #f8f9fa;
    gridline-color: #ecedef;
    font-size: 12px;
    selection-background-color: #d5e8f7;
}

QTableWidget::item {
    padding: 6px 8px;
    border-bottom: 1px solid #ecedef;
}

QTableWidget::item:selected {
    background-color: #d5e8f7;
    color: #1a1a1a;
}

QTableWidget::item:hover {
    background-color: #e8f4fc;
}

QTableWidget QTableCornerButton::section {
    background-color: #f8f9fa;
    border: none;
}

QHeaderView::section {
    background-color: #f8f9fa;
    color: #2c3e50;
    padding: 10px;
    border: none;
    border-bottom: 1px solid #e0e4e8;
    font-weight: bold;
    font-size: 12px;
}

/* ========== 文本编辑 ========== */
QTextEdit {
    border: 1px solid #dcdde1;
    border-radius: 8px;
    background-color: #1e1e1e;
    color: #ecf0f1;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    padding: 8px;
}

/* ========== 下拉框 ========== */
QComboBox {
    border: 1px solid #dcdde1;
    border-radius: 6px;
    padding: 8px 12px;
    background-color: white;
    color: #2c3e50;
}

QComboBox:hover {
    border: 1px solid #667eea;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

/* ========== 筛选输入框 ========== */
QLineEdit#filterEdit {
    border: 1px solid #dcdde1;
    border-radius: 6px;
    padding: 8px 12px;
    background-color: white;
}

QLineEdit#filterEdit:focus {
    border: 2px solid #667eea;
}

"""


class CheckThread(QThread):
    progress_signal = Signal(str)
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, folder_path, water_system_shp, parent=None):
        super().__init__(parent)
        self.folder_path = folder_path
        self.water_system_shp = water_system_shp

    def run(self):
        try:
            checker = WaterSystemChecker(
                folder_path=self.folder_path,
                water_system_shp=self.water_system_shp
            )
            checker.progress_callback = lambda msg: self.progress_signal.emit(msg)
            results = checker.process_all()
            self.finished_signal.emit({
                'results': results,
                'water_records': checker.water_records,
                'all_records': checker.all_records,
                'water_codes': checker.water_codes,
                'water_names': checker.water_names,
                'water_code_to_name': checker.water_code_to_name,
                'water_original_columns': checker.water_original_columns
            })
        except Exception as e:
            self.error_signal.emit(str(e))


class LogWindow(QDialog):
    log_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("日志输出")
        self.setMinimumSize(700, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.log_text)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self.log_text.clear)
        btn_layout.addWidget(clear_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def append_log(self, msg):
        self.log_text.append(msg)

    def closeEvent(self, event):
        self.hide()
        event.ignore()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.folder_path = ""
        self.water_system_shp = ""
        self.check_thread = None
        self.check_results = None
        self.log_visible = True
        self.original_detail_data = []
        self.original_duanmian_data = []
        self.original_fangzhi_data = []
        self.original_yinhuan_data = []
        self.original_water_data = []
        self.log_window = None
        self.sidebar_collapsed = False  # 侧边栏折叠状态
        self.setObjectName("mainWidget")
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("青海空间数据工具")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(STYLE_SHEET)

        # ========== 主布局：左侧边栏 + 右侧内容区 ==========
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ========== 左侧边栏 ==========
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setSpacing(0)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)

        # 标题区域
        self.title_label = QLabel("⚡ 青海水文")
        self.title_label.setObjectName("sidebarTitle")
        sidebar_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("空间数据处理工具")
        self.subtitle_label.setObjectName("sidebarSubtitle")
        sidebar_layout.addWidget(self.subtitle_label)

        # 分隔线
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setStyleSheet("background-color: #34495e; max-height: 1px;")
        sidebar_layout.addWidget(self.separator)

        # 导航按钮
        self.nav_check_btn = QPushButton("🔍  空间数据检查")
        self.nav_check_btn.setObjectName("sidebarBtn")
        self.nav_check_btn.setCheckable(True)
        self.nav_check_btn.setChecked(True)
        self.nav_check_btn.clicked.connect(lambda: self.switch_page(0))
        sidebar_layout.addWidget(self.nav_check_btn)

        self.nav_report_btn = QPushButton("📊  成果报表展示")
        self.nav_report_btn.setObjectName("sidebarBtn")
        self.nav_report_btn.setCheckable(True)
        self.nav_report_btn.clicked.connect(lambda: self.switch_page(1))
        sidebar_layout.addWidget(self.nav_report_btn)

        # 弹性空间
        sidebar_layout.addStretch()

        # 底部：折叠按钮 + 版本信息
        bottom_layout = QVBoxLayout()
        bottom_layout.setSpacing(5)

        # 折叠按钮
        self.collapse_btn = QPushButton("◀  收起侧栏")
        self.collapse_btn.setObjectName("collapseBtn")
        self.collapse_btn.clicked.connect(self.toggle_sidebar)
        bottom_layout.addWidget(self.collapse_btn)

        # 版本信息
        self.version_label = QLabel("Version 1.0.0")
        self.version_label.setObjectName("sidebarVersion")
        bottom_layout.addWidget(self.version_label)

        sidebar_layout.addLayout(bottom_layout)

        self.sidebar.setLayout(sidebar_layout)
        main_layout.addWidget(self.sidebar)

        # ========== 右侧内容区 ==========
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_layout = QVBoxLayout()
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # 页面容器
        self.page_stack = QStackedWidget()

        # --- 页面1：空间数据检查 ---
        self.page_check = QWidget()
        check_layout = QVBoxLayout()
        check_layout.setSpacing(15)
        check_layout.setContentsMargins(0, 0, 0, 0)

        config_group = QGroupBox("检查配置")
        config_layout = QVBoxLayout()
        config_layout.setSpacing(12)

        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(10)
        folder_label = QLabel("目标文件夹:")
        folder_label.setFixedWidth(100)
        folder_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("选择要检查的文件夹...")
        self.folder_edit.setReadOnly(True)
        folder_btn = QPushButton("浏览...")
        folder_btn.setFixedWidth(80)
        folder_btn.clicked.connect(self.select_folder)
        folder_layout.addWidget(folder_label, 0, Qt.AlignLeft)
        folder_layout.addWidget(self.folder_edit, 1)
        folder_layout.addWidget(folder_btn, 0, Qt.AlignRight)
        config_layout.addLayout(folder_layout)

        water_layout = QHBoxLayout()
        water_layout.setSpacing(10)
        water_label = QLabel("水系文件:")
        water_label.setFixedWidth(100)
        water_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        self.water_edit = QLineEdit()
        self.water_edit.setPlaceholderText("选择水系Shp文件...")
        self.water_edit.setReadOnly(True)
        water_btn = QPushButton("浏览...")
        water_btn.setFixedWidth(80)
        water_btn.clicked.connect(self.select_water_file)
        water_layout.addWidget(water_label, 0, Qt.AlignLeft)
        water_layout.addWidget(self.water_edit, 1)
        water_layout.addWidget(water_btn, 0, Qt.AlignRight)
        config_layout.addLayout(water_layout)

        config_group.setLayout(config_layout)
        check_layout.addWidget(config_group)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.addStretch()
        self.start_btn = QPushButton("开始检查")
        self.start_btn.clicked.connect(self.start_check)
        self.start_btn.setEnabled(False)
        self.start_btn.setFixedWidth(120)
        self.export_btn = QPushButton("导出Excel")
        self.export_btn.setObjectName("exportBtn")
        self.export_btn.clicked.connect(self.export_excel)
        self.export_btn.setEnabled(False)
        self.export_btn.setFixedWidth(120)
        self.clear_btn = QPushButton("清空")
        self.clear_btn.setObjectName("clearBtn")
        self.clear_btn.clicked.connect(self.clear_results)
        self.clear_btn.setFixedWidth(80)
        self.log_toggle_btn = QPushButton("隐藏日志")
        self.log_toggle_btn.setObjectName("logToggleBtn")
        self.log_toggle_btn.setFixedWidth(100)
        self.log_toggle_btn.clicked.connect(self.toggle_log)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.export_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addWidget(self.log_toggle_btn)
        btn_layout.addStretch()
        check_layout.addLayout(btn_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(20)
        check_layout.addWidget(self.progress_bar)

        self.tabs = QTabWidget()
        self.summary_tab = QWidget()
        self.setup_summary_tab()
        self.detail_duanmian_tab = QWidget()
        self.setup_detail_duanmian_tab()
        self.detail_fangzhi_tab = QWidget()
        self.setup_detail_fangzhi_tab()
        self.detail_yinhuan_tab = QWidget()
        self.setup_detail_yinhuan_tab()
        self.water_tab = QWidget()
        self.setup_water_tab()
        self.tabs.addTab(self.summary_tab, "汇总统计")
        self.tabs.addTab(self.detail_duanmian_tab, "断面平面位置")
        self.tabs.addTab(self.detail_fangzhi_tab, "防治对象分布")
        self.tabs.addTab(self.detail_yinhuan_tab, "隐患要素分布")
        self.tabs.addTab(self.water_tab, "水系数据")
        check_layout.addWidget(self.tabs, 1)

        self.page_check.setLayout(check_layout)
        self.page_stack.addWidget(self.page_check)

        # --- 页面2：成果报表展示 ---
        self.page_report = ReportPage()
        self.page_stack.addWidget(self.page_report)

        content_layout.addWidget(self.page_stack, 1)
        content_frame.setLayout(content_layout)
        main_layout.addWidget(content_frame, 1)

        self.setLayout(main_layout)

    def switch_page(self, index):
        """切换页面"""
        self.page_stack.setCurrentIndex(index)
        self.nav_check_btn.setChecked(index == 0)
        self.nav_report_btn.setChecked(index == 1)

    def toggle_sidebar(self):
        """切换侧边栏折叠状态"""
        self.sidebar_collapsed = not self.sidebar_collapsed

        if self.sidebar_collapsed:
            # 折叠状态
            self.sidebar.setFixedWidth(60)

            # 隐藏标题和副标题
            self.title_label.hide()
            self.subtitle_label.hide()
            self.separator.hide()
            self.version_label.hide()

            # 按钮只显示图标
            self.nav_check_btn.setText("🔍")
            self.nav_report_btn.setText("📊")

            # 折叠按钮 - 只显示箭头，居中
            self.collapse_btn.setText("▶")
            self.collapse_btn.setStyleSheet("""
                QPushButton#collapseBtn {
                    margin: 0 5px;
                    padding: 10px 15px;
                }
            """)

        else:
            # 展开状态
            self.sidebar.setFixedWidth(200)

            # 显示标题和副标题
            self.title_label.show()
            self.subtitle_label.show()
            self.separator.show()
            self.version_label.show()

            # 按钮显示完整文字
            self.nav_check_btn.setText("🔍  空间数据检查")
            self.nav_report_btn.setText("📊  成果报表展示")

            # 折叠按钮
            self.collapse_btn.setText("◀  收起侧栏")
            self.collapse_btn.setStyleSheet("")

    def setup_summary_tab(self):
        layout = QVBoxLayout()
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(8)
        self.summary_table.setHorizontalHeaderLabels([
            "序号", "文件名", "状态", "总记录", "有效", "无效", "重复", "有效率"
        ])
        self.summary_table.horizontalHeader().setStretchLastSection(False)
        self.summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.summary_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.summary_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.summary_table.setAlternatingRowColors(True)
        layout.addWidget(self.summary_table)
        self.summary_tab.setLayout(layout)

    def create_filter_layout(self, status_combo, code_edit, name_edit, status_changed_cb, clear_cb):
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        filter_label = QLabel("筛选:")
        filter_label.setStyleSheet("font-weight: bold; color: #2c3e50;")

        status_combo.addItems(["全部", "通过", "不通过"])
        status_combo.setFixedWidth(100)
        status_combo.currentTextChanged.connect(status_changed_cb)

        code_edit.setObjectName("filterEdit")
        code_edit.setPlaceholderText("河流代码...")
        code_edit.textChanged.connect(status_changed_cb)
        code_edit.setFixedWidth(150)

        name_edit.setObjectName("filterEdit")
        name_edit.setPlaceholderText("河流名称...")
        name_edit.textChanged.connect(status_changed_cb)
        name_edit.setFixedWidth(150)

        clear_filter_btn = QPushButton("清除筛选")
        clear_filter_btn.setFixedWidth(80)
        clear_filter_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #95a5a6, stop:1 #7f8c8d);
                padding: 5px 10px;
                font-size: 12px;
                min-width: 60px;
            }
        """)
        clear_filter_btn.clicked.connect(clear_cb)

        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(status_combo)
        filter_layout.addWidget(code_edit)
        filter_layout.addWidget(name_edit)
        filter_layout.addWidget(clear_filter_btn)
        filter_layout.addStretch()

        return filter_layout

    def setup_detail_duanmian_tab(self):
        layout = QVBoxLayout()

        self.duanmian_status_combo = QComboBox()
        self.duanmian_code_edit = QLineEdit()
        self.duanmian_name_edit = QLineEdit()
        filter_layout = self.create_filter_layout(
            self.duanmian_status_combo, self.duanmian_code_edit, self.duanmian_name_edit,
            self.apply_duanmian_filter, self.clear_duanmian_filter
        )
        layout.addLayout(filter_layout)

        self.duanmian_table = QTableWidget()
        self.duanmian_table.horizontalHeader().setStretchLastSection(False)
        self.duanmian_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.duanmian_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.duanmian_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.duanmian_table.setAlternatingRowColors(True)
        layout.addWidget(self.duanmian_table)
        self.detail_duanmian_tab.setLayout(layout)

    def setup_detail_fangzhi_tab(self):
        layout = QVBoxLayout()

        self.fangzhi_status_combo = QComboBox()
        self.fangzhi_code_edit = QLineEdit()
        self.fangzhi_name_edit = QLineEdit()
        filter_layout = self.create_filter_layout(
            self.fangzhi_status_combo, self.fangzhi_code_edit, self.fangzhi_name_edit,
            self.apply_fangzhi_filter, self.clear_fangzhi_filter
        )
        layout.addLayout(filter_layout)

        self.fangzhi_table = QTableWidget()
        self.fangzhi_table.horizontalHeader().setStretchLastSection(False)
        self.fangzhi_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.fangzhi_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.fangzhi_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.fangzhi_table.setAlternatingRowColors(True)
        layout.addWidget(self.fangzhi_table)
        self.detail_fangzhi_tab.setLayout(layout)

    def setup_detail_yinhuan_tab(self):
        layout = QVBoxLayout()

        self.yinhuan_status_combo = QComboBox()
        self.yinhuan_code_edit = QLineEdit()
        self.yinhuan_name_edit = QLineEdit()
        filter_layout = self.create_filter_layout(
            self.yinhuan_status_combo, self.yinhuan_code_edit, self.yinhuan_name_edit,
            self.apply_yinhuan_filter, self.clear_yinhuan_filter
        )
        layout.addLayout(filter_layout)

        self.yinhuan_table = QTableWidget()
        self.yinhuan_table.horizontalHeader().setStretchLastSection(False)
        self.yinhuan_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.yinhuan_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.yinhuan_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.yinhuan_table.setAlternatingRowColors(True)
        layout.addWidget(self.yinhuan_table)
        self.detail_yinhuan_tab.setLayout(layout)

    def setup_water_tab(self):
        layout = QVBoxLayout()

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        filter_label = QLabel("筛选:")
        filter_label.setStyleSheet("font-weight: bold; color: #2c3e50;")

        self.water_filter_status_combo = QComboBox()
        self.water_filter_status_combo.addItems(["全部", "通过", "不通过"])
        self.water_filter_status_combo.setFixedWidth(100)
        self.water_filter_status_combo.currentTextChanged.connect(self.apply_water_filter)

        self.water_filter_code_edit = QLineEdit()
        self.water_filter_code_edit.setObjectName("filterEdit")
        self.water_filter_code_edit.setPlaceholderText("河流代码...")
        self.water_filter_code_edit.textChanged.connect(self.apply_water_filter)
        self.water_filter_code_edit.setFixedWidth(150)

        clear_filter_btn = QPushButton("清除筛选")
        clear_filter_btn.setFixedWidth(80)
        clear_filter_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #95a5a6, stop:1 #7f8c8d);
                padding: 5px 10px;
                font-size: 12px;
                min-width: 60px;
            }
        """)
        clear_filter_btn.clicked.connect(self.clear_water_filter)

        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.water_filter_status_combo)
        filter_layout.addWidget(self.water_filter_code_edit)
        filter_layout.addWidget(clear_filter_btn)
        filter_layout.addStretch()

        layout.addLayout(filter_layout)

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
        self.water_table.setAlternatingRowColors(True)
        layout.addWidget(self.water_table)
        self.water_tab.setLayout(layout)

    def toggle_log(self):
        self.log_visible = not self.log_visible
        if self.log_visible:
            if self.log_window is None:
                self.log_window = LogWindow(self)
                self.log_window.log_signal.connect(self.append_log_message)
            self.log_window.show()
            self.log_toggle_btn.setText("隐藏日志")
        else:
            if self.log_window:
                self.log_window.hide()
            self.log_toggle_btn.setText("显示日志")

    def append_log_message(self, msg):
        if self.log_window:
            self.log_window.append_log(msg)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.folder_path = folder
            self.folder_edit.setText(folder)
            self.update_start_button()

    def select_water_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "选择水系文件", "", "Shp Files (*.shp)"
        )
        if file:
            self.water_system_shp = file
            self.water_edit.setText(file)
            self.update_start_button()

    def update_start_button(self):
        self.start_btn.setEnabled(
            bool(self.folder_path and self.water_system_shp)
        )

    def log_message(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {msg}"
        if self.log_window:
            self.log_window.append_log(log_entry)

    def start_check(self):
        if not self.folder_path or not self.water_system_shp:
            QMessageBox.warning(self, "警告", "请选择文件夹和水系文件")
            return

        self.start_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        if self.log_window:
            self.log_window.log_text.clear()
        self.log_message("开始检查...")

        self.check_thread = CheckThread(self.folder_path, self.water_system_shp)
        self.check_thread.progress_signal.connect(self.on_check_progress)
        self.check_thread.finished_signal.connect(self.on_check_finished)
        self.check_thread.error_signal.connect(self.on_check_error)
        self.check_thread.start()

    @Slot(str)
    def on_check_progress(self, msg):
        self.log_message(msg)

    @Slot(dict)
    def on_check_finished(self, data):
        self.check_results = data
        self.progress_bar.setVisible(False)
        self.start_btn.setEnabled(True)
        self.export_btn.setEnabled(True)

        self.log_message("检查完成!")

        results = data['results']
        water_records = data['water_records']
        all_records = data['all_records']

        duanmian_records = [r for r in all_records if '断面平面位置' in r.get('源文件', '')]
        fangzhi_records = [r for r in all_records if '防治对象分布' in r.get('源文件', '')]
        yinhuan_records = [r for r in all_records if '隐患要素分布' in r.get('源文件', '')]

        self.original_duanmian_data = duanmian_records
        self.original_fangzhi_data = fangzhi_records
        self.original_yinhuan_data = yinhuan_records
        self.original_water_data = water_records

        self.update_summary_table(results)
        self.update_duanmian_table(duanmian_records)
        self.update_fangzhi_table(fangzhi_records)
        self.update_yinhuan_table(yinhuan_records)
        self.update_water_table(water_records)

        passed = sum(1 for r in results if r['status'] == '通过')
        total = len(results)
        self.log_message(f"通过: {passed}/{total}")

        QMessageBox.information(self, "完成", "检查已完成!")

    @Slot(str)
    def on_check_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.start_btn.setEnabled(True)
        self.log_message(f"错误: {error_msg}")
        QMessageBox.critical(self, "错误", f"检查失败:\n{error_msg}")

    def apply_duanmian_filter(self):
        status_filter = self.duanmian_status_combo.currentText()
        code_filter = self.duanmian_code_edit.text().strip().upper()
        name_filter = self.duanmian_name_edit.text().strip().upper()

        filtered_data = []
        for record in self.original_duanmian_data:
            status = str(record.get('验证状态', ''))
            code_val = record.get('河流代码')
            name_val = record.get('河流名称')
            code = str(code_val).upper() if code_val is not None else ''
            name = str(name_val).upper() if name_val is not None else ''

            if status_filter == "通过" and status != '通过':
                continue
            if status_filter == "不通过" and status != '不通过':
                continue
            if code_filter and code_filter not in code:
                continue
            if name_filter and name_filter not in name:
                continue

            filtered_data.append(record)

        self.update_duanmian_table(filtered_data)

    def clear_duanmian_filter(self):
        self.duanmian_status_combo.setCurrentText("全部")
        self.duanmian_code_edit.clear()
        self.duanmian_name_edit.clear()
        self.update_duanmian_table(self.original_duanmian_data)

    def apply_fangzhi_filter(self):
        status_filter = self.fangzhi_status_combo.currentText()
        code_filter = self.fangzhi_code_edit.text().strip().upper()
        name_filter = self.fangzhi_name_edit.text().strip().upper()

        filtered_data = []
        for record in self.original_fangzhi_data:
            status = str(record.get('验证状态', ''))
            code_val = record.get('河流代码')
            name_val = record.get('河流名称')
            code = str(code_val).upper() if code_val is not None else ''
            name = str(name_val).upper() if name_val is not None else ''

            if status_filter == "通过" and status != '通过':
                continue
            if status_filter == "不通过" and status != '不通过':
                continue
            if code_filter and code_filter not in code:
                continue
            if name_filter and name_filter not in name:
                continue

            filtered_data.append(record)

        self.update_fangzhi_table(filtered_data)

    def clear_fangzhi_filter(self):
        self.fangzhi_status_combo.setCurrentText("全部")
        self.fangzhi_code_edit.clear()
        self.fangzhi_name_edit.clear()
        self.update_fangzhi_table(self.original_fangzhi_data)

    def apply_yinhuan_filter(self):
        status_filter = self.yinhuan_status_combo.currentText()
        code_filter = self.yinhuan_code_edit.text().strip().upper()
        name_filter = self.yinhuan_name_edit.text().strip().upper()

        filtered_data = []
        for record in self.original_yinhuan_data:
            status = str(record.get('验证状态', ''))
            code_val = record.get('河流代码')
            name_val = record.get('河流名称')
            code = str(code_val).upper() if code_val is not None else ''
            name = str(name_val).upper() if name_val is not None else ''

            if status_filter == "通过" and status != '通过':
                continue
            if status_filter == "不通过" and status != '不通过':
                continue
            if code_filter and code_filter not in code:
                continue
            if name_filter and name_filter not in name:
                continue

            filtered_data.append(record)

        self.update_yinhuan_table(filtered_data)

    def clear_yinhuan_filter(self):
        self.yinhuan_status_combo.setCurrentText("全部")
        self.yinhuan_code_edit.clear()
        self.yinhuan_name_edit.clear()
        self.update_yinhuan_table(self.original_yinhuan_data)

    def apply_water_filter(self):
        status_filter = self.water_filter_status_combo.currentText()
        code_filter = self.water_filter_code_edit.text().strip().upper()

        filtered_data = []
        for record in self.original_water_data:
            status = str(record.get('验证状态', ''))
            code_val = record.get('河流代码')
            code = str(code_val).upper() if code_val is not None else ''

            if status_filter == "通过" and status != '通过':
                continue
            if status_filter == "不通过" and status != '不通过':
                continue
            if code_filter and code_filter not in code:
                continue

            filtered_data.append(record)

        self.update_water_table(filtered_data)

    def clear_water_filter(self):
        self.water_filter_status_combo.setCurrentText("全部")
        self.water_filter_code_edit.clear()
        self.update_water_table(self.original_water_data)

    def update_summary_table(self, results):
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
                item = QTableWidgetItem(text)
                if result['status'] == '通过':
                    item.setBackground(QColor(230, 255, 230))
                else:
                    item.setBackground(QColor(255, 240, 240))
                self.summary_table.setItem(row, col, item)

    def update_duanmian_table(self, records):
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
        header_labels = list(original_cols) + [
            '河流代码', '河流名称', '编号', '名称',
            '河流代码长度17位', '河流代码在水系中', '河流名称与水系一致',
            '编号长度23位', '编号前17位=河流代码', '编号后5位=名称后5位',
            '断面名称CS格式', 'CS后河流名称', '断面名称与河流名称一致',
            '错误信息', '验证状态'
        ]

        self.duanmian_table.setColumnCount(len(header_labels))
        self.duanmian_table.setHorizontalHeaderLabels(header_labels)
        self.duanmian_table.horizontalHeader().setStretchLastSection(False)
        self.duanmian_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.duanmian_table.setRowCount(len(records))

        for row, record in enumerate(records):
            for col, field in enumerate(header_labels):
                text = str(record.get(field, ''))
                item = QTableWidgetItem(text)
                status = str(record.get('验证状态', ''))
                if status == '通过':
                    item.setBackground(QColor(230, 255, 230))
                elif status == '不通过':
                    item.setBackground(QColor(255, 240, 240))
                self.duanmian_table.setItem(row, col, item)

    def update_fangzhi_table(self, records):
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
        header_labels = list(original_cols) + [
            '河流代码', '河流名称',
            '河流代码长度17位', '河流代码在水系中', '河流名称与水系一致',
            '错误信息', '验证状态'
        ]

        self.fangzhi_table.setColumnCount(len(header_labels))
        self.fangzhi_table.setHorizontalHeaderLabels(header_labels)
        self.fangzhi_table.horizontalHeader().setStretchLastSection(False)
        self.fangzhi_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.fangzhi_table.setRowCount(len(records))

        for row, record in enumerate(records):
            for col, field in enumerate(header_labels):
                text = str(record.get(field, ''))
                item = QTableWidgetItem(text)
                status = str(record.get('验证状态', ''))
                if status == '通过':
                    item.setBackground(QColor(230, 255, 230))
                elif status == '不通过':
                    item.setBackground(QColor(255, 240, 240))
                self.fangzhi_table.setItem(row, col, item)

    def update_yinhuan_table(self, records):
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
        header_labels = list(original_cols) + [
            '河流代码', '河流名称', '编号',
            '河流代码长度17位', '河流代码在水系中', '河流名称与水系一致',
            '编号长度28位', '编号开头6位为数字', '编号7-23位=河流代码',
            '错误信息', '验证状态'
        ]

        self.yinhuan_table.setColumnCount(len(header_labels))
        self.yinhuan_table.setHorizontalHeaderLabels(header_labels)
        self.yinhuan_table.horizontalHeader().setStretchLastSection(False)
        self.yinhuan_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.yinhuan_table.setRowCount(len(records))

        for row, record in enumerate(records):
            for col, field in enumerate(header_labels):
                text = str(record.get(field, ''))
                item = QTableWidgetItem(text)
                status = str(record.get('验证状态', ''))
                if status == '通过':
                    item.setBackground(QColor(230, 255, 230))
                elif status == '不通过':
                    item.setBackground(QColor(255, 240, 240))
                self.yinhuan_table.setItem(row, col, item)

    def update_water_table(self, water_records):
        self.water_table.setRowCount(len(water_records))
        for row, record in enumerate(water_records):
            items = [
                str(record.get('记录序号', '')),
                record.get('河流代码', ''),
                record.get('河流名称', ''),
                record.get('河流代码是否为17位', ''),
                record.get('验证状态', ''),
                record.get('错误信息', '')
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(str(text))
                status = record.get('验证状态', '')
                if status == '通过':
                    item.setBackground(QColor(230, 255, 230))
                elif status == '不通过':
                    item.setBackground(QColor(255, 240, 240))
                self.water_table.setItem(row, col, item)
        self.water_table.resizeRowsToContents()

    def export_excel(self):
        if not self.check_results:
            QMessageBox.warning(self, "警告", "没有可导出的结果")
            return

        file, _ = QFileDialog.getSaveFileName(
            self, "导出Excel", "检查结果.xlsx", "Excel Files (*.xlsx)"
        )
        if file:
            try:
                import pandas as pd
                from pathlib import Path

                output_dir = Path(file).parent
                output_path = output_dir / "检查结果.xlsx"

                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    df_water = pd.DataFrame(self.check_results['water_records'])
                    water_original_cols = self.check_results.get('water_original_columns', [])
                    if water_original_cols:
                        extra_cols = [c for c in df_water.columns if c not in water_original_cols]
                        df_water = df_water[water_original_cols + extra_cols]
                    df_water.to_excel(writer, sheet_name='水系数据概览', index=False)

                    results = self.check_results['results']
                    for result in results:
                        sheet_name = result['file_name'][:28].replace('.shp', '').replace('.', '_')
                        file_records = [r for r in self.check_results['all_records']
                                       if r.get('源文件', '').endswith(result['file_name'])]
                        if file_records:
                            df_records = pd.DataFrame(file_records)
                            original_cols = result.get('original_columns', [])
                            if original_cols:
                                extra_cols = [c for c in df_records.columns if c not in original_cols]
                                df_records = df_records[original_cols + extra_cols]
                            df_records.to_excel(writer, sheet_name=sheet_name, index=False)

                    summary_data = []
                    for idx, result in enumerate(results, 1):
                        summary_data.append({
                            '序号': idx,
                            '文件名': result['file_name'],
                            '状态': result['status'],
                            '总记录数': result['total_records'],
                            '有效记录': result['valid_records'],
                            '无效记录': result['invalid_records'],
                            '重复记录': result.get('duplicate_records', 0)
                        })
                    df_summary = pd.DataFrame(summary_data)
                    df_summary.to_excel(writer, sheet_name='汇总统计', index=False)

                self.log_message(f"已导出: {output_path}")
                QMessageBox.information(self, "完成", f"已导出到:\n{output_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")

    def clear_results(self):
        self.folder_path = ""
        self.water_system_shp = ""
        self.folder_edit.clear()
        self.water_edit.clear()
        self.check_results = None
        self.original_detail_data = []
        self.original_duanmian_data = []
        self.original_fangzhi_data = []
        self.original_yinhuan_data = []
        self.original_water_data = []
        self.summary_table.setRowCount(0)
        self.duanmian_table.setRowCount(0)
        self.fangzhi_table.setRowCount(0)
        self.yinhuan_table.setRowCount(0)
        self.water_table.setRowCount(0)
        if self.log_window:
            self.log_window.log_text.clear()
        self.duanmian_status_combo.setCurrentText("全部")
        self.duanmian_code_edit.clear()
        self.duanmian_name_edit.clear()
        self.fangzhi_status_combo.setCurrentText("全部")
        self.fangzhi_code_edit.clear()
        self.fangzhi_name_edit.clear()
        self.yinhuan_status_combo.setCurrentText("全部")
        self.yinhuan_code_edit.clear()
        self.yinhuan_name_edit.clear()
        self.water_filter_status_combo.setCurrentText("全部")
        self.water_filter_code_edit.clear()
        self.start_btn.setEnabled(False)
        self.export_btn.setEnabled(False)