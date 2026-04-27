"""
PyInstaller 打包配置文件 - Onedir 模式（开发调试用）
使用方法: pyinstaller build_onedir.spec
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

PROJECT_ROOT = Path(SPECPATH)
RUNTIME_HOOK_PATH = PROJECT_ROOT / 'hooks' / 'runtime_hook_encoding.py'

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
        ('scripts', 'scripts'),
        ('config', 'config'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtNetwork',
        *numpy_hiddenimports,
        *fiona_hiddenimports,
        *geopandas_hiddenimports,
        *shapely_hiddenimports,
        *pyproj_hiddenimports,
        *pandas_hiddenimports,
        'openpyxl',
        'openpyxl.cell',
        'openpyxl.worksheet',
        'xlrd',
        'codecs',
        'encodings',
        'encodings.gb18030',
        'encodings.gbk',
        'encodings.gb2312',
        'encodings.utf_8',
        'encodings.latin_1',
        'encodings.iso8859_1',
        'fiona.drvsupport',
        'fiona.schema',
        'fiona.errors',
        'fiona.crs',
        'fiona.collection',
        'tqdm',
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[str(RUNTIME_HOOK_PATH)],
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
        'PIL',
        'cv2',
        'imageio',
        'sympy',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

icon_path = PROJECT_ROOT / 'assets' / 'icon.ico'
icon_str = str(icon_path) if icon_path.exists() else None

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=f'空间数据检查工具_v1.3.0_{VERSION_DATE}',
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

# Onedir 模式使用 COLLECT
coll = COLLECT(
    exe,
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
