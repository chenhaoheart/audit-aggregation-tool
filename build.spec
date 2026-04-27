# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置文件
使用方法: pyinstaller build.spec
"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
from datetime import datetime

VERSION_DATE = datetime.now().strftime("%Y%m%d")

numpy_hiddenimports = collect_submodules('numpy')
fiona_hiddenimports = collect_submodules('fiona')
geopandas_hiddenimports = collect_submodules('geopandas')
shapely_hiddenimports = collect_submodules('shapely')
pyproj_hiddenimports = collect_submodules('pyproj')
pandas_hiddenimports = collect_submodules('pandas')

numpy_data_files = collect_data_files('numpy')
geopandas_data_files = collect_data_files('geopandas')
shapely_data_files = collect_data_files('shapely')
fiona_data_files = collect_data_files('fiona')
pyproj_data_files = collect_data_files('pyproj')

pyogrio_data_files = []
pyogrio_hiddenimports = []
try:
    pyogrio_data_files = collect_data_files('pyogrio')
    pyogrio_hiddenimports = collect_submodules('pyogrio')
except Exception:
    pass

pyside6_data_files = []
pyside6_hiddenimports = []
try:
    pyside6_data_files = collect_data_files('PySide6')
    pyside6_hiddenimports = collect_submodules('PySide6')
except Exception:
    pass

pillow_data_files = []
pillow_hiddenimports = []
try:
    pillow_data_files = collect_data_files('PIL')
    pillow_hiddenimports = collect_submodules('PIL')
except Exception:
    pass

PROJECT_ROOT = Path(SPECPATH)

RUNTIME_HOOK_ENCODING = PROJECT_ROOT / 'hooks' / 'runtime_hook_encoding.py'
RUNTIME_HOOK_WEBENGINE = PROJECT_ROOT / 'hooks' / 'runtime_hook_webengine.py'

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        *numpy_data_files,
        *geopandas_data_files,
        *shapely_data_files,
        *fiona_data_files,
        *pyproj_data_files,
        *pyogrio_data_files,
        *pyside6_data_files,
        *pillow_data_files,
        ('scripts', 'scripts'),
        ('config', 'config'),
        ('resources/gis', 'resources/gis'),
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtNetwork',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebChannel',
        *pyside6_hiddenimports,
        *numpy_hiddenimports,
        *fiona_hiddenimports,
        *geopandas_hiddenimports,
        *shapely_hiddenimports,
        *pyproj_hiddenimports,
        *pandas_hiddenimports,
        *pyogrio_hiddenimports,
        *pillow_hiddenimports,
        'numpy.core._multiarray_tests',
        'numpy.core.multiarray',
        'numpy.core.umath',
        'numpy.core.numeric',
        'numpy.core.fromnumeric',
        'numpy.core._dtype',
        'numpy.core._rational',
        'PIL',
        'PIL.Image',
        'PIL._imaging',
        'openpyxl',
        'openpyxl.cell',
        'openpyxl.worksheet',
        'xlrd',
        'codecs',
        'encodings',
        'encodings.gb18030',
        'encodings.gbk',
        'encodings.gb2312',
        'encodings.cp936',
        'encodings.utf_8',
        'encodings.latin_1',
        'encodings.iso8859_1',
        'fiona.drvsupport',
        'fiona._drivers',
        'fiona.schema',
        'fiona.errors',
        'fiona.crs',
        'fiona.collection',
        'fiona._env',
        'pyogrio',
        'pyogrio.raw',
        'pyogrio.geopandas',
        'pyogrio._io',
        'pyogrio._version',
        'dbfread',
        'dbfread.read',
        'shapefile',
        'tqdm',
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[str(RUNTIME_HOOK_ENCODING), str(RUNTIME_HOOK_WEBENGINE)],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'sphinx',
        'docutils',
        'urllib3',
        'requests',
        'cv2',
        'imageio',
        'sympy',
        'PyQt6',
        'PyQt5',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtWebEngineWidgets',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
    ],
    noarchive=False,
)

# 过滤不必要的二进制文件
filtered_binaries = []
for binary in a.binaries:
    path = binary[0].lower()
    if 'numpy\\_core' in path or 'numpy/_core' in path:
        filtered_binaries.append(binary)
        continue
    if 'numpy\\core' in path or 'numpy/core' in path:
        filtered_binaries.append(binary)
        continue
    exclude_patterns = ['debug', 'pytest']
    if any(pattern in path for pattern in exclude_patterns):
        continue
    if 'tests' in path and 'numpy' not in path:
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
    name=f'空间数据检查工具_v1.4.0_{VERSION_DATE}',
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