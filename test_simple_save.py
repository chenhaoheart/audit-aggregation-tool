# -*- coding: utf-8 -*-
"""
简化版主题保存测试 - 直接测试核心功能
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.theme_manager import get_theme_manager, ThemeMode


def test_theme_persistence():
    """测试主题持久化功能"""
    print("=" * 70)
    print("🧪 主题持久化测试")
    print("=" * 70)

    theme_manager = get_theme_manager()
    config_file = theme_manager.config_file

    print(f"\n📁 配置文件路径: {config_file}")
    print(f"   文件存在: {os.path.exists(config_file)}")

    # 测试序列：模拟用户多次切换主题
    test_themes = [
        (ThemeMode.DARK, "暗黑"),
        (ThemeMode.LIGHT, "纯净"),
        (ThemeMode.AURORA, "极光"),
        (ThemeMode.FLAME, "晨曦"),
        (ThemeMode.FOREST, "森林"),
    ]

    print(f"\n{'='*70}")
    print(f"🔄 开始模拟用户切换主题...")
    print(f"{'='*70}")

    all_passed = True

    for i, (mode, display_name) in enumerate(test_themes, 1):
        print(f"\n📍 步骤 {i}/{len(test_themes)}: 切换到 [{display_name}] ({mode})")

        # 调用 set_mode（这是 ThemeDialog._on_theme_clicked 中调用的方法）
        print(f"   ▶️  调用 theme_manager.set_mode('{mode}')")
        theme_manager.set_mode(mode)

        # 等待文件系统同步
        time.sleep(0.1)

        # 立即验证是否写入文件
        print(f"   🔍 验证配置文件...")

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)

            saved_mode = saved_data.get('mode')
            print(f"   📄 文件内容: {json.dumps(saved_data, ensure_ascii=False)}")

            if saved_mode == mode:
                print(f"   ✅ 成功！已正确保存为 '{saved_mode}'")
            else:
                print(f"   ❌ 失败！期望 '{mode}'，实际 '{saved_mode}'")
                all_passed = False

            # 同时验证内存中的值
            if theme_manager.mode == mode:
                print(f"   ✅ 内存状态一致")
            else:
                print(f"   ⚠️  内存状态不一致: {theme_manager.mode}")
                all_passed = False

        except Exception as e:
            print(f"   ❌ 读取配置文件失败: {e}")
            all_passed = False

    # 最终验证
    print(f"\n{'='*70}")
    print(f"📊 最终验证")
    print(f"{'='*70}")

    with open(config_file, 'r', encoding='utf-8') as f:
        final_data = json.load(f)

    final_mode = final_data.get('mode')
    print(f"\n💾 最终配置文件内容:")
    print(f"   {json.dumps(final_data, indent=2, ensure_ascii=False)}")

    print(f"\n🎯 结论:")
    if all_passed:
        print(f"   ✅ 所有测试通过！主题切换后立即保存到配置文件")
        print(f"   ✅ 下次启动将使用主题: {final_mode}")
        return True
    else:
        print(f"   ❌ 部分测试失败！请检查错误信息")
        return False


if __name__ == '__main__':
    success = test_theme_persistence()
    print(f"\n{'='*70}")
    sys.exit(0 if success else 1)
