import hashlib
import ctypes

from django.urls import reverse, reverse_lazy

def url_reverse_lazy(urlconf):
    from django.urls import reverse_lazy
    if urlconf['route_name']:
        args = None
        kwargs = None
        query = None
        fragment = None
        if 'args' in urlconf:
            if urlconf['args']: args = urlconf['args']
        if 'kwargs' in urlconf:
            if urlconf['kwargs']: kwargs = urlconf['kwargs']
        if 'query' in urlconf:
            if urlconf['query']: query = urlconf['query']
        if 'fragment' in urlconf:
            if urlconf['fragment']: fragment = urlconf['fragment']
        return reverse_lazy(urlconf['route_name'], args=args, kwargs=kwargs, query=query, fragment=fragment)
    return ''

def windows_api(executable, parameters= "", operation="open", directory=None, show_cmd=1):
        """
        使用 ShellExecuteW 调用 Windows 程序或执行命令
        :param executable: 要执行的程序路径，如 "cmd.exe", "notepad.exe"
        :param parameters: 命令行参数，如 "/c echo Hello"
        :param operation: 操作类型，如 "open", "print", "runas"（管理员权限）
        :param directory: 工作目录，可为 None
        :param show_cmd: 显示方式，1=正常显示, 3=最大化, 5=恢复
        :return: 成功返回 True，失败返回 False
        """
        result = ctypes.windll.shell32.ShellExecuteW(
            None,           # 父窗口句柄
            operation,      # 操作类型
            executable,     # 程序路径
            parameters,     # 参数
            directory,      # 工作目录
            show_cmd        # 显示方式
        )
        if result <= 32:
            raise RuntimeError(f"ShellExecuteW failed with code: {result}")
        return True

def run_command(args,timeout=None, shell=False,cwd=None, env=None, encoding='utf-8'):
    """
    通用命令执行工具函数，适用于执行外部命令并处理输出和错误。
    参数:
        args (list): 要执行的命令和参数，例如 ['ls', '-l']。
        check (bool): 如果为 True，当命令返回非0状态码时抛出异常。
        timeout (float, optional): 命令执行的最大时间（秒），超时则抛出异常。
        shell (bool): 是否通过系统 shell 执行命令（注意安全风险）。
        cwd (str, optional): 设置命令执行的当前工作目录。
        env (dict, optional): 设置环境变量。
        encoding (str): 用于解码 stdout 和 stderr 的编码格式，默认为 'utf-8'。

    返回:
        返回一个 subprocess.CompletedProcess 对象
        result: returncode, stdout, stderr, args。
        返回值的属性
            args   执行的命令及其参数（字符串或列表形式）。
                示例：['ls', '-l'] 或 'echo $HOME'（如果通过 shell=True 执行）。
            returncode   子进程的退出状态码：
                0 表示命令执行成功。
                非零值表示命令执行失败（具体含义取决于命令本身）。
                示例：result.returncode
            stdout   子进程的标准输出内容（bytes 类型或字符串，取决于参数设置）。
                如果未设置 stdout=subprocess.PIPE 或 capture_output=True，则此属性为 None。
                示例：result.stdout.decode('utf-8')（需手动解码字节为字符串）。
            stderr 子进程的标准错误输出内容（与 stdout 类似）。
            示例：result.stderr
    """
    import subprocess
    return subprocess.run(
        args,
        shell=shell,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding=encoding,
        timeout=timeout
    )

def get_file_md5(file_path):
    """
    计算指定文件的MD5值
    :param file_path: 文件路径
    :return: MD5值
    """
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


def list_to_dict(from_list, key):
    """
    将列表转换为字典
    :param from_list: 列表
    :param key: 字典的键
    :return: 字典
    """
    return {item[key]: item for item in from_list}

def check_sha256(file_path, expected_sha256):
    """
    检查文件的SHA256哈希值是否与预期值匹配

    Args:
        file_path: 文件路径
        expected_sha256: 预期的SHA256哈希值

    Returns:
        bool: 如果哈希值匹配返回True，否则返回False
    """
    if not expected_sha256:
        return True

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest().lower() == expected_sha256.lower()
    except FileNotFoundError:
        return False
    except Exception:
        return False

def ensure_path_end_separator(path):
    """
    确保路径或URL以适当分隔符结尾的通用函数

    自动识别并处理:
    - 本地文件系统路径 (使用操作系统特定分隔符)
    - 网络URL路径 (使用正斜杠分隔符)

    参数:
        path (str): 输入路径或URL字符串

    返回:
        str: 以适当分隔符结尾的路径或URL字符串
    """
    import os
    from urllib.parse import urlparse

    if not isinstance(path, str):
        raise TypeError("路径必须是字符串类型")

    if not path:
        return ''

    parsed = urlparse(path)
    if parsed.scheme and parsed.scheme in ['http', 'https', 'ftp', 'ftps']:
        return path if path.endswith('/') else path + '/'
    else:
        if path.endswith('/'): return path
        return path + '/'

def remove_trailing_separator(path, keep_root_separator=True):
    """
    删除URL或路径末尾的分隔符的通用函数

    自动识别并处理:
    - 本地文件系统路径 (处理操作系统特定分隔符)
    - 网络URL路径 (处理正斜杠分隔符)

    参数:
        path (str): 输入路径或URL字符串
        keep_root_separator (bool): 是否保留根路径分隔符，如 "/" 或 "C:\\"

    返回:
        str: 删除末尾分隔符后的路径或URL字符串

    示例:
        remove_trailing_separator('/path/to/resource/') -> '/path/to/resource'
        remove_trailing_separator('https://example.com/api/') -> 'https://example.com/api'
        remove_trailing_separator('C:\\Users\\Admin\\') -> 'C:\\Users\\Admin'
        remove_trailing_separator('/') -> '/' 或 '' (取决于keep_root_separator参数)
    """
    import os
    from urllib.parse import urlparse

    if not isinstance(path, str):
        raise TypeError("路径必须是字符串类型")

    if not path:
        return '' if not keep_root_separator else os.sep

    # 判断是否为URL
    parsed = urlparse(path)
    is_url = parsed.scheme and parsed.scheme in ['http', 'https', 'ftp', 'ftps']

    if is_url:
        # 处理URL
        while path.endswith('/'):
            path = path[:-1]
            # 如果只剩协议部分，停止删除
            if path.count('/') <= 2 and '://' in path:
                break
    else:
        # 处理本地路径
        while path.endswith('/') or (os.name == 'nt' and path.endswith('/')):
            # 检查是否是根目录
            if len(path) <= 1:
                break

            # Windows驱动器根目录检查 (如 C:\)
            if os.name == 'nt' and len(path) == 3 and path[1:] == ':\\':
                break

            path = path[:-1]

            # Unix根目录检查
            if os.name != 'nt' and path == '':
                if keep_root_separator:
                    return '/'
                else:
                    return ''
                break

    # 特殊情况处理：Windows驱动器根目录
    if os.name == 'nt' and len(path) == 2 and path.endswith(':'):
        return path + '\\'

    # 特殊情况处理：根目录
    if path in ['/', '\\']:
        return path if keep_root_separator else ''

    return path


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


def move_and_rename_folder(src_folder, dest_parent, new_name=None):
    """
    移动文件夹到指定位置，并可选择性地重命名

    参数:
        src_folder (str): 源文件夹路径
        dest_parent (str): 目标父目录路径
        new_name (str, optional): 新的文件夹名称，如果为None则保持原名

    返回:
        str: 新文件夹的完整路径
    """
    import shutil
    import os
    # 检查源文件夹是否存在
    if not os.path.exists(src_folder):
        raise FileNotFoundError(f"源文件夹不存在: {src_folder}")
    # 确定新文件夹名称
    if new_name is None:
        new_name = os.path.basename(src_folder.rstrip('/\\'))
    # 构建目标路径
    dest_path = os.path.join(dest_parent, new_name)
    # 检查目标是否已存在
    if os.path.exists(dest_path):
        raise FileExistsError(f"目标路径已存在: {dest_path}")
    # 确保目标父目录存在
    os.makedirs(dest_parent, exist_ok=True)
    # 移动并重命名文件夹
    shutil.move(src_folder, dest_path)
    return dest_path


def copy_file_content_only(src_file, dest_file):
    """
    仅复制文件内容到指定位置

    参数:
        src_file (str): 源文件路径
        dest_file (str): 目标文件路径

    返回:
        str: 目标文件路径
    """
    import shutil
    try:
        shutil.copyfile(src_file, dest_file)
        return dest_file
    except Exception as e:
        raise Exception(f"复制文件失败: {e}")


def get_unique_missing_elements(sub_list, main_list):
    """
    返回在子列表中但不在主列表中的唯一元素（去重版本）

    参数:
        sub_list (list): 子列表
        main_list (list): 主列表

    返回:
        list: 不在主列表中的唯一元素（去重，保持在sub_list中首次出现的顺序）

    使用示例:
        get_unique_missing_elements([1, 2, 2, 3], [1, 2])  # 返回 [3]
        get_unique_missing_elements([1, 2, 3, 2, 4], [1])  # 返回 [2, 3, 4]
    """
    main_set = set(main_list)
    missing_elements = []
    seen = set()

    for item in sub_list:
        if item not in main_set and item not in seen:
            missing_elements.append(item)
            seen.add(item)

    return missing_elements
    
def read_file(filepath, mode='r'):
    from pathlib import Path

    if not Path(filepath): return False
    fp = None
    try:
        fp = open(filepath, mode)
        f_content = fp.read()
    except Exception as ex:
        fp = open(filepath, mode, encoding="utf-8", errors='ignore')
        f_content = fp.read()
    finally:
        if fp and not fp.closed: fp.close()
    return f_content


def write_file(filename, content, mode='w+'):
    try:
        fp = open(filename, mode)
        fp.write(content)
        fp.close()
        return True
    except:
        try:
            fp = open(filename, mode, encoding="utf-8")
            fp.write(content)
            fp.close()
            return True
        except:
            return False


def make_dir(dir_path):
    try:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    except:
        return False
    
