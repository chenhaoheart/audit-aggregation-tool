# -*- coding: utf-8 -*-
"""
批量重命名对话框 - 设置重命名模式和参数
"""

from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QLineEdit, QSpinBox, QGraphicsOpacityEffect
)
from PySide6.QtCore import Signal, Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPalette, QColor

from core.theme_manager import get_theme_manager


class BatchRenameDialog(QDialog):
    """批量重命名对话框"""

    rename_requested = Signal(list, str, int)  # 文件列表, 模式, 起始序号

    def __init__(self, file_list: list = None, parent=None):
        super().__init__(parent)
        self._file_list = file_list or []
        self._pattern = "{index}"
        self._start_index = 1

        self.setWindowTitle("批量重命名")
        self.setMinimumSize(450, 300)
        self.setWindowFlags(self.windowFlags() | Qt.Dialog)

        self._init_ui()

    def _init_ui(self):
        """初始化界面"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 获取主题管理器用于取色
        theme_manager = get_theme_manager()

        # 标题
        title_label = QLabel("批量重命名")
        title_label.setObjectName("sectionHeaderMd")
        main_layout.addWidget(title_label)

        # 选中文件数量
        file_count_label = QLabel(f"已选中 {len(self._file_list)} 个文件")
        file_count_label.setObjectName("secondaryLabel")
        main_layout.addWidget(file_count_label)

        # 模式输入框
        pattern_frame = QFrame()
        pattern_layout = QVBoxLayout()
        pattern_layout.setSpacing(5)
        pattern_layout.setContentsMargins(0, 0, 0, 0)

        pattern_label = QLabel("命名模式")
        pattern_label.setObjectName("boldLabel")
        pattern_layout.addWidget(pattern_label)

        self.pattern_input = QLineEdit(self._pattern)
        self.pattern_input.setPlaceholderText("输入命名模式，如: {index}")
        self.pattern_input.setMinimumHeight(36)
        self.pattern_input.textChanged.connect(self._on_pattern_changed)
        pattern_layout.addWidget(self.pattern_input)

        pattern_frame.setLayout(pattern_layout)
        main_layout.addWidget(pattern_frame)

        # 模式帮助说明
        help_frame = QFrame()
        help_layout = QVBoxLayout()
        help_layout.setSpacing(2)
        help_layout.setContentsMargins(0, 0, 0, 0)

        help_title = QLabel("可用占位符:")
        help_title.setObjectName("secondaryLabel")
        help_layout.addWidget(help_title)

        placeholders = [
            "{index} - 序号",
            "{name} - 原文件名",
            "{ext} - 扩展名",
            "{date} - 当前日期"
        ]
        for placeholder in placeholders:
            placeholder_label = QLabel(f"  {placeholder}")
            placeholder_label.setObjectName("secondaryLabel")
            help_layout.addWidget(placeholder_label)

        help_frame.setLayout(help_layout)
        main_layout.addWidget(help_frame)

        # 起始序号输入框
        start_index_frame = QFrame()
        start_index_layout = QHBoxLayout()
        start_index_layout.setSpacing(10)
        start_index_layout.setContentsMargins(0, 0, 0, 0)

        start_index_label = QLabel("起始序号")
        start_index_label.setObjectName("boldLabel")
        start_index_layout.addWidget(start_index_label)

        self.start_index_input = QSpinBox()
        self.start_index_input.setMinimum(0)
        self.start_index_input.setMaximum(999999)
        self.start_index_input.setValue(self._start_index)
        self.start_index_input.setFixedWidth(100)
        self.start_index_input.valueChanged.connect(self._on_start_index_changed)
        start_index_layout.addWidget(self.start_index_input)

        start_index_layout.addStretch()
        start_index_frame.setLayout(start_index_layout)
        main_layout.addWidget(start_index_frame)

        # 预览
        preview_frame = QFrame()
        preview_layout = QVBoxLayout()
        preview_layout.setSpacing(5)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        preview_label = QLabel("预览")
        preview_label.setObjectName("boldLabel")
        preview_layout.addWidget(preview_label)

        self.preview_text = QLabel()
        self.preview_text.setObjectName("secondaryLabel")
        self.preview_text.setWordWrap(True)
        preview_layout.addWidget(self.preview_text)

        preview_frame.setLayout(preview_layout)
        main_layout.addWidget(preview_frame)

        # 更新预览
        self._update_preview()

        # 分隔线
        separator = QFrame()
        separator.setObjectName("dialogSeparator")
        separator.setFrameShape(QFrame.HLine)
        main_layout.addWidget(separator)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.confirm_btn = QPushButton("确定")
        self.confirm_btn.setObjectName("confirmBtn")
        self.confirm_btn.setMinimumWidth(100)
        self.confirm_btn.clicked.connect(self._on_confirm)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.clicked.connect(self._on_cancel)

        btn_layout.addWidget(self.confirm_btn)
        btn_layout.addSpacing(15)
        btn_layout.addWidget(self.cancel_btn)

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

        # 应用主题样式
        self._apply_theme_style()

    def _on_pattern_changed(self, text: str):
        """模式输入变化"""
        self._pattern = text
        self._update_preview()

    def _on_start_index_changed(self, value: int):
        """起始序号变化"""
        self._start_index = value
        self._update_preview()

    def _update_preview(self):
        """更新预览"""
        if not self._file_list:
            self.preview_text.setText("无选中文件")
            return

        # 显示前3个文件的预览
        preview_examples = []
        for i, file_path in enumerate(self._file_list[:3]):
            new_name = self._generate_name(file_path, self._start_index + i)
            from pathlib import Path
            old_name = Path(file_path).name
            preview_examples.append(f"{old_name} -> {new_name}")

        if len(self._file_list) > 3:
            preview_examples.append("...")

        self.preview_text.setText("\n".join(preview_examples))

    def _generate_name(self, file_path: str, index: int) -> str:
        """根据模式生成新文件名"""
        from pathlib import Path
        path = Path(file_path)
        name = path.stem
        ext = path.suffix
        date_str = datetime.now().strftime("%Y%m%d")

        result = self._pattern
        result = result.replace("{index}", str(index))
        result = result.replace("{name}", name)
        result = result.replace("{ext}", ext)
        result = result.replace("{date}", date_str)

        return result

    def get_pattern(self) -> str:
        """获取命名模式"""
        return self._pattern

    def get_start_index(self) -> int:
        """获取起始序号"""
        return self._start_index

    def _on_confirm(self):
        """确定按钮点击"""
        self.rename_requested.emit(self._file_list, self._pattern, self._start_index)
        self.accept()

    def _on_cancel(self):
        """取消按钮点击"""
        self.reject()

    def showEvent(self, event):
        """对话框显示事件"""
        super().showEvent(event)
        if not hasattr(self, '_animated'):
            self._animated = True
            self._animate_entrance()

    def _animate_entrance(self):
        """淡入入场动画"""
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        effect.setOpacity(0.0)

        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(200)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(lambda: self.setGraphicsEffect(None))
        anim.start()
        self._entrance_anim = anim

    def _apply_theme_style(self):
        """应用当前主题样式"""
        theme_manager = get_theme_manager()
        theme = theme_manager.get_current_theme()

        # 设置对话框背景色
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(theme['content_bg']))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # 使用全局样式表
        self.setStyleSheet(theme_manager.get_stylesheet())