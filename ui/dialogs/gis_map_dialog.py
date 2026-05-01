# -*- coding: utf-8 -*-
"""
GIS地图独立弹窗

功能：
- 独立窗口展示地图和属性表
- 自动加载检查相关的SHP文件
- 属性表查看、定位、编辑
- 全屏模式
"""

import os
import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QSplitter, QComboBox, QAbstractItemView, QMessageBox,
    QFileDialog
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QIcon, QPixmap

from ui.components.gis_map_widget import GisMapWidget, HAS_WEB_ENGINE
from ui.dialogs.feature_edit_dialog import FeatureEditDialog
from .tianditu_config_dialog import TiandituConfigDialog
from core.theme_manager import get_theme_manager


class GisMapDialog(QDialog):
    """GIS地图独立弹窗"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._map_edit_mode = False
        self.setWindowTitle("GIS 地图视图")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        # 设置焦点策略，确保能接收键盘事件
        self.setFocusPolicy(Qt.StrongFocus)
        if HAS_WEB_ENGINE:
            self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.theme_manager = get_theme_manager()
        theme = self.theme_manager.get_current_theme()
        text_color = theme.get('text_primary', '#374151')
        text_secondary = theme.get('text_secondary', '#6b7280')
        border_color = theme.get('input_border', '#d1d5db')
        card_bg = theme.get('card_bg', 'rgba(243,244,246,0.95)')
        hover_bg = theme.get('hover_glow', 'rgba(99,102,241,0.15)')
        accent_color = theme.get('accent_color', '#6366f1')

        toolbar = QFrame()
        toolbar.setObjectName("card")
        toolbar.setStyleSheet("QFrame#card { background: rgba(255,255,255,0.95); border-bottom: 1px solid #e5e7eb; }")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setSpacing(6)
        toolbar_layout.setContentsMargins(8, 4, 8, 4)

        title_label = QLabel("GIS")
        title_label.setStyleSheet("font-size: 12px; color: #6366f1; font-weight: bold;")
        toolbar_layout.addWidget(title_label)
        toolbar_layout.addSpacing(8)

        if getattr(sys, 'frozen', False):
            gis_base = os.path.join(sys._MEIPASS, 'resources', 'gis')
        else:
            gis_base = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'gis')
        spritesheet_png = os.path.join(gis_base, 'images', 'spritesheet.png')

        def create_icon(x_offset, y_offset=0, width=30, height=30):
            full_pixmap = QPixmap(spritesheet_png)
            if full_pixmap.isNull():
                return QIcon()
            icon_pixmap = full_pixmap.copy(x_offset, y_offset, width, height)
            return QIcon(icon_pixmap)

        icon_btn_style = f"""
            QPushButton {{
                padding: 0px;
                border: none;
                border-radius: 3px;
                background: transparent;
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
                color: {text_color};
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
            }}
            QPushButton:checked {{
                background-color: {accent_color};
                color: white;
            }}
        """

        text_btn_style = f"QPushButton {{ padding: 3px 4px; font-size: 12px; border: none; border-radius: 2px; background: transparent; min-width: 32px; color: {text_color}; }} QPushButton:hover {{ background: {accent_color}; color: white; }} QPushButton:checked {{ background: {accent_color}; color: white; }}"

        combo_style = f"QComboBox {{ padding: 2px 4px; font-size: 11px; border: 1px solid {border_color}; border-radius: 4px; min-width: 80px; max-width: 120px; color: {text_color}; }} QComboBox:hover {{ border-color: {accent_color}; }}"

        self.target_layer_combo = QComboBox()
        self.target_layer_combo.setStyleSheet(combo_style)
        self.target_layer_combo.addItem("新建图层", "drawn")
        self.target_layer_combo.setToolTip("选择要添加要素的目标图层")
        self.target_layer_combo.currentIndexChanged.connect(self._on_target_layer_changed)

        self.map_load_shp_btn = QPushButton("加载")
        self.map_load_shp_btn.setStyleSheet(text_btn_style)
        self.map_load_shp_btn.clicked.connect(self._on_load_shp)

        self.map_load_check_btn = QPushButton("检查")
        self.map_load_check_btn.setStyleSheet(text_btn_style)
        self.map_load_check_btn.setEnabled(False)
        self.map_load_check_btn.clicked.connect(self._on_load_check_results)

        self.map_fit_btn = QPushButton("适应")
        self.map_fit_btn.setStyleSheet(text_btn_style)
        self.map_fit_btn.clicked.connect(lambda: self.gis_map.fit_bounds())

        self.map_clear_btn = QPushButton("清除")
        self.map_clear_btn.setStyleSheet(text_btn_style)
        self.map_clear_btn.clicked.connect(self._on_clear)

        self.map_edit_btn = QPushButton("编辑")
        self.map_edit_btn.setStyleSheet(text_btn_style)
        self.map_edit_btn.setCheckable(True)
        self.map_edit_btn.clicked.connect(self._on_toggle_edit_mode)

        self.draw_point_btn = QPushButton()
        self.draw_point_btn.setStyleSheet(icon_btn_style)
        self.draw_point_btn.setIcon(create_icon(120, 0, 30, 30))
        self.draw_point_btn.setIconSize(QSize(24, 24))
        self.draw_point_btn.setToolTip("绘制点")
        self.draw_point_btn.clicked.connect(lambda: self.gis_map._run_js('startDrawPoint();'))

        self.draw_line_btn = QPushButton()
        self.draw_line_btn.setStyleSheet(icon_btn_style)
        self.draw_line_btn.setIcon(create_icon(0, 0, 30, 30))
        self.draw_line_btn.setIconSize(QSize(24, 24))
        self.draw_line_btn.setToolTip("绘制线")
        self.draw_line_btn.clicked.connect(lambda: self.gis_map._run_js('startDrawLine();'))

        self.draw_polygon_btn = QPushButton()
        self.draw_polygon_btn.setStyleSheet(icon_btn_style)
        self.draw_polygon_btn.setIcon(create_icon(30, 0, 30, 30))
        self.draw_polygon_btn.setIconSize(QSize(24, 24))
        self.draw_polygon_btn.setToolTip("绘制面")
        self.draw_polygon_btn.clicked.connect(lambda: self.gis_map._run_js('startDrawPolygon();'))

        self.edit_geom_btn = QPushButton()
        self.edit_geom_btn.setStyleSheet(icon_btn_style)
        self.edit_geom_btn.setIcon(create_icon(150, 0, 30, 30))
        self.edit_geom_btn.setIconSize(QSize(24, 24))
        self.edit_geom_btn.setToolTip("编辑几何")
        self.edit_geom_btn.clicked.connect(lambda: self.gis_map._run_js('toggleEditGeometry();'))

        self.delete_draw_btn = QPushButton()
        self.delete_draw_btn.setStyleSheet(icon_btn_style)
        self.delete_draw_btn.setIcon(create_icon(180, 0, 30, 30))
        self.delete_draw_btn.setIconSize(QSize(24, 24))
        self.delete_draw_btn.setToolTip("删除选中要素")
        self.delete_draw_btn.clicked.connect(lambda: self.gis_map._run_js('deleteSelectedDrawnFeature();'))

        self.stop_draw_btn = QPushButton("取消")
        self.stop_draw_btn.setStyleSheet(text_btn_style)
        self.stop_draw_btn.clicked.connect(lambda: self.gis_map._run_js('stopDraw();'))

        self.save_draw_btn = QPushButton("保存")
        self.save_draw_btn.setStyleSheet(text_btn_style)
        self.save_draw_btn.setToolTip("保存绘制要素到SHP文件（当前存储在'绘制要素'临时图层）")
        self.save_draw_btn.clicked.connect(self._on_save_features)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"font-size: 11px; color: {text_secondary};")

        self.fullscreen_btn = QPushButton("全屏")
        self.fullscreen_btn.setStyleSheet(text_btn_style)
        self.fullscreen_btn.setCheckable(True)
        self.fullscreen_btn.clicked.connect(self._on_toggle_fullscreen)

        self.tianditu_config_btn = QPushButton("设置")
        self.tianditu_config_btn.setStyleSheet(text_btn_style)
        self.tianditu_config_btn.setToolTip("配置天地图API Key")
        self.tianditu_config_btn.clicked.connect(self._on_tianditu_config)

        # 按钮容器 - 带背景框
        btn_container = QFrame()
        btn_container.setStyleSheet("QFrame { background: rgba(243,244,246,0.95); border-radius: 4px; }")
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(2, 1, 2, 1)
        btn_layout.setSpacing(1)

        btn_layout.addWidget(self.map_load_shp_btn)
        btn_layout.addWidget(self.map_load_check_btn)
        btn_layout.addWidget(self.map_fit_btn)
        btn_layout.addWidget(self.map_clear_btn)
        btn_layout.addWidget(self.map_edit_btn)
        btn_layout.addWidget(self.target_layer_combo)
        btn_layout.addWidget(self.draw_point_btn)
        btn_layout.addWidget(self.draw_line_btn)
        btn_layout.addWidget(self.draw_polygon_btn)
        btn_layout.addWidget(self.edit_geom_btn)
        btn_layout.addWidget(self.delete_draw_btn)
        btn_layout.addWidget(self.stop_draw_btn)
        btn_layout.addWidget(self.save_draw_btn)

        toolbar_layout.addWidget(btn_container)
        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self.status_label)

        # 全屏按钮单独一组 - 带背景框
        fullscreen_container = QFrame()
        fullscreen_container.setStyleSheet("QFrame { background: rgba(243,244,246,0.95); border-radius: 4px; }")
        fullscreen_layout = QHBoxLayout(fullscreen_container)
        fullscreen_layout.setContentsMargins(2, 1, 2, 1)
        fullscreen_layout.setSpacing(1)
        fullscreen_layout.addWidget(self.tianditu_config_btn)
        fullscreen_layout.addWidget(self.fullscreen_btn)
        toolbar_layout.addWidget(fullscreen_container)

        self._toolbar = toolbar
        layout.addWidget(toolbar)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(3)
        splitter.setStyleSheet("QSplitter::handle { background: #d1d5db; }")

        self.gis_map = GisMapWidget()
        self.gis_map.setMinimumHeight(300)
        self.gis_map.layer_loaded.connect(self._on_layer_loaded)
        self.gis_map.feature_clicked.connect(self._on_feature_clicked)
        self.gis_map.map_error.connect(self._on_map_error)
        splitter.addWidget(self.gis_map)

        attr_panel = self._setup_attribute_panel()
        splitter.addWidget(attr_panel)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([500, 200])

        self._splitter = splitter
        layout.addWidget(splitter, 1)
        
        # 创建全屏模式下的浮动退出按钮
        self._exit_fullscreen_btn = QPushButton("× 退出全屏")
        self._exit_fullscreen_btn.setFixedSize(100, 32)
        self._exit_fullscreen_btn.setStyleSheet("QPushButton { background: rgba(99,102,241,0.9); color: white; border: none; border-radius: 6px; font-size: 13px; } QPushButton:hover { background: rgba(99,102,241,1); }")
        self._exit_fullscreen_btn.clicked.connect(lambda: self._on_toggle_fullscreen(False))
        self._exit_fullscreen_btn.setParent(self.gis_map)
        self._exit_fullscreen_btn.hide()  # 默认隐藏，位置在resize事件中动态设置

    def _setup_attribute_panel(self):
        panel = QFrame()
        panel.setObjectName("card")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        theme = self.theme_manager.get_current_theme()
        text_color = theme.get('text_primary', '#374151')
        text_secondary = theme.get('text_secondary', '#6b7280')
        border_color = theme.get('input_border', '#d1d5db')
        card_bg = theme.get('card_bg', 'rgba(243,244,246,0.95)')
        header_bg = theme.get('card_bg', 'rgba(255,255,255,0.95)')
        accent_color = theme.get('accent_color', '#6366f1')

        header = QFrame()
        header.setStyleSheet(f"background: {header_bg}; border-bottom: 1px solid {border_color}; ")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 4, 8, 4)
        header_layout.setSpacing(6)

        attr_title = QLabel("属性")
        attr_title.setStyleSheet(f"font-size: 12px; color: {accent_color}; font-weight: bold; margin-right: 8px; ")
        header_layout.addWidget(attr_title)

        self.layer_label = QLabel("图层:")
        self.layer_label.setStyleSheet(f"font-size: 11px; color: {text_secondary}; ")
        header_layout.addWidget(self.layer_label)
        self.attr_layer_combo = QComboBox()
        self.attr_layer_combo.setStyleSheet(f"QComboBox {{ padding: 3px 6px; font-size: 11px; border: 1px solid {border_color}; border-radius: 4px; min-width: 80px; color: {text_color}; }}")
        self.attr_layer_combo.currentTextChanged.connect(self._on_attr_layer_changed)
        header_layout.addWidget(self.attr_layer_combo)

        attr_btn_style = f"QPushButton {{ padding: 4px 0px; font-size: 12px; border: none; border-radius: 3px; background: transparent; min-width: 36px; color: {text_color}; }} QPushButton:hover {{ background: {accent_color}; color: white; }}"
        danger_btn_style = f"QPushButton {{ padding: 4px 0px; font-size: 12px; border: none; border-radius: 3px; background: transparent; min-width: 36px; color: {text_color}; }} QPushButton:hover {{ background: #ef4444; color: white; }}"
        
        self.attr_btn_container = QFrame()
        self.attr_btn_container.setStyleSheet(f"QFrame {{ background: {card_bg}; border-radius: 6px; padding: 2px; }}")
        attr_btn_layout = QHBoxLayout(self.attr_btn_container)
        attr_btn_layout.setContentsMargins(4, 2, 4, 2)
        attr_btn_layout.setSpacing(2)
        
        self.attr_locate_btn = QPushButton("定位")
        self.attr_locate_btn.setStyleSheet(attr_btn_style)
        self.attr_locate_btn.clicked.connect(self._on_attr_locate)
        attr_btn_layout.addWidget(self.attr_locate_btn)
        
        self.attr_edit_btn = QPushButton("编辑")
        self.attr_edit_btn.setStyleSheet(attr_btn_style)
        self.attr_edit_btn.clicked.connect(self._on_attr_edit)
        attr_btn_layout.addWidget(self.attr_edit_btn)
        
        self.attr_delete_btn = QPushButton("删除")
        self.attr_delete_btn.setStyleSheet(danger_btn_style)
        self.attr_delete_btn.clicked.connect(self._on_attr_delete)
        attr_btn_layout.addWidget(self.attr_delete_btn)
        
        header_layout.addWidget(self.attr_btn_container)

        header_layout.addStretch()

        self.attr_collapse_btn = QPushButton("折叠")
        self.attr_collapse_btn.setStyleSheet(attr_btn_style)
        self.attr_collapse_btn.clicked.connect(self._on_attr_collapse)
        header_layout.addWidget(self.attr_collapse_btn)

        panel_layout.addWidget(header)

        self.attr_table = QTableWidget()
        self.attr_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.attr_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.attr_table.setAlternatingRowColors(False)
        self.attr_table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.attr_table.horizontalHeader().setStretchLastSection(False)
        self.attr_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.attr_table.verticalHeader().setDefaultSectionSize(24)
        self.attr_table.verticalHeader().setMinimumSectionSize(20)
        self.attr_table.currentCellChanged.connect(self._on_attr_row_changed)
        panel_layout.addWidget(self.attr_table)

        self._attr_panel = panel
        return panel

    def load_shp_from_check(self, folder_path: str, water_shp_path: str, check_results: dict = None):
        """从检查结果加载SHP文件（委托给service处理）"""
        self._folder_path = folder_path
        self._water_shp_path = water_shp_path
        self._check_results = check_results or {}

        try:
            loaded_count = self.gis_map.service.batch_load_shp_from_folder(folder_path, water_shp_path)

            if loaded_count > 0:
                for layer_id in list(self.gis_map.service.loaded_layers.keys()):
                    layer_meta = self.gis_map.service.get_layer(layer_id)
                    if layer_meta:
                        self.gis_map.load_geojson(layer_id, layer_meta['geojson'], layer_meta['color'])

                QTimer.singleShot(500, self.gis_map.fit_bounds)
                self.status_label.setText(f"已加载 {loaded_count} 个图层")
            else:
                self.status_label.setText("未找到可加载的SHP文件")

            if check_results:
                self.map_load_check_btn.setEnabled(True)

        except Exception as e:
            self.status_label.setText(f"加载失败: {str(e)[:50]}")

    def _on_load_shp(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "选择SHP文件", "", "Shp Files (*.shp)"
        )
        if file:
            self.gis_map.load_shp_file(file)

    def _on_load_check_results(self):
        """加载检查结果图层（委托给service）"""
        if not self._check_results:
            QMessageBox.warning(self, "警告", "没有可加载的检查结果")
            return

        results = self._check_results.get('results', [])
        try:
            loaded = self.gis_map.service.batch_load_check_results(results)

            if loaded > 0:
                for layer_id in list(self.gis_map.service.loaded_layers.keys()):
                    layer_meta = self.gis_map.service.get_layer(layer_id)
                    if layer_meta and layer_id in ['duanmian', 'fangzhi', 'yinhuan']:
                        self.gis_map.load_geojson(layer_id, layer_meta['geojson'], layer_meta['color'])

                self.gis_map.fit_bounds()
                self.status_label.setText(f"已加载 {loaded} 个检查图层")
            else:
                self.status_label.setText("未找到可加载的检查数据")
        except Exception as e:
            self.status_label.setText(f"加载失败: {str(e)[:50]}")

    def _on_clear(self):
        """清除所有图层（UI+service同步）"""
        self.gis_map.clear_all()
        self.status_label.setText("")
        self.attr_table.setRowCount(0)
        self.attr_layer_combo.clear()

    def _on_tianditu_config(self):
        dialog = TiandituConfigDialog(self)
        result = dialog.exec()
        if result == QDialog.Accepted:
            QMessageBox.information(
                self, "提示",
                "天地图API Key已更新。\n请关闭当前地图窗口后重新打开，新配置才会生效。"
            )

    def _on_toggle_fullscreen(self, checked=None):
        if checked is None:
            checked = not self.fullscreen_btn.isChecked()
            self.fullscreen_btn.setChecked(checked)
        if checked:
            self._toolbar.hide()
            self._splitter.widget(1).hide()
            self.fullscreen_btn.setText("退出全屏")
            self._update_exit_btn_position()
            self._exit_fullscreen_btn.show()
            self._exit_fullscreen_btn.raise_()
        else:
            self._toolbar.show()
            self._splitter.widget(1).show()
            self.fullscreen_btn.setText("全屏")
            self._exit_fullscreen_btn.hide()
        QTimer.singleShot(100, self.gis_map.fit_bounds)

    def _update_exit_btn_position(self):
        btn_width = self._exit_fullscreen_btn.width()
        btn_height = self._exit_fullscreen_btn.height()
        margin_right = 210
        margin_top = 10
        x = self.gis_map.width() - margin_right - btn_width
        y = margin_top
        self._exit_fullscreen_btn.move(x, y)

    def _on_toggle_edit_mode(self, checked: bool):
        self._map_edit_mode = checked
        self.gis_map._run_js(f'setEditMode({str(checked).lower()});')
        if checked:
            self.map_edit_btn.setText("退出编辑")
            self.status_label.setText("编辑模式 - 点击要素编辑属性")
        else:
            self.map_edit_btn.setText("编辑模式")
            self.status_label.setText("")

    def _on_layer_loaded(self, layer_id: str, feature_count: int):
        """图层加载完成回调"""
        from services.gis_map_service import GisMapService
        name = GisMapService.LAYER_NAMES.get(layer_id, layer_id)
        self._refresh_attr_combo()
        self._refresh_target_layer_combo()

    def _refresh_target_layer_combo(self):
        """刷新目标图层下拉框"""
        self.target_layer_combo.blockSignals(True)
        current_data = self.target_layer_combo.currentData()
        self.target_layer_combo.clear()
        self.target_layer_combo.addItem("新建图层", "drawn")
        for lid, data in self.gis_map.service.loaded_layers.items():
            if lid == 'drawn':
                continue
            name = data.get('name', lid)
            geojson = data.get('geojson', {})
            features = geojson.get('features', [])
            if features:
                geom_type = features[0].get('geometry', {}).get('type', 'Unknown')
                if geom_type.startswith('Multi'):
                    geom_type = geom_type.replace('Multi', '')
                self.target_layer_combo.addItem(f"{name} ({geom_type})", lid)
        idx = self.target_layer_combo.findData(current_data)
        if idx >= 0:
            self.target_layer_combo.setCurrentIndex(idx)
        self.target_layer_combo.blockSignals(False)
        self._on_target_layer_changed(self.target_layer_combo.currentIndex())

    def _on_target_layer_changed(self, index: int):
        """目标图层切换事件"""
        layer_id = self.target_layer_combo.currentData()
        if layer_id == 'drawn':
            self.gis_map._run_js('setTargetLayer(null);')
            self.status_label.setText("绘制要素将保存到新建图层")
        else:
            layer_data = self.gis_map.service.get_layer(layer_id)
            if layer_data:
                geojson = layer_data.get('geojson', {})
                features = geojson.get('features', [])
                if features:
                    geom_type = features[0].get('geometry', {}).get('type', 'Unknown')
                    if geom_type.startswith('Multi'):
                        geom_type = geom_type.replace('Multi', '')
                    self.gis_map._run_js(f'setTargetLayer("{layer_id}", "{geom_type}");')
                    self.status_label.setText(f"绘制要素将添加到: {layer_data.get('name', layer_id)}")

    def _refresh_attr_combo(self):
        """刷新图层下拉框（使用service数据）"""
        self.attr_layer_combo.blockSignals(True)
        current = self.attr_layer_combo.currentText()
        self.attr_layer_combo.clear()
        for lid, data in self.gis_map.service.loaded_layers.items():
            name = data.get('name', lid)
            count = len(data.get('geojson', {}).get('features', []))
            self.attr_layer_combo.addItem(f"{name} ({count})", lid)
        idx = self.attr_layer_combo.findText(current)
        if idx >= 0:
            self.attr_layer_combo.setCurrentIndex(idx)
        self.attr_layer_combo.blockSignals(False)
        if self.attr_layer_combo.count() > 0:
            self._on_attr_layer_changed(self.attr_layer_combo.currentText())

    def _on_attr_layer_changed(self, text):
        """图层切换事件（使用service获取数据）"""
        layer_id = self.attr_layer_combo.currentData()
        all_keys, features = self.gis_map.service.get_layer_features_for_table(layer_id)

        if not all_keys or not features:
            self.attr_table.setRowCount(0)
            return

        skip_keys = {'_original_columns', '_status', 'geometry'}

        self.attr_table.setColumnCount(len(all_keys))
        self.attr_table.setHorizontalHeaderLabels(all_keys)
        self.attr_table.setRowCount(len(features))
        for row, f in enumerate(features):
            props = f.get('properties', {})
            for col, key in enumerate(all_keys):
                val = str(props.get(key, ''))
                item = QTableWidgetItem(val)
                item.setData(Qt.UserRole, f.get('id'))
                self.attr_table.setItem(row, col, item)

    def _on_attr_row_changed(self, row, col, prev_row, prev_col):
        """属性表行切换事件（使用service）"""
        if row < 0:
            return
        layer_id = self.attr_layer_combo.currentData()
        feature = self.gis_map.service.find_feature_by_row(layer_id, row)
        if feature:
            self.gis_map._run_js(f'highlightFeature("{layer_id}", {feature.get("id", 0)});')

    def _on_attr_locate(self):
        """定位要素（使用service）"""
        row = self.attr_table.currentRow()
        if row < 0:
            return
        layer_id = self.attr_layer_combo.currentData()
        feature = self.gis_map.service.find_feature_by_row(layer_id, row)
        if feature:
            self.gis_map._run_js(f'locateFeature("{layer_id}", {feature.get("id", 0)});')

    def _on_attr_edit(self):
        """编辑要素属性（使用service）"""
        row = self.attr_table.currentRow()
        if row < 0:
            return
        layer_id = self.attr_layer_combo.currentData()
        feature = self.gis_map.service.find_feature_by_row(layer_id, row)
        if feature:
            props = dict(feature.get('properties', {}))
            props['id'] = feature.get('id')
            dialog = FeatureEditDialog(layer_id, props, self)
            dialog.properties_updated.connect(
                lambda p: self._on_properties_updated(layer_id, p, row)
            )
            dialog.exec()

    def _on_attr_collapse(self):
        if self.attr_table.isVisible():
            self.attr_table.hide()
            self.attr_btn_container.hide()
            self.attr_layer_combo.hide()
            self.layer_label.hide()
            self.attr_collapse_btn.setText("展开")
            self._splitter.setSizes([self.height() - 40, 40])
        else:
            self.attr_table.show()
            self.attr_btn_container.show()
            self.attr_layer_combo.show()
            self.layer_label.show()
            self.attr_collapse_btn.setText("折叠")
            self._splitter.setSizes([int(self.height() * 0.75), int(self.height() * 0.25)])

    def _on_attr_delete(self):
        """删除要素（使用service）"""
        row = self.attr_table.currentRow()
        if row < 0:
            return
        layer_id = self.attr_layer_combo.currentData()
        feature = self.gis_map.service.find_feature_by_row(layer_id, row)
        if not feature:
            return

        feature_id = feature.get('id')
        reply = QMessageBox.question(
            self, '确认删除',
            f'确定要删除该要素吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.gis_map.delete_feature(layer_id, feature_id)
            self._on_attr_layer_changed(self.attr_layer_combo.currentText())

    def _on_feature_clicked(self, layer_id: str, properties: dict, coords):
        """要素点击事件处理"""
        from services.gis_map_service import GisMapService
        name = GisMapService.LAYER_NAMES.get(layer_id, layer_id)
        code = properties.get('河流代码', '')
        feature_name = properties.get('河流名称', properties.get('名称', ''))
        status = properties.get('验证状态', properties.get('_status', ''))

        if self._map_edit_mode:
            dialog = FeatureEditDialog(layer_id, properties, self)
            dialog.properties_updated.connect(
                lambda p: self._on_properties_updated(layer_id, p)
            )
            dialog.exec()
        else:
            feature_id = properties.get('id')
            if feature_id is not None:
                for row in range(self.attr_table.rowCount()):
                    item = self.attr_table.item(row, 0)
                    if item and item.data(Qt.UserRole) == feature_id:
                        self.attr_table.selectRow(row)
                        self.attr_table.scrollTo(
                            self.attr_table.model().index(row, 0)
                        )
                        break

    def _on_properties_updated(self, layer_id: str, updated_props: dict, row=None):
        self.gis_map.update_feature_properties(layer_id, updated_props)
        if row is not None:
            self._on_attr_layer_changed(self.attr_layer_combo.currentText())

    def _on_map_error(self, error_msg: str):
        self.status_label.setText(f"错误: {error_msg[:50]}")

    def _on_save_features(self):
        """保存要素 - 根据目标图层选择保存方式"""
        target_layer_id = self.target_layer_combo.currentData()
        
        if target_layer_id == 'drawn':
            self._on_save_drawn_features()
        else:
            self._on_save_layer_features(target_layer_id)

    def _on_save_layer_features(self, layer_id: str):
        """保存图层要素到原SHP文件"""
        layer_data = self.gis_map.service.get_layer(layer_id)
        if not layer_data:
            QMessageBox.warning(self, "警告", "图层数据不存在")
            return
        
        file_path = layer_data.get('file_path')
        if not file_path:
            new_path, _ = QFileDialog.getSaveFileName(
                self, f"保存图层: {layer_data.get('name', layer_id)}",
                f"{layer_id}.shp", "Shapefile (*.shp)"
            )
            if not new_path:
                return
            file_path = new_path
        
        geojson = layer_data.get('geojson', {})
        features = geojson.get('features', [])
        feature_count = len(features)
        
        reply = QMessageBox.question(
            self, '确认保存',
            f'确定要将 {feature_count} 个要素保存到:\n{file_path}\n\n这将覆盖原文件！',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            success = self.gis_map.service.save_layer_to_shp(layer_id, file_path)
            if success:
                self.status_label.setText(f"已保存 {feature_count} 个要素到: {os.path.basename(file_path)}")
                QMessageBox.information(self, "成功", f"图层已保存到:\n{file_path}\n\n包含 {feature_count} 个要素")
            else:
                QMessageBox.warning(self, "警告", "保存失败")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", str(e))

    def _on_save_drawn_features(self):
        """保存绘制的要素到SHP文件（委托给service）"""
        drawn_features = self.gis_map.service.get_drawn_features()
        if not drawn_features:
            QMessageBox.warning(self, "警告", "没有绘制的要素可保存\n\n请先使用点、线、面按钮绘制要素")
            return

        feature_count = len(drawn_features)
        feature_types = {}
        for f in drawn_features:
            geom_type = f.get('geometry', {}).get('type', 'Unknown')
            if geom_type.startswith('Multi'):
                geom_type = geom_type.replace('Multi', '')
            feature_types[geom_type] = feature_types.get(geom_type, 0) + 1
        
        type_summary = ', '.join([f"{t}: {c}" for t, c in feature_types.items()])
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, f"保存绘制要素 ({feature_count}个: {type_summary})", 
            "drawn_features.shp", "Shapefile (*.shp)"
        )
        if not file_path:
            return

        try:
            result = self.gis_map.service.save_drawn_features_to_shp(file_path)
            if not result:
                QMessageBox.warning(self, "警告", "保存失败")
                return

            saved_files = result.get('files', [])
            type_counts = {k: v for k, v in result.items() if k != 'files'}
            
            if len(saved_files) > 1:
                file_list = '\n'.join([os.path.basename(f) for f in saved_files])
                self.status_label.setText(f"已保存 {len(saved_files)} 个文件")
                QMessageBox.information(self, "成功", 
                    f"由于 Shapefile 只能存储单一几何类型，已按类型分别保存:\n\n{file_list}\n\n"
                    f"统计: {type_summary}")
            else:
                self.status_label.setText(f"已保存 {feature_count} 个要素到: {os.path.basename(saved_files[0])}")
                QMessageBox.information(self, "成功", 
                    f"绘制要素已保存到:\n{saved_files[0]}\n\n包含 {feature_count} 个要素 ({type_summary})")

        except Exception as e:
            QMessageBox.warning(self, "保存失败", str(e))

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(200, self.gis_map.fit_bounds)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._exit_fullscreen_btn.isVisible():
            self._update_exit_btn_position()

    def keyPressEvent(self, event):
        """按键事件处理 - ESC键退出全屏"""
        if event.key() == Qt.Key_Escape:
            # 如果当前是全屏模式，退出全屏
            if self.fullscreen_btn.isChecked():
                self._on_toggle_fullscreen(False)
                event.accept()
                return
        super().keyPressEvent(event)
