# -*- coding: utf-8 -*-
"""
SHP图层属性表格式化处理模块
通过子进程调用ArcGIS Python执行处理
"""

import os
import sys
import json
import tempfile
import subprocess
import shutil
from typing import List, Dict, Any, Optional, Callable
from core.config_manager import get_config, ArcGISConfig


def get_arcgis_python_path() -> Optional[str]:
    """
    获取配置的ArcGIS Python路径
    优先查找ArcGIS Pro，如果未找到则查找ArcGIS Desktop 10.8

    Returns:
        Python可执行文件路径或None
    """
    config = ArcGISConfig()
    python_dir = config.python_path

    if not python_dir:
        # 尝试默认路径 - 优先ArcGIS Pro
        pro_paths = [
            r"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3",
            r"C:\Program Files (x86)\ArcGIS\Pro\bin\Python\envs\arcgispro-py3",
        ]
        for p in pro_paths:
            if os.path.exists(p):
                python_dir = p
                break

        # 如果Pro未找到，尝试ArcGIS Desktop 10.8
        if not python_dir:
            desktop_paths = [
                r"C:\Python27\ArcGIS10.8",
            ]
            for p in desktop_paths:
                if os.path.exists(p):
                    python_dir = p
                    break

    if not python_dir:
        return None

    python_exe = os.path.join(python_dir, "python.exe")
    if os.path.exists(python_exe):
        return python_exe

    # 尝试Scripts目录
    python_exe = os.path.join(python_dir, "Scripts", "python.exe")
    if os.path.exists(python_exe):
        return python_exe

    return None


def test_arcgis_connection(python_exe: str = None) -> tuple:
    """
    测试ArcGIS Python连接

    Args:
        python_exe: Python可执行文件路径，为None则自动获取

    Returns:
        (是否成功, 错误信息)
    """
    if python_exe is None:
        python_exe = get_arcgis_python_path()
        if python_exe is None:
            return False, "未配置ArcGIS Python路径"

    try:
        result = subprocess.run(
            [python_exe, "-c", "import arcpy; print('OK')"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0 and "OK" in result.stdout:
            return True, None
        else:
            return False, result.stderr or "无法导入arcpy模块"

    except subprocess.TimeoutExpired:
        return False, "连接超时"
    except Exception as e:
        return False, str(e)


class ShpFormatter:
    """SHP格式化处理器 - 子进程模式"""

    def __init__(self):
        self.config = get_config()
        self.progress_callback: Optional[Callable[[str], None]] = None
        self._cancelled = False
        self._process = None

    def set_progress_callback(self, callback: Callable[[str], None]):
        """设置进度回调函数"""
        self.progress_callback = callback

    def log(self, message: str):
        """输出日志"""
        if self.progress_callback:
            self.progress_callback(message)
        print(message)

    def cancel(self):
        """取消处理"""
        self._cancelled = True
        if self._process:
            try:
                self._process.terminate()
            except:
                pass

    def process_folder(self, input_root: str, output_root: str) -> List[Dict[str, Any]]:
        """
        处理整个文件夹 - 批量循环查询生成新的统一命名shp文件

        Args:
            input_root: 输入根目录
            output_root: 输出根目录

        Returns:
            处理结果列表
        """
        self._cancelled = False

        # 获取ArcGIS Python路径
        python_exe = get_arcgis_python_path()
        if not python_exe:
            self.log("错误: 未配置ArcGIS Python路径，请在ArcGIS配置中设置")
            return []

        # 获取工作脚本路径（支持 PyInstaller 打包）
        import sys
        if getattr(sys, 'frozen', False):
            # 打包后的路径
            base_dir = sys._MEIPASS
        else:
            # 开发环境路径
            script_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(script_dir)

        worker_script = os.path.join(base_dir, "scripts", "shp_format_worker.py")

        if not os.path.exists(worker_script):
            self.log(f"错误: 找不到处理脚本: {worker_script}")
            return []

        # 创建临时工作目录（避免中文路径问题）
        temp_work_dir = None
        temp_rules_file = None
        temp_script_file = None

        try:
            # 在系统临时目录创建工作目录
            temp_work_dir = tempfile.mkdtemp(prefix="shp_format_")
            self.log(f"临时工作目录: {temp_work_dir}")

            # 复制脚本到临时目录
            temp_script_file = os.path.join(temp_work_dir, "shp_format_worker.py")
            shutil.copy2(worker_script, temp_script_file)
            self.log(f"脚本已复制到: {temp_script_file}")

            # 创建临时规则文件
            temp_rules_file = os.path.join(temp_work_dir, "rules.json")
            with open(temp_rules_file, 'w', encoding='utf-8') as f:
                json.dump(self.config.rules, f, ensure_ascii=False)

            self.log(f"使用ArcGIS Python: {python_exe}")
            self.log(f"输入目录: {input_root}")
            self.log(f"输出目录: {output_root}")

            # 构建命令
            cmd = [
                python_exe, "-u", temp_script_file,
                "--input", input_root,
                "--output", output_root,
                "--rules", temp_rules_file,
            ]

            self.log("启动处理进程...")

            # 设置环境变量，支持中文
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['LANG'] = 'zh_CN.GBK'
            env['LC_ALL'] = 'zh_CN.GBK'
            env['ARCGIS_SHP_ENCODING'] = 'GBK'

            # 启动子进程
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                env=env
            )

            # 实时读取输出
            results = []
            while True:
                if self._cancelled:
                    self.log("用户取消，正在终止进程...")
                    self._process.terminate()
                    break

                line = self._process.stdout.readline()
                if not line and self._process.poll() is not None:
                    break

                if line:
                    line = line.rstrip()
                    if line.startswith("RESULT:"):
                        # 解析结果
                        try:
                            results = json.loads(line[7:])
                        except:
                            pass
                    else:
                        self.log(line)

            # 等待进程结束
            self._process.wait()
            self._process = None

            if not self._cancelled:
                self.log("\n处理完成!")

            return results

        except Exception as e:
            self.log(f"处理出错: {e}")
            return []

        finally:
            # 清理临时目录
            if temp_work_dir and os.path.exists(temp_work_dir):
                try:
                    shutil.rmtree(temp_work_dir)
                    self.log("已清理临时目录")
                except Exception as cleanup_err:
                    self.log(f"清理临时目录失败: {cleanup_err}")