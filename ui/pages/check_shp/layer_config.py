# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QAbstractItemView
)
from PySide6.QtCore import Signal, Qt
from services.check_service import LAYER_TYPES


class CheckLayerConfig(QFrame):

    folder_selected = Signal(str)
    rescan_requested = Signal()
    layer_file_selected = Signal(str, str)
    start_clicked = Signal()
    clear_clicked = Signal()
    gis_map_clicked = Signal()
    export_clicked = Signal()
    log_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.layer_paths = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        self._build_folder_row(layout)
        self._build_layer_section(layout)
        self._build_action_row(layout)

    def _build_folder_row(self, parent_layout):
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(10)

        folder_label = QLabel("目标文件夹:")
        folder_label.setFixedWidth(100)
        folder_label.setObjectName("boldLabel")
        folder_layout.addWidget(folder_label, 0, Qt.AlignLeft)

        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("选择要检查的文件夹...")
        self.folder_edit.setReadOnly(True)
        import os
        default_folder = r"D:\github\空间数据检查桌面版\青海24示范小流域-药草沟-20260313\630121_大通"
        if os.path.exists(default_folder):
            self.folder_edit.setText(default_folder)
        folder_layout.addWidget(self.folder_edit, 1)

        rescan_btn = QPushButton("重新扫描")
        rescan_btn.setFixedWidth(80)
        rescan_btn.setObjectName("clearBtn")
        rescan_btn.clicked.connect(self.rescan_requested.emit)
        folder_layout.addWidget(rescan_btn, 0, Qt.AlignRight)

        folder_btn = QPushButton("浏览...")
        folder_btn.setFixedWidth(80)
        folder_btn.clicked.connect(self._on_browse)
        folder_layout.addWidget(folder_btn, 0, Qt.AlignRight)

        parent_layout.addLayout(folder_layout)

    def _build_layer_section(self, parent_layout):
        self._layer_collapsed = False
        collapse_header = QHBoxLayout()
        self._layer_collapse_btn = QPushButton("▼ SHP图层匹配清单")
        self._layer_collapse_btn.setObjectName("collapseSectionBtn")
        self._layer_collapse_btn.setFlat(True)
        self._layer_collapse_btn.setCursor(Qt.PointingHandCursor)
        self._layer_collapse_btn.clicked.connect(self._toggle_layer_section)
        collapse_header.addWidget(self._layer_collapse_btn)
        collapse_header.addStretch()
        parent_layout.addLayout(collapse_header)

        self.layer_table = QTableWidget()
        self.layer_table.setObjectName("layerTable")
        self.layer_table.setColumnCount(5)
        self.layer_table.setHorizontalHeaderLabels([
            "图层类型", "匹配状态", "SHP文件路径", "启用", "操作"
        ])
        self.layer_table.horizontalHeader().setStretchLastSection(False)
        self.layer_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.layer_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.layer_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.layer_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.layer_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.layer_table.setColumnWidth(0, 130)
        self.layer_table.setColumnWidth(3, 55)
        self.layer_table.setColumnWidth(4, 90)
        self.layer_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.layer_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.layer_table.setAlternatingRowColors(False)
        self.layer_table.verticalHeader().setVisible(False)
        self.layer_table.verticalHeader().setDefaultSectionSize(36)
        parent_layout.addWidget(self.layer_table)

        self._init_layer_table()

    def _build_action_row(self, parent_layout):
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        from core.effects_manager import ButtonGlowHelper

        self.start_btn = QPushButton("开始检查")
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.clicked.connect(self.start_clicked.emit)
        self.start_btn.setEnabled(False)
        ButtonGlowHelper.install(self.start_btn)
        btn_layout.addWidget(self.start_btn)

        self._add_separator(btn_layout)

        self.clear_btn = QPushButton("清空")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setObjectName("clearBtn")
        self.clear_btn.clicked.connect(self.clear_clicked.emit)
        btn_layout.addWidget(self.clear_btn)

        self._add_separator(btn_layout)

        self.gis_map_btn = QPushButton("打开GIS地图")
        self.gis_map_btn.setCursor(Qt.PointingHandCursor)
        self.gis_map_btn.setEnabled(False)
        self.gis_map_btn.clicked.connect(self.gis_map_clicked.emit)
        btn_layout.addWidget(self.gis_map_btn)

        self.export_btn = QPushButton("导出Excel")
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setObjectName("exportBtn")
        self.export_btn.clicked.connect(self.export_clicked.emit)
        self.export_btn.setEnabled(False)
        btn_layout.addWidget(self.export_btn)

        self._add_separator(btn_layout)

        self.log_btn = QPushButton("显示日志")
        self.log_btn.setCursor(Qt.PointingHandCursor)
        self.log_btn.setObjectName("logToggleBtn")
        self.log_btn.clicked.connect(self.log_clicked.emit)
        btn_layout.addWidget(self.log_btn)

        btn_layout.addStretch()
        parent_layout.addLayout(btn_layout)

    def _add_separator(self, layout):
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)

    def _toggle_layer_section(self):
        self._layer_collapsed = not self._layer_collapsed
        if self._layer_collapsed:
            self.layer_table.setVisible(False)
            self._layer_collapse_btn.setText("▶ SHP图层匹配清单")
        else:
            self.layer_table.setVisible(True)
            self._layer_collapse_btn.setText("▼ SHP图层匹配清单")

    def _init_layer_table(self):
        self.layer_table.setRowCount(len(LAYER_TYPES))
        row_height = self.layer_table.verticalHeader().defaultSectionSize()
        header_height = self.layer_table.horizontalHeader().height()
        self.layer_table.setFixedHeight(
            len(LAYER_TYPES) * row_height + header_height + 2
        )
        self.layer_checkboxes = {}
        self.layer_path_edits = {}
        self.layer_select_btns = {}

        for row, lt in enumerate(LAYER_TYPES):
            key = lt['key']
            name_item = QTableWidgetItem(lt['name'])
            name_item.setTextAlignment(Qt.AlignCenter)
            self.layer_table.setItem(row, 0, name_item)

            status_label = QLabel("未匹配")
            status_label.setObjectName("layerBadgeFail")
            status_label.setAlignment(Qt.AlignCenter)
            status_label.setFixedHeight(22)
            self.layer_table.setCellWidget(row, 1, status_label)

            path_edit = QLineEdit()
            path_edit.setReadOnly(True)
            path_edit.setPlaceholderText("未找到匹配文件...")
            path_edit.setObjectName("layerPathEdit")
            self.layer_table.setCellWidget(row, 2, path_edit)
            self.layer_path_edits[key] = path_edit

            checkbox = QCheckBox()
            checkbox.setChecked(True)
            self.layer_table.setCellWidget(row, 3, checkbox)
            self.layer_checkboxes[key] = checkbox

            select_btn = QPushButton("选择文件")
            select_btn.setFixedWidth(80)
            select_btn.clicked.connect(lambda checked, k=key: self.layer_file_selected.emit(k, ''))
            self.layer_table.setCellWidget(row, 4, select_btn)
            self.layer_select_btns[key] = select_btn

            self.layer_paths[key] = ''

    def _on_browse(self):
        from PySide6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.folder_edit.setText(folder)
            self.folder_selected.emit(folder)

    def get_folder_path(self) -> str:
        return self.folder_edit.text()

    def set_folder_path(self, path: str):
        self.folder_edit.setText(path)

    def update_layer_table(self, scan_result: dict):
        layers = scan_result.get('layers', {})
        for key, info in layers.items():
            path = info.get('path', '')
            matched = info.get('matched', False)
            self.layer_paths[key] = path

            if key in self.layer_path_edits:
                self.layer_path_edits[key].setText(path if matched else '')
                self.layer_path_edits[key].setPlaceholderText(
                    path if matched else '未找到匹配文件...'
                )

            if key in self.layer_checkboxes:
                self.layer_checkboxes[key].setChecked(matched)

            row = self._get_layer_row(key)
            if row is not None:
                status_label = self.layer_table.cellWidget(row, 1)
                if status_label:
                    if matched:
                        status_label.setText("已匹配")
                        status_label.setObjectName("layerBadgePass")
                    else:
                        status_label.setText("未匹配")
                        status_label.setObjectName("layerBadgeFail")
                    status_label.setStyle(status_label.style())

    def select_layer_file(self, layer_key: str, file_path: str):
        self.layer_paths[layer_key] = file_path
        if layer_key in self.layer_path_edits:
            self.layer_path_edits[layer_key].setText(file_path)

        row = self._get_layer_row(layer_key)
        if row is not None:
            status_label = self.layer_table.cellWidget(row, 1)
            if status_label:
                status_label.setText("已匹配")
                status_label.setObjectName("layerBadgePass")
                status_label.setStyle(status_label.style())

        if layer_key in self.layer_checkboxes:
            self.layer_checkboxes[layer_key].setChecked(True)

    def _get_layer_row(self, key: str):
        for row, lt in enumerate(LAYER_TYPES):
            if lt['key'] == key:
                return row
        return None

    def get_enabled_layer_paths(self) -> dict:
        result = {}
        for key, path in self.layer_paths.items():
            if path and key in self.layer_checkboxes and self.layer_checkboxes[key].isChecked():
                result[key] = path
        return result

    def get_water_shp(self):
        water_path = self.layer_paths.get('water', '')
        if water_path and self.layer_checkboxes.get('water', QCheckBox()).isChecked():
            return water_path
        return None

    def set_start_enabled(self, enabled: bool):
        self.start_btn.setEnabled(enabled)

    def set_export_enabled(self, enabled: bool):
        self.export_btn.setEnabled(enabled)

    def set_gis_map_enabled(self, enabled: bool):
        self.gis_map_btn.setEnabled(enabled)

    def update_start_button(self, has_folder: bool):
        self.start_btn.setEnabled(has_folder)

    def clear(self):
        self.folder_edit.clear()
        self.layer_paths = {}

        for key in self.layer_path_edits:
            self.layer_path_edits[key].setText('')
            self.layer_path_edits[key].setPlaceholderText('未找到匹配文件...')
            self.layer_checkboxes[key].setChecked(True)
            self.layer_paths[key] = ''

            row = self._get_layer_row(key)
            if row is not None:
                status_label = self.layer_table.cellWidget(row, 1)
                if status_label:
                    status_label.setText("未匹配")
                    status_label.setObjectName("layerBadgeFail")
                    status_label.setStyle(status_label.style())

        self.start_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.gis_map_btn.setEnabled(False)
