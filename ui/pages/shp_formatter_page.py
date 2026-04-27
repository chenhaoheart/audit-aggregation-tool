# -*- coding: utf-8 -*-
"""
SHP图层属性表格式化页面
"""

import os
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QFileDialog, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QMessageBox, QAbstractItemView, QFrame, QTabWidget
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer
from PySide6.QtGui import QColor, QMovie
from core.shp_formatter import ShpFormatter, get_arcgis_python_path, test_arcgis_connection
from ui.dialogs.field_mapping_dialog import FieldMappingDialog
from ui.dialogs.arcgis_config_dialog import ArcGISConfigDialog
from core.theme_manager import get_theme_manager
from core.effects_manager import StaggerEntrance, TabFadeTransition, ButtonGlowHelper


class CheckEnvironmentThread(QThread):
    """后台环境检测线程"""
    finished_signal = Signal(bool, str, str)  # 成功, 消息, python路径

    def run(self):
        python_exe = get_arcgis_python_path()
        if python_exe:
            success, error = test_arcgis_connection(python_exe)
            if success:
                self.finished_signal.emit(True, python_exe, python_exe)
            else:
                self.finished_signal.emit(False, error or "连接失败", python_exe)
        else:
            self.finished_signal.emit(False, "未配置ArcGIS Python路径", "")


class FormatThread(QThread):
    """格式化处理线程"""
    progress_signal = Signal(str)
    finished_signal = Signal(list)
    error_signal = Signal(str)

    def __init__(self, formatter: ShpFormatter, input_root: str, output_root: str, parent=None):
        super().__init__(parent)
        self.formatter = formatter
        self.input_root = input_root
        self.output_root = output_root

    def run(self):
        try:
            self.formatter.set_progress_callback(
                lambda msg: self.progress_signal.emit(msg)
            )
            results = self.formatter.process_folder(
                self.input_root,
                self.output_root
            )
            self.finished_signal.emit(results)
        except Exception as e:
            self.error_signal.emit(str(e))


class ShpFormatterPage(QWidget):
    """SHP格式化页面"""

    # 环境检查结果缓存（全局共享）
    _env_checked = False
    _env_success = False
    _env_python_path = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.formatter = ShpFormatter()
        self.format_thread = None
        self._init_ui()
        # 不在初始化时检查，改为延迟检查或手动检查
        self._update_env_status_lazy()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        # 获取主题管理器
        self.theme_manager = get_theme_manager()

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

        page_title = QLabel("SHP属性格式化")
        page_title.setObjectName("sectionHeaderLg")
        title_layout.addWidget(page_title)

        page_subtitle = QLabel("批量处理SHP图层属性表，按流域目录格式化输出")
        page_subtitle.setObjectName("pageSubtitle")
        title_layout.addWidget(page_subtitle)

        header_layout.addLayout(title_layout, 1)
        layout.addWidget(header_card)

        # ========== 环境状态卡片 ==========
        env_card = QFrame()
        env_card.setObjectName("card")
        env_layout = QHBoxLayout(env_card)
        env_layout.setSpacing(15)
        env_layout.setContentsMargins(18, 14, 18, 14)

        self.env_label = QLabel("正在检测ArcGIS环境...")
        self.env_label.setStyleSheet(self.theme_manager.get_inline_style('env_info'))
        env_layout.addWidget(self.env_label, 1)

        self.config_btn = QPushButton("配置ArcGIS")
        self.config_btn.setMinimumHeight(38)
        self.config_btn.setObjectName("validateBtn")
        self.config_btn.clicked.connect(self._show_arcgis_config)
        env_layout.addWidget(self.config_btn)

        self.field_btn = QPushButton("字段映射配置")
        self.field_btn.setMinimumHeight(38)
        self.field_btn.setCursor(Qt.PointingHandCursor)
        self.field_btn.setObjectName("validateBtn")
        self.field_btn.clicked.connect(self._show_field_config)
        env_layout.addWidget(self.field_btn)

        layout.addWidget(env_card)

        # ========== 处理配置卡片 ==========
        config_card = QFrame()
        config_card.setObjectName("card")
        config_layout = QVBoxLayout(config_card)
        config_layout.setSpacing(12)
        config_layout.setContentsMargins(16, 16, 16, 16)

        # 输入目录
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        input_label = QLabel("输入目录:")
        input_label.setFixedWidth(100)
        input_label.setObjectName("boldLabel")
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("选择包含流域文件夹的根目录...")
        self.input_edit.setReadOnly(True)
        input_btn = QPushButton("浏览...")
        input_btn.setFixedWidth(80)
        input_btn.clicked.connect(self._select_input_dir)
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_edit, 1)
        input_layout.addWidget(input_btn)
        config_layout.addLayout(input_layout)

        # 输出目录
        output_layout = QHBoxLayout()
        output_layout.setSpacing(10)
        output_label = QLabel("输出目录:")
        output_label.setFixedWidth(100)
        output_label.setObjectName("boldLabel")
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("选择输出目录...")
        self.output_edit.setReadOnly(True)
        output_btn = QPushButton("浏览...")
        output_btn.setFixedWidth(80)
        output_btn.clicked.connect(self._select_output_dir)
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_edit, 1)
        output_layout.addWidget(output_btn)
        config_layout.addLayout(output_layout)

        # 操作按钮（开始处理 + 取消 居中显示）
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        btn_layout.addStretch()

        self.start_btn = QPushButton("开始处理")
        self.start_btn.clicked.connect(self._start_process)
        self.start_btn.setFixedWidth(120)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("clearBtn")
        self.cancel_btn.clicked.connect(self._cancel_process)
        self.cancel_btn.setFixedWidth(80)
        self.cancel_btn.setEnabled(False)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.cancel_btn)

        btn_layout.addStretch()
        config_layout.addLayout(btn_layout)

        layout.addWidget(config_card)

        # ========== 进度条 ==========
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(12)
        layout.addWidget(self.progress_bar)

        # ========== 结果+日志 Tab ==========
        self.result_tabs = QTabWidget()
        self.result_tabs.setObjectName("resultTabs")

        # Tab 1: 处理结果
        result_tab = QWidget()
        result_tab_layout = QVBoxLayout(result_tab)
        result_tab_layout.setSpacing(0)
        result_tab_layout.setContentsMargins(0, 4, 0, 4)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels([
            "序号", "流域/目录", "输出文件", "记录数", "状态"
        ])
        self.result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.result_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.result_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.result_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.result_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.result_table.setColumnWidth(0, 60)
        self.result_table.setColumnWidth(1, 150)
        self.result_table.setColumnWidth(2, 200)
        self.result_table.setColumnWidth(3, 80)
        self.result_table.setColumnWidth(4, 80)
        self.result_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.result_table.setAlternatingRowColors(False)
        result_tab_layout.addWidget(self.result_table)

        self.result_tabs.addTab(result_tab, "处理结果")

        # Tab 2: 运行日志
        log_tab = QWidget()
        log_tab_layout = QVBoxLayout(log_tab)
        log_tab_layout.setSpacing(0)
        log_tab_layout.setContentsMargins(0, 4, 0, 4)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setObjectName("logText")
        log_tab_layout.addWidget(self.log_text)

        self.result_tabs.addTab(log_tab, "运行日志")

        layout.addWidget(self.result_tabs, 1)

        self.setLayout(layout)

        self._tab_fade = TabFadeTransition(self.result_tabs, duration=180)
        self._tab_fade.attach()

        for btn in self.findChildren(QPushButton):
            if btn.objectName() in ('startBtn',):
                ButtonGlowHelper.install(btn)

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, '_entrance_played'):
            self._entrance_played = True
            StaggerEntrance.play(self, stagger_ms=60, duration=320)

    def _update_env_status_lazy(self):
        """延迟更新环境状态（不执行实际检查）"""
        from core.config_manager import ArcGISConfig

        config = ArcGISConfig()
        python_path = config.python_path
        verified = config.verified

        # 如果之前已验证成功，直接显示已就绪
        if python_path and verified:
            ShpFormatterPage._env_checked = True
            ShpFormatterPage._env_success = True
            ShpFormatterPage._env_python_path = python_path
            self.env_label.setText(f"已就绪: {python_path}")
            self.env_label.setStyleSheet(get_theme_manager().get_inline_style('env_success'))
            self.start_btn.setEnabled(True)
            self.start_btn.setToolTip("")
        elif python_path:
            # 路径已配置但未验证
            self.env_label.setText(f"待验证: {python_path} (点击开始处理时验证)")
            self.env_label.setStyleSheet(get_theme_manager().get_inline_style('env_warning'))
            self.start_btn.setEnabled(True)
            self.start_btn.setToolTip("环境路径已配置，点击开始处理时将自动验证")
        else:
            # 未配置
            self.env_label.setText("未配置: 请点击'配置ArcGIS'设置Python路径")
            self.env_label.setStyleSheet(get_theme_manager().get_inline_style('env_error'))
            self.start_btn.setEnabled(False)
            self.start_btn.setToolTip("请点击'配置ArcGIS'设置Python路径")

    def _check_environment(self):
        """检查ArcGIS环境（异步版本）"""
        self.env_label.setText("正在检测ArcGIS环境...")
        self.env_label.setStyleSheet(get_theme_manager().get_inline_style('env_info'))
        self.start_btn.setEnabled(False)
        self.start_btn.setToolTip("正在检测环境...")

        loading_dots = ["......", "o.....", ".o....", "..o...", "...o..", "....o.", ".....o", "......"]
        self._loading_index = 0
        self._loading_timer = QTimer(self)
        self._loading_timer.timeout.connect(lambda: self._update_loading())
        self._loading_timer.start(150)

        self.check_thread = CheckEnvironmentThread()
        self.check_thread.finished_signal.connect(self._on_environment_checked)
        self.check_thread.start()

    def _update_loading(self):
        """更新loading动画"""
        loading_dots = ["......", "o.....", ".o....", "..o...", "...o..", "....o.", ".....o", "......"]
        self._loading_index = (self._loading_index + 1) % len(loading_dots)
        self.env_label.setText(f"正在检测ArcGIS环境 {loading_dots[self._loading_index]}")

    def _on_environment_checked(self, success: bool, message: str, python_path: str):
        """环境检测完成回调"""
        if hasattr(self, '_loading_timer'):
            self._loading_timer.stop()

        # 更新缓存
        ShpFormatterPage._env_checked = True
        ShpFormatterPage._env_success = success
        ShpFormatterPage._env_python_path = python_path

        if success:
            self.env_label.setText(f"已就绪: {python_path}")
            self.env_label.setStyleSheet(get_theme_manager().get_inline_style('env_success'))
            self.start_btn.setEnabled(True)
            self.start_btn.setToolTip("")
        else:
            self.env_label.setText(f"未就绪: {message}")
            self.env_label.setStyleSheet(get_theme_manager().get_inline_style('env_error'))
            self.start_btn.setEnabled(False)
            self.start_btn.setToolTip("请点击'配置ArcGIS'设置Python路径")

    def _select_input_dir(self):
        """选择输入目录"""
        folder = QFileDialog.getExistingDirectory(self, "选择输入目录")
        if folder:
            self.input_path = folder
            self.input_edit.setText(folder)
            self._update_start_button()

    def _select_output_dir(self):
        """选择输出目录"""
        folder = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if folder:
            self.output_path = folder
            self.output_edit.setText(folder)
            self._update_start_button()

    def _update_start_button(self):
        """更新开始按钮状态"""
        has_input = bool(self.input_edit.text())
        has_output = bool(self.output_edit.text())
        has_arcgis = get_arcgis_python_path() is not None
        self.start_btn.setEnabled(has_input and has_output and has_arcgis)

    def _show_field_config(self):
        """显示字段映射配置对话框"""
        dialog = FieldMappingDialog(self)
        if dialog.exec():
            self._append_log("字段映射配置已更新")

    def _show_arcgis_config(self):
        """显示ArcGIS环境配置对话框"""
        dialog = ArcGISConfigDialog(self)
        if dialog.exec():
            self._check_environment()

    def _start_process(self):
        """开始处理"""
        input_root = self.input_edit.text()
        output_root = self.output_edit.text()

        if not input_root or not output_root:
            QMessageBox.warning(self, "警告", "请选择输入和输出目录")
            return

        python_exe = get_arcgis_python_path()
        if not python_exe:
            QMessageBox.critical(self, "错误", "未配置ArcGIS Python路径")
            return

        # 如果环境未验证，先验证
        if not ShpFormatterPage._env_checked:
            self.env_label.setText("正在验证ArcGIS环境...")
            self.env_label.setStyleSheet(get_theme_manager().get_inline_style('env_info'))
            self.start_btn.setEnabled(False)

            # 在后台验证环境
            self._pre_check_thread = CheckEnvironmentThread()
            self._pre_check_thread.finished_signal.connect(
                lambda success, msg, path: self._on_pre_check_done(success, msg, path, input_root, output_root)
            )
            self._pre_check_thread.start()
            return

        # 环境已验证成功，直接开始处理
        self._do_process(input_root, output_root)

    def _on_pre_check_done(self, success: bool, message: str, python_path: str, input_root: str, output_root: str):
        """预检查完成回调"""
        from core.config_manager import ArcGISConfig

        ShpFormatterPage._env_checked = True
        ShpFormatterPage._env_success = success
        ShpFormatterPage._env_python_path = python_path

        if success:
            self.env_label.setText(f"已就绪: {python_path}")
            self.env_label.setStyleSheet(get_theme_manager().get_inline_style('env_success'))
            # 更新配置文件中的验证状态
            config = ArcGISConfig()
            config.save_python_path(python_path, verified=True)
            self._do_process(input_root, output_root)
        else:
            self.env_label.setText(f"验证失败: {message}")
            self.env_label.setStyleSheet(get_theme_manager().get_inline_style('env_error'))
            self.start_btn.setEnabled(True)
            QMessageBox.critical(self, "错误", f"ArcGIS环境验证失败:\n{message}")

    def _do_process(self, input_root: str, output_root: str):
        """执行实际处理"""
        python_exe = get_arcgis_python_path()
        if not python_exe:
            QMessageBox.critical(self, "错误", "未配置ArcGIS Python路径")
            return

        # 清空之前的结果
        self.result_table.setRowCount(0)
        self.log_text.clear()

        # 更新UI状态
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self._append_log(f"开始处理: {datetime.now().strftime('%H:%M:%S')}")

        # 创建并启动处理线程
        self.format_thread = FormatThread(
            self.formatter,
            input_root,
            output_root
        )
        self.format_thread.progress_signal.connect(self._on_progress)
        self.format_thread.finished_signal.connect(self._on_finished)
        self.format_thread.error_signal.connect(self._on_error)
        self.format_thread.start()

    def _cancel_process(self):
        """取消处理"""
        if self.format_thread and self.format_thread.isRunning():
            self.formatter.cancel()
            self._append_log("正在取消...")

    def _on_progress(self, msg):
        """处理进度回调"""
        self._append_log(msg)

    def _on_finished(self, results):
        """处理完成"""
        self.progress_bar.setVisible(False)
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

        self._append_log(f"处理完成: {datetime.now().strftime('%H:%M:%S')}")

        # 更新结果表格
        self.result_table.setRowCount(len(results))
        for row, result in enumerate(results):
            items = [
                str(row + 1),
                result.get('basin', ''),
                result.get('output_file', ''),
                str(result.get('record_count', 0)),
                result.get('status', '')
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                theme = get_theme_manager().get_current_theme()
                if result.get('status') == '成功':
                    item.setBackground(QColor(theme['success_bg']))
                else:
                    item.setBackground(QColor(theme['error_bg']))
                self.result_table.setItem(row, col, item)

        # 统计
        success_count = sum(1 for r in results if r.get('status') == '成功')
        self._append_log(f"成功处理: {success_count}/{len(results)}")

        QMessageBox.information(self, "完成", f"处理完成!\n成功: {success_count}/{len(results)}")

    def _on_error(self, error_msg):
        """处理错误"""
        self.progress_bar.setVisible(False)
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

        self._append_log(f"错误: {error_msg}")
        QMessageBox.critical(self, "错误", f"处理失败:\n{error_msg}")

    def _append_log(self, msg):
        """追加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {msg}")