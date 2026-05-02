# -*- coding: utf-8 -*-
"""
带调试日志的主题切换完整流程测试
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt
from core.theme_manager import get_theme_manager, ThemeMode


class TestApp(QWidget):
    def __init__(self):
        super().__init__()
        self.theme_manager = get_theme_manager()
        self.config_file = self.theme_manager.config_file

        self.setWindowTitle("主题保存功能测试")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout()

        # 状态显示区
        self.status_label = QLabel("准备就绪")
        self.status_label.setStyleSheet("font-size: 14px; padding: 10px;")
        layout.addWidget(self.status_label)

        # 配置文件内容显示
        self.config_label = QLabel()
        self.config_label.setStyleSheet("font-size: 12px; padding: 10px; background: #f5f5f5;")
        layout.addWidget(self.config_label)

        # 测试按钮
        for mode, name in [(ThemeMode.DARK, "暗黑"), (ThemeMode.LIGHT, "纯净"),
                           (ThemeMode.AURORA, "极光"), (ThemeMode.FLAME, "晨曦")]:
            btn = QPushButton(f"切换到 {name} ({mode})")
            btn.clicked.connect(lambda checked, m=mode: self.test_switch(m))
            layout.addWidget(btn)

        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新配置文件显示")
        refresh_btn.clicked.connect(self.refresh_config)
        layout.addWidget(refresh_btn)

        self.setLayout(layout)
        self.refresh_config()

    def test_switch(self, mode):
        """测试切换主题"""
        print(f"\n{'='*50}")
        print(f"🖱️  用户点击按钮，切换到主题: {mode}")
        print(f"{'='*50}")

        # 记录切换前的配置
        before = self.read_config()
        print(f"📄 切换前配置: {before}")

        # 调用 set_mode（这是ThemeDialog._on_theme_clicked中的调用）
        print(f"▶️  调用 theme_manager.set_mode('{mode}')")
        self.theme_manager.set_mode(mode)

        # 记录切换后的配置
        after = self.read_config()
        print(f"📄 切换后配置: {after}")

        # 验证结果
        if after.get('mode') == mode:
            msg = f"✅ 成功！已保存为 '{mode}'"
            print(f"✅ {msg}")
            self.status_label.setText(msg)
            self.status_label.setStyleSheet("font-size: 14px; padding: 10px; color: green; font-weight: bold;")
        else:
            msg = f"❌ 失败！期望 '{mode}'，实际 '{after.get('mode')}'"
            print(f"❌ {msg}")
            self.status_label.setText(msg)
            self.status_label.setStyleSheet("font-size: 14px; padding: 10px; color: red; font-weight: bold;")

        self.refresh_config()

    def read_config(self):
        """读取配置文件"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def refresh_config(self):
        """刷新显示"""
        config = self.read_config()
        config_text = f"""📁 配置文件路径: {self.config_file}
📄 当前内容:
{json.dumps(config, indent=2, ensure_ascii=False)}

💾 内存中的模式: {self.theme_manager.mode}"""
        self.config_label.setText(config_text)


def main():
    app = QApplication(sys.argv)

    print("=" * 70)
    print("🧪 主题保存功能交互式测试")
    print("=" * 70)
    print("\n使用说明:")
    print("  1. 点击不同的主题按钮")
    print("  2. 观察控制台输出和界面显示")
    print("  3. 检查 config/theme.json 文件是否实时更新")
    print("=" * 70)

    window = TestApp()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
