# -*- coding: utf-8 -*-
import sys
import os
import arcpy

reload(sys)
sys.setdefaultencoding('utf-8')

os.environ['ESRI_ENCODING'] = 'GBK'
os.environ['SHAPE_ENCODING'] = 'GBK'

def test_final_fields():
    arcpy.env.overwriteOutput = True

    test_dir = r"C:\temp_test_shp"
    test_shp = os.path.join(test_dir, "test_fields.shp")

    if not os.path.exists(test_dir):
        os.makedirs(test_dir)

    for ext in ['.shp', '.shx', '.dbf', '.prj', '.sbn', '.sbx', '.cpg']:
        f = test_shp.replace('.shp', ext)
        if os.path.exists(f):
            try:
                os.remove(f)
            except:
                pass

    print("Test: 河流名称 and 河流代码")
    print("=" * 50)

    try:
        arcpy.CreateFeatureclass_management(
            test_dir, "test_fields.shp", "POINT",
            spatial_reference=arcpy.SpatialReference(4326)
        )
        print("Created SHP")

        test_fields = [
            u"\u6cb3\u6d41\u540d\u79f0",
            u"\u6cb3\u6d41\u4ee3\u7801",
        ]

        for field_name in test_fields:
            print("")
            print("Adding: [" + field_name + "]")
            print("  CharCount: " + str(len(field_name)))

            try:
                arcpy.AddField_management(test_shp, field_name, "TEXT", field_length=255)
                print("  AddField: OK")
            except Exception as e:
                print("  AddField Error: " + str(e))

        print("")
        print("=" * 50)
        print("Field List:")

        fields = arcpy.ListFields(test_shp)
        for f in fields:
            if f.name not in ['OBJECTID', 'Shape', 'FID', 'Id']:
                print("  [" + f.name + "] Len: " + str(len(f.name)))

        print("")
        print("Test insert data:")

        try:
            with arcpy.da.InsertCursor(test_shp, ["SHAPE@", u"\u6cb3\u6d41\u540d\u79f0", u"\u6cb3\u6d41\u4ee3\u7801"]) as cursor:
                cursor.insertRow([arcpy.Point(100, 30), u"\u6cb3\u6d41\u540d\u79f0\u6570\u636e", u"\u6cb3\u6d41\u4ee3\u7801\u6570\u636e"])
            print("  Insert: OK")
        except Exception as e:
            print("  Insert Error: " + str(e))

        print("")
        print("Read data:")
        try:
            with arcpy.da.SearchCursor(test_shp, [u"\u6cb3\u6d41\u540d\u79f0", u"\u6cb3\u6d41\u4ee3\u7801"]) as cursor:
                for row in cursor:
                    print("  RiverName: [" + str(row[0]) + "]")
                    print("  RiverCode: [" + str(row[1]) + "]")
        except Exception as e:
            print("  Read Error: " + str(e))

        print("")
        print("Cleanup...")
        for ext in ['.shp', '.shx', '.dbf', '.prj', '.sbn', '.sbx', '.cpg']:
            f = test_shp.replace('.shp', ext)
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass
        print("Done!")

    except Exception as e:
        print("Error: " + str(e))
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_final_fields()