# 异常断面HTML导出功能改造说明

## 改造目标

将"导出异常断面HTML"功能从原来简单的单图表模板，替换为 `generate_section_chart_with_coords_青海.py` 中功能丰富的组合图模板，使导出的HTML具备完整的交互能力。

## 改造前后对比

### 改造前（旧模板 `_generate_anomaly_html_template`）

- 左侧边栏仅按文件路径分组，无搜索、无过滤、无分页
- 点击断面只显示**断面形态图**（起点距-高程），无测量点位置图
- 无水位线开关
- 无序号/经纬度标注切换
- 无多列布局切换
- 无批量选择加载功能
- 约100行内联HTML模板代码

### 改造后（复用 `generate_section_chart_with_coords_青海.py`）

- 左侧边栏带搜索框、过滤按钮（仅异常/仅校验错误）、分页控件
- 每个断面卡片同时显示**断面形态图**和**测量点位置图**（上下排列）
- 支持多选断面批量加载成图
- 支持水位线开关（历史最高水位/成灾水位/壅水高程）
- 支持序号/经纬度标注切换
- 支持1-4列布局切换
- 复用已有成熟模板，减少重复代码

## 涉及文件

| 文件 | 修改内容 |
|------|---------|
| `services/section_chart_service.py` | 重写 `export_anomaly_html` 方法，删除 `_generate_anomaly_html_template` 方法 |
| `services/generate_section_chart_with_coords_青海.py` | 无修改，仅作为依赖被引用 |

## 核心改动

### 1. `export_anomaly_html` 方法重写

**文件**: `services/section_chart_service.py` 第1088-1107行

```python
def export_anomaly_html(self, output_path: str) -> str:
    from services.generate_section_chart_with_coords_青海 import generate_html, build_tree_data

    self.recalculate_sections()
    sections = self.get_anomaly_sections()
    if not sections:
        return ""

    for key, sec in sections.items():
        sec["river"] = sec.get("category", "")
        sec["district"] = sec.get("file_name", "")

    tree = build_tree_data(sections)
    html = generate_html(sections, tree, "异常断面汇总", default_filter_anomaly=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path
```

### 2. 删除旧方法

删除了 `_generate_anomaly_html_template` 方法（约100行内联HTML模板代码），不再需要。

## 数据字段映射

`generate_section_chart_with_coords_青海.py` 中的 `build_tree_data` 和 `generate_html` 依赖以下字段构建树形结构和图表：

| 模板所需字段 | 当前系统字段 | 说明 |
|-------------|------------|------|
| `river` | `category` | 一级分组，对应"防治对象"、"跨沟桥涵"、"沟滩占地对象"等文件夹目录名 |
| `district` | `file_name` | 二级分组，对应Excel文件名 |
| `name` | `name` | 断面名称 |
| `points` | `points` | 测量点数据列表 |
| `anomaly` | `anomaly` | 是否经纬度连线异常 |
| `validation_error` | `validation_error` | 是否有校验错误 |
| `validation_warning` | `validation_warning` | 是否有校验警告 |
| `validation_issues` | `validation_issues` | 校验问题详情列表 |
| `hmz` | `hmz` | 历史最高水位 |
| `czz` | `czz` | 成灾水位 |
| `backwater` | `backwater` | 壅水高程 |

### 映射逻辑

`get_anomaly_sections` 方法从数据库读取数据时，已将 `category` 映射为 `river`、`location` 映射为 `district`。但由于 `location` 在本系统中是断面位置描述（如"药草沟1号坝"），而非文件名，因此在 `export_anomaly_html` 中重新映射：

```python
sec["river"] = sec.get("category", "")      # 防治对象/跨沟桥涵/沟滩占地对象
sec["district"] = sec.get("file_name", "")   # Excel文件名
```

这样在导出的HTML中，左侧树形结构为：

```
├── 防治对象
│   ├── 630121_大通_防治对象.xlsx
│   │   ├── 断面1
│   │   └── 断面2
│   └── ...
├── 跨沟桥涵
│   └── ...
└── 沟滩占地对象
    └── ...
```

## 测量点数据格式

每个测量点需包含以下字段供ECharts图表使用：

| 字段 | 类型 | 说明 |
|------|------|------|
| `seq` | int/float | 序号 |
| `distance` | float | 起点距(m) |
| `elevation` | float | 高程(m) |
| `lon` | float/None | 经度(°) |
| `lat` | float/None | 纬度(°) |
| `feature` / `feature_desc` | str | 特征描述 |
| `isFeature` | bool | 是否特征点 |

## 调用链路

```
用户点击"导出异常断面HTML"按钮
  → section_check_page.py: _export_anomaly_html()
    → section_check_service.py: export_anomaly_html(output_path)
      → section_chart_service.py: export_anomaly_html(output_path)
        → get_anomaly_sections()           # 从SQLite读取异常断面
        → 字段映射 (river←category, district←file_name)
        → build_tree_data(sections)        # 构建树形结构
        → generate_html(sections, tree, "异常断面汇总", default_filter_anomaly=True)
        → 写入HTML文件
```

## 注意事项

1. `generate_section_chart_with_coords_青海.py` 中有 `import numpy as np` 和 `import pandas as pd`，这些依赖在 `build_tree_data` 和 `generate_html` 中不直接使用，但该文件顶部的 `SpatialContinuityChecker` 类依赖它们。如果仅导入 `generate_html` 和 `build_tree_data`，不会触发这些依赖的加载问题。

2. `default_filter_anomaly=True` 参数使导出的HTML默认开启"仅显示异常断面"过滤，因为导出的本身就是异常断面数据。

3. `get_anomaly_sections` 查询条件为 `WHERE anomaly = 1 OR validation_error = 1`，同时包含经纬度异常和数据校验错误的断面。

4. **成图表与规范表的校验差异**：断面数据分为"成图表"（`table_type=chengtu`）和"规范表"（`table_type=guifan`）两种类型。成图表只有起点距和高程数据，天然没有经纬度，因此校验逻辑中已对成图表做了豁免处理——以下三条规则对成图表不报错：
   - `lon_zero`（经度为零或缺失）
   - `lat_zero`（纬度为零或缺失）
   - `coord_missing`（经纬度缺失）

   这意味着成图表不会因为缺少经纬度而被标记为校验错误，只有规范表缺少经纬度时才会触发这些校验规则。
