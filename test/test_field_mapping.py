# -*- coding: utf-8 -*-
"""
字段映射配置测试页面
"""

import sys
import os

os.environ['PYTHONIOENCODING'] = 'utf-8'

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QTextEdit
from PySide6.QtCore import Qt


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("字段映射配置测试")
        self.setMinimumSize(500, 400)

        central = QWidget()
        layout = QVBoxLayout(central)

        # 标题
        title = QLabel("字段映射规则配置测试")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        # 说明
        info = QLabel(
            "功能说明：\n"
            "• 点击'添加SHP文件'或'选择文件夹'导入SHP\n"
            "• 每个SHP可以配置输出的标准图层名称\n"
            "• 可以自定义字段映射关系\n"
            "• 支持导出/导入配置"
        )
        info.setStyleSheet("color: #7f8c8d; line-height: 1.8; padding: 10px;")
        layout.addWidget(info)

        # 打开按钮
        btn = QPushButton("打开字段映射配置对话框")
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5a6fd6, stop:1 #6a4190);
            }
        """)
        btn.clicked.connect(self._open_dialog)
        layout.addWidget(btn)

        # 结果显示
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(200)
        self.result_text.setPlaceholderText("配置结果将显示在这里...")
        layout.addWidget(self.result_text)

        layout.addStretch()

        self.setCentralWidget(central)

    def _open_dialog(self):
        from ui.field_mapping_dialog import FieldMappingDialog

        dialog = FieldMappingDialog(self)
        result = dialog.exec()

        if result:
            self.result_text.clear()
            configs = dialog.get_configs()

            self.result_text.append(f"✅ 用户点击了保存，共 {len(configs)} 个SHP配置：\n")

            for i, cfg in enumerate(configs, 1):
                self.result_text.append(f"\n【{i}】{cfg.get('shp_name', '')}")
                self.result_text.append(f"  输出图层: {cfg.get('output_name', '未设置')}")
                self.result_text.append(f"  源字段数: {len(cfg.get('source_fields', []))}")
                field_mapping = cfg.get('field_mapping', {})
                if field_mapping:
                    self.result_text.append(f"  字段映射:")
                    for target, candidates in field_mapping.items():
                        self.result_text.append(f"    {target} → {candidates}")
        else:
            self.result_text.setText("❌ 用户点击了取消")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())