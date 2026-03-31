# -*- mode: python ; coding: utf-8 -*-
"""
测试打包配置 - 用于验证 geopandas 读取 SHP 文件
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# 收集所有子模块
numpy_hiddenimports = collect_submodules('numpy')
fiona_hiddenimports = collect_submodules('fiona')
geopandas_hiddenimports = collect_submodules('geopandas')
shapely_hiddenimports = collect_submodules('shapely')
pyproj_hiddenimports = collect_submodules('pyproj')
pandas_hiddenimports = collect_submodules('pandas')

# 收集数据文件
numpy_data_files = collect_data_files('numpy')
geopandas_data_files = collect_data_files('geopandas')
shapely_data_files = collect_data_files('shapely')
fiona_data_files = collect_data_files('fiona')
pyproj_data_files = collect_data_files('pyproj')

a = Analysis(
    ['test_shp_standalone.py'],
    pathex=[],
    binaries=[],
    datas=[
        *numpy_data_files,
        *geopandas_data_files,
        *shapely_data_files,
        *fiona_data_files,
        *pyproj_data_files,
    ],
    hiddenimports=[
        *numpy_hiddenimports,
        *fiona_hiddenimports,
        *geopandas_hiddenimports,
        *shapely_hiddenimports,
        *pyproj_hiddenimports,
        *pandas_hiddenimports,
        'codecs',
        'encodings',
        'encodings.gb18030',
        'encodings.gbk',
        'encodings.gb2312',
        'encodings.cp936',
        'encodings.utf_8',
        'encodings.latin_1',
    ],
    hookspath=['hooks'],
    excludes=['tkinter', 'matplotlib', 'scipy', 'IPython', 'jupyter', 'pytest'],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='test_shp_read',
    debug=False,
    console=True,
)