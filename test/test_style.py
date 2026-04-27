import sys
sys.path.insert(0, r'd:\github\空间数据检查桌面版-主题-design')
from ui.pages.photo_gallery_page import PhotoGalleryPage
print('PhotoGalleryPage import OK')

# 检查样式定义
from core.stylesheet.sections.content import generate_content_stylesheet
from core.theme_manager import get_theme_manager
tm = get_theme_manager()
theme = tm.get_current_theme()
css = generate_content_stylesheet(theme)

print(f'Has QFrame#pageHeader: {"QFrame#pageHeader" in css}')
print(f'Has QFrame#accentBar: {"QFrame#accentBar" in css}')
print(f'Has QLabel#sectionHeaderLg: {"QLabel#sectionHeaderLg" in css}')
print(f'Has QLabel#pageSubtitle: {"QLabel#pageSubtitle" in css}')

print('\n样式统一完成!')