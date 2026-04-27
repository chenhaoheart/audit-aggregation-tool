# -*- coding: utf-8 -*-
"""
PyInstaller hook for fiona - ensure GDAL and encoding components are packaged
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs
import os
import sys

# 收集所有子模块
hiddenimports = collect_submodules('fiona')

# 确保关键模块
hiddenimports += [
    'fiona.drvsupport',
    'fiona._drivers',
    'fiona.schema',
    'fiona.errors',
    'fiona.crs',
    'fiona.collection',
    'fiona.feature',
    'fiona.io',
    'fiona.logutils',
    'fiona.meta',
    'fiona.model',
    'fiona.props',
    'fiona.rfc3339',
    'fiona.session',
    'fiona.transform',
    'fiona.vfs',
    'fiona._err',
    'fiona._show_versions',
    'fiona._env',
    # 编码相关
    'fiona.encoding',
]

# 收集数据文件（包括驱动支持文件）
datas = collect_data_files('fiona')

# 收集动态库（GDAL DLL 等）
binaries = collect_dynamic_libs('fiona')

# 额外：收集 GDAL 数据文件（对 shapefile 支持至关重要）
try:
    import fiona
    fiona_path = os.path.dirname(fiona.__file__)
    gdal_data_candidates = [
        os.path.join(fiona_path, 'gdal_data'),
        os.path.join(sys.prefix, 'share', 'gdal'),
    ]
    for gdal_data in gdal_data_candidates:
        if os.path.exists(gdal_data):
            datas.append((gdal_data, 'gdal_data'))
            break
except Exception:
    pass