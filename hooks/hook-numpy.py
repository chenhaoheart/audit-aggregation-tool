"""
PyInstaller hook to force pre-import of numpy internal modules
that may be missing or have lazy import issues in numpy 1.x and 2.x
"""
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = collect_submodules('numpy')

hiddenimports += [
    'numpy._core._multiarray_tests',
    'numpy._core._dtype',
    'numpy._core._ufunc_config',
    'numpy._core._rational',
    'numpy.core._multiarray_tests',
    'numpy.core._dtype',
    'numpy.core._ufunc_config',
    'numpy.core._rational',
    'numpy.core.multiarray',
    'numpy.core.umath',
    'numpy.core.numeric',
    'numpy.core.fromnumeric',
]

datas = collect_data_files('numpy')
