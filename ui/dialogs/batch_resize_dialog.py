# -*- coding: utf-8 -*-
"""
批量缩放对话框 - 用于批量调整图片尺寸
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFrame, QSpinBox, QCheckBox,
    QSlider, QGraphicsOpacityEffect
)
from PySide6.QtCore import Signal, Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPalette, QColor

from core.theme_manager import get_theme_manager


class BatchResizeDialog(QDialog):
    """批量缩放对话框"""

    resize_requested = Signal(list, int, int, bool, int)  # 文件列表, 宽度, 高度, 保持宽高比, 质量

    def __init__(self, file_count: int = 0, parent=None):
        super().__init__(parent)
        self._file_count = file_count

        self.setWindowTitle("批量缩放")
        self.setMinimumWidth(400)
        self.setWindowFlags(self.windowFlags() | Qt.Dialog)

        self._init_ui()
        self._apply_theme_style()

    def _init_ui(self):
        """初始化界面"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title_label = QLabel("批量缩放")
        title_label.setObjectName("sectionHeaderMd")
        main_layout.addWidget(title_label)

        # 选中文件数量
        file_count_label = QLabel(f"已选中 {self._file_count} 个文件")
        file_count_label.setObjectName("secondaryLabel")
        main_layout.addWidget(file_count_label)

        # 尺寸设置区域
        size_frame = QFrame()
        size_layout = QGridLayout()
        size_layout.setSpacing(10)
        size_layout.setContentsMargins(0, 0, 0, 0)

        # 宽度
        width_label = QLabel("宽度:")
        width_label.setObjectName("boldLabel")
        self.width_spin = QSpinBox()
        self.width_spin.setMinimum(1)
        self.width_spin.setMaximum(10000)
        self.width_spin.setValue(1920)
        self.width_spin.setFixedWidth(120)
        self.width_spin.setSuffix(" px")
        self.width_spin.valueChanged.connect(self._on_width_changed)

        # 高度
        height_label = QLabel("高度:")
        height_label.setObjectName("boldLabel")
        self.height_spin = QSpinBox()
        self.height_spin.setMinimum(1)
        self.height_spin.setMaximum(10000)
        self.height_spin.setValue(1080)
        self.height_spin.setFixedWidth(120)
        self.height_spin.setSuffix(" px")
        self.height_spin.valueChanged.connect(self._on_height_changed)

        size_layout.addWidget(width_label, 0, 0)
        size_layout.addWidget(self.width_spin, 0, 1)
        size_layout.addWidget(height_label, 1, 0)
        size_layout.addWidget(self.height_spin, 1, 1)

        # 保持宽高比
        self.keep_aspect_check = QCheckBox("保持宽高比")
        self.keep_aspect_check.setChecked(True)
        self.keep_aspect_check.stateChanged.connect(self._on_keep_aspect_changed)
        size_layout.addWidget(self.keep_aspect_check, 2, 0, 1, 2)

        size_frame.setLayout(size_layout)
        main_layout.addWidget(size_frame)

        # 预设按钮区域
        preset_frame = QFrame()
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(10)
        preset_layout.setContentsMargins(0, 0, 0, 0)

        preset_label = QLabel("预设:")
        preset_label.setObjectName("boldLabel")
        preset_layout.addWidget(preset_label)

        preset_1920 = QPushButton("1920x1080")
        preset_1920.setFixedWidth(100)
        preset_1920.clicked.connect(lambda: self._apply_preset(1920, 1080))
        preset_layout.addWidget(preset_1920)

        preset_1280 = QPushButton("1280x720")
        preset_1280.setFixedWidth(100)
        preset_1280.clicked.connect(lambda: self._apply_preset(1280, 720))
        preset_layout.addWidget(preset_1280)

        preset_800 = QPushButton("800x600")
        preset_800.setFixedWidth(100)
        preset_800.clicked.connect(lambda: self._apply_preset(800, 600))
        preset_layout.addWidget(preset_800)

        preset_layout.addStretch()
        preset_frame.setLayout(preset_layout)
        main_layout.addWidget(preset_frame)

        # 质量滑块区域
        quality_frame = QFrame()
        quality_layout = QHBoxLayout()
        quality_layout.setSpacing(10)
        quality_layout.setContentsMargins(0, 0, 0, 0)

        quality_label = QLabel("质量:")
        quality_label.setObjectName("boldLabel")
        quality_layout.addWidget(quality_label)

        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setMinimum(1)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(85)
        self.quality_slider.setSingleStep(1)
        self.quality_slider.setPageStep(10)
        self.quality_slider.valueChanged.connect(self._on_quality_changed)
        quality_layout.addWidget(self.quality_slider)

        self.quality_value_label = QLabel("85%")
        self.quality_value_label.setObjectName("secondaryLabel")
        self.quality_value_label.setFixedWidth(45)
        quality_layout.addWidget(self.quality_value_label)

        quality_frame.setLayout(quality_layout)
        main_layout.addWidget(quality_frame)

        # 分隔线
        separator = QFrame()
        separator.setObjectName("dialogSeparator")
        separator.setFrameShape(QFrame.HLine)
        main_layout.addWidget(separator)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.clicked.connect(self.reject)

        self.confirm_btn = QPushButton("确认")
        self.confirm_btn.setObjectName("confirmBtn")
        self.confirm_btn.setMinimumWidth(100)
        self.confirm_btn.clicked.connect(self._on_confirm)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addSpacing(15)
        btn_layout.addWidget(self.confirm_btn)

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

        # 保存原始宽高比
        self._aspect_ratio = 1920 / 1080
        self._updating = False

    def _on_width_changed(self, value: int):
        """宽度变化时，如果保持宽高比则自动调整高度"""
        if self._updating or not self.keep_aspect_check.isChecked():
            self._aspect_ratio = value / self.height_spin.value()
            return
        self._updating = True
        new_height = int(value / self._aspect_ratio)
        self.height_spin.setValue(max(1, new_height))
        self._updating = False

    def _on_height_changed(self, value: int):
        """高度变化时，如果保持宽高比则自动调整宽度"""
        if self._updating or not self.keep_aspect_check.isChecked():
            self._aspect_ratio = self.width_spin.value() / value
            return
        self._updating = True
        new_width = int(value * self._aspect_ratio)
        self.width_spin.setValue(max(1, new_width))
        self._updating = False

    def _on_keep_aspect_changed(self, state: int):
        """保持宽高比状态变化时，重新计算宽高比"""
        if state == Qt.Checked:
            self._aspect_ratio = self.width_spin.value() / self.height_spin.value()

    def _apply_preset(self, width: int, height: int):
        """应用预设尺寸"""
        self._updating = True
        self.width_spin.setValue(width)
        self.height_spin.setValue(height)
        self._aspect_ratio = width / height
        self._updating = False

    def _on_quality_changed(self, value: int):
        """质量滑块值变化"""
        self.quality_value_label.setText(f"{value}%")

    def _on_confirm(self):
        """确认按钮点击"""
        self.accept()

    def get_resize_params(self) -> tuple:
        """获取缩放参数"""
        return (
            self.width_spin.value(),
            self.height_spin.value(),
            self.keep_aspect_check.isChecked(),
            self.quality_slider.value()
        )

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