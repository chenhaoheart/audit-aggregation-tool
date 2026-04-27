# -*- coding: utf-8 -*-
"""
图册管理业务服务层

职责:
- 文件夹扫描(照片/视频)
- EXIF GPS 信息提取
- 批量重命名
- 批量缩放
- 缩略图生成
- 文件夹删除
"""

import os
import re
import shutil
import base64
import io
from datetime import datetime
from typing import Dict, List, Optional, Any
from PySide6.QtCore import QObject, Signal, QThread

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

try:
    import exifread
    HAS_EXIFREAD = True
except ImportError:
    HAS_EXIFREAD = False


PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}


class PhotoGalleryService(QObject):
    """图册管理业务服务"""

    scan_finished = Signal(dict)
    scan_progress = Signal(str)
    rename_finished = Signal(dict)
    resize_finished = Signal(dict)
    error_occurred = Signal(str)
    gps_extracted = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scan_result = None
        self._is_running = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def scan_result(self) -> Optional[dict]:
        return self._scan_result

    def scan_folder(self, folder_path: str, recursive: bool = True) -> dict:
        """
        扫描文件夹，返回文件列表和统计信息

        返回:
            {
                'root_path': str,
                'folders': [{'folder_path': str, 'files': [...], 'photo_count': int, 'video_count': int, 'total_size': int}],
                'total_photos': int,
                'total_videos': int,
                'total_size_mb': float
            }
        """
        self._is_running = True
        self.scan_progress.emit(f"开始扫描: {folder_path}")

        result = {
            'root_path': folder_path,
            'folders': [],
            'total_photos': 0,
            'total_videos': 0,
            'total_size_mb': 0.0
        }

        try:
            if not os.path.isdir(folder_path):
                raise ValueError(f"路径不存在: {folder_path}")

            folder_files = {}

            if recursive:
                for root, dirs, files in os.walk(folder_path):
                    for f in files:
                        ext = os.path.splitext(f)[1].lower()
                        if ext in PHOTO_EXTENSIONS or ext in VIDEO_EXTENSIONS:
                            full_path = os.path.join(root, f)
                            file_info = self._get_file_info(full_path)
                            if root not in folder_files:
                                folder_files[root] = []
                            folder_files[root].append(file_info)
            else:
                for f in os.listdir(folder_path):
                    full_path = os.path.join(folder_path, f)
                    if os.path.isfile(full_path):
                        ext = os.path.splitext(f)[1].lower()
                        if ext in PHOTO_EXTENSIONS or ext in VIDEO_EXTENSIONS:
                            file_info = self._get_file_info(full_path)
                            folder_files[folder_path] = folder_files.get(folder_path, [])
                            folder_files[folder_path].append(file_info)

            total_size = 0
            for folder_path, files in folder_files.items():
                photo_count = sum(1 for f in files if f['type'] == 'photo')
                video_count = sum(1 for f in files if f['type'] == 'video')
                folder_size = sum(f['size'] for f in files)

                result['folders'].append({
                    'folder_path': folder_path,
                    'files': files,
                    'photo_count': photo_count,
                    'video_count': video_count,
                    'total_size': folder_size
                })

                result['total_photos'] += photo_count
                result['total_videos'] += video_count
                total_size += folder_size

            result['total_size_mb'] = round(total_size / (1024 * 1024), 2)
            self._scan_result = result

            self.scan_progress.emit(f"扫描完成: {result['total_photos']} 照片, {result['total_videos']} 视频")
            self.scan_finished.emit(result)

        except Exception as e:
            self.error_occurred.emit(str(e))

        finally:
            self._is_running = False

        return result

    def _get_file_info(self, file_path: str) -> dict:
        """获取单个文件的信息"""
        stat = os.stat(file_path)
        ext = os.path.splitext(file_path)[1].lower()
        filename = os.path.basename(file_path)

        file_type = 'photo' if ext in PHOTO_EXTENSIONS else 'video'
        modified_time = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')

        gps_info = self._extract_gps(file_path) if HAS_EXIFREAD and file_type == 'photo' else None

        return {
            'path': file_path,
            'name': filename,
            'extension': ext,
            'type': file_type,
            'size': stat.st_size,
            'modified': modified_time,
            'has_gps': gps_info is not None,
            'latitude': gps_info.get('latitude') if gps_info else None,
            'longitude': gps_info.get('longitude') if gps_info else None,
            'exif': gps_info.get('exif') if gps_info else None
        }

    def _extract_gps(self, file_path: str) -> Optional[dict]:
        """从图片提取 GPS 信息"""
        if not HAS_EXIFREAD:
            return None

        try:
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)

            gps_latitude = tags.get('GPS GPSLatitude')
            gps_latitude_ref = tags.get('GPS GPSLatitudeRef')
            gps_longitude = tags.get('GPS GPSLongitude')
            gps_longitude_ref = tags.get('GPS GPSLongitudeRef')

            if not gps_latitude or not gps_longitude:
                return None

            lat = self._convert_to_degrees(gps_latitude)
            if gps_latitude_ref and gps_latitude_ref.values == 'S':
                lat = -lat

            lon = self._convert_to_degrees(gps_longitude)
            if gps_longitude_ref and gps_longitude_ref.values == 'W':
                lon = -lon

            exif_info = {
                'make': str(tags.get('Image Make', '')),
                'model': str(tags.get('Image Model', '')),
                'date_original': str(tags.get('EXIF DateTimeOriginal', '')),
                'width': tags.get('EXIF ExifImageWidth'),
                'height': tags.get('EXIF ExifImageHeight')
            }
            if exif_info['width']:
                exif_info['width'] = str(exif_info['width'])
            if exif_info['height']:
                exif_info['height'] = str(exif_info['height'])

            return {
                'latitude': lat,
                'longitude': lon,
                'exif': exif_info
            }

        except Exception:
            return None

    def _convert_to_degrees(self, value) -> float:
        """将 GPS 坐标转换为度数"""
        if not value:
            return 0.0

        try:
            values = value.values
            d = float(values[0].num) / float(values[0].den) if values[0].den != 0 else 0
            m = float(values[1].num) / float(values[1].den) if values[1].den != 0 else 0
            s = float(values[2].num) / float(values[2].den) if values[2].den != 0 else 0
            return d + (m / 60.0) + (s / 3600.0)
        except Exception:
            return 0.0

    def get_gps_for_files(self, file_paths: List[str]) -> List[dict]:
        """批量获取文件的 GPS 信息"""
        locations = []

        for path in file_paths:
            ext = os.path.splitext(path)[1].lower()
            if ext in PHOTO_EXTENSIONS:
                gps_info = self._extract_gps(path)
                if gps_info:
                    locations.append({
                        'path': path,
                        'name': os.path.basename(path),
                        'latitude': gps_info['latitude'],
                        'longitude': gps_info['longitude']
                    })

        self.gps_extracted.emit(locations)
        return locations

    def batch_rename(self, file_paths: List[str], pattern: str = '{index}', start_index: int = 1) -> dict:
        """
        批量重命名文件

        pattern 支持: {index}, {name}, {ext}, {date}
        """
        result = {'success': 0, 'failed': 0, 'errors': []}

        for i, path in enumerate(file_paths):
            try:
                old_name = os.path.basename(path)
                name_without_ext = os.path.splitext(old_name)[0]
                ext = os.path.splitext(path)[1]
                date_str = datetime.now().strftime('%Y%m%d')
                modified_date = datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y%m%d')

                new_name = pattern.replace('{index}', str(start_index + i))
                new_name = new_name.replace('{name}', name_without_ext)
                new_name = new_name.replace('{ext}', ext.lstrip('.'))
                new_name = new_name.replace('{date}', date_str)

                if not new_name.endswith(ext):
                    new_name += ext

                new_path = os.path.join(os.path.dirname(path), new_name)

                if new_path != path:
                    os.rename(path, new_path)
                    result['success'] += 1

            except Exception as e:
                result['failed'] += 1
                result['errors'].append({'path': path, 'error': str(e)})

        self.rename_finished.emit(result)
        return result

    def batch_resize(self, file_paths: List[str], width: int = 1920, height: int = 1080,
                     keep_aspect: bool = True, quality: int = 85, output_dir: str = None) -> dict:
        """
        批量缩放图片

        参数:
            file_paths: 图片路径列表
            width: 目标宽度
            height: 目标高度
            keep_aspect: 是否保持宽高比
            quality: 输出质量 (1-100)
            output_dir: 输出目录，None 则覆盖原文件
        """
        if not HAS_PILLOW:
            self.error_occurred.emit("Pillow 未安装，无法执行缩放操作")
            return {'success': 0, 'failed': len(file_paths), 'errors': [{'path': '', 'error': 'Pillow not installed'}]}

        result = {'success': 0, 'failed': 0, 'errors': []}

        for path in file_paths:
            try:
                ext = os.path.splitext(path)[1].lower()
                if ext not in PHOTO_EXTENSIONS:
                    result['failed'] += 1
                    result['errors'].append({'path': path, 'error': 'Not a photo file'})
                    continue

                img = Image.open(path)
                original_w, original_h = img.size

                if keep_aspect:
                    ratio = min(width / original_w, height / original_h)
                    new_w = int(original_w * ratio)
                    new_h = int(original_h * ratio)
                else:
                    new_w = width
                    new_h = height

                resized = img.resize((new_w, new_h), Image.LANCZOS)

                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                    save_path = os.path.join(output_dir, os.path.basename(path))
                else:
                    save_path = path

                save_format = 'JPEG' if ext in {'.jpg', '.jpeg'} else 'PNG' if ext == '.png' else None
                if save_format == 'JPEG':
                    resized.save(save_path, format=save_format, quality=quality)
                elif save_format:
                    resized.save(save_path, format=save_format)
                else:
                    resized.save(save_path)

                result['success'] += 1

            except Exception as e:
                result['failed'] += 1
                result['errors'].append({'path': path, 'error': str(e)})

        self.resize_finished.emit(result)
        return result

    def get_thumbnail(self, file_path: str, size: int = 200) -> Optional[str]:
        """
        生成缩略图并返回临时路径

        返回临时文件路径，调用方负责清理
        """
        if not HAS_PILLOW:
            return None

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in PHOTO_EXTENSIONS:
            return None

        try:
            img = Image.open(file_path)
            img.thumbnail((size, size), Image.LANCZOS)

            import tempfile
            temp_path = tempfile.mktemp(suffix='.jpg')
            img.save(temp_path, 'JPEG', quality=80)

            return temp_path

        except Exception:
            return None

    def delete_folder(self, folder_path: str) -> bool:
        """删除文件夹及其所有内容"""
        try:
            if not os.path.isdir(folder_path):
                return False

            shutil.rmtree(folder_path)
            return True

        except Exception as e:
            self.error_occurred.emit(f"删除文件夹失败: {str(e)}")
            return False

    def format_size(self, bytes: int) -> str:
        """格式化文件大小"""
        if bytes < 1024:
            return f"{bytes} B"
        if bytes < 1024 * 1024:
            return f"{bytes / 1024:.1f} KB"
        return f"{bytes / (1024 * 1024):.1f} MB"

    def build_tree_structure(self, result: dict) -> dict:
        """将扫描结果构建为树形数据结构"""
        root_path = result.get('root_path', '')

        tree = {
            'name': os.path.basename(root_path) or root_path,
            'path': root_path,
            'isRoot': True,
            'children': {},
            'files': [],
            'photo_count': result['total_photos'],
            'video_count': result['total_videos']
        }

        for folder_info in result['folders']:
            folder_path = folder_info['folder_path']
            relative_path = folder_path.replace(root_path, '').lstrip('/\\')
            parts = [p for p in relative_path.split('/' if '/' in relative_path else '\\') if p]

            current = tree
            current_path = root_path

            for part in parts:
                current_path = os.path.join(current_path, part)
                if part not in current['children']:
                    current['children'][part] = {
                        'name': part,
                        'path': current_path,
                        'children': {},
                        'files': [],
                        'photo_count': 0,
                        'video_count': 0
                    }
                current = current['children'][part]

            current['files'] = folder_info['files']
            current['photo_count'] = folder_info['photo_count']
            current['video_count'] = folder_info['video_count']

        return tree

    def build_fubiao_geojson(self, matched_records: list, type_label: str) -> dict:
        """将附表匹配记录构建为GeoJSON FeatureCollection"""
        features = []
        for rec in matched_records:
            lon = rec.get('longitude')
            lat = rec.get('latitude')
            if not lon or not lat:
                continue
            try:
                lon = float(lon)
                lat = float(lat)
            except (ValueError, TypeError):
                continue

            photos_data = []
            for photo in rec.get('photos', []):
                thumb_b64 = self.encode_photo_thumbnail(photo['path'])
                if thumb_b64:
                    photos_data.append({
                        'name': photo['name'],
                        'path': photo['path'].replace('\\', '/'),
                        'data': thumb_b64
                    })

            properties = {
                '_popup_type': 'photo_card',
                '_type_label': type_label,
                'name': rec.get('name', ''),
                'code': rec.get('code', ''),
                'river_name': rec.get('river_name', ''),
                'river_code': rec.get('river_code', ''),
                'longitude': str(lon),
                'latitude': str(lat),
                '_photos': photos_data
            }

            features.append({
                'type': 'Feature',
                'id': rec.get('code', ''),
                'geometry': {'type': 'Point', 'coordinates': [lon, lat]},
                'properties': properties
            })

        return {'type': 'FeatureCollection', 'features': features}

    def build_photo_geojson(self, files: list, layer_id: str = 'photos') -> dict:
        """将带GPS的文件列表构建为GeoJSON FeatureCollection"""
        locations = [f for f in files if f.get('has_gps')]
        features = []
        for loc in locations:
            features.append({
                'type': 'Feature',
                'id': loc['path'],
                'geometry': {'type': 'Point', 'coordinates': [loc['longitude'], loc['latitude']]},
                'properties': {'name': loc['name'], 'path': loc['path']}
            })
        return {'type': 'FeatureCollection', 'features': features}

    def encode_photo_thumbnail(self, photo_path: str, size: int = 96) -> str:
        """将图片编码为base64 JPEG缩略图"""
        try:
            if not HAS_PILLOW or not os.path.exists(photo_path):
                return ''
            with Image.open(photo_path) as img:
                img.load()
                img.thumbnail((size, size), Image.LANCZOS)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                return base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception:
            return ''

    def get_folder_photos(self, folder_path: str) -> List[str]:
        """获取文件夹下所有照片文件路径"""
        photos = []
        try:
            for f in os.listdir(folder_path):
                ext = os.path.splitext(f)[1].lower()
                if ext in PHOTO_EXTENSIONS:
                    photos.append(os.path.join(folder_path, f))
        except Exception:
            pass
        return photos

    def file_matches_filter(self, file_info: dict, search_query: str = '', filter_type: str = 'all') -> bool:
        """检查文件是否匹配过滤条件"""
        if search_query and search_query not in file_info['name'].lower():
            return False
        if filter_type == "photo" and file_info['type'] != 'photo':
            return False
        if filter_type == "video" and file_info['type'] != 'video':
            return False
        return True