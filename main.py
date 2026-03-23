# -*- coding: utf-8 -*-
"""
青海空间数据检查工具 - 桌面应用入口
"""

import sys
import os

os.environ['PYTHONIOENCODING'] = 'utf-8'

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("青海空间数据检查工具")
    app.setOrganizationName("青海水文")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()