# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QFrame, QHBoxLayout
from ui.components.dashboard_widgets import StatMetricCard, HealthScoreGauge


class DashboardStatsRow(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(12, 18, 12, 18)

        self.stat_cards = {}

        errors_card = StatMetricCard("总错误", "\u274c", "error_text")
        errors_card.set_value("0", "\u4e25\u91cd\u95ee\u9898", "error_text")
        layout.addWidget(errors_card)
        self.stat_cards["errors"] = errors_card

        warnings_card = StatMetricCard("总警告", "\u26a0\ufe0f", "warning_text")
        warnings_card.set_value("0", "\u9700\u8981\u5173\u6ce8", "warning_text")
        layout.addWidget(warnings_card)
        self.stat_cards["warnings"] = warnings_card

        overall_card = StatMetricCard("综合评定", "\U0001f4ca", "text_primary")
        overall_card.set_value("--", "", None)
        layout.addWidget(overall_card)
        self.stat_cards["overall"] = overall_card

        self.health_gauge = HealthScoreGauge(110)
        self.health_gauge.setObjectName("healthGaugeContainer")
        layout.addWidget(self.health_gauge)
        self.stat_cards["score"] = self.health_gauge

    def update_stats(self, data: dict):
        summary = data.get('summary', {})
        errors = summary.get('total_errors', 0)
        warnings = summary.get('total_warnings', 0)
        overall = summary.get('overall_status', 'pending')

        err_color_key = "error_text" if errors > 0 else "success_text"
        self.stat_cards["errors"].set_value(
            str(errors),
            "\u4e25\u91cd\u95ee\u9898" if errors > 0 else "\u6570\u636e\u6b63\u5e38",
            err_color_key
        )

        warn_color_key = "warning_text" if warnings > 0 else "success_text"
        self.stat_cards["warnings"].set_value(
            str(warnings),
            "\u9700\u8981\u5173\u6ce8" if warnings > 0 else "\u65e0\u8b66\u544a",
            warn_color_key
        )

        overall_map = {
            'pass': ('\u2705 \u5168\u901a\u8fc7', '', 'success_text'),
            'warn': ('\u6709\u8b66\u544a', f'{warnings}\u9879\u8b66\u544a', 'warning_text'),
            'fail': ('\u274c \u6709\u9519\u8bef', f'{errors}\u9879\u9519\u8bef', 'error_text'),
        }
        val, sub, color_key = overall_map.get(overall, ('--', '', None))
        self.stat_cards["overall"].set_value(val, sub, color_key)

        score = max(0, 100 - errors * 5 - warnings * 2)
        self.health_gauge.set_score(score)

    def reset(self):
        self.stat_cards["errors"].set_value("--", "", None)
        self.stat_cards["warnings"].set_value("--", "", None)
        self.stat_cards["overall"].set_value("--", "", None)
        self.health_gauge.set_score(0)
