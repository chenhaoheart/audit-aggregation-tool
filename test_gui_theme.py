# -*- coding: utf-8 -*-
"""
完整测试主题切换和保存功能 - 模拟真实使用场景
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from core.theme_manager import get_theme_manager, ThemeMode
from ui.dialogs.theme_dialog import ThemeDialog


def monitor_config_file(config_file, callback):
    """监控配置文件变化"""
    last_mtime = 0
    if os.path.exists(config_file):
        last_mtime = os.path.getmtime(config_file)

    def check():
        nonlocal last_mtime
        if os.path.exists(config_file):
            current_mtime = os.path.getmtime(config_file)
            if current_mtime != last_mtime:
                last_mtime = current_mtime
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                callback(data)
        QTimer.singleShot(100, check)

    check()


def test_theme_switching():
    """测试主题切换的完整流程"""
    print("=" * 70)
    print("🧪 完整主题切换测试")
    print("=" * 70)

    app = QApplication(sys.argv)
    theme_manager = get_theme_manager()

    config_file = theme_manager.config_file
    print(f"\n📁 配置文件: {config_file}")

    # 记录配置文件变化
    changes = []

    def on_config_changed(data):
        change = {
            'time': time.strftime('%H:%M:%S'),
            'mode': data.get('mode'),
            'opacity': data.get('glass_opacity')
        }
        changes.append(change)
        print(f"  ⚡ [{change['time']}] 配置文件已更新: mode={change['mode']}, opacity={change['opacity']}")

    # 启动文件监控
    monitor_config_file(config_file, on_config_changed)

    # 显示初始状态
    print(f"\n📊 初始状态:")
    print(f"   当前主题: {theme_manager.mode}")
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            initial_data = json.load(f)
        print(f"   配置文件: {initial_data}")

    # 创建主题对话框
    dialog = ThemeDialog()

    # 模拟用户操作的定时器序列
    test_sequence = [
        (1000, "打开对话框", lambda: None),
        (2000, "点击 DARK 主题", lambda: simulate_click(dialog, ThemeMode.DARK)),
        (3000, "检查是否保存", lambda: check_saved(config_file, ThemeMode.DARK)),
        (4000, "点击 LIGHT 主题", lambda: simulate_click(dialog, ThemeMode.LIGHT)),
        (5000, "检查是否保存", lambda: check_saved(config_file, ThemeMode.LIGHT)),
        (6000, "点击 AURORA 主题", lambda: simulate_click(dialog, ThemeMode.AURORA)),
        (7000, "检查是否保存", lambda: check_saved(config_file, ThemeMode.AURORA)),
        (8000, "关闭对话框", lambda: dialog.close()),
    ]

    def run_step(step_index):
        if step_index >= len(test_sequence):
            print_test_results()
            app.quit()
            return

        delay, description, action = test_sequence[step_index]
        print(f"\n⏱️  {description} ({delay}ms后)")
        QTimer.singleShot(delay, lambda: execute_step(step_index))

    def execute_step(step_index):
        delay, description, action = test_sequence[step_index]
        try:
            action()
        except Exception as e:
            print(f"   ❌ 执行失败: {e}")
        run_step(step_index + 1)

    def simulate_click(dialog_obj, theme_mode):
        """模拟点击主题卡片"""
        print(f"   🖱️  模拟点击主题: {theme_mode}")
        if theme_mode in dialog_obj._theme_cards:
            # 直接调用点击处理函数
            dialog_obj._on_theme_clicked(theme_mode)
            print(f"   ✅ 已调用 _on_theme_clicked({theme_mode})")
        else:
            print(f"   ⚠️  主题卡片未找到: {theme_mode}")

    def check_saved(expected_mode):
        """检查配置文件是否保存了期望的主题"""
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            actual_mode = data.get('mode')
            if actual_mode == expected_mode:
                print(f"   ✅ 验证通过！已保存为: {actual_mode}")
            else:
                print(f"   ❌ 验证失败！期望: {expected_mode}, 实际: {actual_mode}")
        else:
            print(f"   ❌ 配置文件不存在！")

    def print_test_results():
        print("\n" + "=" * 70)
        print("📋 测试结果汇总")
        print("=" * 70)
        print(f"\n📊 配置文件变化次数: {len(changes)}")
        for i, change in enumerate(changes, 1):
            print(f"   {i}. [{change['time']}] mode={change['mode']}")

        print(f"\n💾 最终配置:")
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                final_data = json.load(f)
            print(f"   {json.dumps(final_data, indent=2, ensure_ascii=False)}")

        print(f"\n✅ 测试完成！下次启动将使用主题: {final_data.get('mode', 'unknown')}")

    # 开始测试
    dialog.show()
    run_step(0)

    app.exec()


if __name__ == '__main__':
    test_theme_switching()
