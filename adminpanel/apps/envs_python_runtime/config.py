import os
from pathlib import Path
from django.conf import settings

app_name = 'envs_python_runtime'
app_dir = Path(__file__).resolve().parent

app_data_dir = app_dir / 'data'
user_data_dir = settings.DATA_ROOT / app_name
cache_dir = app_dir / 'cache'

project_python_path = settings.PYTHON_ROOT / 'python.exe'

download_site_file = app_data_dir / 'downloadsite.json'
versions_json = app_data_dir / 'versions.json'
pypi_json = app_data_dir / 'pypi.json'

user_config_json = user_data_dir / 'user_config.json'
user_installed_json = user_data_dir / 'installed.json'


download_site_json_url = [
    "https://www.python.org/ftp/python/index-windows.json",
    "https://www.python.org/ftp/python/index-windows-recent.json",
    "https://www.python.org/ftp/python/index-windows-legacy.json",
]

create_type = {
    'install': "安装",
    'import': "导入",
}