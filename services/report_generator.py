# -*- coding: utf-8 -*-
"""
Dashboard检查报告生成服务
生成HTML格式的检查报告
"""

import os
from datetime import datetime


def safe_html(s) -> str:
    """HTML安全编码"""
    if s is None:
        return ''
    try:
        text = str(s)
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        text = text.replace('"', '&quot;').replace("'", '&#39;')
        return text
    except Exception:
        return '(编码异常)'


def status_icon(st: str) -> str:
    """状态转图标"""
    rev = {
        'pass': '✅',
        'fail': '❌',
        'warn': '⚠️',
        'error': '🔴',
        'pending': '⏳'
    }
    return rev.get(st, '?')


def status_cn(st: str) -> str:
    """状态转中文"""
    cns = {'pass': '通过', 'fail': '不通过', 'warn': '警告', 'error': '异常', 'pending': '待检查'}
    return cns.get(st, st)


def status_badge(st: str) -> str:
    """状态转CSS badge类名"""
    badge_map = {'pass': 'pass', 'fail': 'fail', 'warn': 'warn', 'error': 'fail', 'pending': 'pend'}
    return badge_map.get(st, 'pend')


def build_report_html(check_result: dict, root_path: str) -> str:
    """
    构建HTML报告内容
    
    Args:
        check_result: 检查结果数据
        root_path: 根目录路径
        
    Returns:
        HTML报告字符串
    """
    d = check_result
    s = d.get('summary', {})
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    root_name = safe_html(os.path.basename(root_path)) if root_path else "未指定"

    fb = d.get('fubiao_check', {})
    sp = d.get('spatial_check', {})
    sec = d.get('section_check', {})
    ph = d.get('photo_check', {})
    cr = d.get('cross_check', {})

    fb_errors = fb.get('errors', [])
    sp_results = sp.get('results', [])
    sec_stats = sec.get('stats', {})
    ph_sum = ph.get('match_result', {}).get('summary', {})
    cr_items = cr.get('items', [])

    fb_rows = ''.join(
        "<tr><td>" + str(i+1) + "</td><td>" + safe_html(e.get('表名','')) + "</td>"
        "<td>" + safe_html(e.get('字段名','')) + "</td>"
        "<td>" + safe_html(e.get('错误类型','')) + "</td>"
        "<td>" + safe_html(e.get('错误描述','')) + "</td>"
        "<td>" + safe_html(e.get('当前值','')) + "</td></tr>"
        for i, e in enumerate(fb_errors)
    )
    sp_rows = ''.join(
        "<tr><td>" + str(i+1) + "</td><td>" + safe_html(r.get('file_name','')) + "</td>"
        "<td style=\"color:" + ('#22c55e' if r.get('status')=='通过' else '#ef4444') + "\">" + safe_html(r.get('status','')) + "</td>"
        "<td>" + str(r.get('total_records',0)) + "</td><td>" + str(r.get('valid_records',0)) + "</td>"
        "<td>" + str(r.get('invalid_records',0)) + "</td></tr>"
        for i, r in enumerate(sp_results)
    )
    cr_rows = ''
    for it in cr_items:
        level_icon = '❌' if it.get('level')=='error' else '⚠️'
        detail_data = it.get('detail', [])
        if isinstance(detail_data, list):
            detail_str = '; '.join(safe_html(str(d)) for d in detail_data[:3])
        else:
            detail_str = safe_html(str(detail_data))
        cr_rows += "<tr><td>" + level_icon + "</td><td>" + safe_html(it.get('category',''))
        cr_rows += "</td><td>" + safe_html(it.get('desc','')) + "</td><td>" + detail_str + "</td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>Dashboard检查报告 - {root_name}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif; background:#f8fafc; color:#1e293b; line-height:1.6; }}
.container {{ max-width:1100px; margin:0 auto; padding:32px 24px; }}
.header {{ background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); color:#fff; padding:32px; border-radius:16px; margin-bottom:24px;
    box-shadow:0 4px 24px rgba(102,126,234,0.3); }}
.header h1 {{ font-size:24px; font-weight:700; }} .header p {{ opacity:.9; font-size:14px; margin-top:4px; }}
.stats-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:24px; }}
.stat-card {{ background:#fff; border-radius:12px; padding:20px; box-shadow:0 1px 3px rgba(0,0,0,.08);
    border-left:4px solid #667eea; transition:transform .2s; }}
.stat-card:hover {{ transform:translateY(-2px); }}
.stat-value {{ font-size:32px; font-weight:800; }} .stat-label {{ font-size:13px; color:#64748b; margin-top:4px; }}
.section {{ background:#fff; border-radius:12px; padding:24px; margin-bottom:16px; box-shadow:0 1px 3px rgba(0,0,0,.08); }}
.section-title {{ font-size:16px; font-weight:700; margin-bottom:16px; display:flex; align-items:center; gap:8px;
    padding-bottom:12px; border-bottom:2px solid #f1f5f9; }}
.status-badge {{ display:inline-block; padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; }}
.badge-pass {{ background:#dcfce7; color:#166534; }} .badge-fail {{ background:#fee2e2; color:#991b1b; }}
.badge-warn {{ background:#fef3c7; color:#92400e; }} .badge-pend {{ background:#f1f5f9; color:#64748b; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }} th {{ background:#f8fafc; padding:10px 12px; text-align:left; font-weight:600;
    border-bottom:2px solid #e2e8f0; white-space:nowrap; }} td {{ padding:8px 12px; border-bottom:1px solid #f1f5f9; }}
tr:hover td {{ background:#f8fafc; }} .num {{ text-align:right; font-variant-numeric:tabular-nums; }}
.footer {{ text-align:center; color:#94a3b8; font-size:12px; margin-top:24px; padding:16px; }}
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>📊 Dashboard 汇总检查报告</h1>
<p>项目: {root_name} &nbsp;|&nbsp; 生成时间: {now}</p>
</div>

<div class="stats-grid">
<div class="stat-card"><div class="stat-value">{s.get('total_errors',0)}</div><div class="stat-label">❌ 总错误数</div></div>
<div class="stat-card"><div class="stat-value">{s.get('total_warnings',0)}</div><div class="stat-label">⚠️ 总警告数</div></div>
<div class="stat-card"><div class="stat-value">{status_icon(s.get('overall_status',''))} {status_cn(s.get('overall_status',''))}</div><div class="stat-label">📊 综合评定</div></div>
<div class="stat-card"><div class="stat-value">{max(0,100-s.get('total_errors',0)*5-s.get('total_warnings',0)*2)}</div><div class="stat-label">🎯 健康评分</div></div>
</div>

<div class="section">
<div class="section-title">📋 附表1/2/3检查 <span class="status-badge badge-{status_badge(fb.get('status',''))}">{status_cn(fb.get('status',''))}</span></div>
<p>共发现 <strong>{len(fb_errors)}</strong> 个问题</p>
<table><thead><tr><th>#</th><th>表名</th><th>字段名</th><th>错误类型</th><th>错误描述</th><th>当前值</th></tr></thead>
<tbody>{fb_rows if fb_rows else '<tr><td colspan="6" style="text-align:center;color:#94a3b8;">无问题</td></tr>'}</tbody></table>
</div>

<div class="section">
<div class="section-title">🗺️ 空间数据检查 <span class="status-badge badge-{status_badge(sp.get('status',''))}">{status_cn(sp.get('status',''))}</span></div>
<p>共检查 <strong>{len(sp_results)}</strong> 个图层</p>
<table><thead><tr><th>#</th><th>文件名</th><th>状态</th><th>总记录</th><th>有效</th><th>无效</th></tr></thead>
<tbody>{sp_rows if sp_rows else '<tr><td colspan="6" style="text-align:center;color:#94a3b8;">无数据</td></tr>'}</tbody></table>
</div>

<div class="section">
<div class="section-title">📖 断面数据检查 <span class="status-badge badge-{status_badge(sec.get('status',''))}">{status_cn(sec.get('status',''))}</span></div>
<p>总断面: <strong>{sec_stats.get('total_sections',0)}</strong> &nbsp;|
测点: <strong>{sec_stats.get('total_points',0)}</strong> &nbsp;|
异常: <strong>{sec_stats.get('anomaly_count',0)}</strong> &nbsp;|
校验错误: <strong>{sec_stats.get('validation_error_count',0)}</strong></p>
</div>

<div class="section">
<div class="section-title">📷 照片匹配检查 <span class="status-badge badge-{status_badge(ph.get('status',''))}">{status_cn(ph.get('status',''))}</span></div>
<p>附表2: {ph_sum.get('fubiao2_total',0)}条 ({ph_sum.get('fubiao2_matched',0)}匹配/{ph_sum.get('fubiao2_unmatched',0)}未匹配) &nbsp;|&nbsp;
附表3: {ph_sum.get('fubiao3_total',0)}条 ({ph_sum.get('fubiao3_matched',0)}匹配/{ph_sum.get('fubiao3_unmatched',0)}未匹配)</p>
</div>

<div class="section">
<div class="section-title">🔗 交叉校验 <span class="status-badge badge-{status_badge(cr.get('status',''))}">{status_cn(cr.get('status',''))}</span></div>
<p>错误: <strong>{len(cr.get('errors',[]))}</strong> &nbsp;|&nbsp; 警告: <strong>{len(cr.get('warnings',[]))}</strong></p>
<table><thead><tr><th>级别</th><th>类别</th><th>描述</th><th>详情</th></tr></thead>
<tbody>{cr_rows if cr_rows else '<tr><td colspan="4" style="text-align:center;color:#94a3b8;">无问题</td></tr>'}</tbody></table>
</div>

<div class="footer">由空间数据检查桌面版自动生成 &copy; {now.split()[0]}</div>
</div>
</body>
</html>"""
    return html