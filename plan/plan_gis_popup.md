# GIS地图弹出页面改造计划

## 目标
将 GIS 地图从 CheckPage 的 Tab 页面中移出，改为独立的弹出对话框（QDialog），在"开始检查"按钮旁新增"打开GIS地图"按钮，打开后自动加载已选择的 SHP 文件图层。

---

## 一、涉及文件及变更概览

| 文件 | 操作 | 说明 |
|------|------|------|
| `ui/dialogs/gis_map_dialog.py` | **新建** | GIS 地图独立弹窗（QDialog） |
| `ui/pages/check_page.py` | 修改 | 移除 map_tab，添加"打开GIS地图"按钮 |
| `ui/components/gis_map_widget.py` | 不变 | 保持现有接口 |
| `ui/components/ant_menu.py` | 不变 | 已移除 GIS 地图菜单项 |
| `main_window.py` | 不变 | 无需改动 |

---

## 二、详细步骤

### 步骤1：新建 `ui/dialogs/gis_map_dialog.py`

创建独立的 QDialog 类 `GisMapDialog`：

```
GisMapDialog(QDialog)
├── 布局：
│   ├── 顶部工具栏 QFrame(card)
│   │   ├── "GIS地图" 标题
│   │   ├── 加载SHP / 加载检查结果 / 适应范围 / 清除图层 / 编辑模式 按钮
│   │   └── 状态标签
│   ├── 中间 QSplitter(Vertical)
│   │   ├── GisMapWidget (stretch=3)
│   │   └── 属性表面板 (stretch=1) — 图层下拉框 + 定位/编辑 + 属性表
│   └── 底部栏 — 全屏按钮
│
├── 公开方法：
│   ├── load_shp_from_check(folder_path, water_shp_path, results) — 自动加载所有图层
│   ├── load_shp_file(shp_path) — 单独加载SHP
│   └── fit_bounds() — 适应范围
│
└── 设计要点：
    ├── 尺寸: setMinimumSize(1000, 700)，居中显示
    ├── 非模态: 允许同时操作主界面
    ├── 关闭不清空: 下次打开可继续使用
    └── 全屏在 Dialog 内部处理: 隐藏 toolbar + 属性面板
```

内部逻辑从 CheckPage 迁移：
- `_setup_attribute_panel()` → GisMapDialog 内部方法
- `_on_attr_layer_changed()`, `_on_attr_locate()`, `_on_attr_edit()`, `_on_attr_row_changed()`, `_refresh_attr_layer_combo()` → 全部迁移
- `_on_map_feature_clicked()`, `_on_map_toggle_edit_mode()`, `_on_map_toggle_fullscreen()`, `_on_properties_updated()` → 全部迁移
- 编辑模式点击要素 → 弹出 FeatureEditDialog

### 步骤2：修改 `check_page.py`

**2.1 删除内容：**
- `_init_ui()` 中地图 Tab 添加代码（L272-275）
- `_setup_map_tab()` 方法（L414-499）
- `_setup_attribute_panel()` 方法（L501-548）
- 所有 `_on_map_*` 回调方法（~L1120-1357）
- `_map_edit_mode` 实例变量
- `navigate_to()` 中 `"check_map": 5` 映射

**2.2 在"开始检查"按钮后添加新按钮：**
```python
self.gis_map_btn = QPushButton("🗺️ 打开GIS地图")
self.gis_map_btn.setFixedWidth(130)
self.gis_map_btn.setEnabled(False)  # 选了文件夹和水系后可用
self.gis_map_btn.clicked.connect(self._open_gis_map_dialog)
btn_layout.addWidget(self.gis_map_btn)  # 紧跟 start_btn 之后
```

**2.3 新增回调：**
```python
def _open_gis_map_dialog(self):
    from ui.dialogs.gis_map_dialog import GisMapDialog
    if not hasattr(self, '_gis_dialog') or not self._gis_dialog:
        self._gis_dialog = GisMapDialog(self)
    self._gis_dialog.load_shp_from_check(
        self.folder_path, self.water_system_shp, self.check_results
    )
    self._gis_dialog.show()
    self._gis_dialog.raise_()
    self._gis_dialog.activateWindow()

def _update_start_button(self):
    has_data = bool(self.folder_path and self.water_system_shp)
    self.start_btn.setEnabled(has_data)
    if hasattr(self, 'gis_map_btn'):
        self.gis_map_btn.setEnabled(has_data)
```

**2.4 更新 `_on_finished` 和 `clear_results`：**
- 清理 `map_load_check_btn` 相关引用
- 如果弹窗开着，通知加载检查结果

---

## 三、用户操作流程

```
1. 选择目标文件夹 + 水系文件 → "打开GIS地图"按钮变为可用
2. 点击"打开GIS地图" → 弹出 GisMapDialog，自动加载水系+断面+防治+隐患SH
3. 用户可在弹窗中操作：查看属性表、定位要素、编辑属性、全屏等
4. 关闭弹窗 → 数据保留，再次点击可重新打开
5. 执行"开始检查"后 → 如果弹窗开着，自动加载带状态的检查结果
```
