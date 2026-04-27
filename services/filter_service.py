# -*- coding: utf-8 -*-
"""
数据筛选服务
"""

from typing import List, Dict, Any, Optional


class FilterService:
    """筛选业务服务"""

    @staticmethod
    def filter_records(
        records: List[Dict[str, Any]],
        status: Optional[str] = None,
        code: Optional[str] = None,
        name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        筛选记录

        Args:
            records: 原始记录列表
            status: 状态筛选（"全部"/"通过"/"不通过"）
            code: 河流代码筛选
            name: 河流名称筛选

        Returns:
            筛选后的记录列表
        """
        if not records:
            return []

        filtered = []
        for record in records:
            # 状态筛选
            if status and status != "全部":
                record_status = str(record.get('验证状态', ''))
                if status == "通过" and record_status != '通过':
                    continue
                if status == "不通过" and record_status != '不通过':
                    continue

            # 代码筛选
            if code:
                code_val = record.get('河流代码')
                record_code = str(code_val).upper() if code_val is not None else ''
                if code.upper() not in record_code:
                    continue

            # 名称筛选
            if name:
                name_val = record.get('河流名称')
                record_name = str(name_val).upper() if name_val is not None else ''
                if name.upper() not in record_name:
                    continue

            filtered.append(record)

        return filtered

    @staticmethod
    def get_filter_options(records: List[Dict[str, Any]], field: str) -> List[str]:
        """获取某字段的所有唯一值"""
        options = set()
        for record in records:
            val = record.get(field)
            if val is not None:
                options.add(str(val))
        return sorted(list(options))