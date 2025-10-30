from pathlib import Path

from django.conf import settings

app_name = 'db_mysql'

app_path = Path(__file__).resolve().parent
config_file_path = settings.DATA_ROOT / app_name / 'config.json'

installed_file_path = settings.DATA_ROOT / app_name / 'installed.json'
app_data_dir = app_path / 'data'
app_cache_dir = app_path / 'cache'
version_file = app_data_dir / 'version.json'
software_file = app_data_dir / 'software.json'

download_url = 'https://downloads.mysql.com/archives/get/p/23/file/mysql-{}-winx64.zip'

# https://cdn.mysql.com/archives/mysql-8.3/mysql-8.3.0-winx64.zip
