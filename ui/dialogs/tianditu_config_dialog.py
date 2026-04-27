# -*- coding: utf-8 -*-
"""
天地图API Key配置对话框
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QFrame, QFormLayout, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPalette, QColor
from core.config_manager import TiandituConfig, DEFAULT_TIANDITU_KEY
from core.theme_manager import get_theme_manager


class TiandituConfigDialog(QDialog):
    """天地图API Key配置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("天地图API配置")
        self.setMinimumSize(500, 350)
        self.config = TiandituConfig()
        self.theme_manager = get_theme_manager()
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(self.theme_manager.get_stylesheet())

        theme = self.theme_manager.get_current_theme()
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(theme['content_bg']))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        header_card = QFrame()
        header_card.setObjectName("pageHeader")
        header_layout = QHBoxLayout(header_card)
        header_layout.setSpacing(16)
        header_layout.setContentsMargins(20, 16, 20, 16)

        accent_bar = QFrame()
        accent_bar.setObjectName("accentBar")
        accent_bar.setFixedWidth(4)
        header_layout.addWidget(accent_bar)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        page_title = QLabel("天地图 API Key 配置")
        page_title.setObjectName("sectionHeaderLg")
        title_layout.addWidget(page_title)

        page_subtitle = QLabel("配置天地图地图服务的API密钥，用于底图加载")
        page_subtitle.setObjectName("pageSubtitle")
        title_layout.addWidget(page_subtitle)

        header_layout.addLayout(title_layout, 1)
        layout.addWidget(header_card)

        config_card = QFrame()
        config_card.setObjectName("card")
        config_inner = QVBoxLayout(config_card)
        config_inner.setSpacing(12)

        card_title_layout = QHBoxLayout()
        card_title_layout.setSpacing(8)
        card_title = QLabel("API Key 设置")
        card_title.setObjectName("sectionHeaderMd")
        card_title_layout.addWidget(card_title)
        card_title_layout.addStretch()
        config_inner.addLayout(card_title_layout)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("请输入天地图API Key")
        self.key_edit.setText(self.config.api_key)
        self.key_edit.setMinimumWidth(300)
        form_layout.addRow("API Key:", self.key_edit)

        config_inner.addLayout(form_layout)

        hint_label = QLabel(
            "申请方式:\n"
            "1. 访问天地图官网: https://console.tianditu.gov.cn/\n"
            "2. 注册账号并创建应用\n"
            "3. 获取API Key并填入上方输入框\n\n"
            "提示: API Key有每日调用次数限制，如遇到地图加载失败，请检查Key是否有效"
        )
        hint_label.setObjectName("secondaryLabel")
        hint_label.setWordWrap(True)
        config_inner.addWidget(hint_label)

        layout.addWidget(config_card)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.reset_btn = QPushButton("恢复默认")
        self.reset_btn.setObjectName("clearBtn")
        self.reset_btn.clicked.connect(self._reset_to_default)
        btn_layout.addWidget(self.reset_btn)

        btn_layout.addStretch()

        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self._save_config)
        btn_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("clearBtn")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _reset_to_default(self):
        self.key_edit.setText(DEFAULT_TIANDITU_KEY)

    def _save_config(self):
        key = self.key_edit.text().strip()
        if not key:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "提示", "API Key不能为空")
            return

        if self.config.save_api_key(key):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "成功", "天地图API Key已保存，重新打开地图窗口后生效。")
            self.accept()
        else:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "失败", "保存配置失败")

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, '_animated'):
            self._animated = True
            self._animate_entrance()

    def _animate_entrance(self):
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