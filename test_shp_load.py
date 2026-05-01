# -*- coding: utf-8 -*-
"""
临时测试脚本：验证 shp 文件加载逻辑
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, r'D:\github\空间数据检查桌面版-主题-design-2026')

from core.config_manager import get_shp_match_config
from core.data_validator import DataValidator

def test_shp_loading():
    """测试shp加载"""
    folder_path = r'D:\github\空间数据检查桌面版-主题-design-2026\青海24示范小流域-药草沟-20260313'

    print("=" * 60)
    print("🔍 开始诊断 shp 加载问题")
    print("=" * 60)

    # 1. 检查文件夹是否存在
    print(f"\n📂 根目录: {folder_path}")
    print(f"   存在: {os.path.exists(folder_path)}")

    if not os.path.exists(folder_path):
        print("❌ 根目录不存在！")
        return

    # 2. 列出子文件夹
    subfolders = []
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            subfolders.append(item_path)

    print(f"\n📁 发现 {len(subfolders)} 个子文件夹:")
    for sf in subfolders:
        print(f"   - {os.path.basename(sf)}")

    if not subfolders:
        print("⚠️  未发现任何子文件夹！")
        return

    # 3. 获取配置的文件名
    shp_cfg = get_shp_match_config()
    fangzhi_filename = shp_cfg.get_layer_keyword('fangzhi') + 'P.shp'
    yinhuan_filename = shp_cfg.get_layer_keyword('yinhuan') + 'L.shp'

    print(f"\n⚙️  配置的文件名:")
    print(f"   - 防治对象: {fangzhi_filename}")
    print(f"   - 隐患要素: {yinhuan_filename}")

    # 4. 遍历查找shp文件
    print("\n" + "=" * 60)
    print("🔎 开始扫描子文件夹...")
    print("=" * 60)

    found_fangzhi = []
    found_yinhuan = []

    for subfolder in subfolders:
        subfolder_name = os.path.basename(subfolder)
        print(f"\n📁 扫描: {subfolder_name}")

        file_count = 0
        shp_count = 0

        for root, dirs, files in os.walk(subfolder):
            file_count += len(files)

            for file in files:
                if file.endswith('.shp'):
                    shp_count += 1
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, folder_path)

                    if file == fangzhi_filename:
                        found_fangzhi.append(full_path)
                        print(f"   ✅ 找到防治对象: {rel_path}")
                    elif file == yinhuan_filename:
                        found_yinhuan.append(full_path)
                        print(f"   ✅ 找到隐患要素: {rel_path}")

        print(f"   📊 文件总数: {file_count}, SHP文件数: {shp_count}")

    # 5. 总结
    print("\n" + "=" * 60)
    print("📋 扫描结果总结:")
    print("=" * 60)
    print(f"   防治对象分布P.shp: 找到 {len(found_fangzhi)} 个")
    print(f"   隐患要素分布L.shp: 找到 {len(found_yinhuan)} 个")

    if found_fangzhi:
        print(f"\n   📍 防治对象位置:")
        for fp in found_fangzhi:
            print(f"      {fp}")

    if found_yinhuan:
        print(f"\n   📍 隐患要素位置:")
        for fp in found_yinhuan:
            print(f"      {fp}")

    # 6. 测试实际加载
    print("\n" + "=" * 60)
    print("🧪 测试 DataValidator.load_shp_data()")
    print("=" * 60)

    validator = DataValidator()

    def log_callback(msg):
        print(f"   [日志] {msg}")

    validator.progress_callback = log_callback

    success = validator.load_shp_data(folder_path)

    print(f"\n📊 加载结果:")
    print(f"   返回值: {success}")
    print(f"   防治对象记录数: {len(validator.shp_data['fangzhi'])}")
    print(f"   隐患要素记录数: {len(validator.shp_data['yinhuan'])}")

    if len(validator.shp_data['fangzhi']) > 0:
        print(f"\n   ✅ 成功！示例记录:")
        sample = validator.shp_data['fangzhi'][0]
        print(f"      来源文件夹: {sample.get('_source_folder')}")
        print(f"      字段列表: {list(sample.keys())[:10]}")

if __name__ == '__main__':
    test_shp_loading()
