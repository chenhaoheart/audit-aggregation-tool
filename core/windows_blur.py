# -*- coding: utf-8 -*-
"""
Windows 毛玻璃效果模块 - 使用 DWM API 实现真正的系统级模糊效果

支持:
- Windows 10 1803+: SetWindowCompositionAttribute (Acrylic 效果)
- Windows 11: DwmSetWindowAttribute (DWMWA_SYSTEMBACKDROP_TYPE)
- Windows 7/8: DwmExtendFrameIntoClientArea (基础模糊)
"""

import sys
import ctypes
from ctypes import wintypes, Structure, POINTER, byref, sizeof, pointer
from typing import Optional, Tuple

if sys.platform != 'win32':
    HAS_WINDOWS_BLUR = False
else:
    try:
        user32 = ctypes.windll.user32
        dwmapi = ctypes.windll.dwmapi
        HAS_WINDOWS_BLUR = True
    except Exception:
        HAS_WINDOWS_BLUR = False


class ACCENT_POLICY(Structure):
    _fields_ = [
        ("AccentState", wintypes.INT),
        ("AccentFlags", wintypes.INT),
        ("GradientColor", wintypes.DWORD),
        ("AnimationId", wintypes.INT),
    ]


class WINDOWCOMPOSITIONATTRIBDATA(Structure):
    _fields_ = [
        ("Attrib", wintypes.INT),
        ("pvData", POINTER(ACCENT_POLICY)),
        ("cbData", wintypes.INT),
    ]


class MARGINS(Structure):
    _fields_ = [
        ("cxLeftWidth", wintypes.INT),
        ("cxRightWidth", wintypes.INT),
        ("cyTopHeight", wintypes.INT),
        ("cyBottomHeight", wintypes.INT),
    ]


ACCENT_DISABLED = 0
ACCENT_ENABLE_BLURBEHIND = 3
ACCENT_ENABLE_ACRYLICBLURBEHIND = 4

WCA_ACCENT_POLICY = 19

DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_SYSTEMBACKDROP_TYPE = 38
DWMWA_MICA_EFFECT = 35

DWMSBT_DISABLE = 1
DWMSBT_MAINWINDOW = 2
DWMSBT_TRANSIENTWINDOW = 3
DWMSBT_TABBEDWINDOW = 4


def get_windows_version() -> Tuple[int, int, int]:
    """获取 Windows 版本号"""
    if not HAS_WINDOWS_BLUR:
        return (0, 0, 0)
    try:
        version_info = wintypes.DWORD()
        user32.GetVersionExW(byref(version_info))
        major = version_info.value >> 8 & 0xFF
        minor = version_info.value & 0xFF
        return (major, minor, 0)
    except Exception:
        try:
            import platform
            version = platform.version()
            parts = version.split('.')
            return (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0, int(parts[2]) if len(parts) > 2 else 0)
        except Exception:
            return (10, 0, 0)


def enable_blur_behind(hwnd: int, enable: bool = True) -> bool:
    """
    启用基础的 DWM 模糊效果 (Windows 7+)
    
    Args:
        hwnd: 窗口句柄
        enable: 是否启用
    
    Returns:
        是否成功
    """
    if not HAS_WINDOWS_BLUR:
        return False
    
    try:
        margins = MARGINS(-1, -1, -1, -1) if enable else MARGINS(0, 0, 0, 0)
        result = dwmapi.DwmExtendFrameIntoClientArea(hwnd, byref(margins))
        return result == 0
    except Exception as e:
        print(f"启用 DwmExtendFrameIntoClientArea 失败: {e}")
        return False


def enable_acrylic_effect(hwnd: int, color: int = 0x99000000, enable: bool = True) -> bool:
    """
    启用 Windows 10 Acrylic 模糊效果 (需要 Windows 10 1803+)
    
    Args:
        hwnd: 窗口句柄
        color: AARRGGBB 格式的颜色 (AA=透明度, RR=红, GG=绿, BB=蓝)
        enable: 是否启用
    
    Returns:
        是否成功
    """
    if not HAS_WINDOWS_BLUR:
        return False
    
    try:
        accent_state = ACCENT_ENABLE_ACRYLICBLURBEHIND if enable else ACCENT_DISABLED
        accent = ACCENT_POLICY(accent_state, 2, color, 0)
        data = WINDOWCOMPOSITIONATTRIBDATA(WCA_ACCENT_POLICY, pointer(accent), sizeof(accent))
        result = user32.SetWindowCompositionAttribute(hwnd, byref(data))
        return result != 0
    except Exception as e:
        print(f"启用 Acrylic 效果失败: {e}")
        return False


def enable_mica_effect(hwnd: int, enable: bool = True, dark_mode: bool = False) -> bool:
    """
    启用 Windows 11 Mica 效果
    
    Args:
        hwnd: 窗口句柄
        enable: 是否启用
        dark_mode: 是否使用暗色模式
    
    Returns:
        是否成功
    """
    if not HAS_WINDOWS_BLUR:
        return False
    
    try:
        major, minor, _ = get_windows_version()
        if major < 11:
            return enable_acrylic_effect(hwnd, 0x99000000 if dark_mode else 0x99FFFFFF, enable)
        
        backdrop_type = DWMSBT_MAINWINDOW if enable else DWMSBT_DISABLE
        result = dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_SYSTEMBACKDROP_TYPE, 
            byref(wintypes.INT(backdrop_type)), sizeof(wintypes.INT)
        )
        
        if dark_mode:
            dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                byref(wintypes.INT(1)), sizeof(wintypes.INT)
            )
        
        return result == 0
    except Exception as e:
        print(f"启用 Mica 效果失败: {e}")
        return False


def enable_system_blur(hwnd: int, opacity: float = 0.8, dark_mode: bool = False) -> bool:
    """
    根据系统版本自动选择最佳的模糊效果
    
    Args:
        hwnd: 窗口句柄
        opacity: 透明度 (0.0-1.0)
        dark_mode: 是否使用暗色模式
    
    Returns:
        是否成功
    """
    if not HAS_WINDOWS_BLUR:
        return False
    
    major, minor, build = get_windows_version()
    
    alpha = int(opacity * 255)
    if dark_mode:
        color = (alpha << 24) | 0x000000
    else:
        color = (alpha << 24) | 0xFFFFFF
    
    if major >= 11:
        return enable_mica_effect(hwnd, True, dark_mode)
    elif major >= 10 and build >= 17134:
        return enable_acrylic_effect(hwnd, color, True)
    else:
        return enable_blur_behind(hwnd, True)


def disable_system_blur(hwnd: int) -> bool:
    """
    禁用系统模糊效果
    
    Args:
        hwnd: 窗口句柄
    
    Returns:
        是否成功
    """
    if not HAS_WINDOWS_BLUR:
        return False
    
    major, minor, build = get_windows_version()
    
    if major >= 11:
        return enable_mica_effect(hwnd, False)
    elif major >= 10 and build >= 17134:
        return enable_acrylic_effect(hwnd, 0, False)
    else:
        return enable_blur_behind(hwnd, False)


def get_hwnd_from_widget(widget) -> Optional[int]:
    """
    从 Qt Widget 获取 Windows 窗口句柄
    
    Args:
        widget: QWidget 实例
    
    Returns:
        窗口句柄或 None
    """
    try:
        from PySide6.QtWidgets import QWidget
        if not isinstance(widget, QWidget):
            return None
        
        win_id = widget.winId()
        if hasattr(win_id, 'toInt'):
            hwnd = win_id.toInt()[0]
        else:
            hwnd = int(win_id)
        return hwnd
    except Exception as e:
        print(f"获取窗口句柄失败: {e}")
        return None


class WindowsBlurManager:
    """
    Windows 毛玻璃效果管理器
    
    用法:
        blur_manager = WindowsBlurManager()
        blur_manager.apply_blur(main_window, opacity=0.8)
    """
    
    def __init__(self):
        self._current_hwnd: Optional[int] = None
        self._blur_enabled: bool = False
        self._current_opacity: float = 0.8
    
    def is_available(self) -> bool:
        """检查系统是否支持毛玻璃效果"""
        return HAS_WINDOWS_BLUR
    
    def apply_blur(self, widget, opacity: float = 0.8, dark_mode: bool = False) -> bool:
        """
        为 Widget 应用毛玻璃效果
        
        Args:
            widget: QWidget 实例
            opacity: 透明度 (0.0-1.0)
            dark_mode: 是否使用暗色模式
        
        Returns:
            是否成功
        """
        hwnd = get_hwnd_from_widget(widget)
        if hwnd is None:
            return False
        
        self._current_hwnd = hwnd
        self._current_opacity = opacity
        self._blur_enabled = True
        
        return enable_system_blur(hwnd, opacity, dark_mode)
    
    def update_opacity(self, opacity: float, dark_mode: bool = False) -> bool:
        """
        更新透明度
        
        Args:
            opacity: 新的透明度 (0.0-1.0)
            dark_mode: 是否使用暗色模式
        
        Returns:
            是否成功
        """
        if self._current_hwnd is None:
            return False
        
        self._current_opacity = opacity
        return enable_system_blur(self._current_hwnd, opacity, dark_mode)
    
    def remove_blur(self) -> bool:
        """
        移除毛玻璃效果
        
        Returns:
            是否成功
        """
        if self._current_hwnd is None:
            return False
        
        self._blur_enabled = False
        return disable_system_blur(self._current_hwnd)
    
    def is_blur_enabled(self) -> bool:
        """检查当前是否启用了模糊效果"""
        return self._blur_enabled
    
    def get_current_opacity(self) -> float:
        """获取当前透明度"""
        return self._current_opacity


_blur_manager: Optional[WindowsBlurManager] = None


def get_blur_manager() -> WindowsBlurManager:
    """获取全局毛玻璃效果管理器"""
    global _blur_manager
    if _blur_manager is None:
        _blur_manager = WindowsBlurManager()
    return _blur_manager