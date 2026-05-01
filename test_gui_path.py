# -*- coding: utf-8 -*-
"""
模拟 GUI 实际路径的测试脚本
"""
import os
import sys
sys.path.insert(0, r'D:\github\空间数据检查桌面版-主题-design-2026')

from core.data_validator import DataValidator
from core.report_reader import load_all_reports
from core.config_manager import get_validation_mapping_config
import copy


def test_with_gui_path():
    """使用 GUI 实际传给 load_shp_data 的路径测试"""

    # GUI 传递给 load_shp_data 的实际路径（空间数据文件夹本身，没有子文件夹）
    shp_folder = r'D:\github\空间数据检查桌面版-主题-design-2026\青海24示范小流域-药草沟-20260313\630121_大通\电子数据\空间数据'

    report_folder = r'D:\github\空间数据检查桌面版-主题-design-2026\青海24示范小流域-药草沟-20260313\630121_大通\成果报表'

    print("=" * 70)
    print("🧪 模拟 GUI 实际路径测试")
    print("=" * 70)
    print(f"\n📂 shp_folder (GUI实际传入): {shp_folder}")
    print(f"   该目录下项目: {os.listdir(shp_folder)[:8]}...")
    print(f"   是否有子目录: {any(os.path.isdir(os.path.join(shp_folder, x)) for x in os.listdir(shp_folder))}")

    # 模拟 GUI 流程
    report_data = load_all_reports(report_folder)
    validator = DataValidator()

    def log_callback(msg):
        print(f"   {msg}")

    validator.progress_callback = log_callback

    # 加载附表
    validator.load_fubiao(report_data)

    # 加载 shp - 使用 GUI 实际路径
    validator.load_shp_data(shp_folder)

    # 加载配置 - 模拟 GUI 做法
    cfg = get_validation_mapping_config()
    field_mapping = copy.deepcopy(cfg.mapping)
    validator.set_field_mapping(field_mapping)

    print(f"\n📊 shp加载结果:")
    print(f"   fangzhi 记录数: {len(validator.shp_data['fangzhi'])}")
    print(f"   yinhuan 记录数: {len(validator.shp_data['yinhuan'])}")

    # 执行校验
    results = validator.validate_all()

    print(f"\n📈 校验结果:")
    r1 = results['fubiao1_vs_fangzhi']
    print(f"   附表1: 匹配{r1['match_count']}, 仅附表{r1['fubiao_only_count']}, 仅SHP{r1['shp_only_count']}")

    r23 = results['fubiao23_vs_yinhuan']
    print(f"   附表2: 匹配{r23['fubiao2_match_count']}, 仅附表{r23['fubiao2_only_count']}")
    print(f"   附表3: 匹配{r23['fubiao3_match_count']}, 仅附表{r23['fubiao3_only_count']}")

    all_ok = (r1['match_count'] > 0 and r23['fubiao2_match_count'] > 0 and r23['fubiao3_match_count'] > 0)
    print(f"\n{'✅ 测试通过！' if all_ok else '❌ 测试失败！'}")


if __name__ == '__main__':
    test_with_gui_path()
