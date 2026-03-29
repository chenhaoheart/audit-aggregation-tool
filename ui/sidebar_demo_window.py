# -*- coding: utf-8 -*-
"""
侧边栏Demo V8 - Apple/macOS 风格
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt


APPLE_QSS = """
/* ==================== 主窗口 ==================== */
QWidget#mainWidget {
    background-color: #e8e8ed;
}

/* ==================== 侧边栏容器 ==================== */
#sidebar {
    background-color: rgba(246, 246, 250, 0.85);
    border: none;
    border-right: 1px solid rgba(0, 0, 0, 0.08);
}

/* ==================== 标题区域 ==================== */
QLabel#brand_label {
    color: #1d1d1f;
    font-size: 16px;
    font-weight: 600;
    font-family: "Microsoft YaHei", "微软雅黑", "Segoe UI", sans-serif;
    padding: 0 4px;
}

QLabel#subtitle_label {
    color: #86868b;
    font-size: 12px;
    font-family: "Microsoft YaHei", "微软雅黑", "Segoe UI", sans-serif;
    padding: 0 4px;
}

QLabel#section_title {
    color: #86868b;
    font-size: 13px;
    font-weight: 600;
    font-family: "Microsoft YaHei", "微软雅黑", "Segoe UI", sans-serif;
    padding: 20px 12px 4px 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QPushButton#nav_btn {
    background-color: transparent;
    color: #1d1d1f;
    border: none;
    border-radius: 6px;
    padding: 10px 12px;
    font-size: 14px;
    text-align: left;
    font-family: "Microsoft YaHei", "微软雅黑", "Segoe UI", sans-serif;
    margin: 1px 8px;
}

QPushButton#nav_btn:hover {
    background-color: rgba(0, 0, 0, 0.04);
    color: #1d1d1f;
}

QPushButton#nav_btn:checked {
    background-color: rgba(0, 122, 255, 0.15);
    color: #007aff;
    font-weight: 500;
}

/* ==================== 分割线 ==================== */
QFrame#divider {
    background-color: rgba(0, 0, 0, 0.08);
    max-height: 1px;
    margin: 8px 16px;
}

/* ==================== 底部区域 ==================== */
QFrame#footer {
    background-color: rgba(246, 246, 250, 0.5);
    border-top: 1px solid rgba(0, 0, 0, 0.06);
}

QLabel#footer_label {
    color: #86868b;
    font-size: 12px;
    font-family: "Microsoft YaHei", "微软雅黑", "Segoe UI", sans-serif;
}

/* ==================== 内容区域 ==================== */
QLabel#content_title {
    color: #1d1d1f;
    font-size: 32px;
    font-weight: 600;
    font-family: "Microsoft YaHei", "微软雅黑", "Segoe UI", sans-serif;
    padding-bottom: 6px;
}

QLabel#content_subtitle {
    color: #86868b;
    font-size: 16px;
    font-family: "Microsoft YaHei", "微软雅黑", "Segoe UI", sans-serif;
}

/* ==================== 卡片 ==================== */
QFrame#card {
    background-color: white;
    border-radius: 12px;
    border: 1px solid rgba(0, 0, 0, 0.06);
    padding: 20px;
}

QLabel#card_title {
    color: #1d1d1f;
    font-size: 17px;
    font-weight: 500;
    font-family: "Microsoft YaHei", "微软雅黑", "Segoe UI", sans-serif;
}

QLabel#card_desc {
    color: #86868b;
    font-size: 14px;
    font-family: "Microsoft YaHei", "微软雅黑", "Segoe UI", sans-serif;
}
"""


class SidebarDemoV8(QWidget):
    def __init__(self):
        super().__init__()
        self.active_index = 0
        self.nav_buttons = []
        self.init_ui()

    def init_ui(self):
        self.setObjectName("mainWidget")
        self.setWindowTitle("侧边栏Demo V8 - Apple风格")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(APPLE_QSS)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 侧边栏
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setSpacing(0)
        sidebar_layout.setContentsMargins(12, 16, 12, 0)

        # 标题
        header = QFrame()
        header.setStyleSheet("background: transparent; padding: 4px 8px;")
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)

        brand = QLabel("审核汇集")
        brand.setObjectName("brand_label")

        subtitle = QLabel("智能分析平台")
        subtitle.setObjectName("subtitle_label")

        header_layout.addWidget(brand)
        header_layout.addWidget(subtitle)
        header.setLayout(header_layout)
        sidebar_layout.addWidget(header)

        # 功能分组
        section1 = QLabel("功能")
        section1.setObjectName("section_title")
        sidebar_layout.addWidget(section1)

        nav_items = [
            ("🔍", "空间数据检查"),
            ("📊", "成果报表展示"),
            ("📈", "数据分析"),
            ("📝", "报告生成"),
        ]
        for i, (icon, text) in enumerate(nav_items):
            btn = QPushButton(f"  {icon}  {text}")
            btn.setObjectName("nav_btn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True)
            btn.setChecked(i == self.active_index)
            btn.clicked.connect(lambda _, idx=i: self.set_active(idx))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        # 分割线
        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFixedHeight(1)
        sidebar_layout.addWidget(divider)

        # 系统分组
        section2 = QLabel("系统")
        section2.setObjectName("section_title")
        sidebar_layout.addWidget(section2)

        system_items = [
            ("⚙", "设置"),
            ("❓", "帮助"),
            ("ℹ", "关于"),
        ]
        for icon, text in system_items:
            btn = QPushButton(f"  {icon}  {text}")
            btn.setObjectName("nav_btn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(False)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        # 底部
        footer = QFrame()
        footer.setObjectName("footer")
        footer_layout = QVBoxLayout()
        footer_layout.setContentsMargins(8, 12, 8, 12)

        footer_label = QLabel("v2.0  © 2024")
        footer_label.setObjectName("footer_label")
        footer_label.setAlignment(Qt.AlignCenter)

        footer_layout.addWidget(footer_label)
        footer.setLayout(footer_layout)
        sidebar_layout.addWidget(footer)

        sidebar.setLayout(sidebar_layout)
        main_layout.addWidget(sidebar)

        # 内容区域
        content = QFrame()
        content.setStyleSheet("background-color: #f5f5f7; border: none;")
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(48, 48, 48, 48)
        content_layout.setSpacing(24)

        # 标题区域
        title_area = QFrame()
        title_area.setStyleSheet("background: transparent;")
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        title = QLabel("Apple 风格界面设计")
        title.setObjectName("content_title")

        subtitle_t = QLabel("简洁、现代、人性化的设计语言")
        subtitle_t.setObjectName("content_subtitle")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle_t)
        title_area.setLayout(title_layout)
        content_layout.addWidget(title_area)

        # 卡片区域
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        cards = [
            ("🎨", "设计原则", "简洁即美，减少视觉噪音"),
            ("⚡", "交互体验", "流畅、直观、响应迅速"),
            ("🔵", "色彩系统", "蓝色为主，低饱和度配色"),
        ]

        for icon, card_title, card_desc in cards:
            card = QFrame()
            card.setObjectName("card")
            card_layout = QVBoxLayout()
            card_layout.setSpacing(8)

            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 32px; background: transparent;")

            ct = QLabel(card_title)
            ct.setObjectName("card_title")

            cd = QLabel(card_desc)
            cd.setObjectName("card_desc")

            card_layout.addWidget(icon_label)
            card_layout.addWidget(ct)
            card_layout.addWidget(cd)
            card.setLayout(card_layout)
            cards_layout.addWidget(card, 1)

        content_layout.addLayout(cards_layout)
        content_layout.addStretch()
        content.setLayout(content_layout)

        main_layout.addWidget(content, 1)
        self.setLayout(main_layout)

    def set_active(self, index):
        self.active_index = index
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = SidebarDemoV8()
    window.show()
    sys.exit(app.exec())
