# -*- coding: utf-8 -*-
"""
编码兼容性测试脚本
测试 Python 2.7 (ArcMap) 和 Python 3.x (ArcGIS Pro) 的编码兼容性
"""

from __future__ import print_function
import os
import sys
import io

# Python 2 编码设置
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
else:
    unicode = str

print("=" * 50)
print("Python 版本: {}".format(sys.version))
print("=" * 50)


def to_unicode(s):
    """将字符串转换为 unicode（兼容 Python 2/3）"""
    if sys.version_info[0] == 2:
        # Python 2
        if isinstance(s, unicode):
            return s
        if isinstance(s, str):
            try:
                return s.decode('utf-8')
            except:
                try:
                    return s.decode('gbk')
                except:
                    return s.decode('utf-8', errors='replace')
    # Python 3
    return s if isinstance(s, str) else str(s)


def test_to_unicode():
    """测试 to_unicode 函数"""
    print("\n--- 测试 to_unicode ---")

    # 测试1: 中文 UTF-8 字符串
    test_cases = [
        u"隐患要素分布L.shp",           # unicode 字符串
        "隐患要素分布L.shp",            # 字节字符串 (UTF-8)
        "乐都空间数据",                  # 中文
        "test_english",                 # 英文
        b"byte_string",                 # 字节
    ]

    for i, tc in enumerate(test_cases):
        try:
            result = to_unicode(tc)
            print("  测试 {}: {} -> {} [OK]".format(i+1, repr(tc), repr(result)))
        except Exception as e:
            print("  测试 {}: {} -> FAILED: {}".format(i+1, repr(tc), e))
            return False

    return True


def test_string_operations():
    """测试字符串操作"""
    print("\n--- 测试字符串操作 ---")

    # 模拟从 JSON 读取的关键词
    keywords = [u"隐患", u"要素", u"L"]
    fname = to_unicode("隐患要素分布L.shp")

    for kw in keywords:
        kw_u = to_unicode(kw)
        try:
            if kw_u in fname:
                print("  关键词 '{}' 在文件名中找到 [OK]".format(kw_u))
            else:
                print("  关键词 '{}' 不在文件名中 [OK]".format(kw_u))
        except Exception as e:
            print("  关键词 '{}' 检查失败: {}".format(kw_u, e))
            return False

    return True


def test_json_io():
    """测试 JSON 读写"""
    print("\n--- 测试 JSON 读写 ---")

    import tempfile
    import json

    # 测试数据
    test_data = {
        "output_name": "隐患要素分布L.shp",
        "keywords": ["隐患", "要素", "L"],
        "field_mapping": {
            "名称": ["名称", "NAME", "name"],
            "类型": ["类型", "TYPE", "type"]
        }
    }

    # 写入临时文件
    temp_file = tempfile.mktemp(suffix=".json")
    try:
        # 写入 - Python 2 需要确保 unicode
        with io.open(temp_file, 'w', encoding='utf-8') as f:
            json_str = json.dumps(test_data, ensure_ascii=False, indent=2)
            if sys.version_info[0] == 2 and isinstance(json_str, str):
                json_str = json_str.decode('utf-8')
            f.write(json_str)
        print("  JSON 写入成功 [OK]")

        # 读取
        with io.open(temp_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)

        # 验证 - 检查关键值是否可正确访问和使用
        output_name = to_unicode(loaded.get("output_name", ""))
        if output_name == u"隐患要素分布L.shp":
            print("  JSON 读取验证成功 [OK]")
        else:
            print("  JSON 读取验证失败: output_name={}".format(output_name))
            return False

        # 验证嵌套结构
        field_mapping = loaded.get("field_mapping", {})
        if u"名称" in [to_unicode(k) for k in field_mapping.keys()]:
            print("  JSON 嵌套结构验证成功 [OK]")
        else:
            print("  JSON 嵌套结构验证失败")
            return False

        return True

    except Exception as e:
        print("  JSON 操作失败: {}".format(e))
        return False
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_path_operations():
    """测试路径操作"""
    print("\n--- 测试路径操作 ---")

    paths = [
        u"E:/青海/2026_03_24_湟中空间图层",
        "E:/青海/2026_03_24_湟中空间图层",
        u"C:\\用户\\测试\\空间数据",
    ]

    for p in paths:
        try:
            p_u = to_unicode(p)
            basename = os.path.basename(p_u)
            dirname = os.path.dirname(p_u)
            print("  路径: {} -> basename: {} [OK]".format(p_u, basename))
        except Exception as e:
            print("  路径操作失败: {} -> {}".format(p, e))
            return False

    return True


def test_field_comparison():
    """测试字段比较"""
    print("\n--- 测试字段比较 ---")

    # 模拟字段列表 - 使用实际字段名
    field_list = ["FID", "Shape", "名称", "河流名称", "河流代码", "类型", "CODE"]

    def get_first_existing_field(field_list, candidates):
        for cand in candidates:
            cand_u = to_unicode(cand)
            for f in field_list:
                if to_unicode(f) == cand_u:
                    return cand
        return None

    # 实际使用场景测试
    test_cases = [
        (["河流名称", "NAME"], "河流名称"),
        (["河流代码", "CODE"], "河流代码"),
        (["名称", "河流名称"], "名称"),  # 名称字段存在
        (["类型", "TYPE"], "类型"),
        (["NotExist", "None"], None),
    ]

    for candidates, expected in test_cases:
        result = get_first_existing_field(field_list, candidates)
        if result == expected:
            print("  候选 {} -> 找到: {} [OK]".format(candidates, result))
        else:
            print("  候选 {} -> 期望: {}, 实际: {} [FAIL]".format(candidates, expected, result))
            return False

    return True


def main():
    """运行所有测试"""
    print("\n开始编码兼容性测试...\n")

    tests = [
        ("to_unicode 函数", test_to_unicode),
        ("字符串操作", test_string_operations),
        ("JSON 读写", test_json_io),
        ("路径操作", test_path_operations),
        ("字段比较", test_field_comparison),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print("\n{} 测试异常: {}".format(name, e))
            results.append((name, False))

    # 汇总
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print("=" * 50)

    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print("  {} : {}".format(name, status))
        if not passed:
            all_passed = False

    print("\n总计: {}/{} 通过".format(sum(1 for _, p in results if p), len(results)))

    if all_passed:
        print("\n所有测试通过!")
        return 0
    else:
        print("\n存在失败的测试!")
        return 1


if __name__ == "__main__":
    sys.exit(main())