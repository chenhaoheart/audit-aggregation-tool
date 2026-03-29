# -*- coding: utf-8 -*-
"""
检测SHP文件的编码格式
通过读取DBF文件的LDID（Language Driver ID）来判断编码
"""
from __future__ import print_function
import os
import sys

# Python 2 编码设置
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')

def detect_shp_encoding(shp_path):
    """
    检测SHP文件的编码格式

    LDID值对照:
    - 0x00: 未指定/ANSI
    - 0x64 (100): GBK/CP936 (简体中文)
    - 0x65 (101): Big5 (繁体中文)
    - 0x78 (120): UTF-8
    """
    try:
        # 方法1: 使用pyshp读取
        try:
            import shapefile
            r = shapefile.Reader(shp_path)

            # 获取编码信息
            encoding = getattr(r, 'encoding', None)
            ldid = None

            # 尝试读取DBF头部的LDID
            dbf_path = shp_path.replace('.shp', '.dbf')
            if os.path.exists(dbf_path):
                with open(dbf_path, 'rb') as f:
                    f.seek(29)  # LDID在DBF文件的第29字节
                    ldid_byte = f.read(1)
                    ldid = ord(ldid_byte) if ldid_byte else None

            print("\n文件: " + os.path.basename(shp_path))
            print("-" * 50)

            # 显示字段名
            print("字段列表:")
            for i, f in enumerate(r.fields):
                if f[0] != 'DeletionFlag':
                    field_name = f[0]
                    # 计算字段名字节长度
                    try:
                        gbk_len = len(field_name.encode('gbk'))
                        utf8_len = len(field_name.encode('utf-8'))
                        print(u"  {} - GBK:{}字节, UTF-8:{}字节".format(field_name, gbk_len, utf8_len))
                    except:
                        print(u"  {}".format(field_name))

            print("")
            print("编码信息:")
            print(u"  pyshp检测编码: {}".format(encoding or u'未知'))
            print(u"  LDID值: {} (0x{:02X})".format(ldid or '未知', ldid or 0))

            # 解析LDID
            if ldid == 0x64:
                print(u"  实际编码: GBK (简体中文)")
            elif ldid == 0x65:
                print(u"  实际编码: Big5 (繁体中文)")
            elif ldid == 0x78 or ldid == 0x00:
                print(u"  实际编码: 可能是UTF-8或ANSI")
            elif ldid:
                print(u"  实际编码: 其他编码 (CP{})".format(ldid))

            r.close()
            return ldid, encoding

        except ImportError:
            print("pyshp未安装，尝试直接读取DBF...")

            # 方法2: 直接读取DBF文件头
            dbf_path = shp_path.replace('.shp', '.dbf')
            if os.path.exists(dbf_path):
                with open(dbf_path, 'rb') as f:
                    f.seek(29)
                    ldid = ord(f.read(1))

                    # 读取字段描述（从32字节开始）
                    f.seek(0)
                    header = f.read(32)
                    header_size = ord(header[8]) + (ord(header[9]) << 8)

                    # 读取字段定义
                    pos = 32
                    fields = []
                    while pos < header_size - 1:
                        f.seek(pos)
                        field_name_bytes = f.read(11)
                        # 尝试不同编码解码
                        try:
                            field_name = field_name_bytes.rstrip('\x00').decode('gbk')
                        except:
                            try:
                                field_name = field_name_bytes.rstrip('\x00').decode('utf-8')
                            except:
                                field_name = field_name_bytes.rstrip('\x00').decode('latin-1')

                        if field_name:
                            fields.append(field_name)
                        pos += 32

                    print("\n文件: " + os.path.basename(shp_path))
                    print("-" * 50)
                    print("字段列表:")
                    for fn in fields:
                        try:
                            gbk_len = len(fn.encode('gbk'))
                            utf8_len = len(fn.encode('utf-8'))
                            print(u"  {} - GBK:{}字节, UTF-8:{}字节".format(fn, gbk_len, utf8_len))
                        except:
                            print(u"  {}".format(fn))

                    print("")
                    print(u"LDID值: {} (0x{:02X})".format(ldid, ldid))

                    if ldid == 0x64:
                        print(u"实际编码: GBK (简体中文)")
                    elif ldid == 0x00:
                        print(u"实际编码: ANSI/未指定 (可能UTF-8)")
                    else:
                        print(u"实际编码: CP{}".format(ldid))

                    return ldid, None

    except Exception as e:
        print(u"检测失败: {}".format(str(e)))
        import traceback
        traceback.print_exc()
        return None, None


def scan_folder(folder):
    """扫描文件夹中的所有SHP文件"""
    print(u"\n扫描目录: " + folder)
    print("=" * 60)

    shp_files = []
    for root, dirs, files in os.walk(folder):
        for f in files:
            if f.lower().endswith('.shp'):
                shp_files.append(os.path.join(root, f))

    if not shp_files:
        print(u"未找到SHP文件")
        return

    print(u"找到 {} 个SHP文件\n".format(len(shp_files)))

    gbk_count = 0
    utf8_count = 0
    other_count = 0

    for shp in shp_files:
        ldid, enc = detect_shp_encoding(shp)
        if ldid == 0x64:
            gbk_count += 1
        elif ldid == 0x00 or ldid == 0x78:
            utf8_count += 1
        else:
            other_count += 1

    print("\n" + "=" * 60)
    print(u"统计结果:")
    print(u"  GBK编码文件: {} 个".format(gbk_count))
    print(u"  UTF-8/ANSI编码文件: {} 个".format(utf8_count))
    print(u"  其他编码文件: {} 个".format(other_count))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.isdir(path):
            scan_folder(path)
        elif os.path.isfile(path) and path.lower().endswith('.shp'):
            detect_shp_encoding(path)
        else:
            print(u"无效路径: " + path)
    else:
        print(u"用法: python detect_shp_encoding.py <SHP文件或目录>")
        print(u"\n示例:")
        print(u"  python detect_shp_encoding.py E:\\数据\\xxx.shp")
        print(u"  python detect_shp_encoding.py E:\\数据\\")