# -*- coding: utf-8 -*-
"""
PyInstaller 打包配置文件
"""

import sys
import os
from datetime import datetime

VERSION_DATE = datetime.now().strftime("%Y%m%d")
block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('scripts', 'scripts'),
    ],
    hiddenimports=[
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'geopandas',
        'pandas',
        'openpyxl',
        'tqdm',
        'fiona',
        'fiona.drvsupport',
        'pyproj',
        'shapely',
        # 编码处理
        'encodings.gb18030',
        'encodings.gbk',
        'encodings.gb2312',
        'encodings.cp936',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=f'空间数据检查工具_{VERSION_DATE}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=True,
    upx_exclude=[],
    name=f'空间数据检查工具_{VERSION_DATE}',
)