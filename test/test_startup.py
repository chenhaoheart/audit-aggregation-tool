# -*- coding: utf-8 -*-
"""
启动测试脚本 - 检测导入和初始化错误
"""

import sys
import os
import traceback

os.environ['PYTHONIOENCODING'] = 'utf-8'

def test_imports():
    """测试所有模块导入"""
    print("=" * 60)
    print("测试模块导入...")
    print("=" * 60)
    
    errors = []
    
    modules_to_test = [
        ("ui.pages", "from ui.pages import CheckPage, ReportPage, SectionCheckPage, PhotoGalleryPage, ShpFormatterPage"),
        ("ui.pages.check_page", "from ui.pages.check_page import CheckPage"),
        ("ui.pages.report_page", "from ui.pages.report_page import ReportPage"),
        ("ui.pages.section_check_page", "from ui.pages.section_check_page import SectionCheckPage"),
        ("ui.pages.photo_gallery_page", "from ui.pages.photo_gallery_page import PhotoGalleryPage"),
        ("ui.pages.shp_formatter_page", "from ui.pages.shp_formatter_page import ShpFormatterPage"),
        ("ui.dialogs", "from ui.dialogs import LogDialog, ThemeDialog, ArcGISConfigDialog, FieldMappingDialog, TiandituConfigDialog"),
        ("ui.dialogs.log_dialog", "from ui.dialogs.log_dialog import LogDialog"),
        ("ui.dialogs.theme_dialog", "from ui.dialogs.theme_dialog import ThemeDialog"),
        ("ui.dialogs.arcgis_config_dialog", "from ui.dialogs.arcgis_config_dialog import ArcGISConfigDialog"),
        ("ui.dialogs.field_mapping_dialog", "from ui.dialogs.field_mapping_dialog import FieldMappingDialog"),
        ("ui.dialogs.tianditu_config_dialog", "from ui.dialogs.tianditu_config_dialog import TiandituConfigDialog"),
        ("ui.main_window", "from ui.main_window import MainWindow"),
        ("core.theme_manager", "from core.theme_manager import get_theme_manager"),
    ]
    
    for name, import_stmt in modules_to_test:
        try:
            exec(import_stmt)
            print(f"✓ {name}")
        except Exception as e:
            print(f"✗ {name}: {e}")
            errors.append((name, str(e), traceback.format_exc()))
    
    return errors

def test_widget_creation():
    """测试Widget创建"""
    print("\n" + "=" * 60)
    print("测试Widget创建...")
    print("=" * 60)
    
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    errors = []
    
    from ui.pages.check_page import CheckPage
    from ui.pages.report_page import ReportPage
    from ui.pages.section_check_page import SectionCheckPage
    from ui.pages.photo_gallery_page import PhotoGalleryPage
    from ui.pages.shp_formatter_page import ShpFormatterPage
    from ui.main_window import MainWindow
    
    widgets_to_test = [
        ("CheckPage", CheckPage),
        ("ReportPage", ReportPage),
        ("SectionCheckPage", SectionCheckPage),
        ("PhotoGalleryPage", PhotoGalleryPage),
        ("ShpFormatterPage", ShpFormatterPage),
        ("MainWindow", MainWindow),
    ]
    
    for name, widget_class in widgets_to_test:
        try:
            widget = widget_class()
            print(f"✓ {name}")
            widget.deleteLater()
        except Exception as e:
            print(f"✗ {name}: {e}")
            errors.append((name, str(e), traceback.format_exc()))
    
    return errors

def main():
    all_errors = []
    
    import_errors = test_imports()
    all_errors.extend(import_errors)
    
    if not import_errors:
        creation_errors = test_widget_creation()
        all_errors.extend(creation_errors)
    
    print("\n" + "=" * 60)
    if all_errors:
        print(f"发现 {len(all_errors)} 个错误:")
        print("=" * 60)
        for name, error, tb in all_errors:
            print(f"\n[{name}]")
            print(tb)
    else:
        print("所有测试通过！")
        print("=" * 60)
    
    return len(all_errors)

if __name__ == "__main__":
    error_count = main()
    sys.exit(error_count)