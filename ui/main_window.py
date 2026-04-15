# -*- coding: utf-8 -*-
"""
主窗口模块 - 重构版

使用分离的组件：
- DockBar: Dock风格导航栏 (ui/components/dock_bar.py)
- CheckPage: 数据检查页面 (ui/pages/check_page.py)
- ReportPage: 成果报表页面 (ui/report_page.py)
- ShpFormatterPage: SHP格式化页面 (ui/shp_formatter_page.py)
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QFileDialog, QMessageBox,
    QStackedWidget, QFrame
)
from PySide6.QtCore import Qt, Signal, Slot
from datetime import datetime

from ui.components.ant_menu import AntSidebar, ITEM_TO_PAGE
from ui.pages.check_page import CheckPage
from ui.report_page import ReportPage
from ui.shp_formatter_page import ShpFormatterPage
from ui.dialogs.log_dialog import LogDialog
from core.theme_manager import get_theme_manager
from core.effects_manager import ButtonClickHelper, ButtonShadowHelper
from core.page_animator import PageAnimator


class MainWindow(QWidget):
    """
    主窗口 - 精简版

    仅负责：
    - 主布局结构（侧边栏 + 内容区）
    - 页面切换导航
    - 连接各组件信号
    """

    def __init__(self):
        super().__init__()
        self.setObjectName("mainWidget")

        # 主题管理器
        self.theme_manager = get_theme_manager()
        self.theme_manager.theme_changed.connect(self._on_theme_changed)

        # 日志窗口
        self.log_dialog = None

        # 初始化UI
        self._init_ui()

    def _on_theme_changed(self, mode: str):
        """主题切换回调"""
        self.setStyleSheet(self.theme_manager.get_stylesheet())

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("风险隐患调查与影响分析成果审核小工具")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(self.theme_manager.get_stylesheet())

        # ========== 主布局：左侧边栏 + 右侧内容区 ==========
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ========== 左侧 Ant 侧边栏 ==========
        self.ant_sidebar = AntSidebar()
        self.ant_sidebar.item_selected.connect(self._on_menu_item_selected)
        self.ant_sidebar.theme_changed.connect(self._on_sidebar_theme_changed)
        self.ant_sidebar.collapse_toggled.connect(self._on_collapse_toggled)
        main_layout.addWidget(self.ant_sidebar)

        # ========== 右侧内容区 ==========
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_layout = QVBoxLayout()
        content_layout.setSpacing(16)
        content_layout.setContentsMargins(24, 24, 24, 24)

        # 页面容器
        self.page_stack = QStackedWidget()

        # --- 页面1：空间数据检查（使用CheckPage组件） ---
        self.check_page = CheckPage()
        self.check_page.log_message.connect(self._on_log_message)
        self.check_page.export_requested.connect(self._on_export_requested)
        self.page_stack.addWidget(self.check_page)

        # --- 页面2：成果报表展示 ---
        self.report_page = ReportPage()
        self.page_stack.addWidget(self.report_page)

        # --- 页面3：SHP属性格式化 ---
        self.format_page = ShpFormatterPage()
        self.page_stack.addWidget(self.format_page)

        content_layout.addWidget(self.page_stack, 1)
        content_frame.setLayout(content_layout)
        main_layout.addWidget(content_frame, 1)

        self.setLayout(main_layout)

    def _on_sidebar_theme_changed(self, mode: str):
        """侧边栏主题切换"""
        self.setStyleSheet(self.theme_manager.get_stylesheet())

    def _switch_page(self, index: int):
        """切换页面"""
        PageAnimator.fade_transition(self.page_stack, index, duration=220)

    def _on_menu_item_selected(self, item_id: str):
        """菜单项选中回调"""
        page_index = ITEM_TO_PAGE.get(item_id, 0)
        PageAnimator.fade_transition(self.page_stack, page_index, duration=220)
        if item_id.startswith("check_"):
            self.check_page.navigate_to(item_id)

    def _on_collapse_toggled(self, collapsed: bool):
        """侧边栏折叠/展开切换（侧边栏自行处理宽度，此处无需额外操作）"""
        pass

    def _on_log_message(self, msg: str):
        """处理日志消息"""
        if self.log_dialog:
            self.log_dialog.append_log(msg)

        # 显示日志窗口（如果尚未显示）
        if not self.log_dialog or self.log_dialog.isHidden():
            self._show_log_dialog()
            if self.log_dialog:
                self.log_dialog.append_log(msg)

    def _show_log_dialog(self):
        """显示日志对话框"""
        if self.log_dialog is None:
            self.log_dialog = LogDialog(self)
        self.log_dialog.show()

    @Slot(dict)
    def _on_export_requested(self, data: dict):
        """处理导出请求"""
        file_path = data.get('file_path')
        results = data.get('results')

        if not file_path or not results:
            QMessageBox.warning(self, "警告", "没有可导出的结果")
            return

        try:
            import pandas as pd
            from pathlib import Path

            output_dir = Path(file_path).parent
            output_path = output_dir / "检查结果.xlsx"

            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # 水系数据概览
                df_water = pd.DataFrame(results.get('water', []))
                df_water.to_excel(writer, sheet_name='水系数据概览', index=False)

                # 各文件明细
                check_results = results.get('results', [])
                all_records = results.get('all_records', results.get('duanmian', []) + results.get('fangzhi', []) + results.get('yinhuan', []))

                for result in check_results:
                    sheet_name = result['file_name'][:28].replace('.shp', '').replace('.', '_')
                    file_records = [r for r in all_records
                                   if r.get('源文件', '').endswith(result['file_name'])]
                    if file_records:
                        df_records = pd.DataFrame(file_records)
                        original_cols = result.get('original_columns', [])
                        if original_cols:
                            extra_cols = [c for c in df_records.columns if c not in original_cols]
                            df_records = df_records[original_cols + extra_cols]
                        df_records.to_excel(writer, sheet_name=sheet_name, index=False)

                # 汇总统计
                summary_data = []
                for idx, result in enumerate(check_results, 1):
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

            self._log_message(f"已导出: {output_path}")
            QMessageBox.information(self, "完成", f"已导出到:\n{output_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")

    def _log_message(self, msg: str):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {msg}"
        if self.log_dialog:
            self.log_dialog.append_log(log_entry)