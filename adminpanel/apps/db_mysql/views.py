import json
import os
import shutil
import time
import configparser
import uuid
import psutil

from django.contrib import messages
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect

from jiefoundation.jiebase import JsonView
from jiefoundation.utils import run_command, read_file, write_file
from jiefoundation.utils import windows_api_blocking, windows_api

from panelcore.mixin import DatabaseMixin
from panelcore.helper import find_available_port, get_sorted
from .helper import get_installed, get_config, get_version, parse_mysql_version
from .config import app_name, version_file, config_file_path, app_cache_dir, installed_file_path
from .forms import ConfigForm, InitializeForm, UserPasswordForm, ConfigEditForm, ImportForm, ImportServiceForm


class MysqlMixin(DatabaseMixin):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_menu'] = app_name
        return context


class CheckConfigView(MysqlMixin, RedirectView):
    def get(self, request, *args, **kwargs):
        config = get_config()
        if not config['install_folder']:
            self.url = reverse_lazy(f'{app_name}:config')
        else:
            self.url = reverse_lazy(f'{app_name}:index')
        return super().get(request, *args, **kwargs)


class ConfigView(MysqlMixin, FormView):
    form_class = ConfigForm
    template_name = f'{app_name}/config.html'
    success_url = reverse_lazy(f'{app_name}:index')

    def get_initial(self):
        initial = super().initial
        initial['install_folder'] = get_config()['install_folder']
        return initial.copy()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '配置MySQL安装路径'
        return context

    def form_valid(self, form):
        config = get_config()
        config['install_folder'] = form.cleaned_data['install_folder']
        with open(config_file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        messages.success(self.request, '配置保存成功~')
        return redirect(reverse_lazy(f'{app_name}:index'))


class SoftwareView(MysqlMixin, TemplateView):
    template_name = f'{app_name}/software.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'MySQL管理软件'
        context['breadcrumb'] = [
            {
                'title': 'MySQL服务',
                'href': reverse_lazy(f'{app_name}:index'),
                'active': False
            },
            {
                'title': 'MySQL管理软件',
                'href': reverse_lazy(f'{app_name}:software'),
                'active': True
            },
        ]
        from .config import software_file
        with open(software_file, 'r', encoding='utf-8') as f:
            context['software_list'] = json.load(f)
        return context


class IndexView(MysqlMixin, TemplateView):
    template_name = f'{app_name}/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'MySQL服务'
        context['installed_list'] = get_installed()
        return context


class VersionListView(MysqlMixin, TemplateView):
    template_name = f'{app_name}/version_list.html'

    def get_version_list(self):
        with open(version_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'MySQL安装-选择版本'
        context['versions'] = self.get_version_list()
        context['breadcrumb'] = [
            {
                'title': 'MySQL服务',
                'href': reverse_lazy(f'{app_name}:index'),
                'active': False
            },
            {
                'title': 'MySQL安装-选择版本',
                'href': reverse_lazy(f'{app_name}:version_list'),
                'active': True
            },
        ]
        context['installed_version'] = [item.get('version') for item in get_installed().values()]
        return context


class VersionsRefreshView(RedirectView):
    url = reverse_lazy('db_mysql:version_list')

    def get(self, request, *args, **kwargs):
        """
        使用 requests 获取 MySQL 官方归档页面的版本列表
        """
        import requests
        import re

        urls = [
            ("https://dev.mysql.com/downloads/mysql/", True, '最新版'),
             ("https://downloads.mysql.com/archives/community/", False, '历史版本'),
        ]
        versions = {}
        success_flag = True
        for url in urls:
            response = requests.get(url[0], timeout=10)
            response.raise_for_status()

            select_pattern = r'<select[^>]*id="version"[^>]*>(.*?)</select>'
            select_match = re.search(select_pattern, response.text, re.DOTALL)
            if select_match:
                try:
                    select_content = select_match.group(1)
                    option_pattern = r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)</option>'
                    options = re.findall(option_pattern, select_content)
                    for value, text in options:
                        if (
                                value.strip()
                                and value.strip() != ''
                                and text.strip() not in ['Select Version', '']
                                and 'a' not in value
                                and 'rc' not in text
                                and 'dmr' not in text
                                and 'b' not in value
                                and 'm' not in text
                                and (value.startswith('8.') or value.startswith('9.') or value.startswith('5.7.'))
                        ):
                            version = text.strip().split(' ')[0]
                            version_list = version.split('.')
                            download_url = f'https://cdn.mysql.com/archives/mysql-{version_list[0]}.{version_list[1]}/mysql-{version}-winx64.zip'
                            # download_url = f'https://downloads.mysql.com/archives/get/p/23/file/mysql-{version}-winx64.zip'
                            if url[1]:
                                download_url = f'https://cdn.mysql.com//Downloads/MySQL-{version_list[0]}.{version_list[1]}/mysql-{version}-winx64.zip'
                                # download_url = f'https://dev.mysql.com/get/Downloads/MySQL-{value}/mysql-{version}-winx64.zip'

                            versions[version] = {
                                'version': version,
                                'name': f"MySQL {text.strip()}",
                                'is_new': url[1],
                                'download_url': download_url,
                                'filename': f"mysql-{version}-winx64.zip",
                            }
                except Exception as e:
                    success_flag = False
                    messages.error(request, f'获取 MySQL {url[2]}列表失败~错误信息：{e}')
            else:
                success_flag = False
                messages.error(request, f'分析获取 MySQL {url[2]}失败! ')

        if success_flag:
            def version_key(version_string):
                return [int(x) for x in version_string.split('.')]
            versions = dict(sorted(versions.items(), key=lambda item: version_key(item[0]), reverse=True))
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(versions, f, ensure_ascii=False, indent=4)
            messages.success(request, '获取 MySQL 列表操作完成~')

        return super().get(request, *args, **kwargs)


class ImportView(MysqlMixin, FormView):
    template_name = f'{app_name}/import.html'
    form_class = ImportForm
    success_url = reverse_lazy(f'{app_name}:index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '导入MySQL'
        context['startpath'] = get_config().get('install_folder')
        context['btn_read_txt'] = '读取配置'
        context['breadcrumb'] = [
            {
                'title': 'MySQL服务',
                'href': reverse_lazy(f'{app_name}:index'),
                'active': False
            },
            {
                'title': 'MySQL导入-选择配置文件',
                'href': reverse_lazy(f'{app_name}:import'),
                'active': False
            },
            {
                'title': 'MySQL导入-分析',
                'href': reverse_lazy(f'{app_name}:import'),
                'active': True
            },
        ]
        return context

    def form_valid(self, form):
        config_file = form.cleaned_data.get('config_file')

        if os.path.isdir(config_file):
            form.add_error('config_file', '所输入的配置文件不能是目录!')
            return super().form_invalid(form)
        if not os.path.exists(config_file):
            form.add_error('config_file', '所输入的配置文件不存在!')
            return super().form_invalid(form)
        if os.path.splitext(config_file)[1] != '.ini':
            form.add_error('config_file', '所输入的配置文件格式有误!')
            return super().form_invalid(form)
        from panelcore.helper import is_valid_ini_file
        if not is_valid_ini_file(config_file):
            form.add_error('config_file', '所输入的配置文件格式有误!')
            return super().form_invalid(form)
        installed_dict = get_installed()
        if config_file in [installed_dict[key]['conf_file'] for key in installed_dict]:
            form.add_error('config_file', '选中的配置文件在安装记录中已存在，不能重复导入~')
            return super().form_invalid(form)

        version = form.cleaned_data.get('version')
        install_dir = form.cleaned_data.get('install_dir')
        data_dir = form.cleaned_data.get('data_dir')
        port = form.cleaned_data.get('port')

        version_info = get_version(version)
        if version_info:
            name = version_info['name']
        else:
            name = f"MySQL {version}"

        unique_id = str(uuid.uuid4())
        with open(installed_file_path, 'r', encoding='utf-8') as f:
            installed = json.load(f)
        installed[unique_id] = {
            'uuid': unique_id,
            'version': version,
            'name': name,
            'title': name,
            'install_dir': install_dir,
            'set_root_password': 2,
            'config_status': 2,
            "data_dir": data_dir,
            "conf_file": config_file,
            "port": port,
            "set_service": False,
            "service_name": '',
            "service_auto": "",
        }
        installed = get_sorted(installed, 'version')

        with open(installed_file_path, 'w', encoding='utf-8') as f:
            json.dump(installed, f, ensure_ascii=False, indent=4)

        return super().form_valid(form)
        # if os.path.isdir(config_file):
        #     form.add_error('config_file', '所输入的配置文件不能是目录!')
        #     return super().form_invalid(form)
        # if not os.path.exists(config_file):
        #     form.add_error('config_file', '所输入的配置文件不存在!')
        #     return super().form_invalid(form)
        # if os.path.splitext(config_file)[1] != '.ini':
        #     form.add_error('config_file', '所输入的配置文件格式有误!')
        #     return super().form_invalid(form)
        # from panelcore.helper import is_valid_ini_file
        # if not is_valid_ini_file(config_file):
        #     form.add_error('config_file', '所输入的配置文件格式有误!')
        #     return super().form_invalid(form)
        # 
        # config = configparser.ConfigParser()
        # config.read(config_file, encoding='utf-8')
        # basedir = config.get('mysqld', 'basedir')
        # 
        # if not os.path.exists(basedir):
        #     form.add_error('config_file', '所输入的配置文件所对应的安装目录不存在!')
        #     return super().form_invalid(form)
        # 
        # mysql_exe = f"{basedir}/bin/mysql.exe"
        # version = ''
        # try:
        #     result = run_command([mysql_exe, '--version'])
        #     if result.returncode == 0: version = parse_mysql_version(result.stdout)
        # except:
        #     form.add_error('config_file', '无法获取MySQL版本!')
        #     return super().form_invalid(form)
        # 
        # installed_dict = get_installed()
        # if config_file in [installed_dict[key]['conf_file'] for key in installed_dict]:
        #     form.add_error('config_file', '选中的配置文件在安装记录中已存在，不能重复生成~')
        #     return super().form_invalid(form)
        # 
        # data_dir = config.get('mysqld', 'datadir')
        # port = config.get('mysqld', 'port')
        # 
        # new_form = self.get_form()
        # new_form.initial = {
        #     'config_file': config_file,
        #     'version': version,
        #     'install_dir': basedir,
        #     'data_dir': data_dir,
        #     'port': port,
        # }
        # context = self.get_context_data(form=new_form)
        # context['submitted'] = True
        # context['btn_read_txt'] = '重新读取'
        # # context['version'] = version
        # # context['basedir'] = basedir
        # # context['datadir'] = data_dir
        # # context['port'] = port
        # # context['set_service'] = set_service
        # # context['have_service_info'] = have_service_info
        # 
        # return self.render_to_response(context)


class AnalyzeConfigView(JsonView):
    csrf_exempt = True

    def post(self, request, *args, **kwargs):
        config_file = self.request.POST.get('config_file')

        if os.path.isdir(config_file):
            return self.render_to_json_error('所输入的配置文件不能是目录!')
        if not os.path.exists(config_file):
            return self.render_to_json_error('所输入的配置文件不存在!')
        from panelcore.helper import is_valid_ini_file
        if not is_valid_ini_file(config_file):
            return self.render_to_json_error('所输入的配置文件格式有误!')
        if os.path.splitext(config_file)[1] != '.ini':
            return self.render_to_json_error('所输入的配置文件格式有误!')
        installed_dict = get_installed()
        if config_file in [installed_dict[key]['conf_file'] for key in installed_dict]:
            return self.render_to_json_error('选中的配置文件在安装记录中已存在，不能重复导入~')

        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')
        basedir = config.get('mysqld', 'basedir')
        mysql_exe = f"{basedir}/bin/mysql.exe"
        if not os.path.exists(mysql_exe):
            return self.render_to_json_error('所选择的MySQL安装目录里没有运行文件!请检查安装目录是否完整~')
        version = ''
        try:
            result = run_command([mysql_exe, '--version'])
            if result.returncode == 0:
                version = parse_mysql_version(result.stdout)
        except Exception:
            pass
        if not version:
            return self.render_to_json_error('无法获取MySQL版本!')

        return_dict = {
            'version': version,
            'install_dir': basedir,
            'datadir': config.get('mysqld', 'datadir'),
            'port': config.get('mysqld', 'port'),
        }
        #
        # import psutil
        # exists_service_list_html = '<div class="radio-item">'
        # for service in psutil.win_service_iter():
        #     try:
        #         service_info = service.as_dict()
        #         binpath = service_info.get('binpath', '')
        #         if config_file in binpath :
        #             return_dict['have_servie'] = True
        #             return_dict['service_info'][service_info.get('name')] = {
        #                 'name': service_info.get('name'),
        #                 'display_name': service_info.get('display_name'),
        #                 'start_type': service_info.get('start_type'),
        #                 'status': service_info.get('status'),
        #                 'description': service_info.get('description'),
        #                 'binpath': service_info.get('binpath'),
        #             }
        #             exists_service_list_html += f'<input type="radio" id="id_service_name" name="service_name" value="{service_info.get("name")}" />{service_info.get("display_name")}'
        #             break
        #     except Exception as e:
        #         continue
        # return_dict['exists_service_list_html'] = exists_service_list_html + '</div>'
        return self.render_to_json_success(return_dict)


class DownloadView(JsonView):

    def get(self, request, *args, **kwargs):
        version_info = get_version(request.GET.get('version'))
        download_url = version_info['download_url']
        filename = version_info['filename']
        local_file_path = os.path.join(app_cache_dir, filename)

        import requests
        if not os.path.exists(local_file_path):
            try:
                print('开始下载..')
                response = requests.get(download_url, stream=True)
                response.raise_for_status()
                os.makedirs(app_cache_dir, exist_ok=True)
                with open(local_file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print('下载完成...')
                return self.render_to_json_success(filename)
            except Exception as e:
                return self.render_to_json_error(f'文件下载失败: {e}')
        else:
            return self.render_to_json_success(f'文件{filename}已存在,跳过下载。')


class UnzipView(JsonView):

    def get(self, request, *args, **kwargs):
        version = request.GET.get('version')
        version_info = get_version(version)
        filename = version_info['filename']
        cache_file_path = os.path.join(app_cache_dir, filename)
        if not os.path.exists(cache_file_path):
            return self.render_to_json_error('文件不存在')
        else:
            from jiefoundation.utils import extract_from_zip
            install_folder = get_config()['install_folder']
            install_dir = install_folder + '/' + os.path.splitext(filename)[0]
            if os.path.exists(install_dir):
                return self.render_to_json_error('安装目录已存在~不能重复安装~')
            extract_from_zip(cache_file_path, extract_to=install_folder)
            print('解压完成，写入json数据...')

            unique_id = str(uuid.uuid4())
            with open(installed_file_path, 'r', encoding='utf-8') as f:
                installed = json.load(f)
            installed[unique_id] = {
                'uuid': unique_id,
                'version': version,
                'name': version_info['name'],
                'title': version_info['name'],
                'install_dir': install_dir,
                'set_root_password': 0,
                'config_status': 0,
                "data_dir": install_dir + '-data/data/',
                "conf_file": install_dir + '-data/my.ini',
                "port": '',
                "set_service": True,
                "service_name": '',
                "service_auto": "",
            }

            installed = get_sorted(installed, 'version')

            with open(installed_file_path, 'w', encoding='utf-8') as f:
                json.dump(installed, f, ensure_ascii=False, indent=4)
            return self.render_to_json_response({'status':'success', 'id': unique_id, 'message': '解压成功！'})


class CheckPortView(JsonView):
    def get(self, request, *args, **kwargs):
        base_port = new_port = int(request.GET.get('port'))
        installed_ports = []
        installed_list = get_installed()
        for item in installed_list.values():
            installed_ports.append(item['port'])
        is_new = 0

        while True:
            port = find_available_port(new_port)
            if port not in installed_ports:
                import socket
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex(('127.0.0.1', port))
                    sock.close()
                    if result != 0:
                        new_port = port
                        break
                except:
                    new_port = port
                    break
            is_new = 1
            new_port = port + 1
        message = f'端口{base_port}可用！'
        if is_new:
            message = f'端口 {base_port} 已被占用，自动选择新端口 {new_port} ！'
        return self.render_to_json_response({
            'status': 'success',
            'message': message,
            'port': new_port,
        })

class CheckServernameView(JsonView):
    def get(self, request, *args, **kwargs):
        service = request.GET.get('service')
        result = run_command(['sc', 'qc', service])
        if result.returncode == 0:
            return self.render_to_json_error('服务名已存在，请输入其他的服务名~')
        else:
            return self.render_to_json_success('服务名可以使用！')


class InitializeView(MysqlMixin, FormView):
    template_name = 'db_mysql/initialize.html'
    form_class = InitializeForm

    def get_initial(self):
        initial = super().get_initial()
        initial['install_id'] = self.request.GET.get('id')
        install_info =  get_installed(initial['install_id'])
        initial['port'] = find_available_port(3306)
        initial['set_service'] = True
        initial['service_name'] = f'MySQL{install_info['version'].replace('.', '')}'
        initial['service_auto'] = True
        return initial.copy()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'MySQL安装-初始化'
        context['breadcrumb'] = [
            {
                'title': 'MySQL服务',
                'href': reverse_lazy(f'{app_name}:index'),
                'active': False
            },
            {
                'title': 'MySQL安装-初始化',
                'href': '',
                'active': True
            },
        ]
        context['install_info'] = get_installed(self.request.GET.get('id'))
        return context

    def get_success_url(self):
        return reverse_lazy(f'{app_name}:index', query={'id': self.request.GET.get('id')})

    def form_valid(self, form):
        id = form.cleaned_data.get('install_id')
        port = int(form.cleaned_data.get('port'))
        set_service = form.cleaned_data.get('set_service')
        service_auto = form.cleaned_data.get('service_auto')
        service_name = form.cleaned_data.get('service_name')

        from panelcore.helper import is_port_available
        installed_ports = []
        installed_list = get_installed()
        for item in installed_list.values():
            installed_ports.append(item['port'])

        check_error = 0
        if not is_port_available(port) or port in installed_ports:
            form.add_error('port', '端口被占用！请选择其他端口~')
            check_error = 1
        if set_service:
            result = run_command(['sc', 'qc', service_name])
            if result.returncode == 0:
                form.add_error('service_name', '服务名已存在！请输入其他服务名~')
                check_error = 1

        if check_error:
            return self.form_invalid(form)

        install_info = get_installed(id)
        if not install_info:
            messages.error(self.request, '安装信息不存在！请勿修改链接或从非法地址进入~')
            return self.form_invalid(form)
        print('创建 my.ini 文件')
        install_info['port'] = port
        import configparser
        config_dir = os.path.dirname(install_info['conf_file'])
        os.makedirs(config_dir, exist_ok=True)

        config = configparser.ConfigParser()
        config['mysqld'] = {
            'port': str(port),
            'basedir': install_info['install_dir'],
            'datadir': install_info['data_dir'],
            'character-set-server': 'utf8mb4',
            'default-storage-engine': 'INNODB',
        }
        config['mysql'] = {
            'default-character-set': 'utf8mb4'
        }
        config['client'] = {
            'port': str(port),
            'default-character-set': 'utf8mb4'
        }
        with open(install_info['conf_file'], 'w', encoding='utf-8') as configfile:
            config.write(configfile)
        print(f"MySQL配置文件已创建: {install_info['conf_file']}")

        print(f"开始初始化数据库...")
        # runt_mysqld = f'{install_info['install_dir']}/bin/mysqld.exe'
        # parameters = f'--defaults-file={install_info['conf_file']} --initialize-insecure'
        # print(runt_mysqld + ' ' + parameters)
        # windows_api(runt_mysqld, parameters, operation="runas")
        run_file = f'{install_info['install_dir']}/bin/mysqld.exe --defaults-file={install_info['conf_file']} --initialize-insecure'
        print(run_file)
        result = run_command(run_file, shell=True, cwd=install_info['install_dir'])
        if result.returncode != 0:
            messages.error(self.request, f'初始化数据库失败！错误内容{result.stderr}')
            return self.form_invalid(form)
        # print(f"数据库初始化完成")

        install_info['set_service'] = set_service
        install_info['service_name'] = service_name
        install_info['service_auto'] = service_auto

        if set_service:
            # 创建服务
            print(f"开始创建服务: {service_name}")

            try:
                windows_api_blocking(
                    executable=f'{install_info['install_dir']}/bin/mysqld.exe',
                    parameters=f'--install "{service_name}" --defaults-file={install_info['conf_file']}',
                    operation="runas",
                )
                windows_api_blocking(
                    executable='sc',
                    parameters=f'description "{service_name}" "{install_info['name']} 服务"',
                    operation="runas",
                )

            except Exception as e:
                print(f'创建服务失败！{e}')
            if service_auto:
                print(f"设置服务自动启动: {service_name}")
                if service_auto:
                    auto_str = 'auto'
                else:
                    auto_str = 'demand'
                windows_api_blocking(
                    executable='sc',
                    parameters=f'config "{service_name}" start={auto_str}',
                    operation="runas",
                )
                print('尝试立即启动服务。。。')
                windows_api_blocking(
                    executable='sc',
                    parameters=f'start "{service_name}"',
                    operation="runas",
                )
                print(f"服务启动完成: {service_name}")
            print(f"服务创建完成: {service_name}")
        install_info['config_status'] = 1
        installed_list[id] = install_info

        with open(installed_file_path, 'w', encoding='utf-8') as f:
            json.dump(installed_list, f, ensure_ascii=False, indent=4)

        return super().form_valid(form)


class ServerDetailView(MysqlMixin, TemplateView):
    template_name = 'db_mysql/detail.html'

    def get_context_data(self, **kwargs):
        from panelcore.helper import get_service_status
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'MySQL服务详情'
        context['breadcrumb'] = [
            {
                'title': 'MySQL服务',
                'href': reverse_lazy(f'{app_name}:index'),
                'active': False
            },
            {
                'title': 'MySQL服务详情',
                'href': '',
                'active': True
            },
        ]
        context['id'] = self.kwargs.get('id')
        install_info = get_installed(self.kwargs.get('id'))
        context['install_info'] = install_info
        context['server_status'] = {}
        if install_info['set_service'] and install_info['service_name']:
            context['server_status'] = get_service_status(install_info['service_name'])
        return context


class UninstallView(RedirectView):
    url = reverse_lazy(f'{app_name}:index')

    def get(self, request, *args, **kwargs):
        id = self.kwargs.get('id')
        install_info = get_installed(id)
        if not install_info:
            messages.error(self.request, '安装信息不存在！请勿修改链接或从非法地址进入~')
            self.url = reverse_lazy(f'{app_name}:index')
            return super().get(request, *args, **kwargs)

        if install_info['set_service'] and install_info['service_name']:
            print(f"开始删除服务: {install_info['service_name']}")

            windows_api_blocking(
                executable='sc',
                parameters=f'stop "{install_info['service_name']}"',
                operation="runas",
            )
            windows_api_blocking(
                executable='sc',
                parameters=f'delete "{install_info['service_name']}"',
                operation="runas",
            )
            print(f"服务删除完成: {install_info['service_name']}")

            # time.sleep(3)
        # 删除安装文件夹
        data_dir = os.path.dirname(install_info['conf_file'])
        if os.path.exists(data_dir):
            print(f"开始删除数据文件夹: {data_dir}")
            shutil.rmtree(data_dir)
            print('数据文件夹删除完成。。')

        if os.path.exists(install_info['install_dir']):
            print(f"开始删除安装文件夹: {install_info['install_dir']}")
            shutil.rmtree(install_info['install_dir'])
            print('安装文件夹删除完成。。')

        install_list = get_installed()
        install_list.pop(id)
        with open(installed_file_path, 'w', encoding='utf-8') as f:
            json.dump(install_list, f, ensure_ascii=False, indent=4)

        print('卸载完成')
        return super().get(request, *args, **kwargs)


class StatusActionView(JsonView):
    def get(self, request, *args, **kwargs):
        id = self.kwargs.get('id')
        service_name = get_installed(id)['service_name']
        action = self.kwargs.get('action')

        if not service_name:
            return self.render_to_json_error('服务名称不能为空')

        if not action:
            return self.render_to_json_error('操作类型不能为空')

        valid_actions = {'start':'启动', 'stop':'停止', 'restart': '重启'}
        if action not in valid_actions:
            return self.render_to_json_error(f'不支持的操作类型: {action}')

        try:
            if action == 'restart':
                windows_api_blocking(executable='sc', parameters=f'stop "{service_name}"', operation="runas")
                # time.sleep(2)
                windows_api_blocking(executable='sc', parameters=f'start "{service_name}"', operation="runas")
            else:
                windows_api_blocking(executable='sc', parameters=f'{action} "{service_name}"', operation="runas")
            return self.render_to_json_success(f'服务操作完成: {service_name} {valid_actions[action]}')
        except Exception as e:
            return self.render_to_json_error(f'执行服务操作时发生异常: {str(e)}')


class InitRootPasswordView(MysqlMixin, FormView):
    template_name = 'db_mysql/init_root.html'
    form_class = UserPasswordForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'MySQL安装-初始化root密码'
        context['breadcrumb'] = [
            {
                'title': 'MySQL环境管理',
                'href': reverse_lazy(f'{app_name}:index'),
                'active': False
            },
            {
                'title': 'MySQL安装-初始化root密码',
                'href': '',
                'active': True
            },
        ]
        context['id'] = self.kwargs.get('id')
        context['install_info'] = get_installed(self.kwargs.get('id'))
        return context

    def get_success_url(self):
        return reverse_lazy(f'{app_name}:init_root_password', kwargs={'id': self.kwargs.get('id')})

    def form_valid(self, form):
        id = self.kwargs.get('id')
        password = form.cleaned_data.get('password')
        installed_list = get_installed()
        install_info = installed_list[id]
        mysqladmin_file = f'{install_info['install_dir']}/bin/mysqladmin.exe'
        result = run_command(
            f'{mysqladmin_file} --host localhost --port {install_info['port']} -u root password "{password}"',
            shell=True,
            cwd=install_info['install_dir']
        )
        if result.returncode == 0:
            install_info['set_root_password'] = 1
            installed_list[id] = install_info
            with open(installed_file_path, 'w', encoding='utf-8') as f:
                json.dump(installed_list, f, ensure_ascii=False, indent=4)
            messages.success(self.request, '初始化root密码完成！')
        else:
            messages.error(self.request, f'初始化root密码失败！错误信息:{result.stderr}')

        return super().form_valid(form)


class LoginMysqlView(JsonView):
    csrf_exempt = True

    def post(self, request, *args, **kwargs):
        get_id = self.request.POST.get('id')
        password = self.request.POST.get('password')
        installed_list = get_installed()
        install_info = installed_list.get(get_id)
        if not install_info:
            return self.render_to_json_error('安装信息不存在')

        service_name = install_info.get('service_name')
        if service_name:
            from panelcore.helper import get_service_status
            service_status = get_service_status(service_name)
            if service_status['status'] != 'running':
                return self.render_to_json_error('MySQL服务未运行，请先启动服务')
        mysql_file = f'{install_info["install_dir"]}/bin/mysql.exe'
        port = install_info.get('port')
        try:
            test_command = [
                mysql_file,
                '-u', 'root',
                f'-p{password}',
                '-h', 'localhost',
                '-P', str(port),
                '-e', 'SELECT VERSION()'
            ]
            result = run_command(
                test_command,
                cwd=install_info['install_dir']
            )
            if result.returncode == 0:
                return self.render_to_json_success('您可以使用其他管理工具连接使用！')
            else:
                error_msg = result.stderr.strip()
                if 'access denied' in error_msg.lower():
                    return self.render_to_json_error('用户名或密码错误!')
                elif 'can\'t connect' in error_msg.lower():
                    return self.render_to_json_error('无法连接到MySQL服务器!')
                else:
                    return self.render_to_json_error(f'{error_msg}')

        except Exception as e:
            return self.render_to_json_error(f'执行登录测试时发生异常: {str(e)}')



class CleanCacheView(MysqlMixin, RedirectView):
    url = reverse_lazy(f'{app_name}:index')

    def get(self, request, *args, **kwargs):
        try:
            if os.path.exists(app_cache_dir):
                shutil.rmtree(app_cache_dir)
                os.makedirs(app_cache_dir, exist_ok=True)
                messages.success(request, '缓存清理完成！')
            else:
                # 如果目录不存在，创建它
                os.makedirs(app_cache_dir, exist_ok=True)
                messages.info(request, '缓存目录不存在，已创建空目录！')
        except PermissionError:
            messages.error(request, '权限不足，无法清理缓存！请确保程序有足够权限。')
        except Exception as e:
            messages.error(request, f'清理缓存时发生错误: {str(e)}')

        return super().get(request, *args, **kwargs)


class EditConfigView(MysqlMixin, FormView):
    template_name = 'db_mysql/edit_config.html'
    form_class = ConfigEditForm

    def get_success_url(self):
        return reverse_lazy(f'{app_name}:edit_config', kwargs={'id': self.kwargs.get('id')})

    def get_initial(self):
        initial = super().get_initial()
        ini_file = get_installed(self.kwargs.get('id'))['conf_file']
        initial['content']  = read_file(ini_file)
        return initial.copy()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '编辑配置文件my.ini'
        context['breadcrumb'] = [
            {
                'title': 'MySQL环境管理',
                'href': reverse_lazy(f'{app_name}:index'),
                'active': False
            },
            {
                'title': 'MySQL服务详情',
                'href': reverse_lazy(f'{app_name}:detail', kwargs={'id': self.kwargs.get('id')}),
                'active': False
            },
            {
                'title': '编辑配置文件my.ini',
                'href': '',
                'active': True
            }
        ]
        context['conf_file'] = get_installed(self.kwargs.get('id'))['conf_file']
        return context

    def form_valid(self, form):
        content = form.cleaned_data.get('content')
        ini_file = get_installed(self.kwargs.get('id'))['conf_file']
        content = content.replace('\r\n', '\n').replace('\r', '\n')


        write_file(ini_file, content)
        messages.success(self.request, '配置文件保存成功！')
        return super().form_valid(form)


class ImportServiceView(MysqlMixin, FormView):
    template_name = f'{app_name}/import_service.html'
    form_class = ImportServiceForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'MySQL导入配置服务'
        context['breadcrumb'] = [
            {
                'title': 'MySQL环境管理',
                'href': reverse_lazy(f'{app_name}:index'),
                'active': False
            },
            {
                'title': 'MySQL服务详情',
                'href': reverse_lazy(f'{app_name}:detail', kwargs={'id': self.kwargs.get('id')}),
                'active': False
            },
            {
                'title': 'MySQL导入配置服务',
                'href': '',
                'active': True
            }
        ]
        context['id'] = self.kwargs.get('id')
        install_info = get_installed(self.kwargs.get('id'))
        context['install_info'] = install_info
        context['have_service'] = False
        context['system_service'] = []
        context['default_service_name'] = f'MySQL{install_info["version"].replace('.', '')}'
        i = 1
        is_select = False
        for service in psutil.win_service_iter():
            try:
                service_info = service.as_dict()
                binpath = service_info.get('binpath')
                if install_info['conf_file'] in binpath:
                    context['have_service'] = True
                    if i == 1: is_select  = True
                    context['system_service'].append({
                        'name': service_info.get('name'),
                        'display_name': service_info.get('display_name'),
                        'start_type': service_info.get('start_type'),
                        'status': service_info.get('status'),
                        'description': service_info.get('description'),
                        'binpath': service_info.get('binpath'),
                        'is_select': is_select
                    })
                    i = i + 1
            except Exception as e:
                continue
        return context

    def get_success_url(self):
        return reverse_lazy(f'{app_name}:detail', kwargs={'id': self.kwargs.get('id')})

    def form_valid(self, form):
        id = self.kwargs.get('id')
        select_service_type = form.cleaned_data.get('select_service_type')
        system_service_name = form.cleaned_data.get('system_service_name')
        service_name = form.cleaned_data.get('service_name')
        service_auto = form.cleaned_data.get('service_auto')

        set_service = False
        config_status = 2

        if select_service_type == 'system':
            set_service = True
            config_status = 1
            service_name = system_service_name
            service_auto = True
        if select_service_type == 'new':
            set_service = True
            config_status = 1
        if select_service_type == 'no':
            set_service = False
            config_status = 1
            service_name = ''
            service_auto = False

        with open(installed_file_path, 'r+', encoding='utf-8') as f:
            installed_data = json.load(f)

        installed_data[id]['set_service'] = set_service
        installed_data[id]['service_name'] = service_name
        installed_data[id]['service_auto'] = service_auto
        installed_data[id]['config_status'] = config_status

        with open(installed_file_path, 'w', encoding='utf-8') as f:
            json.dump(installed_data, f, ensure_ascii=False, indent=4)

        return super().form_valid(form)
