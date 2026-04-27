# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame,
    QListWidget, QListWidgetItem, QLineEdit, QMessageBox, QGraphicsOpacityEffect
)
from PySide6.QtCore import Signal, Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPalette, QColor

from core.theme_manager import get_theme_manager
from services.section_chart_service import get_feature_keywords, save_feature_keywords


class FeatureKeywordsDialog(QDialog):
    keywords_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._original_keywords = []
        self.setWindowTitle("特征点关键词配置")
        self.setMinimumSize(400, 350)
        self.setWindowFlags(self.windowFlags() | Qt.Dialog)
        self._init_ui()
        self._load_keywords()

    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel("特征点关键词配置")
        title_label.setObjectName("sectionHeaderMd")
        main_layout.addWidget(title_label)

        desc_label = QLabel("包含以下关键词的测量点将被标记为特征点，在断面成图中显示")
        desc_label.setObjectName("secondaryLabel")
        desc_label.setWordWrap(True)
        main_layout.addWidget(desc_label)

        self.keywords_list = QListWidget()
        self.keywords_list.setObjectName("keywordsList")
        self.keywords_list.setAlternatingRowColors(True)
        self.keywords_list.setMinimumHeight(150)
        main_layout.addWidget(self.keywords_list)

        add_layout = QHBoxLayout()
        add_layout.setSpacing(10)
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("输入新关键词...")
        self.keyword_input.setMaxLength(20)
        add_layout.addWidget(self.keyword_input, 1)
        self.add_btn = QPushButton("添加")
        self.add_btn.setFixedWidth(80)
        self.add_btn.clicked.connect(self._on_add_keyword)
        add_layout.addWidget(self.add_btn)
        self.remove_btn = QPushButton("删除")
        self.remove_btn.setFixedWidth(80)
        self.remove_btn.clicked.connect(self._on_remove_keyword)
        add_layout.addWidget(self.remove_btn)
        main_layout.addLayout(add_layout)

        separator = QFrame()
        separator.setObjectName("dialogSeparator")
        separator.setFrameShape(QFrame.HLine)
        main_layout.addWidget(separator)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.confirm_btn = QPushButton("确定")
        self.confirm_btn.setObjectName("confirmBtn")
        self.confirm_btn.setMinimumWidth(100)
        self.confirm_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self.confirm_btn)
        btn_layout.addSpacing(15)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)
        self._apply_theme_style()

    def _load_keywords(self):
        keywords = get_feature_keywords()
        self._original_keywords = keywords.copy()
        self.keywords_list.clear()
        for kw in keywords:
            item = QListWidgetItem(kw)
            self.keywords_list.addItem(item)

    def _on_add_keyword(self):
        new_kw = self.keyword_input.text().strip()
        if not new_kw:
            QMessageBox.warning(self, "提示", "请输入关键词")
            return
        for i in range(self.keywords_list.count()):
            if self.keywords_list.item(i).text() == new_kw:
                QMessageBox.warning(self, "提示", "关键词已存在")
                return
        self.keywords_list.addItem(QListWidgetItem(new_kw))
        self.keyword_input.clear()

    def _on_remove_keyword(self):
        current_item = self.keywords_list.currentItem()
        if current_item:
            self.keywords_list.takeItem(self.keywords_list.row(current_item))
        else:
            QMessageBox.warning(self, "提示", "请先选择要删除的关键词")

    def _on_confirm(self):
        keywords = []
        for i in range(self.keywords_list.count()):
            keywords.append(self.keywords_list.item(i).text())
        if not keywords:
            QMessageBox.warning(self, "提示", "至少保留一个关键词")
            return
        save_feature_keywords(keywords)
        self.keywords_changed.emit(keywords)
        self.accept()

    def _on_cancel(self):
        self.reject()

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

    def _apply_theme_style(self):
        theme_manager = get_theme_manager()
        theme = theme_manager.get_current_theme()
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(theme['content_bg']))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        self.setStyleSheet(theme_manager.get_stylesheet())