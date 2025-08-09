import os
from pathlib import Path
from django.conf import settings

app_base_path = Path(__file__).resolve().parent
pypi_json = app_base_path / 'data' / 'pypi.json'

project_python_path = settings.PYTHON_ROOT / 'python.exe'
tools_pip_path = settings.PYTHON_ROOT / 'Scripts' / 'pip.exe'

