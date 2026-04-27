# -*- coding: utf-8 -*-
"""
页面过渡动画管理器
为 QStackedWidget 提供平滑的切换动画
"""

from PySide6.QtWidgets import QStackedWidget, QGraphicsOpacityEffect
from PySide6.QtCore import QPropertyAnimation, QEasingCurve


class PageAnimator:
    """页面切换动画 - 通过透明度实现 QStackedWidget 平滑过渡"""

    @staticmethod
    def fade_transition(stack: QStackedWidget, new_index: int, duration: int = 220):
        """
        淡入淡出切换页面

        Args:
            stack: QStackedWidget 实例
            new_index: 目标页面索引
            duration: 动画时长（毫秒）
        """
        old_index = stack.currentIndex()
        if old_index == new_index:
            return

        # 先切换索引（QStackedWidget 会自动隐藏旧页面、显示新页面）
        stack.setCurrentIndex(new_index)

        new_widget = stack.widget(new_index)

        # 对新页面做淡入动画
        effect = QGraphicsOpacityEffect(new_widget)
        new_widget.setGraphicsEffect(effect)
        effect.setOpacity(0.0)

        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def _cleanup():
            new_widget.setGraphicsEffect(None)

        anim.finished.connect(_cleanup)
        anim.start()

        # 保持动画引用防止被 GC
        new_widget._page_anim = anim
