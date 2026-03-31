"""
PyInstaller hook to force pre-import of numpy internal modules
that may be missing or have lazy import issues in numpy 2.0
"""
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all numpy submodules
hiddenimports = collect_submodules('numpy')

# Force import these specific modules that have issues with lazy loading
hiddenimports += [
    'numpy._core._multiarray_tests',
    'numpy._core._dtype',
    'numpy._core._ufunc_config',
    'numpy._core._rational',
]

datas = collect_data_files('numpy')
