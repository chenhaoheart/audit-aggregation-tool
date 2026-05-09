# -*- coding: utf-8 -*-
"""
Dashboard状态常量与映射
"""

STATUS_BADGE_MAP = {
    'pass': 'statusBadgePass',
    'fail': 'statusBadgeFail',
    'warn': 'statusBadgeWarn',
    'error': 'statusBadgeFail',
    'pending': 'statusBadgePending',
    'running': 'statusBadgeRunning',
}

CHECK_CARD_BADGE_MAP = {
    'pass': 'checkCardBadgePass',
    'fail': 'checkCardBadgeFail',
    'warn': 'checkCardBadgeWarn',
    'error': 'checkCardBadgeFail',
    'pending': 'checkCardBadgePending',
    'running': 'checkCardBadgeRunning',
}

STATUS_RING_COLORS = {
    'pass': 'success_text',
    'fail': 'error_text',
    'warn': 'warning_text',
    'error': 'error_text',
    'pending': 'text_muted',
    'running': 'accent_color',
}

STATUS_ICONS = {
    'pass': '\u2705',
    'fail': '\u274c',
    'warn': '\u26a0\ufe0f',
    'error': '\ud83d\udd34',
    'pending': '\u23f3',
    'running': '\U0001f504',
}

STATUS_TEXTS = {
    'pass': '\u2705 通过',
    'fail': '\u274c 不通过',
    'warn': '\u26a0\ufe0f 警告',
    'error': '\ud83d\udd34 异常',
    'pending': '\u23f3 待检查',
    'running': '\U0001f504 检查中...',
}
