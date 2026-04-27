# -*- coding: utf-8 -*-
"""
自动启动脚本 - 捕获异常并尝试自动修复
"""
import subprocess
import sys
import os
import traceback
import time

os.chdir(os.path.dirname(os.path.abspath(__file__)))

PY_FILES_TO_CHECK = [
    "main.py",
    "ui/main_window.py",
    "ui/components/dock_bar.py",
    "core/theme_manager.py",
    "ui/pages/check_page.py",
    "ui/report_page.py",
    "ui/shp_formatter_page.py",
]


def check_syntax():
    """检查所有关键文件语法"""
    errors = []
    for f in PY_FILES_TO_CHECK:
        if not os.path.exists(f):
            errors.append(f"文件不存在: {f}")
            continue
        try:
            with open(f, "r", encoding="utf-8") as fp:
                compile(fp.read(), f, "exec")
            print(f"  [OK] {f}")
        except SyntaxError as e:
            errors.append(f"  [ERR] {f}: 行 {e.lineno}, {e.msg}")
            print(f"  [ERR] {f}: 行 {e.lineno}, {e.msg}")
    return errors


def auto_fix_syntax_errors():
    """尝试修复常见语法问题"""
    fixed = False
    for f in PY_FILES_TO_CHECK:
        if not os.path.exists(f):
            continue
        try:
            with open(f, "r", encoding="utf-8") as fp:
                compile(fp.read(), f, "exec")
        except SyntaxError:
            # 尝试用 UTF-8-BOM 读取并重新保存为 UTF-8
            try:
                with open(f, "r", encoding="utf-8-sig") as fp:
                    content = fp.read()
                with open(f, "w", encoding="utf-8") as fp:
                    fp.write(content)
                print(f"  [FIX] {f}: 已修复编码")
                fixed = True
            except Exception:
                pass
    return fixed


def main():
    print("=" * 50)
    print("  空间数据检查工具 - 启动器")
    print("=" * 50)
    print()

    while True:
        print("[1/2] 语法检查...")
        errors = check_syntax()

        if errors:
            print(f"\n[发现 {len(errors)} 个错误] 尝试自动修复...")
            auto_fix_syntax_errors()
            print("\n[修复后] 重新检查...")
            errors = check_syntax()
            if errors:
                print(f"\n仍有 {len(errors)} 个错误，请手动修复后重试。")
                print("按 Enter 退出...")
                input()
                sys.exit(1)
            else:
                print("\n所有错误已修复!")

        print("\n[2/2] 启动程序...")
        print("-" * 50)

        try:
            result = subprocess.run(
                [sys.executable, "main.py"],
                encoding="utf-8",
                errors="replace"
            )

            if result.returncode == 0:
                print("\n[正常退出]")
                break
            else:
                print(f"\n[异常退出] 退出码: {result.returncode}")
                print("按 Enter 重新启动，或关闭此窗口退出...")
                input()
                print("\n" + "=" * 50 + "\n")

        except KeyboardInterrupt:
            print("\n[手动中断] 程序已停止")
            break
        except Exception as e:
            print(f"\n[启动失败] {e}")
            traceback.print_exc()
            print("\n按 Enter 重新尝试...")
            input()
            print("\n" + "=" * 50 + "\n")


if __name__ == "__main__":
    main()
