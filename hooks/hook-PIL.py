"""
PyInstaller hook for PIL/Pillow
Ensures image processing libraries are included
"""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = collect_submodules('PIL')
hiddenimports += [
    'PIL.Image',
    'PIL._imaging',
    'PIL._imagingft',
    'PIL._imagingmorph',
]

datas = collect_data_files('PIL')