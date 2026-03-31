# -*- coding: utf-8 -*-
"""
独立测试脚本 - 用于打包后验证读取SHP文件
"""

import sys
import os

# 设置编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

import geopandas as gpd

shp_path = r"E:\青海\青海山洪四预\审核汇集\630000_空间数据和附表检查\空间数据水系检查\同仁\RIVL-同仁.shp"

def main():
    print("=" * 60)
    print("测试读取水系SHP文件 (打包后验证)")
    print("=" * 60)
    print(f"Python: {sys.version}")
    print(f"geopandas: {gpd.__version__}")
    print(f"文件路径: {shp_path}")
    print()

    if not os.path.exists(shp_path):
        print(f"文件不存在!")
        return

    # 尝试不同编码读取
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'cp936', 'latin1']

    success = False
    for encoding in encodings:
        print(f"尝试编码: {encoding}")
        try:
            gdf = gpd.read_file(shp_path, encoding=encoding)
            print(f"  成功! 记录数: {len(gdf)}")
            print(f"  字段: {list(gdf.columns)}")

            rvcd_field = None
            rvnm_field = None
            for col in gdf.columns:
                col_lower = str(col).lower()
                if col_lower == 'rvcd':
                    rvcd_field = col
                elif col_lower == 'rvnm':
                    rvnm_field = col

            if rvcd_field and rvnm_field:
                print()
                print("前5条记录:")
                for idx in range(min(5, len(gdf))):
                    row = gdf.iloc[idx]
                    rvcd = row.get(rvcd_field)
                    rvnm = row.get(rvnm_field)
                    print(f"  记录{idx}: 河流代码={rvcd}, 河流名称={rvnm}")
                success = True
                break
            else:
                print(f"  未找到 rvcd/rvnm 字段!")

        except Exception as e:
            print(f"  失败: {type(e).__name__}: {e}")

    if not success:
        print()
        print("所有编码尝试失败，尝试不指定编码:")
        try:
            gdf = gpd.read_file(shp_path)
            print(f"成功! 记录数: {len(gdf)}")
            print(f"字段: {list(gdf.columns)}")
        except Exception as e:
            print(f"失败: {type(e).__name__}: {e}")

    print()
    print("=" * 60)
    print("测试完成")
    input("按回车键退出...")

if __name__ == '__main__':
    main()