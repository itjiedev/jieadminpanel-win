import json
from pathlib import Path

def get_installed(id=None):
    from .config import installed_file_path
    if not installed_file_path.exists():
        installed_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(installed_file_path, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
        return {}
    with open(installed_file_path, 'r', encoding='utf-8') as f:
        installed = json.load(f)
    if id: return installed[id]
    return installed

def get_config():
    from .config import config_file_path
    if not config_file_path.exists():
        config_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file_path, 'w', encoding='utf-8') as f:
            json.dump({'install_folder': ''}, f, ensure_ascii=False, indent=4)
            return {'install_folder': ''}
    with open(config_file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_version(version=None):
    from .config import version_file
    with open(version_file, 'r', encoding='utf-8') as f:
        versions = json.load(f)
    if version:
        return versions.get(version)
    return versions
