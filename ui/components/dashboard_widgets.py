# -*- coding: utf-8 -*-
"""
Dashboard页面专用组件 - 兼容性重导出模块

原始单文件已按功能域拆分为以下模块：
  - dashboard_constants.py  : 状态常量与映射
  - dashboard_indicators.py : 状态指示器基础组件 (StatusRingWidget, DotIndicator, ChevronIcon, ClickableHeader)
  - dashboard_charts.py     : 统计图表组件 (StatNumberCard, StatMetricCard, HealthScoreGauge, HorizontalBarChart, MiniDonutWidget)
  - dashboard_cards.py      : 检查卡片与面板 (CollapsibleCard, CollapsibleCardsContainer, CheckCategoryCard, CheckStatusPanel, CheckProgressPanel, HorizontalSwipeCards)
  - dashboard_spatial.py    : 空间数据与照片匹配 (SpatialLayerCard, SpatialResultGrid, PhotoMatchDashboard)
  - dashboard_cross.py      : 交叉检查 (CrossCheckTimeline, CrossIssueItem, CrossCheckListPanel)

本文件保留所有旧导入路径的兼容性，新代码请直接从子模块导入。
"""

from .dashboard_constants import (
    STATUS_BADGE_MAP,
    CHECK_CARD_BADGE_MAP,
    STATUS_RING_COLORS,
    STATUS_ICONS,
    STATUS_TEXTS,
)

from .dashboard_indicators import (
    ClickableHeader,
    ChevronIcon,
    DotIndicator,
    StatusRingWidget,
)

from .dashboard_charts import (
    StatNumberCard,
    StatMetricCard,
    HealthScoreGauge,
    HorizontalBarChart,
    MiniDonutWidget,
)

from .dashboard_cards import (
    CollapsibleCard,
    CollapsibleCardsContainer,
    CheckCategoryCard,
    CheckStatusPanel,
    CheckProgressPanel,
    HorizontalSwipeCards,
)

from .dashboard_spatial import (
    SpatialLayerCard,
    SpatialResultGrid,
    PhotoMatchDashboard,
)

from .dashboard_cross import (
    CrossCheckTimeline,
    CrossIssueItem,
    CrossCheckListPanel,
)

__all__ = [
    'STATUS_BADGE_MAP', 'CHECK_CARD_BADGE_MAP', 'STATUS_RING_COLORS', 'STATUS_ICONS', 'STATUS_TEXTS',
    'ClickableHeader', 'ChevronIcon', 'DotIndicator', 'StatusRingWidget',
    'StatNumberCard', 'StatMetricCard', 'HealthScoreGauge', 'HorizontalBarChart', 'MiniDonutWidget',
    'CollapsibleCard', 'CollapsibleCardsContainer', 'CheckCategoryCard', 'CheckStatusPanel',
    'CheckProgressPanel', 'HorizontalSwipeCards',
    'SpatialLayerCard', 'SpatialResultGrid', 'PhotoMatchDashboard',
    'CrossCheckTimeline', 'CrossIssueItem', 'CrossCheckListPanel',
]
