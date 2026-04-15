# -*- coding: utf-8 -*-
"""
青海空间数据检查工具 - 桌面应用入口
"""

import sys
import os

os.environ['PYTHONIOENCODING'] = 'utf-8'

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from ui.main_window import MainWindow


def main():
    # PySide6/Qt6 高DPI缩放默认启用，无需手动设置

    app = QApplication(sys.argv)
    app.setApplicationName("风险隐患调查与影响分析成果审核小工具")
    app.setOrganizationName("审核汇集")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()