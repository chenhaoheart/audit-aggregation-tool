# -*- coding: utf-8 -*-
"""
SHP格式化处理工作脚本
由主程序通过子进程调用，使用ArcGIS Python环境执行
功能：批量循环查询SHP文件，进行属性映射，生成统一命名的新SHP/GDB文件

兼容 Python 2.7 (ArcGIS Desktop) 和 Python 3.x (ArcGIS Pro)
"""

from __future__ import print_function
import os
import sys
import json
import argparse
import io

# 设置环境变量 - 强制使用GBK编码创建shapefile
os.environ['ESRI_ENCODING'] = 'GBK'
os.environ['SHAPE_ENCODING'] = 'GBK'

# Python 2 编码设置 - 必须在所有代码之前
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('gbk')  # 改为gbk，不是utf-8
else:
    # Python 3 兼容: unicode 不存在，str 就是 unicode
    unicode = str

# 设置ArcGIS环境编码为系统默认(GBK)，避免SHP字段名被截断
if sys.version_info[0] == 2:
    import locale
    locale.setlocale(locale.LC_ALL, 'chs')
    locale.setlocale(locale.LC_CTYPE, 'chs')

# 尝试导入arcpy
try:
    import arcpy
    arcpy.env.overwriteOutput = True
    if sys.version_info[0] == 2:
        arcpy.env.encoding = 'GBK'
    ARCPY_AVAILABLE = True
except ImportError:
    ARCPY_AVAILABLE = False
    print("ERROR: arcpy not available")
    sys.exit(1)


# 关键字段
CRITICAL_TARGETS = [u"名称"]


def to_unicode(s):
    """将字符串转换为 unicode（兼容 Python 2/3）
    注意：ArcGIS创建的SHP字段名是GBK编码，优先使用GBK解码
    """
    if sys.version_info[0] == 2:
        # Python 2
        if isinstance(s, unicode):
            return s
        if isinstance(s, str):
            # 优先尝试GBK解码（ArcGIS DBF字段名编码）
            try:
                return s.decode('gbk')
            except:
                try:
                    return s.decode('utf-8')
                except:
                    return s.decode('gbk', errors='replace')
    # Python 3
    return s if isinstance(s, str) else str(s)


def log(message):
    """输出日志"""
    try:
        print(message)
        sys.stdout.flush()
    except Exception as e:
        try:
            print(message.encode('utf-8', errors='replace'))
            sys.stdout.flush()
        except:
            pass


def is_valid_shp(shp_path):
    """检查SHP文件是否有效"""
    try:
        if not arcpy.Exists(shp_path):
            return False
        count = int(arcpy.GetCount_management(shp_path).getOutput(0))
        return count > 0
    except Exception as e:
        log(u"    警告: 检查文件时出错")
        return False


def find_source_files(folder, keywords):
    """查找匹配关键词的SHP文件"""
    matching_files = []

    for root, dirs, files in os.walk(folder):
        root_u = to_unicode(root)
        if "output" in root_u.lower() or "temp" in root_u.lower():
            continue

        for fname in files:
            fname_u = to_unicode(fname)
            if fname_u.lower().endswith(u".shp"):
                for kw in keywords:
                    kw_u = to_unicode(kw)
                    if kw_u in fname_u:
                        file_path = os.path.join(root, fname)
                        if is_valid_shp(file_path):
                            matching_files.append(file_path)
                            log(u"    找到: " + fname_u)
                        break

    return matching_files


def get_first_existing_field(field_list, candidates):
    """获取第一个存在的字段 - 改进匹配逻辑"""
    for cand in candidates:
        for f in field_list:
            # 将字段名解码为unicode进行比较
            try:
                if sys.version_info[0] == 2:
                    f_u = f.decode('gbk') if isinstance(f, str) else unicode(f)
                else:
                    f_u = f
                cand_u = cand if isinstance(cand, unicode) else unicode(cand)
                if f_u == cand_u:
                    return f
            except:
                if f == cand:
                    return f
    return None


def has_non_empty_value(fc, field_name):
    """检查字段是否有非空值 - 使用老版本游标避免编码问题"""
    try:
        cur = arcpy.SearchCursor(fc)
        for row in cur:
            val = row.getValue(field_name)
            if val is not None:
                try:
                    if sys.version_info[0] == 2:
                        if isinstance(val, str):
                            if val.decode('gbk').strip() != '':
                                return True
                        elif unicode(val).strip() != '':
                            return True
                    elif str(val).strip() != '':
                        return True
                except:
                    if str(val).strip() != '':
                        return True
        del cur
        return False
    except Exception:
        return False


def makedirs_safe(path):
    """安全创建目录（兼容Python 2.7）"""
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise


def export_standardized(in_fc, rule, out_fc):
    """导出标准化后的要素类"""
    try:
        # 设置输出字段名的编码环境
        arcpy.env.outputCoordinateSystem = arcpy.Describe(in_fc).spatialReference

        desc = arcpy.Describe(in_fc)
        in_fields_all = [f.name for f in arcpy.ListFields(in_fc)]

        field_mapping = rule["field_mapping"]

        # 解析字段映射（新格式：数组，保持顺序）
        target_field_list = []  # 目标字段名列表（有序）
        candidates_map = {}  # 目标字段名 -> 候选列表
        for item in field_mapping:
            target_name = item["name"]
            target_field_list.append(target_name)
            candidates_map[target_name] = item["candidates"]

        # 匹配源字段
        src_map = {}
        for target in target_field_list:
            src = get_first_existing_field(in_fields_all, candidates_map[target])
            src_map[target] = src

        # 检查关键字段
        for target in CRITICAL_TARGETS:
            src_field = src_map.get(target)
            if src_field is None or not has_non_empty_value(in_fc, src_field):
                log(u"    警告: 关键字段缺失或无有效值: " + target)
                return False

        # 删除已存在的输出
        if arcpy.Exists(out_fc):
            arcpy.Delete_management(out_fc)

        # 创建输出要素类
        out_folder = os.path.dirname(out_fc)
        out_name = os.path.basename(out_fc)

        if out_folder and not os.path.exists(out_folder):
            makedirs_safe(out_folder)

        # 直接创建SHP文件（使用系统编码GBK，字段名按GBK计算长度）
        # 先创建空的SHP
        arcpy.CreateFeatureclass_management(
            out_path=out_folder,
            out_name=out_name,
            geometry_type=desc.shapeType,
            spatial_reference=desc.spatialReference
        )

        log(u"    创建SHP: " + to_unicode(out_name))

        # 在SHP中添加字段（按配置文件定义的顺序）
        for field_name in target_field_list:
            if field_name.lower() in ["id"]:
                arcpy.AddField_management(out_fc, field_name, "LONG",
                                          field_is_nullable="NULLABLE")
            elif field_name.lower() in ["shape_leng", "objectid"]:
                arcpy.AddField_management(out_fc, field_name, "DOUBLE",
                                          field_is_nullable="NULLABLE")
            else:
                arcpy.AddField_management(out_fc, field_name, "TEXT",
                                          field_length=255,
                                          field_is_nullable="NULLABLE")

        # 检查实际创建的字段名（保持原始编码格式）
        actual_fields = [f.name for f in arcpy.ListFields(out_fc)]
        # 过滤系统字段，保留原始字符串格式
        actual_field_names_raw = []
        for f in actual_fields:
            f_lower = f.lower() if isinstance(f, str) else unicode(f).lower()
            if f_lower not in [u'fid', u'shape', u'id', u'objectid']:
                actual_field_names_raw.append(f)

        # 用于日志显示的unicode版本
        actual_field_names_u = [to_unicode(f) for f in actual_field_names_raw]
        log(u"    创建字段: " + u", ".join(actual_field_names_u))

        # 准备游标字段（按固定顺序）
        real_in_fields = ["SHAPE@"]
        for target in target_field_list:
            src = src_map.get(target)
            if src is not None:
                real_in_fields.append(src)

        # 输出字段名列表 - 使用实际创建的字段名（原始格式）
        out_fields = ["SHAPE@"] + actual_field_names_raw

        missing_fields = [t for t, s in src_map.items() if s is None]
        if missing_fields:
            log(u"    字段缺失: " + u', '.join(missing_fields))

        # 复制数据到SHP - 使用老版本游标API避免编码问题
        count = 0
        try:
            with arcpy.da.InsertCursor(out_fc, out_fields) as icur:
                # 使用老版本SearchCursor
                try:
                    scur = arcpy.SearchCursor(in_fc)
                except Exception as e:
                    log(u"    游标创建失败: " + to_unicode(str(e)))
                    return False

                while True:
                    try:
                        row = scur.next()
                        if not row:
                            break
                    except StopIteration:
                        break
                    except Exception:
                        continue

                    try:
                        new_row = [row.Shape]  # SHAPE
                        for target in target_field_list:
                            src = src_map.get(target)
                            if src:
                                raw_val = row.getValue(src)
                            else:
                                raw_val = None

                            # 类型转换和编码处理
                            if target.lower() in ["id"]:
                                final_val = int(float(raw_val)) if raw_val else 0
                            elif target.lower() in ["objectid", "shape_leng"]:
                                final_val = float(raw_val) if raw_val else 0.0
                            else:
                                final_val = ""
                                if raw_val is not None:
                                    try:
                                        if sys.version_info[0] == 2 and isinstance(raw_val, str):
                                            final_val = raw_val.decode('gbk').strip()
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
                    except Exception:
                        pass
                del scur
        except Exception as e:
            log(u"    数据复制失败: " + to_unicode(str(e)))
            return False

        try:
            arcpy.AddSpatialIndex_management(out_fc)
        except:
            pass

        count = int(arcpy.GetCount_management(out_fc).getOutput(0))
        log(u"    完成: " + to_unicode(out_name) + u" (" + unicode(count) + u" 条)")
        return True

    except Exception as e:
        log(u"    导出失败: " + to_unicode(str(e)))
        return False


def copy_original(in_fc, out_fc, rule_name):
    """原样复制"""
    # 检查输入输出是否为同一文件
    in_path = os.path.normpath(os.path.abspath(in_fc))
    out_path = os.path.normpath(os.path.abspath(out_fc))

    if in_path.lower() == out_path.lower():
        log(u"    跳过: 输入输出为同一文件")
        return

    if arcpy.Exists(out_fc):
        arcpy.Delete_management(out_fc)
    arcpy.Copy_management(in_fc, out_fc)
    log(u"    原样导出: " + to_unicode(os.path.basename(out_fc)))


def process_folder(input_root, output_root, rules):
    """
    处理整个文件夹 - 批量循环查询生成新的统一命名shp文件
    支持两种模式：
    1. 输入目录包含子文件夹（流域），遍历子文件夹处理
    2. 输入目录直接包含SHP文件，直接处理当前目录
    """
    makedirs_safe(output_root)
    results = []

    # 检查输入目录下是否有子文件夹
    subdirs = []
    has_shp_in_root = False

    for item in os.listdir(input_root):
        item_path = os.path.join(input_root, item)
        if os.path.isdir(item_path):
            # 排除 output 和 temp 目录
            item_u = to_unicode(item).lower()
            if 'output' not in item_u and 'temp' not in item_u:
                subdirs.append(item)
        elif item.lower().endswith('.shp'):
            has_shp_in_root = True

    # 决定处理模式
    if subdirs:
        # 模式1：遍历子文件夹
        log(u"检测到子目录模式，遍历处理...")
        process_items = subdirs
    elif has_shp_in_root:
        # 模式2：直接处理当前目录
        log(u"检测到直接SHP模式，处理当前目录...")
        process_items = [u'']  # 空字符串表示直接使用输入目录
    else:
        log(u"未找到可处理的SHP文件或子目录")
        return results

    # 遍历处理
    for basin in process_items:
        if basin:
            basin_path = os.path.join(input_root, basin)
            basin_u = to_unicode(basin)
        else:
            basin_path = input_root
            basin_u = to_unicode(os.path.basename(input_root))

        log(u"\n--- 处理: " + basin_u + u" ---")

        # 遍历每个规则
        for rule in rules:
            output_name = to_unicode(rule['output_name'])
            log(u"  查找: " + output_name)

            # 查找匹配的源文件
            src_files = find_source_files(basin_path, rule["keywords"])
            if not src_files:
                log(u"    未找到匹配文件")
                continue

            # 使用第一个匹配的文件
            src_file = src_files[0]
            if len(src_files) > 1:
                log(u"    找到 " + unicode(len(src_files)) + u" 个文件，使用: " + to_unicode(os.path.basename(src_file)))

            # 输出路径
            if basin:
                out_basin_dir = os.path.join(output_root, basin, u'空间数据')
            else:
                out_basin_dir = output_root
            makedirs_safe(out_basin_dir)
            out_file = os.path.join(out_basin_dir, output_name)

            # 导出标准化后的shp
            success = export_standardized(src_file, rule, out_file)
            if not success:
                copy_original(src_file, out_file, output_name)

            # 统计
            try:
                count = int(arcpy.GetCount_management(out_file).getOutput(0))
            except:
                count = 0

            results.append({
                'basin': basin_u,
                'output_file': output_name,
                'record_count': count,
                'status': u'成功' if success else u'部分成功'
            })

    log(u"\n处理完成!")
    return results


def main():
    parser = argparse.ArgumentParser(description='SHP格式化处理')
    parser.add_argument('--input', required=True, help='输入目录')
    parser.add_argument('--output', required=True, help='输出目录')
    parser.add_argument('--rules', required=True, help='规则JSON文件路径')

    args = parser.parse_args()

    # 将路径参数转换为 unicode（Python 2 兼容）
    input_root = to_unicode(args.input)
    output_root = to_unicode(args.output)
    rules_path = to_unicode(args.rules)

    # 读取规则 - 使用 io.open 兼容 Python 2/3
    with io.open(rules_path, 'r', encoding='utf-8') as f:
        rules = json.load(f)

    # 执行处理
    results = process_folder(input_root, output_root, rules)

    # 输出结果JSON（最后一行）
    print("RESULT:" + json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    main()