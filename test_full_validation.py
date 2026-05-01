# -*- coding: utf-8 -*-
"""
完整测试脚本：验证附表与shp的匹配逻辑
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, r'D:\github\空间数据检查桌面版-主题-design-2026')

from core.data_validator import DataValidator
from core.report_reader import load_all_reports

def test_full_validation():
    """完整测试附表+shp匹配"""

    base_folder = r'D:\github\空间数据检查桌面版-主题-design-2026\青海24示范小流域-药草沟-20260313'
    report_folder = os.path.join(base_folder, '630121_大通', '成果报表')

    print("=" * 70)
    print("🧪 完整测试：附表 + SHP 匹配校验")
    print("=" * 70)

    # 1. 加载附表
    print("\n" + "=" * 70)
    print("📋 第1步：加载附表数据")
    print("=" * 70)

    try:
        report_data = load_all_reports(report_folder)
        print(f"✅ 附表1记录数: {len(report_data.get('fubiao1', {}).get('records', []))}")
        print(f"✅ 附表2记录数: {len(report_data.get('fubiao2', {}).get('records', []))}")
        print(f"✅ 附表3记录数: {len(report_data.get('fubiao3', {}).get('records', []))}")

        if report_data.get('fubiao1', {}).get('records'):
            sample = report_data['fubiao1']['records'][0]
            print(f"\n📝 附表1示例记录字段:")
            for k, v in list(sample.items())[:8]:
                if not k.startswith('_'):
                    print(f"   {k}: {v}")

    except Exception as e:
        print(f"❌ 附表加载失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 2. 创建validator并加载数据
    print("\n" + "=" * 70)
    print("📊 第2步：创建 Validator 并加载数据")
    print("=" * 70)

    validator = DataValidator()

    def log_callback(msg):
        print(f"   {msg}")

    validator.progress_callback = log_callback

    validator.load_fubiao(report_data)
    validator.load_shp_data(base_folder)

    # 3. 显示当前的字段映射配置
    print("\n" + "=" * 70)
    print("⚙️  第3步：查看字段映射配置")
    print("=" * 70)

    mapping = validator.field_mapping
    print("\n📌 当前使用的字段映射:")

    for key in ['fubiao1_vs_fangzhi', 'fubiao2_vs_yinhuan', 'fubiao3_vs_yinhuan']:
        if key in mapping:
            config = mapping[key]
            match_fields = config.get('match_fields', {})
            print(f"\n   [{key}]")
            print(f"      match_fields: {match_fields}")
        else:
            print(f"\n   ⚠️  [{key}] 未找到配置！")

    # 4. 执行校验
    print("\n" + "=" * 70)
    print("🔍 第4步：执行匹配校验")
    print("=" * 70)

    try:
        results = validator.validate_all()

        print("\n" + "=" * 70)
        print("📈 校验结果汇总:")
        print("=" * 70)

        # 附表1 vs 防治对象
        r1 = results['fubiao1_vs_fangzhi']
        print(f"\n📊 附表1 ↔ 防治对象分布P.shp:")
        print(f"   ✅ 匹配成功: {r1['match_count']} 条")
        print(f"   ❌ 仅附表有: {r1['fubiao_only_count']} 条")
        print(f"   ⚠️  仅SHP有: {r1['shp_only_count']} 条")

        # 附表2/3 vs 隐患要素
        r23 = results['fubiao23_vs_yinhuan']
        print(f"\n📊 附表2 ↔ 隐患要素分布L.shp:")
        print(f"   ✅ 匹配成功: {r23['fubiao2_match_count']} 条")
        print(f"   ❌ 仅附表有: {r23['fubiao2_only_count']} 条")

        print(f"\n📊 附表3 ↔ 隐患要素分布L.shp:")
        print(f"   ✅ 匹配成功: {r23['fubiao3_match_count']} 条")
        print(f"   ❌ 仅附表有: {r23['fubiao3_only_count']} 条")
        print(f"   ⚠️  仅SHP有: {r23['shp_only_count']} 条")

        # 5. 如果匹配为0，分析原因
        if r1['match_count'] == 0 and r1['fubiao_only_count'] > 0:
            print("\n" + "=" * 70)
            print("🔬 深度分析：为什么匹配失败？")
            print("=" * 70)

            print("\n❌ 附表1中的未匹配记录:")
            for i, rec in enumerate(r1['fubiao_only'][:3]):
                print(f"\n   记录{i+1}:")
                mapping1 = validator.field_mapping.get('fubiao1_vs_fangzhi', {})
                match_fields1 = mapping1.get('match_fields', {})

                for fb_field in match_fields1.values():
                    val = rec.get(fb_field, 'N/A')
                    print(f"      {fb_field} = '{val}'")

            print("\n✅ SHP中的记录（用于对比）:")
            for i, rec in enumerate(validator.shp_data['fangzhi'][:3]):
                print(f"\n   记录{i+1}:")
                mapping1 = validator.field_mapping.get('fubiao1_vs_fangzhi', {})
                match_fields1 = mapping1.get('match_fields', {})

                for shp_field in match_fields1.keys():
                    val = rec.get(shp_field, 'N/A')
                    print(f"      {shp_field} = '{val}'")

    except Exception as e:
        print(f"\n❌ 校验执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_full_validation()
