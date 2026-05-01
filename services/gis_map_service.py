# -*- coding: utf-8 -*-
"""
GIS地图业务服务层

职责：
- 图层数据管理（增删改查）
- SHP/GeoJSON 数据转换与处理
- 要素属性操作（更新、删除）
- 批量数据加载
- 绘制要素管理
"""

import json
import os
from typing import Dict, List, Optional, Any
from PySide6.QtCore import QObject, Signal
from core.config_manager import get_shp_match_config


class GisMapService(QObject):
    """GIS地图业务服务"""

    layer_loaded = Signal(str, int)
    feature_created = Signal(dict)
    feature_edited = Signal(list)
    feature_deleted = Signal(list)

    LAYER_COLORS = {
        'water': '#3b82f6',
        'xiaoliuyu': '#06b6d4',
        'duanmian': '#22c55e',
        'fangzhi': '#f59e0b',
        'yinhuan': '#ef4444',
        'custom': '#8b5cf6',
    }

    LAYER_NAMES = {
        'water': '水系',
        'xiaoliuyu': '小流域',
        'duanmian': '',
        'fangzhi': '',
        'yinhuan': '',
        'custom': '自定义图层',
    }

    @classmethod
    def _init_layer_names(cls):
        shp_cfg = get_shp_match_config()
        cls.LAYER_NAMES['duanmian'] = shp_cfg.get_layer_keyword('duanmian')
        cls.LAYER_NAMES['fangzhi'] = shp_cfg.get_layer_keyword('fangzhi')
        cls.LAYER_NAMES['yinhuan'] = shp_cfg.get_layer_keyword('yinhuan')

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_layer_names()
        self._loaded_layers: Dict[str, Dict] = {}

    @property
    def loaded_layers(self) -> Dict[str, Dict]:
        return self._loaded_layers

    def get_layer(self, layer_id: str) -> Optional[Dict]:
        """获取图层数据"""
        return self._loaded_layers.get(layer_id)

    def load_geojson(self, layer_id: str, geojson_data: dict, color: str = None, file_path: str = None) -> dict:
        """
        加载GeoJSON数据到图层

        返回完整的图层元数据
        """
        color = color or self.LAYER_COLORS.get(layer_id, '#6366f1')
        name = self.LAYER_NAMES.get(layer_id, layer_id)

        layer_meta = {
            'geojson': geojson_data,
            'color': color,
            'name': name,
            'file_path': file_path,
        }

        self._loaded_layers[layer_id] = layer_meta

        feature_count = len(geojson_data.get('features', []))
        self.layer_loaded.emit(layer_id, feature_count)

        return layer_meta

    def load_shp_file(self, shp_path: str, layer_id: str = None, color: str = None) -> Optional[str]:
        """
        加载SHP文件并转换为GeoJSON

        返回 layer_id，失败返回 None
        """
        try:
            import geopandas as gpd

            gdf = gpd.read_file(shp_path)
            gdf.columns = [str(col) for col in gdf.columns]

            if layer_id is None:
                layer_id = os.path.splitext(os.path.basename(shp_path))[0]

            for col in gdf.columns:
                if col != gdf.geometry.name:
                    gdf[col] = gdf[col].apply(lambda x: str(x) if x is not None else '')

            geojson_data = json.loads(gdf.to_json())
            self.load_geojson(layer_id, geojson_data, color, file_path=shp_path)
            return layer_id

        except Exception as e:
            raise Exception(f"无法加载SHP文件 {shp_path}:\n{str(e)}")

    def load_shp_with_status(self, shp_path: str, layer_id: str, check_records: list, color: str = None) -> Optional[str]:
        """
        加载SHP文件并标注检查状态

        参数：
            check_records: 检查记录列表，每条记录应包含 '记录序号' 和 '验证状态'
        """
        try:
            import geopandas as gpd

            gdf = gpd.read_file(shp_path)
            gdf.columns = [str(col) for col in gdf.columns]

            status_map = {}
            for record in check_records:
                idx = record.get('记录序号')
                if idx is not None:
                    status_map[int(idx)] = record.get('验证状态', '')

            for col in gdf.columns:
                if col != gdf.geometry.name:
                    gdf[col] = gdf[col].apply(lambda x: str(x) if x is not None else '')

            geojson_data = json.loads(gdf.to_json())
            for feature in geojson_data.get('features', []):
                fid = feature.get('id')
                if fid is not None and fid in status_map:
                    feature['properties']['_status'] = status_map[fid]

            self.load_geojson(layer_id, geojson_data, color)
            return layer_id

        except Exception as e:
            raise Exception(f"无法加载SHP文件 {shp_path}:\n{str(e)}")

    def remove_layer(self, layer_id: str) -> bool:
        """移除指定图层"""
        if layer_id in self._loaded_layers:
            del self._loaded_layers[layer_id]
            return True
        return False

    def clear_all(self):
        """清除所有图层"""
        self._loaded_layers.clear()

    def update_feature_properties(self, layer_id: str, properties: dict) -> bool:
        """
        更新指定要素的属性

        参数：
            layer_id: 图层ID
            properties: 新的属性字典，必须包含 'id' 字段用于匹配要素
        """
        if layer_id not in self._loaded_layers:
            return False

        layer_data = self._loaded_layers[layer_id]
        geojson_data = layer_data['geojson']

        for feature in geojson_data.get('features', []):
            if feature.get('properties'):
                feature_id = feature.get('id')
                if feature_id is not None and str(feature_id) == str(properties.get('id', '')):
                    feature['properties'].update(properties)
                    return True

        return False

    def delete_feature_from_layer(self, layer_id: str, feature_id: Any) -> bool:
        """
        从图层数据中删除指定要素

        注意：这只会更新内存中的数据，不会自动刷新地图显示
        """
        if layer_id not in self._loaded_layers:
            return False

        layer_data = self._loaded_layers[layer_id]
        geojson_data = layer_data['geojson']
        features = geojson_data.get('features', [])

        for i, feature in enumerate(features):
            if feature.get('id') == feature_id:
                features.pop(i)
                return True

        return False

    def add_drawn_feature(self, geojson: dict):
        """添加绘制的要素到'drawn'图层"""
        if 'drawn' not in self._loaded_layers:
            self._loaded_layers['drawn'] = {
                'geojson': {'type': 'FeatureCollection', 'features': []},
                'color': '#8b5cf6',
                'name': '绘制要素'
            }

        self._loaded_layers['drawn']['geojson']['features'].append(geojson)
        self.feature_created.emit(geojson)

    def get_drawn_features(self) -> List[dict]:
        """获取所有绘制的要素"""
        drawn_layer = self._loaded_layers.get('drawn')
        if drawn_layer:
            return drawn_layer['geojson'].get('features', [])
        return []

    def remove_drawn_feature(self, feature_id: str) -> bool:
        """删除指定的绘制要素"""
        drawn_layer = self._loaded_layers.get('drawn')
        if not drawn_layer:
            return False
        
        features = drawn_layer['geojson'].get('features', [])
        for i, f in enumerate(features):
            if f.get('id') == feature_id:
                features.pop(i)
                return True
        return False

    def add_feature_to_layer(self, layer_id: str, feature: dict) -> bool:
        """将要素添加到指定图层"""
        if layer_id not in self._loaded_layers:
            return False
        
        layer_data = self._loaded_layers[layer_id]
        geojson = layer_data.get('geojson', {})
        features = geojson.get('features', [])
        features.append(feature)
        return True

    def get_layer_file_path(self, layer_id: str) -> Optional[str]:
        """获取图层对应的原始文件路径"""
        layer_data = self._loaded_layers.get(layer_id)
        if layer_data:
            return layer_data.get('file_path')
        return None

    def save_layer_to_shp(self, layer_id: str, file_path: str = None) -> bool:
        """保存图层到SHP文件"""
        layer_data = self._loaded_layers.get(layer_id)
        if not layer_data:
            return False
        
        geojson = layer_data.get('geojson')
        if not geojson:
            return False
        
        file_path = file_path or layer_data.get('file_path')
        if not file_path:
            return False
        
        try:
            import geopandas as gpd
            from shapely.geometry import shape
            
            features = geojson.get('features', [])
            if not features:
                return False
            
            geometries = []
            properties_list = []
            for f in features:
                geom = shape(f['geometry'])
                geometries.append(geom)
                props = dict(f.get('properties', {}))
                properties_list.append(props)
            
            gdf = gpd.GeoDataFrame(properties_list, geometry=geometries, crs='EPSG:4326')
            gdf.to_file(file_path, driver='ESRI Shapefile')
            return True
            
        except Exception as e:
            raise Exception(f"保存图层失败:\n{str(e)}")

    def save_drawn_features_to_shp(self, file_path: str) -> dict:
        """
        保存绘制的要素到SHP文件
        
        由于 Shapefile 只能存储单一几何类型，会按类型分别保存：
        - 点要素: {base_name}_point.shp
        - 线要素: {base_name}_line.shp
        - 面要素: {base_name}_polygon.shp
        
        返回保存结果字典: {'Point': count, 'LineString': count, 'Polygon': count, 'files': [file_paths]}
        """
        try:
            import geopandas as gpd
            from shapely.geometry import shape

            features = self.get_drawn_features()
            if not features:
                return {}

            type_features = {}
            for f in features:
                geom_type = f.get('geometry', {}).get('type', '')
                if geom_type.startswith('Multi'):
                    geom_type = geom_type.replace('Multi', '')
                if geom_type not in type_features:
                    type_features[geom_type] = []
                type_features[geom_type].append(f)

            base_path = file_path.rsplit('.', 1)[0] if file_path.endswith('.shp') else file_path
            saved_files = []
            result = {'files': saved_files}

            type_suffix = {
                'Point': '_point',
                'LineString': '_line',
                'Polygon': '_polygon',
            }

            for geom_type, feat_list in type_features.items():
                suffix = type_suffix.get(geom_type, '')
                type_file_path = f"{base_path}{suffix}.shp"
                
                geometries = []
                properties_list = []
                for f in feat_list:
                    geom = shape(f['geometry'])
                    geometries.append(geom)
                    props = dict(f.get('properties', {}))
                    properties_list.append(props)

                gdf = gpd.GeoDataFrame(properties_list, geometry=geometries, crs='EPSG:4326')
                gdf.to_file(type_file_path, driver='ESRI Shapefile')
                
                saved_files.append(type_file_path)
                result[geom_type] = len(feat_list)

            return result

        except Exception as e:
            raise Exception(f"保存绘制要素失败:\n{str(e)}")

    def batch_load_shp_from_folder(self, folder_path: str, water_shp_path: str = None) -> int:
        """
        从文件夹批量加载SHP文件

        自动识别断面、防治、隐患等类型的SHP文件

        返回成功加载的图层数量
        """
        loaded_count = 0

        if water_shp_path and os.path.exists(water_shp_path):
            try:
                self.load_shp_file(
                    water_shp_path, layer_id='water',
                    color=self.LAYER_COLORS['water']
                )
                loaded_count += 1
            except Exception:
                pass

        if folder_path and os.path.isdir(folder_path):
            shp_names = {
                'xiaoliuyu': ['小流域', 'xiaoliuyu', 'XLLY'],
                'duanmian': ['断面', 'duanmian', 'DM'],
                'fangzhi': ['防治', 'fangzhi', 'FZ'],
                'yinhuan': ['隐患', 'yinhuan', 'YH'],
            }
            for root, dirs, files in os.walk(folder_path):
                for f in files:
                    if not f.endswith('.shp'):
                        continue
                    fpath = os.path.join(root, f)
                    fname_lower = f.lower()
                    for lid, keywords in shp_names.items():
                        if any(kw in fname_lower for kw in keywords):
                            try:
                                self.load_shp_file(
                                    fpath, layer_id=lid,
                                    color=self.LAYER_COLORS.get(lid, '#6366f1')
                                )
                                loaded_count += 1
                            except Exception:
                                pass
                            break

        return loaded_count

    def batch_load_check_results(self, results: list) -> int:
        """
        从检查结果批量加载带状态的SHP文件

        参数：
            results: 检查结果列表，每项包含 file_path 和 file_name

        返回成功加载的图层数量
        """
        loaded = 0
        for result in results:
            shp_path = result.get('file_path', '')
            file_name = result.get('file_name', '')
            if not shp_path or not os.path.exists(shp_path):
                continue

            if '小流域' in file_name:
                lid = 'xiaoliuyu'
            elif self.LAYER_NAMES.get('duanmian', '') and self.LAYER_NAMES['duanmian'] in file_name:
                lid = 'duanmian'
            elif self.LAYER_NAMES.get('fangzhi', '') and self.LAYER_NAMES['fangzhi'] in file_name:
                lid = 'fangzhi'
            elif self.LAYER_NAMES.get('yinhuan', '') and self.LAYER_NAMES['yinhuan'] in file_name:
                lid = 'yinhuan'
            else:
                continue

            try:
                self.load_shp_with_status(
                    shp_path, layer_id=lid, check_records=[],
                    color=self.LAYER_COLORS.get(lid, '#6366f1')
                )
                loaded += 1
            except Exception:
                pass

        return loaded

    def get_layer_features_for_table(self, layer_id: str) -> tuple:
        """
        获取用于属性表格显示的数据

        返回：(all_keys, features) 元组
        """
        if layer_id not in self._loaded_layers:
            return [], []

        layer_data = self._loaded_layers[layer_id]
        geojson = layer_data.get('geojson', {})
        features = geojson.get('features', [])

        skip_keys = {'_original_columns', '_status', 'geometry'}
        all_keys = []
        for f in features:
            for k in f.get('properties', {}):
                if k not in skip_keys and k not in all_keys:
                    all_keys.append(k)

        return all_keys, features

    def find_feature_by_row(self, layer_id: str, row: int) -> Optional[dict]:
        """根据行号获取要素"""
        if layer_id not in self._loaded_layers:
            return None

        layer_data = self._loaded_layers[layer_id]
        features = layer_data['geojson'].get('features', [])

        if 0 <= row < len(features):
            return features[row]
        return None
