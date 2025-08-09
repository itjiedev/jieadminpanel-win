import json
from  django.conf import settings
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView, RedirectView
from panelcore.mixin import RuntimeEnvsMixin

from jiefoundation.utils import run_command

from .config import project_python_path
from .helper import get_pypi_list



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
    template_name = 'envs_python/pypi_list.html'

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
        result = run_command(f"{str(project_python_path)} -m pip config set global.index-url {get_pypi_info}")
        return super().get(request, *args, **kwargs)