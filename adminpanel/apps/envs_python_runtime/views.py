import json,os
import shutil
from pathlib import Path
import uuid

from django.contrib import messages
from django.views.generic.edit import FormView
from django.views.generic.base import  TemplateView, RedirectView
from django.urls import reverse_lazy

from jiefoundation.jiebase import JsonView
from jiefoundation.utils import check_sha256, run_command, ensure_path_end_separator
from panelcore.helper import (
    download_file_with_retry,get_reg_user_env, set_reg_user_env,
)

from apps.envs_python.views import EnvsPythonMixin
from apps.envs_python.helper import get_default_env_python
from .config import cache_dir, user_installed_json,app_data_dir, create_type
from .helper import (
    update_version_info, get_versions, get_installed, get_user_config,get_downloadsite, user_config_json
)
from .forms import InstallConfigForm, UninstallForm, ImportForm, PythonForm


app_name = 'envs_python_runtime'

class PythonRuntimeMixin(EnvsPythonMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_category'] = app_name
        return context

class CheckConfigView(RedirectView):
    """检查是否有配置，如果没有配置，跳转到配置页面"""
    def get(self, request, *args, **kwargs):
        user_config = get_user_config()
        if user_config:
            self.url = reverse_lazy(f'{app_name}:python_list')
        else:
            self.url = reverse_lazy(f'{app_name}:config')
        return super().get(request, *args, **kwargs)


class PythonListView(PythonRuntimeMixin, TemplateView):
    """ 已安装的python列表"""
    template_name = f'{app_name}/python_list.html'

    def get_context_data(self, **kwargs):
        from .helper import get_installed_sorted
        context = super().get_context_data(**kwargs)
        context['page_title'] = '压缩包安装管理'
        context['python_list'] = get_installed_sorted()
        context['default_env_python'] = get_default_env_python()
        return context


class InstallConfigView(PythonRuntimeMixin, FormView):
    """ 设置安装配置 """
    form_class = InstallConfigForm
    template_name = f'{app_name}/install_config.html'
    success_url = reverse_lazy(f'{app_name}:config')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '安装配置'
        context['breadcrumb'] = [
            {
                'title': '压缩包安装管理',
                'href': reverse_lazy(f'{app_name}:config_check'),
                'active': False
            },
            {
                'title': '安装配置',
                'href': reverse_lazy(f'{app_name}:config'),
                'active': True
            }
        ]
        user_config = get_user_config()
        context['install_folder'] = ''
        if user_config:
            context['install_folder'] = get_user_config()['install_folder'].replace('\\', '/')
        return  context

    def get_initial(self):
        inited = super().get_initial()
        get_config = get_user_config()
        if get_config:
            inited['install_folder'] = get_config['install_folder'].replace('\\', '/')
            inited['install_source'] = get_config['install_source']['id']
            inited['check_file'] = get_config['check_file']
        return inited.copy()

    def form_valid(self, form):
        install_folder = form.cleaned_data['install_folder']
        install_source = form.cleaned_data['install_source']
        check_file = form.cleaned_data['check_file']
        config = {
            'install_folder': install_folder,
            'install_source': get_downloadsite(install_source),
            'check_file': check_file
        }
        with open(user_config_json, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        messages.success(self.request, "配置已保存")
        return super().form_valid(form)


class VersionsListView(PythonRuntimeMixin, TemplateView):
    """可安装版本列表"""
    template_name = f'{app_name}/versions_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '可安装版本列表'
        context['installed'] = [item['version'] for item in get_installed().values()]
        context['versions'] = get_versions()
        context['default_env_python'] = get_default_env_python()
        context['breadcrumb'] = [
            {
                'title': '压缩包安装管理',
                'href': reverse_lazy(f'{app_name}:config_check'),
                'active': False
            },
            {
                'title': '可安装版本列表',
                'href': reverse_lazy(f'{app_name}:versions_list'),
                'active': True
            }
        ]
        context['download_url_prefix'] = get_user_config()['install_source']['url-prefix']
        return context


class VersionsRefreshView(RedirectView):
    """
    版本刷新视图类

    该类继承自RedirectView，用于处理版本信息的刷新请求，
    在处理GET请求时会先更新版本信息，然后重定向到版本列表页面。
    """
    url = reverse_lazy(f'{app_name}:versions_list')
    def get(self, request, *args, **kwargs):
        update_version_info()
        messages.success(request, '版本信息已重新下载！')
        return super().get(request, *args, **kwargs)


class ClearCacheView(RedirectView):
    """
    清理缓存
    """
    url = reverse_lazy(f'{app_name}:python_list')

    def get(self, request, *args, **kwargs):
        try:
            shutil.rmtree(cache_dir, ignore_errors=True)
            cache_dir.mkdir(exist_ok=True)
            messages.success(request, '清理缓存完成！')
        except Exception as e:
            messages.error(request, f'清理缓存失败！{e}')
        return super().get(request, *args, **kwargs)


class DownloadView(JsonView):
    """
    下载安装压缩包
    """
    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        version = request.POST.get('version')
        version_info = get_versions(version)
        user_config = get_user_config()
        install_file_path = cache_dir / version_info['file_name']
        download_url = version_info['url']

        if (download_url.startswith('https://www.python.org/ftp/python/') and
                get_user_config('install_source')['id'] != 'python'):
            download_url = download_url.replace(
                'https://www.python.org/ftp/python/', ensure_path_end_separator(get_user_config('install_source')['url-prefix'])
            )
        sha256 = version_info['sha256']
        if not install_file_path.exists():
            download = download_file_with_retry(download_url, install_file_path)
            if not download: return self.render_to_json_error('下载失败~请刷新重试、更换下载源或者选择较低的的版本安装！')
        if user_config['check_file']:
            if sha256:
                if not check_sha256(install_file_path, sha256):
                    return self.render_to_json_error('下载文件sha256校验失败~请换地址或者清理缓存后再重试！')
        return self.render_to_json_success('下载成功')


class PythonInstallView(PythonRuntimeMixin, FormView):
    """
    Python安装表单
    """
    form_class = PythonForm
    template_name = f'{app_name}/python_install.html'
    success_url = reverse_lazy(f'{app_name}:python_list')

    def get_initial(self):
        initial = super().get_initial()
        version = self.kwargs.get('version')
        initial['version'] = self.kwargs.get('version')
        install_config = get_user_config()

        folder_name = version
        if os.path.exists(os.path.join(install_config['install_folder'], folder_name)):
            import string
            import random
            chars = string.ascii_lowercase + string.digits
            random_suffix = ''.join(random.choices(chars, k=3))
            folder_name = f"{version}_{random_suffix}"

        initial['folder'] = os.path.join(install_config['install_folder'], folder_name).replace("/", "\\")
        return initial.copy()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '安装Python'
        context['versions'] = get_versions()
        context['default_env_python'] = get_default_env_python()
        context['breadcrumb'] = [
            {
                'title': '压缩包安装管理',
                'href': reverse_lazy(f'{app_name}:config_check'),
                'active': False
            },
            {
                'title': 'Python版本列表',
                'href': reverse_lazy(f'{app_name}:versions_list'),
                'active': False
            },
            {
                'title': '安装Python',
                'href': reverse_lazy(f'{app_name}:python_install'),
                'active': True
            }
        ]
        return context


class InstallView(JsonView):
    """
    安装python
    """
    def post(self, request, *args, **kwargs):
        name = request.POST.get('name').strip()
        version = request.POST.get('version')
        folder = request.POST.get('folder').replace("\\", "/")
        if not name:  name = version

        version_info = get_versions(version)
        install_file_path = cache_dir / version_info['file_name']
        user_config = get_user_config()
        install_folder = Path(folder)
        sha256 = version_info['sha256']

        if not install_file_path.exists():
            return self.render_to_json_error('请先下载安装包！')
        if user_config['check_file']:
            if sha256:
                if not check_sha256(install_file_path, version_info['sha256']):
                    return self.render_to_json_error('安装时sha256校验失败！')
        # try:
        extract_path = install_folder
        if extract_path.exists():
            return self.render_to_json_error('该版本已存在！')

        from jiefoundation.utils import extract_from_zip, move_and_rename_folder

        print('解压，请稍候....')
        result = False
        if Path(install_file_path).suffix.lower() == '.zip':
            result = extract_from_zip(install_file_path, extract_to=folder)
        if Path(install_file_path).suffix.lower() == '.nupkg':
            install_dir =os.path.dirname(folder)
            folder_name = folder.split('/')[-1]
            version_tmp_path = cache_dir / folder_name

            if version_tmp_path.exists():
                shutil.rmtree(version_tmp_path)
            result = extract_from_zip(install_file_path, extract_to=version_tmp_path )
            if result:
                move_and_rename_folder(version_tmp_path / 'tools', install_dir, new_name=folder_name)
                shutil.rmtree(version_tmp_path)

        if result:
            version_split = version_info['sort_version'].split('.')
            version_major = int(version_split[0])
            version_minor = int(version_split[1])
            get_pip_file = app_data_dir / 'get-pip' / 'get-pip.py'
            if version_minor == 3 and version_major <= 8:
                get_pip_file = app_data_dir / 'get-pip' / f'get-pip-{version_major}.{version_minor}.py'
            print('开始安装pip')
            python_interpreter = Path(folder) / 'python.exe'
            result = run_command(
                [python_interpreter, get_pip_file, '--no-warn-script-location'],
                cwd=folder
            )
            if result.returncode != 0:
                print('选中源安装pip失败，尝试使用官方源安装pip')
                result = run_command(
                    [python_interpreter, get_pip_file, '--no-warn-script-location', '-i', 'https://pypi.org/simple'],
                    cwd=folder
                )
                if result.returncode != 0:
                    messages.warning(self.request, f'安装 pip 失败！请在包管理里尝试重新安装或者升级！错误信息：{result.stderr}~')
            installed_python = {}
            with open(user_installed_json, 'r', encoding='utf-8') as f:
                installed_python = json.load(f)
            unique_identifier = str(uuid.uuid4())
            installed_python[unique_identifier] = {
                'name': name,
                'version': version,
                'folder': ensure_path_end_separator(str(extract_path).replace('\\', '/')),
                'create_type': 'install',
                'create_type_title': create_type['install'],
                'version_major': int(version_split[0]),
                'version_minor': int(version_split[1]),
                'version_patch': int(version_split[2]),
            }
            with open(user_installed_json, 'w', encoding='utf-8') as f:
                json.dump(installed_python, f, ensure_ascii=False, indent=4)
        return self.render_to_json_success('安装成功~')
        # except Exception as e:
        #     return self.render_to_json_error(f'解压失败: {str(e)}')


class NameEditView(PythonRuntimeMixin, FormView):
    form_class = PythonForm
    template_name = f'{app_name}/update_name.html'
    success_url = reverse_lazy(f'{app_name}:python_list')

    def get_initial(self):
        initial = super().get_initial()
        unique_identifier = self.kwargs.get('uuid')
        installed_python = get_installed(unique_identifier)
        if installed_python:
            if 'name' in installed_python:
                initial['name'] = installed_python['name']
            else:
                initial['name'] = installed_python['version']
            initial['folder'] = installed_python['folder'].replace('/', '\\')
            initial['version'] = installed_python['version']
        return initial.copy()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '修改环境信息'
        context['breadcrumb'] = [
            {
                'title': '压缩包安装管理',
                'href': reverse_lazy(f'{app_name}:config_check'),
                'active': False
            },
            {
                'title': '修改环境信息',
                'href': '',
                'active': True
            }
        ]
        return context

    def form_valid(self, form):
        unique_identifier = self.kwargs.get('uuid')
        name = form.cleaned_data.get('name')
        installed_dict = get_installed()
        if unique_identifier in installed_dict:
            installed_dict[unique_identifier]['name'] = name
            with open(user_installed_json, 'w', encoding='utf-8') as f:
                json.dump(installed_dict, f, ensure_ascii=False, indent=4)
            messages.success(self.request, '环境标题修改成功~')
        else:
            form.add_error('name', '没有找到需要修改的环境~')
            return super().form_invalid(form)
        return super().form_valid(form)


class SetDefaultView(RedirectView):
    url = reverse_lazy(f'{app_name}:python_list')

    def get(self, request, *args, **kwargs):
        version = kwargs.get('version')
        installed_info = get_installed(version)
        get_user_env = get_reg_user_env('PATH').split(';')
        for item in get_user_env[:]:
            if os.path.exists(os.path.join(item, 'python.exe')) or os.path.exists(os.path.join(item, 'pip.exe')):
                get_user_env.remove(item)
        install_folder = installed_info['folder'].rstrip('/').replace('/', '\\')

        get_user_env.insert(0, str(os.path.join(install_folder, 'Scripts')))
        get_user_env.insert(0, install_folder)
        set_reg_user_env('PATH', ';'.join(get_user_env))
        return super().get(request, *args, **kwargs)


class UninstallView(PythonRuntimeMixin, FormView):
    form_class = UninstallForm
    template_name = f'{app_name}/uninstall.html'
    success_url = reverse_lazy(f'{app_name}:python_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '卸载Python'
        context['breadcrumb'] = [
            {
                'title': '压缩包安装管理',
                'href': reverse_lazy(f'{app_name}:config_check'),
                'active': False
            },
            {
                'title': '卸载Python',
                'href': '',
                'active': True
            }
        ]
        context['installed_info'] = get_installed(self.kwargs.get('version'))
        return  context
    
    def form_valid(self, form):
        version = self.kwargs.get('version')
        installed_info = get_installed(version)

        if os.path.exists(installed_info['folder']):
            # 删除安装目录
            shutil.rmtree(installed_info['folder'])
        else:
            if 'name' in installed_info:
                name = installed_info['name']
            else:
                name = installed_info['version']
            messages.warning(
                self.request, f'{name} 安装目录{installed_info['folder']}不存在~仅删除安装信息~'
            )
        # 删除环境变量
        get_user_env = get_reg_user_env('PATH').split(';')
        installed_folder = installed_info['folder'].replace('/', '\\')
        for item in get_user_env[:]:
            if item.startswith(installed_folder):
                get_user_env.remove(item)
        set_reg_user_env('PATH', ';'.join(get_user_env))
        # 删除安装信息
        with open(user_installed_json, 'r', encoding='utf-8') as f:
            installed_python = json.load(f)
        del installed_python[version]
        with open(user_installed_json, 'w', encoding='utf-8') as f:
            json.dump(installed_python, f, ensure_ascii=False, indent=4)

        return super().form_valid(form)


class ResetDefaultView(RedirectView):
    url = reverse_lazy(f'{app_name}:python_list')

    def get(self, request, *args, **kwargs):
        user_path_list = get_reg_user_env("PATH").split(';')
        for path_value in user_path_list[:]:
            path_value = path_value.strip()
            if path_value:
                if os.path.exists(os.path.join(path_value, 'python.exe')) or os.path.exists(
                        os.path.join(path_value, 'pip.exe')):
                    user_path_list.remove(path_value)
            else:
                user_path_list.remove('')
        set_reg_user_env("PATH", ";".join(user_path_list))
        messages.success(self.request, '环境变量重置完成~')
        return super().get(request, *args, **kwargs)
    

class ImportView(PythonRuntimeMixin, FormView):
    form_class = ImportForm
    template_name = f'{app_name}/import.html'
    success_url = reverse_lazy(f'{app_name}:python_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '导入Python环境'
        context['startpath'] = get_user_config('install_folder').replace("\\", '\\\\')
        return  context

    def form_valid(self, form):
        import_dir = form.cleaned_data.get('import_dir')
        if import_dir and os.path.exists(import_dir):
            import_python_file = os.path.join(import_dir, 'python.exe')
            if os.path.exists(import_python_file):
                version_str = ''
                result = run_command([import_python_file, '-V'])
                if result.stdout:version_str = result.stdout
                if result.stderr:version_str = result.stderr
                import_version = version_str.split(maxsplit=1)[1].strip()
                
                import_version_list = import_version.split('.')
                import_name = f'Python-{import_version}'
                installed_dict = get_installed()
                folder_list = [item['folder'] for item in installed_dict.values()]

                if ensure_path_end_separator(import_dir) not in folder_list:
                    unique_identifier = str(uuid.uuid4())
                    installed_dict[unique_identifier] = {
                        'name': import_name,
                        'version': import_name,
                        'folder': ensure_path_end_separator(import_dir),
                        'create_type': 'import',
                        'create_type_title': create_type['import'],
                        'version_major': int(import_version_list[0]),
                        'version_minor': int(import_version_list[1]),
                        'version_patch': int(import_version_list[2]),
                    }
                    with open(user_installed_json, 'w', encoding='utf-8') as f:
                        json.dump(installed_dict, f, ensure_ascii=False, indent=4)
                else:
                    form.add_error('import_dir', '存在已安装路径记录！请检查是否选择错误~')
                    return super().form_invalid(form)
            else:
                form.add_error('import_dir', '所选择的目录没有 python.exe 解释器文件~')
                return super().form_invalid(form)
        return super().form_valid(form)


from apps.envs_python.views import PackageListMixin
class PackageListView(PythonRuntimeMixin, PackageListMixin):
    app_namespace = app_name
    template_name = f'{app_name}/package_list.html'

    def get_python_path(self):
        python_version_info = get_installed(self.request.GET.get('uid'))
        return f'{ensure_path_end_separator(python_version_info["folder"])}Python.exe'

    def get_env_info(self):
        return get_installed(self.request.GET.get('uid'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Python包管理'
        context['breadcrumb'] = [
            {
                'title': '压缩包安装管理',
                'href': reverse_lazy(f'{app_name}:python_list'),
                'active': False
            },
            {
                'title': 'Python包列表',
                'href': reverse_lazy(f'{app_name}:package_list', kwargs={'version': self.kwargs.get('version')}),
                'active': True
            }
        ]
        context['uid'] = self.request.GET.get('uid')
        return context


from apps.envs_python.views import PackageInstallMixin
class PackageInstallView(PythonRuntimeMixin, PackageInstallMixin):
    app_namespace = app_name
    template_name = f'{app_name}/package_install.html'

    def get_python_path(self):
        installed_info = get_installed(self.request.GET.get('uid'))
        return ensure_path_end_separator(installed_info['folder']) + 'python.exe'

    def get_env_info(self):
        return get_installed(self.request.GET.get('uid'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Python包安装'
        context['uid'] = self.request.GET.get('uid')
        context['breadcrumb'] = [
            {
                'title': '压缩包安装管理',
                'href': reverse_lazy(f'{app_name}:python_list'),
                'active': False
            },
            {
                'title': '包列表',
                'href': reverse_lazy(f'{app_name}:package_list', query={'uid':context['uid']}),
                'active': False
            },
            {
                'title': 'Python包安装',
                'href': reverse_lazy(f'{app_name}:package_install', query={'uid': context['uid']}),
                'active': True
            }
        ]
        return context


from apps.envs_python.views import PackageUninstallMixin
class PackageUninstallView(PackageUninstallMixin):
    app_namespace = app_name

    def get_python_path(self):
        installed_info = get_installed(self.request.GET.get('uid'))
        return ensure_path_end_separator(str(installed_info['folder'])) + 'python.exe'


from apps.envs_python.views import PackageUpgradeMixin
class PackageUpgradeView(PackageUpgradeMixin):
    app_namespace = app_name

    def get_python_path(self):
        return ensure_path_end_separator(get_installed(self.request.GET.get('uid'))['folder']) + 'python.exe'


class PythonDeleteView(RedirectView):
    """
    根据传入的path路径删除Python配置，不会删除实际环境
    """
    url = reverse_lazy(f'{app_name}:python_list')

    def get(self, request, *args, **kwargs):
        uuid_name = request.GET.get('uuid')
        installed_dict = get_installed()
        if uuid_name in installed_dict:
            if 'name' in installed_dict[uuid_name]:
                name = installed_dict[uuid_name]['name']
            else:
                name = installed_dict[uuid_name]['version']

            del installed_dict[uuid_name]

            with open(user_installed_json, 'w', encoding='utf-8') as f:
                json.dump(installed_dict, f, ensure_ascii=False, indent=4)
            messages.success(request, f'{name}删除成功')
        else:
            messages.error(request, '删除失败~没有找到要删除的记录~')
        return super().get(request, *args, **kwargs)


class  RunPythonComponentView(JsonView):
    def get(self, request, *args, **kwargs):
        component = self.kwargs.get('component')
        uuid = self.kwargs.get('uuid')
        installed_dict = get_installed(uuid)
        if component == 'idle':
            print(f'启动 {installed_dict["folder"]}中的 IDEL 编辑器')
            runcmd = f'"{installed_dict["folder"]}python.exe" "{installed_dict["folder"]}/Lib/idlelib/idle.pyw"'
        if component == 'python':
            print(f'启动 {installed_dict["folder"]}中的 Python 交互式环境')
            runcmd = f'start cmd /c "{installed_dict["folder"]}python.exe"'
        result = run_command(runcmd, shell=True)
        return self.render_to_json_success('打开完成')
