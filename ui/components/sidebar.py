# -*- coding: utf-8 -*-
"""
侧边栏组件 - 重新设计版本
简化折叠逻辑，图标自动居中
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup

from core.theme_manager import get_theme_manager, ThemeMode
from ui.dialogs.theme_dialog import ThemeDialog


# 导航项配置
NAV_ITEMS = [
    ("\U0001f50d", "空间数据检查", 0),
    ("\U0001f4c8", "成果报表展示", 1),
    ("\U0001f4ca", "断面数据检查", 2),
    ("\U0001f6e0\ufe0f", "SHP属性格式化", 3)
]

# 侧边栏宽度
WIDTH_EXPANDED = 200
WIDTH_COLLAPSED = 60


class Sidebar(QFrame):
    """侧边栏组件"""

    page_changed = Signal(int)
    theme_changed = Signal(str)
    collapse_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._collapsed = False
        self._animating = False
        self.theme_manager = get_theme_manager()

        self.setObjectName("sidebar")
        self.setFixedWidth(WIDTH_EXPANDED)
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # ========== 标题区域 ==========
        self.title_label = QLabel("🌏 审核汇集")
        self.title_label.setObjectName("sidebarTitle")
        layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("风险隐患调查审核工具")
        self.subtitle_label.setObjectName("sidebarSubtitle")
        layout.addWidget(self.subtitle_label)

        # 分隔线
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setObjectName("sidebarSeparator")
        layout.addWidget(self.separator)

        # ========== 导航按钮 ==========
        self.nav_buttons = []
        self.nav_labels = []  # 保存文字标签用于折叠

        for icon, text, index in NAV_ITEMS:
            btn = QPushButton(f"{icon}  {text}")
            btn.setObjectName("sidebarBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=index: self._on_nav_clicked(i))
            layout.addWidget(btn)
            self.nav_buttons.append(btn)
            self.nav_labels.append((icon, text))

        self.nav_buttons[0].setChecked(True)

        # ========== 弹性空间 ==========
        layout.addStretch()

        # ========== 底部区域 ==========
        self.theme_btn = QPushButton("主题: 自动")
        self.theme_btn.setObjectName("themeBtn")
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self._update_theme_button()
        self.theme_btn.clicked.connect(self._show_theme_dialog)
        layout.addWidget(self.theme_btn)

        self.collapse_btn = QPushButton("◀")
        self.collapse_btn.setObjectName("collapseBtn")
        self.collapse_btn.setCursor(Qt.PointingHandCursor)
        self.collapse_btn.clicked.connect(self.toggle_collapse)
        layout.addWidget(self.collapse_btn)

        self.version_label = QLabel("v1.4.0")
        self.version_label.setObjectName("sidebarVersion")
        layout.addWidget(self.version_label)

        self.setLayout(layout)

    def _update_theme_button(self):
        """更新主题按钮文字"""
        mode = self.theme_manager.mode
        text_map = {
            ThemeMode.FLAME: "晨曦",
            ThemeMode.QWEN: "渐变",
            ThemeMode.GLASS: "毛玻璃",
            ThemeMode.FOREST: "森林",
            ThemeMode.AURORA: "极光",
            ThemeMode.DARK: "暗黑",
            ThemeMode.LIGHT: "亮色",
            ThemeMode.AUTO: "自动",
        }
        self.theme_btn.setText(f"主题: {text_map.get(mode, '晨曦')}")

    def _on_nav_clicked(self, index: int):
        """导航按钮点击"""
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        self.page_changed.emit(index)

    def _show_theme_dialog(self):
        """显示主题选择对话框"""
        print(f"[DEBUG-SIDEBAR] 打开主题对话框")
        dialog = ThemeDialog(self)
        result = dialog.exec()
        print(f"[DEBUG-SIDEBAR] 对话框关闭，返回值: {result}")
        print(f"[DEBUG-SIDEBAR] 不再调用 _on_theme_changed，因为点击即保存")

    def _on_theme_changed(self, mode: str):
        """主题更改"""
        self.theme_manager.set_mode(mode)
        self._update_theme_button()
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
        target_width = WIDTH_COLLAPSED if self._collapsed else WIDTH_EXPANDED

        # 动画
        self._animating = True
        self._animation_group = QParallelAnimationGroup(self)

        min_anim = QPropertyAnimation(self, b"minimumWidth")
        min_anim.setDuration(250)
        min_anim.setStartValue(self.width())
        min_anim.setEndValue(target_width)
        min_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._animation_group.addAnimation(min_anim)

        max_anim = QPropertyAnimation(self, b"maximumWidth")
        max_anim.setDuration(250)
        max_anim.setStartValue(self.width())
        max_anim.setEndValue(target_width)
        max_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._animation_group.addAnimation(max_anim)

        self._animation_group.finished.connect(lambda: self._on_animation_finished(target_width))
        self._animation_group.start()
        self.collapse_toggled.emit(self._collapsed)

    def _on_animation_finished(self, target_width: int):
        """动画完成"""
        self._animating = False
        self.setFixedWidth(target_width)
        self._update_collapse_state()

    def _update_collapse_state(self):
        """更新折叠状态"""
        if self._collapsed:
            # 折叠状态：只显示图标
            self.title_label.hide()
            self.subtitle_label.hide()
            self.separator.hide()
            self.version_label.hide()
            self.theme_btn.hide()

            for i, btn in enumerate(self.nav_buttons):
                icon, _ = self.nav_labels[i]
                btn.setText(icon)
                btn.setObjectName("sidebarBtnCollapsed")

            self.collapse_btn.setText("▶")
            self.collapse_btn.setObjectName("collapseBtnCollapsed")
        else:
            # 展开状态：显示完整文字
            self.title_label.show()
            self.subtitle_label.show()
            self.separator.show()
            self.version_label.show()
            self.theme_btn.show()

            for i, btn in enumerate(self.nav_buttons):
                icon, text = self.nav_labels[i]
                btn.setText(f"{icon}  {text}")
                btn.setObjectName("sidebarBtn")

            self.collapse_btn.setText("◀")
            self.collapse_btn.setObjectName("collapseBtn")

        # 强制刷新样式
        self.style().unpolish(self)
        self.style().polish(self)