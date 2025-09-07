import configparser
import os
import winreg
import json
import requests
import shutil

from django.contrib import messages
from django.views.generic import FormView
from pathlib import Path
from django.urls import reverse, reverse_lazy
from django.views.generic.base import TemplateView, RedirectView

from jiefoundation.utils import (
    run_command, get_file_md5, WindowsAPI, set_reg_user_env,
    get_reg_user_env, ensure_path_separator
)
from jiefoundation.jiebase import JsonView
from apps.envs_python.helper import get_default_env_python
from apps.envs_python.views import EnvsPythonMixin

from .config import (
    installed_file_path, python_download_path,
    python_cache_dir,py_ini_path
)
from .helper import get_installed as get_installed_python
from .helper import get_python_versions, python_list_paths
from .forms import PythonInstallForm, PythonUninstallForm

app_name = 'envs_python_installer'


class PythonInstallerMixin(EnvsPythonMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "安装包环境"
        context['current_category'] = app_name
        return context


class PythonListView(PythonInstallerMixin, TemplateView):
    template_name = f'{app_name}/python_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pythons'] = python_list_paths()
        with open(installed_file_path, 'w', encoding='utf-8') as f:
            json.dump(context['pythons'], f, ensure_ascii=False, indent=4)
        context['default_python'] = get_default_env_python()
        return context


class SetPyDefaultView(PythonInstallerMixin, RedirectView):
    url = reverse_lazy(f'{app_name}:python_list')

    def get(self, request, *args, **kwargs):
        get_version = kwargs.get('version')
        version = get_version.split('.')
        if version:
            config = configparser.ConfigParser()
            config['defaults'] = {'python': f'{version[0]}.{version[1]}'}
            local_app_data = os.environ.get('LOCALAPPDATA')
            config_path = os.path.join(local_app_data, 'py.ini')
            with open(config_path, 'w') as configfile:
                config.write(configfile)
            installed_path = {}

            with open(installed_file_path, 'r', encoding='utf-8') as f:
                installed_path = json.load(f)
                for key, value in installed_path.items():
                    if key != get_version:
                        installed_path[key]['is_py_default'] = False
                    else:
                        installed_path[key]['is_py_default'] = True

            with open(installed_file_path, 'w', encoding='utf-8') as f:
                json.dump(installed_path, f, ensure_ascii=False, indent=4)

        return super().get(request, *args, **kwargs)


class SetEnvironDefaultView(PythonInstallerMixin, RedirectView):
    url = reverse_lazy(f"{app_name}:python_list")

    def get(self, request, *args, **kwargs):
        version = kwargs.get('version')
        if version:
            user_path_list = get_reg_user_env("PATH").split(';')
            for path_value in user_path_list[:]:
                path_value = path_value.strip()
                if path_value:
                    if os.path.exists(os.path.join(path_value, 'python.exe')) or os.path.exists(os.path.join(path_value, 'pip.exe')):
                        user_path_list.remove(path_value)
                else:
                    user_path_list.remove('')

            with open(installed_file_path, 'r', encoding='utf-8') as f:
                installed_path = json.load(f)

            installed_dir = installed_path[version]['path'].rstrip('\\python.exe')
            user_path_list.insert(0, installed_dir)
            user_path_list.insert(0, os.path.join(installed_dir, 'Scripts'))

            set_reg_user_env("PATH", ";".join(user_path_list))

        return super().get(request, *args, **kwargs)


class PythonUninstallView(PythonInstallerMixin, FormView):
    template_name = f'{app_name}/python_uninstall.html'
    form_class = PythonUninstallForm
    success_url = reverse_lazy(f"{app_name}:python_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] += ' - 卸载'
        context['version'] = self.kwargs.get('version')
        context['breadcrumb'] = [
            {'title': 'Python列表', 'href': reverse_lazy(f'{app_name}:python_list'), 'active': False},
            {
                'title': 'Python卸载',
                'href': reverse_lazy(f'{app_name}:uninstall', kwargs={'version': self.kwargs.get('version')}),
                'active': True
            },
        ]
        return context

    def form_valid(self, form):
        version = self.kwargs.get('version')
        rm_folder = form.cleaned_data.get('rm_folder')
        accept = form.cleaned_data.get('accept')

        if accept:
            with open(installed_file_path, 'r', encoding='utf-8') as f:
                install_versions = json.load(f)
            if install_versions[version]:
                installed_info = install_versions[version]
                # version_info = get_python_versions(version)
                install_file_name = f'python-{version}-amd64.exe'
                cache_file_path = python_cache_dir / install_file_name
                installed_dir = installed_info['path'].replace('python.exe', '')

                if not cache_file_path.exists():
                    version_list = version.split('.')
                    key_value = ''
                    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, f'Installer\\Dependencies\\CPython-{version_list[0]}.{version_list[1]}') as key:
                        key_value, _ = winreg.QueryValueEx(key, '')
                        if key_value:
                            system_cache_file = Path(
                                os.environ.get('LOCALAPPDATA')) / 'Package Cache' / key_value / install_file_name
                            if system_cache_file.exists():
                                cache_file_path = system_cache_file
                try:
                    result = run_command([str(cache_file_path), '/uninstall', '/passive', '/simple'])
                    if result['returncode'] == 0:
                        # 删除安装目录
                        if rm_folder:
                            if os.path.exists(installed_dir): shutil.rmtree(installed_dir)
                        # 删除安装信息
                        with open(installed_file_path, 'r', encoding='utf-8') as f:
                            installed_path = json.load(f)
                            installed_path.pop(version)
                        with open(installed_file_path, 'w', encoding='utf-8') as f:
                            json.dump(installed_path, f, ensure_ascii=False, indent=4)
                        # 如果是py默认，重置默认
                        if installed_info['is_py_default']:
                            if os.path.exists(py_ini_path): os.remove(py_ini_path)
                        # 如果是环境变量默认，重置默认
                        # if installed_info['is_default']:
                        #     reg_user_env = get_reg_user_env("PATH").split(";")
                        #     for path in reg_user_env:
                        #         if reg_user_env.startswith(installed_dir):
                        #             reg_user_env.remove(path)
                        #     set_reg_user_env("PATH", ';'.joing(reg_user_env))

                except WindowsError as e:
                    raise e
        return super().form_valid(form)


class PythonInstallView(PythonInstallerMixin, FormView):
    template_name = f'{app_name}/python_install.html'
    initial = {"folder": os.path.join(os.environ.get('LOCALAPPDATA'), 'Programs', 'Python')}
    form_class = PythonInstallForm
    success_url = reverse_lazy(f'{app_name}:python_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] += " - 安装"
        context['breadcrumb'] = [
            {
                'title': 'Python环境管理',
                'href': reverse_lazy(f'{app_name}:python_list'),
                'active': False
            },
            {
                'title': '安装',
                'href': reverse_lazy(f'{app_name}:python_install'),
                'active': True
            }
        ]
        context['get_user_folder'] = os.path.join(os.environ.get('LOCALAPPDATA'), 'Programs', 'Python').replace('\\',
                                                                                                               '\\\\')
        context['get_system_folder'] = os.path.join(os.environ.get('ProgramFiles'), 'Python').replace('\\', '\\\\')
        return context


class PythonDownloadView(JsonView):

    def post(self, request, *args, **kwargs):
        download_id = request.POST.get('download_source')
        version = request.POST.get('version')

        get_versions = get_python_versions(version)
        download_source = "https://www.python.org/ftp/python/"

        with open(python_download_path, 'r', encoding='utf-8') as f:
            download_sources_list = json.load(f)
            for source in download_sources_list:
                if source['id'] == download_id:
                    download_source = source['url-prefix']

        download_url = f'{download_source}/{version}/{get_versions["installer-file-name"]}'
        if download_id == 'aliyun':
            download_url = f'{download_source}/{get_versions["installer-file-name"]}'

        python_cache_file = python_cache_dir / get_versions['installer-file-name']
        if not python_cache_file.exists():
            try:
                with requests.get(download_url, stream=True) as r:
                    r.raise_for_status()
                    with open(python_cache_file, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk: f.write(chunk)
            except requests.exceptions.RequestException as e:
                return self.render_to_json_error("存在下载地址错误或者网络问题~")

        check_file_md5 = get_file_md5(python_cache_file)
        if check_file_md5 != get_versions['md5sum']:
            with requests.get(download_url, stream=True) as r:
                r.raise_for_status()
                with open(python_cache_file, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):  # 分块读取文件
                        if chunk: f.write(chunk)
            check_file_md5 = get_file_md5(python_cache_file)
            if check_file_md5 != get_versions['md5sum']:
                return self.render_to_json_error('文件校验失败！请手动下载后放置在_cache目录中安装！')
        return self.render_to_json_response({'message': '下载完成~'})


class RunPythonInstallView(JsonView):

    def post(self, request, *args, **kwargs):
        folder = request.POST.get('folder')
        version = request.POST.get('version')
        version_info = get_python_versions(version)
        install_folder = os.path.join(folder, f'Python{version_info["version_major"]}{version_info["version_minor"]}')
        python_cache_file = python_cache_dir / version_info['installer-file-name']

        try:
            WindowsAPI.execute(
                executable=str(python_cache_file),
                parameters=f'/passive InstallAllUsers=1 TargetDir="{install_folder}"',
                operation="runas",
            )
            return self.render_to_json_response({'status':'success', 'message': '安装成功~'})
        except Exception as e:
            return self.render_to_json_error(str(e))

class ClearCacheView(RedirectView):
    url = reverse_lazy(f'{app_name}:python_list')
    def get(self, request, *args, **kwargs):
        shutil.rmtree(python_cache_dir)
        python_cache_dir.mkdir(exist_ok=True)
        messages.success(request, '下载缓存清理完成~')
        return super().get(request, *args, **kwargs)

class ResetDefaultView(RedirectView):
    url = reverse_lazy(f'{app_name}:python_list')

    def get(self, request, *args, **kwargs):
        name = self.kwargs.get('name')
        if os.path.exists(py_ini_path):
            os.remove(py_ini_path)

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
        return super().get(request, *args, **kwargs)


from apps.envs_python.views import PackageListMixin
class PackageListView(PythonInstallerMixin, PackageListMixin):
    app_namespace = app_name

    def get_python_path(self):
        version = self.kwargs.get('version')
        return ensure_path_separator(get_installed_python(version)['path']) + 'python.exe'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Python包管理'
        context['breadcrumb'] = [
            {
                'title': 'Python环境管理',
                'href': reverse_lazy(f'{app_name}:python_list'),
                'active': False
            },
            {
                'title': 'Python包列表',
                'href': reverse_lazy(f'{app_name}:package_list', kwargs={'version': self.kwargs.get('version')}),
                'active': True
            }
        ]
        return context


from apps.envs_python.views import PackageInstallMixin
class PackageInstallView(PythonInstallerMixin, PackageInstallMixin):
    app_namespace = app_name

    def get_python_path(self):
        version = self.kwargs.get('version')
        return ensure_path_separator(get_installed_python(version)['path']) + 'python.exe'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Python包安装'
        context['breadcrumb'] = [
            {
                'title': 'Python环境管理',
                'href': reverse_lazy(f'{app_name}:python_list'),
                'active': False
            },
            {
                'title': 'Python包列表',
                'href': reverse_lazy(f'{app_name}:package_list', kwargs={'version': self.kwargs.get('version')}),
                'active': False
            },
            {
                'title': 'Python包安装',
                'href': reverse_lazy(f'{app_name}:package_install', kwargs={'version': self.kwargs.get('version')}),
                'active': True
            }
        ]
        context['version'] = self.kwargs.get('version')
        return context


from apps.envs_python.views import PackageUninstallMixin
class PackageUninstallView(PackageUninstallMixin):
    app_namespace = app_name

    def get_python_path(self):
        version = self.kwargs.get('version')
        return ensure_path_separator(get_installed_python(version)['path']) + 'python.exe'


from apps.envs_python.views import PackageUpgradeMixin
class PackageUpgradeView(PackageUpgradeMixin):
    app_namespace = app_name

    def get_python_path(self):
        version = self.kwargs.get('version')
        return ensure_path_separator(get_installed_python(version)['path']) + 'python.exe'
