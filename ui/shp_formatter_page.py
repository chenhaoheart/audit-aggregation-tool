# -*- coding: utf-8 -*-
"""
SHP图层属性表格式化页面
"""

import os
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QFileDialog, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QGroupBox, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer
from PySide6.QtGui import QColor, QMovie
from core.shp_formatter import ShpFormatter, get_arcgis_python_path, test_arcgis_connection
from ui.field_mapping_dialog import FieldMappingDialog
from ui.arcgis_config_dialog import ArcGISConfigDialog


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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.formatter = ShpFormatter()
        self.format_thread = None
        self._init_ui()
        self._check_environment()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # ========== 环境状态 ==========
        env_group = QGroupBox("环境状态")
        env_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """)
        env_layout = QHBoxLayout()
        env_layout.setContentsMargins(10, 15, 10, 10)
        env_layout.setSpacing(15)

        self.env_label = QLabel("正在检测ArcGIS环境...")
        self.env_label.setStyleSheet("color: #3498db; font-size: 14px; font-weight: bold;")
        env_layout.addWidget(self.env_label, 1)

        self.config_btn = QPushButton("配置ArcGIS")
        self.config_btn.setFixedHeight(28)
        self.config_btn.setStyleSheet("""
            QPushButton {
                background: #4a9eff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 0 12px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #3d8bdb;
            }
        """)
        self.config_btn.clicked.connect(self._show_arcgis_config)
        env_layout.addWidget(self.config_btn)

        env_group.setLayout(env_layout)
        layout.addWidget(env_group)

        # ========== 处理配置 ==========
        config_group = QGroupBox("处理配置")
        config_layout = QVBoxLayout()
        config_layout.setSpacing(12)

        # 输入目录
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        input_label = QLabel("输入目录:")
        input_label.setFixedWidth(100)
        input_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
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
        output_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
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

        # 字段映射配置按钮
        field_layout = QHBoxLayout()
        field_layout.setSpacing(10)

        self.field_btn = QPushButton("字段映射配置")
        self.field_btn.setFixedHeight(32)
        self.field_btn.setCursor(Qt.PointingHandCursor)
        self.field_btn.setStyleSheet("""
            QPushButton {
                background: #4a9eff; color: white;
                border: 1px solid #3a8eef;
                font-size: 13px; padding: 0 12px;
                min-width: 0px;
            }
            QPushButton:hover { background: #3d8bdb; }
        """)
        self.field_btn.clicked.connect(self._show_field_config)
        field_layout.addWidget(self.field_btn)
        field_layout.addStretch()

        config_layout.addLayout(field_layout)

        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.addStretch()

        self.start_btn = QPushButton("开始处理")
        self.start_btn.clicked.connect(self._start_process)
        self.start_btn.setFixedWidth(120)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("clearBtn")
        self.cancel_btn.clicked.connect(self._cancel_process)
        self.cancel_btn.setFixedWidth(80)
        self.cancel_btn.setEnabled(False)

        self.log_btn = QPushButton("查看日志")
        self.log_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #95a5a6, stop:1 #7f8c8d);
                min-width: 80px;
                color: white;
            }
        """)
        self.log_btn.clicked.connect(self._toggle_log)
        self.log_btn.setFixedWidth(100)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.log_btn)
        btn_layout.addStretch()
        config_layout.addLayout(btn_layout)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # ========== 进度条 ==========
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(20)
        layout.addWidget(self.progress_bar)

        # ========== 结果表格 ==========
        result_group = QGroupBox("处理结果")
        result_layout = QVBoxLayout()

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels([
            "序号", "流域/目录", "输出文件", "记录数", "状态"
        ])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.result_table.setColumnWidth(0, 60)
        self.result_table.setColumnWidth(1, 150)
        self.result_table.setColumnWidth(2, 200)
        self.result_table.setColumnWidth(3, 80)
        self.result_table.setColumnWidth(4, 80)
        self.result_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.result_table.setAlternatingRowColors(True)
        result_layout.addWidget(self.result_table)

        result_group.setLayout(result_layout)
        layout.addWidget(result_group, 1)

        # ========== 日志区域 ==========
        self.log_text = QTextEdit()
        self.log_text.setVisible(False)
        self.log_text.setMaximumHeight(200)
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

        self.setLayout(layout)

    def _check_environment(self):
        """检查ArcGIS环境（异步版本）"""
        self.env_label.setText("正在检测ArcGIS环境...")
        self.env_label.setStyleSheet("color: #3498db; font-size: 14px; font-weight: bold;")
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

        if success:
            self.env_label.setText(f"已就绪: {python_path}")
            self.env_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 14px;")
            self.start_btn.setEnabled(True)
            self.start_btn.setToolTip("")
        else:
            self.env_label.setText(f"未就绪: {message}")
            self.env_label.setStyleSheet("color: #e74c3c; font-size: 14px;")
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
                if result.get('status') == '成功':
                    item.setBackground(QColor(230, 255, 230))
                else:
                    item.setBackground(QColor(255, 240, 240))
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

    def _toggle_log(self):
        """切换日志显示"""
        if self.log_text.isVisible():
            self.log_text.setVisible(False)
            self.log_btn.setText("查看日志")
        else:
            self.log_text.setVisible(True)
            self.log_btn.setText("隐藏日志")

    def _append_log(self, msg):
        """追加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {msg}")