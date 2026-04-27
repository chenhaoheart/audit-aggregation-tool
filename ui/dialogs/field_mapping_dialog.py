# -*- coding: utf-8 -*-
"""
字段映射配置对话框 - 支持多SHP导入配置
"""

import os
import json
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QMessageBox, QFileDialog, QAbstractItemView,
    QWidget, QFrame, QSplitter, QPlainTextEdit, QComboBox, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette
from core.config_manager import get_config, DEFAULT_RULES
from core.theme_manager import get_theme_manager

# ============================================================
# Theme-aware QSS helper functions for inline styles
# ============================================================

def _danger_button_qss(fixed_size=None):
    """Generate danger button QSS using theme colors."""
    theme = get_theme_manager().get_current_theme()
    hover_start = theme.get('btn_danger_hover_start', '#c0392b')
    hover_end = theme.get('btn_danger_hover_end', '#b91c1c')
    if fixed_size:
        size_qss = f"min-width: {fixed_size[0]}px; max-width: {fixed_size[0]}px; min-height: {fixed_size[1]}px; max-height: {fixed_size[1]}px;"
    else:
        size_qss = "min-width: 0px;"
    return f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {theme.get('btn_danger_start', '#e74c3c')},
                stop:1 {theme.get('btn_danger_end', '#c0392b')});
            color: white;
            border: 1px solid {theme.get('btn_danger_end', '#c0392b')};
            border-radius: 0px;
            font-size: 12px;
            padding: 0px;
            {size_qss}
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {hover_start},
                stop:1 {hover_end});
        }}
    """


def _secondary_button_qss():
    """Generate secondary/gray button QSS using theme colors."""
    theme = get_theme_manager().get_current_theme()
    return f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {theme.get('btn_secondary_start', '#95a5a6')},
                stop:1 {theme.get('btn_secondary_end', '#7f8c8d')});
            color: white;
            border: 1px solid {theme.get('btn_secondary_end', '#7f8c8d')};
            border-radius: 0px;
            padding: 0 16px;
            min-width: 0px;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {theme.get('btn_secondary_end', '#7f8c8d')},
                stop:1 {theme.get('btn_secondary_start', '#95a5a6')});
        }}
    """


def _success_button_qss():
    """Generate success button QSS using theme colors."""
    theme = get_theme_manager().get_current_theme()
    return f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {theme.get('btn_success_start', '#2ecc71')},
                stop:1 {theme.get('btn_success_end', '#27ae60')});
            color: white;
            border: 1px solid {theme.get('btn_success_end', '#27ae60')};
            border-radius: 0px;
            padding: 0 16px;
            min-width: 0px;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {theme.get('btn_success_hover_start', '#27ae60')},
                stop:1 {theme.get('btn_success_hover_end', '#1e8449')});
        }}
    """


def _tag_bg_style(matched=False):
    """Generate CandidateTag background style using theme accent color."""
    theme = get_theme_manager().get_current_theme()
    if matched:
        bg = theme.get('success_text', '#27ae60')
        return f"""
            CandidateTag {{
                background: {bg};
                border: 1px solid {theme.get('btn_success_end', '#1e7e34')};
            }}
        """
    else:
        bg = theme.get('accent_color', '#6366f1')
        return f"""
            CandidateTag {{
                background: {bg};
                border: 1px solid {theme.get('btn_info_start', '#3b82f6')};
            }}
        """


def _status_success_style():
    theme = get_theme_manager().get_current_theme()
    return f"color: {theme.get('success_text', '#27ae60')}; font-weight: bold;"


def _status_error_style():
    theme = get_theme_manager().get_current_theme()
    return f"color: {theme.get('error_text', '#e74c3c')};"


def _theme_qcolor(key: str, fallback: str = '#000000') -> QColor:
    """Get a QColor from theme by key."""
    return QColor(get_theme_manager().get_color(key) or fallback)


def read_shp_fields(shp_path):
    """读取SHP文件的字段列表"""
    fields = []
    errors = []

    # 方法1：使用pyshp库
    try:
        import shapefile
        sf = shapefile.Reader(shp_path)
        for field in sf.fields[1:]:
            field_name = field[0]
            fields.append(field_name)
        if fields:
            return fields, None
    except ImportError:
        errors.append("pyshp库未安装，使用DBF直接读取")
    except Exception as e:
        errors.append(f"pyshp读取失败: {e}")

    # 方法2：DBF直接读取
    base_path = os.path.splitext(shp_path)[0]
    dbf_path = base_path + '.dbf'
    if not os.path.exists(dbf_path):
        dbf_path = base_path + '.DBF'

    if os.path.exists(dbf_path):
        try:
            with open(dbf_path, 'rb') as f:
                f.read(1)  # 版本
                f.read(3)  # 日期
                f.read(4)  # 记录数
                header_size = int.from_bytes(f.read(2), 'little')
                f.read(2)  # 记录长度
                f.read(20)  # 保留

                pos = 32
                while pos < header_size - 1:
                    field_name_bytes = f.read(11)
                    if len(field_name_bytes) < 11:
                        break
                    if field_name_bytes[0] == 0x0D:
                        break

                    field_name = None
                    for encoding in ['gbk', 'gb2312', 'cp936', 'utf-8', 'latin1']:
                        try:
                            decoded = field_name_bytes.rstrip(b'\x00').decode(encoding)
                            field_name = ''.join(c for c in decoded if c.isprintable()).strip()
                            if field_name:
                                break
                        except Exception:
                            continue

                    if not field_name:
                        field_name = f"FIELD_{len(fields)}"

                    if field_name:
                        fields.append(field_name)

                    f.read(21)
                    pos += 32

            if fields:
                return fields, None
            errors.append("DBF解析未找到字段")
        except Exception as e:
            errors.append(f"DBF解析失败: {e}")
    else:
        errors.append(f"找不到DBF文件: {dbf_path}")

    return fields, "; ".join(errors)


class CandidateTag(QFrame):
    """候选字段标签 - 简单边框样式"""
    deleted = Signal(str)

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._text = text
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 2, 2)
        layout.setSpacing(2)

        theme = get_theme_manager().get_current_theme()
        self.label = QLabel(self._text)
        self.label.setStyleSheet(f"color: {theme.get('text_primary', 'white')}; font-size: 12px;")
        layout.addWidget(self.label)

        self.delete_btn = QPushButton("×")
        self.delete_btn.setFixedSize(18, 18)
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {theme.get('text_primary', 'white')};
                border: none; border-radius: 0px;
                font-size: 16px; font-weight: bold;
                min-width: 0px; padding: 0px;
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.3);
            }}
        """)
        self.delete_btn.clicked.connect(self._on_delete)
        layout.addWidget(self.delete_btn)

        self.setStyleSheet(_tag_bg_style(matched=False))
        self.setMinimumHeight(24)

    @property
    def text(self) -> str:
        return self._text

    def _on_delete(self):
        self.deleted.emit(self._text)

    def set_matched(self, matched: bool):
        self.setStyleSheet(_tag_bg_style(matched=matched))


class CandidateFieldList(QWidget):
    """候选字段列表 - 简单边框样式"""
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._candidates = []
        self._shp_fields = []
        self._matched_fields = []
        self._setup_ui()

    def _setup_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(4)
        self.main_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.tags_layout = QHBoxLayout()
        self.tags_layout.setSpacing(4)
        self.tags_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.main_layout.addLayout(self.tags_layout)

        theme = get_theme_manager().get_current_theme()
        accent = theme.get('accent_color', '#6366f1')
        self.add_btn = QPushButton("+")
        self.add_btn.setFixedSize(24, 24)
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {accent}; color: white; border: 1px solid {theme.get('btn_info_start', '#3b82f6')};
                font-size: 18px; font-weight: bold;
                border-radius: 0px; min-width: 0px; padding: 0px;
            }}
            QPushButton:hover {{ background: {theme.get('btn_info_hover_start', '#5a5fd6')}; }}
        """)
        self.add_btn.clicked.connect(self._on_add)
        self.main_layout.addWidget(self.add_btn)
        self.main_layout.addStretch()

    def set_shp_fields(self, fields: list):
        self._shp_fields = fields

    def set_matched_fields(self, matched: list):
        self._matched_fields = matched
        self._update_tag_styles()

    def set_candidates(self, candidates: list):
        self._candidates = list(candidates)
        self._rebuild_tags()
        self.changed.emit()

    def get_candidates(self) -> list:
        return self._candidates.copy()

    def add_candidate(self, candidate: str):
        if candidate and candidate not in self._candidates:
            self._candidates.append(candidate)
            self._rebuild_tags()
            self.changed.emit()

    def _rebuild_tags(self):
        while self.tags_layout.count():
            item = self.tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for candidate in self._candidates:
            tag = CandidateTag(candidate)
            tag.deleted.connect(self._on_tag_deleted)
            if candidate in self._matched_fields:
                tag.set_matched(True)
            self.tags_layout.addWidget(tag)

    def _update_tag_styles(self):
        for i in range(self.tags_layout.count()):
            item = self.tags_layout.itemAt(i)
            if item and item.widget():
                tag = item.widget()
                if isinstance(tag, CandidateTag):
                    tag.set_matched(tag.text in self._matched_fields)

    def _on_add(self):
        dialog = AddCandidateDialog(self._shp_fields, self)
        if dialog.exec() == QDialog.Accepted:
            field_name = dialog.get_field_name()
            if field_name and field_name not in self._candidates:
                self._candidates.append(field_name)
                self._rebuild_tags()
                self.changed.emit()

    def _on_tag_deleted(self, text: str):
        if text in self._candidates:
            self._candidates.remove(text)
            self._rebuild_tags()
            self.changed.emit()


class AddCandidateDialog(QDialog):
    """添加候选字段"""

    def __init__(self, shp_fields: list = None, parent=None):
        super().__init__(parent)
        self._shp_fields = shp_fields or []

        # 设置主题样式（支持暗黑主题）
        self.theme_manager = get_theme_manager()
        theme = self.theme_manager.get_current_theme()
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(theme['content_bg']))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        self.setStyleSheet(self.theme_manager.get_stylesheet())

        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("添加候选字段")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        layout.addWidget(QLabel("添加候选字段名："))

        input_layout = QHBoxLayout()
        if self._shp_fields:
            self.field_combo = QComboBox()
            self.field_combo.addItems(self._shp_fields)
            self.field_combo.setEditable(True)
            self.field_combo.lineEdit().setPlaceholderText("选择或输入字段名...")
            input_layout.addWidget(self.field_combo, 1)
        else:
            self.field_edit = QLineEdit()
            self.field_edit.setPlaceholderText("输入字段名...")
            input_layout.addWidget(self.field_edit, 1)
        layout.addLayout(input_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self._on_ok)
        btn_layout.addWidget(ok_btn)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def get_field_name(self) -> str:
        if hasattr(self, 'field_combo'):
            return self.field_combo.currentText().strip()
        elif hasattr(self, 'field_edit'):
            return self.field_edit.text().strip()
        return ""

    def _on_ok(self):
        if not self.get_field_name():
            QMessageBox.warning(self, "提示", "请输入字段名")
            return
        self.accept()


class ShpConfigWidget(QWidget):
    """单个SHP文件的配置面板"""
    config_changed = Signal()

    OUTPUT_LAYERS = [
        "隐患要素分布L.shp",
        "断面平面位置L.shp",
        "防治对象分布P.shp",
        "【自定义图层】"
    ]

    KEYWORD_RULES = {
        "隐患要素分布L.shp": ["隐患", "灾害", "地质", "滑坡", "崩塌", "泥石流"],
        "断面平面位置L.shp": ["断面", "剖面", "横断", "纵断"],
        "防治对象分布P.shp": ["防治", "保护", "对象", "居民", "建筑", "设施"]
    }

    def __init__(self, shp_path: str, source_fields: list, parent=None):
        super().__init__(parent)
        self.shp_path = shp_path
        self.shp_name = os.path.basename(shp_path)
        self.source_fields = source_fields or []
        self._field_mapping = {}
        self._keywords = []  # 用户自定义的关键词
        self.theme_manager = get_theme_manager()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 输出图层选择
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出图层:"))

        self.output_combo = QComboBox()
        self.output_combo.addItems(self.OUTPUT_LAYERS)
        self.output_combo.currentTextChanged.connect(self._on_output_changed)
        output_layout.addWidget(self.output_combo, 1)

        self.custom_output_edit = QLineEdit()
        self.custom_output_edit.setPlaceholderText("输入自定义输出图层名称，如: 水系分布L.shp")
        self.custom_output_edit.setVisible(False)
        self.custom_output_edit.textChanged.connect(lambda: self.config_changed.emit())
        output_layout.addWidget(self.custom_output_edit, 1)

        self.auto_match_btn = QPushButton("自动匹配")
        self.auto_match_btn.setFixedHeight(36)
        self.auto_match_btn.setCursor(Qt.PointingHandCursor)
        self.auto_match_btn.setToolTip("根据文件名关键词自动匹配输出图层")
        self.auto_match_btn.setObjectName("validateBtn")
        self.auto_match_btn.clicked.connect(self._auto_match_output)
        output_layout.addWidget(self.auto_match_btn)

        layout.addLayout(output_layout)

        # 关键词编辑（仅自定义图层显示）
        self.kw_widget = QWidget()
        kw_layout = QHBoxLayout(self.kw_widget)
        kw_layout.setContentsMargins(0, 0, 0, 0)
        kw_layout.addWidget(QLabel("匹配关键词:"))
        self.keywords_edit = QLineEdit()
        self.keywords_edit.setPlaceholderText("多个关键词用逗号分隔，如: 水系,河流,水网")
        self.keywords_edit.textChanged.connect(self._on_keywords_changed)
        kw_layout.addWidget(self.keywords_edit, 1)
        self.kw_widget.setVisible(False)
        layout.addWidget(self.kw_widget)

        # 匹配状态提示
        self.match_hint_label = QLabel("")
        self.match_hint_label.setObjectName("secondaryLabel")
        layout.addWidget(self.match_hint_label)

        # 源字段信息
        info_label = QLabel(f"源字段 ({len(self.source_fields)}个): {', '.join(self.source_fields[:10])}{'...' if len(self.source_fields) > 10 else ''}")
        info_label.setObjectName("secondaryLabel")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # 字段映射表格
        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(4)
        self.mapping_table.setHorizontalHeaderLabels(["目标字段", "候选字段列表", "匹配状态", "操作"])
        self.mapping_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.mapping_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.mapping_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.mapping_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.mapping_table.setColumnWidth(0, 120)
        self.mapping_table.setColumnWidth(2, 100)
        self.mapping_table.setColumnWidth(3, 70)
        self.mapping_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.mapping_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.mapping_table.setAlternatingRowColors(False)
        self.mapping_table.verticalHeader().setDefaultSectionSize(40)  # 增加行高
        self.mapping_table.verticalHeader().setVisible(False)
        self.mapping_table.cellChanged.connect(self._on_target_field_changed)
        layout.addWidget(self.mapping_table)

        # 添加字段按钮
        add_btn_layout = QHBoxLayout()
        add_btn_layout.setSpacing(6)
        add_btn = QPushButton("+ 添加目标字段")
        add_btn.setFixedHeight(36)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setObjectName("exportBtn")
        add_btn.clicked.connect(self._add_target_field)
        add_btn_layout.addStretch()
        add_btn_layout.addWidget(add_btn)

        auto_add_btn = QPushButton("从源字段添加")
        auto_add_btn.setToolTip("将源字段作为目标字段添加到映射表")
        auto_add_btn.setFixedHeight(36)
        auto_add_btn.setCursor(Qt.PointingHandCursor)
        auto_add_btn.setObjectName("logToggleBtn")
        auto_add_btn.clicked.connect(self._add_from_source_fields)
        add_btn_layout.addWidget(auto_add_btn)

        layout.addLayout(add_btn_layout)

        # 初始化
        self._auto_match_output()

    def _auto_match_output(self):
        """自动匹配输出图层"""
        name_lower = self.shp_name.lower()
        matched_output = None
        matched_keyword = None

        for output_name, keywords in self.KEYWORD_RULES.items():
            for keyword in keywords:
                if keyword.lower() in name_lower:
                    matched_output = output_name
                    matched_keyword = keyword
                    break
            if matched_output:
                break

        if matched_output:
            self.output_combo.blockSignals(True)
            self.output_combo.setCurrentText(matched_output)
            self.output_combo.blockSignals(False)
            self.match_hint_label.setText(f"✓ 自动匹配: 检测到关键词 '{matched_keyword}'")
            self.match_hint_label.setStyleSheet(self.theme_manager.get_inline_style('env_success'))
            self.custom_output_edit.setVisible(False)
            self.kw_widget.setVisible(False)  # 预设图层不需要编辑关键词
            self._keywords = []
            self._load_default_field_mapping(matched_output)
        else:
            self.output_combo.blockSignals(True)
            self.output_combo.setCurrentText("【自定义图层】")
            self.output_combo.blockSignals(False)
            self.custom_output_edit.setVisible(True)
            self.custom_output_edit.setFocus()
            self.kw_widget.setVisible(True)  # 自定义图层需要编辑关键词
            self.match_hint_label.setText("⚠ 未匹配到预设图层，请手动选择或输入自定义图层名称")
            self.match_hint_label.setStyleSheet(self.theme_manager.get_inline_style('env_warning'))

            # 从文件名自动提取关键词
            self._extract_keywords_from_filename()

            self._field_mapping = {}
            self._refresh_table()

        self.config_changed.emit()

    def _extract_keywords_from_filename(self):
        """从文件名提取关键词"""
        # 去除扩展名和常见前后缀
        name = os.path.splitext(self.shp_name)[0]

        # 去除常见前缀
        prefixes = ['DZ_', 'dz_', 'DZ', 'dz', 'XZ_', 'xz_', 'XZ', 'xz']
        for prefix in prefixes:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break

        # 去除数字和特殊字符，提取中文/英文关键词
        import re
        # 提取中文词
        chinese = re.findall(r'[\u4e00-\u9fa5]+', name)
        # 提取英文词
        english = re.findall(r'[A-Za-z]+', name)

        keywords = []
        if chinese:
            keywords.extend(chinese)
        if english:
            # 过滤太短的英文
            keywords.extend([w for w in english if len(w) > 2])

        if keywords:
            self.keywords_edit.setText(', '.join(keywords))
        else:
            self.keywords_edit.setText(name)

    def _on_keywords_changed(self, text: str):
        """关键词改变"""
        self._keywords = [k.strip() for k in text.split(',') if k.strip()]
        self.config_changed.emit()

    def _on_output_changed(self, output_name: str):
        """输出图层改变"""
        if output_name == "【自定义图层】":
            self.custom_output_edit.setVisible(True)
            self.custom_output_edit.setFocus()
            self.kw_widget.setVisible(True)
            self.match_hint_label.setText("请输入自定义输出图层名称和匹配关键词")
            self.match_hint_label.setStyleSheet(self.theme_manager.get_inline_style('env_info'))
            self._extract_keywords_from_filename()
            self._field_mapping = {}
            self._refresh_table()
        else:
            self.custom_output_edit.setVisible(False)
            self.kw_widget.setVisible(False)  # 预设图层不显示关键词编辑
            self.match_hint_label.setText("")
            self._keywords = []
            self._load_default_field_mapping(output_name)
        self.config_changed.emit()

    def _load_default_field_mapping(self, output_name: str):
        """加载默认字段映射"""
        for rule in DEFAULT_RULES:
            if rule['output_name'] == output_name:
                self._field_mapping = rule.get('field_mapping', {}).copy()
                break
        else:
            self._field_mapping = {}
        self._refresh_table()

    def _refresh_table(self):
        """刷新表格"""
        self.mapping_table.blockSignals(True)
        self.mapping_table.setRowCount(0)

        for target, candidates in self._field_mapping.items():
            row = self.mapping_table.rowCount()
            self.mapping_table.insertRow(row)

            target_item = QTableWidgetItem(target)
            self.mapping_table.setItem(row, 0, target_item)

            candidates_widget = CandidateFieldList()
            candidates_widget.set_shp_fields(self.source_fields)
            candidates_widget.set_candidates(candidates)
            candidates_widget.changed.connect(self._update_match_status)
            self.mapping_table.setCellWidget(row, 1, candidates_widget)

            status_label = QLabel("--")
            status_label.setAlignment(Qt.AlignCenter)
            self.mapping_table.setCellWidget(row, 2, status_label)

            # 删除按钮容器 - 去掉边距
            delete_container = QWidget()
            delete_layout = QHBoxLayout(delete_container)
            delete_layout.setContentsMargins(0, 0, 0, 0)
            delete_btn = QPushButton("删除")
            delete_btn.setFixedSize(50, 26)
            delete_btn.setCursor(Qt.PointingHandCursor)
            delete_btn.setStyleSheet(_danger_button_qss(fixed_size=(50, 26)))
            delete_btn.clicked.connect(lambda checked, r=row: self._delete_target_field(r))
            delete_layout.addWidget(delete_btn)
            self.mapping_table.setCellWidget(row, 3, delete_container)

        self._update_match_status()
        self.mapping_table.blockSignals(False)

    def _update_match_status(self):
        """更新匹配状态"""
        for row in range(self.mapping_table.rowCount()):
            candidates_widget = self.mapping_table.cellWidget(row, 1)
            if not candidates_widget:
                continue

            candidates = candidates_widget.get_candidates()
            matched = None

            for c in candidates:
                if c in self.source_fields:
                    matched = c
                    break

            status_label = self.mapping_table.cellWidget(row, 2)
            if status_label:
                if matched:
                    status_label.setText(f"\u2713 {matched}")
                    status_label.setStyleSheet(_status_success_style())
                    candidates_widget.set_matched_fields([matched])
                else:
                    status_label.setText("\u2717 未匹配")
                    status_label.setStyleSheet(_status_error_style())
                    candidates_widget.set_matched_fields([])

    def _on_target_field_changed(self, row: int, column: int):
        """目标字段变化时触发配置更新"""
        if column == 0:  # 只有目标字段列变化才触发
            self.config_changed.emit()

    def _add_target_field(self):
        """添加目标字段"""
        row = self.mapping_table.rowCount()
        self.mapping_table.insertRow(row)

        target_item = QTableWidgetItem("")
        self.mapping_table.setItem(row, 0, target_item)

        candidates_widget = CandidateFieldList()
        candidates_widget.set_shp_fields(self.source_fields)
        candidates_widget.changed.connect(self._update_match_status)
        self.mapping_table.setCellWidget(row, 1, candidates_widget)

        status_label = QLabel("--")
        status_label.setAlignment(Qt.AlignCenter)
        self.mapping_table.setCellWidget(row, 2, status_label)

        # 删除按钮容器
        delete_container = QWidget()
        delete_layout = QHBoxLayout(delete_container)
        delete_layout.setContentsMargins(0, 0, 0, 0)
        delete_btn = QPushButton("删除")
        delete_btn.setFixedHeight(26)
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setStyleSheet(_danger_button_qss())
        delete_btn.clicked.connect(lambda checked, r=row: self._delete_target_field(r))
        delete_layout.addWidget(delete_btn)
        self.mapping_table.setCellWidget(row, 3, delete_container)

    def _add_from_source_fields(self):
        """从源字段添加"""
        self.mapping_table.setRowCount(0)

        for field in self.source_fields:
            row = self.mapping_table.rowCount()
            self.mapping_table.insertRow(row)

            target_item = QTableWidgetItem(field)
            self.mapping_table.setItem(row, 0, target_item)

            candidates_widget = CandidateFieldList()
            candidates_widget.set_shp_fields(self.source_fields)
            candidates_widget.add_candidate(field)
            candidates_widget.changed.connect(self._update_match_status)
            self.mapping_table.setCellWidget(row, 1, candidates_widget)

            status_label = QLabel(f"\u2713 {field}")
            status_label.setAlignment(Qt.AlignCenter)
            status_label.setStyleSheet(_status_success_style())
            self.mapping_table.setCellWidget(row, 2, status_label)

            # 删除按钮容器
            delete_container = QWidget()
            delete_layout = QHBoxLayout(delete_container)
            delete_layout.setContentsMargins(0, 0, 0, 0)
            delete_btn = QPushButton("删除")
            delete_btn.setFixedSize(50, 26)
            delete_btn.setCursor(Qt.PointingHandCursor)
            delete_btn.setStyleSheet(_danger_button_qss(fixed_size=(50, 26)))
            delete_btn.clicked.connect(lambda checked, r=row: self._delete_target_field(r))
            delete_layout.addWidget(delete_btn)
            self.mapping_table.setCellWidget(row, 3, delete_container)

        self.config_changed.emit()

    def _delete_target_field(self, row: int):
        """删除目标字段"""
        self.mapping_table.removeRow(row)
        for r in range(row, self.mapping_table.rowCount()):
            # 删除按钮容器
            delete_container = QWidget()
            delete_layout = QHBoxLayout(delete_container)
            delete_layout.setContentsMargins(0, 0, 0, 0)
            delete_btn = QPushButton("删除")
            delete_btn.setFixedSize(50, 26)
            delete_btn.setCursor(Qt.PointingHandCursor)
            delete_btn.setStyleSheet(_danger_button_qss(fixed_size=(50, 26)))
            delete_btn.clicked.connect(lambda checked, idx=r: self._delete_target_field(idx))
            delete_layout.addWidget(delete_btn)
            self.mapping_table.setCellWidget(r, 3, delete_container)
        self.config_changed.emit()

    def get_config(self) -> dict:
        """获取配置"""
        field_mapping = {}
        for row in range(self.mapping_table.rowCount()):
            target_item = self.mapping_table.item(row, 0)
            candidates_widget = self.mapping_table.cellWidget(row, 1)

            if target_item:
                target = target_item.text().strip()
                if target:
                    candidates = []
                    if candidates_widget:
                        candidates = candidates_widget.get_candidates()
                    if candidates:
                        field_mapping[target] = candidates

        output_name = self.output_combo.currentText()
        if output_name == "【自定义图层】":
            output_name = self.custom_output_edit.text().strip()
            if not output_name:
                output_name = "自定义图层.shp"

        return {
            'shp_path': self.shp_path,
            'shp_name': self.shp_name,
            'output_name': output_name,
            'keywords': self._keywords.copy() if self._keywords else [],
            'source_fields': self.source_fields,
            'field_mapping': field_mapping
        }


class FieldMappingDialog(QDialog):
    """字段映射配置对话框"""

    config_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("字段映射配置")
        self.setMinimumSize(1100, 700)
        self._shp_configs = []

        # 使用主题管理器
        self.theme_manager = get_theme_manager()
        self.setStyleSheet(self.theme_manager.get_stylesheet())

        # 设置对话框背景色（QSS 无法控制 QDialog 原生背景，需用调色板）
        theme = self.theme_manager.get_current_theme()
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(theme['content_bg']))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        self._setup_ui()

    def _setup_ui(self):
        # 应用主题样式（支持暗黑主题）
        self.setStyleSheet(self.theme_manager.get_stylesheet())

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # ========== 页面标题区 ==========
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

        page_title = QLabel("字段映射配置")
        page_title.setObjectName("sectionHeaderLg")
        title_layout.addWidget(page_title)

        page_subtitle = QLabel("添加SHP文件并配置目标字段映射规则")
        page_subtitle.setObjectName("pageSubtitle")
        title_layout.addWidget(page_subtitle)

        header_layout.addLayout(title_layout, 1)
        layout.addWidget(header_card)

        # ========== 添加SHP卡片 ==========
        add_card = QFrame()
        add_card.setObjectName("card")
        add_inner = QVBoxLayout(add_card)
        add_inner.setSpacing(10)

        # 卡片标题
        card_title_layout = QHBoxLayout()
        card_title_layout.setSpacing(8)
        card_title = QLabel("添加SHP文件")
        card_title.setObjectName("sectionHeaderMd")
        card_title_layout.addWidget(card_title)
        card_title_layout.addStretch()
        add_inner.addLayout(card_title_layout)

        # 按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.add_shp_btn = QPushButton("选择SHP文件...")
        self.add_shp_btn.setFixedHeight(38)
        self.add_shp_btn.setCursor(Qt.PointingHandCursor)
        self.add_shp_btn.setObjectName("validateBtn")
        self.add_shp_btn.clicked.connect(self._add_shp_files)
        btn_row.addWidget(self.add_shp_btn)

        self.add_folder_btn = QPushButton("选择文件夹...")
        self.add_folder_btn.setFixedHeight(38)
        self.add_folder_btn.setCursor(Qt.PointingHandCursor)
        self.add_folder_btn.setObjectName("validateBtn")
        self.add_folder_btn.clicked.connect(self._add_shp_folder)
        btn_row.addWidget(self.add_folder_btn)

        btn_row.addStretch()

        self.clear_all_btn = QPushButton("清空全部")
        self.clear_all_btn.setFixedHeight(38)
        self.clear_all_btn.setCursor(Qt.PointingHandCursor)
        self.clear_all_btn.setObjectName("clearBtn")
        self.clear_all_btn.clicked.connect(self._clear_all)
        btn_row.addWidget(self.clear_all_btn)

        add_inner.addLayout(btn_row)
        layout.addWidget(add_card)

        # ========== 中部：左侧列表 + 右侧配置 ==========
        splitter_card = QFrame()
        splitter_card.setObjectName("card")
        splitter_card_layout = QVBoxLayout(splitter_card)
        splitter_card_layout.setSpacing(0)
        splitter_card_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("cardInnerPanel")

        # 左侧：SHP文件列表
        left_widget = QWidget()
        left_widget.setObjectName("cardInnerPanel")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(16, 14, 4, 10)

        left_label = QLabel("已添加的SHP文件")
        left_label.setObjectName("boldLabel")
        left_layout.addWidget(left_label)

        self.shp_list = QTableWidget()
        self.shp_list.setColumnCount(4)
        self.shp_list.setHorizontalHeaderLabels(["文件名", "字段数", "输出图层", "操作"])
        self.shp_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.shp_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.shp_list.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.shp_list.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.shp_list.setColumnWidth(1, 60)
        self.shp_list.setColumnWidth(3, 70)
        self.shp_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.shp_list.setAlternatingRowColors(False)
        self.shp_list.verticalHeader().setDefaultSectionSize(32)
        self.shp_list.verticalHeader().setVisible(False)
        self.shp_list.itemSelectionChanged.connect(self._on_shp_selected)
        left_layout.addWidget(self.shp_list)

        splitter.addWidget(left_widget)

        # 右侧：当前SHP配置
        right_widget = QWidget()
        right_widget.setObjectName("cardInnerPanel")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(4, 14, 16, 10)

        self.config_title = QLabel("选择左侧SHP文件进行配置")
        self.config_title.setObjectName("boldLabel")
        right_layout.addWidget(self.config_title)

        self.config_stack = QWidget()
        self.config_stack.setObjectName("cardInnerPanel")
        self.config_stack_layout = QVBoxLayout(self.config_stack)
        self.config_stack_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.config_stack, 1)

        self.empty_hint = QLabel("\n\n请在左侧添加SHP文件")
        self.empty_hint.setAlignment(Qt.AlignCenter)
        self.empty_hint.setObjectName("secondaryLabel")
        self.config_stack_layout.addWidget(self.empty_hint)

        splitter.addWidget(right_widget)
        splitter.setSizes([350, 750])

        splitter_card_layout.addWidget(splitter, 1)
        layout.addWidget(splitter_card, 1)

        # ========== 底部按钮 ==========
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(8)

        self.export_btn = QPushButton("导出配置")
        self.export_btn.setFixedHeight(38)
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setObjectName("logToggleBtn")
        self.export_btn.clicked.connect(self._export_config)
        bottom_layout.addWidget(self.export_btn)

        self.import_btn = QPushButton("导入配置")
        self.import_btn.setFixedHeight(38)
        self.import_btn.setCursor(Qt.PointingHandCursor)
        self.import_btn.setObjectName("logToggleBtn")
        self.import_btn.clicked.connect(self._import_config)
        bottom_layout.addWidget(self.import_btn)

        self.export_rules_btn = QPushButton("Rules格式预览")
        self.export_rules_btn.setToolTip("预览并导出为merge_shp_中文属性转换_青海专用.py中使用的rules格式")
        self.export_rules_btn.setFixedHeight(38)
        self.export_rules_btn.setCursor(Qt.PointingHandCursor)
        self.export_rules_btn.setObjectName("validateBtn")
        self.export_rules_btn.clicked.connect(self._export_rules_format)
        bottom_layout.addWidget(self.export_rules_btn)

        bottom_layout.addStretch()

        self.save_btn = QPushButton("保存")
        self.save_btn.setFixedHeight(38)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.clicked.connect(self._save_and_close)
        bottom_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedHeight(38)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setObjectName("clearBtn")
        self.cancel_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(self.cancel_btn)

        layout.addLayout(bottom_layout)
        self.setLayout(layout)

    def _add_shp_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择SHP文件", "", "Shapefile (*.shp *.SHP)")
        for f in files:
            self._add_shp(f)

    def _add_shp_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            for root, dirs, files in os.walk(folder):
                for f in files:
                    if f.lower().endswith('.shp'):
                        self._add_shp(os.path.join(root, f))

    def _add_shp(self, shp_path: str):
        for cfg in self._shp_configs:
            if cfg.get('shp_path') == shp_path:
                QMessageBox.warning(self, "提示", f"文件已存在: {os.path.basename(shp_path)}")
                return

        fields, error = read_shp_fields(shp_path)
        if not fields:
            QMessageBox.warning(self, "错误", f"无法读取 {os.path.basename(shp_path)}:\n{error}")
            return

        shp_name = os.path.basename(shp_path)

        # 自动匹配输出图层
        output_name, keywords, field_mapping = self._auto_match_shp(shp_name)

        config = {
            'shp_path': shp_path,
            'shp_name': shp_name,
            'source_fields': fields,
            'output_name': output_name,
            'keywords': keywords,
            'field_mapping': field_mapping
        }
        self._shp_configs.append(config)
        self._refresh_shp_list()
        self.shp_list.selectRow(len(self._shp_configs) - 1)

    def _auto_match_shp(self, shp_name: str) -> tuple:
        """自动匹配SHP文件，返回 (output_name, keywords, field_mapping)"""
        name_lower = shp_name.lower()
        matched_output = None

        for output_name, keywords in ShpConfigWidget.KEYWORD_RULES.items():
            for keyword in keywords:
                if keyword.lower() in name_lower:
                    matched_output = output_name
                    break
            if matched_output:
                break

        if matched_output:
            # 预设图层：保留原始keywords和field_mapping
            for rule in DEFAULT_RULES:
                if rule['output_name'] == matched_output:
                    return matched_output, [], rule.get('field_mapping', {}).copy()
            return matched_output, [], {}
        else:
            # 自定义图层：从文件名提取关键词
            import re
            name = os.path.splitext(shp_name)[0]
            chinese = re.findall(r'[\u4e00-\u9fa5]+', name)
            english = re.findall(r'[A-Za-z]+', name)
            keywords = chinese + [w for w in english if len(w) > 2]
            return '', keywords, {}

    def _refresh_shp_list(self):
        self.shp_list.setRowCount(len(self._shp_configs))

        for row, cfg in enumerate(self._shp_configs):
            name_item = QTableWidgetItem(cfg.get('shp_name', ''))
            name_item.setData(Qt.UserRole, row)
            self.shp_list.setItem(row, 0, name_item)

            fields = cfg.get('source_fields', [])
            count_item = QTableWidgetItem(str(len(fields)))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.shp_list.setItem(row, 1, count_item)

            # 输出图层显示
            output_name = cfg.get('output_name', '')
            keywords = cfg.get('keywords', [])
            if output_name:
                output_item = QTableWidgetItem(output_name)
                output_item.setForeground(_theme_qcolor('success_text', '#27ae60'))
            elif keywords:
                # 自定义图层，有关键词但未设置输出名称
                output_item = QTableWidgetItem(f"[自定义] {', '.join(keywords[:2])}")
                output_item.setForeground(_theme_qcolor('warning_text', '#e67e22'))
            else:
                output_item = QTableWidgetItem('未设置')
                output_item.setForeground(_theme_qcolor('error_text', '#e74c3c'))
            self.shp_list.setItem(row, 2, output_item)

            delete_btn = QPushButton("删除")
            delete_btn.setFixedSize(50, 26)
            delete_btn.setCursor(Qt.PointingHandCursor)
            delete_btn.setStyleSheet(_danger_button_qss(fixed_size=(50, 26)))
            delete_btn.clicked.connect(lambda checked, r=row: self._remove_shp(r))
            # 删除按钮容器
            delete_container = QWidget()
            delete_layout = QHBoxLayout(delete_container)
            delete_layout.setContentsMargins(0, 0, 0, 0)
            delete_layout.addWidget(delete_btn)
            self.shp_list.setCellWidget(row, 3, delete_container)

    def _on_shp_selected(self):
        row = self.shp_list.currentRow()
        if row < 0 or row >= len(self._shp_configs):
            return

        # 清除旧面板
        while self.config_stack_layout.count():
            item = self.config_stack_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cfg = self._shp_configs[row]
        self.config_title.setText(f"配置: {cfg.get('shp_name', '')}")

        config_widget = ShpConfigWidget(cfg.get('shp_path', ''), cfg.get('source_fields', []), self)

        if cfg.get('output_name'):
            if cfg['output_name'] in ShpConfigWidget.OUTPUT_LAYERS:
                config_widget.output_combo.setCurrentText(cfg['output_name'])
            else:
                # 自定义图层已有名称
                config_widget.output_combo.setCurrentText("【自定义图层】")
                config_widget.custom_output_edit.setText(cfg['output_name'])
                config_widget.custom_output_edit.setVisible(True)
                config_widget.kw_widget.setVisible(True)
                if cfg.get('keywords'):
                    config_widget.keywords_edit.setText(', '.join(cfg['keywords']))
                    config_widget._keywords = cfg['keywords'].copy()
        elif cfg.get('keywords'):
            # 自定义图层，有关键词但未设置输出名称
            config_widget.output_combo.setCurrentText("【自定义图层】")
            config_widget.custom_output_edit.setVisible(True)
            config_widget.kw_widget.setVisible(True)
            config_widget.keywords_edit.setText(', '.join(cfg['keywords']))
            config_widget._keywords = cfg['keywords'].copy()

        if cfg.get('field_mapping'):
            config_widget._field_mapping = cfg['field_mapping'].copy()
            config_widget._refresh_table()

        config_widget.config_changed.connect(lambda: self._update_config(row, config_widget))
        self.config_stack_layout.addWidget(config_widget)

    def _update_config(self, row: int, widget: ShpConfigWidget):
        if 0 <= row < len(self._shp_configs):
            cfg = widget.get_config()
            self._shp_configs[row]['output_name'] = cfg['output_name']
            self._shp_configs[row]['keywords'] = cfg['keywords']
            self._shp_configs[row]['field_mapping'] = cfg['field_mapping']

            output_item = self.shp_list.item(row, 2)
            if output_item:
                output_item.setText(cfg['output_name'] or '未设置')
                if cfg['output_name']:
                    output_item.setForeground(_theme_qcolor('success_text', '#27ae60'))
                else:
                    output_item.setForeground(_theme_qcolor('error_text', '#e74c3c'))

    def _remove_shp(self, row: int):
        if 0 <= row < len(self._shp_configs):
            del self._shp_configs[row]
            self._refresh_shp_list()

            while self.config_stack_layout.count():
                item = self.config_stack_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self.config_stack_layout.addWidget(self.empty_hint)
            self.config_title.setText("选择左侧SHP文件进行配置")

    def _clear_all(self):
        if not self._shp_configs:
            return
        if QMessageBox.question(self, "确认", "确定要清空所有SHP文件吗？", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self._shp_configs.clear()
            self._refresh_shp_list()
            while self.config_stack_layout.count():
                item = self.config_stack_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self.config_stack_layout.addWidget(self.empty_hint)
            self.config_title.setText("选择左侧SHP文件进行配置")

    def _export_config(self):
        if not self._shp_configs:
            QMessageBox.warning(self, "提示", "没有配置可导出")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "导出配置", "shp_mapping_config.json", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self._shp_configs, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "成功", "配置已导出")
            except Exception as e:
                QMessageBox.warning(self, "失败", f"导出失败: {e}")

    def _import_config(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "导入配置", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    configs = json.load(f)
                if not isinstance(configs, list):
                    QMessageBox.warning(self, "错误", "配置格式不正确")
                    return
                self._shp_configs = configs
                self._refresh_shp_list()
                QMessageBox.information(self, "成功", f"已导入 {len(configs)} 个配置")
            except Exception as e:
                QMessageBox.warning(self, "失败", f"导入失败: {e}")

    def _export_rules_format(self):
        """导出为rules格式 - 先预览再保存"""

        # 判断是否有用户配置
        has_user_configs = bool(self._shp_configs)

        if has_user_configs:
            # 建立预设图层名称到原始keywords的映射
            preset_keywords = {}
            for rule in DEFAULT_RULES:
                preset_keywords[rule['output_name']] = rule.get('keywords', [])

            # 按output_name分组
            grouped = {}
            for cfg in self._shp_configs:
                output_name = cfg.get('output_name', '')
                if not output_name:
                    continue

                if output_name not in grouped:
                    if output_name in preset_keywords:
                        keywords = preset_keywords[output_name].copy()
                    else:
                        keywords = cfg.get('keywords', []).copy()
                    grouped[output_name] = {
                        'output_name': output_name,
                        'keywords': keywords,
                        'field_mapping': {}
                    }

                field_mapping = cfg.get('field_mapping', {})
                for target, candidates in field_mapping.items():
                    if target not in grouped[output_name]['field_mapping']:
                        grouped[output_name]['field_mapping'][target] = []
                    for c in candidates:
                        if c not in grouped[output_name]['field_mapping'][target]:
                            grouped[output_name]['field_mapping'][target].append(c)

            rules = list(grouped.values())

            if not rules:
                QMessageBox.warning(self, "提示", "没有有效的配置")
                return
        else:
            # 使用默认配置
            rules = DEFAULT_RULES.copy()

        # 创建预览对话框
        preview = QDialog(self)
        title = "Rules格式预览" if has_user_configs else "Rules格式预览 (系统默认配置)"
        preview.setWindowTitle(title)
        preview.setMinimumSize(900, 600)

        # 应用主题背景
        theme = self.theme_manager.get_current_theme()
        palette = preview.palette()
        palette.setColor(QPalette.Window, QColor(theme['content_bg']))
        preview.setPalette(palette)
        preview.setAutoFillBackground(True)
        preview.setStyleSheet(self.theme_manager.get_stylesheet())

        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(10, 10, 10, 10)

        # 使用分割器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：树形结构
        theme = self.theme_manager.get_current_theme()
        tree_widget = QTreeWidget()
        tree_widget.setHeaderLabel("规则结构")
        tree_widget.setStyleSheet(f"""
            QTreeWidget {{
                border: 1px solid {theme['card_border']};
                background-color: {theme['content_bg']};
                color: {theme['text_primary']};
                font-size: 12px;
            }}
            QTreeWidget::item {{
                padding: 2px;
            }}
            QTreeWidget::item:selected {{
                background-color: {theme['active_glow']};
                color: {theme['text_primary']};
            }}
        """)

        for i, rule in enumerate(rules):
            # 一级节点：规则索引
            rule_item = QTreeWidgetItem(tree_widget)
            rule_item.setText(0, f"[{i+1}] {rule['output_name']}")
            rule_item.setExpanded(False)

            # 二级节点：output_name
            name_item = QTreeWidgetItem(rule_item)
            name_item.setText(0, f"output_name: {rule['output_name']}")

            # 二级节点：keywords
            kw_item = QTreeWidgetItem(rule_item)
            kw_text = ', '.join(rule['keywords']) if rule['keywords'] else '(空)'
            kw_item.setText(0, f"keywords: [{kw_text}]")

            # 二级节点：field_mapping
            fm_item = QTreeWidgetItem(rule_item)
            fm_item.setText(0, "field_mapping:")
            field_mapping = rule.get('field_mapping', {})
            if field_mapping:
                for target, candidates in field_mapping.items():
                    # 三级节点：字段映射项
                    map_item = QTreeWidgetItem(fm_item)
                    cand_text = ', '.join(candidates) if candidates else '(空)'
                    map_item.setText(0, f"{target} → [{cand_text}]")
            else:
                empty_item = QTreeWidgetItem(fm_item)
                empty_item.setText(0, "(空)")

        splitter.addWidget(tree_widget)

        # 右侧：JSON预览
        json_widget = QPlainTextEdit()
        json_widget.setReadOnly(True)
        json_widget.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {theme['log_bg']}; color: {theme['log_text']};
                font-family: 'Consolas', 'Courier New', monospace; font-size: 12px;
                border: 1px solid {theme['card_border']};
            }}
        """)

        # 生成Python格式内容
        content = "rules = [\n"
        for i, rule in enumerate(rules):
            content += "    {\n"
            content += f'        "output_name": "{rule["output_name"]}",\n'
            content += f'        "keywords": {json.dumps(rule["keywords"], ensure_ascii=False)},\n'
            content += '        "field_mapping": {\n'
            for target, candidates in rule["field_mapping"].items():
                content += f'            "{target}": {json.dumps(candidates, ensure_ascii=False)},\n'
            content += "        }\n"
            content += "    }" + (",\n" if i < len(rules) - 1 else "\n")
        content += "]\n"
        json_widget.setPlainText(content)

        splitter.addWidget(json_widget)
        splitter.setSizes([300, 600])

        preview_layout.addWidget(splitter)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_btn = QPushButton("保存到文件")
        save_btn.setFixedHeight(38)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(_success_button_qss())

        def on_save():
            file_path, _ = QFileDialog.getSaveFileName(preview, "保存Rules格式", "rules_config.json", "JSON Files (*.json)")
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(rules, f, ensure_ascii=False, indent=4)

                    py_path = file_path.replace('.json', '.py')
                    with open(py_path, 'w', encoding='utf-8') as f:
                        f.write('# -*- coding: utf-8 -*-\n')
                        f.write('""" 字段映射规则配置 """\n\n')
                        f.write('rules = ')
                        f.write(json.dumps(rules, ensure_ascii=False, indent=4))

                    QMessageBox.information(preview, "成功", f"已保存:\nJSON: {file_path}\nPython: {py_path}")
                except Exception as e:
                    QMessageBox.warning(preview, "失败", f"保存失败: {e}")

        save_btn.clicked.connect(on_save)
        btn_layout.addWidget(save_btn)

        close_btn = QPushButton("关闭")
        close_btn.setFixedHeight(38)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(_secondary_button_qss())
        close_btn.clicked.connect(preview.reject)
        btn_layout.addWidget(close_btn)

        preview_layout.addLayout(btn_layout)

        preview.exec()

    def _save_and_close(self):
        unconfigured = [cfg['shp_name'] for cfg in self._shp_configs if not cfg.get('output_name')]
        if unconfigured:
            reply = QMessageBox.question(
                self, "提示",
                f"以下文件未配置输出图层:\n{', '.join(unconfigured)}\n\n是否继续保存？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        self.config_changed.emit()
        self.accept()

    def get_configs(self) -> list:
        return self._shp_configs