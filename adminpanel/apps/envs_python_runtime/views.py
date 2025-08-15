import json,os
import shutil
from pathlib import Path

from django.contrib import messages
from django.views.generic.edit import FormView
from django.views.generic.base import TemplateView, RedirectView
from django.urls import reverse_lazy

from jiefoundation.jiebase import JsonView
from jiefoundation.utils import (
    check_sha256, download_file_with_retry,get_reg_user_env,run_command,
    set_reg_user_env, ensure_path_separator
)

from apps.envs_python.views import EnvsPythonMixin
from apps.envs_python.helper import get_default_env_python
from .config import cache_dir, user_installed_json,app_data_dir, create_type
from .helper import (
    update_version_info, get_versions, get_installed, get_user_config,get_downloadsite, user_config_json
)
from .forms import InstallConfigForm, UninstallForm, ImportForm


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
        context['page_title'] = 'Runtime安装管理'
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
                'title': 'Runtime环境管理',
                'href': reverse_lazy(f'{app_name}:config_check'),
                'active': False
            },
            {
                'title': '安装配置',
                'href': reverse_lazy(f'{app_name}:config'),
                'active': True
            }
        ]
        return  context

    def get_initial(self):
        inited = super().get_initial()
        get_config = get_user_config()
        if get_config:
            inited['install_folder'] = get_config['install_folder']
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
        context['installed'] = list(get_installed().keys())
        context['versions'] = get_versions()
        context['default_env_python'] = get_default_env_python()
        context['breadcrumb'] = [
            {
                'title': 'Runtime环境管理',
                'href': reverse_lazy(f'{app_name}:config_check'),
                'active': False
            },
            {
                'title': '可安装版本列表',
                'href': reverse_lazy(f'{app_name}:versions_list'),
                'active': True
            }
        ]
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
    def get(self, request, *args, **kwargs):
        version = request.GET.get('version')
        version_info = get_versions(version)
        user_config = get_user_config()
        install_file_path = cache_dir / version_info['file_name']
        download_url = version_info['url']

        if (download_url.startswith('https://www.python.org/ftp/python/') and
                get_user_config('install_source')['id'] != 'python'):
            download_url = download_url.replace(
                'https://www.python.org/ftp/python/', ensure_path_separator(get_user_config('install_source')['url-prefix'])
            )
        sha256 = version_info['sha256']
        if not install_file_path.exists():
            download = download_file_with_retry(download_url, install_file_path)
            if not download: return self.render_to_json_error('下载失败~请刷新页面重新尝试！')
        if user_config['check_file']:
            if sha256:
                if not check_sha256(install_file_path, sha256):
                    return self.render_to_json_error('下载文件sha256校验失败~请换地址或者清理缓存后再重试！')
        return self.render_to_json_success('下载成功')


class InstallView(JsonView):
    """
    安装python
    """
    def get(self, request, *args, **kwargs):
        version = request.GET.get('version')
        version_info = get_versions(version)
        install_file_path = cache_dir / version_info['file_name']
        user_config = get_user_config()
        install_folder = Path(user_config['install_folder'])
        sha256 = version_info['sha256']

        if not install_file_path.exists():
            return self.render_to_json_error('请先下载安装包！')
        if user_config['check_file']:
            if sha256:
                if not check_sha256(install_file_path, version_info['sha256']):
                    return self.render_to_json_error('安装时sha256校验失败！')
        try:
            extract_path = install_folder / version
            if extract_path.exists():
                return self.render_to_json_error('该版本已存在！')
            from .urls import app_name
            from jiefoundation.utils import extract_from_zip, move_and_rename_folder

            result = False
            if Path(install_file_path).suffix.lower() == '.zip':
                result = extract_from_zip(install_file_path, extract_to=extract_path)
            if Path(install_file_path).suffix.lower() == '.nupkg':
                version_tmp_path = cache_dir / version
                result = extract_from_zip(install_file_path, extract_to=version_tmp_path )
                if result:
                    move_and_rename_folder(version_tmp_path / 'tools', install_folder, new_name=version)
                    shutil.rmtree(version_tmp_path)
            if result:
                # 配置运行 get-pip.py
                from jiefoundation.utils import run_command, copy_file_content_only

                version_split = version_info['sort_version'].split('.')
                version_major = int(version_split[0])
                version_minor = int(version_split[1])
                get_pip_file = app_data_dir / 'get-pip' / 'get-pip.py'
                if version_minor == 3 and version_major <= 8:
                    get_pip_file = app_data_dir / 'get-pip' / f'get-pip-{version_major}.{version_minor}.py'
                python_interpreter = install_folder / version / 'python.exe'
                result = run_command(
                    [python_interpreter, get_pip_file, '--no-warn-script-location'],
                    shell=True, cwd=install_folder / version
                )
                installed_python = {}
                with open(user_installed_json, 'r', encoding='utf-8') as f:
                    installed_python = json.load(f)
                installed_python[version] = {
                    'version': version,
                    'folder': ensure_path_separator(str(extract_path)),
                    'create_type': 'install',
                    'create_type_title': create_type['install'],
                    'version_major': int(version_split[0]),
                    'version_minor': int(version_split[1]),
                    'version_patch': int(version_split[2]),
                }
                with open(user_installed_json, 'w', encoding='utf-8') as f:
                    json.dump(installed_python, f, ensure_ascii=False, indent=4)
            return self.render_to_json_success('解压成功~')
        except Exception as e:
            return self.render_to_json_error(f'解压失败: {str(e)}')


class SetDefaultView(RedirectView):
    url = reverse_lazy(f'{app_name}:python_list')

    def get(self, request, *args, **kwargs):
        version = kwargs.get('version')
        installed_info = get_installed(version)
        get_user_env = get_reg_user_env('PATH').split(';')
        for item in get_user_env[:]:
            if os.path.exists(os.path.join(item, 'python.exe')) or os.path.exists(os.path.join(item, 'pip.exe')):
                get_user_env.remove(item)

        get_user_env.insert(0, str(os.path.join(installed_info['folder'], 'Scripts')))
        get_user_env.insert(0, installed_info['folder'])
        set_reg_user_env('PATH', ';'.join(get_user_env))

        return super().get(request, *args, **kwargs)


class UninstallView(PythonRuntimeMixin, FormView):
    form_class = UninstallForm
    template_name = f'{app_name}/uninstall.html'
    success_url = reverse_lazy(f'{app_name}:python_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '卸载Python'
        return  context
    
    def form_valid(self, form):
        version = self.kwargs.get('version')
        installed_info = get_installed(version)
        # 删除环境变量
        get_user_env = get_reg_user_env('PATH').split(';')
        for item in get_user_env[:]:
            if item.startswith(installed_info['folder']) or item.startswith(os.path.join(installed_info['folder'], 'Scripts')):
                get_user_env.remove(item)
        set_reg_user_env('PATH', ';'.join(get_user_env))
        # 删除安装信息
        with open(user_installed_json, 'r', encoding='utf-8') as f:
            installed_python = json.load(f)
        del installed_python[version]
        with open(user_installed_json, 'w', encoding='utf-8') as f:
            json.dump(installed_python, f, ensure_ascii=False, indent=4)
        # 删除安装目录
        shutil.rmtree(installed_info['folder'])

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

        # with open(user_installed_json, 'r', encoding='utf-8') as f:
        #     installed_python = json.load(f)
        #     for k, v in installed_python.items():
        #         installed_python[k]['default'] = False
        # with open(user_installed_json, 'w', encoding='utf-8') as f:
        #     json.dump(installed_python, f, ensure_ascii=False, indent=4)

        return super().get(request, *args, **kwargs)
    

class ImportView(PythonRuntimeMixin, FormView):
    form_class = ImportForm
    template_name = f'{app_name}/import.html'
    success_url = reverse_lazy(f'{app_name}:python_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '导入Python环境'
        return  context

    def form_valid(self, form):
        import_dir = form.cleaned_data.get('import_dir')
        if import_dir and os.path.exists(import_dir):
            import_python_file = os.path.join(import_dir, 'python.exe')
            if os.path.exists(import_python_file):
                import_version = run_command([import_python_file, '-V'])['stdout'].split(maxsplit=1)[1].strip()
                import_version_list = import_version.split('.')
                import_name = f'Python-{import_version}'
                installed_list = get_installed()
                if import_name not in installed_list:
                    installed_list[import_name] = {
                        'version': import_name,
                        'folder': ensure_path_separator(import_dir),
                        'create_type': 'import',
                        'create_type_title': create_type['import'],
                        'version_major': int(import_version_list[0]),
                        'version_minor': int(import_version_list[1]),
                        'version_patch': int(import_version_list[2]),
                    }
                    with open(user_installed_json, 'w', encoding='utf-8') as f:
                        json.dump(installed_list, f, ensure_ascii=False, indent=4)
                else:
                    form.add_error('import_dir', '存在已安装信息记录！请检查是否选择错误~')
                    return super().form_invalid(form)
            else:
                form.add_error('import_dir', '所选择的目录没有 python.exe 解释器文件~')
                return super().form_invalid(form)
        return super().form_valid(form)


from apps.envs_python.views import PackageListMixin
class PackageListView(PythonRuntimeMixin, PackageListMixin):
    app_namespace = app_name

    def get_python_path(self):
        python_version_info = get_installed()[self.kwargs.get('version')]
        return f'{ensure_path_separator(python_version_info["folder"])}Python.exe'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Python包管理'
        context['breadcrumb'] = [
            {
                'title': 'Runtime 环境管理',
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
class PackageInstallView(PythonRuntimeMixin, PackageInstallMixin):
    app_namespace = app_name

    def get_python_path(self):
        installed_info = get_installed(self.kwargs.get('version'))
        print(installed_info)
        return ensure_path_separator(installed_info['folder']) + 'python.exe'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Python包安装'
        context['breadcrumb'] = [
            {
                'title': 'Runtime 环境管理',
                'href': reverse_lazy(f'{app_name}:python_list'),
                'active': False
            },
            {
                'title': '包列表',
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
        installed_info = get_installed(version)
        return ensure_path_separator(str(installed_info['folder'])) + 'python.exe'


from apps.envs_python.views import PackageUpgradeMixin
class PackageUpgradeView(PackageUpgradeMixin):
    app_namespace = app_name

    def get_python_path(self):
        version = self.kwargs.get('version')
        return ensure_path_separator(get_installed(version)['folder']) + 'python.exe'
