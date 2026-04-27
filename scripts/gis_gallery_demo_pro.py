import sys
import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
import json
from datetime import datetime
import random
import base64

class PhotoItem:
    """照片数据模型"""
    def __init__(self, path, lat, lng, title="", date=None, location_name=""):
        self.path = path
        self.lat = lat
        self.lng = lng
        self.title = title or os.path.basename(path)
        self.date = date or datetime.now()
        self.location_name = location_name
        
    def get_image_base64(self):
        """将图片转换为base64编码"""
        try:
            with open(self.path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
                # 根据文件扩展名确定MIME类型
                ext = os.path.splitext(self.path)[1].lower()
                mime_types = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.bmp': 'image/bmp'
                }
                mime_type = mime_types.get(ext, 'image/png')
                return f"data:{mime_type};base64,{encoded_string}"
        except:
            return None

class MapBridge(QObject):
    """用于Python和JavaScript通信的桥接类"""
    markerClicked = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
    @pyqtSlot(str)
    def onMarkerClicked(self, marker_id):
        self.markerClicked.emit(marker_id)

class MapWidget(QWidget):
    """地图组件"""
    photo_clicked = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.photos = []
        self.marker_map = {}  # 存储marker_id和photo_item的映射
        self.bridge = MapBridge()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建WebEngine视图
        self.web_view = QWebEngineView()
        
        # 设置WebChannel用于通信
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)
        
        # 连接信号
        self.bridge.markerClicked.connect(self.handle_marker_click)
        
        # 加载地图
        self.web_view.loadFinished.connect(self.on_load_finished)
        self.load_map()
        
        layout.addWidget(self.web_view)
        
    def load_map(self):
        """加载Leaflet地图"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8"/>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <style>
                body { margin: 0; padding: 0; }
                #map { height: 100vh; width: 100%; }
                .custom-marker {
                    background: white;
                    border: 3px solid #007AFF;
                    border-radius: 50%;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                    cursor: pointer;
                    overflow: hidden;
                }
                .marker-popup {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                }
                .marker-popup img {
                    border-radius: 8px;
                    margin-bottom: 8px;
                }
                .marker-popup h3 {
                    margin: 0 0 5px 0;
                    font-size: 14px;
                }
                .marker-popup p {
                    margin: 0;
                    color: #666;
                    font-size: 12px;
                }
                .leaflet-popup-content-wrapper {
                    border-radius: 12px;
                }
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var map;
                var markers = [];
                var bridge = null;
                var isMapInitialized = false;
                
                // 初始化WebChannel
                new QWebChannel(qt.webChannelTransport, function(channel) {
                    bridge = channel.objects.bridge;
                });
                
                function initMap() {
                    if (isMapInitialized) return;
                    
                    map = L.map('map', {
                        center: [39.9042, 116.4074],
                        zoom: 12,
                        zoomControl: true
                    });
                    
                    // 添加多个图层选项
                    var osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                        attribution: '© OpenStreetMap contributors',
                        maxZoom: 19
                    });
                    
                    var cartoLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png', {
                        attribution: '© CartoDB',
                        maxZoom: 19
                    });
                    
                    osmLayer.addTo(map);
                    
                    // 添加图层控制
                    var baseMaps = {
                        "OpenStreetMap": osmLayer,
                        "CartoDB Light": cartoLayer
                    };
                    
                    L.control.layers(baseMaps).addTo(map);
                    
                    // 添加比例尺
                    L.control.scale().addTo(map);
                    
                    isMapInitialized = true;
                    console.log("Map initialized successfully");
                }
                
                function addMarker(lat, lng, title, imageData, photoId) {
                    if (!map) {
                        console.error("Map not initialized");
                        return;
                    }
                    
                    // 创建自定义图标
                    var markerHtml = '<div style="width:40px;height:40px;border-radius:50%;overflow:hidden;background:#007AFF;">';
                    if (imageData) {
                        markerHtml += '<img src="' + imageData + '" style="width:100%;height:100%;object-fit:cover;">';
                    } else {
                        markerHtml += '<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:white;font-size:20px;">📷</div>';
                    }
                    markerHtml += '</div>';
                    
                    var customIcon = L.divIcon({
                        className: 'custom-marker',
                        html: markerHtml,
                        iconSize: [44, 44],
                        iconAnchor: [22, 22],
                        popupAnchor: [0, -22]
                    });
                    
                    var marker = L.marker([lat, lng], {icon: customIcon}).addTo(map);
                    
                    // 创建弹出窗口
                    var popupContent = '<div class="marker-popup">';
                    if (imageData) {
                        popupContent += '<img src="' + imageData + '" style="width:250px;height:150px;object-fit:cover;">';
                    }
                    popupContent += '<h3>' + title + '</h3>';
                    popupContent += '<p>📍 ' + lat.toFixed(4) + ', ' + lng.toFixed(4) + '</p>';
                    popupContent += '</div>';
                    
                    marker.bindPopup(popupContent, {
                        maxWidth: 270,
                        className: 'marker-popup'
                    });
                    
                    marker.on('click', function() {
                        if (bridge) {
                            bridge.onMarkerClicked(photoId);
                        }
                        map.setView([lat, lng], map.getZoom() < 14 ? 14 : map.getZoom(), {
                            animate: true,
                            duration: 0.5
                        });
                    });
                    
                    marker.photoId = photoId;
                    markers.push(marker);
                }
                
                function clearAllMarkers() {
                    markers.forEach(function(marker) {
                        map.removeLayer(marker);
                    });
                    markers = [];
                }
                
                function focusOnLocation(lat, lng) {
                    if (map) {
                        map.setView([lat, lng], 15, {
                            animate: true,
                            duration: 0.5
                        });
                    }
                }
                
                function fitAllMarkers() {
                    if (map && markers.length > 0) {
                        try {
                            var group = new L.featureGroup(markers);
                            map.fitBounds(group.getBounds().pad(0.2), {
                                animate: true,
                                duration: 0.5
                            });
                        } catch(e) {
                            console.error("Error fitting bounds:", e);
                        }
                    }
                }
                
                // 页面加载完成后初始化地图
                document.addEventListener('DOMContentLoaded', function() {
                    initMap();
                });
                
                // 如果DOMContentLoaded已经触发，直接初始化
                if (document.readyState === 'complete' || document.readyState === 'interactive') {
                    setTimeout(initMap, 100);
                }
            </script>
        </body>
        </html>
        """
        self.web_view.setHtml(html)
        
    def on_load_finished(self, ok):
        """页面加载完成后更新标记"""
        if ok:
            print("Map loaded successfully")
            # 延迟添加标记，确保地图完全初始化
            QTimer.singleShot(1000, self.update_markers)
            
    def update_markers(self):
        """更新地图标记"""
        # 先清除所有标记
        self.web_view.page().runJavaScript("clearAllMarkers();")
        
        # 添加新的标记
        for photo in self.photos:
            self.add_photo_marker(photo)
            
        # 适配所有标记
        QTimer.singleShot(500, self.fit_all_markers)
            
    def add_photo_marker(self, photo_item):
        """添加照片标记到地图"""
        photo_id = str(id(photo_item))
        self.marker_map[photo_id] = photo_item
        
        # 获取base64编码的图片
        image_data = photo_item.get_image_base64()
        
        # 转义字符串
        escaped_title = photo_item.title.replace("'", "\\'").replace('"', '\\"')
        
        # JavaScript代码
        if image_data:
            js_code = f"""
            addMarker({photo_item.lat}, {photo_item.lng}, "{escaped_title}", "{image_data}", "{photo_id}");
            """
        else:
            js_code = f"""
            addMarker({photo_item.lat}, {photo_item.lng}, "{escaped_title}", null, "{photo_id}");
            """
        
        self.web_view.page().runJavaScript(js_code)
        
    def clear_markers(self):
        """清除所有标记"""
        self.marker_map.clear()
        self.web_view.page().runJavaScript("clearAllMarkers();")
        
    def focus_on_photo(self, photo_item):
        """聚焦到指定照片位置"""
        js_code = f"focusOnLocation({photo_item.lat}, {photo_item.lng});"
        self.web_view.page().runJavaScript(js_code)
        
    def fit_all_markers(self):
        """适配所有标记到视图"""
        self.web_view.page().runJavaScript("fitAllMarkers();")
        
    def handle_marker_click(self, marker_id):
        """处理标记点击事件"""
        if marker_id in self.marker_map:
            photo_item = self.marker_map[marker_id]
            self.photo_clicked.emit(photo_item)
            
    def update_photos(self, photos):
        """更新照片列表并刷新地图"""
        self.photos = photos
        if self.web_view.page():
            self.update_markers()

class PhotoCard(QFrame):
    """照片卡片组件"""
    clicked = pyqtSignal(object)

    def __init__(self, photo_item, parent=None):
        super().__init__(parent)
        self.photo_item = photo_item
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(200, 220)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
            QFrame:hover {
                border: 2px solid #007aff;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.image_label = QLabel()
        pixmap = QPixmap(self.photo_item.path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(190, 150,
                                  Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(pixmap)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border-radius: 8px;")

        title_label = QLabel(self.photo_item.title)
        title_label.setFont(QFont("Arial", 10))
        title_label.setWordWrap(True)

        location_label = QLabel(f"📍 {self.photo_item.location_name}")
        location_label.setFont(QFont("Arial", 9))
        location_label.setStyleSheet("color: #666;")

        layout.addWidget(self.image_label)
        layout.addWidget(title_label)
        layout.addWidget(location_label)

    def mousePressEvent(self, event):
        self.clicked.emit(self.photo_item)
        super().mousePressEvent(event)

class PhotoGridView(QScrollArea):
    """照片网格视图"""
    photo_selected = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.widget = QWidget()
        self.grid_layout = QGridLayout(self.widget)
        self.grid_layout.setSpacing(15)
        self.setWidget(self.widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("background: transparent;")

    def add_photos(self, photos):
        """添加照片到网格"""
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        cols = 4
        for i, photo in enumerate(photos):
            card = PhotoCard(photo)
            card.clicked.connect(self.photo_selected.emit)
            row, col = divmod(i, cols)
            self.grid_layout.addWidget(card, row, col)

class PhotoDetailDialog(QDialog):
    """照片详情对话框"""

    def __init__(self, photo_item, parent=None):
        super().__init__(parent)
        self.photo_item = photo_item
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"照片详情 - {self.photo_item.title}")
        self.setMinimumSize(600, 500)
        self.setStyleSheet("""
            QDialog {
                background: white;
            }
            QPushButton {
                background: #007aff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #0051d5;
            }
            QLabel {
                color: #333;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        image_label = QLabel()
        pixmap = QPixmap(self.photo_item.path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(550, 400,
                                  Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation)
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        info_layout = QFormLayout()
        info_layout.addRow("标题:", QLabel(self.photo_item.title))
        info_layout.addRow("位置:", QLabel(self.photo_item.location_name))
        info_layout.addRow("坐标:",
                          QLabel(f"{self.photo_item.lat:.4f}, {self.photo_item.lng:.4f}"))
        info_layout.addRow("日期:",
                          QLabel(self.photo_item.date.strftime("%Y-%m-%d %H:%M")))

        btn_layout = QHBoxLayout()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)

        layout.addWidget(image_label)
        layout.addLayout(info_layout)
        layout.addLayout(btn_layout)

class ApplePhotosApp(QMainWindow):
    """主应用程序"""
    def __init__(self):
        super().__init__()
        self.all_photos = []
        self.filtered_photos = []
        self.init_ui()
        self.load_sample_data()
        
    def init_ui(self):
        self.setWindowTitle("照片地图浏览器 - PyQt6")
        self.setGeometry(100, 100, 1400, 800)
        
        # 设置全局样式
        self.setStyleSheet("""
            QMainWindow {
                background: #f5f5f7;
            }
            QStatusBar {
                background: #f5f5f7;
                border-top: 1px solid #e0e0e0;
            }
        """)
        
        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 工具栏
        toolbar_widget = QWidget()
        toolbar_widget.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 0.8);
                border-radius: 10px;
                padding: 10px;
            }
        """)
        toolbar = QHBoxLayout(toolbar_widget)
        
        # 标题
        title_label = QLabel("📸 照片地图")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1d1d1f;")
        
        # 视图切换按钮
        self.view_mode_btn = QPushButton("🗺️ 显示地图")
        self.view_mode_btn.setCheckable(True)
        self.view_mode_btn.clicked.connect(self.toggle_view_mode)
        self.view_mode_btn.setStyleSheet("""
            QPushButton {
                background: #007AFF;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #0056b3;
            }
            QPushButton:checked {
                background: #5856D6;
            }
        """)
        
        # 导入按钮
        import_btn = QPushButton("📁 导入照片")
        import_btn.clicked.connect(self.import_photos)
        import_btn.setStyleSheet("""
            QPushButton {
                background: #34C759;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #28a745;
            }
        """)
        
        # 适配按钮
        fit_btn = QPushButton("🔍 显示所有")
        fit_btn.clicked.connect(self.fit_all_markers)
        fit_btn.setStyleSheet("""
            QPushButton {
                background: #FF9500;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #e68600;
            }
        """)
        
        toolbar.addWidget(title_label)
        toolbar.addStretch()
        toolbar.addWidget(self.view_mode_btn)
        toolbar.addWidget(fit_btn)
        toolbar.addWidget(import_btn)
        
        main_layout.addWidget(toolbar_widget)
        
        # 内容区域
        self.content_stack = QStackedWidget()
        
        # 照片网格视图
        self.photo_grid = PhotoGridView()
        self.photo_grid.photo_selected.connect(self.show_photo_detail)
        
        # 地图视图
        self.map_widget = MapWidget()
        self.map_widget.photo_clicked.connect(self.show_photo_detail)
        
        self.content_stack.addWidget(self.photo_grid)
        self.content_stack.addWidget(self.map_widget)
        
        # 状态栏
        self.status_label = QLabel("准备就绪")
        self.status_label.setStyleSheet("color: #666; padding: 5px;")
        self.statusBar().addWidget(self.status_label)
        
        main_layout.addWidget(self.content_stack)
        
    def load_sample_data(self):
        """加载示例照片数据"""
        sample_locations = [
            (39.9042, 116.4074, "天安门广场"),
            (39.9142, 116.3974, "故宫博物院"),
            (39.8822, 116.4066, "天坛公园"),
            (39.9342, 116.4074, "国家体育场"),
            (39.9142, 116.3874, "北海公园"),
            (39.9242, 116.4174, "雍和宫"),
        ]
        
        for i, (lat, lng, name) in enumerate(sample_locations):
            sample_path = f"sample_photo_{i+1}.png"
            if not os.path.exists(sample_path):
                self.create_sample_image(sample_path, i, name)
            
            photo = PhotoItem(
                path=sample_path,
                lat=lat + (i * 0.002),
                lng=lng + (i * 0.002),
                title=f"{name}",
                date=datetime(2024, 1, i+1),
                location_name=name
            )
            self.all_photos.append(photo)
        
        self.filtered_photos = self.all_photos.copy()
        self.photo_grid.add_photos(self.filtered_photos)
        self.map_widget.update_photos(self.filtered_photos)
        
    def create_sample_image(self, path, index, name):
        """创建示例图片"""
        # ... [与之前相同的代码] ...
        pass
        
    def toggle_view_mode(self):
        """切换视图模式"""
        if self.view_mode_btn.isChecked():
            self.content_stack.setCurrentIndex(1)
            self.view_mode_btn.setText("📷 显示网格")
            self.status_label.setText("地图视图 - 点击标记查看照片")
            # 切换到地图时自动适配
            QTimer.singleShot(500, self.map_widget.fit_all_markers)
        else:
            self.content_stack.setCurrentIndex(0)
            self.view_mode_btn.setText("🗺️ 显示地图")
            self.status_label.setText("网格视图")
            
    def show_photo_detail(self, photo_item):
        """显示照片详情"""
        dialog = PhotoDetailDialog(photo_item, self)
        
        # 切换到地图并聚焦
        if not self.view_mode_btn.isChecked():
            self.view_mode_btn.setChecked(True)
            self.toggle_view_mode()
            
        self.map_widget.focus_on_photo(photo_item)
        dialog.exec()
        
    def fit_all_markers(self):
        """适配所有标记"""
        if not self.view_mode_btn.isChecked():
            self.view_mode_btn.setChecked(True)
            self.toggle_view_mode()
        self.map_widget.fit_all_markers()
        
    def import_photos(self):
        """导入照片"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择照片", "",
            "图片文件 (*.jpg *.jpeg *.png *.gif *.bmp)"
        )
        
        if files:
            for file_path in files:
                photo = PhotoItem(
                    path=file_path,
                    lat=39.9042 + random.uniform(-0.05, 0.05),
                    lng=116.4074 + random.uniform(-0.05, 0.05),
                    title=os.path.splitext(os.path.basename(file_path))[0],
                    date=datetime.now(),
                    location_name=f"导入位置"
                )
                self.all_photos.append(photo)
            
            self.filtered_photos = self.all_photos.copy()
            self.photo_grid.add_photos(self.filtered_photos)
            self.map_widget.update_photos(self.filtered_photos)
            
            QMessageBox.information(self, "导入成功", f"成功导入 {len(files)} 张照片！")
            
    def closeEvent(self, event):
        """关闭事件"""
        # 清理示例图片
        for i in range(1, 7):
            sample_path = f"sample_photo_{i}.png"
            if os.path.exists(sample_path):
                try:
                    os.remove(sample_path)
                except:
                    pass
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("照片地图浏览器")
    
    window = ApplePhotosApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()