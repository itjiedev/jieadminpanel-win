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


def parse_mysql_version(version_string):
    """解析MySQL版本号，支持5.7和8.0格式"""
    import re
    # MySQL 8.0: mysql  Ver 8.0.33 for Win64 on x86_64
    # MySQL 5.7: mysql.exe  Ver 14.14 Distrib 5.7.44, for Win64 (x86_64)
    # 优先匹配包含"Distrib"的5.7格式
    distrib_pattern = r'Distrib\s+([\d\.]+)'
    match = re.search(distrib_pattern, version_string)
    if match:
        return match.group(1)

    # 匹配8.0格式的版本号 (第二个Ver)
    ver_patterns = list(re.finditer(r'Ver\s+([\d\.]+)', version_string))
    if ver_patterns:
        # 如果有多个Ver匹配，取最后一个（通常是实际版本号）
        if len(ver_patterns) > 1:
            return ver_patterns[-1].group(1)
        else:
            return ver_patterns[0].group(1)

    # 通用格式匹配
    general_pattern = r'(\d+\.\d+\.\d+)'
    match = re.search(general_pattern, version_string)
    if match:
        return match.group(1)

    return None