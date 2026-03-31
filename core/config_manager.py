# -*- coding: utf-8 -*-
"""
字段映射配置管理模块
"""

import os
import json
from typing import List, Dict, Any, Optional


# 默认字段映射规则
DEFAULT_RULES = [
    {
        "output_name": "隐患要素分布L.shp",
        "keywords": ["隐患要素"],
        "field_mapping": {
            "名称": ["名称", "NAME", "Name", "name"],
            "编号": ["PID", "编号", "编码", "pid", "Pid"],
            "类别": ["TYPE", "TYPES", "types", "TYPBS", "类别"],
            "河流名称": ["RVNM", "RVNAME", "rvname", "RAVNME", "RVNAVB", "河流名称", "河流名"],
            "河流代码": ["RVCD", "rvcd", "河流代码", "河流代"]
        }
    },
    {
        "output_name": "断面平面位置L.shp",
        "keywords": ["断面"],
        "field_mapping": {
            "名称": ["断面NM", "断面", "审核汇", "名称", "NAME", "Name", "name", "断面名称", "断面名"],
            "编号": ["PID", "断面编", "编号", "编码", "pid"],
            "类别": ["TYPE", "TYPES", "TYPBS", "类别", "类型", "断面类"],
            "河流名称": ["RVNM", "RVNAME", "RVNAME", "RVNAVB", "河流名称", "河流名"],
            "河流代码": ["RVCD", "rvcd", "RIVL", "河流代码", "河流代"]
        }
    },
    {
        "output_name": "防治对象分布P.shp",
        "keywords": ["防治对象", "保护对象", "防止对象"],
        "field_mapping": {
            "名称": ["NAME", "Name", "name", "名称", "行政区"],
            "代码": ["PID", "代码", "pid", "行政_1"],
            "人口": ["PCOUNT", "POPULATION", "人口"],
            "类别": ["TYPE", "TYPES", "TYPBS", "类别", "类型"],
            "河流名称": ["RVNM", "RVNAME", "RVNAME", "RVNAVB", "河流名称", "河流名", "所在流"],
            "河流代码": ["RVCD", "rvcd", "河流代码", "河流代"]
        }
    }
]

# 关键字段列表（必须存在且有值）
CRITICAL_TARGETS = ["名称"]

# ArcGIS配置文件名
ARCGIS_CONFIG_FILE = "arcgis_config.json"


class ArcGISConfig:
    """ArcGIS环境配置管理"""

    def __init__(self, config_dir: str = None):
        if config_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_dir = os.path.dirname(current_dir)
            config_dir = os.path.join(project_dir, "config")

        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, ARCGIS_CONFIG_FILE)
        self._python_path = None
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """确保配置目录存在"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, exist_ok=True)

    @property
    def python_path(self) -> Optional[str]:
        """获取配置的ArcGIS Python路径"""
        if self._python_path is not None:
            return self._python_path

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._python_path = data.get('python_path')
                    self._verified = data.get('verified', False)
                    return self._python_path
            except Exception:
                pass
        return None

    @property
    def verified(self) -> bool:
        """获取环境是否已验证成功"""
        return getattr(self, '_verified', False)

    def save_python_path(self, path: str, verified: bool = True) -> bool:
        """保存ArcGIS Python路径"""
        try:
            data = {
                'python_path': path,
                'verified': verified
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._python_path = path
            self._verified = verified
            return True
        except Exception as e:
            print(f"保存ArcGIS配置失败: {e}")
            return False

    def clear_python_path(self) -> bool:
        """清除ArcGIS Python路径配置"""
        self._python_path = None
        if os.path.exists(self.config_file):
            try:
                os.remove(self.config_file)
            except Exception:
                pass
        return True


class FieldMappingConfig:
    """字段映射配置管理器"""

    def __init__(self, config_dir: str = None):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目录，默认为当前模块所在目录的config子目录
        """
        if config_dir is None:
            # 获取当前模块所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_dir = os.path.dirname(current_dir)
            config_dir = os.path.join(project_dir, "config")

        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "field_mapping.json")
        self._rules = None
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """确保配置目录存在"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, exist_ok=True)

    @property
    def rules(self) -> List[Dict[str, Any]]:
        """获取字段映射规则，优先从配置文件读取，否则使用默认值"""
        if self._rules is not None:
            return self._rules

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._rules = json.load(f)
                    return self._rules
            except Exception:
                pass

        self._rules = DEFAULT_RULES.copy()
        return self._rules

    def save_rules(self, rules: List[Dict[str, Any]]) -> bool:
        """
        保存字段映射规则到配置文件

        Args:
            rules: 规则列表

        Returns:
            是否保存成功
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(rules, f, ensure_ascii=False, indent=2)
            self._rules = rules
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

    def reset_to_default(self) -> bool:
        """
        重置为默认规则

        Returns:
            是否重置成功
        """
        self._rules = DEFAULT_RULES.copy()
        return self.save_rules(self._rules)

    def export_config(self, file_path: str) -> bool:
        """
        导出配置到指定文件

        Args:
            file_path: 目标文件路径

        Returns:
            是否导出成功
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.rules, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False

    def import_config(self, file_path: str) -> bool:
        """
        从指定文件导入配置

        Args:
            file_path: 源文件路径

        Returns:
            是否导入成功
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                rules = json.load(f)
            # 验证配置格式
            if not isinstance(rules, list):
                return False
            for rule in rules:
                if not all(key in rule for key in ['output_name', 'keywords', 'field_mapping']):
                    return False
            return self.save_rules(rules)
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False

    def get_rule_by_output_name(self, output_name: str) -> Optional[Dict[str, Any]]:
        """
        根据输出文件名获取规则

        Args:
            output_name: 输出文件名

        Returns:
            规则字典或None
        """
        for rule in self.rules:
            if rule['output_name'] == output_name:
                return rule
        return None

    def get_rule_by_keyword(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        根据文件名匹配关键词获取规则

        Args:
            filename: 源文件名

        Returns:
            匹配的规则或None
        """
        for rule in self.rules:
            for keyword in rule['keywords']:
                if keyword in filename:
                    return rule
        return None


# 全局配置实例
_config_instance = None


def get_config() -> FieldMappingConfig:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = FieldMappingConfig()
    return _config_instance