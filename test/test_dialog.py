# -*- coding: utf-8 -*-
"""
测试 photo_match_report_dialog 对话框
"""

import sys
import os

os.environ['PYTHONIOENCODING'] = 'utf-8'

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("测试对话框")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()