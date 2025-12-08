import winreg
import os
import configparser
import socket
import ctypes

def refresh_environment():
    """刷新环境变量，使更改立即生效"""
    # 发送系统消息通知所有进程环境变量已更改
    HWND_BROADCAST = 0xFFFF
    WM_SETTINGCHANGE = 0x1A
    SMTO_ABORTIFHUNG = 0x0002

    # 通过ctypes调用Windows API
    result = ctypes.c_long()
    ctypes.windll.user32.SendMessageTimeoutW(
        HWND_BROADCAST,
        WM_SETTINGCHANGE,
        0,
        "Environment",
        SMTO_ABORTIFHUNG,
        5000,
        ctypes.byref(result)
    )

def read_registry_value(hive, key_path, value_name, default=None):
    """
    通用函数：读取指定的注册表键值

    参数:
        hive: 注册表根键 (如 winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE)
        key_path: 注册表项路径 (如 'Environment', r'SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment')
        value_name: 要读取的值名称
        default: 如果找不到值时返回的默认值

    返回:
        注册表值或默认值
    # 使用示例
    # 读取用户环境变量
    # user_path = read_registry_value(winreg.HKEY_CURRENT_USER, 'Environment', 'PATH')
    """
    try:
        with winreg.OpenKey(hive, key_path) as key:
            value, _ = winreg.QueryValueEx(key, value_name)
            return value
    except FileNotFoundError:
        # 键或值不存在
        return default
    except Exception as e:
        # 其他异常情况
        print(f"读取注册表失败: {e}")
        return default


def get_reg_user_env(env_name):
    """获取当前用户注册表环境变量"""
    value = ''
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment') as key:
        value, _ = winreg.QueryValueEx(key, env_name)
    return value

def set_reg_user_env(env_name, env_value):
    """
    设置用户环境变量到注册表
    :param env_name: 环境变量名，例如 "PATH"
    :param env_value: 环境变量值，例如 "C:\\Python39;%PATH%"
    """
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, env_name, 0, winreg.REG_EXPAND_SZ, env_value)
        refresh_environment()
        return True
    except Exception as e:
        print(f"写入注册表失败: {e}")
        return False


def set_reg_system_env(env_name, env_value):
    """
    设置系统环境变量到注册表（需要管理员权限）
    :param env_name: 环境变量名，例如 "PATH"
    :param env_value: 环境变量值，例如 "C:\\Python39;%PATH%"
    """
    key_path = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, env_name, 0, winreg.REG_EXPAND_SZ, env_value)
        refresh_environment()
        return True
    except PermissionError:
        print("权限不足，请以管理员身份运行程序。")
        return False
    except Exception as e:
        print(f"写入系统注册表失败: {e}")
        return False

# 获取系统 PATH
def get_reg_system_env(env_name):
    """
    获取系统环境变量
    """
    value = ''
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                        r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment') as key:
        value, _ = winreg.QueryValueEx(key, env_name)
    return value

def download_file_with_retry(url, destination, chunk_size=8192, max_retries=3, timeout=30):
    """
    带重试机制的大文件下载

    参数:
        url (str): 要下载文件的URL地址
        destination (str): 文件保存的目标路径
        chunk_size (int): 每次读取的数据块大小，默认为8192字节
        max_retries (int): 最大重试次数，默认为3次

    返回值:
        bool: 下载成功返回True，失败返回False
    """
    import requests
    import time

    headers = {
        # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0'
    }

    for attempt in range(max_retries):
        try:
            # 发起GET请求，stream=True表示流式下载
            response = requests.get(url, headers=headers, stream=True, timeout=timeout)
            response.raise_for_status()  # 检查HTTP错误
            # 写入文件
            with open(destination, 'wb') as file:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # 过滤掉保持连接的空块
                        file.write(chunk)
            print("下载完成!")
            return True
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"下载失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                time.sleep(2 ** attempt)  # 指数退避
            else:
                print(f"下载失败，已达到最大重试次数: {e}")
                return False
        except Exception as e:
            print(f"下载过程中发生错误: {e}")
            return False
    return False


def is_port_available(port):
    """
    检查指定端口是否可用
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # 尝试绑定到指定端口
        sock.bind(('localhost', port))
        # 如果绑定成功，说明端口可用
        return True
    except socket.error:
        # 如果绑定失败，说明端口已被占用
        return False
    finally:
        sock.close()
def find_available_port(start_port=3306):
    """
    从指定端口开始查找可用的端口
    默认从3306端口开始检查
    """
    port = start_port
    while True:
        if is_port_available(port):
            return port
        port += 1


def get_sorted(dict_list, key):
    """
    获取按版本从高到低排序的已安装MySQL列表
    """
    from collections import OrderedDict

    def version_key(version_string):
        return [int(x) for x in version_string.split('.')]
    sorted_items = sorted(
        dict_list.items(),
        key=lambda item: version_key(item[1][key]),
        reverse=True
    )
    return OrderedDict(sorted_items)


def get_service_status(service_name):
    """
    获取指定 Windows 服务的当前状态（简化版）

    Args:
        service_name (str): Windows 服务名称

    Returns:
        dict: 包含服务状态信息的字典
    """
    if not service_name:
        return {
            'status': 'invalid',
            'status_text': '服务名称无效',
            'service_name': service_name
        }

    try:
        from jiefoundation.utils import run_command

        # 查询服务状态
        result = run_command(['sc', 'query', service_name])

        if result.returncode == 0:
            output = result.stdout.lower()
            if 'state' in output:
                if 'running' in output or '4 running' in output:
                    color, status, status_text = 'success', 'running', '运行中'
                elif 'stopped' in output or '1 stopped' in output:
                    color, status, status_text = 'danger', 'stopped', '已停止'
                elif 'paused' in output or '7 paused' in output:
                    color, status, status_text = 'warning', 'paused', '已暂停'
                elif 'start pending' in output or '2 start_pending' in output:
                    color, status, status_text = 'success', 'starting', '正在启动'
                elif 'stop pending' in output or '3 stop_pending' in output:
                    color, status, status_text = 'warning', 'stopping', '正在停止'
                else:
                    color, status, status_text = 'secondary', 'unknown', '未知状态'
            else:
                color, status, status_text = 'secondary', 'unknown', '未知状态'

            return {
                'status': status,
                'color': color,
                'status_text': status_text,
                'service_name': service_name
            }
        else:
            return {
                'status': 'not_found',
                'color': 'secondary',
                'status_text': '服务不存在',
                'service_name': service_name
            }

    except Exception as e:
        return {
            'status': 'error',
            'color': 'danger',
            'status_text': f'查询失败: {str(e)}',
            'service_name': service_name
        }


def is_valid_ini_file(file_path):
    """
    综合多种方法判断是否为有效的INI文件
    """
    # 首先检查文件是否存在
    if not os.path.exists(file_path):
        return False

    # 方法1: 尝试使用configparser解析
    try:
        config = configparser.ConfigParser()
        config.read(file_path, encoding='utf-8')
        # 如果解析成功且有内容，则认为是INI文件
        if config.sections() or config.defaults():
            return True
    except:
        pass

    # 方法2: 检查文件内容特征
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(1024)  # 只读取前1024个字符

        # 检查是否包含INI文件的典型特征
        lines = content.split('\n')[:20]  # 只检查前20行

        section_count = 0
        kv_count = 0

        for line in lines:
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                section_count += 1
            elif '=' in line and not line.startswith('#') and not line.startswith(';'):
                kv_count += 1

        # 如果有足够的节或键值对，则认为是INI文件
        return (section_count > 0) or (kv_count > 0)
    except:
        return False