# -*- coding: utf-8 -*-
"""
PyInstaller Runtime Hook for PySide6 QtWebEngine
解决打包后 WebEngine 无法正常工作的问题
"""

import os
import sys

def setup_webengine_paths():
    if not getattr(sys, 'frozen', False):
        return
    
    base_path = sys._MEIPASS
    
    pyside6_path = os.path.join(base_path, 'PySide6')
    if os.path.exists(pyside6_path):
        os.environ['QTWEBENGINEPROCESS_PATH'] = os.path.join(pyside6_path, 'QtWebEngineProcess.exe')
        
        resources_path = os.path.join(pyside6_path, 'resources')
        if os.path.exists(resources_path):
            os.environ['QTWEBENGINE_RESOURCES_PATH'] = resources_path
        
        qt_plugin_path = os.path.join(pyside6_path, 'plugins')
        if os.path.exists(qt_plugin_path):
            os.environ['QT_PLUGIN_PATH'] = qt_plugin_path
        
        os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--disable-gpu --disable-software-rasterizer'

setup_webengine_paths()

try:
    import PySide6
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEngineSettings
    from PySide6.QtWebChannel import QWebChannel
except ImportError as e:
    pass
except Exception as e:
    pass