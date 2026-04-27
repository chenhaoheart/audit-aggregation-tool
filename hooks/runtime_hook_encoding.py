# -*- coding: utf-8 -*-
"""
PyInstaller Runtime Hook for Fiona encoding fix
解决打包后 fiona/geopandas 读取 shapefile 时编码问题
"""

import os
import sys

# 设置环境变量确保正确处理中文编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 预加载所有中文相关编码（关键！）
try:
    import encodings
    # 预加载 GBK 系列编码
    for enc_name in ['gbk', 'gb18030', 'gb2312', 'cp936', 'utf_8', 'latin_1']:
        try:
            enc = encodings.search_function(enc_name)
            if enc:
                # 强制注册编码
                encodings._cache[enc_name] = enc
        except Exception:
            pass
except Exception:
    pass

# Fiona 关键：设置 GDAL 环境变量
# GDAL 读取 DBF 时需要正确的编码配置
if sys.platform == 'win32':
    # 不强制设置编码，让 Fiona 自动检测
    # 但确保编码模块可用
    pass

# 尝试预加载 fiona 的关键模块
try:
    import fiona
    import fiona.drvsupport
    # 确保驱动支持已初始化
    fiona.drvsupport.supported_drivers

    # 重要：确保 GDAL_DATA 环境变量正确设置
    import fiona._env
    if hasattr(fiona._env, 'GDALDataFinder'):
        finder = fiona._env.GDALDataFinder()
        gdal_data = finder.search()
        if gdal_data:
            os.environ.setdefault('GDAL_DATA', str(gdal_data))
except Exception:
    pass