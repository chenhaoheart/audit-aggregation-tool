# -*- coding: utf-8 -*-
"""
报表数据检查工具
对附表数据进行字段级别校验
"""

from typing import Dict, List


class DataChecker:
    """报表数据检查器"""

    def __init__(self, report_data: dict):
        self.report_data = report_data
        self.errors = []
        self.fubiao1_records = report_data.get('fubiao1', {}).get('records', [])
        self.fubiao2_records = report_data.get('fubiao2', {}).get('records', [])
        self.fubiao3_records = report_data.get('fubiao3', {}).get('records', [])
        self.fubiao2_headers = report_data.get('fubiao2', {}).get('headers', [])
        self.fubiao3_headers = report_data.get('fubiao3', {}).get('headers', [])

    def find_field_by_keyword(self, keyword: str, headers: List[str] = None) -> str:
        """在字段列表中按关键词查找字段名"""
        if headers is None:
            headers = self.fubiao2_headers
        for h in headers:
            if keyword in h:
                return h
        return ''

    def check_all(self) -> List[Dict]:
        """执行所有检查"""
        self.errors = []
        self.check_region_code()            # R1: 政区代码15位
        self.check_bridge_consistency()     # R2: 桥涵名称编码双向一致性
        self.check_coordinate_format()      # R3: 经纬度格式
        self.check_area_ratio()             # R4: 阻水面积比整数
        self.check_storage_capacity()       # R5: 阻水库容小数位
        self.check_object_reference()       # R6: 对象引用一致性
        self.check_fubiao2_code_consistency()  # R7-R11: 附表2编码、类型、断面形态校验
        self.check_fubiao3()                # R7-R13: 附表3校验
        return self.errors

    def check_fubiao2_code_consistency(self):
        """R7-R11: 附表2编码、类型、断面形态校验
        - 编码(6.编码)必须为28位
        - 编码前6位必须和区县代码(2.县（区、市、旗）代码)前6位一致
        - 编码第7-23位(共17位)必须和河流代码(16.河流代码)一致
        - 编码不能重复
        - 类型(9.类型)必须是英文大写字母A~D
        - 断面形态(12.断面形态)必须是英文大写字母A~E
        """
        # 精确匹配字段名
        code_field = None
        county_code_field = None
        river_code_field = None
        type_field = None
        section_field = None
        for h in self.fubiao2_headers:
            if h == '6.编码':
                code_field = h
            elif h == '2.县（区、市、旗）代码':
                county_code_field = h
            elif h == '16.河流代码':
                river_code_field = h
            elif h == '9.类型':
                type_field = h
            elif h == '12.断面形态':
                section_field = h

        # 收集所有编码用于重复检查
        code_count = {}

        for i, rec in enumerate(self.fubiao2_records):
            code = str(rec.get(code_field, '')).strip() if code_field else ''
            county_code = str(rec.get(county_code_field, '')).strip() if county_code_field else ''
            river_code = str(rec.get(river_code_field, '')).strip() if river_code_field else ''

            if code:
                # 编码必须为28位
                if len(code) != 28:
                    self.add_error('附表2', i+1, code_field, '格式错误',
                                  f'编码应为28位，实际{len(code)}位', code)

                # 编码前6位必须和区县代码前6位一致
                if county_code and len(code) >= 6:
                    if code[:6] != county_code[:6]:
                        self.add_error('附表2', i+1, code_field, '一致性错误',
                                      f'编码前6位[{code[:6]}]与区县代码前6位[{county_code[:6]}]不一致', code)

                # 编码第7-23位必须和河流代码一致
                if river_code and len(code) >= 23:
                    code_river_part = code[6:23]  # 第7-23位（索引6-22）
                    if code_river_part != river_code:
                        self.add_error('附表2', i+1, code_field, '一致性错误',
                                      f'编码第7-23位[{code_river_part}]与河流代码[{river_code}]不一致', code)

                # 收集编码用于重复检查
                if code not in code_count:
                    code_count[code] = []
                code_count[code].append(i+1)

            # 类型必须是英文大写字母A~D
            if type_field:
                type_val = str(rec.get(type_field, '')).strip()
                if type_val and type_val not in ['A', 'B', 'C', 'D']:
                    self.add_error('附表2', i+1, type_field, '格式错误',
                                  f'类型必须为A~D，实际值为[{type_val}]', type_val)

            # 断面形态必须是英文大写字母A~E
            if section_field:
                section_val = str(rec.get(section_field, '')).strip()
                if section_val and section_val not in ['A', 'B', 'C', 'D', 'E']:
                    self.add_error('附表2', i+1, section_field, '格式错误',
                                  f'断面形态必须为A~E，实际值为[{section_val}]', section_val)

        # 编码不能重复
        for code, rows in code_count.items():
            if len(rows) > 1:
                for row in rows:
                    self.add_error('附表2', row, code_field, '一致性错误',
                                  f'编码[{code}]重复出现在行{rows}', code)

    def check_fubiao3(self):
        """附表3校验：编号、经纬度、阻水面积比、类型、断面形态
        - 编号(6.编号)必须为28位
        - 编号前6位必须和区县代码(2.县（区、市、旗）代码)前6位一致
        - 编号第7-23位(共17位)必须和河流代码(15. 河流代码)一致
        - 编号不能重复
        - 经纬度(7.经度, 8.纬度)必须保留6位小数
        - 阻水面积比(13.阻水面积比 R1/%)必须是整数
        - 类型(9.类型)必须是英文大写字母A~D
        - 断面形态(12.断面形态)必须是英文大写字母A~E
        """
        # 精确匹配字段名
        code_field = None
        county_code_field = None
        river_code_field = None
        lon_field = None
        lat_field = None
        area_ratio_field = None
        type_field = None
        section_field = None

        for h in self.fubiao3_headers:
            if h == '6.编号':
                code_field = h
            elif h == '2.县（区、市、旗）代码':
                county_code_field = h
            elif h == '15. 河流代码':
                river_code_field = h
            elif h == '7.经度':
                lon_field = h
            elif h == '8.纬度':
                lat_field = h
            elif '阻水面积比' in h:
                area_ratio_field = h
            elif h == '9.类型':
                type_field = h
            elif h == '12.断面形态':
                section_field = h

        # 收集编号用于重复检查
        code_count = {}

        for i, rec in enumerate(self.fubiao3_records):
            code = str(rec.get(code_field, '')).strip() if code_field else ''
            county_code = str(rec.get(county_code_field, '')).strip() if county_code_field else ''
            river_code = str(rec.get(river_code_field, '')).strip() if river_code_field else ''

            # 编号校验
            if code:
                # 编号必须为28位
                if len(code) != 28:
                    self.add_error('附表3', i+1, code_field, '格式错误',
                                  f'编号应为28位，实际{len(code)}位', code)

                # 编号前6位必须和区县代码前6位一致
                if county_code and len(code) >= 6:
                    if code[:6] != county_code[:6]:
                        self.add_error('附表3', i+1, code_field, '一致性错误',
                                      f'编号前6位[{code[:6]}]与区县代码前6位[{county_code[:6]}]不一致', code)

                # 编号第7-23位必须和河流代码一致
                if river_code and len(code) >= 23:
                    code_river_part = code[6:23]  # 第7-23位（索引6-22）
                    if code_river_part != river_code:
                        self.add_error('附表3', i+1, code_field, '一致性错误',
                                      f'编号第7-23位[{code_river_part}]与河流代码[{river_code}]不一致', code)

                # 收集编号
                if code not in code_count:
                    code_count[code] = []
                code_count[code].append(i+1)

            # R10: 经纬度必须保留6位小数
            for field_name, field in [('经度', lon_field), ('纬度', lat_field)]:
                if not field:
                    continue
                val = str(rec.get(field, '')).strip()
                if val:
                    try:
                        float(val)
                        if '.' in val:
                            decimal_places = len(val.split('.')[1])
                            if decimal_places != 6:
                                self.add_error('附表3', i+1, field, '格式错误',
                                              f'{field_name}应为6位小数，实际{decimal_places}位', val)
                    except ValueError:
                        self.add_error('附表3', i+1, field, '格式错误',
                                      f'{field_name}不是有效数字', val)

            # R11: 阻水面积比必须是整数
            if area_ratio_field:
                val = str(rec.get(area_ratio_field, '')).strip()
                if val:
                    try:
                        fval = float(val)
                        if fval != int(fval):
                            self.add_error('附表3', i+1, area_ratio_field, '格式错误',
                                          '阻水面积比应为整数', val)
                    except ValueError:
                        pass

            # R12: 类型必须是英文大写字母A~D
            if type_field:
                type_val = str(rec.get(type_field, '')).strip()
                if type_val and type_val not in ['A', 'B', 'C', 'D']:
                    self.add_error('附表3', i+1, type_field, '格式错误',
                                  f'类型必须为A~D，实际值为[{type_val}]', type_val)

            # R13: 断面形态必须是英文大写字母A~E
            if section_field:
                section_val = str(rec.get(section_field, '')).strip()
                if section_val and section_val not in ['A', 'B', 'C', 'D', 'E']:
                    self.add_error('附表3', i+1, section_field, '格式错误',
                                  f'断面形态必须为A~E，实际值为[{section_val}]', section_val)

        # R9: 编号不能重复
        for code, rows in code_count.items():
            if len(rows) > 1:
                for row in rows:
                    self.add_error('附表3', row, code_field, '一致性错误',
                                  f'编号[{code}]重复出现在行{rows}', code)

    def add_error(self, table: str, row_num: int, field: str,
                  error_type: str, message: str, value: str):
        """添加错误记录"""
        self.errors.append({
            '序号': row_num,
            '表名': table,
            '字段名': field,
            '错误类型': error_type,
            '错误描述': message,
            '当前值': value
        })

    def check_region_code(self):
        """R1: 政区代码校验
        - 【6.代码】必须为15位
        - 【2.县（区、市、旗）代码】前6位与【6.代码】前6位一致
        - 【4.乡镇代码】前9位与【6.代码】前9位一致
        """
        for i, rec in enumerate(self.fubiao1_records):
            # 获取【6.代码】
            obj_code = str(rec.get('6.代码', '')).strip()

            # 校验【6.代码】是否为15位
            if obj_code and len(obj_code) != 15:
                self.add_error('附表1', i+1, '代码(6.代码)', '格式错误',
                              f'防治对象代码应为15位，实际{len(obj_code)}位', obj_code)

            # 校验【2.县（区、市、旗）代码】前6位与【6.代码】前6位一致
            county_code = str(rec.get('2.县（区、市、旗）代码', '')).strip()
            if obj_code and county_code:
                if county_code[:6] != obj_code[:6]:
                    self.add_error('附表1', i+1, '县代码(2.县代码)', '一致性错误',
                                  f'县代码前6位[{county_code[:6]}]与防治对象代码前6位[{obj_code[:6]}]不一致', county_code)

            # 校验【4.乡镇代码】前9位与【6.代码】前9位一致
            town_code = str(rec.get('4.乡镇代码', '')).strip()
            if obj_code and town_code:
                if town_code[:9] != obj_code[:9]:
                    self.add_error('附表1', i+1, '乡镇代码(4.乡镇代码)', '一致性错误',
                                  f'乡镇代码前9位[{town_code[:9]}]与防治对象代码前9位[{obj_code[:9]}]不一致', town_code)

    def check_bridge_consistency(self):
        """R2: 附表1桥涵名称/编码与附表2双向一致性
        附表1: 11.名称, 12.编码
        附表2: 5.名称, 6.编码
        """
        # 收集附表1列11-12（跨沟道路桥涵）的名称和编码
        fubiao1_bridge = set()
        for rec in self.fubiao1_records:
            name = str(rec.get('11.名称', '')).strip()
            code = str(rec.get('12.编码', '')).strip()
            if name or code:
                fubiao1_bridge.add((name, code))

        # 收集附表2的名称和编码 (5.名称, 6.编码)
        fubiao2_bridge = set()
        for i, rec in enumerate(self.fubiao2_records):
            name = str(rec.get('5.名称', '')).strip()
            code = str(rec.get('6.编码', '')).strip()
            if name or code:
                fubiao2_bridge.add((name, code))

        # 检查附表1有但附表2没有的
        for i, rec in enumerate(self.fubiao1_records):
            name = str(rec.get('11.名称', '')).strip()
            code = str(rec.get('12.编码', '')).strip()
            if (name or code) and (name, code) not in fubiao2_bridge:
                self.add_error('附表1', i+1, '跨沟道路桥涵(11.名称/12.编码)', '一致性错误',
                              f'桥涵[{name}/{code}]在附表2(5.名称/6.编码)中不存在', f'{name}/{code}')

        # 检查附表2有但附表1没有的
        for i, rec in enumerate(self.fubiao2_records):
            name = str(rec.get('5.名称', '')).strip()
            code = str(rec.get('6.编码', '')).strip()
            if (name or code) and (name, code) not in fubiao1_bridge:
                self.add_error('附表2', i+1, '名称/编码(5.名称/6.编码)', '一致性错误',
                              f'在附表1桥涵列(11.名称/12.编码)中不存在', f'{name}/{code}')

    def check_coordinate_format(self):
        """R3: 经纬度必须保留6位小数"""
        lon_field = self.find_field_by_keyword('经度')
        lat_field = self.find_field_by_keyword('纬度')

        for i, rec in enumerate(self.fubiao2_records):
            for field_name, field in [('经度', lon_field), ('纬度', lat_field)]:
                if not field:
                    continue
                val = str(rec.get(field, '')).strip()
                if val:
                    try:
                        float(val)
                        # 检查小数位
                        if '.' in val:
                            decimal_places = len(val.split('.')[1])
                            if decimal_places != 6:
                                self.add_error('附表2', i+1, field, '格式错误',
                                              f'{field_name}应为6位小数，实际{decimal_places}位', val)
                    except ValueError:
                        self.add_error('附表2', i+1, field, '格式错误',
                                      f'{field_name}不是有效数字', val)

    def check_area_ratio(self):
        """R4: 阻水面积比必须是整数"""
        field = self.find_field_by_keyword('阻水面积比')
        if not field:
            return

        for i, rec in enumerate(self.fubiao2_records):
            val = str(rec.get(field, '')).strip()
            if val:
                try:
                    fval = float(val)
                    if fval != int(fval):
                        self.add_error('附表2', i+1, field, '格式错误',
                                      '阻水面积比应为整数', val)
                except ValueError:
                    pass  # 非数字在其他检查中处理

    def check_storage_capacity(self):
        """R5: 阻水库容保留4位小数"""
        field = self.find_field_by_keyword('阻水库容')
        if not field:
            return

        for i, rec in enumerate(self.fubiao2_records):
            val = str(rec.get(field, '')).strip()
            if val:
                try:
                    float(val)
                    if '.' in val:
                        decimal_places = len(val.split('.')[1])
                        if decimal_places != 4:
                            self.add_error('附表2', i+1, field, '格式错误',
                                          f'阻水库容应为4位小数，实际{decimal_places}位', val)
                except ValueError:
                    pass

    def check_object_reference(self):
        """R6: 壅水/溃决/漫流改道影响对象须在附表1中存在
        附表2字段:
        - 17.壅水影响对象名称, 18.壅水影响对象编码
        - 19.溃决影响对象名称, 20.溃决影响对象编码
        - 21.漫流改道影响对象名称, 22.漫流改道影响对象代码
        对应附表1: 5.名称, 6.代码
        分别判断名称和编码是否在附表1中存在
        """
        # 分别收集附表1的名称集合和代码集合
        fubiao1_names = set()
        fubiao1_codes = set()
        for rec in self.fubiao1_records:
            name = str(rec.get('5.名称', '')).strip()
            code = str(rec.get('6.代码', '')).strip()
            if name:
                fubiao1_names.add(name)
            if code:
                fubiao1_codes.add(code)

        # 需要检查的对象字段：附表2中的确切字段名
        object_fields = [
            ('壅水影响对象', '17.壅水影响对象名称', '18.壅水影响对象编码'),
            ('溃决影响对象', '19.溃决影响对象名称', '20.溃决影响对象编码'),
            ('漫流改道影响对象', '21.漫流改道影响对象名称', '22.漫流改道影响对象代码')
        ]

        for obj_type, name_field, code_field in object_fields:
            for i, rec in enumerate(self.fubiao2_records):
                name = str(rec.get(name_field, '')).strip()
                code = str(rec.get(code_field, '')).strip()

                # 分别检查名称和编码
                if name and name not in fubiao1_names:
                    self.add_error('附表2', i+1, f'{name_field}', '一致性错误',
                                  f'{obj_type}名称[{name}]在附表1(5.名称)中不存在', name)

                if code and code not in fubiao1_codes:
                    self.add_error('附表2', i+1, f'{code_field}', '一致性错误',
                                  f'{obj_type}编码[{code}]在附表1(6.代码)中不存在', code)