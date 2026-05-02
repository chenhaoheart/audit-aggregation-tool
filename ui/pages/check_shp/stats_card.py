# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class CheckStatsCard(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(18, 10, 18, 10)

        self.stats_labels = {}
        for key, label_text in [("total_files", "文件数"), ("passed", "通过"),
                                 ("failed", "不通过"), ("pass_rate", "通过率")]:
            item_layout = QVBoxLayout()
            item_layout.setSpacing(2)
            val_label = QLabel("0")
            val_label.setObjectName("statValue")
            val_label.setAlignment(Qt.AlignCenter)
            name_label = QLabel(label_text)
            name_label.setObjectName("statName")
            name_label.setAlignment(Qt.AlignCenter)
            item_layout.addWidget(val_label)
            item_layout.addWidget(name_label)
            layout.addLayout(item_layout)
            self.stats_labels[key] = val_label

    def update_stats(self, results: list):
        passed = sum(1 for r in results if r['status'] == '通过')
        failed = sum(1 for r in results if r['status'] != '通过')
        total = len(results)
        rate = f"{passed / total * 100:.1f}%" if total > 0 else "--"

        self.stats_labels["total_files"].setText(str(total))
        self.stats_labels["passed"].setText(str(passed))
        self.stats_labels["failed"].setText(str(failed))
        self.stats_labels["pass_rate"].setText(rate)

    def reset(self):
        for key in self.stats_labels:
            self.stats_labels[key].setText("0")
