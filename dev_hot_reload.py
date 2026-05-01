# -*- coding: utf-8 -*-
"""
热重载开发模式启动器
- 修改文件后等待 60 秒无新变化才自动重载
- 按 Ctrl+R 立即重载
- 执行 `python reload.py` 命令立即重载
"""
import sys
import os
import importlib
import time
from pathlib import Path

from PySide6.QtWidgets import QApplication, QShortcut
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QKeySequence
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_MODULES = [
    'ui.main_window',
    'ui.components.dock_bar',
    'core.theme_manager',
    'ui.pages.check_page',
    'ui.report_page',
    'ui.shp_formatter_page',
]

WATCH_DIRS = ['ui', 'core']

DEBOUNCE_SECONDS = 60.0

TRIGGER_FILE = Path(__file__).parent / '.reload_trigger'


class HotReloadHandler(FileSystemEventHandler):
    def __init__(self, schedule_reload, force_reload):
        super().__init__()
        self.schedule_reload = schedule_reload
        self.force_reload = force_reload

    def on_modified(self, event):
        if event.is_directory:
            return
        src_path = Path(event.src_path)
        
        if src_path.name == '.reload_trigger':
            self.force_reload()
            return
        
        if not event.src_path.endswith('.py'):
            return
        if '__pycache__' in event.src_path:
            return
        self.schedule_reload(event.src_path)


class HotReloadApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        self.observer = Observer()
        self.reload_timer = QTimer()
        self.reload_timer.setSingleShot(True)
        self.reload_timer.timeout.connect(self.do_reload)
        self.pending_files = set()
        self.last_change_time = 0
        self.shortcut = None

    def schedule_reload(self, filepath):
        self.pending_files.add(filepath)
        self.last_change_time = time.time()
        self.reload_timer.start(int(DEBOUNCE_SECONDS * 1000))
        print(f"[检测到变化] {Path(filepath).name}，{int(DEBOUNCE_SECONDS)}秒后重载（或执行 python reload.py）")

    def force_reload(self):
        self.reload_timer.stop()
        self.pending_files.add("(命令触发)")
        self.do_reload()

    def do_reload(self):
        if time.time() - self.last_change_time < DEBOUNCE_SECONDS - 0.1:
            if self.reload_timer.isActive():
                return

        print("\n" + "=" * 40)
        print("[热重载] 开始重载...")
        for f in self.pending_files:
            print(f"  - {Path(f).name if '(' not in str(f) else f}")
        self.pending_files.clear()

        success = True
        for module_name in WATCH_MODULES:
            if module_name in sys.modules:
                try:
                    importlib.reload(sys.modules[module_name])
                    print(f"  [OK] {module_name}")
                except Exception as e:
                    print(f"  [ERR] {module_name}: {e}")
                    success = False

        if success:
            try:
                from ui.main_window import MainWindow
                if self.window:
                    self.window.close()
                    self.window.deleteLater()
                self.window = MainWindow()
                self.window.show()
                self._setup_shortcut()
                print("[完成] 窗口已刷新")
            except Exception as e:
                print(f"[失败] {e}")
                import traceback
                traceback.print_exc()
        else:
            print("[跳过] 有模块重载失败，保持当前窗口")

        print("=" * 40 + "\n")

    def _setup_shortcut(self):
        if self.shortcut:
            del self.shortcut
        self.shortcut = QShortcut(QKeySequence("Ctrl+R"), self.window)
        self.shortcut.activated.connect(self.force_reload)

    def run(self):
        self.do_reload()

        handler = HotReloadHandler(self.schedule_reload, self.force_reload)
        base_path = Path(__file__).parent
        for d in WATCH_DIRS:
            p = base_path / d
            if p.exists():
                self.observer.schedule(handler, str(p), recursive=True)
        
        self.observer.schedule(handler, str(base_path), recursive=False)

        self.observer.start()

        print("\n" + "=" * 50)
        print("  热重载模式已启动")
        print(f"  自动重载: 修改后 {int(DEBOUNCE_SECONDS)} 秒无新变化")
        print("  手动重载: 按 Ctrl+R 或执行 python reload.py")
        print("=" * 50 + "\n")

        try:
            sys.exit(self.app.exec())
        finally:
            self.observer.stop()
            self.observer.join()


if __name__ == '__main__':
    app = HotReloadApp()
    app.run()