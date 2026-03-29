# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import os
import arcpy

def test_chinese_fieldname():
    arcpy.env.overwriteOutput = True

    test_gdb = r"E:\青海\test_chinese_field.gdb"
    fc_name = "test_fc"
    fc_path = os.path.join(test_gdb, fc_name)

    print("Test start...")
    print("Python version: " + sys.version)

    try:
        if arcpy.Exists(test_gdb):
            arcpy.Delete_management(test_gdb)
            print("Deleted old GDB")

        arcpy.CreateFileGDB_management(os.path.dirname(test_gdb), os.path.basename(test_gdb))
        print("Created GDB: " + test_gdb)

        arcpy.CreateFeatureclass_management(
            test_gdb, fc_name, "POINT",
            spatial_reference=arcpy.SpatialReference(4326)
        )
        print("Created feature class: " + fc_path)

        test_fieldname = u"河流代码"
        print("")
        print("Field name to add: [" + test_fieldname + "]")
        print("Field name char count: " + str(len(test_fieldname)))

        arcpy.AddField_management(fc_path, test_fieldname, "TEXT", field_length=255)
        print("AddField_management success")

        fields = arcpy.ListFields(fc_path)
        print("")
        print("=== Field List ===")
        for f in fields:
            fname = f.name
            print("Field: [" + fname + "] Len: " + str(len(fname)))

        target_field = None
        for f in fields:
            if u"河流" in f.name:
                target_field = f
                break

        if target_field:
            print("")
            print("Found target field!")
            print("  Field name: [" + target_field.name + "]")
            print("  Char count: " + str(len(target_field.name)))
            if target_field.name == test_fieldname:
                print("  Status: FULL MATCH!")
            else:
                print("  Status: TRUNCATED!")
                print("  Expected: [" + test_fieldname + "]")
                print("  Actual: [" + target_field.name + "]")
        else:
            print("")
            print("Target field not found!")

        print("")
        print("=== Test Insert Data ===")
        try:
            with arcpy.da.InsertCursor(fc_path, ["SHAPE@", test_fieldname]) as cursor:
                cursor.insertRow([arcpy.Point(100, 30), u"TestData"])
            print("Insert data success!")
        except Exception as e:
            print("Insert data failed: " + str(e))

        print("")
        print("=== Read Data ===")
        with arcpy.da.SearchCursor(fc_path, [test_fieldname]) as cursor:
            for row in cursor:
                print("Read: [" + str(row[0]) + "]")

        print("")
        print("=== Cleanup ===")
        arcpy.Delete_management(test_gdb)
        print("Deleted test GDB")
        print("Test complete!")

    except Exception as e:
        print("")
        print("Error: " + str(e))
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_chinese_fieldname()