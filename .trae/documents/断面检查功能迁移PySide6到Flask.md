# 断面检查功能迁移：PySide6 → Flask

## 概述

将 `d:\github\空间数据检查桌面版-主题-design-2026` 项目中的断面数据检查功能（PySide6 桌面应用），完整迁移到 `D:\qh-dcpj-py\24青海审核汇数据处理_202604\24青海审核汇数据处理_202604_GUI` Flask Web 项目中，新增"断面测量表检查"菜单。

## 迁移日期

2026-05-11

---

## 一、源项目功能分析

### 源文件清单

| 文件 | 路径 | 角色 |
|------|------|------|
| section_check_page.py | ui/pages/check_section/ | 主页面（PySide6 QWidget） |
| chart_tab.py | ui/pages/check_section/ | 断面成图Tab（QWebEngineView + ECharts） |
| points_tab.py | ui/pages/check_section/ | 数据详情Tab（QTableWidget） |
| issues_tab.py | ui/pages/check_section/ | 校验问题Tab |
| section_tree_card.py | ui/pages/check_section/ | 断面树导航 |
| section_check_service.py | services/ | UI服务门面（QThread异步加载） |
| section_chart_service.py | services/ | **核心业务逻辑** |
| section_html_builder.py | services/ | 单断面ECharts HTML生成器 |
| generate_section_chart_with_coords_青海.py | services/ | 批量断面交互式HTML |
| feature_keywords_dialog.py | ui/dialogs/ | 特征点关键词配置对话框 |
| log_dialog.py | ui/dialogs/ | 日志对话框 |

### 核心业务逻辑（section_chart_service.py）

- **数据加载**：递归扫描目录下所有 `.xlsx` 文件，使用 openpyxl 只读模式加载
- **表格识别**：自动识别"规范表"（含"沟道横断面测量成果表"关键字）和"成图表"（仅起点距+高程）
- **规范表解析**：从固定行位提取断面属性（位置/区划代码/沟道代码/基点坐标/方位角/水位等），从第10行起逐行读取测量点
- **成图表解析**：仅读取起点距和高程两列
- **特征点识别**：根据特征描述字段是否包含预设关键词（基点/堤顶/深泓等16个），自动标记 isFeature
- **SQLite持久化**：sections 表（28列）+ section_points 表（9列）

### 19条校验规则

| 规则ID | 描述 | 级别 |
|--------|------|------|
| seq_missing | 序号缺失 | error |
| seq_duplicate | 序号重复 | error |
| seq_not_monotonic | 序号非递增 | warning |
| seq_gap | 序号跳号 | warning |
| dist_negative | 起点距为负 | error |
| dist_not_monotonic | 起点距回退 | error |
| dist_duplicate | 起点距重复 | warning |
| dist_jump | 起点距跳变 | warning |
| lon_out_of_range | 经度超范围 | error |
| lon_zero | 经度为零或缺失 | error |
| lon_jump | 经度跳变 | warning |
| lat_out_of_range | 纬度超范围 | error |
| lat_zero | 纬度为零或缺失 | error |
| lat_jump | 纬度跳变 | warning |
| lonlat_swapped | 经纬度互换 | error |
| coord_missing | 经纬度缺失 | warning |
| all_same_coord | 所有点坐标相同 | error |
| linear_fit_deviation | 线性拟合偏差 | warning |
| direction_reversal | 连线方向折返 | error |
| adjacent_reversal | 相邻线段折返 | error |

### 空间异常检测

- **方向反转**：某段线与首末点主方向夹角>90度
- **相邻线段折返**：相邻两段线夹角>90度
- **线段交叉**：使用叉积法检测非相邻线段是否相交

### 导出格式

1. **Excel校验报告**（.xlsx）— 异常断面汇总
2. **异常断面HTML** — 交互式ECharts图表，左侧树形导航
3. **全部断面成图HTML** — 同上结构，包含所有断面
4. **单断面成图HTML** — 双图表（断面形态图 + 测量点位置图）

---

## 二、目标项目架构

### 技术栈

- **后端**：Flask + Python
- **前端**：Tailwind CSS + 原生 JS + ECharts 5.5
- **实时通信**：SSE (Server-Sent Events)
- **数据存储**：SQLite
- **Excel处理**：openpyxl + pandas

### MVC模式

```
┌─────────────────────────────────────────┐
│  Flask 路由层 (app.py)                   │  ← HTTP 接口
├─────────────────────────────────────────┤
│  控制器层 (core/controllers.py)          │  ← 业务编排，线程管理
├─────────────────────────────────────────┤
│  模型层 (core/models.py)                 │  ← 状态管理，回调通知
├─────────────────────────────────────────┤
│  工作线程层 (core/*_worker.py)           │  ← 耗时计算，独立线程
├─────────────────────────────────────────┤
│  前端模板 (templates/*.html)             │  ← UI 渲染
│  静态资源 (static/css, static/js)        │
└─────────────────────────────────────────┘
```

### 核心设计模式

1. **观察者模式** — Model 通过 `on_xxx` 回调属性实现变更通知
2. **生产者-消费者** — Worker 线程产生事件放入 Queue，SSE 端消费推送到前端
3. **模板继承** — Jinja2 base.html 提供统一布局
4. **主题系统** — CSS 变量 + data-theme 属性实现多主题切换
5. **服务端文件浏览** — 自定义文件选择器替代浏览器原生文件上传

---

## 三、迁移实施

### 新增文件（5个）

| 文件 | 说明 |
|------|------|
| `core/section_check_service.py` | 核心业务逻辑：Excel读取、19条校验规则、空间异常检测、SQLite持久化、导出功能 |
| `core/section_html_builder.py` | 单断面ECharts HTML生成器（移除PySide6 QUrl依赖） |
| `core/section_chart_batch.py` | 批量断面交互式HTML生成器（含左侧树导航+右侧多列图表） |
| `core/section_check_worker.py` | 工作线程：异步执行数据加载 |
| `templates/section_check.html` | 前端页面模板：Tailwind CSS + ECharts + 原生JS |

### 修改文件（5个）

| 文件 | 修改内容 |
|------|----------|
| `core/models.py` | 新增 `SectionCheckConfig` + `SectionCheckModel` |
| `core/controllers.py` | 新增 `SectionCheckController`（遵循现有MVC模式） |
| `core/__init__.py` | 导出新类 |
| `app.py` | 新增1个页面路由 + 13个API路由 |
| `templates/base.html` | 侧边栏新增"断面测量表检查"菜单项 |

### API路由清单

| 路由 | 方法 | 功能 |
|------|------|------|
| `/section_check` | GET | 页面路由 |
| `/api/section_check/start` | POST | 启动数据加载 |
| `/api/section_check/stop` | POST | 停止加载 |
| `/api/section_check/stats` | GET | 获取统计信息 |
| `/api/section_check/tree` | GET | 获取断面树形数据 |
| `/api/section_check/sections` | GET | 按条件查询断面列表 |
| `/api/section_check/detail/<key>` | GET | 获取断面详情 |
| `/api/section_check/chart/<key>` | GET | 获取单断面ECharts HTML |
| `/api/section_check/export/report` | POST | 导出Excel校验报告 |
| `/api/section_check/export/anomaly_html` | POST | 导出异常断面HTML |
| `/api/section_check/export/all_html` | POST | 导出全部断面成图HTML |
| `/api/section_check/keywords` | GET | 获取特征点关键词 |
| `/api/section_check/keywords` | POST | 保存特征点关键词 |

### SSE事件类型

| 事件类型 | 数据 | 说明 |
|----------|------|------|
| `section_check_state_changed` | `{state: "IDLE/RUNNING/COMPLETED/ERROR"}` | 状态变更 |
| `section_check_progress_changed` | `{message, pct}` | 进度更新 |
| `section_check_log` | `{text}` | 日志消息 |
| `section_check_processing_complete` | `{total_sections, total_points, anomaly_count, validation_error_count}` | 加载完成 |

---

## 四、迁移适配要点

### 4.1 PySide6 → Flask 的关键转换

| PySide6 组件 | Flask 对应 |
|-------------|-----------|
| QThread 异步加载 | Worker 线程 + SSE 推送 |
| QWebEngineView 渲染 ECharts | 前端直接用 ECharts JS |
| QTreeWidget 断面导航 | HTML 树形列表 + JS 渲染 |
| QTabWidget 详情标签 | HTML Tab 切换 |
| QTableWidget 数据表格 | HTML `<table>` + JS 动态填充 |
| QMessageBox 弹窗 | JS `alert()` / 自定义模态框 |
| QFileDialog 目录选择 | `createFileBrowser()` 自定义文件浏览器 |
| Signal/Slot 通信 | SSE EventSource + fetch API |

### 4.2 文件浏览器适配

最初使用了简陋的内联模态框实现，发现无法正常选择目录。后替换为项目统一的 `createFileBrowser()` 方案：

- JS 动态创建 DOM 元素
- 返回 Promise，`await` 获取路径
- 支持目录/文件两种选择模式
- 使用 `themes.css` 中已定义的 `.file-browser-*` 样式
- 与 index.html / area.html 完全一致

### 4.3 核心业务逻辑迁移

`section_chart_service.py` → `section_check_service.py` 的主要改动：

1. **移除 PySide6 依赖**：删除 QUrl、QThread 等 import
2. **数据库路径调整**：DB_PATH 改为相对于 Flask 项目根目录的 `data/section_check.db`
3. **导出方法适配**：`export_anomaly_html()` 和 `export_all_html()` 改为从 `section_chart_batch` 导入
4. **新增查询方法**：`get_sections_by_filter()` 支持按分类/异常/错误/搜索过滤

---

## 五、验证结果

### 导入测试

```
from core import SectionCheckController, SectionCheckModel, SectionCheckConfig
# Import OK ✓
```

### 路由注册测试

```
/section_check [GET] ✓
/api/section_check/start [POST] ✓
/api/section_check/stop [POST] ✓
/api/section_check/stats [GET] ✓
/api/section_check/tree [GET] ✓
/api/section_check/sections [GET] ✓
/api/section_check/detail/<path:key> [GET] ✓
/api/section_check/chart/<path:key> [GET] ✓
/api/section_check/export/report [POST] ✓
/api/section_check/export/anomaly_html [POST] ✓
/api/section_check/export/all_html [POST] ✓
/api/section_check/keywords [GET] ✓
/api/section_check/keywords [POST] ✓
```

### 页面访问测试

```
GET http://127.0.0.1:9010/section_check → Status: 200 ✓
HTML length: 52723
Contains: chartContainer ✓, sectionTree ✓, echarts ✓, loadBtn ✓
```

### API 测试

```
GET /api/section_check/stats → {total_sections: 0, total_points: 0, ...} ✓
```

---

## 六、遇到的问题及解决

### 问题1：页面404

**原因**：有旧的 Flask 进程（PID 4880 和 9180）仍在 9010 端口上运行，请求被旧进程处理。

**解决**：杀掉旧进程后重新启动。

### 问题2：文件浏览器无法选择目录

**原因**：使用了简陋的内联模态框实现，缺少关键功能（上级按钮、路径手动输入、Promise返回值等）。

**解决**：替换为项目统一的 `createFileBrowser()` 方案，与 index.html / area.html 完全一致。

### 问题3：浏览器缓存

**原因**：浏览器缓存了旧页面，看不到新增的菜单项。

**解决**：`Ctrl + Shift + R` 强制刷新。
