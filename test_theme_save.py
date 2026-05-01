# -*- coding: utf-8 -*-
"""
测试主题保存功能
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.theme_manager import get_theme_manager, ThemeMode


def test_theme_save():
    print("=" * 60)
    print("测试主题保存功能")
    print("=" * 60)

    theme_manager = get_theme_manager()

    # 1. 显示当前配置文件路径
    print(f"\n📁 配置文件路径: {theme_manager.config_file}")
    print(f"   文件是否存在: {os.path.exists(theme_manager.config_file)}")

    # 2. 读取当前配置
    if os.path.exists(theme_manager.config_file):
        with open(theme_manager.config_file, 'r', encoding='utf-8') as f:
            current_config = json.load(f)
        print(f"\n📄 当前配置内容: {current_config}")
        print(f"   当前主题模式: {theme_manager.mode}")

    # 3. 测试切换到不同主题
    test_themes = [ThemeMode.DARK, ThemeMode.LIGHT, ThemeMode.AURORA]

    for theme in test_themes:
        print(f"\n{'='*40}")
        print(f"🔄 切换到主题: {theme}")

        # 调用 set_mode
        theme_manager.set_mode(theme)

        # 立即检查是否保存
        if os.path.exists(theme_manager.config_file):
            with open(theme_manager.config_file, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
            print(f"✅ 保存成功！")
            print(f"   保存的模式: {saved_config.get('mode')}")
            print(f"   内存中的模式: {theme_manager.mode}")

            if saved_config.get('mode') == theme:
                print(f"✅ 验证通过：文件和内存一致")
            else:
                print(f"❌ 错误：文件和内存不一致！")
                return False
        else:
            print(f"❌ 错误：配置文件不存在！")
            return False

    # 4. 最终状态
    print(f"\n{'='*60}")
    with open(theme_manager.config_file, 'r', encoding='utf-8') as f:
        final_config = json.load(f)
    print(f"🎉 测试完成！最终配置: {final_config}")
    print(f"   下次启动将使用主题: {final_config.get('mode')}")

    return True


if __name__ == '__main__':
    success = test_theme_save()
    sys.exit(0 if success else 1)
