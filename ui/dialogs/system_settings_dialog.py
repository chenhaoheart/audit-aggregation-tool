# -*- coding: utf-8 -*-
"""
系统参数配置对话框
左侧二级菜单 + 右侧内容区，整合主题设置、默认参数、SHP图层格式化、天地图配置
"""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QFrame, QStackedWidget, QWidget, QFormLayout,
    QSlider, QMessageBox, QFileDialog, QListWidget, QListWidgetItem,
    QSplitter, QGridLayout, QSizePolicy, QGraphicsOpacityEffect,
    QScrollArea, QToolButton, QTabWidget
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer, QRectF
from PySide6.QtGui import QPalette, QColor, QPainter, QPainterPath, QBrush, QPen, QFont, QLinearGradient

from core.theme_manager import get_theme_manager, ThemeMode, ThemeGroup, THEME_GROUP_MAP, THEME_DISPLAY_NAMES, get_theme_group
from core.config_manager import (
    TiandituConfig, ArcGISConfig, ShpMatchConfig, get_shp_match_config,
    DEFAULT_TIANDITU_KEY, DEFAULT_SHP_MATCH,
    ValidationMappingConfig, get_validation_mapping_config, DEFAULT_VALIDATION_FIELD_MAPPING
)
from ui.components.theme_preview_card import ThemePreviewCard


SETTINGS_MENU = [
    {"id": "theme", "icon": "🎨", "text": "主题设置"},
    {"id": "default_params", "icon": "⚙️", "text": "默认参数设置"},
    {"id": "shp_format", "icon": "🗺️", "text": "SHP图层格式化参数"},
    {"id": "validation_mapping", "icon": "🔗", "text": "校验字段映射"},
    {"id": "tianditu", "icon": "🌐", "text": "天地图配置"},
]


class _SettingsNavItem(QPushButton):
    def __init__(self, icon: str, text: str, item_id: str, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self._icon = icon
        self._text = text
        self.setObjectName("settingsNavItem")
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setText(f"  {self._icon}   {self._text}")
        self.setToolTip(self._text)


class ThemeSettingsPage(QWidget):
    theme_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_theme = None
        self._original_theme = None
        self._current_group = ThemeGroup.LIGHT
        self._theme_cards = {}
        self._init_ui()
        self._load_current()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)

        header = self._make_header("主题设置", "选择界面主题风格，支持浅色系与暗色系切换")
        layout.addWidget(header)

        group_frame = QWidget()
        group_layout = QHBoxLayout(group_frame)
        group_layout.setSpacing(16)
        group_layout.setContentsMargins(0, 0, 0, 0)

        self.light_card = _GroupSelectorCard(ThemeGroup.LIGHT)
        self.dark_card = _GroupSelectorCard(ThemeGroup.DARK)
        self.light_card.clicked_group.connect(self._on_group_selected)
        self.dark_card.clicked_group.connect(self._on_group_selected)

        group_layout.addStretch()
        group_layout.addWidget(self.light_card)
        group_layout.addWidget(self.dark_card)
        group_layout.addStretch()
        layout.addWidget(group_frame)

        self.subthemes_container = QWidget()
        self.subthemes_layout = QHBoxLayout(self.subthemes_container)
        self.subthemes_layout.setSpacing(14)
        self.subthemes_layout.setContentsMargins(0, 4, 0, 0)
        self.subthemes_layout.addStretch()
        layout.addWidget(self.subthemes_container)

        self.opacity_frame = QFrame()
        opacity_layout = QHBoxLayout(self.opacity_frame)
        opacity_layout.setContentsMargins(0, 0, 0, 0)
        opacity_layout.setSpacing(12)

        opacity_label = QLabel("\u900f\u660e\u5ea6")
        opacity_label.setObjectName("settingsLabel")
        opacity_layout.addWidget(opacity_label)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(10)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setSingleStep(5)
        self.opacity_slider.setPageStep(10)
        tm = get_theme_manager()
        slider_val = int(tm.glass_opacity * 100)
        self.opacity_slider.setValue(min(100, max(10, slider_val)))
        self.opacity_slider.setFixedWidth(180)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        opacity_layout.addWidget(self.opacity_slider)

        display_pct = min(100, max(10, slider_val))
        self.opacity_value_label = QLabel(f"{display_pct}%")
        self.opacity_value_label.setObjectName("settingsOpacityValue")
        opacity_layout.addWidget(self.opacity_value_label)
        opacity_layout.addStretch()
        layout.addWidget(self.opacity_frame)
        self.opacity_frame.hide()

        layout.addStretch()

    def _make_header(self, title: str, subtitle: str) -> QFrame:
        header_card = QFrame()
        header_card.setObjectName("pageHeader")
        header_layout = QHBoxLayout(header_card)
        header_layout.setSpacing(16)
        header_layout.setContentsMargins(20, 14, 20, 14)

        accent_bar = QFrame()
        accent_bar.setObjectName("accentBar")
        accent_bar.setFixedWidth(4)
        header_layout.addWidget(accent_bar)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        t = QLabel(title)
        t.setObjectName("sectionHeaderLg")
        title_layout.addWidget(t)
        s = QLabel(subtitle)
        s.setObjectName("pageSubtitle")
        title_layout.addWidget(s)
        header_layout.addLayout(title_layout, 1)
        return header_card

    def _load_current(self):
        theme_manager = get_theme_manager()
        current_mode = theme_manager.mode
        self._original_theme = current_mode
        self._selected_theme = current_mode

        group = get_theme_group(current_mode) or ThemeGroup.LIGHT
        self._current_group = group
        self.light_card.set_active(group == ThemeGroup.LIGHT)
        self.dark_card.set_active(group == ThemeGroup.DARK)
        self._populate_subthemes(group)

        if current_mode in self._theme_cards:
            self._theme_cards[current_mode].set_selected(True)
        self._update_opacity_visibility()

    def _on_group_selected(self, group: str):
        if self._current_group == group:
            return
        self._current_group = group
        self.light_card.set_active(group == ThemeGroup.LIGHT)
        self.dark_card.set_active(group == ThemeGroup.DARK)

        group_themes = THEME_GROUP_MAP[group]["modes"]
        self._selected_theme = group_themes[0] if group_themes else None
        self._animate_subthemes_switch(group)

    def _populate_subthemes(self, group: str):
        for card in list(self._theme_cards.values()):
            card.setParent(None)
            card.deleteLater()
        self._theme_cards.clear()

        while self.subthemes_layout.count():
            item = self.subthemes_layout.takeAt(0)
            if item.widget():
                item.widget().hide()

        self.subthemes_layout.addStretch()
        group_themes = THEME_GROUP_MAP[group]["modes"]
        for mode in group_themes:
            card = ThemePreviewCard(mode)
            card.clicked.connect(self._on_theme_clicked)
            self._theme_cards[mode] = card
            self.subthemes_layout.addWidget(card)
        self.subthemes_layout.addStretch()

    def _animate_subthemes_switch(self, group: str):
        for mode, card in list(self._theme_cards.items()):
            effect = QGraphicsOpacityEffect(card)
            card.setGraphicsEffect(effect)
            effect.setOpacity(1.0)
            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(100)
            anim.setStartValue(1.0)
            anim.setEndValue(0.0)
            anim.setEasingCurve(QEasingCurve.InCubic)
            anim.start(QPropertyAnimation.DeleteWhenStopped)
            card._fade_anim = anim

        def on_fade_done():
            self._populate_subthemes(group)
            if self._selected_theme and self._selected_theme in self._theme_cards:
                self._theme_cards[self._selected_theme].set_selected(True)
            self._update_opacity_visibility()
            for i, (mode, card) in enumerate(self._theme_cards.items()):
                effect = QGraphicsOpacityEffect(card)
                card.setGraphicsEffect(effect)
                effect.setOpacity(0.0)
                anim = QPropertyAnimation(effect, b"opacity")
                anim.setDuration(180)
                anim.setStartValue(0.0)
                anim.setEndValue(1.0)
                anim.setEasingCurve(QEasingCurve.OutCubic)

                def cleanup(eff=effect, c=card):
                    if c.graphicsEffect() is eff:
                        c.setGraphicsEffect(None)

                anim.finished.connect(cleanup)
                QTimer.singleShot(i * 40, anim.start)
                card._fade_in_anim = anim

        QTimer.singleShot(120, on_fade_done)

    def _on_theme_clicked(self, theme_mode: str):
        for mode, card in self._theme_cards.items():
            card.set_selected(False)
        if theme_mode in self._theme_cards:
            self._theme_cards[theme_mode].set_selected(True)
            self._selected_theme = theme_mode
        self._update_opacity_visibility()
        self._apply_theme_immediately()

    def _update_opacity_visibility(self):
        is_glass = self._selected_theme == ThemeMode.GLASS
        self.opacity_frame.setVisible(is_glass)

    def _on_opacity_changed(self, value: int):
        self.opacity_value_label.setText(f"{value}%")
        theme_manager = get_theme_manager()
        theme_manager.set_glass_opacity(value / 100.0)

    def _apply_theme_immediately(self):
        if self._selected_theme:
            theme_manager = get_theme_manager()
            theme_manager.set_mode(self._selected_theme)
            self.theme_changed.emit(self._selected_theme)

    def restore_original(self):
        if self._original_theme:
            theme_manager = get_theme_manager()
            theme_manager.set_mode(self._original_theme)


class _GroupSelectorCard(QPushButton):
    clicked_group = Signal(str)

    def __init__(self, group: str, parent=None):
        super().__init__(parent)
        self._group = group
        self._active = False
        self._hover_state = False
        config = THEME_GROUP_MAP[group]
        self._icon = config["icon"]
        self._name = config["name"]
        self._subtitle = config["subtitle"]
        self.setObjectName("groupSelectorCard")
        self.setFixedSize(210, 100)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self.clicked.connect(lambda: self.clicked_group.emit(group))

    def set_active(self, active: bool):
        self._active = active
        self.update()

    def enterEvent(self, event):
        self._hover_state = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover_state = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(0, 0, self.width(), self.height())
        path = QPainterPath()
        path.addRoundedRect(rect.adjusted(1, 1, -1, -1), 16, 16)

        if self._group == ThemeGroup.LIGHT:
            if self._active:
                grad = QLinearGradient(0, 0, 0, self.height())
                grad.setColorAt(0, QColor("#fff3e0"))
                grad.setColorAt(0.4, QColor("#ffe0b2"))
                grad.setColorAt(0.7, QColor("#ffccbc"))
                grad.setColorAt(1, QColor("#ffab91"))
            else:
                grad = QLinearGradient(0, 0, 0, self.height())
                grad.setColorAt(0, QColor("#fdfaf6"))
                grad.setColorAt(0.5, QColor("#faf3eb"))
                grad.setColorAt(1, QColor("#f5e6d8"))
        else:
            if self._active:
                grad = QLinearGradient(0, 0, 0, self.height())
                grad.setColorAt(0, QColor("#1a1a2e"))
                grad.setColorAt(0.4, QColor("#141b3d"))
                grad.setColorAt(0.7, QColor("#0a0e27"))
                grad.setColorAt(1, QColor("#0d1117"))
            else:
                grad = QLinearGradient(0, 0, 0, self.height())
                grad.setColorAt(0, QColor("#1e1f35"))
                grad.setColorAt(0.5, QColor("#1a1c30"))
                grad.setColorAt(1, QColor("#131525"))

        painter.fillPath(path, QBrush(grad))

        if self._active:
            border_color = QColor("#FF7F50") if self._group == ThemeGroup.LIGHT else QColor("#00d4aa")
            painter.setPen(QPen(border_color, 2.5))
            painter.drawPath(path)
        elif self._hover_state:
            painter.setPen(QPen(QColor(180, 180, 180, 100), 1))
            painter.drawPath(path)

        text_color = QColor("#5D4037") if self._group == ThemeGroup.LIGHT else QColor("#e8eaf6")
        subtitle_color = QColor("#8D6E63") if self._group == ThemeGroup.LIGHT else QColor("#7986cb")

        fn_icon = QFont()
        fn_icon.setPointSize(20)
        painter.setFont(fn_icon)
        painter.setPen(QPen(text_color))
        painter.drawText(QRectF(0, 8, self.width(), 32), Qt.AlignCenter, self._icon)

        fn_name = QFont()
        fn_name.setPointSize(12)
        fn_name.setBold(True)
        painter.setFont(fn_name)
        painter.setPen(QPen(text_color))
        painter.drawText(QRectF(0, 38, self.width(), 24), Qt.AlignCenter, self._name)

        fn_sub = QFont()
        fn_sub.setPointSize(9)
        painter.setFont(fn_sub)
        painter.setPen(QPen(subtitle_color))
        painter.drawText(QRectF(0, 62, self.width(), 22), Qt.AlignCenter, self._subtitle)

        painter.end()


class DefaultParamsPage(QWidget):
    config_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.arcgis_config = ArcGISConfig()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)

        header = self._make_header("默认参数设置", "配置ArcGIS Python环境路径")
        layout.addWidget(header)

        config_card = QFrame()
        config_card.setObjectName("card")
        config_inner = QVBoxLayout(config_card)
        config_inner.setSpacing(12)

        card_title = QLabel("ArcGIS Python 环境路径")
        card_title.setObjectName("sectionHeaderMd")
        config_inner.addWidget(card_title)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("例如: C:\\Program Files\\ArcGIS\\Pro\\bin\\Python\\envs\\arcgispro-py3")
        self.path_edit.setText(self.arcgis_config.python_path or "")
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.setFixedWidth(80)
        self.browse_btn.clicked.connect(self._browse_path)
        path_layout.addWidget(self.path_edit, 1)
        path_layout.addWidget(self.browse_btn)
        form_layout.addRow("Python目录:", path_layout)

        hint_label = QLabel("常见路径:\nC:\\Program Files\\ArcGIS\\Pro\\bin\\Python\\envs\\arcgispro-py3")
        hint_label.setObjectName("secondaryLabel")
        hint_label.setWordWrap(True)
        form_layout.addRow("", hint_label)

        config_inner.addLayout(form_layout)
        layout.addWidget(config_card)

        self.status_label = QLabel("")
        self.status_label.setObjectName("secondaryLabel")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self._save_config)
        btn_layout.addWidget(self.save_btn)

        self.clear_btn = QPushButton("清除配置")
        self.clear_btn.setObjectName("clearBtn")
        self.clear_btn.clicked.connect(self._clear_config)
        btn_layout.addWidget(self.clear_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()

    def _make_header(self, title: str, subtitle: str) -> QFrame:
        header_card = QFrame()
        header_card.setObjectName("pageHeader")
        header_layout = QHBoxLayout(header_card)
        header_layout.setSpacing(16)
        header_layout.setContentsMargins(20, 14, 20, 14)

        accent_bar = QFrame()
        accent_bar.setObjectName("accentBar")
        accent_bar.setFixedWidth(4)
        header_layout.addWidget(accent_bar)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        t = QLabel(title)
        t.setObjectName("sectionHeaderLg")
        title_layout.addWidget(t)
        s = QLabel(subtitle)
        s.setObjectName("pageSubtitle")
        title_layout.addWidget(s)
        header_layout.addLayout(title_layout, 1)
        return header_card

    def _browse_path(self):
        folder = QFileDialog.getExistingDirectory(self, "选择ArcGIS Python目录", self.path_edit.text() or "")
        if folder:
            self.path_edit.setText(os.path.normpath(folder))

    def _save_config(self):
        path = self.path_edit.text().strip()
        if path:
            path = os.path.normpath(path)
            self.path_edit.setText(path)
        if path and not os.path.exists(path):
            reply = QMessageBox.question(self, "确认", "指定的目录不存在，是否仍要保存？", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        if self.arcgis_config.save_python_path(path, verified=False):
            self.status_label.setText("\u2713 \u914d\u7f6e\u5df2\u4fdd\u5b58")
            self.status_label.setObjectName("settingsStatusSuccess")
            self.style().unpolish(self.status_label)
            self.style().polish(self.status_label)
            self.config_changed.emit()
        else:
            QMessageBox.warning(self, "\u5931\u8d25", "\u4fdd\u5b58\u914d\u7f6e\u5931\u8d25")

    def _clear_config(self):
        self.arcgis_config.clear_python_path()
        self.path_edit.setText("")
        self.status_label.setText("\u2713 \u914d\u7f6e\u5df2\u6e05\u9664")
        self.status_label.setObjectName("settingsStatusSuccess")
        self.style().unpolish(self.status_label)
        self.style().polish(self.status_label)
        self.config_changed.emit()


class ShpFormatParamsPage(QWidget):
    config_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.shp_config = get_shp_match_config()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)

        header = self._make_header("SHP图层格式化参数", "配置SHP文件匹配关键词和图层分类规则，修改后立即生效")
        layout.addWidget(header)

        water_card = QFrame()
        water_card.setObjectName("card")
        water_inner = QVBoxLayout(water_card)
        water_inner.setSpacing(10)

        water_title = QLabel("水系SHP文件匹配关键词")
        water_title.setObjectName("sectionHeaderMd")
        water_inner.addWidget(water_title)

        water_hint = QLabel("匹配文件名中包含以下关键词的SHP文件（英文关键词不区分大小写），用逗号分隔")
        water_hint.setObjectName("secondaryLabel")
        water_hint.setWordWrap(True)
        water_inner.addWidget(water_hint)

        self.water_keywords_edit = QLineEdit()
        self.water_keywords_edit.setText(", ".join(self.shp_config.water_system_keywords))
        self.water_keywords_edit.setPlaceholderText("例如: 水系, river, rivl")
        water_inner.addWidget(self.water_keywords_edit)

        layout.addWidget(water_card)

        spatial_card = QFrame()
        spatial_card.setObjectName("card")
        spatial_inner = QVBoxLayout(spatial_card)
        spatial_inner.setSpacing(10)

        spatial_title = QLabel("空间数据定位文件名")
        spatial_title.setObjectName("sectionHeaderMd")
        spatial_inner.addWidget(spatial_title)

        spatial_hint = QLabel("用于定位空间数据文件夹的精确文件名，用逗号分隔")
        spatial_hint.setObjectName("secondaryLabel")
        spatial_hint.setWordWrap(True)
        spatial_inner.addWidget(spatial_hint)

        self.spatial_filenames_edit = QLineEdit()
        self.spatial_filenames_edit.setText(", ".join(self.shp_config.spatial_data_filenames))
        self.spatial_filenames_edit.setPlaceholderText("例如: 防治对象分布P.shp, 断面平面位置L.shp")
        spatial_inner.addWidget(self.spatial_filenames_edit)

        layout.addWidget(spatial_card)

        layer_card = QFrame()
        layer_card.setObjectName("card")
        layer_inner = QVBoxLayout(layer_card)
        layer_inner.setSpacing(10)

        layer_title = QLabel("图层分类关键词")
        layer_title.setObjectName("sectionHeaderMd")
        layer_inner.addWidget(layer_title)

        layer_hint = QLabel("用于按源文件名过滤和分类记录的关键词映射")
        layer_hint.setObjectName("secondaryLabel")
        layer_hint.setWordWrap(True)
        layer_inner.addWidget(layer_hint)

        self.layer_edits = {}
        layer_grid = QFormLayout()
        layer_grid.setSpacing(10)

        label_map = {
            "duanmian": "断面平面位置",
            "fangzhi": "防治对象分布",
            "yinhuan": "隐患要素分布",
        }
        for key, label_text in label_map.items():
            edit = QLineEdit()
            edit.setText(self.shp_config.get_layer_keyword(key))
            edit.setPlaceholderText(f"例如: {label_text}")
            layer_grid.addRow(f"{label_text}:", edit)
            self.layer_edits[key] = edit

        layer_inner.addLayout(layer_grid)
        layout.addWidget(layer_card)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.save_btn = QPushButton("保存并生效")
        self.save_btn.clicked.connect(self._save_config)
        btn_layout.addWidget(self.save_btn)

        self.reset_btn = QPushButton("恢复默认")
        self.reset_btn.setObjectName("clearBtn")
        self.reset_btn.clicked.connect(self._reset_to_default)
        btn_layout.addWidget(self.reset_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.status_label = QLabel("")
        self.status_label.setObjectName("secondaryLabel")
        layout.addWidget(self.status_label)

        layout.addStretch()

    def _make_header(self, title: str, subtitle: str) -> QFrame:
        header_card = QFrame()
        header_card.setObjectName("pageHeader")
        header_layout = QHBoxLayout(header_card)
        header_layout.setSpacing(16)
        header_layout.setContentsMargins(20, 14, 20, 14)

        accent_bar = QFrame()
        accent_bar.setObjectName("accentBar")
        accent_bar.setFixedWidth(4)
        header_layout.addWidget(accent_bar)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        t = QLabel(title)
        t.setObjectName("sectionHeaderLg")
        title_layout.addWidget(t)
        s = QLabel(subtitle)
        s.setObjectName("pageSubtitle")
        title_layout.addWidget(s)
        header_layout.addLayout(title_layout, 1)
        return header_card

    def _save_config(self):
        water_keywords = [kw.strip() for kw in self.water_keywords_edit.text().split(",") if kw.strip()]
        spatial_filenames = [fn.strip() for fn in self.spatial_filenames_edit.text().split(",") if fn.strip()]
        layer_keywords = {}
        for key, edit in self.layer_edits.items():
            val = edit.text().strip()
            if val:
                layer_keywords[key] = val

        new_config = {
            "water_system_keywords": water_keywords,
            "spatial_data_filenames": spatial_filenames,
            "layer_keywords": layer_keywords,
        }

        if self.shp_config.save_config(new_config):
            self.status_label.setText("\u2713 \u914d\u7f6e\u5df2\u4fdd\u5b58\u5e76\u7acb\u5373\u751f\u6548")
            self.status_label.setObjectName("settingsStatusSuccess")
            self.style().unpolish(self.status_label)
            self.style().polish(self.status_label)
            self.config_changed.emit()
        else:
            QMessageBox.warning(self, "\u5931\u8d25", "\u4fdd\u5b58\u914d\u7f6e\u5931\u8d25")

    def _reset_to_default(self):
        self.water_keywords_edit.setText(", ".join(DEFAULT_SHP_MATCH["water_system_keywords"]))
        self.spatial_filenames_edit.setText(", ".join(DEFAULT_SHP_MATCH["spatial_data_filenames"]))
        for key, edit in self.layer_edits.items():
            edit.setText(DEFAULT_SHP_MATCH["layer_keywords"].get(key, ""))
        self.status_label.setText('\u5df2\u6062\u5909\u9ed8\u8ba4\u503c\uff0c\u70b9\u51fb"\u4fdd\u5b58\u5e76\u751f\u6548"\u4f7f\u5176\u751f\u6548')
        self.status_label.setObjectName("settingsStatusWarning")
        self.style().unpolish(self.status_label)
        self.style().polish(self.status_label)


class ValidationMappingSettingsPage(QWidget):
    config_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mapping_config = get_validation_mapping_config()
        self._mapping_edits = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        header = self._make_header("校验字段映射", "配置空间数据与附表交叉检查时的字段自动映射规则，修改后立即生效")
        layout.addWidget(header)

        mapping = self.mapping_config.mapping

        tab_configs = [
            ("fubiao1_vs_fangzhi", "防治对象 ↔ 附表1", "防治对象分布P.shp与附表1的字段对应关系"),
            ("fubiao2_vs_yinhuan", "隐患要素 ↔ 附表2", "隐患要素分布L.shp与附表2的字段对应关系"),
            ("fubiao3_vs_yinhuan", "隐患要素 ↔ 附表3", "隐患要素分布L.shp与附表3的字段对应关系"),
        ]

        self._detail_forms = {}

        tab_widget = QTabWidget()
        tab_widget.setObjectName("mappingTabWidget")

        for mapping_key, tab_title, tab_desc in tab_configs:
            tab_page = QWidget()
            tab_layout = QVBoxLayout(tab_page)
            tab_layout.setSpacing(10)
            tab_layout.setContentsMargins(16, 14, 16, 14)

            desc_label = QLabel(tab_desc)
            desc_label.setObjectName("secondaryLabel")
            desc_label.setWordWrap(True)
            tab_layout.addWidget(desc_label)

            mapping_data = mapping.get(mapping_key, {})

            match_sep = QFrame()
            match_sep.setFrameShape(QFrame.HLine)
            match_sep.setFixedHeight(1)
            match_sep.setObjectName("settingsSeparator")
            tab_layout.addWidget(match_sep)

            match_header_row = QHBoxLayout()
            match_title = QLabel("\U0001f511 \u5339\u914d\u5b57\u6bb5\uff08\u7528\u4e8e\u8bb0\u5f55\u5339\u914d\uff09")
            match_title.setObjectName("settingsFieldTitle")
            match_header_row.addWidget(match_title)
            match_header_row.addStretch()
            tab_layout.addLayout(match_header_row)

            match_fields = mapping_data.get('match_fields', {})
            match_form = QFormLayout()
            match_form.setSpacing(6)
            for shp_field, fubiao_field in match_fields.items():
                row_widget = self._create_mapping_row(mapping_key, 'match_fields', shp_field, fubiao_field, removable=False)
                match_form.addRow(f"shp[{shp_field}] →", row_widget)
            tab_layout.addLayout(match_form)

            detail_sep = QFrame()
            detail_sep.setFrameShape(QFrame.HLine)
            detail_sep.setFixedHeight(1)
            detail_sep.setObjectName("settingsSeparator")
            tab_layout.addWidget(detail_sep)

            detail_header_row = QHBoxLayout()
            detail_title = QLabel("\U0001f4cb \u8be6\u60c5\u5b57\u6bb5\uff08\u7528\u4e8e\u5c5e\u6027\u5bf9\u6bd4\u68c0\u67e5\uff09")
            detail_title.setObjectName("settingsFieldTitle")
            detail_header_row.addWidget(detail_title)
            detail_header_row.addStretch()
            add_detail_btn = QToolButton()
            add_detail_btn.setText("+ \u6dfb\u52a0")
            add_detail_btn.setObjectName("settingsAddBtn")
            add_detail_btn.setCursor(Qt.PointingHandCursor)
            add_detail_btn.clicked.connect(lambda checked, mk=mapping_key: self._add_detail_row(mk))
            detail_header_row.addWidget(add_detail_btn)
            tab_layout.addLayout(detail_header_row)

            detail_fields = mapping_data.get('detail_fields', {})
            detail_form = QFormLayout()
            detail_form.setSpacing(6)
            self._detail_forms[mapping_key] = detail_form
            for shp_field, fubiao_field in detail_fields.items():
                row_widget = self._create_mapping_row(mapping_key, 'detail_fields', shp_field, fubiao_field, removable=True)
                detail_form.addRow(f"shp[{shp_field}] →", row_widget)
            tab_layout.addLayout(detail_form)

            tab_layout.addStretch()

            tab_widget.addTab(tab_page, tab_title)

        layout.addWidget(tab_widget, 1)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.save_btn = QPushButton("保存并生效")
        self.save_btn.clicked.connect(self._save_config)
        btn_layout.addWidget(self.save_btn)

        self.reset_btn = QPushButton("恢复默认")
        self.reset_btn.setObjectName("clearBtn")
        self.reset_btn.clicked.connect(self._reset_to_default)
        btn_layout.addWidget(self.reset_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.status_label = QLabel("")
        self.status_label.setObjectName("secondaryLabel")
        layout.addWidget(self.status_label)

    def _create_mapping_row(self, mapping_key, field_type, shp_field, fubiao_field, removable=True):
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)

        edit = QLineEdit()
        edit.setText(fubiao_field)
        edit.setPlaceholderText("附表字段名")
        edit.setMinimumWidth(180)
        self._mapping_edits[(mapping_key, field_type, shp_field)] = edit
        row_layout.addWidget(edit, 1)

        if removable:
            del_btn = QToolButton()
            del_btn.setText("\u2715")
            del_btn.setFixedSize(22, 22)
            del_btn.setObjectName("settingsDelBtn")
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setToolTip("删除此映射")
            del_btn.clicked.connect(lambda checked, mk=mapping_key, ft=field_type, sf=shp_field: self._remove_detail_row(mk, ft, sf))
            row_layout.addWidget(del_btn)

        return row

    def _add_detail_row(self, mapping_key):
        from PySide6.QtWidgets import QInputDialog
        shp_field, ok = QInputDialog.getText(self, "添加详情字段", "请输入SHP字段名（作为映射键）:")
        if not ok or not shp_field.strip():
            return
        shp_field = shp_field.strip()
        existing_key = (mapping_key, 'detail_fields', shp_field)
        if existing_key in self._mapping_edits:
            QMessageBox.warning(self, "提示", f"字段 [{shp_field}] 已存在")
            return

        detail_form = self._detail_forms.get(mapping_key)
        if not detail_form:
            return

        row_widget = self._create_mapping_row(mapping_key, 'detail_fields', shp_field, '', removable=True)
        detail_form.addRow(f"shp[{shp_field}] →", row_widget)

    def _remove_detail_row(self, mapping_key, field_type, shp_field):
        key = (mapping_key, field_type, shp_field)
        if key not in self._mapping_edits:
            return
        edit = self._mapping_edits.pop(key)
        row_widget = edit.parentWidget()
        if not row_widget:
            return
        form_layout = self._detail_forms.get(mapping_key)
        if form_layout is None:
            parent_widget = row_widget.parentWidget()
            if parent_widget is not None:
                form_layout = parent_widget.layout()
        if form_layout is None:
            row_widget.hide()
            row_widget.deleteLater()
            return
        for i in range(form_layout.rowCount()):
            item = form_layout.itemAt(i, QFormLayout.FieldRole)
            if item and item.widget() is row_widget:
                label_item = form_layout.itemAt(i, QFormLayout.LabelRole)
                if label_item and label_item.widget():
                    label_item.widget().hide()
                    label_item.widget().deleteLater()
                form_layout.removeRow(i)
                row_widget.hide()
                row_widget.deleteLater()
                return
        row_widget.hide()
        row_widget.deleteLater()

    def _make_header(self, title: str, subtitle: str) -> QFrame:
        header_card = QFrame()
        header_card.setObjectName("pageHeader")
        header_layout = QHBoxLayout(header_card)
        header_layout.setSpacing(16)
        header_layout.setContentsMargins(20, 14, 20, 14)

        accent_bar = QFrame()
        accent_bar.setObjectName("accentBar")
        accent_bar.setFixedWidth(4)
        header_layout.addWidget(accent_bar)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        t = QLabel(title)
        t.setObjectName("sectionHeaderLg")
        title_layout.addWidget(t)
        s = QLabel(subtitle)
        s.setObjectName("pageSubtitle")
        title_layout.addWidget(s)
        header_layout.addLayout(title_layout, 1)
        return header_card

    def _save_config(self):
        new_mapping = {}
        for (mapping_key, field_type, shp_field), edit in self._mapping_edits.items():
            if mapping_key not in new_mapping:
                new_mapping[mapping_key] = {'match_fields': {}, 'detail_fields': {}}
            value = edit.text().strip()
            if value:
                new_mapping[mapping_key][field_type][shp_field] = value

        if self.mapping_config.save_mapping(new_mapping):
            self.status_label.setText("\u2713 \u914d\u7f6e\u5df2\u4fdd\u5b58\u5e76\u7acb\u5373\u751f\u6548")
            self.status_label.setObjectName("settingsStatusSuccess")
            self.style().unpolish(self.status_label)
            self.style().polish(self.status_label)
            self.config_changed.emit()
        else:
            QMessageBox.warning(self, "\u5931\u8d25", "\u4fdd\u5b58\u914d\u7f6e\u5931\u8d25")

    def _reset_to_default(self):
        import copy
        default = copy.deepcopy(DEFAULT_VALIDATION_FIELD_MAPPING)
        for (mapping_key, field_type, shp_field), edit in self._mapping_edits.items():
            value = default.get(mapping_key, {}).get(field_type, {}).get(shp_field, '')
            edit.setText(value)
        self.status_label.setText('\u5df2\u6062\u5909\u9ed8\u8ba4\u503c\uff0c\u70b9\u51fb"\u4fdd\u5b58\u5e76\u751f\u6548"\u4f7f\u5176\u751f\u6548')
        self.status_label.setObjectName("settingsStatusWarning")
        self.style().unpolish(self.status_label)
        self.style().polish(self.status_label)


class TiandituSettingsPage(QWidget):
    config_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = TiandituConfig()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)

        header = self._make_header("天地图配置", "配置天地图地图服务的API密钥，用于底图加载")
        layout.addWidget(header)

        config_card = QFrame()
        config_card.setObjectName("card")
        config_inner = QVBoxLayout(config_card)
        config_inner.setSpacing(12)

        card_title = QLabel("API Key 设置")
        card_title.setObjectName("sectionHeaderMd")
        config_inner.addWidget(card_title)

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

        self.save_btn = QPushButton("保存并生效")
        self.save_btn.clicked.connect(self._save_config)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

        self.status_label = QLabel("")
        self.status_label.setObjectName("secondaryLabel")
        layout.addWidget(self.status_label)

        layout.addStretch()

    def _make_header(self, title: str, subtitle: str) -> QFrame:
        header_card = QFrame()
        header_card.setObjectName("pageHeader")
        header_layout = QHBoxLayout(header_card)
        header_layout.setSpacing(16)
        header_layout.setContentsMargins(20, 14, 20, 14)

        accent_bar = QFrame()
        accent_bar.setObjectName("accentBar")
        accent_bar.setFixedWidth(4)
        header_layout.addWidget(accent_bar)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        t = QLabel(title)
        t.setObjectName("sectionHeaderLg")
        title_layout.addWidget(t)
        s = QLabel(subtitle)
        s.setObjectName("pageSubtitle")
        title_layout.addWidget(s)
        header_layout.addLayout(title_layout, 1)
        return header_card

    def _reset_to_default(self):
        self.key_edit.setText(DEFAULT_TIANDITU_KEY)

    def _save_config(self):
        key = self.key_edit.text().strip()
        if not key:
            QMessageBox.warning(self, "提示", "API Key不能为空")
            return
        if self.config.save_api_key(key):
            self.status_label.setText("\u2713 \u914d\u7f6e\u5df2\u4fdd\u5b58\u5e76\u7acb\u5373\u751f\u6548")
            self.status_label.setObjectName("settingsStatusSuccess")
            self.style().unpolish(self.status_label)
            self.style().polish(self.status_label)
            self.config_changed.emit()
        else:
            QMessageBox.warning(self, "失败", "保存配置失败")


class SystemSettingsDialog(QDialog):
    theme_changed = Signal(str)
    config_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_page_id = "theme"

        self.setWindowTitle("系统参数配置")
        self.setMinimumSize(900, 560)
        self.setWindowFlags(self.windowFlags() | Qt.Dialog | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)

        self._init_ui()
        self._apply_dialog_theme()

    def _init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        sidebar = QFrame()
        sidebar.setObjectName("settingsSidebar")
        sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(0)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)

        sidebar_header = QLabel("  系统参数配置")
        sidebar_header.setObjectName("settingsSidebarHeader")
        sidebar_header.setFixedHeight(48)
        sidebar_layout.addWidget(sidebar_header)

        sep = QFrame()
        sep.setObjectName("sidebarSeparator")
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sidebar_layout.addWidget(sep)

        self._nav_items = []
        for cfg in SETTINGS_MENU:
            btn = _SettingsNavItem(cfg["icon"], cfg["text"], cfg["id"])
            btn.clicked.connect(lambda checked, bid=cfg["id"]: self._on_nav_clicked(bid))
            sidebar_layout.addWidget(btn)
            self._nav_items.append(btn)

        sidebar_layout.addStretch()

        close_btn = QPushButton("  ✕   关闭")
        close_btn.setObjectName("settingsCloseBtn")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFixedHeight(36)
        close_btn.clicked.connect(self.reject)
        sidebar_layout.addWidget(close_btn)

        main_layout.addWidget(sidebar)

        self.page_stack = QStackedWidget()
        self.page_stack.setObjectName("settingsContent")

        self.theme_page = ThemeSettingsPage()
        self.theme_page.theme_changed.connect(self._on_theme_changed)
        self.page_stack.addWidget(self.theme_page)

        self.default_params_page = DefaultParamsPage()
        self.default_params_page.config_changed.connect(self._on_config_changed)
        self.page_stack.addWidget(self.default_params_page)

        self.shp_format_page = ShpFormatParamsPage()
        self.shp_format_page.config_changed.connect(self._on_config_changed)
        self.page_stack.addWidget(self.shp_format_page)

        self.validation_mapping_page = ValidationMappingSettingsPage()
        self.validation_mapping_page.config_changed.connect(self._on_config_changed)
        self.page_stack.addWidget(self.validation_mapping_page)

        self.tianditu_page = TiandituSettingsPage()
        self.tianditu_page.config_changed.connect(self._on_config_changed)
        self.page_stack.addWidget(self.tianditu_page)

        main_layout.addWidget(self.page_stack, 1)

        self.setLayout(main_layout)
        self._on_nav_clicked("theme")

    def _on_nav_clicked(self, item_id: str):
        self._current_page_id = item_id
        page_index = next((i for i, cfg in enumerate(SETTINGS_MENU) if cfg["id"] == item_id), 0)
        self.page_stack.setCurrentIndex(page_index)

        for btn in self._nav_items:
            btn.setChecked(btn.item_id == item_id)

    def _on_theme_changed(self, mode: str):
        self.theme_changed.emit(mode)
        self._apply_dialog_theme()

    def _on_config_changed(self):
        self.config_changed.emit()

    def _apply_dialog_theme(self):
        theme_manager = get_theme_manager()
        theme = theme_manager.get_current_theme()

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(theme.get('content_bg', '#f0f2f5')))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        self.setStyleSheet(theme_manager.get_stylesheet())

    def reject(self):
        self.theme_page.restore_original()
        super().reject()

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
