# UI 重新设计：现代极简 + 数据优先

## Context

当前 PySide6 桌面应用"风险隐患调查与影响分析成果审核小工具"使用传统的 QGroupBox 表单布局、emoji 图标、行背景着色的表格状态显示。整体视觉偏"重"，缺乏现代数据工具的设计感。本次重新设计采用 Linear/Notion 风格的极简数据优先设计，在 **不改变现有功能、信号接口、公共 API** 的前提下，对 UI 组件进行全面重构。

**技术约束**: 纯 PySide6 + QSS，不使用 Web 嵌入。保持 light/dark/qwen 三主题系统。

## 设计原则
- 去除 QGroupBox → 无边框卡片 (QFrame + border-radius + 微阴影)
- 去除 emoji → Unicode 几何符号 (◆ ■ ▲ ○)
- 表格行背景着色 → 状态徽章 (pill badge)
- 空表格 → 空状态提示
- 扁平按钮 → 减少渐变，实心色块
- Tab 选中 → 底部高亮线代替填充色块
- 新增：页面标题区 + 统计卡片

## 文件改动清单

| 文件 | 改动量 | 说明 |
|------|--------|------|
| `core/theme_manager.py` | 大 | 新增配色 token、重写 QSS、添加 badge/card/stat 样式 |
| `ui/pages/check_page.py` | 大 | 布局重构、统计卡片、徽章、空状态 |
| `ui/report_page.py` | 大 | 同上 |
| `ui/components/filter_bar.py` | 中 | 去标签、更简洁 |
| `ui/components/ant_menu.py` | 小 | 替换 emoji 为几何符号 |
| `ui/components/dock_bar.py` | 小 | 替换 emoji 为几何符号 |
| `core/effects_manager.py` | 小 | 进度条变细适配 |
| `ui/main_window.py` | 小 | 边距微调 |

## 实施步骤（分两阶段并行）

### Phase 1：基础组件（4 个 Agent 并行）

#### Agent A: 主题系统重写 (`core/theme_manager.py`)
- 在 LIGHT_THEME / DARK_THEME / QWEN_THEME 中新增配色 token：
  - `badge_pass_bg`, `badge_pass_text`, `badge_fail_bg`, `badge_fail_text`
  - `card_bg`, `card_border`, `card_radius`（已有，复用）
  - `stat_card_bg`, `stat_card_border`, `stat_number_color`, `stat_label_color`
  - `empty_state_color`, `empty_state_icon_color`
  - `header_text_primary`, `header_text_secondary`
  - `tab_underline_color`
- 重写 `_generate_stylesheet()`:
  - **QGroupBox**: 改为扁平卡片风格（无标题、圆角、细边框、无渐变）
  - **QPushButton**: 主按钮用实心色（非渐变），仅"开始检查"保留微渐变
  - **QProgressBar**: 高度 8px，更细更精致
  - **QTabBar**: 下划线选中态（类似 Linear），非填充色块
  - **QTableWidget**: 去掉交替行色，表头仅底部边框
  - **新增 #badgePass / #badgeFail 样式**（药丸形状，22px 高，圆角 11px）
  - **新增 .statCard 样式**（统计卡片）
  - **新增 .sectionHeaderLg / .sectionHeaderMd 样式**（页面标题层级）
  - **新增 #emptyState 样式**（空状态提示）
- 更新 `get_inline_style()` 返回 badge 样式

#### Agent B: 侧边栏图标替换 (`ui/components/ant_menu.py` + `ui/components/dock_bar.py`)
- `ant_menu.py`:
  - MENU_CONFIG 中 emoji → 几何符号：
    - `check_config`: `\u25c6` (◆ 菱形) — 数据检查
    - `report`: `\u25a0` (■ 方形) — 报表
    - `shp_format`: `\u2699` (⚙ 齿轮) — 格式化
  - COLLAPSED_ICONS 同步替换
  - 标题 `"\U0001f30f 审核汇集"` → `"◆ 审核汇集"`
  - 主题按钮 `"\u2699\ufe0f"` → `"⚙"`
- `dock_bar.py`:
  - NAV_ITEMS 中 emoji 同步替换
  - 标题和主题按钮 emoji 同步替换

#### Agent C: 筛选栏重构 (`ui/components/filter_bar.py`)
- 去掉 "筛选:" 标签
- 更紧凑的布局、更小的间距
- 状态筛选改为更紧凑的 pill 样式（通过 QSS）
- 保持公开 API 不变：`filter_changed` 信号、`clear_requested` 信号、`get_filter_conditions()` 方法

#### Agent D: 效果管理器更新 (`core/effects_manager.py`)
- ShimmerProgress 适配更细的进度条（8px 高度）
- 确认 ShadowHelper 的卡片阴影适合新设计

### Phase 2：页面重构（2 个 Agent 并行）

#### Agent E: CheckPage 重构 (`ui/pages/check_page.py`)
- **页面标题区**: 顶部添加 "空间数据检查" 大标题 (sectionHeaderLg)
- **替换 QGroupBox**: 改为 QFrame(objectName="card")，标题作为独立 QLabel 放在卡片上方
- **统计卡片栏**: 在 Tab 上方添加 4 个统计卡片（文件总数 / 通过 / 不通过 / 通过率），初始显示 "--"，检查完成后更新
- **进度条**: 高度改为 8px
- **表格状态徽章**: 所有 `_update_*_table()` 方法中，"验证状态" / "状态" 列改用 `setCellWidget` 放置 QLabel badge（#badgePass / #badgeFail），不再整行着色
- **空状态**: 初始化时显示空状态提示，加载数据后移除
- **表格样式**: `setAlternatingRowColors(False)`
- **保持所有信号和公共 API 不变**

#### Agent F: ReportPage 重构 (`ui/report_page.py`)
- 同上处理：页面标题、卡片化、统计卡片、徽章、空状态
- ValidationDialog 和 FieldMappingDialog 也做卡片化处理（同一个文件内的内部类）
- **保持所有现有方法和行为不变**

### Phase 3：收尾
- `ui/main_window.py`: 内容区边距微调（从 20px 改为 24px，配合新设计节奏）

## 关键实现模式

### 徽章单元格
```python
if field in ('验证状态', '状态'):
    badge = QLabel("通过" if status == "通过" else "不通过")
    badge.setObjectName("badgePass" if status == "通过" else "badgeFail")
    badge.setAlignment(Qt.AlignCenter)
    badge.setFixedHeight(22)
    table.setCellWidget(row, col, badge)
```

### 卡片容器
```python
header = QLabel("检查配置")
header.setObjectName("sectionHeaderMd")
layout.addWidget(header)

card = QFrame()
card.setObjectName("card")
card_layout = QVBoxLayout(card)
# ... 添加内容
layout.addWidget(card)
```

## 验证方式
1. 运行 `python main.py` 确认应用能正常启动
2. 切换三个主题（亮/暗/Qwen）确认样式正确
3. 侧边栏折叠/展开确认图标正常
4. 执行一次数据检查，确认：
   - 统计卡片更新
   - 表格显示徽章而非行背景
   - 空状态正确显示/消失
5. 筛选功能正常工作
6. 报表页面加载数据、校验功能正常
