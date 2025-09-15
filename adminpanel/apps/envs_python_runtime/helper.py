import os
import json
import requests

from .config import (
    download_site_file, user_config_json, download_site_json_url, versions_json, pypi_json,
    user_installed_json, project_python_path
)
from jiefoundation.utils import run_command

def get_user_config(config_name=None):
    if not os.path.exists(user_config_json):
        with open(user_config_json, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
    with open(user_config_json, 'r', encoding='utf-8') as f:
        configs = json.load(f)
    if config_name and config_name in configs: return configs[config_name]
    return configs

def get_downloadsite(site_name=None):
    with open(download_site_file, 'r', encoding='utf-8') as f:
        downloadsites = json.load(f)
    if site_name and site_name in downloadsites: return downloadsites[site_name]
    return downloadsites

def update_version_info():
    """
    从远程URL获取版本信息，经过梳理后，更新本地版本信息json文件。
    """
    try:
        from packaging.version import Version as version_parser
    except ImportError:
        def version_parser(version_str):
            import re
            clean_version = re.search(r'[\d.]+', version_str)
            if clean_version:
                return [int(x) for x in clean_version.group().split('.')]
            return version_str

    try:
        versions = {}
        for json_url in download_site_json_url:
            response = requests.get(json_url)
            response.raise_for_status()
            json_data = response.json()
            for version in json_data['versions']:
                if (version['id'].endswith('-64') and ('embeddable' not in version['display-name'])
                        and ('with tests' not in version['display-name']) and ('free-threaded' not in version['display-name'])
                        and ('-dev-' not in version['tag'])
                ):
                    version['display-name'] = version['display-name'].replace(' ', '-')
                    file_name = os.path.basename(version['url'])
                    sha256 = ''
                    if 'hash' in version:
                        sha256 = version['hash']['sha256']
                    versions[version['display-name']] = {
                        'sort_version': version['sort-version'],
                        'tag': version['tag'],
                        'display_name': version['display-name'],
                        'url': version['url'],
                        'file_name': file_name,
                        'sha256': sha256,
                    }
        sorted_versions_list = sorted(
            versions.items(),
            key=lambda item: version_parser(item[1]['sort_version']),
            reverse=True
        )
        sorted_versions = dict(sorted_versions_list)
        with open(versions_json, 'w', encoding='utf-8') as f:
            json.dump(sorted_versions, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"更新版本信息时出错: {e}")

def get_versions(version=None):
    """
    读取版本信息json文件，返回字典
    """
    with open(versions_json, 'r', encoding='utf-8') as f:
        versions = json.load(f)
    if version and version in versions:
        return versions[version]
    return versions


def get_installed(unique_identifier=None):
    """
    读取已安装的版本信息json文件，返回字典
    """
    with open(user_installed_json, 'r', encoding='utf-8') as f:
        installed = json.load(f)
    for unique_name, info in installed.items():
        installed[unique_name]['folder'] = installed[unique_name]['folder'].replace('\\', '/')
        installed[unique_name]['is_path'] = os.path.exists(info['folder'])
    if unique_identifier:
        if unique_identifier in installed:
            return installed[unique_identifier]
        else:
            return None

    return installed

def get_available_versions():
    """
    获取可安装的版本列表（过滤掉已安装的版本）
    """
    all_versions = get_versions()
    installed_versions = get_installed()
    return {version: info for version, info in all_versions.items()
            if version not in installed_versions}


def get_installed_sorted():
    """
    获取已安装版本并按版本号从高到低排序
    """
    installed = get_installed()

    def version_key(item):
        version_str, version_info = item
        return (
            version_info.get('version_major', 0),
            version_info.get('version_minor', 0),
            version_info.get('version_patch', 0)
        )
    sorted_items = sorted(installed.items(), key=version_key, reverse=True)
    return dict(sorted_items)

def get_default_pypi():
    result = run_command(f"{project_python_path} -m pip config get global.index-url")
    if result['returncode'] == 1:
        return "https://pypi.org/simple"
    else:
        return result['stdout'].strip()


def get_pypi_list():
    pypi_list = {}
    default_pypi = get_default_pypi()

    with open(pypi_json, 'r', encoding='utf-8') as f:
        pypis = json.load(f)
        for name, pypi in pypis.items():
            if pypi['url'] == default_pypi:
                is_default = True
            else:
                is_default = False
            pypi_list[name] = {
                'title': pypi['title'],
                'url': pypi['url'],
                'is_default': is_default,
            }
    return pypi_list