# -*- coding: utf-8 -*-
"""
测试短路径转换和子进程调用
"""

import os
import sys
import subprocess
import ctypes
from ctypes import wintypes

def get_short_path(long_path: str) -> str:
    """获取短路径名（8.3格式），解决中文路径问题"""
    try:
        GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
        GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
        GetShortPathNameW.restype = wintypes.DWORD

        buffer_size = GetShortPathNameW(long_path, None, 0)
        if buffer_size > 0:
            buffer = ctypes.create_unicode_buffer(buffer_size)
            GetShortPathNameW(long_path, buffer, buffer_size)
            return buffer.value
    except Exception as e:
        print(f"get_short_path 错误: {e}")
    return long_path


def test_short_path():
    """测试短路径转换"""
    # 测试路径
    test_paths = [
        r"D:\qh-dcpj-py\24青海断面数据整理检查脚本\省平台断面汇总增强版\空间数据检查桌面版\scripts\shp_format_worker.py",
        r"E:\青海\2026_03_24_湟中空间图层",
    ]

    print("=" * 60)
    print("测试短路径转换")
    print("=" * 60)

    for path in test_paths:
        print(f"\n原始路径: {path}")
        print(f"存在: {os.path.exists(path)}")
        short = get_short_path(path)
        print(f"短路径: {short}")
        print(f"是否相同: {path == short}")


def test_subprocess_call():
    """测试子进程调用"""
    print("\n" + "=" * 60)
    print("测试子进程调用")
    print("=" * 60)

    # Python 路径
    python_exe = r"C:\Python27\ArcGIS10.8\python.exe"
    script_path = r"D:\qh-dcpj-py\24青海断面数据整理检查脚本\省平台断面汇总增强版\空间数据检查桌面版\scripts\shp_format_worker.py"

    print(f"\nPython: {python_exe}")
    print(f"Python存在: {os.path.exists(python_exe)}")
    print(f"脚本: {script_path}")
    print(f"脚本存在: {os.path.exists(script_path)}")

    # 获取短路径
    script_short = get_short_path(script_path)
    print(f"\n脚本短路径: {script_short}")

    # 测试简单命令
    print("\n测试简单命令: python --version")
    result = subprocess.run(
        [python_exe, "--version"],
        capture_output=True,
        text=True
    )
    print(f"stdout: {result.stdout}")
    print(f"stderr: {result.stderr}")
    print(f"returncode: {result.returncode}")

    # 测试运行脚本（带短路径）
    print("\n测试运行脚本（短路径）...")
    cmd = [python_exe, "-u", script_short, "--help"]

    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=env,
            timeout=10
        )
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        print(f"returncode: {result.returncode}")
    except Exception as e:
        print(f"错误: {e}")


def test_file_content():
    """测试脚本文件是否有语法错误"""
    print("\n" + "=" * 60)
    print("测试脚本文件")
    print("=" * 60)

    script_path = r"D:\qh-dcpj-py\24青海断面数据整理检查脚本\省平台断面汇总增强版\空间数据检查桌面版\scripts\shp_format_worker.py"

    print(f"读取脚本: {script_path}")

    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"文件大小: {len(content)} 字节")
        print(f"前100字符: {content[:100]}")

        # 检查第30行
        lines = content.split('\n')
        if len(lines) >= 30:
            print(f"\n第30行内容: {repr(lines[29])}")
    except Exception as e:
        print(f"读取错误: {e}")


if __name__ == "__main__":
    test_short_path()
    test_file_content()
    test_subprocess_call()