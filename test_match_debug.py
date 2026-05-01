# -*- coding: utf-8 -*-
"""
测试脚本：使用实际的DataValidator和report_reader复现匹配问题
"""
import sys
import os
sys.path.insert(0, r"D:\github\空间数据检查桌面版-主题-design-2026")

from core.report_reader import load_all_reports, load_fubiao1, load_fubiao2, load_fubiao3
from core.data_validator import DataValidator

DATA_ROOT = r"D:\github\空间数据检查桌面版-主题-design-2026\青海24示范小流域-药草沟-20260313\630121_大通"
SHP_FOLDER = DATA_ROOT
FUBIAO_FOLDER = os.path.join(DATA_ROOT, "成果报表")

print("=" * 80)
print("1. 直接用 report_reader 加载附表数据，检查字段名和值")
print("=" * 80)

report_data = load_all_reports(FUBIAO_FOLDER)

for table_key in ['fubiao1', 'fubiao2', 'fubiao3']:
    records = report_data[table_key]['records']
    headers = report_data[table_key]['headers']
    print(f"\n{table_key}: 记录数={len(records)}")
    print(f"  headers = {headers}")
    if records:
        print(f"  第一条记录的keys = {list(records[0].keys())}")
        # 找匹配相关字段
        for rec in records[:3]:
            match_vals = {}
            for k, v in rec.items():
                if '名称' in str(k) or '代码' in str(k) or '编码' in str(k) or '编号' in str(k):
                    match_vals[k] = repr(v)
            if match_vals:
                print(f"  匹配相关: {match_vals}")

print("\n" + "=" * 80)
print("2. 使用 DataValidator 完整流程")
print("=" * 80)

validator = DataValidator()

def progress_cb(msg):
    print(f"  [进度] {msg}")

validator.progress_callback = progress_cb

# 加载附表
validator.load_fubiao(report_data)

# 检查加载后的数据
print(f"\nfubiao1 记录数: {len(validator.fubiao_data.get('fubiao1', []))}")
print(f"fubiao2 记录数: {len(validator.fubiao_data.get('fubiao2', []))}")
print(f"fubiao3 记录数: {len(validator.fubiao_data.get('fubiao3', []))}")

# 检查附表1记录的字段名和值
fubiao1_recs = validator.fubiao_data.get('fubiao1', [])
if fubiao1_recs:
    print(f"\n附表1第一条记录keys: {list(fubiao1_recs[0].keys())}")
    for i, rec in enumerate(fubiao1_recs[:5]):
        name_val = rec.get('5.名称', '<MISSING>')
        code_val = rec.get('6.代码', '<MISSING>')
        print(f"  记录{i}: 5.名称={repr(name_val)}, 6.代码={repr(code_val)}")

# 加载shp
print(f"\n加载shp数据: {SHP_FOLDER}")
shp_ok = validator.load_shp_data(SHP_FOLDER)
print(f"shp加载结果: {shp_ok}")

# 检查shp数据
fangzhi_recs = validator.shp_data.get('fangzhi', [])
yinhuan_recs = validator.shp_data.get('yinhuan', [])
print(f"\n防治对象 shp记录数: {len(fangzhi_recs)}")
print(f"隐患要素 shp记录数: {len(yinhuan_recs)}")

if fangzhi_recs:
    print(f"\n防治对象第一条记录keys: {list(fangzhi_recs[0].keys())}")
    for i, rec in enumerate(fangzhi_recs[:3]):
        name_val = rec.get('名称', '<MISSING>')
        code_val = rec.get('代码', '<MISSING>')
        print(f"  记录{i}: 名称={repr(name_val)}, 代码={repr(code_val)}")

if yinhuan_recs:
    print(f"\n隐患要素第一条记录keys: {list(yinhuan_recs[0].keys())}")
    for i, rec in enumerate(yinhuan_recs[:3]):
        name_val = rec.get('名称', '<MISSING>')
        code_val = rec.get('编号', '<MISSING>')
        print(f"  记录{i}: 名称={repr(name_val)}, 编号={repr(code_val)}")

# 执行校验
print("\n" + "=" * 80)
print("3. 执行校验")
print("=" * 80)
results = validator.validate_all()

print("\n" + "=" * 80)
print("4. 手动构建索引对比")
print("=" * 80)

# 手动模拟附表1匹配
if fangzhi_recs and fubiao1_recs:
    match_fields = {'名称': '5.名称', '代码': '6.代码'}
    shp_match = list(match_fields.keys())
    fb_match = list(match_fields.values())

    print(f"shp匹配字段: {shp_match}")
    print(f"附表匹配字段: {fb_match}")

    shp_index = {}
    for rec in fangzhi_recs:
        key_parts = []
        for f in shp_match:
            val = str(rec.get(f, '')).strip().upper()
            key_parts.append(val)
        key = '|'.join(key_parts)
        if key not in shp_index:
            shp_index[key] = []
        shp_index[key].append(rec)

    fb_index = {}
    for i, rec in enumerate(fubiao1_recs):
        key_parts = []
        for f in fb_match:
            val = str(rec.get(f, '')).strip().upper()
            key_parts.append(val)
        key = '|'.join(key_parts)
        if key not in fb_index:
            fb_index[key] = []
        fb_index[key].append(rec)

    print(f"\nshp索引keys ({len(shp_index)} 个):")
    for k in shp_index:
        print(f"  [{k}]")

    print(f"\n附表索引keys ({len(fb_index)} 个):")
    for k in fb_index:
        print(f"  [{k}]")

    matched = 0
    fb_only = 0
    shp_only = 0
    for key, recs in fb_index.items():
        if key in shp_index:
            matched += len(recs)
        else:
            fb_only += len(recs)
    for key, recs in shp_index.items():
        if key not in fb_index:
            shp_only += len(recs)

    print(f"\n手动匹配结果: 匹配={matched}, 仅附表={fb_only}, 仅shp={shp_only}")
