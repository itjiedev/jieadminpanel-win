import os
import json
from jiefoundation.utils import run_command, get_reg_user_env, ensure_path_separator

from .config import project_python_path, pypi_json

def get_default_pypi():
    result = run_command(f"{project_python_path} -m pip config get global.index-url")
    if result['returncode'] == 1:
        return "https://pypi.org/simple"
    else:
        return result['stdout'].strip()


def get_pypi_list(pypi_name=None):
    """
    获取PyPI包列表信息

    参数:
        name (str, optional): 指定要获取的包名称，如果为None则返回所有包信息

    返回:
        dict: 如果指定了name且存在对应包信息，则返回该包的信息字典；
              否则返回包含所有包信息的字典
    """
    default_pypi = get_default_pypi()
    pypi_list = {}
    with open(pypi_json, 'r', encoding='utf-8') as f:
        pypi_list = json.load(f)
        for name, pypi in pypi_list.items():
            if pypi['url'] == default_pypi:
                is_default = True
            else:
                is_default = False
            pypi_list[name] = {
                'title': pypi['title'],
                'url': pypi['url'],
                'is_default': is_default,
            }
            if pypi_name == name:
                return pypi_list[name]
    return pypi_list


def get_default_env_python():
    """
    通过环境变量的path值来 判断默认的环境变量中设置的python版本和路径
    """
    user_path_list = get_reg_user_env("PATH").split(";")
    for path in user_path_list:
        path = ensure_path_separator(path)
        if os.path.exists(os.path.join(path, 'python.exe')):
            return {
                "path": path, "version": run_command([f'{path}python.exe', '-V'])['stdout'].split(maxsplit=1)[1].strip()}
    return ''


def get_packages(python_path):
    """
    获取包列表

    Args:
        python_path: 要执行的 pytthon 文件路径

    Returns:
        包含包信息的字典列表
    """
    cmd = [python_path, '-m', 'pip', 'list', '--format=json']
    result = run_command(cmd)
    package_list = json.loads(result['stdout'])
    return package_list


def get_packages_update(python_path, packages = None):
    """
    获取包更新信息

    Args:
        python_path: 要执行的 python 文件路径
        packages: 要检查的包列表，如果为None则检查所有包

    Returns:
        包含更新信息的字典列表
    """
    if packages is None:
        cmd = [python_path, '-m', 'pip', 'list', '--outdated', '--format=json']
    else:
        cmd = [python_path, '-m', 'pip', 'list', '--outdated', packages, '--format=json']
    outdated_list = json.loads(run_command(cmd)['stdout'])
    return_dict = {}
    for package in outdated_list:
        return_dict[package['name']] = {
            'name': package['name'],
            'current_version': package['version'],
            'latest_version': package['latest_version'],
            'latest_filetype': package['latest_filetype'],
        }
    return return_dict


def get_package_list(python_path, packages = None):
    """
    获取包更新信息

    Args:
        python_path: 要执行的 pytthon 文件路径
        packages: 要检查的包列表，如果为None则检查所有包

    Returns:
        包含更新信息的字典列表
    """
    try:
        packages = get_packages(python_path)
        updates = get_packages_update(python_path)

        return_dict = {}
        for package in packages:
            latest_version = ''
            latest_filetype = ''
            if package['name'] in updates:
                latest_version = updates[package['name']]['latest_version']
                latest_filetype = updates[package['name']]['latest_filetype']
            return_dict[package['name']] = {
                'name': package['name'],
                'current_version': package['version'],
                'latest_version': latest_version,
                'latest_filetype': latest_filetype,
            }
        return return_dict
    except json.JSONDecodeError as e:
        print(f"解析JSON时出错: {e}")
        return []


# def parse_pip_list(python_path):
#     packages = get_package_list(python_path)
#     updates = get_package_updates(python_path)
#
#     package_list = {}
#     for line in output.strip().split('\n'):
#         if line.startswith('Package') or not line.strip() or line.startswith('---'):
#             continue
#         parts = line.split()
#         if len(parts) >= 2:
#             package_name = parts[0]
#             version = parts[1]
#             latest = ''
#             if updates:
#                 if package_name in updates:
#                     latest = updates[package_name]['latest_version']
#             package_list[package_name] = {
#                 'name': package_name,
#                 'version': version,
#                 'latest': latest,
#             }
#     return package_list



def package_upgrade(python_path, package_name):
    """
    升级包

    Args:
        python_path: 要执行的 pytthon 文件路径
        package_name: 要升级的包名称

    Returns:
        执行结果
    """
    cmd = [python_path, '-m', 'pip', 'install', '--upgrade', package_name]
    result = run_command(cmd)
    return result