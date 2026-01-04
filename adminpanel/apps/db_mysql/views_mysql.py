import json
import os
import shutil
import time
import configparser
import uuid
import psutil

from django.contrib import messages
from django.views.generic.list import ListView
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect
from django.views.generic.base import ContextMixin

from jiefoundation.jiebase import JsonView
from jiefoundation.utils import run_command, read_file, write_file
from jiefoundation.utils import windows_api_blocking, windows_api

from .views import MysqlMixin
from .mysqlconn import MysqlConnectionManager

from .helper import get_installed
from .forms import MysqlLoginForm

app_name = 'db_mysql'
this_app_name = 'mysql_manage'


class MysqlInfoMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mysql_id'] = self.kwargs.get('id', '')
        context['mysql_info'] = get_installed(context['mysql_id'])
        return context

class MysqlLoginView(MysqlMixin, MysqlInfoMixin, FormView):
    template_name = f'{app_name}/mysql_login.html'
    form_class = MysqlLoginForm

    def get_success_url(self):
        return reverse_lazy(f'{app_name}:{this_app_name}:db_list', kwargs={'id': self.kwargs.get('id', '')})

    def get_initial(self):
        mysql_info = get_installed(self.kwargs.get('id',''))
        if mysql_info:
            return {
                'host': '127.0.0.1',
                'port': mysql_info.get('port', '3306'),
                'username': 'root'
            }
        return super().get_initial()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '登录MySQL'
        context['breadcrumb'] = [
            {
                'title': 'MySQL服务',
                'href': reverse_lazy(f'{app_name}:index'),
                'active': False
            },
            {
                'title': '登录MySQL',
                'href': '',
                'active': True
            },
        ]
        return context

    def form_valid(self, form):
        user = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        port = form.cleaned_data.get('port')

        self.request.session['host'] = '127.0.0.1'
        self.request.session['user'] = user
        self.request.session['password'] = password
        self.request.session['port'] = port
        try:
            db = MysqlConnectionManager(self.request)
            db.test_connection()
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, str(e))
            return super().form_invalid(form)


class DbListView(MysqlMixin, MysqlInfoMixin, TemplateView):
    template_name = f'{app_name}/mysql_db_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '数据库列表'
        context['breadcrumb'] = [
            {
                'title': 'MySQL服务',
                'href': reverse_lazy(f'{app_name}:index'),
                'active': False
            },
            {
                'title': '数据库列表',
                'href': '',
                'active': True
            },
        ]
        db = MysqlConnectionManager(self.request)
        context['object_list'] = db.get_all_databases()
        return  context


from .forms import MysqlDatabaseForm
class DbCreateView(MysqlMixin, MysqlInfoMixin, FormView):
    template_name = f'{app_name}/mysql_db_form.html'
    form_class = MysqlDatabaseForm

    def get_success_url(self):
        return reverse_lazy(f'{app_name}:{this_app_name}:db_list', kwargs={'id': self.kwargs.get('id')})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # mysql = MysqlConnectionManager(self.request)
        # default_set = mysql.get_charset_settings()
        # initial['character_set'] = default_set['server_charset']
        initial['character_set'] = 'utf8mb4'
        initial['collation'] = 'utf8mb4_0900_ai_ci'
        return initial.copy()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '创建数据库'
        context['breadcrumb'] = [
            {
                'title': 'MySQL服务',
                'href': reverse_lazy(f'{app_name}:index'),
                'active': False
            },
            {
                'title': '数据库列表',
                'href': reverse_lazy(f'{app_name}:{this_app_name}:db_list', kwargs={'id': self.kwargs.get('id')}),
                'active': False
            },
            {
                'title': '创建数据库',
                'href': '',
                'active': True
            }
        ]
        return  context

    def form_valid(self, form):
        database_name = form.cleaned_data.get('database_name')
        # character_set = form.cleaned_data.get('character_set')
        character_set = 'utf8mb4'
        collation = form.cleaned_data.get('collation')
        try:
            db = MysqlConnectionManager(self.request)
            db.execute_query(f'CREATE SCHEMA `{database_name}` DEFAULT CHARACTER SET {character_set} COLLATE {collation}')
            messages.success(self.request, f'数据库 {database_name} 创建成功')
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f'创建失败，错误详情：{str(e)}')
            return super().form_invalid(form)


class DbDeleteView(MysqlMixin, MysqlInfoMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse_lazy(f'{app_name}:{this_app_name}:db_list', kwargs={'id': self.kwargs.get('id')})

    def get(self, request, *args, **kwargs):
        try:
            db_name = self.request.GET.get('db_name')
            db = MysqlConnectionManager(request)
            db.execute_query(f'DROP SCHEMA `{db_name}`')
            messages.success(request, f'数据库 {db_name} 删除成功')
            return super().get(request, *args, **kwargs)
        except Exception as e:
            messages.error(request, f'删除失败，错误详情：{str(e)}')
            self.url = reverse_lazy(f'{app_name}:{this_app_name}:db_list', kwargs={'id': self.kwargs.get('id')})
            return super().get(request, *args, **kwargs)


class DbEditView(MysqlMixin, MysqlInfoMixin, FormView):
    template_name = f'{app_name}/mysql_db_form.html'
    form_class = MysqlDatabaseForm

    def get_success_url(self):
        return reverse_lazy(f'{app_name}:{this_app_name}:db_list', kwargs={'id': self.kwargs.get('id')})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        mysql = MysqlConnectionManager(self.request)
        db_name = self.kwargs.get('db_name')
        db_info = mysql.get_database_charset_collation(db_name)
        initial['database_name'] = db_name
        initial['character_set'] = 'utf8mb4'
        initial['collation'] = db_info['collation']
        return initial.copy()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '修改数据库'
        context['breadcrumb'] = [
            {
                'title': 'MySQL服务',
                'href': reverse_lazy(f'{app_name}:index'),
                'active': False
            },
            {
                'title': '数据库列表',
                'href': reverse_lazy(f'{app_name}:{this_app_name}:db_list', kwargs={'id': self.kwargs.get('id')}),
                'active': False
            },
            {
                'title': '修改数据库',
            }
        ]
        return context

    def form_valid(self, form):
        db_name = form.cleaned_data.get('database_name')
        character_set = 'utf8mb4'
        # character_set = form.cleaned_data.get('character_set')
        collation = form.cleaned_data.get('collation')
        try:
            db = MysqlConnectionManager(self.request)
            db.execute_query(f'ALTER SCHEMA `{db_name}` CHARACTER SET {character_set} COLLATE {collation}')
            messages.success(self.request, f'数据库 {db_name} 修改成功')
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f'修改失败，错误详情：{str(e)}')
            return super().form_invalid(form)