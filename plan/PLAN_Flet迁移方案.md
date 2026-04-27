# PySide6 迁移到 Flet GUI 计划

## 一、项目现状分析

### 当前技术栈
| 组件 | 技术 | 文件 |
|------|------|------|
| GUI框架 | PySide6 (Qt) | `main.py`, `ui/main_window.py` |
| 主题管理 | 自定义 QSS 样式表 | `core/theme_manager.py` |
| 侧边栏 | 自定义 Finder 风格 | `ui/components/ant_menu.py` |
| 数据检查页 | QWidget | `ui/pages/check_page.py` |
| 报表页面 | QWidget | `ui/report_page.py` |
| SHP格式化页 | QWidget | `ui/shp_formatter_page.py` |
| 业务逻辑 | geopandas, fiona | `core/checker.py`, `services/` |

### 当前项目结构
```
空间数据检查桌面版-主题/
├── main.py                 # 入口文件
├── run.py                  # 启动脚本
├── core/
│   ├── theme_manager.py    # 主题管理 (QSS样式)
│   ├── checker.py          # 数据检查逻辑
│   └── shp_formatter.py    # SHP格式化逻辑
├── ui/
│   ├── main_window.py      # 主窗口
│   ├── components/         # UI组件
│   │   ├── ant_menu.py     # 侧边栏菜单
│   │   ├── dock_bar.py     # Dock栏
│   │   └── sidebar.py      # 简洁侧边栏
│   ├── pages/              # 页面
│   │   └── check_page.py   # 数据检查页
│   ├── dialogs/            # 对话框
│   │   ├── theme_dialog.py # 主题选择
│   │   └── log_dialog.py   # 日志窗口
│   ├── report_page.py      # 报表页
│   └── shp_formatter_page.py # SHP格式化页
└── services/               # 业务服务
    ├── check_service.py
    └── filter_service.py
```

## 二、Flet 框架介绍

### 什么是 Flet？
Flet 是一个 Python 框架，用于构建跨平台桌面/移动/Web 应用，基于 Flutter。

### Flet vs PySide6 对比

| 特性 | PySide6 (Qt) | Flet (Flutter) |
|------|-------------|----------------|
| 部署方式 | 桌面应用 | 桌面/Web/移动 |
| 样式系统 | QSS (类CSS) | 内置主题 + 自定义 |
| 学习曲线 | 较陡峭 | 平缓 |
| 跨平台 | 桌面 | 全平台 |
| 打包体积 | 较大 (~100MB) | 较大 (~50MB) |
| 开发效率 | 中等 | 高 (热重载) |
| 社区生态 | 成熟 | 发展中 |

### Flet 核心组件映射

| PySide6 | Flet | 说明 |
|---------|------|------|
| `QWidget` | `ft.Container` | 容器 |
| `QMainWindow` | `ft.Page` | 主窗口 |
| `QVBoxLayout` | `ft.Column` | 垂直布局 |
| `QHBoxLayout` | `ft.Row` | 水平布局 |
| `QPushButton` | `ft.ElevatedButton` / `ft.TextButton` | 按钮 |
| `QLabel` | `ft.Text` | 文本 |
| `QLineEdit` | `ft.TextField` | 输入框 |
| `QComboBox` | `ft.Dropdown` | 下拉框 |
| `QTableWidget` | `ft.DataTable` | 表格 |
| `QStackedWidget` | 状态切换 | 页面切换 |
| `QFileDialog` | `ft.FilePicker` | 文件选择 |
| `QMessageBox` | `ft.AlertDialog` | 对话框 |
| QSS样式 | `theme` / `style` | 主题样式 |

## 三、迁移策略

### 方案A：渐进式迁移（推荐）
保留业务逻辑层，逐步替换 UI 层。

**优点：**
- 风险可控
- 可回滚
- 业务逻辑复用

**阶段：**
1. 创建 Flet 入口和基础布局
2. 迁移主题系统
3. 迁移侧边栏导航
4. 迁移各功能页面
5. 删除 PySide6 依赖

### 方案B：完全重写
从头开始用 Flet 构建新应用。

**优点：**
- 架构清晰
- 充分利用 Flet 特性

**缺点：**
- 工作量大
- 需要重写业务逻辑集成

## 四、详细迁移步骤

### 阶段1：项目初始化 (1-2天)

#### 1.1 创建 Flet 项目结构
```
空间数据检查-Flet版/
├── main.py                 # Flet 入口
├── requirements.txt        # 依赖 (flet, geopandas, fiona)
├── app/
│   ├── __init__.py
│   ├── app.py              # 主应用
│   ├── theme.py            # 主题配置
│   └── router.py           # 路由管理
├── ui/
│   ├── __init__.py
│   ├── sidebar.py          # 侧边栏
│   ├── pages/
│   │   ├── check_page.py   # 数据检查页
│   │   ├── report_page.py  # 报表页
│   │   └── shp_page.py     # SHP格式化页
│   └── dialogs/
│       └── theme_dialog.py # 主题选择
├── core/                   # 业务逻辑 (复用)
│   ├── checker.py
│   └── shp_formatter.py
└── config/
    └── settings.json
```

#### 1.2 更新依赖
```txt
# requirements.txt
flet>=0.21.0
geopandas>=0.14.0
fiona>=1.9.0
pandas>=2.0.0
pyproj>=3.6.0
```

#### 1.3 创建 Flet 入口
```python
# main.py
import flet as ft
from app.app import App

def main(page: ft.Page):
    app = App(page)
    page.add(app)

ft.app(target=main)
```

### 阶段2：主题系统迁移 (1天)

#### 2.1 Flet 主题配置
```python
# app/theme.py
import flet as ft

class ThemeManager:
    THEMES = {
        "light": {
            "primary": "#6366f1",
            "on_primary": "#ffffff",
            "background": "#f8f9fa",
            "surface": "#ffffff",
            "on_surface": "#1e293b",
        },
        "dark": {
            "primary": "#818cf8",
            "on_primary": "#1e1b4b",
            "background": "#1e1b4b",
            "surface": "#312e81",
            "on_surface": "#e2e8f0",
        },
        "qwen": {
            "primary": "#a855f7",
            "on_primary": "#ffffff",
            "background": "#f0f4ff",
            "surface": "#ffffff",
            "on_surface": "#1e1b4b",
        }
    }

    @classmethod
    def apply_theme(cls, page: ft.Page, theme_name: str):
        colors = cls.THEMES.get(theme_name, cls.THEMES["light"])
        page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=colors["primary"],
                on_primary=colors["on_primary"],
                background=colors["background"],
                surface=colors["surface"],
                on_surface=colors["on_surface"],
            )
        )
        page.update()
```

### 阶段3：侧边栏迁移 (1-2天)

#### 3.1 Flet 侧边栏组件
```python
# ui/sidebar.py
import flet as ft

class Sidebar(ft.Container):
    def __init__(self, on_navigate, on_theme_change):
        super().__init__()
        self.on_navigate = on_navigate
        self.on_theme_change = on_theme_change
        self.collapsed = False
        self.width = 220
        self._build_ui()

    def _build_ui(self):
        self.content = ft.Column(
            controls=[
                # 标题区
                ft.Container(
                    content=ft.Column([
                        ft.Text("🌏 审核汇集", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text("风险隐患调查审核工具", size=11, color=ft.colors.GREY),
                    ]),
                    padding=ft.padding.all(16),
                ),
                ft.Divider(),
                # 菜单项
                ft.Column([
                    self._create_menu_item("🔍 数据检查", "check"),
                    self._create_menu_item("📊 成果报表展示", "report"),
                    self._create_menu_item("🛠️ SHP属性格式化", "shp"),
                ]),
                ft.Container(expand=True),
                # 底部按钮
                ft.Row([
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        on_click=self._toggle_collapse,
                    ),
                    ft.IconButton(
                        icon=ft.icons.SETTINGS,
                        on_click=lambda _: self.on_theme_change(),
                    ),
                ]),
            ]
        )

    def _create_menu_item(self, text: str, page_id: str):
        return ft.Container(
            content=ft.Text(text),
            on_click=lambda _: self.on_navigate(page_id),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            ink=True,
            border_radius=ft.border_radius.all(8),
        )

    def _toggle_collapse(self, e):
        self.collapsed = not self.collapsed
        self.width = 72 if self.collapsed else 220
        self.update()
```

### 阶段4：页面迁移 (3-5天)

#### 4.1 数据检查页面
```python
# ui/pages/check_page.py
import flet as ft
from core.checker import DataChecker

class CheckPage(ft.Column):
    def __init__(self):
        super().__init__()
        self.checker = DataChecker()
        self._build_ui()

    def _build_ui(self):
        self.controls = [
            # 顶部工具栏
            ft.Row([
                ft.ElevatedButton("选择目录", icon=ft.icons.FOLDER_OPEN, on_click=self._select_folder),
                ft.ElevatedButton("开始检查", icon=ft.icons.PLAY_ARROW, on_click=self._start_check),
                ft.ElevatedButton("导出报告", icon=ft.icons.DOWNLOAD, on_click=self._export_report),
            ]),
            ft.Divider(),
            # 结果表格
            ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("文件名")),
                    ft.DataColumn(ft.Text("检查项")),
                    ft.DataColumn(ft.Text("状态")),
                    ft.DataColumn(ft.Text("详情")),
                ],
                rows=[],
            ),
        ]

    async def _select_folder(self, e):
        # Flet 文件选择
        pass

    def _start_check(self, e):
        # 调用 core.checker
        pass
```

#### 4.2 报表页面
```python
# ui/pages/report_page.py
import flet as ft

class ReportPage(ft.Column):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        self.controls = [
            ft.Text("成果报表展示", size=24, weight=ft.FontWeight.BOLD),
            # ... 报表内容
        ]
```

#### 4.3 SHP格式化页面
```python
# ui/pages/shp_page.py
import flet as ft
from core.shp_formatter import ShpFormatter

class ShpPage(ft.Column):
    def __init__(self):
        super().__init__()
        self.formatter = ShpFormatter()
        self._build_ui()

    def _build_ui(self):
        self.controls = [
            ft.Text("SHP属性格式化", size=24, weight=ft.FontWeight.BOLD),
            # ... 格式化界面
        ]
```

### 阶段5：主应用整合 (1-2天)

```python
# app/app.py
import flet as ft
from ui.sidebar import Sidebar
from ui.pages.check_page import CheckPage
from ui.pages.report_page import ReportPage
from ui.pages.shp_page import ShpPage
from app.theme import ThemeManager

class App(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.current_page = "check"
        self._setup_page()
        self._build_ui()

    def _setup_page(self):
        self.page.title = "风险隐患调查审核工具"
        self.page.window.width = 1200
        self.page.window.height = 800
        ThemeManager.apply_theme(self.page, "light")

    def _build_ui(self):
        self.pages = {
            "check": CheckPage(),
            "report": ReportPage(),
            "shp": ShpPage(),
        }

        self.content = ft.Row([
            Sidebar(
                on_navigate=self._navigate,
                on_theme_change=self._show_theme_dialog,
            ),
            ft.VerticalDivider(width=1),
            ft.Container(
                content=self.pages[self.current_page],
                expand=True,
                padding=ft.padding.all(16),
            ),
        ], expand=True)

    def _navigate(self, page_id: str):
        self.current_page = page_id
        # 更新内容区
        self.update()

    def _show_theme_dialog(self):
        # 显示主题选择对话框
        pass
```

## 五、关键迁移点

### 5.1 文件选择
**PySide6:**
```python
from PySide6.QtWidgets import QFileDialog
path = QFileDialog.getExistingDirectory(self, "选择目录")
```

**Flet:**
```python
import flet as ft

async def select_folder(e):
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)
    await file_picker.get_directory_path_async()
    # 处理结果
```

### 5.2 表格展示
**PySide6:**
```python
from PySide6.QtWidgets import QTableWidget
table = QTableWidget()
table.setColumnCount(4)
table.setRowCount(10)
```

**Flet:**
```python
import flet as ft

table = ft.DataTable(
    columns=[
        ft.DataColumn(ft.Text("列1")),
        ft.DataColumn(ft.Text("列2")),
    ],
    rows=[
        ft.DataRow(cells=[
            ft.DataCell(ft.Text("值1")),
            ft.DataCell(ft.Text("值2")),
        ]),
    ],
)
```

### 5.3 异步处理
Flet 是异步框架，需要使用 `async/await`：
```python
async def _start_check(self, e):
    # 显示进度
    self.progress.visible = True
    self.update()
    
    # 执行检查
    result = await self._run_check_async()
    
    # 更新UI
    self.progress.visible = False
    self.update()
```

## 六、业务逻辑复用

### 可直接复用的模块
| 模块 | 文件 | 复用程度 |
|------|------|----------|
| 数据检查逻辑 | `core/checker.py` | 100% |
| SHP格式化 | `core/shp_formatter.py` | 100% |
| 数据验证 | `core/data_validator.py` | 100% |
| 配置管理 | `core/config_manager.py` | 100% |

### 需要适配的模块
| 模块 | 变更 |
|------|------|
| 主题管理 | 从 QSS 改为 Flet Theme |
| UI组件 | 全部重写 |
| 对话框 | 使用 Flet 对话框组件 |

## 七、时间估算

| 阶段 | 工作量 | 时间 |
|------|--------|------|
| 项目初始化 | 中 | 1-2天 |
| 主题迁移 | 低 | 1天 |
| 侧边栏迁移 | 中 | 1-2天 |
| 页面迁移 | 高 | 3-5天 |
| 测试调试 | 中 | 2-3天 |
| **总计** | | **8-13天** |

## 八、风险与建议

### 风险
1. **Flet 生态较小** - 某些高级控件可能需要自定义
2. **异步编程** - 需要熟悉 async/await
3. **打包问题** - Flet 打包配置可能与现有流程不同

### 建议
1. **保留原项目** - 创建新目录进行迁移
2. **渐进式迁移** - 先迁移简单页面验证可行性
3. **充分测试** - 确保业务逻辑正确性
4. **文档更新** - 更新开发文档和部署流程

## 九、迁移完成状态

### ✅ 已完成迁移

| 模块 | 文件 | 状态 |
|------|------|------|
| 入口文件 | `main.py` | ✅ 已创建 |
| 依赖配置 | `requirements.txt` | ✅ 已创建 |
| 主题系统 | `app/theme.py` | ✅ 已迁移 |
| 主应用 | `app/app.py` | ✅ 已创建 |
| 路由管理 | `app/router.py` | ✅ 已创建 |
| 侧边栏 | `ui/sidebar.py` | ✅ 已迁移 |
| 数据检查页 | `ui/pages/check_page.py` | ✅ 已迁移 |
| 报表页面 | `ui/pages/report_page.py` | ✅ 已迁移 |
| SHP格式化页 | `ui/pages/shp_page.py` | ✅ 已迁移 |
| 主题对话框 | `ui/dialogs/theme_dialog.py` | ✅ 已迁移 |
| 业务逻辑 | `core/checker.py` | ✅ 已简化迁移 |
| SHP格式化 | `core/shp_formatter.py` | ✅ 已简化迁移 |
| 配置管理 | `core/config_manager.py` | ✅ 已迁移 |
| 检查服务 | `services/check_service.py` | ✅ 已迁移 |
| 筛选服务 | `services/filter_service.py` | ✅ 已迁移 |
| 配置文件 | `config/settings.json` | ✅ 已创建 |

### 项目结构

```
flet/
├── main.py                 # Flet入口
├── requirements.txt        # 依赖
├── app/
│   ├── __init__.py
│   ├── app.py              # 主应用
│   ├── router.py           # 路由
│   └── theme.py            # 主题管理
├── ui/
│   ├── __init__.py
│   ├── sidebar.py          # 侧边栏
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── check_page.py   # 数据检查页
│   │   ├── report_page.py  # 报表页
│   │   └── shp_page.py     # SHP格式化页
│   └── dialogs/
│       ├── __init__.py
│       └── theme_dialog.py # 主题对话框
├── core/
│   ├── __init__.py
│   ├── checker.py          # 数据检查逻辑
│   ├── shp_formatter.py    # SHP格式化逻辑
│   └── config_manager.py   # 配置管理
├── services/
│   ├── __init__.py
│   ├── check_service.py    # 检查服务
│   └── filter_service.py   # 筛选服务
└── config/
    └── settings.json       # 配置文件
```

### 运行方式

```bash
cd flet
pip install -r requirements.txt
python main.py
```

---

## 十、是否推荐迁移？

### 推荐迁移的场景
- 需要跨平台部署（Web/移动端）
- 团队熟悉 Flutter/Flet
- 希望快速开发迭代

### 不推荐迁移的场景
- 仅需桌面应用
- 项目稳定，无需大改
- 团队不熟悉异步编程
- 时间紧迫

### 当前项目建议
**暂不推荐迁移**，原因：
1. 当前 PySide6 版本功能完善
2. 业务逻辑复杂，迁移风险高
3. Flet 对 GIS 数据处理的支持不如 Qt 成熟
4. 打包部署流程需要重新配置

如需跨平台能力，建议：
- 保留桌面版（PySide6）
- 新建 Web 版（Flet/FastAPI）
