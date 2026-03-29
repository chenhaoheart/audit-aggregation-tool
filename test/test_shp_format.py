# -*- coding: utf-8 -*-
"""
测试 SHP 格式化功能 - 模拟调用 ArcGIS Python
"""

import os
import sys
import json
import tempfile
import shutil
import subprocess

# 配置
PYTHON_EXE = r"C:\Python27\ArcGIS10.8\python.exe"
SCRIPT_PATH = r"D:\qh-dcpj-py\24青海断面数据整理检查脚本\省平台断面汇总增强版\空间数据检查桌面版\scripts\shp_format_worker.py"
INPUT_DIR = r"E:\青海\2026_03_24_湟中空间图层"
OUTPUT_DIR = r"E:\青海\图层格式化测试\test_output"

# 规则
RULES = [
    {
        "output_name": "隐患要素分布L.shp",
        "keywords": ["隐患要素"],
        "field_mapping": {
            "名称": ["名称", "NAME", "Name", "name"],
            "编号": ["PID", "编号", "编码", "pid", "Pid"],
            "类别": ["TYPE", "TYPES", "types", "TYPBS", "类别"],
            "河流名称": ["RVNM", "RVNAME", "rvname", "RAVNME", "RVNAVB", "河流名称", "河流名"],
            "河流代码": ["RVCD", "rvcd", "河流代码", "河流代"]
        }
    }
]


def test_basic_python():
    """测试基本 Python 调用"""
    print("=" * 60)
    print("测试 1: 基本 Python 调用")
    print("=" * 60)

    result = subprocess.run(
        [PYTHON_EXE, "-c", "print('Hello from Python 2.7')"],
        capture_output=True,
        text=True
    )
    print("stdout:", result.stdout)
    print("stderr:", result.stderr)
    print("returncode:", result.returncode)


def test_arcpy_import():
    """测试 arcpy 导入"""
    print("\n" + "=" * 60)
    print("测试 2: arcpy 导入")
    print("=" * 60)

    result = subprocess.run(
        [PYTHON_EXE, "-c", "import arcpy; print('arcpy OK')"],
        capture_output=True,
        text=True
    )
    print("stdout:", result.stdout)
    print("stderr:", result.stderr)
    print("returncode:", result.returncode)


def test_script_help():
    """测试脚本帮助"""
    print("\n" + "=" * 60)
    print("测试 3: 脚本 --help")
    print("=" * 60)

    # 复制脚本到临时目录
    temp_dir = tempfile.mkdtemp(prefix="shp_test_")
    temp_script = os.path.join(temp_dir, "worker.py")
    shutil.copy2(SCRIPT_PATH, temp_script)

    print("临时目录:", temp_dir)
    print("临时脚本:", temp_script)

    result = subprocess.run(
        [PYTHON_EXE, "-u", temp_script, "--help"],
        capture_output=True,
        text=True
    )
    print("stdout:", result.stdout)
    print("stderr:", result.stderr)
    print("returncode:", result.returncode)

    shutil.rmtree(temp_dir)


def test_unicode_handling():
    """测试中文处理"""
    print("\n" + "=" * 60)
    print("测试 4: 中文处理")
    print("=" * 60)

    # 测试在 Python 2.7 中打印中文
    test_code = '''
# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# 测试中文
name = u"测试中文"
print("Name:", name)

# 测试 format
folder = u"青海"
msg = u"处理文件夹: {}".format(folder)
print(msg)
'''

    result = subprocess.run(
        [PYTHON_EXE, "-c", test_code],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    print("stdout:", result.stdout)
    print("stderr:", result.stderr)
    print("returncode:", result.returncode)


def test_full_process():
    """测试完整处理流程"""
    print("\n" + "=" * 60)
    print("测试 5: 完整处理流程")
    print("=" * 60)

    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="shp_test_")
    temp_script = os.path.join(temp_dir, "worker.py")
    temp_rules = os.path.join(temp_dir, "rules.json")

    print("临时目录:", temp_dir)

    # 复制脚本
    shutil.copy2(SCRIPT_PATH, temp_script)

    # 创建规则文件
    with open(temp_rules, 'w', encoding='utf-8') as f:
        json.dump(RULES, f, ensure_ascii=False)

    # 创建输出目录
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 构建命令
    cmd = [
        PYTHON_EXE, "-u", temp_script,
        "--input", INPUT_DIR,
        "--output", OUTPUT_DIR,
        "--rules", temp_rules
    ]

    print("命令:", ' '.join(cmd))

    # 设置环境变量
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env
        )

        # 实时读取输出
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                try:
                    print("  ", line.decode('utf-8', errors='replace').rstrip())
                except:
                    print("  ", line.rstrip())

        print("returncode:", process.returncode)

    except Exception as e:
        print("错误:", e)
    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("开始测试...")
    print("Python:", sys.version)
    print()

    test_basic_python()
    test_arcpy_import()
    test_unicode_handling()
    test_script_help()
    test_full_process()

    print("\n测试完成!")