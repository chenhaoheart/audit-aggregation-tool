# -*- coding: utf-8 -*-
"""
删除文件夹确认对话框 - 确认删除操作前的警告提示
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QGraphicsOpacityEffect
)
from PySide6.QtCore import Signal, Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPalette, QColor

from core.theme_manager import get_theme_manager


class DeleteConfirmDialog(QDialog):
    """删除文件夹确认对话框"""

    delete_confirmed = Signal(str)  # 确认删除信号，发出文件夹路径

    def __init__(self, folder_path: str, parent=None):
        super().__init__(parent)
        self._folder_path = folder_path

        self.setWindowTitle("删除文件夹")
        self.setMinimumSize(450, 220)
        self.setWindowFlags(self.windowFlags() | Qt.Dialog)

        self._init_ui()

    def _init_ui(self):
        """初始化界面"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)

        # 获取主题管理器用于取色
        theme_manager = get_theme_manager()

        # 标题区域 (红色警告图标 + 标题)
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)

        # 警告图标 (使用 Unicode 符号作为警告图标)
        warning_icon = QLabel("\u26A0")  # Unicode 警告符号
        warning_icon.setObjectName("warningIconLabel")
        warning_icon.setStyleSheet("""
            QLabel#warningIconLabel {
                color: #E74C3C;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        title_layout.addWidget(warning_icon)

        # 标题文本
        title_label = QLabel("删除文件夹")
        title_label.setObjectName("sectionHeaderMd")
        title_label.setStyleSheet("""
            QLabel#sectionHeaderMd {
                color: #E74C3C;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        main_layout.addLayout(title_layout)

        # 警告提示信息
        warning_label = QLabel("此操作将永久删除文件夹及其所有内容，不可撤销！")
        warning_label.setObjectName("warningLabel")
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("""
            QLabel#warningLabel {
                color: #C0392B;
                font-size: 14px;
                padding: 8px 12px;
                background-color: rgba(231, 76, 60, 0.1);
                border-radius: 6px;
            }
        """)
        main_layout.addWidget(warning_label)

        # 文件夹路径显示
        path_frame = QFrame()
        path_frame.setObjectName("pathFrame")
        path_frame.setStyleSheet("""
            QFrame#pathFrame {
                background-color: rgba(0, 0, 0, 0.05);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 6px;
                padding: 8px;
            }
        """)
        path_layout = QVBoxLayout()
        path_layout.setContentsMargins(12, 8, 12, 8)
        path_layout.setSpacing(4)

        path_title = QLabel("目标路径:")
        path_title.setObjectName("pathTitle")
        path_title.setStyleSheet("""
            QLabel#pathTitle {
                color: #666666;
                font-size: 12px;
            }
        """)
        path_layout.addWidget(path_title)

        path_label = QLabel(self._folder_path)
        path_label.setObjectName("pathLabel")
        path_label.setWordWrap(True)
        path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        path_label.setStyleSheet("""
            QLabel#pathLabel {
                color: #333333;
                font-size: 13px;
                font-family: "Consolas", "Monaco", monospace;
            }
        """)
        path_layout.addWidget(path_label)

        path_frame.setLayout(path_layout)
        main_layout.addWidget(path_frame)

        main_layout.addStretch()

        # 分隔线
        separator = QFrame()
        separator.setObjectName("dialogSeparator")
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("""
            QFrame#dialogSeparator {
                background-color: rgba(0, 0, 0, 0.1);
                max-height: 1px;
            }
        """)
        main_layout.addWidget(separator)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        # 取消按钮 (灰色)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.cancel_btn.setStyleSheet("""
            QPushButton#cancelBtn {
                background-color: #95A5A6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 14px;
            }
            QPushButton#cancelBtn:hover {
                background-color: #7F8C8D;
            }
            QPushButton#cancelBtn:pressed {
                background-color: #6C7A7D;
            }
        """)

        # 确认删除按钮 (红色背景)
        self.confirm_btn = QPushButton("确认删除")
        self.confirm_btn.setObjectName("confirmDeleteBtn")
        self.confirm_btn.setMinimumWidth(100)
        self.confirm_btn.clicked.connect(self._on_confirm)
        self.confirm_btn.setStyleSheet("""
            QPushButton#confirmDeleteBtn {
                background-color: #E74C3C;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#confirmDeleteBtn:hover {
                background-color: #C0392B;
            }
            QPushButton#confirmDeleteBtn:pressed {
                background-color: #A93226;
            }
        """)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addSpacing(15)
        btn_layout.addWidget(self.confirm_btn)

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

        # 应用主题样式
        self._apply_theme_style()

    def get_folder_path(self) -> str:
        """获取文件夹路径"""
        return self._folder_path

    def _on_confirm(self):
        """确认删除按钮点击"""
        self.delete_confirmed.emit(self._folder_path)
        self.accept()

    def _on_cancel(self):
        """取消按钮点击"""
        self.reject()

    def showEvent(self, event):
        """对话框显示事件——首次显示时播放入场动画"""
        super().showEvent(event)
        if not hasattr(self, '_animated'):
            self._animated = True
            self._animate_entrance()

    def _animate_entrance(self):
        """淡入入场动画：200ms, OutCubic"""
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
        self._entrance_anim = anim  # 保持引用防止被 GC

    def _apply_theme_style(self):
        """应用当前主题样式"""
        theme_manager = get_theme_manager()
        theme = theme_manager.get_current_theme()

        # 设置对话框背景色（Windows 上 QSS 无法控制 QDialog 背景）
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(theme['content_bg']))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # 使用全局样式表
        self.setStyleSheet(theme_manager.get_stylesheet())