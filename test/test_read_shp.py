# -*- coding: utf-8 -*-
"""
测试读取水系SHP文件，检查河流名称和河流代码字段
"""

import geopandas as gpd
import sys

shp_path = r"E:\青海\青海山洪四预\审核汇集\630000_空间数据和附表检查\空间数据水系检查\同仁\RIVL-同仁.shp"

print("=" * 60)
print("测试读取水系SHP文件")
print("=" * 60)
print(f"文件路径: {shp_path}")
print()

# 尝试不同编码读取
encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'cp936', 'latin1', 'iso-8859-1']

for encoding in encodings:
    print(f"尝试编码: {encoding}")
    try:
        gdf = gpd.read_file(shp_path, encoding=encoding)
        print(f"  成功! 记录数: {len(gdf)}")
        print(f"  字段列表: {list(gdf.columns)}")

        # 查找河流代码和河流名称字段
        rvcd_field = None
        rvnm_field = None
        for col in gdf.columns:
            col_lower = str(col).lower()
            if col_lower == 'rvcd':
                rvcd_field = col
            elif col_lower == 'rvnm':
                rvnm_field = col

        print(f"  河流代码字段: {rvcd_field}")
        print(f"  河流名称字段: {rvnm_field}")

        if rvcd_field and rvnm_field:
            print()
            print("前5条记录:")
            print("-" * 40)
            for idx in range(min(5, len(gdf))):
                row = gdf.iloc[idx]
                rvcd = row.get(rvcd_field)
                rvnm = row.get(rvnm_field)
                print(f"  记录{idx}: 河流代码={rvcd}, 河流名称={rvnm}")

            # 检查是否有空值
            empty_count = sum(1 for idx in range(len(gdf)) if not gdf.iloc[idx].get(rvnm_field) or str(gdf.iloc[idx].get(rvnm_field)).strip() in ['', 'nan', 'None'])
            print()
            print(f"河流名称为空的记录数: {empty_count}/{len(gdf)}")
        else:
            print("  未找到 rvcd/rvnm 字段!")

        print()
        break  # 成功读取后退出循环

    except Exception as e:
        print(f"  失败: {e}")
        print()

print("=" * 60)
print("测试完成")
print("=" * 60)