@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║          空间数据检查工具 - 打包脚本                        ║
echo ║          空间数据检查桌面版                                 ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

:: 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python
    pause
    exit /b 1
)

:: 检查 PyInstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [提示] 未安装 PyInstaller，正在安装...
    pip install pyinstaller
)

:: 显示当前 Python 版本
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PY_VER=%%i
echo [信息] Python 版本: %PY_VER%

:: 显示 PyInstaller 版本
for /f "tokens=2" %%i in ('python -c "import PyInstaller; print(PyInstaller.__version__)" 2^>^&1') do set PI_VER=%%i
echo [信息] PyInstaller 版本: %PI_VER%
echo.

:: 清理旧的打包文件
echo [步骤 1/3] 清理旧的打包文件...
if exist "dist" (
    rmdir /s /q dist
    echo        已删除 dist 目录
)
if exist "build" (
    rmdir /s /q build
    echo        已删除 build 目录
)
echo        清理完成
echo.

:: 创建 assets 目录（如果不存在）
if not exist "assets" (
    mkdir assets
    echo [提示] 已创建 assets 目录，可放入图标文件 icon.ico
)

:: 执行打包
echo [步骤 2/3] 开始打包...
echo.
pyinstaller build.spec

:: 检查打包结果
echo.
echo [步骤 3/3] 检查打包结果...
if exist "dist\空间数据检查工具.exe" (
    :: 获取文件大小
    for %%A in ("dist\空间数据检查工具.exe") do set SIZE=%%~zA
    set /a SIZE_MB=!SIZE! / 1048576

    echo.
    echo ╔════════════════════════════════════════════════════════════╗
    echo ║                    打包成功！                              ║
    echo ╠════════════════════════════════════════════════════════════╣
    echo ║  输出文件: dist\空间数据检查工具.exe                       ║
    echo ║  文件大小: !SIZE_MB! MB                                    ║
    echo ╚════════════════════════════════════════════════════════════╝
    echo.
    echo [提示] 建议在目标机器上进行以下测试：
    echo        - 程序能正常启动
    echo        - UI 显示正常（中文无乱码）
    echo        - 文件选择对话框可用
    echo        - SHP 文件读取正常
    echo        - Excel 导出功能正常
    echo.

    :: 询问是否打开输出目录
    set /p OPEN_DIR="是否打开输出目录？(Y/N): "
    if /i "!OPEN_DIR!"=="Y" (
        explorer dist
    )
) else (
    echo.
    echo ╔════════════════════════════════════════════════════════════╗
    echo ║                    打包失败！                              ║
    echo ╚════════════════════════════════════════════════════════════╝
    echo.
    echo [错误] 请检查上方的错误信息，常见问题：
    echo        - 缺少依赖：pip install -r requirements.txt
    echo        - 模块找不到：在 build.spec 的 hiddenimports 中添加
    echo        - 编码问题：确保文件使用 UTF-8 编码
)

echo.
pause