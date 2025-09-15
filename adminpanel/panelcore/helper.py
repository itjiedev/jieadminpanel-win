import winreg

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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
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


def extract_from_zip(zip_path, extract_items=None, extract_to=None, overwrite=True):
    """
    从ZIP压缩包中解压指定的文件或文件夹

    参数:
        zip_path (str): ZIP压缩包的路径
        extract_items (str or list, optional): 要解压的文件或文件夹名称，
            可以是单个字符串或字符串列表。如果为None，则解压所有内容
        extract_to (str, optional): 解压目标目录，默认为当前目录
        overwrite (bool): 是否覆盖已存在的文件，默认为True

    返回:
        list: 成功解压的文件列表

    异常:
        FileNotFoundError: 当ZIP文件不存在时抛出
        zipfile.BadZipFile: 当ZIP文件损坏时抛出

    # 使用示例
    # 解压整个ZIP文件
    extract_from_zip('example.zip')

    # 解压ZIP中的特定文件
    extract_from_zip('example.zip', extract_items='config.txt')

    # 解压ZIP中的特定文件夹
    extract_from_zip('example.zip', extract_items=['src/', 'docs/'])

    # 解压到指定目录
    extract_from_zip('example.zip', extract_items=['src/main.py'], extract_to='./extracted')

    # 解压多个指定文件和文件夹
    extract_from_zip('example.zip', extract_items=['README.md', 'src/', 'tests/'])

    """
    import os
    import zipfile
    # 检查ZIP文件是否存在
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"ZIP文件不存在: {zip_path}")
    # 设置默认解压目录
    if extract_to is None:
        extract_to = os.getcwd()
    # 确保解压目录存在
    os.makedirs(extract_to, exist_ok=True)
    # 标准化extract_items为列表
    if extract_items is None:
        extract_items = []
    elif isinstance(extract_items, str):
        extract_items = [extract_items]
    extracted_files = []

    # 打开ZIP文件
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # 获取ZIP文件中的所有文件列表
        all_files = zip_ref.namelist()
        # 确定需要解压的文件列表
        if not extract_items:
            # 如果没有指定特定文件，则解压所有文件
            files_to_extract = all_files
        else:
            # 筛选出需要解压的文件
            files_to_extract = []
            for item in extract_items:
                matched = False
                for file_name in all_files:
                    # 精确匹配文件名
                    if file_name == item:
                        files_to_extract.append(file_name)
                        matched = True
                    # 匹配文件夹（以指定名称开头且后面跟着分隔符）
                    elif file_name.startswith(item.rstrip('/') + '/'):
                        files_to_extract.append(file_name)
                        matched = True
                    # 匹配文件夹内所有文件（处理不同操作系统分隔符）
                    elif item.endswith('/') and file_name.startswith(item):
                        files_to_extract.append(file_name)
                        matched = True
                if not matched:
                    print(f"警告: 在ZIP中未找到 '{item}'")

        # 解压选定的文件
        for file_name in files_to_extract:
            try:
                target_path = os.path.join(extract_to, file_name)
                # 检查是否需要覆盖已存在的文件
                if not overwrite and os.path.exists(target_path):
                    print(f"跳过已存在的文件: {target_path}")
                    continue
                # 创建目标目录（如果需要）
                target_dir = os.path.dirname(target_path)
                if target_dir:
                    os.makedirs(target_dir, exist_ok=True)
                # 解压单个文件
                with zip_ref.open(file_name) as source, open(target_path, 'wb') as target:
                    while True:
                        chunk = source.read(8192)
                        if not chunk:
                            break
                        target.write(chunk)

                extracted_files.append(file_name)
                print(f"已解压: {file_name}")

            except Exception as e:
                print(f"解压文件 '{file_name}' 时出错: {e}")
    return True
