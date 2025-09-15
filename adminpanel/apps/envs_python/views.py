import json
import os.path
from  django.conf import settings
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.edit import FormView
from django.contrib import messages

from panelcore.mixin import RuntimeEnvsMixin

from jiefoundation.utils import run_command
from jiefoundation.jiebase import JsonView

from .config import project_python_path
from .helper import get_package_list, get_pypi_list
from .forms import PackageInstallForm

app_name = 'envs_python'

def get_category():
    with open(settings.MENU_MAIN_JSON, 'r', encoding='utf-8') as f:
        menu_main = json.load(f)
    return menu_main['runtime_envs']['children']['envs_python']['children']['category']


class EnvsPythonMixin(RuntimeEnvsMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_menu'] = 'envs_python'
        context['category_list'] = get_category()
        return context


class PypiListView(EnvsPythonMixin, TemplateView):
    template_name = f'{app_name}/pypi_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '全局PyPi设置'
        context['pypi_list'] = get_pypi_list()
        return context


class SetPypiDefaultView(RedirectView):
    url = reverse_lazy(f'{app_name}:pypi_list')

    def get(self, request, *args, **kwargs):
        name = self.kwargs.get('name')
        get_pypi_info = get_pypi_list()[name]['url']
        result = run_command(f"{str(project_python_path)} -m pip config set global.index-url {get_pypi_info}", shell=True)
        return super().get(request, *args, **kwargs)


class PythonRunMixin:
    python_path = None
    app_namespace = None
    env_info = None

    def get_python_path(self):
        if os.path.exists(self.python_path): return self.python_path
        return None

    def get_app_namespace(self):
        return self.app_namespace

    def get_env_info(self):
        return self.env_info


class PackageListMixin(PythonRunMixin, TemplateView):
    template_name = f'{app_name}/package_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['app_namespace'] = self.get_app_namespace()
            context['packages'] = get_package_list(self.get_python_path())
            context['env_info'] = self.get_env_info()
        except Exception as e:
            messages.warning(self.request, f"显示包列表失败! </br>错误信息为：{e}")
        return context


class PackageInstallMixin(PythonRunMixin, FormView):
    template_name = f'{app_name}/package_install.html'
    form_class = PackageInstallForm

    def get_success_url(self):
        return reverse_lazy(f'{self.get_app_namespace()}:package_list', kwargs={'version': self.kwargs.get('version')})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['app_namespace'] = self.get_app_namespace()
        context['env_info'] = self.get_env_info()
        context['is_path'] = os.path.exists(self.get_python_path())
        return context

    def form_valid(self, form):
        package_name = form.cleaned_data.get('package_name')
        package_version = form.cleaned_data.get('package_version')
        python_path = self.get_python_path()

        cmd = [python_path, "-m", 'pip', 'install']
        if package_version == 'latest':
            cmd.append(package_name)
        else:
            cmd.append(f"{package_name}=={package_version}")
        result = run_command(cmd)
        if result.returncode == 0:
            return super().form_valid(form)
        else:
            err_msg  = result.stderr
            if '[notice] A new release of pip is available' in err_msg:
                err_msg = err_msg.split('[notice] A new release of pip is available')[0].replace('\n', '</br>')
            error_message = f"{result.stdout}</br>{err_msg}"
            form.add_error(None, error_message)
            return self.form_invalid(form)


class PackageSearchView(JsonView):
    def get(self, request, *args, **kwargs):
        package_name = request.GET.get('package_name')
        if package_name:
            cmd = [project_python_path, "-m", 'pip', 'index', 'versions', package_name]
            result = run_command(cmd)
            if result.returncode == 0:
                context = {'status': 'success'}
                version_option_html = '<option value="latest">自动适配最新版本</option>'
                version_str = ''
                for line in result.stdout.split('\n'):
                    if line.startswith('Available versions'):
                        version_str = line.split(':')[1].strip()
                        break
                for version in version_str.split(','):
                    version_option_html += f'<option value="{version}">{version}</option>'
                context['message'] = version_option_html
                return self.render_to_json_response(context)
            else:
                return self.render_to_json_error(message=f"没有找到 {package_name} 名称的包! </br>错误信息为：{result.stderr}")
        return self.render_to_json_error(message="参数错误")


class PackageUninstallMixin(PythonRunMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse_lazy(f'{self.get_app_namespace()}:package_list', kwargs={'version': self.kwargs.get('version')})

    def get(self, request, *args, **kwargs):
        package = request.GET.get('package')
        if package:
            cmd = [self.get_python_path(), "-m", 'pip', 'uninstall', package, '-y']
            result = run_command(cmd)
            if result.returncode == 0:
                messages.success(request, f"卸载 {package} 成功！")
            else:
                messages.warning(request, f"卸载 {package} 失败！ 错误信息为：{result.stderr}")
        return super().get(request, *args, **kwargs)


from apps.envs_python.helper import package_upgrade
class PackageUpgradeMixin(PythonRunMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse_lazy(f'{self.get_app_namespace()}:package_list', kwargs={'version': self.kwargs.get('version')})

    def get(self, request, *args, **kwargs):
        package_name = kwargs.get('package')
        if package_name:
            result = package_upgrade(self.get_python_path(), package_name)
            if result.returncode == 0:
                messages.success(self.request, f"{package_name} 升级完成！")
            else:
                messages.warning(self.request, f"升级失败！错误信息为：{result.stderr}")
        return super().get(request, *args, **kwargs)


from .forms import PackagePipExportForm
class PackagePipExportView(PythonRunMixin, FormView):
    form_class = PackagePipExportForm
    template_name = 'envs_python/package_export.html'

    def get_success_url(self):
        return reverse_lazy(f'{self.get_app_namespace()}:package_list', kwargs={'version': self.kwargs.get('version')})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['app_namespace'] = self.get_app_namespace()
        context['env_info'] = self.get_env_info()
        return context

    def form_valid(self, form):
        save_path = form.cleaned_data.get('save_path')
        python_path = self.get_python_path()
        cmd = [python_path, "-m", 'pip', 'freeze ', '>', f'{save_path}requirements.txt']