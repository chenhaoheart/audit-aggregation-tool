# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Signal
from ui.components.dashboard_widgets import CheckStatusPanel, CrossCheckTimeline


class DashboardChecksGrid(QFrame):

    check_card_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 18, 12, 18)

        section_title = QLabel("\U0001f50d 检查概览")
        section_title.setObjectName("sectionHeaderSm")
        layout.addWidget(section_title)

        grid = QFrame()
        grid.setObjectName("cardInnerPanel")
        grid_layout = QVBoxLayout(grid)
        grid_layout.setSpacing(10)
        grid_layout.setContentsMargins(2, 4, 2, 4)

        self.category_cards = {}
        categories = [
            ("fubiao", "\ud83d\udccb", "附表检查", "字段完整性校验"),
            ("spatial", "\ud83d\uddfa\ufe0f", "空间数据", "SHP图层属性校验"),
            ("section", "\ud83d\udcd0", "断面数据", "测量数据格式校验"),
            ("photo", "\ud83d\udcf7", "照片匹配", "照片与附表一致性"),
            ("cross", "\ud83d\udd17", "交叉校验", "多源数据一致性验证"),
        ]

        from PySide6.QtWidgets import QHBoxLayout
        grid_row = QHBoxLayout()
        grid_row.setSpacing(10)

        for key, icon, title, sub in categories:
            panel = CheckStatusPanel(key, f"{icon} {title}", sub)
            panel.clicked.connect(self.check_card_clicked.emit)
            grid_row.addWidget(panel)
            self.category_cards[key] = panel

        grid_layout.addLayout(grid_row)
        layout.addWidget(grid)

        self.cross_timeline = CrossCheckTimeline()
        self.cross_timeline.setVisible(False)
        layout.addWidget(self.cross_timeline)

    def update_category_cards(self, data: dict):
        fb = data.get('fubiao_check', {})
        sp = data.get('spatial_check', {})
        sec = data.get('section_check', {})
        ph = data.get('photo_check', {})
        cr = data.get('cross_check', {})

        fb_err = len(fb.get('errors', []))
        fb_status = fb.get('status', 'pending')
        self.category_cards["fubiao"].update_status(
            fb_status,
            f"{fb_err} \u4e2a\u95ee\u9898" if fb_err > 0 else "\u6821\u9a8c\u901a\u8fc7")

        sp_invalid = sum(1 for r in sp.get('results', []) if r.get('status') != '\u901a\u8fc7')
        sp_status = sp.get('status', 'pending')
        self.category_cards["spatial"].update_status(
            sp_status,
            f"{sp_invalid}/{len(sp.get('results', []))} \u56fe\u5c42\u5f02\u5e38" if sp_invalid > 0 else "\u6821\u9a8c\u901a\u8fc7")

        sec_stats = sec.get('stats', {})
        sec_err = sec_stats.get('validation_error_count', 0)
        sec_anom = sec_stats.get('anomaly_count', 0)
        sec_detail = f"\u9519\u8bef{sec_err} \u5f02\u5e38{sec_anom}" if (sec_err or sec_anom) else "\u6821\u9a8c\u901a\u8fc7"
        sec_status = sec.get('status', 'pending')
        self.category_cards["section"].update_status(sec_status, sec_detail)

        ph_summary = ph.get('match_result', {}).get('summary', {})
        ph_unmatched = ph_summary.get('fubiao2_unmatched', 0) + ph_summary.get('fubiao3_unmatched', 0)
        ph_status = ph.get('status', 'pending')
        self.category_cards["photo"].update_status(
            ph_status,
            f"{ph_unmatched}\u9879\u672a\u5339\u914d" if ph_unmatched > 0 else "\u5168\u90e8\u5339\u914d")

        cr_err = len(cr.get('errors', []))
        cr_warn = len(cr.get('warnings', []))
        cr_detail = f"\u9519\u8bef{cr_err} \u8b66\u544a{cr_warn}" if (cr_err or cr_warn) else "\u6821\u9a8c\u901a\u8fc7"
        cr_status = cr.get('status', 'pending')
        self.category_cards["cross"].update_status(cr_status, cr_detail)

        cross_items = cr.get('items', [])
        if cross_items:
            self.cross_timeline.set_items(cross_items)
            self.cross_timeline.setVisible(True)

    def reset(self):
        for card in self.category_cards.values():
            card.update_status('pending')
        self.cross_timeline.setVisible(False)
