# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置文件
使用方法: pyinstaller build.spec
"""

import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(SPECPATH)

# 分析入口文件
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 添加非 Python 数据文件（如需要）
        # ('assets', 'assets'),
        # ('config', 'config'),
    ],
    hiddenimports=[
        # PySide6 核心
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtNetwork',
        # 地理数据处理
        'geopandas',
        'shapely',
        'shapely.geometry',
        'shapely.ops',
        'fiona',
        'fiona.crs',
        'pyproj',
        'pyproj.crs',
        # 数据处理
        'pandas',
        'pandas._libs',
        'pandas._libs.tslibs',
        'numpy',
        'openpyxl',
        'openpyxl.cell',
        'openpyxl.worksheet',
        'xlrd',
        # 其他依赖
        'tqdm',
        'pkg_resources',
        'pkg_resources.py2_warn',
        # Fiona 内部依赖
        'fiona._err',
        'fiona._crs',
        'fiona._transform',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块，减小体积
        'tkinter',
        'matplotlib',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'sphinx',
        'docutils',
        'email',
        'html',
        'http',
        'urllib3',
        'requests',
        'PIL',
        'cv2',
        'imageio',
        'sympy',
    ],
    noarchive=False,
)

# 过滤不必要的二进制文件
filtered_binaries = []
for binary in a.binaries:
    path = binary[0].lower()
    # 排除测试文件、调试文件和不必要的 DLL
    exclude_patterns = ['test', 'debug', 'tests', 'pytest', 'qt6qml', 'qt6quick']
    if any(pattern in path for pattern in exclude_patterns):
        continue
    filtered_binaries.append(binary)
a.binaries = filtered_binaries

# 过滤不必要的数据文件
filtered_datas = []
for data in a.datas:
    path = data[0].lower()
    exclude_patterns = ['test', 'tests', 'examples', 'sample', 'doc', 'docs']
    if any(pattern in path for pattern in exclude_patterns):
        continue
    filtered_datas.append(data)
a.datas = filtered_datas

# PYZ 压缩包
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None,
)

# 检查图标文件是否存在
icon_path = PROJECT_ROOT / 'assets' / 'icon.ico'
icon_str = str(icon_path) if icon_path.exists() else None

# 可执行文件配置
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='空间数据检查工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_str,
)