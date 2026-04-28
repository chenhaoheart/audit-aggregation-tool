# -*- coding: utf-8 -*-
"""Generate QSS for page-level components: toolbar, photo cards, badges, chips."""
from typing import Dict


def generate_pages_stylesheet(theme: Dict[str, str]) -> str:
    surface_1 = theme.get('surface_1', theme.get('card_bg', '#ffffff'))
    surface_2 = theme.get('surface_2', theme.get('card_bg', '#f5f5f5'))
    surface_3 = theme.get('surface_3', theme.get('card_bg', '#eeeeee'))
    text_muted = theme.get('text_muted', theme.get('text_secondary', '#94a3b8'))
    text_hint = theme.get('text_hint', theme.get('text_secondary', '#cbd5e1'))
    border_subtle = theme.get('border_subtle', theme.get('card_border', '#e2e8f0'))
    toolbar_bg = theme.get('toolbar_bg', theme.get('card_bg', '#ffffff'))
    toolbar_border = theme.get('toolbar_border', theme.get('card_border', '#e2e8f0'))
    overlay_bg = theme.get('overlay_bg', 'rgba(0,0,0,0.6)')
    photo_card_bg = theme.get('photo_card_bg', theme.get('card_bg', '#ffffff'))
    photo_card_border = theme.get('photo_card_border', theme.get('card_border', '#e2e8f0'))
    photo_card_hover_border = theme.get('photo_card_hover_border', theme.get('accent_color', '#6366f1'))
    badge_bg = theme.get('badge_bg', 'rgba(99,102,241,0.10)')
    badge_text = theme.get('badge_text', theme.get('accent_color', '#6366f1'))
    chip_bg = theme.get('chip_bg', 'rgba(99,102,241,0.08)')
    chip_border = theme.get('chip_border', theme.get('card_border', '#e2e8f0'))
    chip_text = theme.get('chip_text', theme.get('accent_color', '#6366f1'))
    divider_color = theme.get('divider_color', theme.get('card_border', '#e2e8f0'))
    icon_muted = theme.get('icon_muted', theme.get('text_secondary', '#94a3b8'))
    icon_active = theme.get('icon_active', theme.get('accent_color', '#6366f1'))
    accent = theme.get('accent_color', '#6366f1')

    return f"""
/* ========== Page Toolbar ========== */
QFrame#pageToolbar {{
    background: {toolbar_bg};
    border-bottom: 1px solid {toolbar_border};
    padding: 8px 16px;
}}

QLabel#toolbarTitle {{
    font-size: 20px;
    font-weight: 700;
    color: {theme['text_primary']};
}}

QLabel#toolbarSubtitle {{
    font-size: 12px;
    color: {text_muted};
}}

QPushButton#toolbarBtn {{
    background: transparent;
    color: {text_muted};
    border: 1px solid {border_subtle};
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 13px;
}}

QPushButton#toolbarBtn:hover {{
    background: {surface_2};
    color: {theme['text_primary']};
    border-color: {accent};
}}

QPushButton#toolbarBtnPrimary {{
    background: {accent};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 13px;
    font-weight: 600;
}}

QPushButton#toolbarBtnPrimary:hover {{
    background: {theme.get('glow_primary', accent)};
}}

/* ========== Photo Gallery ========== */
QFrame#photoCard {{
    background: {photo_card_bg};
    border: 1px solid {photo_card_border};
    border-radius: 12px;
    padding: 0;
}}

QFrame#photoCard:hover {{
    border-color: {photo_card_hover_border};
}}

QLabel#photoLabel {{
    background: {surface_3};
    border: none;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    padding: 0;
    margin: 0;
}}

QLabel#photoName {{
    font-size: 13px;
    font-weight: 600;
    color: {theme['text_primary']};
    padding: 8px 10px 2px 10px;
}}

QLabel#photoMeta {{
    font-size: 11px;
    color: {text_muted};
    padding: 0px 10px 8px 10px;
}}

QLabel#photoStatus {{
    font-size: 11px;
    color: {text_muted};
    padding: 0px 10px 6px 10px;
}}

QFrame#photoToolbar {{
    background: {toolbar_bg};
    border: none;
    border-top: 1px solid {divider_color};
    border-bottom-left-radius: 12px;
    border-bottom-right-radius: 12px;
    padding: 4px 8px;
}}

QPushButton#photoActionBtn {{
    background: transparent;
    color: {icon_muted};
    border: none;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
}}

QPushButton#photoActionBtn:hover {{
    background: {surface_2};
    color: {icon_active};
}}

QPushButton#photoViewBtn {{
    background: transparent;
    color: {icon_muted};
    border: none;
    border-radius: 6px;
    padding: 4px;
    font-size: 16px;
}}

QPushButton#photoViewBtn:hover {{
    color: {icon_active};
    background: {surface_2};
}}

QPushButton#photoViewBtn:checked {{
    color: {accent};
    background: {badge_bg};
}}

QFrame#galleryGrid {{
    background: transparent;
    border: none;
}}

QLabel#galleryEmpty {{
    font-size: 16px;
    color: {text_hint};
    padding: 60px;
}}

QLabel#galleryEmptyIcon {{
    font-size: 48px;
    color: {text_hint};
}}

/* ========== Badge & Chip ========== */
QLabel#badge {{
    background: {badge_bg};
    color: {badge_text};
    border: none;
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}}

QLabel#badgeSuccess {{
    background: rgba(34,197,94,0.12);
    color: #16a34a;
    border: none;
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}}

QLabel#badgeWarning {{
    background: rgba(245,158,11,0.12);
    color: #d97706;
    border: none;
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}}

QLabel#badgeError {{
    background: rgba(239,68,68,0.12);
    color: #dc2626;
    border: none;
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}}

QFrame#chip {{
    background: {chip_bg};
    color: {chip_text};
    border: 1px solid {chip_border};
    border-radius: 14px;
    padding: 4px 14px;
    font-size: 12px;
}}

QPushButton#chipBtn {{
    background: {chip_bg};
    color: {chip_text};
    border: 1px solid {chip_border};
    border-radius: 14px;
    padding: 4px 14px;
    font-size: 12px;
}}

QPushButton#chipBtn:hover {{
    background: {badge_bg};
    border-color: {accent};
}}

QPushButton#chipBtn:checked {{
    background: {accent};
    color: white;
    border-color: {accent};
}}

/* ========== Section Divider ========== */
QFrame#sectionDivider {{
    background: {divider_color};
    max-height: 1px;
    margin: 8px 0;
}}

QLabel#sectionTitle {{
    font-size: 13px;
    font-weight: 600;
    color: {text_muted};
    padding: 4px 0;
}}

/* ========== Stats Card ========== */
QFrame#statsCard {{
    background: {photo_card_bg};
    border: 1px solid {photo_card_border};
    border-radius: 12px;
    padding: 16px;
}}

QLabel#statsValue {{
    font-size: 28px;
    font-weight: 700;
    color: {theme['text_primary']};
}}

QLabel#statsLabel {{
    font-size: 12px;
    color: {text_muted};
}}

QLabel#statsIcon {{
    font-size: 24px;
    color: {icon_active};
}}

/* ========== Overlay ========== */
QFrame#overlay {{
    background: {overlay_bg};
    border-radius: 12px;
}}

QLabel#overlayTitle {{
    font-size: 16px;
    font-weight: 600;
    color: white;
}}

QLabel#overlayText {{
    font-size: 13px;
    color: rgba(255,255,255,0.80);
}}

/* ========== Search Bar ========== */
QFrame#searchBar {{
    background: {surface_1};
    border: 1px solid {border_subtle};
    border-radius: 10px;
    padding: 4px;
}}

QFrame#searchBar:focus {{
    border-color: {accent};
}}

QLineEdit#searchInput {{
    background: transparent;
    border: none;
    color: {theme['text_primary']};
    padding: 6px 10px;
    font-size: 13px;
}}

QLineEdit#searchInput::placeholder {{
    color: {text_hint};
}}

/* ========== Filter Row ========== */
QFrame#filterRow {{
    background: transparent;
    border: none;
    padding: 4px 0;
}}

/* ========== Image Viewer Dialog ========== */
QFrame#imageViewer {{
    background: {theme.get('content_bg', '#1a1a2e')};
    border-radius: 12px;
}}

QLabel#imageViewerLabel {{
    background: transparent;
    border: none;
}}

QPushButton#imageViewerClose {{
    background: rgba(255,255,255,0.10);
    color: white;
    border: none;
    border-radius: 20px;
    padding: 8px;
    font-size: 18px;
    min-width: 36px;
    max-width: 36px;
    min-height: 36px;
    max-height: 36px;
}}

QPushButton#imageViewerClose:hover {{
    background: rgba(255,255,255,0.20);
}}

/* ========== Check Page Specific ========== */
QFrame#checkCard {{
    background: {photo_card_bg};
    border: 1px solid {photo_card_border};
    border-radius: 12px;
    padding: 20px;
}}

QFrame#checkCard:hover {{
    border-color: {photo_card_hover_border};
}}

QLabel#checkTitle {{
    font-size: 15px;
    font-weight: 600;
    color: {theme['text_primary']};
}}

QLabel#checkDesc {{
    font-size: 12px;
    color: {text_muted};
}}

QPushButton#checkStartBtn {{
    background: {accent};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: 600;
}}

QPushButton#checkStartBtn:hover {{
    background: {theme.get('glow_primary', accent)};
}}

/* ========== Progress Bar ========== */
QProgressBar#themeProgressBar {{
    background: {surface_2};
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
}}

QProgressBar#themeProgressBar::chunk {{
    background: {accent};
    border-radius: 4px;
}}

/* ========== Tab Bar (Page Level) ========== */
QTabBar#pageTabBar {{
    background: transparent;
}}

QTabBar#pageTabBar::tab {{
    background: transparent;
    color: {text_muted};
    border: none;
    border-bottom: 2px solid transparent;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}}

QTabBar#pageTabBar::tab:hover {{
    color: {theme['text_primary']};
    background: {surface_1};
    border-radius: 6px 6px 0 0;
}}

QTabBar#pageTabBar::tab:selected {{
    color: {accent};
    border-bottom: 2px solid {accent};
    font-weight: 600;
}}

/* ========== Dashboard Page ========== */
QScrollArea#dashboardScrollArea {{
    background: transparent;
    border: none;
}}

QTableWidget#dashboardTable {{
    background: {theme.get('table_bg', 'transparent')};
    border: 1px solid {border_subtle};
    border-radius: 8px;
    gridline-color: {theme.get('table_grid', 'transparent')};
}}

QTableWidget#dashboardTable::item {{
    padding: 6px;
}}

QTableWidget#dashboardTable::item:selected {{
    background: {theme.get('table_selection_bg', 'rgba(59,130,246,0.15)')};
}}

QTableWidget#dashboardTable QHeaderView::section {{
    background: {theme.get('table_header_bg', 'rgba(0,0,0,0.03)')};
    padding: 8px;
    border: none;
    font-weight: 600;
}}
"""
