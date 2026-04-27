# -*- coding: utf-8 -*-
"""
开发模式启动器 - 文件变化自动重载
使用 watchdog 监听文件变化，自动重启应用程序
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path
from threading import Thread

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
except ImportError:
    print("请先安装 watchdog: pip install watchdog")
    sys.exit(1)


class RestartHandler(FileSystemEventHandler):
    """文件变化处理器 - 检测到修改后重启应用"""
    
    # 忽略的文件/目录模式
    IGNORE_PATTERNS = {
        '__pycache__', '.pyc', '.pyo', '.git', '.idea', '.vscode',
        'output', 'build', 'dist', '.pytest_cache', '.trae',
        '02空间数据', '空间数据格式化', '青海24示范小流域',
        '.lock', '.sr.lock', '.db', '.log'
    }
    
    # 监听的文件扩展名
    WATCH_EXTENSIONS = {'.py', '.json', '.css', '.qss'}
    
    def __init__(self, restart_callback, debounce_seconds=1.0):
        self.restart_callback = restart_callback
        self.debounce_seconds = debounce_seconds
        self._last_restart_time = 0
        self._pending_restart = False
    
    def should_trigger_restart(self, path: str) -> bool:
        """判断文件变化是否需要触发重启"""
        path_lower = path.lower()
        
        # 检查忽略模式
        for pattern in self.IGNORE_PATTERNS:
            if pattern.lower() in path_lower:
                return False
        
        # 检查扩展名
        ext = Path(path).suffix.lower()
        if ext not in self.WATCH_EXTENSIONS:
            return False
        
        # 只监听项目核心目录
        project_root = Path(__file__).parent
        rel_path = Path(path)
        
        try:
            rel_path = rel_path.relative_to(project_root)
            # 只监听核心目录：core, ui, services, utils, config, main.py
            valid_dirs = {'core', 'ui', 'services', 'utils', 'config', ''}
            first_part = rel_path.parts[0] if rel_path.parts else ''
            if first_part not in valid_dirs:
                return False
        except ValueError:
            return False
        
        return True
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        path = event.src_path
        
        if not self.should_trigger_restart(path):
            return
        
        # 防抖处理 - 避免短时间内多次重启
        current_time = time.time()
        if current_time - self._last_restart_time < self.debounce_seconds:
            return
        
        self._last_restart_time = current_time
        
        print(f"\n[热重载] 检测到文件变化: {Path(path).name}")
        print("[热重载] 正在重启应用...")
        self.restart_callback()


class DevRunner:
    """开发模式运行器"""
    
    def __init__(self):
        self.process = None
        self.project_root = Path(__file__).parent
        self.main_script = self.project_root / "main.py"
        self.observer = None
        self._shutdown = False
    
    def start_app(self):
        """启动应用程序"""
        # 先停止旧进程（确保关闭）
        self.stop_app()
        time.sleep(0.5)  # 等待进程完全退出
        
        # 启动新进程
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        self.process = subprocess.Popen(
            [sys.executable, str(self.main_script)],
            cwd=str(self.project_root),
            env=env,
            # 不捕获输出，让应用直接显示在终端
        )
        
        print(f"[开发模式] 应用已启动 (PID: {self.process.pid})")
    
    def stop_app(self):
        """停止应用程序 - 强制关闭所有相关进程"""
        if self.process:
            pid = self.process.pid
            try:
                # Windows上使用taskkill强制关闭进程树
                if sys.platform == 'win32':
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)],
                                   capture_output=True, timeout=5)
                else:
                    # Unix系统使用terminate
                    self.process.terminate()
                    self.process.wait(timeout=3)
            except Exception as e:
                print(f"[开发模式] 停止应用时出错: {e}")
            finally:
                self.process = None
                print(f"[开发模式] 已关闭旧进程 (PID: {pid})")
    
    def restart_app(self):
        """重启应用程序"""
        self.start_app()
    
    def setup_watcher(self):
        """设置文件监听器"""
        handler = RestartHandler(
            restart_callback=self.restart_app,
            debounce_seconds=1.5  # 1.5秒防抖
        )
        
        self.observer = Observer()
        
        # 监听核心目录
        watch_dirs = [
            self.project_root / 'core',
            self.project_root / 'ui',
            self.project_root / 'services',
            self.project_root / 'utils',
            self.project_root / 'config',
            self.project_root,  # 根目录 (main.py 等)
        ]
        
        for dir_path in watch_dirs:
            if dir_path.exists():
                self.observer.schedule(handler, str(dir_path), recursive=True)
        
        self.observer.start()
        print("[开发模式] 文件监听已启动")
        print(f"[开发模式] 监听目录: core, ui, services, utils, config, main.py")
    
    def run(self):
        """运行开发模式"""
        print("=" * 50)
        print("  空间数据检查工具 - 开发模式 (热重载)")
        print("=" * 50)
        print()
        print("功能说明:")
        print("  - 监听 .py/.json 文件变化")
        print("  - 自动重启应用程序")
        print("  - 按 Ctrl+C 退出开发模式")
        print()
        
        # 启动应用
        self.start_app()
        
        # 设置文件监听
        self.setup_watcher()
        
        # 主循环
        try:
            while not self._shutdown:
                # 检查应用进程状态
                if self.process and self.process.poll() is not None:
                    # 应用已退出（可能是正常退出或崩溃）
                    if not self._shutdown:
                        print("[开发模式] 应用已退出，等待文件变化以重启...")
                
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n[开发模式] 收到退出信号...")
            self._shutdown = True
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        print("[开发模式] 正在清理...")
        
        # 停止监听器
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        # 停止应用
        self.stop_app()
        
        print("[开发模式] 已退出")


def main():
    """主入口"""
    runner = DevRunner()
    runner.run()


if __name__ == "__main__":
    main()