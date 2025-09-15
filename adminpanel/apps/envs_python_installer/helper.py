import json

from jiefoundation.utils import run_command

from .config import (
    installed_file_path, python_version_file_path, py_installed, py_path,python_download_path,
)

def get_python_versions(version_name=None):
    with open(python_version_file_path, 'r', encoding='utf-8') as f:
        versions = json.load(f)
    if version_name:
        return versions[version_name]
    return versions

def get_installed(version_name=None):
    versions = {}
    with open(installed_file_path, 'r', encoding='utf-8') as f:
        versions = json.load(f)
    if version_name: return versions[version_name]
    return versions


def get_py_default_python():
    """
    判断系统中的py launcher默认设置的是什么版本
    """
    if py_installed:
        result = run_command([py_path, '-V'])
        if result.returncode == 0:
            if result.stdout.strip():
                return result.stdout.strip().split(maxsplit=1)[1].strip()
            else:
                return result.stderr.strip().split(maxsplit=1)[1].strip()
    return ''

def python_list_paths():
    """
    使用 py launcher获取已经安装的python版本列表，并进行默认设置
    """
    result = run_command([py_path, '--list-paths'])
    if result.returncode == 0:
        lines = result.stdout.strip().splitlines()
        versions = {}
        for line in lines:
            if not line.startswith('No'):
                if line.strip():
                    parts = line.strip().split(maxsplit=1)
                    if len(parts) == 2:
                        tag, path = parts
                        path = path.replace('* ', '').strip()
                        run_get_version = run_command([path, '-V'])
                        out_str = ''
                        if run_get_version.stdout.strip():
                            out_str = run_get_version.stdout.strip()
                        else:
                            out_str = run_get_version.stderr.strip()
                        version = out_str.split(maxsplit=1)[1].strip()
                        version_split = version.split('.')
                        py_default = get_py_default_python()
                        is_py_default = False
                        if py_default == version: is_py_default = True

                        versions[version] = {
                            'name':  f"Python-{version}",
                            'folder': path.rstrip('python.exe').replace('\\', '/'),
                            'version': version,
                            'is_py_default': is_py_default,
                            'version_major': int(version_split[0]),
                            'version_minor': int(version_split[1]),
                            'version_patch': int(version_split[2]) if len(version_split) > 2 else '0',
                            'tag': f'{version_split[0]}.{version_split[1]}'
                        }
        return versions
    else:
        return {}
