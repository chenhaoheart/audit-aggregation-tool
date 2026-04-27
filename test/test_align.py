import sys
sys.path.insert(0, r'd:\github\空间数据检查桌面版-主题-design')
from ui.pages.photo_gallery_page import PhotoGalleryPage
print('PhotoGalleryPage import OK')

# 检查布局设置
import re
with open(r'd:\github\空间数据检查桌面版-主题-design\ui\pages\photo_gallery_page.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
# 检查三个容器是否都有 AlignTop
tree_align = 'tree_container_layout.setAlignment(Qt.AlignTop)' in content
list_align = 'layout.setAlignment(Qt.AlignTop)' in content and '_setup_list_view' in content
map_align = 'map_container_layout.setAlignment(Qt.AlignTop)' in content

print(f'tree_container_layout has AlignTop: {tree_align}')
print(f'list_view layout has AlignTop: {list_align}')
print(f'map_container_layout has AlignTop: {map_align}')

if tree_align and list_align and map_align:
    print('\nAll three containers now have AlignTop - FIXED!')