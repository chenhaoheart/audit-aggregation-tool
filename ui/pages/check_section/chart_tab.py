# -*- coding: utf-8 -*-
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QUrl

from core.theme_manager import get_theme_manager

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    HAS_WEB_ENGINE = True
except ImportError:
    HAS_WEB_ENGINE = False


class ChartTab(QWidget):
    log_message = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._service = None
        self._current_section_key = None
        self._theme_manager = get_theme_manager()
        self._init_ui()
        self._apply_theme_styles()
        self._theme_manager.theme_changed.connect(self._on_theme_changed)

    def set_service(self, service):
        self._service = service

    def _init_ui(self):
        chart_layout = QVBoxLayout(self)
        chart_layout.setSpacing(0)
        chart_layout.setContentsMargins(0, 8, 0, 8)

        chart_toolbar = QHBoxLayout()
        chart_toolbar.setContentsMargins(8, 0, 8, 0)
        self.export_chart_btn = QPushButton("导出断面成图")
        self.export_chart_btn.setObjectName("toolbarBtn")
        self.export_chart_btn.setFixedHeight(24)
        self.export_chart_btn.setCursor(Qt.PointingHandCursor)
        self.export_chart_btn.clicked.connect(self._open_chart_external)
        chart_toolbar.addWidget(self.export_chart_btn)
        chart_toolbar.addStretch()
        chart_layout.addLayout(chart_toolbar)

        if HAS_WEB_ENGINE:
            self.chart_web = QWebEngineView()
            self.chart_web.setMinimumHeight(500)
            self.chart_web.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            chart_layout.addWidget(self.chart_web, 1)
        else:
            self.chart_placeholder = QLabel("成图功能需要 QWebEngineView 支持\n请安装 PySide6-WebEngine")
            self.chart_placeholder.setAlignment(Qt.AlignCenter)
            chart_layout.addWidget(self.chart_placeholder)

    def _apply_theme_styles(self):
        theme = self._theme_manager.get_current_theme()
        text_secondary = theme.get('text_secondary', '#6b7d9e')
        border_subtle = theme.get('border_subtle', theme.get('card_border', '#e0e4e8'))
        accent = theme.get('accent_color', '#6366f1')
        surface_1 = theme.get('surface_1', theme.get('card_bg', '#f8f9fa'))
        surface_2 = theme.get('surface_2', theme.get('card_bg', '#f0f2f5'))
        text_primary = theme.get('text_primary', '#2c3e50')

        self.export_chart_btn.setStyleSheet(f"""
            QPushButton#toolbarBtn {{
                background: transparent;
                color: {text_secondary};
                border: 1px solid {border_subtle};
                border-radius: 6px;
                padding: 0 8px;
                font-size: 12px;
            }}
            QPushButton#toolbarBtn:hover {{
                background: {surface_2};
                color: {text_primary};
                border-color: {accent};
            }}
        """)

        if not HAS_WEB_ENGINE and hasattr(self, 'chart_placeholder'):
            self.chart_placeholder.setStyleSheet(f"color: {text_secondary}; font-size: 14px;")

    def _on_theme_changed(self, mode: str):
        self._apply_theme_styles()

    def render_chart(self, section_key: str, sec: dict):
        self._current_section_key = section_key
        if not HAS_WEB_ENGINE:
            return
        if not self._service:
            return
        tmp_path = self._service.render_chart_to_temp(section_key, sec)
        url = QUrl.fromLocalFile(tmp_path)
        url.setQuery(f"t={int(time.time() * 1000)}")
        self.chart_web.load(url)

    def _open_chart_external(self):
        if not self._current_section_key:
            return
        if not self._service:
            return
        sec = self._service.get_section_detail(self._current_section_key)
        if not sec:
            return
        output_path = self._service.open_chart_external(self._current_section_key, sec)
        self.log_message.emit(f"已打开断面成图: {output_path}")
