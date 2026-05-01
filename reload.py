# -*- coding: utf-8 -*-
"""
手动触发热重载命令
执行此脚本会通知 dev_hot_reload.py 立即重载
"""
from pathlib import Path
from datetime import datetime

trigger_file = Path(__file__).parent / '.reload_trigger'
trigger_file.write_text(datetime.now().isoformat(), encoding='utf-8')
print("[触发重载] 已发送重载信号")