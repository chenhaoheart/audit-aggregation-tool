# -*- coding: utf-8 -*-
"""
完整测试SHP格式化流程 - 修复版
"""
from __future__ import print_function
import os
import sys

# 设置GBK编码
os.environ['ESRI_ENCODING'] = 'GBK'
os.environ['SHAPE_ENCODING'] = 'GBK'

if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('gbk')
    import locale
    locale.setlocale(locale.LC_ALL, 'chs')
    unicode = str

import arcpy
arcpy.env.overwriteOutput = True

def log(msg):
    try:
        print(msg)
        sys.stdout.flush()
    except:
        pass

# 输入输出路径
input_shp = r"E:\青海\2026_03_24_湟中空间图层\化隆20260324-改(2)\化隆小流域隐患要素.shp"
output_dir = r"E:\青海\2026_03_24_湟中空间图层_统一属性字段\tests"
output_shp = os.path.join(output_dir, "隐患要素分布L.shp")

# 字段映射规则 - 调整候选字段顺序，中文名优先
field_mapping = {
    u"名称": [u"名称", "NAME", "Name", "name"],
    u"编号": [u"编号", u"编码", "PID", "pid", "Pid"],
    u"类别": [u"类别", "TYPE", "TYPES", "types", "TYPBS"],
    u"河流名称": [u"河流名", u"河流名称", "RVNM", "RVNAME", "rvname", "RAVNME", "RVNAVB"],
    u"河流代码": [u"河流代", u"河流代码", "RVCD", "rvcd"]
}

log("Input: " + input_shp)
log("Output: " + output_shp)
log("")

# 检查输入文件
if not arcpy.Exists(input_shp):
    log("ERROR: Input file not found")
    sys.exit(1)

# 读取源字段 - 打印所有字段信息
in_fields_all = [f.name for f in arcpy.ListFields(input_shp)]
log("Source fields (" + str(len(in_fields_all)) + "):")
for i, f in enumerate(in_fields_all):
    log("  [{}] {}".format(i, repr(f)))

# 匹配字段
log("")
log("Matching fields:")
src_map = {}
used_fields = set()  # 已使用的字段

for target, candidates in field_mapping.items():
    src = None
    for cand in candidates:
        for f in in_fields_all:
            if f in used_fields:
                continue
            # 转换为unicode比较
            try:
                if sys.version_info[0] == 2:
                    f_u = f.decode('gbk') if isinstance(f, str) else unicode(f)
                else:
                    f_u = f
                cand_u = cand if isinstance(cand, unicode) else unicode(cand)
                if f_u == cand_u:
                    src = f
                    break
            except:
                # 直接比较
                if f == cand:
                    src = f
                    break
        if src:
            used_fields.add(src)
            break
    src_map[target] = src
    if src:
        log("  {} <- {}".format(target, repr(src)))
    else:
        log("  {} <- NOT FOUND".format(target))

# 创建输出目录
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 删除已存在的输出
if arcpy.Exists(output_shp):
    arcpy.Delete_management(output_shp)

# 创建新的SHP
log("")
desc = arcpy.Describe(input_shp)
arcpy.CreateFeatureclass_management(
    out_path=output_dir,
    out_name="隐患要素分布L.shp",
    geometry_type=desc.shapeType,
    spatial_reference=desc.spatialReference
)
log("SHP created")

# 添加字段
target_fields = list(field_mapping.keys())
for fn in target_fields:
    try:
        arcpy.AddField_management(output_shp, fn, "TEXT", field_length=255)
        log("  Added: " + fn)
    except Exception as e:
        log("  Add FAILED: " + str(e))

# 检查实际创建的字段名
actual_fields = [f.name for f in arcpy.ListFields(output_shp)]
actual_field_names = [f for f in actual_fields if f.lower() not in ['fid', 'shape', 'objectid', 'id']]
log("")
log("Actual fields: " + str(len(actual_field_names)))

# 准备游标字段
in_cursor_fields = ["SHAPE@"]
for target in target_fields:
    src = src_map.get(target)
    if src:
        in_cursor_fields.append(src)

out_cursor_fields = ["SHAPE@"] + actual_field_names

log("")
log("Cursor fields:")
log("  In:  " + str(len(in_cursor_fields)))
log("  Out: " + str(len(out_cursor_fields)))

# 复制数据 - 使用老版本游标API（编码处理更稳定）
log("")
log("Copying data...")
count = 0
errors = 0
try:
    with arcpy.da.InsertCursor(output_shp, out_cursor_fields) as icur:
        # 使用老版本SearchCursor
        try:
            scur = arcpy.SearchCursor(input_shp)
        except Exception as e:
            log("  SearchCursor error: " + str(e))
            scur = None

        if scur:
            while True:
                try:
                    row = scur.next()
                    if not row:
                        break
                except StopIteration:
                    break
                except Exception as e:
                    errors += 1
                    if errors <= 5:
                        log("  Read error: " + str(e))
                    continue

                try:
                    new_row = [row.Shape]  # SHAPE
                    for target in target_fields:
                        src = src_map.get(target)
                        if src:
                            raw_val = row.getValue(src)
                        else:
                            raw_val = None
                        final_val = ""
                        if raw_val is not None:
                            try:
                                # 尝试GBK解码
                                if isinstance(raw_val, str) and sys.version_info[0] == 2:
                                    try:
                                        final_val = raw_val.decode('gbk').strip()
                                    except:
                                        final_val = raw_val.strip()
                                else:
                                    final_val = unicode(raw_val).strip()
                            except:
                                try:
                                    final_val = str(raw_val).strip()
                                except:
                                    final_val = ""
                        new_row.append(final_val)
                    icur.insertRow(new_row)
                    count += 1
                except Exception as e:
                    errors += 1
                    if errors <= 10:
                        log("  Insert error: " + str(e))
            del scur
    log("Copied " + str(count) + " records, " + str(errors) + " errors")
except Exception as e:
    log("FATAL ERROR: " + str(e))
    import traceback
    traceback.print_exc()

# 验证输出
log("")
log("Verifying output...")
try:
    count_out = int(arcpy.GetCount_management(output_shp).getOutput(0))
    log("Output records: " + str(count_out))
except:
    pass

out_fields = [f.name for f in arcpy.ListFields(output_shp)]
for f in out_fields:
    if f.lower() not in ['fid', 'shape', 'objectid', 'id']:
        log("  " + f)

log("")
log("Done!")