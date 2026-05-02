# -*- coding: utf-8 -*-
"""
Dock 风格菜单栏 - macOS Dock 风格
圆角大图标，极简设计，支持折叠
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve

from core.theme_manager import get_theme_manager


# 导航项配置：(图标, 文字, 页面索引)
NAV_ITEMS = [
    ("\u25c6", "空间数据检查", 0),
    ("\u25a0", "成果报表展示", 1),
    ("\u25b2", "断面数据检查", 2),
    ("\u2699", "SHP属性格式化", 3),
]

# Dock 栏宽度
WIDTH_EXPANDED = 72
WIDTH_COLLAPSED = 72


class DockBar(QFrame):
    """Dock 风格导航栏"""

    page_changed = Signal(int)
    theme_changed = Signal(str)
    collapse_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_manager = get_theme_manager()
        self._collapsed = False
        self._animating = False

        self.setObjectName("dockBar")
        self.setFixedWidth(WIDTH_EXPANDED)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 12, 8, 8)

        # ========== 系统简介 ==========
        self.title_label = QLabel("\u25c6 审核汇集")
        self.title_label.setObjectName("dockTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("风险隐患调查审核工具")
        self.subtitle_label.setObjectName("dockSubtitle")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.subtitle_label)

        # 分隔线
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setObjectName("dockSeparator")
        layout.addWidget(self.separator)

        # ========== 导航图标按钮 ==========
        self.nav_buttons = []
        self._icon_labels = []

        for icon, text, index in NAV_ITEMS:
            btn = QPushButton(icon)
            btn.setObjectName("dockBtn")
            btn.setToolTip(text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=index: self._on_nav_clicked(i))

            self._setup_button_hover_anim(btn)

            layout.addWidget(btn, alignment=Qt.AlignHCenter)
            self.nav_buttons.append(btn)
            self._icon_labels.append((icon, text))

        # 默认选中第一个
        self.nav_buttons[0].setChecked(True)

        # ========== 弹性空间 ==========
        layout.addStretch()

        # ========== 底部：折叠按钮 + 主题设置 ==========
        self.collapse_btn = QPushButton("\u25c0")
        self.collapse_btn.setObjectName("dockCollapseBtn")
        self.collapse_btn.setToolTip("折叠/展开")
        self.collapse_btn.setCursor(Qt.PointingHandCursor)
        self.collapse_btn.clicked.connect(self.toggle_collapse)
        layout.addWidget(self.collapse_btn, alignment=Qt.AlignHCenter)

        theme_btn = QPushButton("\u2699")
        theme_btn.setObjectName("dockBtn")
        theme_btn.setToolTip("切换主题")
        theme_btn.setCursor(Qt.PointingHandCursor)
        theme_btn.clicked.connect(self._show_theme_dialog)
        layout.addWidget(theme_btn, alignment=Qt.AlignHCenter)

        self.setLayout(layout)

    def _setup_button_hover_anim(self, btn: QPushButton):
        """为按钮设置悬停缩放动画"""
        btn.enterEvent = lambda event: self._on_btn_hover(btn, True)
        btn.leaveEvent = lambda event: self._on_btn_hover(btn, False)

    def _on_btn_hover(self, btn: QPushButton, is_hover: bool):
        """按钮悬停时的缩放效果"""
        current_min = btn.minimumWidth()
        current_max = btn.maximumWidth()
        base_size = 52

        target = int(base_size * 1.08) if is_hover else base_size

        anim = QPropertyAnimation(btn, b"minimumWidth")
        anim.setDuration(150)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.setStartValue(current_min)
        anim.setEndValue(target)
        anim.start()

        max_anim = QPropertyAnimation(btn, b"maximumWidth")
        max_anim.setDuration(150)
        max_anim.setEasingCurve(QEasingCurve.OutCubic)
        max_anim.setStartValue(current_max)
        max_anim.setEndValue(target)
        max_anim.start()

    def _on_nav_clicked(self, index: int):
        """导航按钮点击"""
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        self.page_changed.emit(index)

    def _show_theme_dialog(self):
        """显示主题选择对话框"""
        from ui.dialogs.theme_dialog import ThemeDialog
        dialog = ThemeDialog(self)
        dialog.exec()

    def _on_theme_changed(self, mode: str):
        """主题更改"""
        self.theme_manager.set_mode(mode)
        self.theme_changed.emit(mode)

    def set_current_page(self, index: int):
        """设置当前页面"""
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

    @property
    def collapsed(self) -> bool:
        return self._collapsed

    def toggle_collapse(self):
        """切换折叠状态"""
        if self._animating:
            return

        self._collapsed = not self._collapsed
        self._update_collapse_state()
        self.collapse_toggled.emit(self._collapsed)

    def _update_collapse_state(self):
        """更新折叠状态"""
        if self._collapsed:
            self.title_label.hide()
            self.subtitle_label.hide()
            self.separator.hide()
            self.collapse_btn.setText("\u25b6")
        else:
            self.title_label.show()
            self.subtitle_label.show()
            self.separator.show()
            self.collapse_btn.setText("\u25c0")
