"""
验证修复：测试附表2与SHP数据匹配
"""
import sys
sys.path.insert(0, r'd:\github\空间数据检查桌面版-主题-design-2026')

from core.report_reader import load_all_reports
from core.checker import WaterSystemChecker
from core.config_manager import get_shp_match_config
import os

def verify_fix():
    root_path = r'E:\青海\青海山洪四预\青海23\最终提交成果-0430\630106_湟中'

    # 1. 加载附表数据（使用修复后的逻辑）
    print("=" * 80)
    print("1. 加载附表数据（使用修复后的字段名）")
    print("=" * 80)
    report_data = load_all_reports(root_path)

    fubiao2_records = report_data.get('fubiao2', {}).get('records', [])
    print(f"附表2记录数: {len(fubiao2_records)}")

    fb2_codes = set()
    for i, r in enumerate(fubiao2_records):
        code = str(r.get('6.编码', '') or r.get('6.编号', '')).strip()
        if code:
            fb2_codes.add(code)
            print(f"✅ 附表2 记录{i}: 找到编号 {code}")

    print(f"\nfb2_codes集合: {fb2_codes}")

    # 2. 查找SHP文件（在电子数据文件夹）
    print("\n" + "=" * 80)
    print("2. 查找SHP文件")
    print("=" * 80)

    subfolder = root_path
    for item in os.listdir(subfolder):
        item_path = os.path.join(subfolder, item)
        if os.path.isdir(item_path) and '电子数据' in item:
            spatial_folder = item_path
            break

    print(f"空间数据文件夹: {spatial_folder}")
    print(f"SHP文件列表:")
    for item in os.listdir(spatial_folder):
        if item.endswith('.shp'):
            print(f"  {item}")

    # 3. 加载SHP数据
    print("\n" + "=" * 80)
    print("3. 加载SHP数据")
    print("=" * 80)

    checker = WaterSystemChecker(spatial_folder, None)
    check_results = checker.process_all()

    shp_cfg = get_shp_match_config()
    yinhuan_kw = shp_cfg.get_layer_keyword('yinhuan')
    yinhuan = [r for r in checker.all_records if yinhuan_kw in r.get('源文件', '')]

    print(f"隐患要素记录数: {len(yinhuan)}")

    yh_codes = set()
    for i, rec in enumerate(yinhuan):
        code = str(rec.get('编号', '')).strip()
        if code:
            yh_codes.add(code)
            print(f"✅ 隐患要素 记录{i}: 找到编号 {code}")

    print(f"\nyh_codes集合: {yh_codes}")

    # 4. 比较结果
    print("\n" + "=" * 80)
    print("4. 匹配结果分析")
    print("=" * 80)

    print(f"\nfb2_codes (附表2): {fb2_codes}")
    print(f"yh_codes (SHP): {yh_codes}")

    fb2_only = fb2_codes - yh_codes
    yh_only = yh_codes - fb2_codes

    print(f"\n仅在附表中存在 (fb2_only): {fb2_only}")
    print(f"仅在SHP中存在 (yh_only): {yh_only}")

    if not fb2_only and not yh_only and fb2_codes and yh_codes:
        print("\n✅✅✅ 修复成功！所有记录完全匹配！")
    elif yh_only:
        print(f"\n❌ 仍然存在问题！SHP中有{len(yh_only)}条记录在附表2/3中不存在:")
        for code in yh_only:
            print(f"  - {repr(code)}")
    else:
        print("\n⚠️ 需要进一步检查")

if __name__ == '__main__':
    verify_fix()
