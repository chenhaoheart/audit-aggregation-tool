# -*- coding: utf-8 -*-
"""
测试使用GDAL创建带中文长字段名的SHP文件
"""
from __future__ import print_function
import os
import sys

# Python 2 编码设置
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')

print("Python:", sys.version)
print()

# 测试GDAL是否可用
try:
    from osgeo import ogr, osr
    print("GDAL/ ogr 可用")
    print("OGR 版本:", ogr.GetVersionInfo())
except ImportError as e:
    print("GDAL不可用:", e)
except Exception as e:
    print("GDAL导入错误:", e)

# 如果GDAL可用，尝试创建带中文长字段名的SHP
if 'ogr' in dir():
    print("\n尝试创建SHP...")
    try:
        # 创建输出目录
        output_dir = r"E:\青海\图层格式化测试\gdal_test"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        output_shp = os.path.join(output_dir, "test_chinese_field.shp")

        # 创建shapefile
        driver = ogr.GetDriverByName("ESRI Shapefile")
        if os.path.exists(output_shp):
            driver.DeleteDataSource(output_shp)

        ds = driver.CreateDataSource(output_shp)

        # 创建空间参考
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)

        # 创建图层
        layer = ds.CreateLayer("test_chinese_field", srs, ogr.wkbPoint)

        # 创建字段 - 设置编码为GBK
        # 在GDAL中，可以使用ogr.OFTString创建文本字段
        # 字段名限制：shapefile是10字节，但GDAL可能按不同编码计算

        field_names = [
            u"名称",
            u"编号",
            u"类别",
            u"河流名称",
            u"河流代码"
        ]

        for fn in field_names:
            field_defn = ogr.FieldDefn(fn.encode('gbk') if sys.version_info[0] == 2 else fn, ogr.OFTString)
            field_defn.SetWidth(255)
            layer.CreateField(field_defn)
            print("  创建字段:", fn)

        # 创建一个要素
        feature_defn = layer.GetLayerDefn()
        feature = ogr.Feature(feature_defn)
        feature.SetGeometry(ogr.CreateGeometryFromWkt("POINT (0 0)"))

        # 设置字段值
        for i, fn in enumerate(field_names):
            feature.SetField(i, "测试值" + fn)

        layer.CreateFeature(feature)

        # 清理
        feature = None
        ds = None

        print("\nSHP创建成功:", output_shp)

        # 读取验证
        ds = ogr.Open(output_shp)
        layer = ds.GetLayer()
        print("\n实际字段名:")
        for i in range(layer.GetLayerDefn().GetFieldCount()):
            field_defn = layer.GetLayerDefn().GetFieldDefn(i)
            print("  ", field_defn.GetName())
        ds = None

    except Exception as e:
        print("创建失败:", e)
        import traceback
        traceback.print_exc()