# -*- coding: utf-8 -*-
"""
Dashboard交叉检查组件
包含：CrossCheckTimeline, _CrossTimelineContent, CrossIssueItem, CrossCheckListPanel
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
    QSizePolicy, QPushButton
)
from PySide6.QtCore import Qt, Signal, QRectF, QPropertyAnimation, QEasingCurve, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QFont

from core.theme_manager import get_theme_manager


class _CrossTimelineContent(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []

    def set_items(self, items: list):
        self._items = items
        content_h = max(80, len(items) * 46 + 40)
        self.setFixedHeight(content_h)
        self.update()

    def paintEvent(self, event):
        if not self._items:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        theme = get_theme_manager().get_current_theme()

        line_x = 32
        line_top = 20

        error_color = QColor(theme.get('error_text', '#ef4444'))
        warn_color = QColor(theme.get('warning_text', '#f59e0b'))

        last_y = line_top + (len(self._items) - 1) * 46

        pen = QPen(QColor(theme.get('border_subtle', '#e5e7eb')), 2)
        painter.setPen(pen)
        painter.drawLine(line_x, line_top, line_x, last_y)

        y = line_top
        for item in self._items:
            level = item.get('level', '')
            is_error = level == 'error'
            dot_color = error_color if is_error else warn_color

            painter.setBrush(dot_color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(line_x, y), 6, 6)

            cat_text = item.get('category', '')
            desc_text = item.get('desc', '')

            font_cat = QFont("Microsoft YaHei UI", 10, QFont.Bold)
            painter.setFont(font_cat)
            cat_color = error_color if is_error else warn_color
            painter.setPen(cat_color)
            painter.drawText(line_x + 18, y - 4, cat_text)

            font_desc = QFont("Microsoft YaHei UI", 9)
            painter.setFont(font_desc)
            desc_color = QColor(theme.get('text_secondary', '#64748b'))
            painter.setPen(desc_color)
            max_w = self.width() - line_x - 24
            elided_desc = painter.fontMetrics().elidedText(desc_text, Qt.ElideRight, max_w)
            painter.drawText(line_x + 18, y + 14, elided_desc)

            y += 46

        painter.end()


class CrossCheckTimeline(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setObjectName("crossTimelineArea")
        self.setMinimumHeight(120)
        self.setMaximumHeight(280)

        self._content = _CrossTimelineContent()
        self._content.setObjectName("crossTimelineContent")
        self.setWidget(self._content)

    def set_items(self, items: list):
        self._content.set_items(items)


class CrossIssueItem(QFrame):
    clicked = Signal(dict)

    def __init__(self, item_data: dict, parent=None):
        super().__init__(parent)
        self._data = item_data
        self.setObjectName("crossIssueItem")
        self.setCursor(Qt.PointingHandCursor)
        self._expanded = False
        self._setup_ui()

    def _calc_base_height(self):
        if not hasattr(self, 'desc_label') or not self.desc_label:
            return 90
        fm = self.desc_label.fontMetrics()
        text = self.desc_label.text()
        label_width = self.desc_label.width() if self.desc_label.width() > 0 else 400
        text_rect = fm.boundingRect(0, 0, label_width, 16777215,
                                     Qt.TextWordWrap | Qt.AlignLeft, text)
        text_h = text_rect.height()
        return max(text_h + 50, 70)

    def _calc_expanded_height(self):
        base_h = self._calc_base_height()
        if not self.detail_label:
            return base_h
        fm = self.detail_label.fontMetrics()
        text = self.detail_label.text()
        label_width = self.detail_label.width() if self.detail_label.width() > 0 else 400
        text_rect = fm.boundingRect(0, 0, label_width, 16777215,
                                     Qt.TextWordWrap | Qt.AlignLeft, text)
        text_h = text_rect.height()
        return base_h + max(text_h + 16, 20)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        level = self._data.get('level', '')
        is_error = level == 'error'

        indicator = QFrame()
        indicator.setObjectName("issueIndicator")
        indicator.setFixedWidth(4)
        layout.addWidget(indicator)

        info_col = QVBoxLayout()
        info_col.setSpacing(3)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        cat_badge = QLabel(self._data.get('category', ''))
        cat_badge.setObjectName("issueCategoryBadge")
        header_row.addWidget(cat_badge)

        level_badge = QLabel('\u274c \u9519\u8bef' if is_error else '\u26a0 \u8b66\u544a')
        level_badge.setObjectName("statusBadgeFail" if is_error else "statusBadgeWarn")
        header_row.addWidget(level_badge)
        header_row.addStretch()
        info_col.addLayout(header_row)

        desc_label = QLabel(self._data.get('desc', ''))
        desc_label.setObjectName("issueDescText")
        desc_label.setWordWrap(True)
        self.desc_label = desc_label
        info_col.addWidget(desc_label)

        detail = self._data.get('detail', [])
        if detail and isinstance(detail, list):
            det_str = '\n'.join(str(d) for d in detail)
            self.detail_label = QLabel(det_str)
            self.detail_label.setObjectName("issueDetailText")
            self.detail_label.setVisible(False)
            self.detail_label.setWordWrap(True)
            info_col.addWidget(self.detail_label)
        else:
            self.detail_label = None

        layout.addLayout(info_col, 1)

        self.chevron_btn = QPushButton("\u25bc")
        self.chevron_btn.setObjectName("issueChevronBtn")
        self.chevron_btn.setFixedSize(28, 28)
        self.chevron_btn.setCursor(Qt.PointingHandCursor)
        self.chevron_btn.clicked.connect(self._toggle_detail)
        layout.addWidget(self.chevron_btn, 0, Qt.AlignVCenter | Qt.AlignRight)

        base_h = self._calc_base_height()
        self.setMinimumHeight(base_h)
        self.setMaximumHeight(base_h)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            child = self.childAt(event.pos())
            if child != self.chevron_btn:
                self._toggle_detail()
            self.clicked.emit(self._data)
        super().mousePressEvent(event)

    def _toggle_detail(self):
        self._expanded = not self._expanded
        if self.detail_label:
            self.detail_label.setVisible(self._expanded)
            if self._expanded:
                target_h = self._calc_expanded_height()
            else:
                target_h = self._calc_base_height()

            rotation = 180 if self._expanded else 0
            self._animate_chevron(rotation)

            anim = QPropertyAnimation(self, b"minimumHeight")
            anim.setDuration(200)
            anim.setStartValue(self.height())
            anim.setEndValue(target_h)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.start()

            anim2 = QPropertyAnimation(self, b"maximumHeight")
            anim2.setDuration(200)
            anim2.setStartValue(self.height())
            anim2.setEndValue(target_h)
            anim2.setEasingCurve(QEasingCurve.OutCubic)
            anim2.start()

    def expand(self, animate: bool = False):
        if not self._expanded and self.detail_label:
            self._expanded = True
            self.detail_label.setVisible(True)
            target_h = self._calc_expanded_height()

            if animate:
                rotation = 180
                self._animate_chevron(rotation)

                anim = QPropertyAnimation(self, b"minimumHeight")
                anim.setDuration(200)
                anim.setStartValue(self.height())
                anim.setEndValue(target_h)
                anim.setEasingCurve(QEasingCurve.OutCubic)
                anim.start()

                anim2 = QPropertyAnimation(self, b"maximumHeight")
                anim2.setDuration(200)
                anim2.setStartValue(self.height())
                anim2.setEndValue(target_h)
                anim2.setEasingCurve(QEasingCurve.OutCubic)
                anim2.start()
            else:
                self.setMinimumHeight(target_h)
                self.setMaximumHeight(target_h)
                self.chevron_btn.setText('\u25b2')

    def _animate_chevron(self, angle: int):
        icon = '\u25b2' if angle == 180 else '\u25bc'
        self.chevron_btn.setText(icon)


class CrossCheckListPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("crossCheckListPanel")
        self._items = []
        self._setup_ui()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        self.header_widget = QWidget()
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(4, 0, 4, 0)
        self.error_count = QLabel("\u274c 错误: 0")
        self.error_count.setObjectName("crossErrorCount")
        header_layout.addWidget(self.error_count)
        self.warn_count = QLabel("\u26a0 警告: 0")
        self.warn_count.setObjectName("crossWarnCount")
        header_layout.addWidget(self.warn_count)
        header_layout.addStretch()
        main_layout.addWidget(self.header_widget)

        self.items_scroll = QScrollArea()
        self.items_scroll.setWidgetResizable(True)
        self.items_scroll.setFrameShape(QFrame.NoFrame)
        self.items_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.items_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.items_scroll.setObjectName("crossItemsScrollArea")

        items_content = QWidget()
        self.items_layout = QVBoxLayout(items_content)
        self.items_layout.setContentsMargins(4, 4, 4, 4)
        self.items_layout.setSpacing(8)
        self.items_layout.addStretch()
        self.items_scroll.setWidget(items_content)
        main_layout.addWidget(self.items_scroll, 1)

    def set_items(self, items: list):
        for item in self._items:
            item.deleteLater()
        self._items.clear()
        while i := self.items_layout.takeAt(0):
            if i.widget():
                i.widget().deleteLater()
        self.items_layout.addStretch()

        errors = sum(1 for i in items if i.get('level') == 'error')
        warnings = sum(1 for i in items if i.get('level') == 'warn')
        self.error_count.setText(f"\u274c 错误: {errors}")
        self.warn_count.setText(f"\u26a0 警告: {warnings}")

        if not items:
            empty = QLabel("\u2705 \u65e0\u4ea4\u53c9\u6821\u9a8c\u95ee\u9898")
            empty.setObjectName("emptyState")
            empty.setAlignment(Qt.AlignCenter)
            empty.setMinimumHeight(100)
            self.items_layout.insertWidget(0, empty)
            return

        for item in items:
            issue_item = CrossIssueItem(item)
            self.items_layout.insertWidget(len(self._items), issue_item)
            self._items.append(issue_item)
