# -*- coding: utf-8 -*-
"""Generate QSS for cards with frosted crystal glass effect."""
from typing import Dict


def generate_cards_stylesheet(theme: Dict[str, str]) -> str:
    badge_warn_bg = theme.get('badge_warn_bg', 'rgba(245,158,11,0.12)')
    badge_warn_text = theme.get('badge_warn_text', '#d97706')
    badge_warn_border = theme.get('badge_warn_border', 'rgba(245,158,11,0.25)')
    badge_pending_bg = theme.get('badge_pending_bg', 'rgba(148,163,184,0.10)')
    badge_pending_text = theme.get('badge_pending_text', '#64748b')
    badge_pending_border = theme.get('badge_pending_border', 'rgba(148,163,184,0.20)')
    badge_running_bg = theme.get('badge_running_bg', 'rgba(99,102,241,0.10)')
    badge_running_text = theme.get('badge_running_text', '#4338ca')
    badge_running_border = theme.get('badge_running_border', 'rgba(99,102,241,0.25)')
    gauge_score_high = theme.get('gauge_score_high', '#22c55e')
    gauge_score_mid = theme.get('gauge_score_mid', '#f59e0b')
    gauge_score_low = theme.get('gauge_score_low', '#ef4444')

    return f"""
/* ========== 分组框 - 毛玻璃卡片 ========== */
QGroupBox {{
    font-size: 13px;
    font-weight: 600;
    color: {theme['text_secondary']};
    border: 1px solid {theme['card_border']};
    border-radius: 16px;
    margin-top: 18px;
    padding: 24px 20px;
    background: {theme['card_bg']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 14px;
    color: {theme['text_primary']};
    background: transparent;
    font-weight: 600;
    font-size: 14px;
}}

/* ========== 卡片 - 毛玻璃效果 ========== */
QFrame#card {{
    background: {theme['card_bg']};
    border: 1px solid {theme['card_border']};
    border-radius: 16px;
    padding: 0;
}}

/* 卡片内部面板 / Splitter —— 透明背景继承父级 */
QWidget#cardInnerPanel,
QSplitter#cardInnerPanel {{
    background: transparent;
    border: none;
}}

QSplitter#mainSplitter {{
    background: transparent;
    border: none;
    spacing: 0;
}}

QSplitter#mainSplitter::handle {{
    background: transparent;
    width: 0;
}}

/* 结果Tab —— 毛玻璃卡片 */
QTabWidget#resultTabs {{
    background: {theme['card_bg']};
    border: 1px solid {theme['card_border']};
    border-radius: 16px;
}}

QTabWidget#resultTabs::pane {{
    border: none;
    background: transparent;
    margin: 0;
    padding: 0;
}}

QTabWidget#resultTabs QTabBar::tab {{
    background: transparent;
    color: {theme['text_secondary']};
    border: none;
    padding: 12px 28px;
    margin-right: 4px;
    font-size: 14px;
    font-weight: 500;
}}

QTabWidget#resultTabs QTabBar::tab:selected {{
    color: {theme['accent_color']};
    border-bottom: 2px solid {theme['tab_underline_color']};
    font-weight: 600;
}}

QTabWidget#resultTabs QTabBar::tab:hover:!selected {{
    color: {theme['text_primary']};
    border-bottom: 2px solid {theme['tab_hover_bg']};
}}

/* ========== 统计卡片 - 琥珀色顶部条 ========== */
QFrame#statCard {{
    background: {theme['stat_card_bg']};
    border: 1px solid {theme['stat_card_border']};
    border-radius: 12px;
    padding: 14px 16px;
    min-width: 110px;
}}

QLabel#statNumber {{
    font-size: 22px;
    font-weight: 700;
    color: {theme['stat_number_color']};
    font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif;
}}

QLabel#statLabel {{
    font-size: 11px;
    font-weight: 500;
    color: {theme['stat_label_color']};
    letter-spacing: 0.3px;
}}

QLabel#emptyState {{
    color: {theme['empty_state_color']};
    font-size: 14px;
}}

/* ========== Dashboard 统计指标卡片 ========== */
QFrame#statMetricCard {{
    background: {theme['card_bg']};
    border: 1px solid {theme['card_border']};
    border-radius: 16px;
    min-height: 100px;
}}

QLabel#statMetricValue {{
    font-size: 32px;
    font-weight: 700;
    color: {theme['text_primary']};
    font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
}}

QLabel#statMetricLabel {{
    font-size: 11px;
    font-weight: 500;
    color: {theme['text_secondary']};
}}

QLabel#statMetricSub {{
    font-size: 9px;
    color: {theme['text_muted']};
}}

QFrame#statStatusBar {{
    background: {theme['accent_color']};
    border-radius: 2px;
}}

/* ========== Dashboard 检查状态面板 ========== */
QFrame#checkStatusPanel {{
    background: {theme['card_bg']};
    border: 1px solid {theme['card_border']};
    border-radius: 16px;
    min-height: 96px;
}}

QFrame#checkStatusPanel:hover {{
    border: 2px solid {theme['glow_primary']};
}}

QLabel#panelTitle {{
    font-size: 14px;
    font-weight: 600;
    color: {theme['text_primary']};
}}

QLabel#panelSubtitle {{
    font-size: 11px;
    color: {theme['text_secondary']};
}}

QLabel#panelDetail {{
    font-size: 10px;
    color: {theme['text_muted']};
}}

/* ========== Dashboard 检查分类卡片 ========== */
QFrame#checkCategoryCard {{
    background: {theme['card_bg']};
    border: 1px solid {theme['card_border']};
    border-radius: 14px;
    min-height: 120px;
}}

QFrame#checkCategoryCard:hover {{
    border: 2px solid {theme['glow_primary']};
}}

QLabel#checkCardTitle {{
    font-size: 15px;
    font-weight: 600;
    color: {theme['text_primary']};
}}

QLabel#checkCardDetail {{
    font-size: 11px;
    color: {theme['text_muted']};
}}

/* ========== Dashboard 进度面板 ========== */
QFrame#checkProgressPanel {{
    background: {theme['glass_bg']};
    border: 1px solid {theme['glass_border']};
    border-radius: 12px;
}}

QProgressBar#dashboardProgress {{
    background: {theme['progress_bg']};
    border: none;
    border-radius: 4px;
    height: 8px;
}}

QProgressBar#dashboardProgress::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {theme['progress_chunk_start']},
        stop:1 {theme['progress_chunk_end']});
    border-radius: 4px;
}}

QLabel#progressSection {{
    font-size: 12px;
    font-weight: 500;
    color: {theme['text_primary']};
}}

QLabel#progressPercent {{
    font-size: 11px;
    font-weight: 600;
    color: {theme['text_secondary']};
}}

/* ========== Dashboard 折叠卡片 ========== */
QFrame#collapsibleCard {{
    background: {theme['card_bg']};
    border: 1px solid {theme['card_border']};
    border-radius: 12px;
}}

QFrame#cardHeader {{
    background: {theme['surface_1']};
    border-radius: 12px;
    border-bottom-left-radius: 0;
    border-bottom-right-radius: 0;
}}

QLabel#cardTitle {{
    font-size: 14px;
    font-weight: 600;
    color: {theme['text_primary']};
}}

QLabel#cardIcon {{
    font-size: 18px;
}}

QWidget#cardContentWrapper {{
    background: transparent;
}}

QWidget#cardContent {{
    background: transparent;
}}

/* ========== Dashboard 状态徽章 ========== */
QLabel#statusBadge {{
    border-radius: 13px;
    padding: 4px 14px;
    font-size: 11px;
    font-weight: 600;
}}

QLabel#statusBadgePass {{
    background: {theme['badge_pass_bg']};
    color: {theme['badge_pass_text']};
    border: 1px solid {theme['badge_pass_border']};
    border-radius: 13px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}}

QLabel#statusBadgeFail {{
    background: {theme['badge_fail_bg']};
    color: {theme['badge_fail_text']};
    border: 1px solid {theme['badge_fail_border']};
    border-radius: 13px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}}

QLabel#statusBadgeWarn {{
    background: {badge_warn_bg};
    color: {badge_warn_text};
    border: 1px solid {badge_warn_border};
    border-radius: 13px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}}

QLabel#statusBadgePending {{
    background: {badge_pending_bg};
    color: {badge_pending_text};
    border: 1px solid {badge_pending_border};
    border-radius: 13px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}}

QLabel#statusBadgeRunning {{
    background: {badge_running_bg};
    color: {badge_running_text};
    border: 1px solid {badge_running_border};
    border-radius: 13px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}}

/* ========== Dashboard 检查分类卡片内徽章 ========== */
QLabel#checkCardBadgePass {{
    background: {theme['badge_pass_bg']};
    color: {theme['badge_pass_text']};
    border-radius: 12px;
    padding: 2px 14px;
    font-size: 11px;
    font-weight: 600;
}}

QLabel#checkCardBadgeFail {{
    background: {theme['badge_fail_bg']};
    color: {theme['badge_fail_text']};
    border-radius: 12px;
    padding: 2px 14px;
    font-size: 11px;
    font-weight: 600;
}}

QLabel#checkCardBadgeWarn {{
    background: {badge_warn_bg};
    color: {badge_warn_text};
    border-radius: 12px;
    padding: 2px 14px;
    font-size: 11px;
    font-weight: 600;
}}

QLabel#checkCardBadgePending {{
    background: {badge_pending_bg};
    color: {badge_pending_text};
    border-radius: 12px;
    padding: 2px 14px;
    font-size: 11px;
    font-weight: 600;
}}

QLabel#checkCardBadgeRunning {{
    background: {badge_running_bg};
    color: {badge_running_text};
    border-radius: 12px;
    padding: 2px 14px;
    font-size: 11px;
    font-weight: 600;
}}

/* ========== Dashboard 结果容器 ========== */
QFrame#resultsContainer {{
    background: transparent;
    border: none;
}}

/* ========== Dashboard 健康评分仪表盘容器 ========== */
QWidget#healthGaugeContainer {{
    background: transparent;
}}

/* ========== Dashboard 结果表格极简样式 ========== */
QTableWidget#minimalResultTable {{
    background: transparent;
    border: none;
    border-radius: 0;
    gridline-color: transparent;
}}

QTableWidget#minimalResultTable::item {{
    padding: 8px 12px;
    border-bottom: 1px solid {theme['divider_color']};
}}

QTableWidget#minimalResultTable::item:selected {{
    background: rgba(59,130,246,0.08);
}}

QTableWidget#minimalResultTable QHeaderView::section {{
    background: transparent;
    padding: 10px 12px;
    border: none;
    border-bottom: 2px solid {theme['divider_color']};
    font-weight: 600;
    color: {theme['text_primary']};
}}

/* ========== Dashboard 空间表格状态标签 ========== */
QLabel#badgePass {{
    background: {theme['badge_pass_bg']};
    color: {theme['badge_pass_text']};
    border-radius: 11px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}}

QLabel#badgeFail {{
    background: {theme['badge_fail_bg']};
    color: {theme['badge_fail_text']};
    border-radius: 11px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}}

/* ========== Dashboard 页面头部强调条 ========== */
QFrame#accentBar {{
    background: {theme['accent_color']};
    border-radius: 2px;
    max-width: 4px;
}}

/* ========== Dashboard 区段标题 ========== */
QLabel#sectionHeaderLg {{
    font-size: 20px;
    font-weight: 700;
    color: {theme['text_primary']};
}}

QLabel#sectionHeaderSm {{
    font-size: 14px;
    font-weight: 600;
    color: {theme['text_primary']};
}}

QLabel#pageSubtitle {{
    font-size: 12px;
    color: {theme['text_secondary']};
}}

QLabel#boldLabel {{
    font-size: 13px;
    font-weight: 600;
    color: {theme['text_primary']};
}}

/* ========== 空间数据图层卡片 ========== */
QFrame#spatialLayerCard {{
    background: {theme['card_bg']};
    border: 1px solid {theme['card_border']};
    border-radius: 10px;
}}

QLabel#layerCardName {{
    font-size: 12px;
    font-weight: 600;
    color: {theme['text_primary']};
}}

QLabel#layerStatText {{
    font-size: 10px;
    color: {theme['text_muted']};
}}

QLabel#layerStatValid {{
    font-size: 10px;
    color: {theme.get('success_text', '#22c55e')};
}}

QLabel#layerStatInvalid {{
    font-size: 10px;
    color: {theme.get('error_text', '#ef4444')};
}}

QLabel#efficiencyLabel {{
    font-size: 11px;
    font-weight: 700;
    color: {theme['text_secondary']};
}}

QLabel#efficiencyLabelPass {{
    font-size: 14px;
    font-weight: 700;
    color: {theme.get('success_text', '#22c55e')};
}}

QLabel#efficiencyLabelFail {{
    font-size: 14px;
    font-weight: 700;
    color: {theme.get('error_text', '#ef4444')};
}}

QWidget#spatialResultGrid {{
    background: transparent;
}}

/* ========== 照片匹配仪表板 ========== */
QWidget#photoMatchDashboard {{
    background: transparent;
}}

/* ========== 交叉检查问题列表 ========== */
QWidget#crossCheckListPanel {{
    background: transparent;
}}

QFrame#crossIssueItem {{
    background: {theme['surface_1']};
    border: 1px solid {theme['border_subtle']};
    border-radius: 8px;
}}

QFrame#crossIssueItem:hover {{
    border-color: {theme['accent_color']};
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {theme['surface_1']},
        stop:1 {theme['surface_2']});
}}

QFrame#issueIndicator {{
    border-top-left-radius: 8px;
    border-bottom-left-radius: 8px;
    background: {theme.get('error_text', '#ef4444')};
}}

QLabel#issueCategoryBadge {{
    font-size: 12px;
    font-weight: 600;
    color: {theme['accent_color']};
    padding: 2px 8px;
    border-radius: 8px;
    background: rgba(99,102,241,0.08);
}}

QLabel#issueDescText {{
    font-size: 13px;
    color: {theme['text_primary']};
    line-height: 1.3;
}}

QLabel#issueDetailText {{
    font-size: 11px;
    color: {theme['text_muted']};
    margin-top: 2px;
    line-height: 1.3;
}}

QLabel#issueChevron {{
    font-size: 11px;
    color: {theme['text_muted']};
}}

QLabel#crossErrorCount {{
    font-size: 11px;
    font-weight: 600;
    color: {theme.get('error_text', '#ef4444')};
    padding: 2px 10px;
    border-radius: 10px;
    background: rgba(239,68,68,0.08);
}}

QLabel#crossWarnCount {{
    font-size: 13px;
    font-weight: 600;
    color: {theme.get('warning_text', '#f59e0b')};
    padding: 2px 10px;
    border-radius: 10px;
    background: rgba(245,158,11,0.08);
}}

QScrollArea#crossItemsScrollArea {{
    background: transparent;
    border: none;
}}

QScrollArea#crossTimelineArea {{
    background: {theme['surface_1']};
    border: 1px solid {theme['border_subtle']};
    border-radius: 8px;
}}

QWidget#crossTimelineContent {{
    background: transparent;
}}

/* ========== Dashboard 横向滑动卡片 ========== */
QWidget#horizontalSwipeCards {{
    background: transparent;
    border: none;
}}

QFrame#swipeContentContainer {{
    background: {theme['card_bg']};
    border: 1px solid {theme['card_border']};
    border-radius: 12px;
}}

QStackedWidget#swipeContentStack {{
    background: transparent;
    border: none;
}}

QWidget#swipeCardContent {{
    background: transparent;
}}

QPushButton#swipeNavBtn {{
    background: {theme['surface_1']};
    border: 1px solid {theme['border_subtle']};
    color: {theme['text_secondary']};
    font-size: 16px;
    font-weight: 700;
    border-radius: 18px;
    min-width: 36px;
    max-width: 36px;
    min-height: 36px;
    max-height: 36px;
    padding: 0px;
}}

QPushButton#swipeNavBtn:hover {{
    background: {theme['surface_2']};
    color: {theme['accent_color']};
    border: 1px solid {theme['accent_color']};
}}

QPushButton#swipeNavBtn:disabled {{
    color: {theme['text_muted']};
    background: transparent;
    border: 1px solid {theme['border_subtle']};
}}

QPushButton#issueChevronBtn {{
    background: transparent;
    border: none;
    color: {theme['text_muted']};
    font-size: 12px;
    font-weight: bold;
    padding: 0px;
}}

QPushButton#issueChevronBtn:hover {{
    color: {theme['accent_color']};
    background: {theme.get('hover_glow', 'rgba(99,102,241,0.10)')};
    border-radius: 14px;
}}

QLabel#spatialBadgePass {{
    color: {theme.get('success_text', '#22c55e')};
    border-radius: 11px;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 10px;
}}

QLabel#spatialBadgeFail {{
    color: {theme.get('error_text', '#ef4444')};
    border-radius: 11px;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 10px;
}}

QLabel#spatialBadgeWarn {{
    color: {theme.get('warning_text', '#f59e0b')};
    border-radius: 11px;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 10px;
}}

QLabel#spatialBadgePending {{
    color: {theme['text_muted']};
    border-radius: 11px;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 10px;
}}

QFrame#swipeIndicatorBar {{
    background: transparent;
    border: none;
}}

QFrame#settingsSeparator {{
    background: {theme.get('border_subtle', 'rgba(128,128,128,0.2)')};
    max-height: 1px;
}}

QLabel#settingsFieldTitle {{
    font-size: 12px;
    font-weight: 600;
    color: {theme['text_secondary']};
}}

QLabel#settingsLabel {{
    font-size: 13px;
    font-weight: 500;
    border: none;
    background: transparent;
}}

QLabel#settingsOpacityValue {{
    font-size: 13px;
    font-weight: 500;
    border: none;
    background: transparent;
    min-width: 40px;
}}

QToolButton#settingsAddBtn {{
    font-size: 11px;
    padding: 2px 8px;
    border: none;
    background: transparent;
    color: {theme['accent_color']};
}}

QToolButton#settingsAddBtn:hover {{
    color: {theme.get('hover_accent', theme['accent_color'])};
    background: {theme.get('hover_glow', 'rgba(99,102,241,0.10)')};
}}

QToolButton#settingsDelBtn {{
    font-size: 12px;
    color: {theme.get('error_text', '#ef4444')};
    border: none;
    background: transparent;
}}

QToolButton#settingsDelBtn:hover {{
    background: {theme.get('error_bg', 'rgba(239,68,68,0.10)')};
    border-radius: 4px;
}}

QLabel#settingsStatusSuccess {{
    color: {theme.get('success_text', '#22c55e')};
    font-size: 13px;
}}

QLabel#settingsStatusWarning {{
    color: {theme.get('warning_text', '#f59e0b')};
    font-size: 13px;
}}
"""
