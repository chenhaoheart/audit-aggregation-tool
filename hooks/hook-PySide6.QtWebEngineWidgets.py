"""
PyInstaller hook for PySide6.QtWebEngineWidgets
Ensures QtWebEngine process and resources are included
"""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = [
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebEngineCore',
    'PySide6.QtWebChannel',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtNetwork',
]

datas = collect_data_files('PySide6', include_py_files=False)

webengine_files = []
for data in datas:
    path = data[0].lower()
    if any(x in path for x in ['webengine', 'qtwebengine', 'resources', 'plugins']):
        webengine_files.append(data)

datas = webengine_files if webengine_files else datas