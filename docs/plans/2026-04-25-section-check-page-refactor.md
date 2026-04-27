# section_check_page.py 拆分重构计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 `section_check_page.py`（1144行）中的业务逻辑和 HTML 生成逻辑拆分到独立的 service 层和 html 模块中，使 UI 层只负责界面展示和事件转发。

**Architecture:** 采用三层拆分策略：
1. **HTML 生成模块** (`services/section_html_builder.py`)：将 ECharts 配置构建、HTML 模板、HTML 生成函数全部迁移
2. **业务逻辑 Service** (`services/section_check_service.py`)：将 UI 中的业务逻辑（数据加载调度、导出报告、导出异常HTML、打开成图等）封装为独立 service
3. **UI 层** (`ui/section_check_page.py`)：仅保留 UI 初始化、事件绑定、数据展示逻辑，业务操作委托给 service

**Tech Stack:** PySide6, Python 3.10+

---

## 当前文件结构分析

`section_check_page.py` 当前包含以下内容（按行号）：

| 行号范围 | 内容 | 拆分去向 |
|----------|------|----------|
| 1-28 | imports + HAS_WEB_ENGINE 检测 | UI 层保留 imports，HTML 模块也需部分 |
| 30-33 | ECHARTS_CDN / ECHARTS_SRC 常量 | → `section_html_builder.py` |
| 36-54 | `LoadDataThread` 类 | → `section_check_service.py` |
| 57-186 | `CHART_HTML_TEMPLATE` 模板 | → `section_html_builder.py` |
| 189-214 | `generate_chart_html()` 函数 | → `section_html_builder.py` |
| 217-313 | `build_section_chart_option_js()` 函数 | → `section_html_builder.py` |
| 316-395 | `build_coord_chart_option_js()` 函数 | → `section_html_builder.py` |
| 398-1144 | `SectionCheckPage` 类 | UI 层保留，但业务逻辑方法迁移 |

### SectionCheckPage 中的方法分类

**保留在 UI 层的方法（纯 UI 逻辑）：**
- `__init__` — 初始化 UI 组件和 service
- `_init_ui` — 纯 UI 布局
- `showEvent` — 入场动画
- `_select_directory` — 文件对话框
- `_on_load_progress` — 进度条更新
- `_on_load_finished` — UI 状态更新 + 统计刷新
- `_on_load_error` — 错误提示
- `_update_stats` — 统计标签更新
- `_refresh_tree` — 树控件刷新
- `_on_section_clicked` — 点击事件
- `_load_section_detail` — 加载详情（调用 service 获取数据 + 调用 UI 渲染）
- `_fill_points_table` — 表格填充
- `_fill_issues_table` — 表格填充
- `_fill_info_table` — 属性表格填充
- `_on_search` / `_on_filter_changed` — 过滤事件
- `_on_log_btn_clicked` — 信号转发
- `_on_feature_config_clicked` — 打开对话框
- `_on_keywords_changed` — 关键词变更后刷新
- `_on_page_size_changed` / `_on_prev_page` / `_on_next_page` — 分页（当前未实现分页逻辑，但预留了）

**迁移到 service 层的方法（业务逻辑）：**
- `_start_load` → `SectionCheckService.start_load()` — 创建线程、启动加载
- `_render_chart` → `SectionCheckService.render_chart_html()` — 生成 HTML + 写临时文件
- `_open_chart_external` → `SectionCheckService.open_chart_external()` — 生成 HTML + 写文件 + 打开
- `_export_report` → `SectionCheckService.export_report()` — 调用 service 导出
- `_export_anomaly_html` → `SectionCheckService.export_anomaly_html()` — 调用 service 导出
- `_preview_excel` → `SectionCheckService.get_excel_preview_info()` — 获取 Excel 预览信息

---

## Task 1: 创建 HTML 生成模块 `services/section_html_builder.py`

**Files:**
- Create: `services/section_html_builder.py`

**Step 1: 创建文件，迁移以下内容**

从 `section_check_page.py` 迁移：
1. `ECHARTS_CDN` 常量（第30行）
2. `_LOCAL_ECHARTS` / `ECHARTS_SRC` 常量（第32-33行）— 需要调整路径计算（因为文件位置变了）
3. `CHART_HTML_TEMPLATE` 模板（第57-186行）
4. `generate_chart_html()` 函数（第189-214行）
5. `build_section_chart_option_js()` 函数（第217-313行）
6. `build_coord_chart_option_js()` 函数（第316-395行）

**关键注意事项：**
- `_LOCAL_ECHARTS` 的路径计算基于 `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`，在 `services/` 目录下，这仍然指向项目根目录，所以路径计算不变
- `generate_chart_html()` 中使用了 `ECHARTS_SRC` 和 `ECHARTS_CDN`，迁移后它们在同一个文件中，无需改动
- `generate_chart_html()` 的 `json` import 需要添加

```python
# -*- coding: utf-8 -*-
import json
import os

from PySide6.QtCore import QUrl

ECHARTS_CDN = "https://registry.npmmirror.com/echarts/5.5.0/files/dist/echarts.min.js"

_LOCAL_ECHARTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "js", "echarts.min.js")
ECHARTS_SRC = QUrl.fromLocalFile(_LOCAL_ECHARTS).toString() if os.path.isfile(_LOCAL_ECHARTS) else ECHARTS_CDN

CHART_HTML_TEMPLATE = """..."""  # 原样复制

def generate_chart_html(sec: dict) -> str:
    # 原样复制

def build_section_chart_option_js(sec: dict) -> dict:
    # 原样复制

def build_coord_chart_option_js(sec: dict) -> dict:
    # 原样复制
```

**Step 2: 验证模块可导入**

Run: `cd d:\github\空间数据检查桌面版-主题-design && python -c "from services.section_html_builder import generate_chart_html, build_section_chart_option_js, build_coord_chart_option_js, ECHARTS_SRC, ECHARTS_CDN; print('OK')"`

---

## Task 2: 创建业务逻辑 Service `services/section_check_service.py`

**Files:**
- Create: `services/section_check_service.py`

**Step 1: 创建文件，迁移以下内容**

从 `section_check_page.py` 迁移：
1. `LoadDataThread` 类（第36-54行）— 需要保留 PySide6 的 QThread 依赖
2. 业务逻辑方法封装为 `SectionCheckService` 类

```python
# -*- coding: utf-8 -*-
import os
import tempfile

from PySide6.QtCore import QThread, Signal

from services.section_chart_service import SectionChartService, get_feature_keywords
from services.section_html_builder import generate_chart_html, ECHARTS_SRC, ECHARTS_CDN


class LoadDataThread(QThread):
    progress_signal = Signal(int, int, str)
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, service: SectionChartService, directory: str, parent=None):
        super().__init__(parent)
        self.service = service
        self.directory = directory

    def run(self):
        try:
            result = self.service.load_from_directory(
                self.directory,
                progress_callback=lambda cur, total, name: self.progress_signal.emit(cur, total, name)
            )
            self.finished_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))


class SectionCheckService:
    def __init__(self):
        self.chart_service = SectionChartService()
        self.load_thread = None

    def start_load(self, directory: str, on_progress, on_finished, on_error, parent=None):
        get_feature_keywords()
        self.load_thread = LoadDataThread(self.chart_service, directory, parent)
        self.load_thread.progress_signal.connect(on_progress)
        self.load_thread.finished_signal.connect(on_finished)
        self.load_thread.error_signal.connect(on_error)
        self.load_thread.start()

    def get_chart_service(self) -> SectionChartService:
        return self.chart_service

    def render_chart_to_temp(self, section_key: str, sec: dict) -> str:
        html = generate_chart_html(sec)
        tmp_dir = os.path.join(tempfile.gettempdir(), "section_charts")
        os.makedirs(tmp_dir, exist_ok=True)
        safe_key = section_key or "default"
        for c in '<>:"/\\|?* ':
            safe_key = safe_key.replace(c, "_")
        tmp_path = os.path.join(tmp_dir, f"chart_{safe_key}.html")
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(html)
        return tmp_path

    def open_chart_external(self, section_key: str, sec: dict) -> str:
        html = generate_chart_html(sec)
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
        os.makedirs(output_dir, exist_ok=True)
        safe_name = sec.get("name", "chart").replace("/", "_").replace("\\", "_").replace(" ", "_")
        output_path = os.path.join(output_dir, f"断面成图_{safe_name}.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        os.startfile(output_path)
        return output_path

    def export_report(self, output_path: str):
        self.chart_service.export_validation_report(output_path)

    def export_anomaly_html(self, output_path: str):
        return self.chart_service.export_anomaly_html(output_path)

    def get_excel_preview_info(self, section_key: str):
        sec = self.chart_service.get_section_detail(section_key)
        if not sec:
            return None
        return {
            "source_file": sec.get("source_file", ""),
            "sheet_name": sec.get("sheet_name", ""),
        }

    def get_stats(self):
        return self.chart_service.get_stats()

    def get_tree_data(self):
        return self.chart_service.get_tree_data()

    def get_section_detail(self, section_key: str):
        return self.chart_service.get_section_detail(section_key)

    def recalculate_sections(self):
        self.chart_service.recalculate_sections()
```

**Step 2: 验证模块可导入**

Run: `cd d:\github\空间数据检查桌面版-主题-design && python -c "from services.section_check_service import SectionCheckService, LoadDataThread; print('OK')"`

---

## Task 3: 更新 `services/__init__.py`

**Files:**
- Modify: `services/__init__.py`

**Step 1: 添加新模块的导出**

```python
# -*- coding: utf-8 -*-
"""
业务服务层
"""

from .check_service import CheckService
from .filter_service import FilterService
from .section_check_service import SectionCheckService
```

---

## Task 4: 重构 `ui/section_check_page.py`

**Files:**
- Modify: `ui/section_check_page.py`

**Step 1: 更新 imports**

删除：
- `ECHARTS_CDN`, `_LOCAL_ECHARTS`, `ECHARTS_SRC` 相关代码
- `LoadDataThread` 的定义
- `CHART_HTML_TEMPLATE` 的定义
- `generate_chart_html`, `build_section_chart_option_js`, `build_coord_chart_option_js` 的定义
- `from services.section_chart_service import SectionChartService, get_feature_keywords`（改为通过 SectionCheckService 间接使用）

添加：
- `from services.section_check_service import SectionCheckService`

保留：
- `from core.theme_manager import get_theme_manager`
- `from core.effects_manager import StaggerEntrance, TabFadeTransition, ButtonGlowHelper`
- `from ui.dialogs.log_dialog import LogDialog`
- `from ui.dialogs.excel_preview_dialog import ExcelPreviewDialog`
- `from ui.dialogs.feature_keywords_dialog import FeatureKeywordsDialog`
- `HAS_WEB_ENGINE` 检测
- `QUrl` import（用于 setUrl）

**Step 2: 重构 `__init__` 方法**

```python
def __init__(self, parent=None):
    super().__init__(parent)
    self.service = SectionCheckService()
    self.theme_manager = get_theme_manager()
    self._current_section_key = None
    self._all_points = []
    self._current_page = 0
    self._page_size = 50
    self._init_ui()
```

**Step 3: 重构 `_start_load` 方法**

原来：
```python
def _start_load(self):
    directory = self.dir_edit.text()
    if not directory:
        QMessageBox.warning(self, "警告", "请先选择测量数据目录")
        return
    if not os.path.exists(directory):
        QMessageBox.warning(self, "警告", "目录不存在")
        return
    get_feature_keywords()
    self.load_btn.setEnabled(False)
    self.export_btn.setEnabled(False)
    self.export_html_btn.setEnabled(False)
    self.open_chart_btn.setEnabled(False)
    self.progress_bar.setVisible(True)
    self.progress_bar.setRange(0, 0)
    self.load_thread = LoadDataThread(self.service, directory)
    self.load_thread.progress_signal.connect(self._on_load_progress)
    self.load_thread.finished_signal.connect(self._on_load_finished)
    self.load_thread.error_signal.connect(self._on_load_error)
    self.load_thread.start()
```

重构后：
```python
def _start_load(self):
    directory = self.dir_edit.text()
    if not directory:
        QMessageBox.warning(self, "警告", "请先选择测量数据目录")
        return
    if not os.path.exists(directory):
        QMessageBox.warning(self, "警告", "目录不存在")
        return
    self.load_btn.setEnabled(False)
    self.export_btn.setEnabled(False)
    self.export_html_btn.setEnabled(False)
    self.open_chart_btn.setEnabled(False)
    self.progress_bar.setVisible(True)
    self.progress_bar.setRange(0, 0)
    self.service.start_load(
        directory,
        on_progress=self._on_load_progress,
        on_finished=self._on_load_finished,
        on_error=self._on_load_error,
        parent=self,
    )
```

**Step 4: 重构 `_on_load_finished` 方法**

原来：
```python
def _on_load_finished(self, result):
    self.progress_bar.setVisible(False)
    self.load_btn.setEnabled(True)
    self.export_btn.setEnabled(True)
    self.export_html_btn.setEnabled(True)
    self.open_chart_btn.setEnabled(True)
    stats = self.service.get_stats()
    self._update_stats(stats)
    self._refresh_tree()
    ...
```

重构后（`self.service` 现在是 `SectionCheckService`，它的 `get_stats()` 委托给 `chart_service`）：
```python
def _on_load_finished(self, result):
    self.progress_bar.setVisible(False)
    self.load_btn.setEnabled(True)
    self.export_btn.setEnabled(True)
    self.export_html_btn.setEnabled(True)
    self.open_chart_btn.setEnabled(True)
    stats = self.service.get_stats()
    self._update_stats(stats)
    self._refresh_tree()
    msg = f"加载完成: {result['total_sections']}个断面, {result['total_points']}个测量点"
    if result['anomaly_count'] > 0:
        msg += f", {result['anomaly_count']}个异常"
    if result['validation_error_count'] > 0:
        msg += f", {result['validation_error_count']}个校验错误"
    self.log_message.emit(msg)
```

**Step 5: 重构 `_render_chart` 方法**

原来：
```python
def _render_chart(self, sec: dict):
    if not HAS_WEB_ENGINE:
        return
    html = generate_chart_html(sec)
    tmp_dir = os.path.join(tempfile.gettempdir(), "section_charts")
    os.makedirs(tmp_dir, exist_ok=True)
    safe_key = (self._current_section_key or "default")
    for c in '<>:"/\\|?* ':
        safe_key = safe_key.replace(c, "_")
    tmp_path = os.path.join(tmp_dir, f"chart_{safe_key}.html")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(html)
    self.chart_web.setUrl(QUrl.fromLocalFile(tmp_path))
```

重构后：
```python
def _render_chart(self, sec: dict):
    if not HAS_WEB_ENGINE:
        return
    tmp_path = self.service.render_chart_to_temp(self._current_section_key, sec)
    self.chart_web.setUrl(QUrl.fromLocalFile(tmp_path))
```

**Step 6: 重构 `_open_chart_external` 方法**

原来：
```python
def _open_chart_external(self):
    if not self._current_section_key:
        QMessageBox.warning(self, "警告", "请先选择一个断面")
        return
    sec = self.service.get_section_detail(self._current_section_key)
    if not sec:
        return
    html = generate_chart_html(sec)
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    os.makedirs(output_dir, exist_ok=True)
    safe_name = sec.get("name", "chart").replace("/", "_").replace("\\", "_").replace(" ", "_")
    output_path = os.path.join(output_dir, f"断面成图_{safe_name}.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    os.startfile(output_path)
    self.log_message.emit(f"已打开断面成图: {output_path}")
```

重构后：
```python
def _open_chart_external(self):
    if not self._current_section_key:
        QMessageBox.warning(self, "警告", "请先选择一个断面")
        return
    sec = self.service.get_section_detail(self._current_section_key)
    if not sec:
        return
    output_path = self.service.open_chart_external(self._current_section_key, sec)
    self.log_message.emit(f"已打开断面成图: {output_path}")
```

**Step 7: 重构 `_export_report` 方法**

原来：
```python
def _export_report(self):
    output_path, _ = QFileDialog.getSaveFileName(...)
    if output_path:
        try:
            self.service.export_validation_report(output_path)
            QMessageBox.information(self, "完成", f"校验报告已导出到:\n{output_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")
```

重构后：
```python
def _export_report(self):
    output_path, _ = QFileDialog.getSaveFileName(
        self, "导出校验报告", f"断面校验报告_{datetime.now().strftime('%Y%m%d')}.xlsx",
        "Excel文件 (*.xlsx)"
    )
    if output_path:
        try:
            self.service.export_report(output_path)
            QMessageBox.information(self, "完成", f"校验报告已导出到:\n{output_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")
```

**Step 8: 重构 `_export_anomaly_html` 方法**

原来：
```python
def _export_anomaly_html(self):
    anomaly_count = self.service.get_stats().get("anomaly_count", 0)
    error_count = self.service.get_stats().get("validation_error_count", 0)
    if anomaly_count == 0 and error_count == 0:
        QMessageBox.information(self, "提示", "当前没有异常断面或校验错误断面")
        return
    output_path, _ = QFileDialog.getSaveFileName(...)
    if output_path:
        try:
            result = self.service.export_anomaly_html(output_path)
            if result:
                QMessageBox.information(self, "完成", f"异常断面HTML已导出到:\n{output_path}")
                os.startfile(output_path)
            else:
                QMessageBox.information(self, "提示", "没有异常断面数据")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")
```

重构后（逻辑不变，只是 `self.service` 类型变了）：
```python
def _export_anomaly_html(self):
    stats = self.service.get_stats()
    anomaly_count = stats.get("anomaly_count", 0)
    error_count = stats.get("validation_error_count", 0)
    if anomaly_count == 0 and error_count == 0:
        QMessageBox.information(self, "提示", "当前没有异常断面或校验错误断面")
        return
    output_path, _ = QFileDialog.getSaveFileName(
        self, "导出异常断面HTML", f"异常断面汇总_{datetime.now().strftime('%Y%m%d')}.html",
        "HTML文件 (*.html)"
    )
    if output_path:
        try:
            result = self.service.export_anomaly_html(output_path)
            if result:
                QMessageBox.information(self, "完成", f"异常断面HTML已导出到:\n{output_path}")
                os.startfile(output_path)
            else:
                QMessageBox.information(self, "提示", "没有异常断面数据")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")
```

**Step 9: 重构 `_preview_excel` 方法**

原来：
```python
def _preview_excel(self):
    if not self._current_section_key:
        QMessageBox.warning(self, "警告", "请先选择一个断面")
        return
    sec = self.service.get_section_detail(self._current_section_key)
    if not sec:
        return
    source_file = sec.get("source_file", "")
    sheet_name = sec.get("sheet_name", "")
    if not source_file or not os.path.exists(source_file):
        QMessageBox.warning(self, "警告", "原始Excel文件不存在")
        return
    dialog = ExcelPreviewDialog(source_file, sheet_name, self)
    dialog.show()
```

重构后：
```python
def _preview_excel(self):
    if not self._current_section_key:
        QMessageBox.warning(self, "警告", "请先选择一个断面")
        return
    info = self.service.get_excel_preview_info(self._current_section_key)
    if not info:
        return
    source_file = info["source_file"]
    sheet_name = info["sheet_name"]
    if not source_file or not os.path.exists(source_file):
        QMessageBox.warning(self, "警告", "原始Excel文件不存在")
        return
    dialog = ExcelPreviewDialog(source_file, sheet_name, self)
    dialog.show()
```

**Step 10: 重构 `_on_keywords_changed` 方法**

原来：
```python
def _on_keywords_changed(self, keywords):
    self.log_message.emit(f"特征点关键词已更新: {', '.join(keywords)}")
    self.service.recalculate_sections()
    self._refresh_tree()
    self._update_stats(self.service.get_stats())
    if self._current_section_key:
        self._load_section_detail(self._current_section_key)
```

重构后（`self.service` 现在是 `SectionCheckService`，方法委托到 `chart_service`）：
```python
def _on_keywords_changed(self, keywords):
    self.log_message.emit(f"特征点关键词已更新: {', '.join(keywords)}")
    self.service.recalculate_sections()
    self._refresh_tree()
    self._update_stats(self.service.get_stats())
    if self._current_section_key:
        self._load_section_detail(self._current_section_key)
```

**Step 11: 重构 `_refresh_tree` 方法**

原来中 `self.service.get_tree_data()` 和 `self.service.get_section_detail()` 的调用不变，因为 `SectionCheckService` 委托了这些方法。

**Step 12: 清理 imports**

删除不再需要的 imports：
- `import tempfile`（移到 service 层）
- `from services.section_chart_service import SectionChartService, get_feature_keywords`（改为 `from services.section_check_service import SectionCheckService`）

保留的 imports：
```python
import json
import os
from datetime import datetime
from PySide6.QtWidgets import (...)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QColor
from services.section_check_service import SectionCheckService
from core.theme_manager import get_theme_manager
from core.effects_manager import StaggerEntrance, TabFadeTransition, ButtonGlowHelper
from ui.dialogs.log_dialog import LogDialog
from ui.dialogs.excel_preview_dialog import ExcelPreviewDialog
from ui.dialogs.feature_keywords_dialog import FeatureKeywordsDialog
```

注意：`json` 仍在 `_fill_issues_table` 中使用（`json.dumps(ad, ensure_ascii=False)`），所以保留。`QThread` 和 `Signal` 不再直接使用（`LoadDataThread` 已移走），但 `Signal` 仍在 `SectionCheckPage` 的类定义中使用（`log_message = Signal(str)`），所以保留 `Signal`，删除 `QThread` 和 `Slot`。

---

## Task 5: 更新 `main_window.py` 的 import

**Files:**
- Modify: `ui/main_window.py`

**Step 1: 确认 import 路径**

`main_window.py` 第26行：
```python
from ui.section_check_page import SectionCheckPage
```

这个 import 不需要改变，因为 `SectionCheckPage` 类仍然在 `ui/section_check_page.py` 中定义。

---

## Task 6: 验证和测试

**Step 1: 运行应用验证**

Run: `cd d:\github\空间数据检查桌面版-主题-design && python -c "from ui.section_check_page import SectionCheckPage; print('UI import OK')"`

**Step 2: 验证 service 层**

Run: `cd d:\github\空间数据检查桌面版-主题-design && python -c "from services.section_check_service import SectionCheckService; s = SectionCheckService(); print('Service init OK')"`

**Step 3: 验证 HTML builder**

Run: `cd d:\github\空间数据检查桌面版-主题-design && python -c "from services.section_html_builder import generate_chart_html; print('HTML builder OK')"`

---

## 重构后的文件结构

```
services/
├── __init__.py                    # 添加 SectionCheckService 导出
├── check_service.py               # 不变
├── filter_service.py              # 不变
├── section_chart_service.py       # 不变（底层数据服务）
├── section_check_service.py       # 新增（业务逻辑层，封装 SectionChartService）
└── section_html_builder.py        # 新增（HTML 生成逻辑）

ui/
├── section_check_page.py          # 精简（仅 UI 展示 + 事件转发）
└── main_window.py                 # 不变
```

## 重构前后对比

| 指标 | 重构前 | 重构后 |
|------|--------|--------|
| section_check_page.py 行数 | ~1144 | ~750 |
| 业务逻辑位置 | 混在 UI 中 | 独立 service 层 |
| HTML 生成逻辑 | 混在 UI 文件中 | 独立 html_builder 模块 |
| SectionChartService 使用 | UI 直接调用 | 通过 SectionCheckService 间接调用 |
| LoadDataThread | 定义在 UI 文件中 | 定义在 service 层 |
