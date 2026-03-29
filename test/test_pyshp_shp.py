# -*- coding: utf-8 -*-
"""
使用pyshp创建带中文长字段名的SHP文件
"""
from __future__ import print_function
import os
import sys

# Python 2 编码设置
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')

import shapefile

print("pyshp version:", shapefile.__version__)
print()

# 输出目录
output_dir = r"E:\青海\图层格式化测试\pyshp_test"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

output_shp = os.path.join(output_dir, "test_chinese_field")

print("创建SHP:", output_shp)

# 创建shapefile writer - 指定GBK编码
w = shapefile.Writer(output_shp, shapeType=shapefile.POINT, encoding='gbk')

# 设置字段 - 使用中文长字段名
# pyshp默认使用GBK编码（LDID=0x64），字段名按GBK计算长度
field_names = [
    u"名称",
    u"编号",
    u"类别",
    u"河流名称",
    u"河流代码"
]

for fn in field_names:
    # pyshp中，字段名最大10字节（GBK编码下，中文每字2字节）
    # "河流名称" = 8字节 < 10字节限制
    w.field(fn, 'C', size=255)
    print("  创建字段:", fn)

# 添加一条记录
w.point(100.0, 30.0)
w.record(u"测试名称", u"001", u"类别1", u"黄河", u"H001")

# 关闭writer
w.close()

print("\nSHP创建成功!")

# 读取验证 - 指定GBK编码
print("\n读取验证:")
r = shapefile.Reader(output_shp, encoding='gbk')
print("字段列表:")
for i, f in enumerate(r.fields):
    if f[0] != 'DeletionFlag':
        print("  ", i, f[0])

print("\n记录数:", len(r))
if len(r) > 0:
    print("第一条记录:", r.record(0))

r.close()
print("\n测试完成!")