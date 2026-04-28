# -*- coding: utf-8 -*-
"""
动画效果管理模块 - 提供可复用的动画和视觉效果组件
"""

from typing import Optional, Tuple, Callable
from PySide6.QtWidgets import QWidget, QGraphicsDropShadowEffect, QPushButton, QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import (
    QPropertyAnimation, QEasingCurve, QTimer, Property,
    QSequentialAnimationGroup, QParallelAnimationGroup, Signal, Slot,
    QObject, QEvent, Qt
)
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont
from core.theme_manager import get_theme_manager
from core.theme_manager import ThemeMode


class AnimatedWidgetMixin:
    """
    为控件添加动画能力的混入类
    使用方式: class MyWidget(QWidget, AnimatedWidgetMixin): ...
    """

    def setup_animation_properties(self):
        """初始化动画属性"""
        self._opacity = 1.0
        self._scale = 1.0
        self._hover_glow_opacity = 0.0

        # 动画对象
        self._opacity_animation: Optional[QPropertyAnimation] = None
        self._scale_animation: Optional[QPropertyAnimation] = None
        self._glow_animation: Optional[QPropertyAnimation] = None

    def get_opacity(self) -> float:
        return self._opacity

    def set_opacity(self, value: float):
        self._opacity = value
        # 更新样式表的透明度
        if hasattr(self, '_apply_opacity'):
            self._apply_opacity(value)

    opacity = Property(float, get_opacity, set_opacity)

    def get_scale(self) -> float:
        return self._scale

    def set_scale(self, value: float):
        self._scale = value
        # 通过调整大小来模拟缩放
        if hasattr(self, '_original_geometry'):
            orig = self._original_geometry
            scaled_w = int(orig.width() * value)
            scaled_h = int(orig.height() * value)
            offset_x = (orig.width() - scaled_w) // 2
            offset_y = (orig.height() - scaled_h) // 2
            self.setGeometry(
                orig.x() + offset_x,
                orig.y() + offset_y,
                scaled_w, scaled_h
            )

    scale = Property(float, get_scale, set_scale)

    def animate_opacity(self, target: float, duration: int = 250,
                        easing: QEasingCurve.Type = QEasingCurve.OutCubic):
        """透明度动画"""
        if self._opacity_animation:
            self._opacity_animation.stop()

        self._opacity_animation = QPropertyAnimation(self, b"opacity")
        self._opacity_animation.setDuration(duration)
        self._opacity_animation.setStartValue(self._opacity)
        self._opacity_animation.setEndValue(target)
        self._opacity_animation.setEasingCurve(easing)
        self._opacity_animation.start()

        # 确保动画完成后不会被删除
        self._opacity_animation.setParent(self)

    def animate_scale(self, target: float, duration: int = 150,
                      easing: QEasingCurve.Type = QEasingCurve.OutCubic):
        """缩放动画"""
        if not hasattr(self, '_original_geometry'):
            self._original_geometry = self.geometry()

        if self._scale_animation:
            self._scale_animation.stop()

        self._scale_animation = QPropertyAnimation(self, b"scale")
        self._scale_animation.setDuration(duration)
        self._scale_animation.setStartValue(self._scale)
        self._scale_animation.setEndValue(target)
        self._scale_animation.setEasingCurve(easing)
        self._scale_animation.start()
        self._scale_animation.setParent(self)

    def animate_scale_click(self):
        """点击缩放反馈动画"""
        # 缩放到 0.95 然后恢复
        if hasattr(self, '_original_geometry'):
            self._original_geometry = self.geometry()

        seq = QSequentialAnimationGroup(self)

        # 缩小
        shrink = QPropertyAnimation(self, b"scale")
        shrink.setDuration(100)
        shrink.setStartValue(1.0)
        shrink.setEndValue(0.95)
        shrink.setEasingCurve(QEasingCurve.OutCubic)
        seq.addAnimation(shrink)

        expand = QPropertyAnimation(self, b"scale")
        expand.setDuration(100)
        expand.setStartValue(0.95)
        expand.setEndValue(1.0)
        expand.setEasingCurve(QEasingCurve.InOutCubic)
        seq.addAnimation(expand)

        seq.start()


class ShadowHelper:
    """阴影效果助手"""

    @staticmethod
    def add_shadow(widget: QWidget, blur_radius: int = 20,
                   offset: Tuple[int, int] = (0, 4),
                   color: str = "#00000030") -> QGraphicsDropShadowEffect:
        """
        为控件添加阴影效果

        Args:
            widget: 目标控件
            blur_radius: 阴影模糊半径
            offset: 阴影偏移 (x, y)
            color: 阴影颜色（支持十六进制带透明度）

        Returns:
            阴影效果对象
        """
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(blur_radius)
        shadow.setOffset(offset[0], offset[1])

        # 解析颜色
        qcolor = ShadowHelper._parse_color(color)
        shadow.setColor(qcolor)

        widget.setGraphicsEffect(shadow)
        return shadow

    @staticmethod
    def _parse_color(color_str: str) -> QColor:
        """解析颜色字符串，支持 #RRGGBBAA 格式"""
        if color_str.startswith('#'):
            hex_val = color_str[1:]
            if len(hex_val) == 8:  # RRGGBBAA
                r = int(hex_val[0:2], 16)
                g = int(hex_val[2:4], 16)
                b = int(hex_val[4:6], 16)
                a = int(hex_val[6:8], 16)
                return QColor(r, g, b, a)
            elif len(hex_val) == 6:  # RRGGBB
                r = int(hex_val[0:2], 16)
                g = int(hex_val[2:4], 16)
                b = int(hex_val[4:6], 16)
                return QColor(r, g, b, 255)

        # 尝试直接解析
        return QColor(color_str)

    @staticmethod
    def add_card_shadow(widget: QWidget, is_dark: bool = None) -> QGraphicsDropShadowEffect:
        """添加卡片阴影效果（自动适配主题）"""
        theme = get_theme_manager().get_current_theme()
        if is_dark is None:
            # Auto-detect from theme mode
            is_dark = get_theme_manager().mode in (ThemeMode.DARK, ThemeMode.AURORA)
        if is_dark:
            return ShadowHelper.add_shadow(
                widget, blur_radius=25, offset=(0, 6),
                color=theme.get('shadow_color', '#00000040')
            )
        else:
            return ShadowHelper.add_shadow(
                widget, blur_radius=12, offset=(0, 2),
                color=theme.get('shadow_color', 'rgba(0,0,0,0.04)')
            )


class GlassmorphismHelper:
    """玻璃态效果助手 - 明亮通透的毛玻璃"""

    @staticmethod
    def apply_glass_style(widget: QWidget,
                          bg_alpha: float = None,
                          border_alpha: float = None,
                          corner_radius: int = None,
                          glow_color: str = None,
                          inner_glow: bool = True):
        """
        为控件应用玻璃态样式

        Args:
            widget: 目标控件
            bg_alpha: 背景透明度 (0-1)，默认使用主题
            border_alpha: 边框透明度 (0-1)，默认使用主题
            corner_radius: 圆角半径，默认使用主题
            glow_color: 发光颜色，默认使用主题
            inner_glow: 是否添加内发光效果
        """
        theme = get_theme_manager().get_current_theme()
        if bg_alpha is None:
            bg_alpha = 0.78
        if border_alpha is None:
            border_alpha = 0.35
        if corner_radius is None:
            corner_radius = int(theme.get('glass_corner_radius', '16'))
        if glow_color is None:
            glow_color = theme.get('glow_primary', 'rgba(232,168,56,0.20)')

        glass_bg = theme.get('glass_bg', f'rgba(255, 255, 255, {bg_alpha})')
        glass_border = theme.get('glass_border', f'rgba(200, 200, 200, {border_alpha})')
        accent = theme.get('accent_color', '#e8a838')

        inner_glow_style = ""
        if inner_glow:
            inner_glow_style = f"""
            {widget.__class__.__name__} {{
                box-shadow: inset 0 1px 0 rgba(255,255,255,0.50);
            }}
            """

        style = f"""
            {widget.__class__.__name__} {{
                background: {glass_bg};
                border: 1px solid {glass_border};
                border-radius: {corner_radius}px;
            }}
            {widget.__class__.__name__}:hover {{
                border: 1px solid {glow_color};
                background: {glass_bg};
            }}
            {inner_glow_style}
        """
        widget.setStyleSheet(style)

    @staticmethod
    def get_glass_stylesheet(corner_radius: int = None,
                             bg_alpha: float = None,
                             border_alpha: float = None,
                             inner_highlight: bool = True) -> str:
        """
        生成玻璃态样式表字符串

        Args:
            corner_radius: 圆角半径
            bg_alpha: 背景透明度
            border_alpha: 边框透明度
            inner_highlight: 是否添加顶部高光线

        Returns:
            样式表字符串
        """
        theme = get_theme_manager().get_current_theme()
        if corner_radius is None:
            corner_radius = int(theme.get('glass_corner_radius', '16'))
        if bg_alpha is None:
            bg_alpha = 0.78
        if border_alpha is None:
            border_alpha = 0.35

        glass_bg = theme.get('glass_bg', f'rgba(255, 255, 255, {bg_alpha})')
        glass_border = theme.get('glass_border', f'rgba(200, 200, 200, {border_alpha})')

        highlight = ""
        if inner_highlight:
            highlight = "border-top: 1px solid rgba(255,255,255,0.50);"

        return f"""
            background: {glass_bg};
            border: 1px solid {glass_border};
            border-radius: {corner_radius}px;
            {highlight}
        """

    @staticmethod
    def apply_frosted_panel(widget: QWidget, intensity: str = "medium"):
        """
        为控件应用毛玻璃面板效果（多层透明度叠加）

        Args:
            widget: 目标控件
            intensity: 透明度强度 "light"/"medium"/"heavy"
        """
        theme = get_theme_manager().get_current_theme()
        corner_radius = int(theme.get('glass_corner_radius', '16'))

        intensity_map = {
            "light": {"bg": "rgba(255,255,255,0.55)", "border": "rgba(200,200,200,0.25)"},
            "medium": {"bg": "rgba(255,255,255,0.78)", "border": "rgba(200,200,200,0.35)"},
            "heavy": {"bg": "rgba(255,255,255,0.92)", "border": "rgba(200,200,200,0.45)"},
        }
        config = intensity_map.get(intensity, intensity_map["medium"])

        style = f"""
            {widget.__class__.__name__} {{
                background: {config['bg']};
                border: 1px solid {config['border']};
                border-radius: {corner_radius}px;
                border-top: 1px solid rgba(255,255,255,0.60);
            }}
            {widget.__class__.__name__}:hover {{
                border: 1px solid {theme.get('glow_primary', 'rgba(232,168,56,0.20)')};
            }}
        """
        widget.setStyleSheet(style)


class AnimationPresets:
    """预设动画效果"""

    @staticmethod
    def slide_in(widget: QWidget, direction: str = 'left',
                duration: int = 300, callback: Callable = None):
        """
        滑入动画

        Args:
            widget: 目标控件
            direction: 方向 ('left', 'right', 'top', 'bottom')
            duration: 动画时长（毫秒）
            callback: 动画完成回调
        """
        geometry = widget.geometry()

        # 根据方向设置起始位置
        if direction == 'left':
            start_geo = geometry.adjusted(-geometry.width(), 0, -geometry.width(), 0)
        elif direction == 'right':
            start_geo = geometry.adjusted(geometry.width(), 0, geometry.width(), 0)
        elif direction == 'top':
            start_geo = geometry.adjusted(0, -geometry.height(), 0, -geometry.height())
        elif direction == 'bottom':
            start_geo = geometry.adjusted(0, geometry.height(), 0, geometry.height())
        else:
            start_geo = geometry

        widget.setGeometry(start_geo)

        anim = QPropertyAnimation(widget, b"geometry")
        anim.setDuration(duration)
        anim.setStartValue(start_geo)
        anim.setEndValue(geometry)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        if callback:
            anim.finished.connect(callback)

        anim.start()
        anim.setParent(widget)

        return anim

    @staticmethod
    def fade_in(widget: QWidget, duration: int = 250, callback: Callable = None):
        """淡入动画"""
        if hasattr(widget, 'get_opacity') and hasattr(widget, 'set_opacity'):
            widget.set_opacity(0)
            widget.animate_opacity(1.0, duration)
            if callback:
                widget._opacity_animation.finished.connect(callback)
        else:
            from PySide6.QtWidgets import QGraphicsOpacityEffect
            from PySide6.QtCore import QPropertyAnimation, QEasingCurve
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
            effect.setOpacity(0.0)
            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(duration)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            if callback:
                anim.finished.connect(callback)
            anim.start()
            widget._fade_in_anim = anim
            widget._fade_in_effect = effect

    @staticmethod
    def scale_in(widget: QWidget, duration: int = 200, callback: Callable = None):
        """缩放入场动画"""
        if hasattr(widget, 'animate_scale'):
            widget.animate_scale(1.0, duration)
            if callback and hasattr(widget, '_scale_animation'):
                widget._scale_animation.finished.connect(callback)


class ShimmerProgress:
    """
    进度条发光条纹动画效果
    使用 QTimer 定时更新样式表中的渐变位置
    """

    def __init__(self, progress_bar: QWidget, update_interval: int = 50,
                 color_start: str = None, color_end: str = None,
                 bg_color: str = None, highlight: str = None):
        """
        Args:
            progress_bar: 进度条控件
            update_interval: 更新间隔（毫秒）
            color_start: 渐变起始色（默认使用主题色）
            color_end: 渐变结束色（默认使用主题色）
            bg_color: 背景色（默认使用主题色）
            highlight: 高亮色
        """
        self.progress_bar = progress_bar
        self._offset = 0
        self._timer = QTimer(progress_bar)
        self._timer.timeout.connect(self._update_shimmer)
        self._update_interval = update_interval
        self._base_style = ""

        theme = get_theme_manager().get_current_theme()
        self._shimmer_color_start = color_start or theme.get('progress_chunk_start', '#667eea')
        self._shimmer_color_end = color_end or theme.get('progress_chunk_end', '#764ba2')
        self._shimmer_highlight = highlight or "#ffffff50"
        self._progress_bg = bg_color or theme.get('progress_bg', '#ecf0f1')
        self._progress_border = theme.get('progress_border', '#e0e4e8')

    def set_colors(self, start: str, end: str, highlight: str = "#ffffff50"):
        """设置发光颜色"""
        self._shimmer_color_start = start
        self._shimmer_color_end = end
        self._shimmer_highlight = highlight

    def start(self):
        """启动 shimmer 动画"""
        self._timer.start(self._update_interval)

    def stop(self):
        """停止 shimmer 动画"""
        self._timer.stop()

    def _update_shimmer(self):
        """更新 shimmer 偏移"""
        self._offset = (self._offset + 3) % 100

        # 计算渐变位置
        shimmer_start = self._offset
        shimmer_mid = self._offset + 15
        shimmer_end = self._offset + 30

        # 限制范围
        if shimmer_mid > 100:
            shimmer_mid = shimmer_mid - 100
            shimmer_end = shimmer_end - 100

        # 从父控件获取实际高度，不再写死
        bar_height = self.progress_bar.height()

        # 构建带 shimmer 的样式
        # 注意：Qt 的 qlineargradient 使用 0-1 的坐标系统
        shimmer_style = f"""
            QProgressBar {{
                background: {self._progress_bg};
                border: 1px solid {self._progress_border};
                border-radius: 4px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(
                    x1:{shimmer_start/100}, y1:0,
                    x2:{shimmer_end/100}, y2:0,
                    stop:0 {self._shimmer_color_start},
                    stop:0.5 {self._shimmer_highlight},
                    stop:1 {self._shimmer_color_end}
                );
                border-radius: 3px;
            }}
        """

        self.progress_bar.setStyleSheet(shimmer_style)


class PulseGlowLabel(QLabel):
    """
    脉冲发光标签 - 用于状态指示
    """

    def __init__(self, text: str = "", parent: QWidget = None, glow_color: str = None):
        super().__init__(text, parent)
        self._glow_opacity = 0.0
        self._pulse_active = False
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._toggle_pulse)
        theme = get_theme_manager().get_current_theme()
        self._glow_color = glow_color or theme.get('success_text', '#22c55e')

    def get_glow_opacity(self) -> float:
        return self._glow_opacity

    def set_glow_opacity(self, value: float):
        self._glow_opacity = value
        # 使用样式表模拟发光
        alpha = int(value * 255)
        glow_hex = f"{alpha:02x}"

        # 从颜色中提取 RGB
        color = QColor(self._glow_color)
        r, g, b = color.red(), color.green(), color.blue()

        style = f"""
            QLabel {{
                color: {self._glow_color};
                background: transparent;
                border: 2px solid rgba({r}, {g}, {b}, {alpha});
                border-radius: 5px;
                padding: 3px 8px;
            }}
        """
        self.setStyleSheet(style)

    glow_opacity = Property(float, get_glow_opacity, set_glow_opacity)

    def start_pulse(self, interval: int = 1000, color: str = "#22c55e"):
        """启动脉冲动画"""
        self._glow_color = color
        self._pulse_active = True
        self._pulse_timer.start(interval)

        # 创建动画
        self._pulse_animation = QPropertyAnimation(self, b"glow_opacity")
        self._pulse_animation.setDuration(500)
        self._pulse_animation.setStartValue(0.0)
        self._pulse_animation.setEndValue(0.8)
        self._pulse_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self._pulse_animation.setLoopCount(-1)  # 无限循环
        self._pulse_animation.setParent(self)
        self._pulse_animation.start()

    def stop_pulse(self):
        """停止脉冲动画"""
        self._pulse_active = False
        self._pulse_timer.stop()
        if hasattr(self, '_pulse_animation'):
            self._pulse_animation.stop()
        self.set_glow_opacity(0)

    def _toggle_pulse(self):
        """切换脉冲状态（备用）"""
        pass


class AnimatedSidebar:
    """
    侧边栏动画助手
    处理展开/折叠的平滑动画
    """

    def __init__(self, sidebar: QWidget, collapsed_width: int = 60,
                 expanded_width: int = 200):
        """
        Args:
            sidebar: 侧边栏控件
            collapsed_width: 折叠宽度
            expanded_width: 展开宽度
        """
        self.sidebar = sidebar
        self.collapsed_width = collapsed_width
        self.expanded_width = expanded_width
        self.is_collapsed = False

        self._width_animation: Optional[QPropertyAnimation] = None
        self._opacity_animation: Optional[QPropertyAnimation] = None

    def toggle(self, duration: int = 300, easing: QEasingCurve.Type = QEasingCurve.OutCubic):
        """切换侧边栏状态"""
        self.is_collapsed = not self.is_collapsed
        target_width = self.collapsed_width if self.is_collapsed else self.expanded_width

        # 创建宽度动画
        self._width_animation = QPropertyAnimation(self.sidebar, b"minimumWidth")
        self._width_animation.setDuration(duration)
        self._width_animation.setStartValue(self.sidebar.width())
        self._width_animation.setEndValue(target_width)
        self._width_animation.setEasingCurve(easing)
        self._width_animation.setParent(self.sidebar)
        self._width_animation.start()

        self._max_width_animation = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self._max_width_animation.setDuration(duration)
        self._max_width_animation.setStartValue(self.sidebar.width())
        self._max_width_animation.setEndValue(target_width)
        self._max_width_animation.setEasingCurve(easing)
        self._max_width_animation.setParent(self.sidebar)
        self._max_width_animation.start()

        return self.is_collapsed

    def expand(self, duration: int = 300):
        """展开侧边栏"""
        if self.is_collapsed:
            self.toggle(duration)

    def collapse(self, duration: int = 300):
        """折叠侧边栏"""
        if not self.is_collapsed:
            self.toggle(duration)


class ClickFeedbackButton(QPushButton, AnimatedWidgetMixin):
    """
    具有点击反馈动画的按钮
    """

    def __init__(self, text: str = "", parent: QWidget = None):
        QPushButton.__init__(self, text, parent)
        AnimatedWidgetMixin.setup_animation_properties(self)

        self._hover_glow = False
        self._original_style = ""

    def enterEvent(self, event):
        """鼠标进入事件 - 悬停效果"""
        super().enterEvent(event)
        self._hover_glow = True
        # 可以在这里添加悬停发光效果

    def leaveEvent(self, event):
        """鼠标离开事件"""
        super().leaveEvent(event)
        self._hover_glow = False

    def mousePressEvent(self, event):
        """鼠标按下事件 - 点击反馈"""
        # 记录原始几何位置
        self._original_geometry = self.geometry()
        self.animate_scale_click()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        super().mouseReleaseEvent(event)


class ButtonClickHelper(QObject):
    """
    按钮点击动画助手 - 使用事件过滤器方式
    可以为任何 QPushButton 添加点击缩放效果

    使用方法:
        helper = ButtonClickHelper(button)
        button.installEventFilter(helper)
    """

    def __init__(self, button: QPushButton, scale_factor: float = 0.95):
        super().__init__(button)
        self.button = button
        self.scale_factor = scale_factor
        self._original_style = ""
        self._is_pressed = False
        self._scale_timer = QTimer(self)
        self._scale_timer.setSingleShot(True)
        self._scale_timer.timeout.connect(self._restore_scale)

    def eventFilter(self, obj, event):
        """事件过滤器"""
        if obj == self.button:
            if event.type() == QEvent.Type.MouseButtonPress:
                self._apply_scale()
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self._schedule_restore()
            elif event.type() == QEvent.Type.Leave:
                if self._is_pressed:
                    self._restore_scale()
        return False

    def _apply_scale(self):
        """应用缩放效果"""
        self._is_pressed = True
        self._original_style = self.button.styleSheet()
        # 通过修改 padding 模拟缩放效果
        self.button.setStyleSheet(self._original_style + """
            QPushButton {
                padding-top: 11px;
                padding-bottom: 9px;
                padding-left: 21px;
                padding-right: 19px;
            }
        """)

    def _schedule_restore(self):
        """安排恢复"""
        if self._is_pressed:
            self._scale_timer.start(100)  # 100ms 后恢复

    def _restore_scale(self):
        """恢复原始样式"""
        self._is_pressed = False
        self.button.setStyleSheet(self._original_style)


class ButtonShadowHelper:
    """
    按钮阴影效果助手
    """

    @staticmethod
    def add_button_shadow(button: QPushButton, blur: int = 8,
                          offset: tuple = (0, 2), color: str = None):
        """
        为按钮添加阴影效果

        Args:
            button: 目标按钮
            blur: 模糊半径
            offset: 阴影偏移 (x, y)
            color: 阴影颜色，默认使用主题色
        """
        if color is None:
            color = get_theme_manager().get_current_theme().get('shadow_color', '#00000030')
        shadow = QGraphicsDropShadowEffect(button)
        shadow.setBlurRadius(blur)
        shadow.setOffset(offset[0], offset[1])

        # 解析颜色
        qcolor = ShadowHelper._parse_color(color)
        shadow.setColor(qcolor)

        button.setGraphicsEffect(shadow)
        return shadow

    @staticmethod
    def add_glow_effect(button: QPushButton, color: str = None):
        """
        为按钮添加发光效果（使用阴影模拟）

        Args:
            button: 目标按钮
            color: 发光颜色，默认使用主题色
        """
        if color is None:
            color = get_theme_manager().get_current_theme().get('glow_primary', '#667eea40')
        shadow = QGraphicsDropShadowEffect(button)
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 0)  # 发光效果偏移为0

        qcolor = ShadowHelper._parse_color(color)
        shadow.setColor(qcolor)

        button.setGraphicsEffect(shadow)
        return shadow


def get_effects_manager():
    """获取效果管理器实例（兼容旧代码）"""
    return {
        'ShadowHelper': ShadowHelper,
        'GlassmorphismHelper': GlassmorphismHelper,
        'AnimationPresets': AnimationPresets,
        'ShimmerProgress': ShimmerProgress,
        'PulseGlowLabel': PulseGlowLabel,
        'AnimatedSidebar': AnimatedSidebar,
        'ClickFeedbackButton': ClickFeedbackButton,
        'AnimatedWidgetMixin': AnimatedWidgetMixin,
        'StaggerEntrance': StaggerEntrance,
        'TabFadeTransition': TabFadeTransition,
        'ButtonGlowHelper': ButtonGlowHelper,
    }


class StaggerEntrance:
    """
    交错入场动画 - 子控件依次淡入

    用法:
        StaggerEntrance.play(container_widget, stagger_ms=60)
    """

    @staticmethod
    def play(parent: QWidget, stagger_ms: int = 60,
             duration: int = 320, skip_first: bool = False):
        """
        对 parent 的直接子控件依次播放入场动画

        Args:
            parent: 容器控件（如页面自身）
            stagger_ms: 每个子控件之间的延迟（毫秒）
            duration: 单个动画时长（毫秒）
            skip_first: 是否跳过第一个子控件（适用于布局间距元素）
        """
        children = parent.findChildren(QWidget, '', Qt.FindDirectChildrenOnly)
        target_widgets = []
        for child in children:
            if child.objectName() in ('qt_scrollarea_hbar', 'qt_scrollarea_vbar',
                                       'qt_scrollarea_viewport'):
                continue
            target_widgets.append(child)

        if skip_first and target_widgets:
            target_widgets = target_widgets[1:]

        for i, widget in enumerate(target_widgets):
            delay = i * stagger_ms
            StaggerEntrance._animate_single(widget, delay, duration)

    @staticmethod
    def _animate_single(widget: QWidget, delay_ms: int, duration: int):
        """为单个控件播放入场动画"""
        opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity_effect)
        opacity_effect.setOpacity(0.0)

        opacity_anim = QPropertyAnimation(opacity_effect, b"opacity")
        opacity_anim.setDuration(duration)
        opacity_anim.setStartValue(0.0)
        opacity_anim.setEndValue(1.0)
        opacity_anim.setEasingCurve(QEasingCurve.OutCubic)

        def _cleanup():
            widget.setGraphicsEffect(None)

        opacity_anim.finished.connect(_cleanup)

        if delay_ms > 0:
            QTimer.singleShot(delay_ms, opacity_anim.start)
        else:
            opacity_anim.start()

        widget._stagger_anim = opacity_anim


class TabFadeTransition(QObject):
    """
    Tab切换淡入动画

    用法:
        helper = TabFadeTransition(tab_widget)
        helper.attach()
    """

    def __init__(self, tab_widget, duration: int = 200):
        super().__init__(tab_widget)
        self.tab_widget = tab_widget
        self.duration = duration
        self._anim = None

    def attach(self):
        """绑定到 QTabWidget 的 currentChanged 信号"""
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, index: int):
        """Tab切换时播放入场动画"""
        page = self.tab_widget.widget(index)
        if page is None:
            return

        opacity_effect = QGraphicsOpacityEffect(page)
        page.setGraphicsEffect(opacity_effect)
        opacity_effect.setOpacity(0.0)

        if self._anim is not None:
            self._anim.stop()

        self._anim = QPropertyAnimation(opacity_effect, b"opacity")
        self._anim.setDuration(self.duration)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

        def _cleanup():
            page.setGraphicsEffect(None)

        self._anim.finished.connect(_cleanup)
        self._anim.start()


class ButtonGlowHelper(QObject):
    """
    按钮悬停发光效果 - 鼠标进入时添加主题色光晕，离开时移除

    用法:
        ButtonGlowHelper.install(button)
    """

    _instances = {}

    @staticmethod
    def install(button: QPushButton, glow_color: str = None):
        """为按钮安装悬停发光效果"""
        helper = ButtonGlowHelper(button, glow_color)
        button.installEventFilter(helper)
        ButtonGlowHelper._instances[id(button)] = helper
        return helper

    def __init__(self, button: QPushButton, glow_color: str = None):
        super().__init__(button)
        self.button = button
        self._glow_color = glow_color
        self._shadow = None
        self._anim = None

    def _get_glow_color(self) -> QColor:
        if self._glow_color:
            return ShadowHelper._parse_color(self._glow_color)
        theme = get_theme_manager().get_current_theme()
        return ShadowHelper._parse_color(theme.get('glow_primary', '#667eea40'))

    def _show_glow(self):
        if self._shadow is not None:
            return
        color = self._get_glow_color()
        self._shadow = QGraphicsDropShadowEffect(self.button)
        self._shadow.setBlurRadius(16)
        self._shadow.setOffset(0, 0)
        self._shadow.setColor(color)
        self.button.setGraphicsEffect(self._shadow)

    def _hide_glow(self):
        if self._shadow is None:
            return
        self.button.setGraphicsEffect(None)
        self._shadow = None

    def eventFilter(self, obj, event):
        if obj == self.button:
            if event.type() == QEvent.Type.Enter:
                self._show_glow()
            elif event.type() == QEvent.Type.Leave:
                self._hide_glow()
        return False