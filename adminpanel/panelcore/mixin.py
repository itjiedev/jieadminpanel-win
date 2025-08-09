from django.views.generic.base import ContextMixin


# class ProjectDeployMixin(ContextMixin):
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['parent_menu'] = 'project_deploy'
#         return context

# class DatabasesMixin(ContextMixin):
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['parent_menu'] = 'databases'
#         return context

class RuntimeEnvsMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parent_menu'] = 'runtime_envs'
        return context
