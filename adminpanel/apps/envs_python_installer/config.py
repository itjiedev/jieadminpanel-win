import os
from pathlib import Path
from django.conf import settings

app_base_path = Path(__file__).resolve().parent
menu_main_file = settings.BASE_DIR / 'config' / 'menu_main.json'
pypi_file = app_base_path / 'data' / 'pypi.json'
python_download_path = app_base_path / 'data' / 'downloadsite.json'
python_version_file_path = app_base_path / 'data' / 'pythonVersions.json'
installed_file_path = app_base_path / "data" / 'installed-python.json'

project_python_path = settings.PYTHON_ROOT / 'python.exe'
tools_pip_path = settings.PYTHON_ROOT / 'Scripts' / 'pip.exe'
python_cache_dir = app_base_path / 'cache'

py_ini_path = os.path.join(os.environ.get('LOCALAPPDATA'), 'py.ini')

py_win_path = 'c:\\windows\\py.exe'
py_installed = False

if os.path.exists(py_win_path):
    py_path = py_win_path
    py_installed = True
else:
    py_path = app_base_path / 'tools' /'py.exe'
