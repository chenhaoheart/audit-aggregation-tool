# -*- coding: utf-8 -*-
import sys
import os
import arcpy

reload(sys)
sys.setdefaultencoding('utf-8')

os.environ['ESRI_ENCODING'] = 'GBK'
os.environ['SHAPE_ENCODING'] = 'GBK'

def test_shp_chinese_field():
    arcpy.env.overwriteOutput = True
    arcpy.env.encoding = 'GBK'

    test_dir = r"C:\temp_test_shp"
    test_shp = os.path.join(test_dir, "test_field.shp")

    if not os.path.exists(test_dir):
        os.makedirs(test_dir)

    print("Test SHP Chinese field name with GBK FULL encoding...")

    for ext in ['.shp', '.shx', '.dbf', '.prj', '.sbn', '.sbx', '.cpg']:
        f = test_shp.replace('.shp', ext)
        if os.path.exists(f):
            try:
                os.remove(f)
            except:
                pass

    try:
        arcpy.CreateFeatureclass_management(
            test_dir, "test_field.shp", "POINT",
            spatial_reference=arcpy.SpatialReference(4326)
        )
        print("Created SHP")

        test_cases = [
            (u"\u6cb3\u6d41", 2, "2汉字(GBK=4字节)"),
            (u"\u6cb3\u6d41\u4ee3", 3, "3汉字(GBK=6字节)"),
            (u"\u6cb3\u6d41\u4ee3\u7801", 4, "4汉字(GBK=8字节)"),
            (u"\u6cb3\u6d41\u4ee3\u7801\u7f16", 5, "5汉字(GBK=10字节)"),
            (u"\u6cb3\u6d41\u4ee3\u7801\u7f16\u7801", 6, "6汉字(GBK=12字节)"),
        ]

        for field_name, char_count, desc in test_cases:
            print("")
            print("=== Test: " + desc + " ===")

            try:
                arcpy.AddField_management(test_shp, field_name, "TEXT", field_length=255)
                print("AddField OK")

                fields = arcpy.ListFields(test_shp)
                found = None
                for f in fields:
                    fname = f.name
                    if u"\u6cb3\u6d41" in fname or "river" in fname.lower():
                        found = f
                        break

                if found:
                    print("  Found: [" + found.name + "]")
                    print("  CharCount: " + str(len(found.name)))
                    if found.name == field_name:
                        print("  Status: FULL MATCH!")
                    else:
                        print("  Status: TRUNCATED!")
                else:
                    print("  Status: NOT FOUND!")

            except Exception as e:
                print("  Error: " + str(e))

        print("")
        print("=== Cleanup ===")
        for ext in ['.shp', '.shx', '.dbf', '.prj', '.sbn', '.sbx', '.cpg']:
            f = test_shp.replace('.shp', ext)
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass
        print("Done!")

    except Exception as e:
        print("")
        print("Error: " + str(e))
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_shp_chinese_field()