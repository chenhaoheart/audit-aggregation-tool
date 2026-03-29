# -*- coding: utf-8 -*-
"""
测试使用ArcGIS Python创建带中文长字段名的SHP文件
"""
from __future__ import print_function
import os
import sys
import arcpy

# 设置GBK编码
os.environ['ESRI_ENCODING'] = 'GBK'
os.environ['SHAPE_ENCODING'] = 'GBK'

if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('gbk')
    import locale
    locale.setlocale(locale.LC_ALL, 'chs')
    unicode = str

arcpy.env.overwriteOutput = True

def log(msg):
    """安全输出"""
    try:
        print(msg)
        sys.stdout.flush()
    except:
        pass

# 输出目录
output_dir = r"E:\青海\2026_03_24_湟中空间图层_统一属性字段\tests"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

output_shp = os.path.join(output_dir, "test_fields.shp")

log("Creating SHP: " + output_dir)

# 创建点要素类
arcpy.CreateFeatureclass_management(
    out_path=output_dir,
    out_name="test_fields.shp",
    geometry_type="POINT",
    spatial_reference=arcpy.SpatialReference(4326)
)

log("SHP created")

# 添加字段 - 使用中文字段名
field_names = [u"名称", u"编号", u"类别", u"河流名称", u"河流代码"]

for fn in field_names:
    try:
        arcpy.AddField_management(output_shp, fn, "TEXT", field_length=255)
        log("  Added field OK")
    except Exception as e:
        log("  Add field FAILED: " + str(e))

# 检查实际创建的字段名
log("")
log("Actual field names:")
fields = arcpy.ListFields(output_shp)
for f in fields:
    fname = f.name
    if fname.lower() not in ['fid', 'shape', 'objectid', 'id']:
        log("  " + fname)

# 添加测试数据
log("")
log("Adding test data...")

# 使用实际字段名
actual_fields = [f.name for f in arcpy.ListFields(output_shp)]
data_fields = ["SHAPE@"] + [f for f in actual_fields if f.lower() not in ['fid', 'shape', 'objectid', 'id']]

log("Field list: " + str(len(data_fields)) + " fields")

try:
    with arcpy.da.InsertCursor(output_shp, data_fields) as cur:
        point = arcpy.Point(100.5, 36.5)
        row = [point, u"测试名称1", u"001", u"类别A", u"黄河", u"H001"]
        cur.insertRow(row)
        log("  Inserted 1 record OK")
except Exception as e:
    log("  Insert FAILED: " + str(e))

log("")
log("Done!")
log("Output: " + output_shp)