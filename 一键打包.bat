@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo           空间数据检查工具 v2.0 - 一键打包脚本
echo ============================================================
echo.

:: 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python
    exit /b 1
)

:: 检查 PyInstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [提示] 未安装 PyInstaller，正在安装...
    pip install pyinstaller -q
)

:: 显示版本信息
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PY_VER=%%i
echo [信息] Python: %PY_VER%
for /f "tokens=2" %%i in ('python -c "import PyInstaller; print(PyInstaller.__version__)" 2^>^&1') do set PI_VER=%%i
echo [信息] PyInstaller: %PI_VER%
echo.

:: 清理旧文件
echo [1/2] 清理旧打包文件...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
echo       完成
echo.

:: 打包
echo [2/2] 开始打包...
python -m PyInstaller build.spec --clean

:: 检查结果
if exist "dist\空间数据检查工具_v2.0.0_*.exe" (
    for %%A in ("dist\空间数据检查工具_v2.0.0_*.exe") do (
        set EXE_FILE=%%A
        set SIZE=%%~zA
    )
    set /a SIZE_MB=!SIZE! / 1048576
    echo.
    echo ============================================================
    echo                    打包成功！
    echo ============================================================
    echo   输出: !EXE_FILE!
    echo   大小: !SIZE_MB! MB
    echo ============================================================
    echo.
    explorer dist
) else (
    echo.
    echo [错误] 打包失败，请检查错误信息
)