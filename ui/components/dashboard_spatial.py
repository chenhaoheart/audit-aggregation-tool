# -*- coding: utf-8 -*-
"""
Dashboard空间数据与照片匹配组件
包含：SpatialLayerCard, SpatialResultGrid, PhotoMatchDashboard
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
)
from PySide6.QtCore import Qt

from core.theme_manager import get_theme_manager
from .dashboard_charts import StatMetricCard, HorizontalBarChart, MiniDonutWidget


class SpatialLayerCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("spatialLayerCard")
        self.setFixedHeight(120)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.file_name = QLabel("...")
        self.file_name.setObjectName("layerCardName")
        top_row.addWidget(self.file_name, 1)

        self.status_badge = QLabel("")
        self.status_badge.setObjectName("statusBadge")
        self.status_badge.setFixedHeight(22)
        top_row.addWidget(self.status_badge, 0, Qt.AlignVCenter)

        layout.addLayout(top_row)

        self.folder_label = QLabel("")
        self.folder_label.setObjectName("folderLabel")
        layout.addWidget(self.folder_label)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        stat1 = QHBoxLayout()
        stat1.setSpacing(4)
        self.total_label = QLabel("")
        self.total_label.setObjectName("layerStatText")
        stat1.addWidget(self.total_label)
        stats_row.addLayout(stat1, 1)

        stat2 = QHBoxLayout()
        stat2.setSpacing(4)
        self.valid_label = QLabel("")
        self.valid_label.setObjectName("layerStatValid")
        stat2.addWidget(self.valid_label)
        stats_row.addLayout(stat2, 1)

        stat3 = QHBoxLayout()
        stat3.setSpacing(4)
        self.invalid_label = QLabel("")
        self.invalid_label.setObjectName("layerStatInvalid")
        stat3.addWidget(self.invalid_label)
        stats_row.addLayout(stat3, 1)

        stat4 = QHBoxLayout()
        stat4.setSpacing(4)
        self.duplicate_label = QLabel("")
        self.duplicate_label.setObjectName("layerStatDup")
        stat4.addWidget(self.duplicate_label)
        stats_row.addLayout(stat4, 1)

        layout.addLayout(stats_row)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)

        self.error_preview = QLabel("")
        self.error_preview.setObjectName("errorPreviewLabel")
        self.error_preview.setWordWrap(True)
        bottom_row.addWidget(self.error_preview, 1)

        right = QVBoxLayout()
        right.setSpacing(2)
        right.setAlignment(Qt.AlignCenter)
        self.efficiency_label = QLabel("--%")
        self.efficiency_label.setObjectName("efficiencyLabel")
        self.efficiency_label.setAlignment(Qt.AlignCenter)
        right.addWidget(self.efficiency_label, 0, Qt.AlignCenter)
        bottom_row.addLayout(right, 0)

        layout.addLayout(bottom_row)

    def set_data(self, file_name: str, status: str, total: int, valid: int, invalid: int,
                 folder_name: str = "", duplicate_records: int = 0, errors: list = None):
        self.file_name.setText(file_name)

        status_config = {
            '通过': ('✅ 通过', 'spatialBadgePass'),
            '存在错误': ('❌ 异常', 'spatialBadgeFail'),
            '文件未找到': ('⚠️ 未找到', 'spatialBadgeWarn'),
            '读取失败': ('💥 失败', 'spatialBadgeFail'),
        }
        status_text, badge_obj = status_config.get(status, (status, 'spatialBadgePending'))
        self.status_badge.setText(f"  {status_text}  ")
        self.status_badge.setObjectName(badge_obj)
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)

        if folder_name:
            self.folder_label.setText(f"📁 {folder_name}")
            self.folder_label.setVisible(True)
        else:
            self.folder_label.setVisible(False)

        self.total_label.setText(f"📋 总计 {total}")
        self.valid_label.setText(f"✅ 有效 {valid}")
        self.invalid_label.setText(f"❌ 无效 {invalid}")
        if duplicate_records > 0:
            self.duplicate_label.setText(f"🔄 重复 {duplicate_records}")
            self.duplicate_label.setVisible(True)
        else:
            self.duplicate_label.setVisible(False)

        pct = f"{valid / max(total, 1) * 100:.1f}%"
        self.efficiency_label.setText(pct)

        is_pass = status == '通过'
        eff_obj = 'efficiencyLabelPass' if is_pass else 'efficiencyLabelFail'
        self.efficiency_label.setObjectName(eff_obj)
        self.efficiency_label.style().unpolish(self.efficiency_label)
        self.efficiency_label.style().polish(self.efficiency_label)

        if errors and len(errors) > 0:
            error_text = "⚠️ " + "; ".join(errors[:2])
            if len(errors) > 2:
                error_text += f" 等{len(errors)}项"
            self.error_preview.setText(error_text)
            self.error_preview.setVisible(True)
        else:
            self.error_preview.setVisible(False)


class SpatialResultGrid(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("spatialResultGrid")
        self._cards = []
        self._setup_ui()

    def _setup_ui(self):
        self.main_layout = QGridLayout(self)
        self.main_layout.setSpacing(12)
        self.main_layout.setContentsMargins(4, 4, 4, 4)

    def set_data(self, results: list):
        for card in self._cards:
            card.deleteLater()
        self._cards.clear()
        while item := self.main_layout.takeAt(0):
            if item.widget():
                item.widget().deleteLater()

        if not results:
            empty = QLabel("\ud83d\udccd \u6682\u65e0\u7a7a\u95f4\u6570\u636e")
            empty.setObjectName("emptyState")
            empty.setAlignment(Qt.AlignCenter)
            self.main_layout.addWidget(empty, 0, 0, 1, -1)
            return

        for i, r in enumerate(results):
            card = SpatialLayerCard()
            card.set_data(
                r.get('file_name', 'Unknown'),
                r.get('status', ''),
                r.get('total_records', 0),
                r.get('valid_records', 0),
                r.get('invalid_records', 0),
                folder_name=r.get('folder_name', ''),
                duplicate_records=r.get('duplicate_records', 0),
                errors=r.get('errors', [])
            )
            col = i % 2
            row = i // 2
            self.main_layout.addWidget(card, row, col)
            self._cards.append(card)


class PhotoMatchDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("photoMatchDashboard")
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(16)

        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        self.fubiao2_card = StatMetricCard("附表2匹配", "\ud83d\udccb", "text_primary")
        self.fubiao2_card.setMinimumHeight(80)
        top_row.addWidget(self.fubiao2_card, 1)

        self.fubiao3_card = StatMetricCard("附表3匹配", "\ud83d\udcf7", "text_primary")
        self.fubiao3_card.setMinimumHeight(80)
        top_row.addWidget(self.fubiao3_card, 1)

        self.photo_status_card = StatMetricCard("照片状态", "\U0001f4f8", "text_primary")
        self.photo_status_card.setMinimumHeight(80)
        top_row.addWidget(self.photo_status_card, 1)

        main_layout.addLayout(top_row)

        donut_row = QHBoxLayout()
        donut_row.setSpacing(24)
        donut_row.setAlignment(Qt.AlignCenter)

        f2_container = QWidget()
        f2_layout = QVBoxLayout(f2_container)
        f2_layout.setAlignment(Qt.AlignCenter)
        f2_title = QLabel("附表2 匹配率")
        f2_title.setObjectName("pageSubtitle")
        f2_title.setAlignment(Qt.AlignCenter)
        f2_layout.addWidget(f2_title)
        self.donut_f2 = MiniDonutWidget(72)
        f2_layout.addWidget(self.donut_f2, 0, Qt.AlignHCenter)
        donut_row.addWidget(f2_container)

        f3_container = QWidget()
        f3_layout = QVBoxLayout(f3_container)
        f3_layout.setAlignment(Qt.AlignCenter)
        f3_title = QLabel("附表3 匹配率")
        f3_title.setObjectName("pageSubtitle")
        f3_title.setAlignment(Qt.AlignCenter)
        f3_layout.addWidget(f3_title)
        self.donut_f3 = MiniDonutWidget(72)
        f3_layout.addWidget(self.donut_f3, 0, Qt.AlignHCenter)
        donut_row.addWidget(f3_container)

        main_layout.addLayout(donut_row)

        bar_section = QWidget()
        bar_section.setObjectName("cardInnerPanel")
        bar_layout = QHBoxLayout(bar_section)
        bar_layout.setContentsMargins(16, 8, 16, 8)
        bar_layout.setSpacing(20)

        self.bar_f2 = HorizontalBarChart()
        self.bar_f2.setFixedHeight(40)
        bar_layout.addWidget(self.bar_f2, 1)

        self.bar_f3 = HorizontalBarChart()
        self.bar_f3.setFixedHeight(40)
        bar_layout.addWidget(self.bar_f3, 1)

        main_layout.addWidget(bar_section)

    def set_data(self, summary: dict):
        f2_total = summary.get('fubiao2_total', 0)
        f2_matched = summary.get('fubiao2_matched', 0)
        f2_unmatched = summary.get('fubiao2_unmatched', 0)
        f3_total = summary.get('fubiao3_total', 0)
        f3_matched = summary.get('fubiao3_matched', 0)
        f3_unmatched = summary.get('fubiao3_unmatched', 0)
        photo_umatched = summary.get('photo_unmatched_f2', 0) + summary.get('photo_unmatched_f3', 0)

        f2_rate = f"{f2_matched / max(f2_total, 1) * 100:.0f}%"
        f3_rate = f"{f3_matched / max(f3_total, 1) * 100:.0f}%"

        f2_color = 'success_text' if f2_unmatched == 0 else ('warning_text' if f2_unmatched < 5 else 'error_text')
        f3_color = 'success_text' if f3_unmatched == 0 else ('warning_text' if f3_unmatched < 5 else 'error_text')
        p_color = 'success_text' if photo_umatched == 0 else ('warning_text' if photo_umatched < 5 else 'error_text')

        self.fubiao2_card.set_value(f2_rate, f"匹配{f2_matched}/{f2_total}", f2_color)
        self.fubiao3_card.set_value(f3_rate, f"匹配{f3_matched}/{f3_total}", f3_color)
        self.photo_status_card.set_value(str(photo_umatched), "张未匹配照片", p_color)

        self.donut_f2.set_data(f2_matched, max(f2_total, 1))
        self.donut_f3.set_data(f3_matched, max(f3_total, 1))

        theme = get_theme_manager().get_current_theme()
        success_c = theme.get('success_text', '#22c55e')
        warn_c = theme.get('warning_text', '#f59e0b')
        error_c = theme.get('error_text', '#ef4444')

        self.bar_f2.set_data([
            {'label': '', 'value': f2_matched, 'color': success_c},
            {'label': '', 'value': f2_unmatched, 'color': error_c},
        ])
        self.bar_f3.set_data([
            {'label': '', 'value': f3_matched, 'color': success_c},
            {'label': '', 'value': f3_unmatched, 'color': error_c},
        ])
