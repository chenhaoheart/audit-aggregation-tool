# 空间数据检查工具 - 附表校验功能实现计划

## 需求概述

在现有空间数据检查工具基础上，新增**可选**的附表Excel与空间数据的交叉校验功能：

| 空间数据图层 | 对应附表Excel |
|------------|-------------|
| 防治对象分布P.shp | 附表1_山洪灾害防治对象名录.xlsx |
| 隐患要素分布L.shp | 附表2_跨沟道路、桥涵、塘（堰）坝调查成果表.xlsx |
| 隐患要素分布L.shp | 附表3_沟滩占地情况调查成果表.xlsx |

## 核心设计原则

**功能解耦**：附表校验与原有水系/空间数据检查**完全独立**
- 用户可以只检查水系和空间数据（不加载附表）
- 用户可以同时检查水系、空间数据和附表
- 附表文件选择为可选项，不影响原有功能

## 校验逻辑

**空间数据 ⊆ 附表（附表为基准）**
- 附表中的记录作为标准答案
- 空间数据中的每一条记录都必须在附表中存在匹配项
- 不存在的记录标记为"不通过"并记录错误信息

## 实施计划

### 步骤1：扩展核心检查模块 (core/checker.py)

#### 1.1 修改WaterSystemChecker构造函数
- 新增 `attachment_files` 参数（字典，包含3个附表文件路径，可为空）
- 新增 `enable_attachment_check` 参数（布尔值，是否执行附表校验）

#### 1.2 添加附表Excel读取方法
- `load_excel_with_merged_cells(file_path)`：使用openpyxl读取Excel，处理合并单元格
- `load_attachment_tables()`：仅当附表文件存在时才加载

#### 1.3 添加附表校验方法
- `validate_fangzhi_vs_attachment1()`：防治对象分布P vs 附表1
- `validate_yinhuan_vs_attachment2()`：隐患要素分布L vs 附表2
- `validate_yinhuan_vs_attachment3()`：隐患要素分布L vs 附表3

#### 1.4 添加附表校验执行方法
- `perform_attachment_validations()`：仅当 `enable_attachment_check=True` 且存在附表文件时执行

#### 1.5 修改主流程
- 在 `process_all()` 方法中，水系和图层检查**始终执行**
- 附表校验在图层检查**之后**执行（如果启用）

### 步骤2：扩展UI界面 (ui/main_window.py)

#### 2.1 修改CheckThread
- 构造函数新增 `attachment_files` 和 `enable_attachment_check` 参数
- 线程执行完毕后传递 `attachment_check_results`（可为空列表）

#### 2.2 添加附表文件选择区域
- 在"检查配置"区域下方添加"附表配置"折叠区域（默认折叠）
- 3个附表文件选择行，每行：QLineEdit + 浏览按钮
- 附表1：附表1_山洪灾害防治对象名录
- 附表2：附表2_跨沟道路、桥涵、塘（堰）坝调查成果表
- 附表3：附表3_沟滩占地情况调查成果表

#### 2.3 新增"附表校验"Tab页
- 仅当有附表校验结果时显示（或Tab保持存在但提示"无数据"）
- 显示附表1校验结果：防治对象分布P vs 附表1
- 显示附表2/3校验结果：隐患要素分布L vs 附表2/3
- 支持按状态、河流代码、河流名称筛选

#### 2.4 添加附表校验结果导出
- 导出Excel时，如果存在附表校验结果，新增"附表校验"Sheet

### 步骤3：更新主窗口数据管理
- `original_attachment_check_data` 存储原始校验数据
- `attachment_files` 字典存储3个附表文件路径
- `enable_attachment_check` 根据是否有附表文件自动设置

## 数据流

### 场景1：只检查水系和空间数据
```
用户选择文件夹 + 水系文件（不选附表）
        ↓
CheckThread(folder_path, water_shp, {}, False)
        ↓
WaterSystemChecker(..., attachment_files={}, enable_attachment_check=False)
        ↓
load_water_system() → process_all() → 返回结果（无附表校验）
        ↓
UI显示检查结果（无附表校验Tab或Tab为空）
```

### 场景2：同时检查空间数据和附表
```
用户选择文件夹 + 水系文件 + 附表文件
        ↓
CheckThread(folder_path, water_shp, attachment_files, True)
        ↓
WaterSystemChecker(..., attachment_files, True)
        ↓
load_water_system() → process_all() → load_attachment_tables() → perform_attachment_validations()
        ↓
返回结果（含附表校验结果）
        ↓
UI显示检查结果（含附表校验Tab）
```

## 附表文件路径（用户提供）

```
附表1: C:\Users\chenh\Desktop\青海24示范小流域-药草沟-20260313\630121_大通\成果报表\附表1_山洪灾害防治对象名录.xlsx
附表2: C:\Users\chenh\Desktop\青海24示范小流域-药草沟-20260313\630121_大通\成果报表\附表2_跨沟道路、桥涵、塘（堰）坝调查成果表.xlsx
附表3: C:\Users\chenh\Desktop\青海24示范小流域-药草沟-20260313\630121_大通\成果报表\附表3_沟滩占地情况调查成果表.xlsx
```

## 附表字段映射（待确认）

由于附表Excel文件尚未读取，字段映射关系需要根据实际文件确定：
- 附表1中用于匹配的字段：河流代码、河流名称（或对象名称）
- 附表2中用于匹配的字段：河流代码、河流名称、编号
- 附表3中用于匹配的字段：河流代码、河流名称、编号

程序中将使用模糊匹配查找这些字段。

## 实现顺序

1. [ ] 完成计划并等待用户确认
2. [ ] 步骤1：修改core/checker.py - 添加可选附表校验
3. [ ] 步骤2.1：修改CheckThread - 支持可选附表参数
4. [ ] 步骤2.2：添加附表文件选择UI（可折叠区域）
5. [ ] 步骤2.3：添加附表校验Tab页
6. [ ] 步骤2.4：添加导出功能（条件导出附表结果）
7. [ ] 步骤3：更新数据管理
8. [ ] 测试验证

## 预计工作量

- 核心逻辑修改：1-2小时
- UI修改：1-2小时
- 测试验证：1小时