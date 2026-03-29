# PyInstaller 打包配置指南

## 1. 环境准备

### 1.1 安装依赖

```bash
pip install -r requirements.txt
pip install pyinstaller
```

### 1.2 验证环境

```bash
# 检查 PyInstaller 版本
pyinstaller --version

# 检查依赖是否完整
python main.py
```

---

## 2. 打包命令

### 2.1 开发调试（单文件，带控制台）

```bash
pyinstaller --onefile --console --name "空间数据检查工具" main.py
```

### 2.2 正式发布（单文件，无控制台）

```bash
pyinstaller --onefile --noconsole --name "空间数据检查工具" --icon=assets/icon.ico main.py
```

### 2.3 目录模式（启动更快）

```bash
pyinstaller --onedir --noconsole --name "空间数据检查工具" --icon=assets/icon.ico main.py
```

---

## 3. 配置文件方式（推荐）

在项目根目录创建 `build.spec` 文件：

```python
# -*- mode: python ; coding: utf-8 -*-

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
        # 添加非 Python 数据文件
        # ('assets', 'assets'),
        # ('config', 'config'),
    ],
    hiddenimports=[
        # PySide6 相关
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtNetwork',
        # 地理数据处理
        'geopandas',
        'shapely',
        'fiona',
        'pyproj',
        # 数据处理
        'pandas',
        'numpy',
        'openpyxl',
        'xlrd',
        # 其他依赖
        'tqdm',
        'pkg_resources.py2_warn',
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
    ],
    noarchive=False,
)

# 过滤不必要的二进制文件
pyd_files = []
for binary in a.binaries:
    path = binary[0]
    # 排除测试文件和调试文件
    if any(x in path.lower() for x in ['test', 'debug', 'tests']):
        continue
    pyd_files.append(binary)
a.binaries = pyd_files

# PYZ 压缩包
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None,
)

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
    upx=True,  # 使用 UPX 压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(PROJECT_ROOT / 'assets' / 'icon.ico') if (PROJECT_ROOT / 'assets' / 'icon.ico').exists() else None,
)
```

### 使用 spec 文件打包

```bash
pyinstaller build.spec
```

---

## 4. 常见问题与解决方案

### 4.1 模块找不到

**问题**: 打包后运行报错 `ModuleNotFoundError`

**解决**: 在 `hiddenimports` 中添加缺失的模块

```python
hiddenimports=[
    'missing_module_name',
]
```

### 4.2 数据文件丢失

**问题**: 配置文件、资源文件找不到

**解决**: 在 `datas` 中添加数据文件

```python
datas=[
    ('config/settings.json', 'config'),
    ('assets/images', 'assets/images'),
],
```

### 4.3 文件过大

**问题**: 打包后文件超过 200MB

**解决方案**:

1. 使用 `--exclude-module` 排除不需要的模块
2. 使用 UPX 压缩
3. 使用目录模式 `--onedir`

```bash
# 安装 UPX
# Windows: https://github.com/upx/upx/releases
# 将 upx.exe 放到 PyInstaller 目录或 PATH 中

pyinstaller --onefile --upx-dir=path/to/upx build.spec
```

### 4.4 GeoPandas 相关问题

**问题**: Fiona/GDAL 找不到投影文件

**解决**:

```python
import os
import sys

def get_resource_path(relative_path):
    """获取资源文件路径，兼容开发环境和打包环境"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)

# 在代码中使用
proj_path = get_resource_path('proj')
os.environ['PROJ_LIB'] = proj_path
```

### 4.5 ArcPy 不可用

**说明**: ArcPy 必须在 ArcGIS 环境中运行，无法打包

**处理**: 在代码中检测并提示用户

```python
# 已在 shp_formatter.py 中实现
try:
    import arcpy
    ARCPY_AVAILABLE = True
except ImportError:
    ARCPY_AVAILABLE = False
```

---

## 5. 打包脚本

创建 `build.bat` 自动化打包脚本：

```batch
@echo off
chcp 65001 >nul
echo ====================================
echo   空间数据检查工具 - 打包脚本
echo ====================================
echo.

:: 清理旧的打包文件
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

:: 执行打包
echo 正在打包...
pyinstaller build.spec

:: 检查结果
if exist "dist\空间数据检查工具.exe" (
    echo.
    echo ====================================
    echo   打包成功！
    echo   输出文件: dist\空间数据检查工具.exe
    echo ====================================
) else (
    echo.
    echo 打包失败，请检查错误信息
)

pause
```

---

## 6. 发布检查清单

打包完成后，在目标机器上验证：

- [ ] 程序能正常启动
- [ ] UI 显示正常（中文无乱码）
- [ ] 文件选择对话框可用
- [ ] SHP 文件读取正常
- [ ] Excel 导出功能正常
- [ ] 日志窗口显示正常
- [ ] 进度条和状态提示正常
- [ ] 内存占用合理（< 500MB）

---

## 7. 目录结构

```
项目根目录/
├── main.py              # 入口文件
├── build.spec           # PyInstaller 配置
├── build.bat            # 打包脚本
├── requirements.txt     # 依赖列表
├── assets/              # 资源文件
│   └── icon.ico         # 程序图标
├── core/                # 核心模块
│   ├── __init__.py
│   ├── checker.py
│   ├── data_validator.py
│   ├── report_reader.py
│   └── shp_formatter.py
├── ui/                  # 界面模块
│   ├── __init__.py
│   ├── main_window.py
│   ├── report_page.py
│   └── shp_formatter_page.py
├── utils/               # 工具模块
│   └── __init__.py
├── build/               # 打包临时目录（自动生成）
└── dist/                # 输出目录（自动生成）
    └── 空间数据检查工具.exe
```

---

## 8. 版本信息

| 项目 | 版本 |
|------|------|
| Python | >= 3.9 |
| PySide6 | >= 6.5.0 |
| PyInstaller | >= 5.13.0 |
| GeoPandas | >= 0.14.0 |

---

## 9. 参考资料

- [PyInstaller 官方文档](https://pyinstaller.org/en/stable/)
- [PyInstaller 使用手册](https://pyinstaller.readthedocs.io/)
- [PySide6 打包指南](https://doc.qt.io/qtforpython/deployment.html)