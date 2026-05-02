# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QProgressBar, QComboBox, QSpinBox, QSlider
)
from PySide6.QtCore import Signal, Qt
from core.theme_manager import get_theme_manager
from core.effects_manager import ShimmerProgress, ButtonGlowHelper


class GalleryToolbar(QFrame):

    browse_clicked = Signal()
    scan_clicked = Signal()
    match_clicked = Signal()
    select_all_clicked = Signal()
    deselect_all_clicked = Signal()
    expand_all_clicked = Signal()
    collapse_all_clicked = Signal()
    rename_clicked = Signal()
    gps_clicked = Signal()
    search_changed = Signal(str)
    type_filter_changed = Signal(int)
    zoom_changed = Signal(int)
    columns_changed = Signal(int)
    view_switched = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.theme_manager = get_theme_manager()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 12, 16, 12)

        self._build_folder_row(layout)
        self._build_progress(layout)
        self._build_action_row(layout)
        self._build_filter_row(layout)

    def _build_folder_row(self, parent_layout):
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(8)

        self.folder_edit = QLineEdit()
        self.folder_edit.setObjectName("filterEdit")
        self.folder_edit.setPlaceholderText("输入文件夹路径或点击浏览选择...")
        self.folder_edit.returnPressed.connect(self.scan_clicked.emit)
        folder_layout.addWidget(self.folder_edit, 1)

        self.browse_btn = QPushButton("浏览")
        self.browse_btn.setObjectName("toolbarBtn")
        self.browse_btn.clicked.connect(self.browse_clicked.emit)
        folder_layout.addWidget(self.browse_btn)

        self.scan_btn = QPushButton("扫描")
        self.scan_btn.setObjectName("toolbarBtnPrimary")
        self.scan_btn.clicked.connect(self.scan_clicked.emit)
        ButtonGlowHelper.install(self.scan_btn)
        folder_layout.addWidget(self.scan_btn)

        self.match_btn = QPushButton("附表校验")
        self.match_btn.setObjectName("toolbarBtn")
        self.match_btn.clicked.connect(self.match_clicked.emit)
        self.match_btn.setEnabled(False)
        folder_layout.addWidget(self.match_btn)

        parent_layout.addLayout(folder_layout)

    def _build_progress(self, parent_layout):
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(4)
        parent_layout.addWidget(self.progress_bar)
        self._progress_shimmer = ShimmerProgress(self.progress_bar)

    def _build_action_row(self, parent_layout):
        row = QHBoxLayout()
        row.setSpacing(6)

        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.setObjectName("toolbarBtn")
        self.select_all_btn.clicked.connect(self.select_all_clicked.emit)
        row.addWidget(self.select_all_btn)

        self.deselect_btn = QPushButton("取消")
        self.deselect_btn.setObjectName("toolbarBtn")
        self.deselect_btn.clicked.connect(self.deselect_all_clicked.emit)
        row.addWidget(self.deselect_btn)

        row.addWidget(self._create_separator())

        self.expand_all_btn = QPushButton("展开全部")
        self.expand_all_btn.setObjectName("toolbarBtn")
        self.expand_all_btn.clicked.connect(self.expand_all_clicked.emit)
        self.expand_all_btn.setEnabled(False)
        row.addWidget(self.expand_all_btn)

        self.collapse_all_btn = QPushButton("折叠全部")
        self.collapse_all_btn.setObjectName("toolbarBtn")
        self.collapse_all_btn.clicked.connect(self.collapse_all_clicked.emit)
        self.collapse_all_btn.setEnabled(False)
        row.addWidget(self.collapse_all_btn)

        row.addWidget(self._create_separator())

        self.rename_btn = QPushButton("重命名")
        self.rename_btn.setObjectName("toolbarBtn")
        self.rename_btn.clicked.connect(self.rename_clicked.emit)
        self.rename_btn.setEnabled(False)
        row.addWidget(self.rename_btn)

        row.addWidget(self._create_separator())

        self.gps_btn = QPushButton("显示GPS")
        self.gps_btn.setObjectName("toolbarBtn")
        self.gps_btn.clicked.connect(self.gps_clicked.emit)
        self.gps_btn.setEnabled(False)
        row.addWidget(self.gps_btn)

        row.addWidget(self._create_separator())

        self.selected_label = QLabel()
        row.addWidget(self.selected_label)

        row.addStretch()
        parent_layout.addLayout(row)

    def _build_filter_row(self, parent_layout):
        row = QHBoxLayout()
        row.setSpacing(8)

        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("filterEdit")
        self.search_edit.setPlaceholderText("搜索文件名...")
        self.search_edit.textChanged.connect(self.search_changed.emit)
        row.addWidget(self.search_edit, 1)

        self.filter_label = QLabel("类型:")
        row.addWidget(self.filter_label)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["全部", "照片", "视频"])
        self.type_combo.currentIndexChanged.connect(self.type_filter_changed.emit)
        row.addWidget(self.type_combo)

        row.addWidget(self._create_separator())

        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setObjectName("zoomSlider")
        self.zoom_slider.setRange(1, 10)
        self.zoom_slider.setValue(5)
        self.zoom_slider.setFixedWidth(80)
        self.zoom_slider.valueChanged.connect(self.zoom_changed.emit)
        row.addWidget(self.zoom_slider)

        self.zoom_label = QLabel("缩放 1.0x")
        self.zoom_label.setObjectName("toolbarSubtitle")
        row.addWidget(self.zoom_label)

        row.addWidget(self._create_separator())

        self.col_label = QLabel("列数:")
        self.col_label.setObjectName("toolbarSubtitle")
        row.addWidget(self.col_label)

        self.col_spin = QSpinBox()
        self.col_spin.setRange(2, 10)
        self.col_spin.setValue(4)
        self.col_spin.valueChanged.connect(self.columns_changed.emit)
        row.addWidget(self.col_spin)

        row.addWidget(self._create_separator())

        self.view_label = QLabel("视图:")
        self.view_label.setObjectName("toolbarSubtitle")
        row.addWidget(self.view_label)

        self.tree_btn = QPushButton("树形")
        self.tree_btn.setObjectName("photoViewBtn")
        self.tree_btn.setCheckable(True)
        self.tree_btn.setChecked(True)
        self.tree_btn.clicked.connect(lambda: self.view_switched.emit("tree"))
        row.addWidget(self.tree_btn)

        self.list_btn = QPushButton("列表")
        self.list_btn.setObjectName("photoViewBtn")
        self.list_btn.setCheckable(True)
        self.list_btn.clicked.connect(lambda: self.view_switched.emit("list"))
        row.addWidget(self.list_btn)

        self.map_btn = QPushButton("地图")
        self.map_btn.setObjectName("photoViewBtn")
        self.map_btn.setCheckable(True)
        self.map_btn.clicked.connect(lambda: self.view_switched.emit("map"))
        row.addWidget(self.map_btn)

        parent_layout.addLayout(row)

    def _create_separator(self) -> QFrame:
        theme = self.theme_manager.get_current_theme()
        sep = QFrame()
        sep.setStyleSheet(f"background: {theme.get('divider_color', '#e2e8f0')}; margin: 0 8px;")
        sep.setFixedWidth(1)
        sep.setFixedHeight(16)
        return sep

    def get_folder_path(self) -> str:
        return self.folder_edit.text().strip()

    def set_folder_path(self, path: str):
        self.folder_edit.setText(path)

    def set_scan_loading(self, loading: bool):
        self.scan_btn.setEnabled(not loading)
        if loading:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            self._progress_shimmer.start()
        else:
            self._progress_shimmer.stop()
            self.progress_bar.setVisible(False)

    def set_match_enabled(self, enabled: bool):
        self.match_btn.setEnabled(enabled)

    def set_expand_collapse_enabled(self, enabled: bool):
        self.expand_all_btn.setEnabled(enabled)
        self.collapse_all_btn.setEnabled(enabled)

    def set_gps_enabled(self, enabled: bool):
        self.gps_btn.setEnabled(enabled)

    def set_rename_enabled(self, enabled: bool):
        self.rename_btn.setEnabled(enabled)

    def update_selection_label(self, count: int):
        self.selected_label.setText(f"已选择 {count} 个" if count > 0 else "")

    def set_columns_enabled(self, enabled: bool):
        self.col_spin.setEnabled(enabled)

    def set_view_buttons(self, view: str):
        self.tree_btn.setChecked(view == "tree")
        self.list_btn.setChecked(view == "list")
        self.map_btn.setChecked(view == "map")
        self.col_spin.setEnabled(view == "tree")

    def update_zoom_label(self, scale: float):
        self.zoom_label.setText(f"缩放 {scale:.1f}x")
