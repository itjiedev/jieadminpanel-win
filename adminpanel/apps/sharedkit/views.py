import psutil
import os
from datetime import datetime
import win32api
import win32file
import win32con

from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.edit import FormView
from jiefoundation.jiebase import JsonView
from jiefoundation.utils import WindowsAPI

def open_system_properties(request):
    try:
        WindowsAPI.execute('rundll32.exe', 'shell32.dll,Control_RunDLL sysdm.cpl')
    except Exception as e:
        messages.error(request, f'Error opening system properties: {str(e)}')
    return


def open_system_services(request):
    try:
        WindowsAPI.execute('mmc.exe', 'services.msc')
    except Exception as e:
        messages.error(request, f'Error opening system services: {str(e)}')
    return

def open_system_cmd(request):
    import ctypes
    try:
        WindowsAPI.execute(executable='cmd.exe', directory='c:', operation='runas')
    except Exception as e:
        messages.error(request, f'Error opening system cmd: {str(e)}')
    return


def get_disk_partitions_info():
    partitions = psutil.disk_partitions()
    result = []

    for partition in partitions:
        try:
            drive = partition.device
            drive_letter = drive[0]  # 提取盘符字母（如 C）
            volume_name = win32api.GetVolumeInformation(drive)[0]  # 卷标
            total_bytes = win32file.GetDiskFreeSpaceEx(drive)[1]  # 总容量
            free_bytes = win32file.GetDiskFreeSpaceEx(drive)[0]  # 可用空间
            used_bytes = total_bytes - free_bytes

            result.append({
                'device': partition.device,
                'drive_letter': drive_letter,
                'mountpoint': partition.mountpoint,  # 挂载路径
                'fstype': partition.fstype,  # 文件系统类型
                'volume_name': volume_name,  # 卷标名称
                'total': total_bytes,
                'used': used_bytes,
                'free': free_bytes,
                'percent_used': (used_bytes / total_bytes) * 100 if total_bytes else 0
            })
        except Exception as e:
            continue
    return result

def is_hidden(path):
    """
    判断指定路径的文件或文件夹是否具有隐藏属性（Windows）
    """
    try:
        attrs = win32file.GetFileAttributes(path)
        return (attrs & win32con.FILE_ATTRIBUTE_HIDDEN) != 0
    except Exception as e:
        print(f"无法访问路径 {path}: {e}")
        return False


class PickerFileDirView(TemplateView):
    template_name = 'sharedkit/picker_file_dir.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['picker_type'] = self.kwargs.get('picker_type')
        context['page_title'] = '选择文件/文件夹'
        get_path = self.request.GET.get('path', '')
        context['path'] = get_path
        context['disk_partitions'] = []
        context['dirs'] = []
        context['files'] = []
        if get_path == '':
            context['disk_partitions'] = get_disk_partitions_info()
        context['parent_path'] = os.path.dirname(get_path)
        context['path_breadcrumb'] = []
        if get_path != '':
            if os.path.ismount(get_path):
                context['path_breadcrumb'] = [{'name': get_path.replace('\\', ''), 'path': get_path}]
            else:
                path_list = get_path.split('\\')

                for i, folder in enumerate(path_list):
                    join_path = (os.path.sep).join(path_list[:i+1])
                    join_path = join_path + os.path.sep
                    context['path_breadcrumb'].append({'name': folder, 'path': join_path})

        context['error'] = ''
        if get_path and os.path.isdir(get_path):
            try:
                all_items = os.listdir(get_path)
                dirs = []
                files = []
                for item in all_items:
                    full_path = os.path.join(get_path, item)
                    if is_hidden(full_path):
                        continue
                    stat = os.stat(full_path)
                    item_info = {
                        'name': item,
                        'path': full_path,
                        'size': stat.st_size if os.path.isfile(full_path) else 0,
                        'mtime': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'is_dir': os.path.isdir(full_path),
                        'is_file': os.path.isfile(full_path),
                    }
                    if item_info['is_dir']:
                        dirs.append(item_info)
                    else:
                        files.append(item_info)
                context['dirs'] = dirs
                context['files'] = files

            except PermissionError:
                context['error'] = "权限不足，无法访问该目录"
            except Exception as e:
                context['error'] = f"读取目录失败：{str(e)}"
        return context


class OpenInExplorerView(JsonView):
    def get(self, request, *args, **kwargs):
        path = request.GET.get('path', '')
        if not os.path.exists(path):
            return self.render_to_json_error('目录不存在')
        try:
            os.startfile(path)
            return self.render_to_json_response({'message': '已打开目录'})
        except PermissionError:
            return self.render_to_json_error('权限不足，无法打开目录')


class CreateDirView(JsonView):
    def post(self, request, *args, **kwargs):
        folder_name = request.POST.get('folder_name', '')
        currentPath = request.POST.get('currentPath', '')
        new_dir_path = os.path.join(currentPath, folder_name)

        if os.path.exists(new_dir_path):
            return self.render_to_json_error('目录已存在')
        try:
            os.makedirs(new_dir_path, exist_ok=True)
            return self.render_to_json_response({'message': f'目录创建成功{currentPath}'})
        except PermissionError:
            return self.render_to_json_error('权限不足，无法创建目录')
        except Exception as e:
            return self.render_to_json_error(f'创建目录失败：{str(e)} ')