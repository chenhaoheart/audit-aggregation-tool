"""
调试脚本v2：分析附表2与SHP数据匹配问题
"""
import sys
sys.path.insert(0, r'd:\github\空间数据检查桌面版-主题-design-2026')

from core.report_reader import load_all_reports
from core.checker import WaterSystemChecker
from core.config_manager import get_shp_match_config
import os

def debug_cross_match():
    root_path = r'E:\青海\青海山洪四预\青海23\最终提交成果-0430\630106_湟中'

    # 1. 加载附表数据
    print("=" * 80)
    print("1. 加载附表数据")
    print("=" * 80)
    report_data = load_all_reports(root_path)

    fubiao2_records = report_data.get('fubiao2', {}).get('records', [])
    fubiao2_headers = report_data.get('fubiao2', {}).get('headers', [])
    print(f"附表2记录数: {len(fubiao2_records)}")
    print(f"附表2表头: {fubiao2_headers}")

    if fubiao2_records:
        print(f"\n附表2第一条记录的所有字段:")
        for key, value in fubiao2_records[0].items():
            print(f"  {repr(key)}: {repr(value)}")

    fb2_codes = set()
    for i, r in enumerate(fubiao2_records):
        # 尝试多种可能的字段名
        possible_fields = ['6.编号', '编号', '编码', 'PID']
        code = ''
        for field in possible_fields:
            val = r.get(field, '')
            if val and str(val).strip():
                code = str(val).strip()
                print(f"\n附表2 记录{i}: 使用字段[{field}]找到编号: {repr(code)}")
                break

        if not code:
            print(f"\n附表2 记录{i}: 未找到编号字段！所有字段值:")
            for key, value in r.items():
                if value and str(value).strip():
                    print(f"  {key}: {repr(value)}")

        if code:
            fb2_codes.add(code)

    print(f"\nfb2_codes集合: {fb2_codes}")

    # 2. 查找空间数据文件夹
    print("\n" + "=" * 80)
    print("2. 查找空间数据文件夹")
    print("=" * 80)

    subfolder = root_path
    if os.path.exists(os.path.join(root_path, '630106')):
        subfolder = os.path.join(root_path, '630106')

    print(f"根目录内容:")
    for item in os.listdir(subfolder):
        item_path = os.path.join(subfolder, item)
        print(f"  [{os.path.isdir(item_path)}] {item}")

        # 如果是目录，列出其shp文件
        if os.path.isdir(item_path):
            try:
                for sub_item in os.listdir(item_path):
                    if sub_item.endswith('.shp'):
                        print(f"      -> {sub_item}")
            except:
                pass

    spatial_folder = None
    for item in os.listdir(subfolder):
        item_path = os.path.join(subfolder, item)
        if os.path.isdir(item_path) and '成果' in item:
            spatial_folder = item_path
            break

    if not spatial_folder:
        spatial_folder = subfolder

    print(f"\n选择的空间数据文件夹: {spatial_folder}")
    print(f"该文件夹的shp文件:")
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
    print(f"隐患要素关键词: {yinhuan_kw}")

    yinhuan = [r for r in checker.all_records if yinhuan_kw in r.get('源文件', '')]
    print(f"隐患要素记录数: {len(yinhuan)}")

    # 也检查all_records中是否有任何包含'隐患'或'yinhuan'的记录
    print(f"\nall_records总数: {len(checker.all_records)}")
    for rec in checker.all_records:
        src = rec.get('源文件', '')
        if '隐患' in src or 'yinhuan' in src.lower() or yinhuan_kw in src:
            print(f"  找到隐患相关记录: {src}")

    if yinhuan:
        print(f"\n隐患要素记录详情:")
        for i, rec in enumerate(yinhuan):
            print(f"\n记录{i}:")
            print(f"  源文件: {rec.get('源文件', '')}")
            print(f"  原始字段: {rec.get('_original_columns', [])}")

            # 列出所有字段和值
            print(f"  所有字段:")
            for key, value in rec.items():
                if not key.startswith('_') and value is not None and str(value).strip():
                    print(f"    {repr(key)}: {repr(value)} (type: {type(value).__name__})")

    yh_codes = set()
    for i, rec in enumerate(yinhuan):
        code_by_name = str(rec.get('编号', '')).strip()
        if code_by_name:
            yh_codes.add(code_by_name)
            print(f"\n添加到yh_codes(通过'编号'字段): {repr(code_by_name)}")

        # 尝试其他可能的字段名
        for field in ['PID', 'pid', 'Pid', '编码']:
            val = rec.get(field, '')
            if val and str(val).strip():
                code = str(val).strip()
                print(f"发现字段[{field}]: {repr(code)}")
                if code not in yh_codes:
                    yh_codes.add(code)
                    print(f"添加到yh_codes(通过'{field}'字段): {repr(code)}")

    print(f"\nyh_codes集合: {yh_codes}")

    # 4. 比较结果
    print("\n" + "=" * 80)
    print("4. 匹配结果分析")
    print("=" * 80)

    print(f"\nfb2_codes (附表2): {fb2_codes}")
    print(f"yh_codes (SHP): {yh_codes}")

    if fb2_codes and yh_codes:
        print("\n详细对比每个代码:")
        for fb2_code in fb2_codes:
            for yh_code in yh_codes:
                match = fb2_code == yh_code
                print(f"\n{repr(fb2_code)} vs {repr(yh_code)}")
                print(f"  直接相等: {match}")
                if not match:
                    print(f"  长度: {len(fb2_code)} vs {len(yh_code)}")
                    print(f"  大写相等: {fb2_code.upper() == yh_code.upper()}")
                    # 找出第一个不同的字符
                    for j in range(min(len(fb2_code), len(yh_code))):
                        if fb2_code[j] != yh_code[j]:
                            print(f"  第{j}个字符不同: {repr(fb2_code[j])} (ord={ord(fb2_code[j])}) vs {repr(yh_code[j])} (ord={ord(yh_code[j])})")
                            break

if __name__ == '__main__':
    debug_cross_match()
