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

def parse_pip_list(output):
    """
    解析 `pip list` 命令的输出，将其转换为字典或列表形式。

    参数:
        output (str): `pip list` 命令的输出内容。

    返回:
        list: 包含每个库名称和版本的字典列表。
    """
    package_list = {}
    for line in output.strip().split('\n'):
        if line.startswith('Package') or not line.strip() or line.startswith('---'):
            continue
        parts = line.split()
        if len(parts) >= 2:
            package_name = parts[0]
            version = parts[1]
            # latest = parts[2]
            package_list[package_name] = {
                'name': package_name,
                'version': version,
                # 'latest': latest,
            }
    return package_list