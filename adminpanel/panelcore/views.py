import locale
from django.views.generic.base import ContextMixin, TemplateView


class HomeMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parent_menu'] = 'systeminfo'
        return context

def get_system_info():
    import subprocess
    encoding = locale.getpreferredencoding()
    result = subprocess.run(
        ['systeminfo'],
        capture_output=True,
        text=True,
        encoding=encoding,
        errors='replace'
    )
    # 解析输出为字典
    info = {}
    for line in result.stdout.splitlines():
        if ':' in line:
            # 处理多行值的情况（如网络适配器）
            if line.startswith(' '):
                if last_key:
                    info[last_key] += "</br>" + line.strip()
            else:
                parts = line.split(':', 1)
                key = parts[0].strip()
                value = parts[1].strip()
                info[key] = value
                last_key = key
    return info

class HomeView(HomeMixin, TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['page_title'] = '系统信息'
        context['system_info'] = dict(list(get_system_info().items())[:27])
        return context
