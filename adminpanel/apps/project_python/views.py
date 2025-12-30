import os
import re
import shutil

from django.urls import reverse_lazy, reverse
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.edit import FormView
from django.contrib import messages

from jiefoundation.jiebase import JsonView
from jiefoundation.utils import windows_api_blocking, remove_blank_lines, run_command
from panelcore.mixin import ProjectMixin

from .forms import PycharmInstallForm, ProjectCreateForm, ProjectSetSdkForm, PycharmResetForm
from .config import app_name, app_data_dir
from .helper import (
    get_pycharm_install, get_pycharm_download, get_pycharm_project, get_pycharm_sdk, 
    get_dict_subkey_value_list,get_project_idea_info, get_pycharm_option, get_project_file_path
)

class ProjectPythonMixin(ProjectMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_menu'] = app_name
        context['page_title'] = 'Pycharm项目'
        context['pycharm'] = get_pycharm_install()
        context['check_options'] = False
        if context['pycharm']:
            option_dir = os.path.join(os.environ.get("APPDATA"), 'JetBrains', context['pycharm']['dataDirectoryName'], 'options')
            if os.path.exists(option_dir): context['check_options'] = True
        return context


class IndexView(ProjectPythonMixin, TemplateView):
    template_name = f'{app_name}/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['projects'] = get_pycharm_project()
        return context
    

class SoftWareView(ProjectPythonMixin, TemplateView):
    template_name = f'{app_name}/software.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '其他 Python 开发工具'
        context['breadcrumb'] = [
            {
                'title': 'Pycharm 项目',
                'href': reverse_lazy(f'{app_name}:index'),
                'active': False
            },
            {
                'title': '其他 Python 开发工具',
                'href': '',
                'active': True
            }
        ]
        return context


class PycharmSdkListView(ProjectPythonMixin, TemplateView):
    template_name = f'{app_name}/pycharm_sdks.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Pycharm解释器环境'
        context['sdk_list'] = get_pycharm_sdk()
        context['project_sdk_list'] = get_dict_subkey_value_list(get_pycharm_project(), 'sdk_name')
        return context


class PycharmDownloadView(ProjectPythonMixin, TemplateView):
    template_name = f'{app_name}/pycharm_download.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '下载pycharm'
        context['breadcrumb'] = [
            {
                'title': 'Pycharm 项目',
                'href': reverse_lazy(f'{app_name}:index'),
                'active': False
            },
            {
                'title': 'Pycharm下载',
                'href': '',
                'active': True
            }
        ]
        pycharm_versions = get_pycharm_download()
        context['releases_list'] = list(pycharm_versions.keys())
        context['current_releases'] = self.request.GET.get('releases', '2025')
        context['sub_version_list'] = {}
        for sub_version, sub_version_info in pycharm_versions[context['current_releases']].items():
            context['sub_version_list'][sub_version] = {
                'default':sub_version_info['default'],
                'versions': list(sub_version_info['versions'].keys())
            }
        context['current_version'] = self.request.GET.get('version')
        if context['current_version']:
            current_sub_version = '.'.join(context['current_version'].split('.')[:2])
            context['sub_version_list'][current_sub_version]['default'] = {
                'version':context['current_version'],
                'type': pycharm_versions[context['current_releases']][current_sub_version]['versions'][context['current_version']]
            }
        context['action'] = self.request.GET.get('action')
        return context

class PycharmInstallFormView(ProjectPythonMixin, FormView):
    form_class = PycharmInstallForm
    template_name = f'{app_name}/pycharm_install.html'

    def get_initial(self):
        initial = super().get_initial()
        initial['install_dir'] = 'c:/program Files/JetBrains'
        return initial.copy()
            
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '安装Pycharm'
        context['breadcrumb'] = [
            {
                'title': 'Pycharm项目',
                'href': reverse_lazy(f'{app_name}:index'),
                'active': False
            },
            {
                'title': 'Pycharm下载',
                'href': reverse_lazy(f'{app_name}:pycharm_download'),
                'active': False
            },
            {
                'title': 'Pycharm安装',
                'href': '',
                'active': True
            }
        ]
        context['version'] = self.kwargs.get('version')
        return context


class PycharmInstallRunView(JsonView):
    csrf_exempt = True

    def post(self, request, *args, **kwargs):
        file_path = self.request.POST.get('file_path').replace('/', '\\')
        install_dir = self.request.POST.get('install_dir').replace('/', '\\')
        if not os.path.exists(file_path):
            return self.render_to_json_error('所选择的文件不存在！请检查选择是否正确！')
        if not os.path.isfile(file_path):
            return self.render_to_json_error('所选择的安装文件不是文件！')
        if not os.path.exists(install_dir):
            return self.render_to_json_error('所选择的安装文件夹路径不存在！')
        if not os.path.isdir(install_dir):
            return self.render_to_json_error('所选择的安装目录不是文件路径~')
        file_name = file_path.split('\\')[-1:][0]
        filename_path, extension = os.path.splitext(file_path)        
        if extension != '.zip' and extension != '.exe':
            return self.render_to_json_error('不是所支持的安装包文件扩展名(.exe或者.zip)~')
        localtion_install_dir = f'{install_dir}\\{file_name.replace(extension, '').replace(' ', '_')}'
        from .config import app_data_dir
        slient_conifg_file = f'{str(app_data_dir)}\\silent.config'
        print('开始安装...')
        windows_api_blocking(
            executable=file_path, 
            parameters=f'/S /CONFIG={slient_conifg_file} /LOG={install_dir}\\install.log /D={localtion_install_dir}',
            operation='runas'
        )
        return self.render_to_json_success('安装完成')


class PycharmRunView(JsonView):

    def get(self, request, *args, **kwargs):
        pycharm_info = get_pycharm_install()
        run_type = self.kwargs.get('runtype')
        if not pycharm_info:
            return self.render_to_json_error('没有找到Pycharm安装配置信息！')
        if run_type == 'normal':
            result = windows_api_blocking(
                f"{pycharm_info['InstallLocation']}/{pycharm_info['launcherPath']}",
                operation='runas'
            )
        if run_type == 'list':
            result = windows_api_blocking(
                f"{pycharm_info['InstallLocation']}/{pycharm_info['launcherPath']}",
                parameters='dontReopenProjects', operation='runas'
            )
        if run_type == 'plugins':
            result = windows_api_blocking(
                f"{pycharm_info['InstallLocation']}/{pycharm_info['launcherPath']}",
                parameters='disableNonBundledPlugins', operation='runas'
            )
        return self.render_to_json_success('ok')


class PycharmResetView(ProjectPythonMixin, FormView):
    form_class = PycharmResetForm
    template_name = f'{app_name}/pycharm_reset.html'
    initial = {'del_cache': False, 'del_settings': False, 'keep_license': True}
    success_url = reverse_lazy(f'{app_name}:index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '重置Pycharm'
        context['breadcrumb'] = [
            {
                'title': 'Pycharm项目',
                'href': reverse_lazy(f'{app_name}:index'),
                'active': False
            },
            {
                'title': '重置Pycharm',
                'href': '',
                'active': True
            }
        ]
        return context

    def form_valid(self, form):
        confirm_reset = form.cleaned_data.get('confirm_reset')
        if not confirm_reset:
            form.add_error('confirm_reset', '如果要重置，请选中此项再提交！')
            return super().form_invalid(form)
        pycharm = get_pycharm_install()
        shutil.rmtree(os.path.join(os.environ.get('LOCALAPPDATA'), 'JetBrains', pycharm['dataDirectoryName']))
        shutil.rmtree(os.path.join(os.environ.get('APPDATA'), 'JetBrains', pycharm['dataDirectoryName']))
        return super().form_valid(form)


class PycharmDetailView(ProjectPythonMixin, TemplateView):
    template_name = f'{app_name}/pycharm_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Pycharm安装信息'
        context['breadcrumb'] = [
            {
                'title': 'Pycharm项目',
                'href': reverse_lazy(f'{app_name}:index'),
                'active': False
            },
            {
                'title': 'Pycharm安装信息',
                'href': '',
                'active': True
            }
        ]
        return context


class PycharmUninstallRunView(JsonView):
    csrf_exempt = True

    def get(self, request, *args, **kwargs):
        config = get_pycharm_install()
        if not config:
            return self.render_to_json_error('没有找到pycharm安装配置信息~')
        try:
            if config['installType'] == 'installer':
                print('运行卸载程序...')
                windows_api_blocking(config['UninstallString'], operation="runas")
                return self.render_to_json_success('卸载完成~')
        except Exception as e:
            return self.render_to_json_error(e)


class  PycharmProjectOpenView(JsonView):
    def post(self, request, *args, **kwargs):
        pycharm_info = get_pycharm_install()
        pycharm_run = pycharm_info['InstallLocation']+'\\'+pycharm_info['launcherPath']
        path = self.request.POST.get('path')
        if os.path.exists(path):
            result = windows_api_blocking(pycharm_run, parameters=path, operation='runas')
            return self.render_to_json_success(f'打开项目操作完成~请检查显示..')
        else:
            return self.render_to_json_error(f'项目文件夹路径不存在！')


class ProjectCreateView(ProjectPythonMixin, FormView):
    form_class = ProjectCreateForm
    template_name = f'{app_name}/project_create.html'
    success_url = reverse_lazy(f'{app_name}:index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '添加Pycharm项目'
        context['breadcrumb'] = [
            {
                'title': 'Pycharm项目',
                'href': reverse_lazy(f'{app_name}:index'),
                'active': False
            },
            {
                'title': '添加Pycharm项目',
                'href': '',
                'active': True
            }
        ]
        return context
    
    def form_valid(self, form):
        project_dir = form.cleaned_data.get('project_dir')
        if not project_dir:
            form.add_error('project_dir', '请输入或者选择要添加的项目文件夹~')
            return super().form_invalid(form)
        if not os.path.exists(project_dir):
            form.add_error('project_dir', '项目文件夹不存在，请重新选择或者输入~')
            return super().form_invalid(form)
        idea_dir = os.path.join(project_dir, '.idea')
        project = {}
        if os.path.exists(idea_dir):
            project= get_project_idea_info(project_dir)
        else:
            project_name = project_dir.split('/')[-1]
            project = {
                'project_dir': project_dir, 'project_path_exists': False, 'project_name': project_name, 
                'old_name': project_name, 'sdk_name':'', 'sdk_path':'', 'sdk_path_exists':False, 'sdk_uuid':''
            }
            shutil.copytree(os.path.join(app_data_dir, 'template_idea'), idea_dir)
            os.rename(os.path.join(idea_dir, 'iml_name.iml'), os.path.join(idea_dir, f'{project_name}.iml'))
            modules_file = os.path.join(idea_dir, 'modules.xml')
            modules_file_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<project version="4">
  <component name="ProjectModuleManager">
    <modules>
      <module fileurl="file://$PROJECT_DIR$/.idea/{project_name}.iml" filepath="$PROJECT_DIR$/.idea/{project_name}.iml" />
    </modules>
  </component>
</project>
"""
            with open(modules_file, 'w', encoding='utf-8') as f:
                f.write(modules_file_content)
        # ----------------添加项目到 pycharm 中---------------------------------------
        pycharm_project_file = get_pycharm_option('project')
        with open(pycharm_project_file, 'r', encoding='utf-8') as f:
            recent_project_content = f.read()
        
        find_index = recent_project_content.rfind('</map>')
        last_opened_index = re.search(r'<option name="lastOpenedProject"', recent_project_content)

        from .config import project_xml_str
        new_recent_project_content = project_xml_str.replace(r"{{project_dir}}", project['project_dir']).replace(r"{{project_name}}", project['project_name'])
        if find_index != -1:
            recent_project_content = recent_project_content[:find_index] + new_recent_project_content + recent_project_content[find_index:]
        elif last_opened_index:
            start_index = last_opened_index.start()
            add_start_map = """
    <option name="additionalInfo">
      <map>"""
            add_end_map = """
      </map>
    </option>
"""
            recent_project_content = recent_project_content[:start_index] + add_start_map + new_recent_project_content + add_end_map + recent_project_content[start_index:]
        else:
            pass
            # form.add_error('project_dir', '导入Pycharm异常~未找到 </map> 或 <option name=\"lastOpenedProject\" 标签')
            # return super().form_invalid(form)
        with open(pycharm_project_file, 'w', encoding='utf-8') as f:
            f.write(recent_project_content)
        return super().form_valid(form)


class ProjectCheckPathView(JsonView):
    def post(self, request, *args, **kwargs):
        project_dir = self.request.POST.get('project_dir')
        if not os.path.exists(project_dir):
            return self.render_to_json_error('所输入的项目路径不存在~请重新选择输入~')
        if project_dir in get_dict_subkey_value_list(get_pycharm_project(), 'project_path'):
            return self.render_to_json_error('此项目路径已经存在~请勿重复添加。')
        if os.path.exists(project_dir + '/.idea'):
            return self.render_to_json_success('检测到当前项目下有配置文件，将自动导入配置文件信息~')        
        return self.render_to_json_success('')


class CheckEnvsFolderExists(JsonView):
    def post(self, request, *args, **kwargs):
        project_path = self.request.POST.get('project_path')
        if os.path.exists(project_path):
            return self.render_to_json_error('注意：文件已存在~提交将会覆盖!')
        return self.render_to_json_success('虚拟环境将保存到上述文件夹中。')


class ProjectDelView(RedirectView):
    url = reverse_lazy(f'{app_name}:index')

    def post(self, *args, **kwargs):
        project_path = self.request.POST.get('project_path')
        project = get_pycharm_project(project_path)
        if not project:
            messages.warning('在Pycharm中没有找到所提交的项目路径！')
            return super().post(*args, **kwargs)
        pycharm_project_file = get_pycharm_option('project')
        with open(pycharm_project_file, 'r', encoding='utf-8') as f:
            content = f.read()
            pattern = re.compile(
            r'<entry key="' + re.escape(project_path) + r'">.*?</entry>',
            re.DOTALL
            )
        new_content = pattern.sub('', content, count=1)
        if new_content == content:
            messages.warning(self.request, f"警告: 未找到 key '{project_path}' 的 entry，文件未修改")
        else:
            with open(pycharm_project_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            messages.success(self.request, f'项目 {project['project_name']} 已经从Pycharm列表中删除。项目地址为{project_path}')
        return super().post(*args, **kwargs)


class ProjectSetSdkView(ProjectPythonMixin, FormView):
    template_name = f'{app_name}/project_set_sdk.html'
    form_class = ProjectSetSdkForm
    success_url = reverse_lazy(f'{app_name}:index')

    def get_initial(self):
        initial = super().get_initial()
        initial['project_path'] = self.request.GET.get('path')
        initial['create_venv'] = True
        project = get_pycharm_project(self.request.GET.get('path'))
        initial['venv_path'] = project['project_path'] + '/' + '.venv'
        return initial.copy()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '设置项目解释器'
        context['breadcrumb'] = [
            {
                'title': 'Pycharm项目',
                'href': reverse_lazy(f'{app_name}:index'),
                'active': False
            },
            {
                'title': '设置项目解释器',
                'href': '',
                'active': True
            }
        ]
        context['project'] = get_pycharm_project(self.request.GET.get('path'))
        return context

    def form_valid(self, form):
        project_path = form.cleaned_data.get('project_path')
        old_sdk_path = get_pycharm_project(project_path)['sdk_path']

        if not os.path.exists:
            form.add_error('project_path', f'当前项目位置{project_path}文件夹不存在！')
            return super().form_invalid(form)       
        sdk_type = form.cleaned_data.get('sdk_type')
        # 清理.idea/misc.xml里可能存在自定义配置sdk名称的项
        misc_file = get_project_file_path(project_path, 'misc.xml')
        if os.path.exists(misc_file):
            with open(misc_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            pattern = r'<component name="Black">[\s\S]*?</component>'
            xml_content = re.sub(pattern, '', xml_content, count=1)
            with open(misc_file, 'w', encoding='utf-8') as f:
                f.write(xml_content)

        iml_file = get_project_file_path(project_path, 'iml')
        if not iml_file:
            form.add_error('project_path', f'当前项目{project_path}配置iml文件异常~')
            return super().form_invalid(form)
        # -----------------清除项目里的解释器配置--------------------------------------
        if sdk_type == 'del':
            # 处理.iml配置文件
            with open(iml_file, 'r', encoding='utf-8') as f:
                iml_content = f.read()
            lines = iml_content.splitlines(keepends=True)
            filtered_lines = []
            for line in lines:
                if '<orderEntry type="jdk" jdkName="' in line:
                    continue
                filtered_lines.append(line)
            iml_content= ''.join(filtered_lines)
            with open(iml_file, 'w', encoding='utf-8') as f: f.write(iml_content)
            # 处理misc.xml
            if os.path.exists(misc_file):
                with open(misc_file, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
                lines = xml_content.splitlines(keepends=True)
                filtered_lines = []
                for line in lines:
                    if '<component name="ProjectRootManager" version="2" project-jdk-name="' in line:
                        continue
                    filtered_lines.append(line)
                xml_content= ''.join(filtered_lines)
                xml_content = remove_blank_lines(xml_content)
                with open(misc_file, 'w', encoding='utf-8') as f:
                    f.write(xml_content)

        #---------------------------------使用pycharm已经存在的环境----------------------------------------------
        if sdk_type == "pycharm":
            pycharm_sdk = form.cleaned_data.get('pycharm_sdk')
            # 处理.iml配置文件          
            with open(iml_file, 'r', encoding='utf-8') as f:
                iml_content = f.read()
            pattern = r'<orderEntry type="jdk" jdkName="'
            filtered_lines = []
            if pattern in iml_content:
                lines = iml_content.splitlines(keepends=True)
                for line in lines:
                    if pattern in line:
                        filtered_lines.append(f'    <orderEntry type="jdk" jdkName="{pycharm_sdk}" jdkType="Python SDK" />\n')
                    else:
                        filtered_lines.append(line)
                iml_content= ''.join(filtered_lines)
            else:
                new_order_entry = f'    <orderEntry type="jdk" jdkName="{pycharm_sdk}" jdkType="Python SDK" />\n'
                content_tag = '<content url="file://$MODULE_DIR$" />'
                index = iml_content.find(content_tag)
                if index != -1:
                    insert_index = index + len(content_tag)
                    iml_content = iml_content[:insert_index] + '\n' +  new_order_entry + iml_content[insert_index:]
                else:
                    new_entry = f'  <orderEntry type="jdk" jdkName="{pycharm_sdk}" jdkType="Python SDK" />'
                    pos = iml_content.find('</content>') + len('</content>')
                    iml_content = iml_content[:pos] + '\n  ' + new_entry + iml_content[pos:]
            iml_content = remove_blank_lines(iml_content)
            with open(iml_file, 'w', encoding='utf-8') as f:
                f.write(iml_content)
            # 处理misc.xml文件
            xml_content = ''
            if not os.path.exists(misc_file):
                from .config import project_misc_content
                xml_content = project_misc_content.replace(
                    '<component name="ProjectRootManager" version="2" project-jdk-name=""',
                    f'<component name="ProjectRootManager" version="2" project-jdk-name="{pycharm_sdk}"',
                )
            else:
                with open(misc_file, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
                filtered_lines = []
                lines = xml_content.splitlines(keepends=True)
                pattern = '<component name="ProjectRootManager" version="2" project-jdk-name="'
                new_content = f'  <component name="ProjectRootManager" version="2" project-jdk-name="{pycharm_sdk}" project-jdk-type="Python SDK" />\n'
                if pattern not in xml_content:
                    for line in lines:
                        if '<project version="4">' in line:
                            filtered_lines.append(line)
                            filtered_lines.append(new_content)
                        else:
                            filtered_lines.append(line)
                else:
                    for line in lines:
                        if pattern in line:
                            filtered_lines.append(new_content)
                        else:
                            filtered_lines.append(line)
                xml_content= ''.join(filtered_lines)
            xml_content = remove_blank_lines(xml_content)
            with open(misc_file, 'w', encoding='utf-8') as f:
                f.write(xml_content)
        # ---------------使用已经有的运行环境进行新的配置------------------------------------------------------
        if sdk_type == "new":
            import uuid
            from .config import sdk_new_str

            python_sdk = form.cleaned_data.get('python_sdk').split(', ')
            sdk_path = python_sdk[0]
            sdk_version = f'Python {python_sdk[1]}'
            project_name = get_pycharm_project(project_path)['project_name']
            sdk_uuid   = str(uuid.uuid4())
            sdk_name = f'{sdk_version}({project_name})'

            create_venv = form.cleaned_data.get('create_venv')
            venv_path = form.cleaned_data.get('venv_path')
            delete_old_venv = form.cleaned_data.get('delete_old_venv')
            if create_venv:                
                if delete_old_venv:
                    if os.path.exists(old_sdk_path):
                        old_sdk_dir = os.path.dirname(os.path.dirname(old_sdk_path))
                        if 'Scripts' in old_sdk_path and os.path.exists(os.path.join(old_sdk_dir, 'pyvenv.cfg')):
                            shutil.rmtree(old_sdk_dir)

                sdk_name = f'{sdk_version}({project_name})-venv'
                result = run_command(f'{sdk_path}python.exe -m venv {venv_path}', shell=True)
                if result.returncode == 0:
                    sdk_path = venv_path + '/' + 'Scripts' + '/'
                    sdk_new_str = sdk_new_str.replace('{sdk_name}', sdk_name).replace('{sdk_version}', sdk_version).replace(
                        '{sdk_path}', sdk_path).replace('{sdk_uuid}', sdk_uuid)
            else:
                sdk_new_str = sdk_new_str.replace('{sdk_name}', sdk_name).replace('{sdk_version}', sdk_version).replace(
                    '{sdk_path}', sdk_path).replace('{sdk_uuid}', sdk_uuid)

            # -----创建 Pycharm 解释器环境配置 ----------------------------------
            pycharm_sdk_table_file = get_pycharm_option('sdk')
            sdk_table_content = ''
            with open(pycharm_sdk_table_file, 'r', encoding='utf-8') as f:
                sdk_table_content = f.read()
            if '<jdk version="2">' not in sdk_table_content:
                sdk_table_content = sdk_table_content.replace(
                    '  <component name="ProjectJdkTable">',
                    '  <component name="ProjectJdkTable">\n'+ sdk_new_str,
                )
            else:
                sdk_end_str = """  </component>
</application>"""
                sdk_table_content = sdk_table_content.replace(
                    sdk_end_str,
                    sdk_new_str + '\n' + sdk_end_str,
                )
            sdk_table_content = remove_blank_lines(sdk_table_content)
            with open(pycharm_sdk_table_file, 'w', encoding='utf-8') as f:
                f.write(sdk_table_content)

            #------创建 Pycharm 项目配置 ----------------------------------
            with open(iml_file, 'r', encoding='utf-8') as f:
                iml_content = f.read()
            pattern = r'<orderEntry type="jdk" jdkName="'
            filtered_lines = []
            if pattern in iml_content:
                lines = iml_content.splitlines(keepends=True)
                for line in lines:
                    if pattern in line:
                        filtered_lines.append(f'    <orderEntry type="jdk" jdkName="{sdk_name}" jdkType="Python SDK" />\n')
                    else:
                        filtered_lines.append(line)
                iml_content= ''.join(filtered_lines)
            else:
                new_order_entry = f'    <orderEntry type="jdk" jdkName="{sdk_name}" jdkType="Python SDK" />\n'
                content_tag = '<content url="file://$MODULE_DIR$" />'
                index = iml_content.find(content_tag)
                if index != -1:
                    insert_index = index + len(content_tag)
                    iml_content = iml_content[:insert_index] + '\n' +  new_order_entry + iml_content[insert_index:]
                else:
                    new_entry = f'  <orderEntry type="jdk" jdkName="{sdk_name}" jdkType="Python SDK" />'
                    pos = iml_content.find('</content>') + len('</content>')
                    iml_content = iml_content[:pos] + '\n  ' + new_entry + iml_content[pos:]
            iml_content = remove_blank_lines(iml_content)
            with open(iml_file, 'w', encoding='utf-8') as f:
                f.write(iml_content)

            # 处理misc.xml文件
            xml_content = ''
            if not os.path.exists(misc_file):
                from .config import project_misc_content
                xml_content = project_misc_content.replace(
                    '<component name="ProjectRootManager" version="2" project-jdk-name=""',
                    f'<component name="ProjectRootManager" version="2" project-jdk-name="{sdk_name}"',
                )
            else:
                with open(misc_file, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
                filtered_lines = []
                lines = xml_content.splitlines(keepends=True)
                pattern = '<component name="ProjectRootManager" version="2" project-jdk-name="'
                new_content = f'  <component name="ProjectRootManager" version="2" project-jdk-name="{sdk_name}" project-jdk-type="Python SDK" />\n'
                if pattern not in xml_content:
                    for line in lines:
                        if '<project version="4">' in line:
                            filtered_lines.append(line)
                            filtered_lines.append(new_content)
                        else:
                            filtered_lines.append(line)
                else:
                    for line in lines:
                        if pattern in line:
                            filtered_lines.append(new_content)
                        else:
                            filtered_lines.append(line)
                xml_content= ''.join(filtered_lines)
            xml_content = remove_blank_lines(xml_content)
            with open(misc_file, 'w', encoding='utf-8') as f:
                f.write(xml_content)

            # ------- 处理自选python.exe解释器的选项-----------------
        if sdk_type == 'python':
            python_interpreter = form.cleaned_data.get('python_interpreter')
            if not python_interpreter:
                messages.warning(self.request, '请选择Python解释器文件')
                return super().form_invalid(form)
            if not python_interpreter.endswith('python.exe'):
                messages.warning(self.request, '请选择Python解释器文件，确保是python.exe文件。')
                return super().form_invalid(form)

            import uuid
            from .config import sdk_new_str
            sdk_path = python_interpreter.replace('python.exe', '')
            sdk_version = f'Python {run_command([python_interpreter, '--version']).stdout.replace("Python ", "").strip()}'
            project_name = get_pycharm_project(project_path)['project_name']
            sdk_uuid  = str(uuid.uuid4())
            sdk_name = f'{sdk_version}({project_name})'
            
            sdk_new_str = sdk_new_str.replace('{sdk_name}', sdk_name).replace('{sdk_version}', sdk_version).replace(
                '{sdk_path}', sdk_path).replace('{sdk_uuid}', sdk_uuid)
            

            pycharm_sdk_table_file = get_pycharm_option('sdk')
    
            sdk_table_content = ''
            with open(pycharm_sdk_table_file, 'r', encoding='utf-8') as f:
                sdk_table_content = f.read()

            if '<jdk version="2">' not in sdk_table_content:
                sdk_table_content = sdk_table_content.replace(
                    '  <component name="ProjectJdkTable">',
                    '  <component name="ProjectJdkTable">\n' + sdk_new_str,
                )
            else:
                sdk_end_str = """  </component>
</application>"""
                sdk_table_content = sdk_table_content.replace(
                    sdk_end_str,
                    sdk_new_str + '\n' + sdk_end_str,
                )
            sdk_table_content = remove_blank_lines(sdk_table_content)
            with open(pycharm_sdk_table_file, 'w', encoding='utf-8') as f:
                f.write(sdk_table_content)

            # ------创建 Pycharm 项目配置 ----------------------------------
            with open(iml_file, 'r', encoding='utf-8') as f:
                iml_content = f.read()
            pattern = r'<orderEntry type="jdk" jdkName="'
            filtered_lines = []
            if pattern in iml_content:
                lines = iml_content.splitlines(keepends=True)
                for line in lines:
                    if pattern in line:
                        filtered_lines.append(
                            f'    <orderEntry type="jdk" jdkName="{sdk_name}" jdkType="Python SDK" />\n')
                    else:
                        filtered_lines.append(line)
                iml_content = ''.join(filtered_lines)
            else:
                new_order_entry = f'    <orderEntry type="jdk" jdkName="{sdk_name}" jdkType="Python SDK" />\n'
                content_tag = '<content url="file://$MODULE_DIR$" />'
                index = iml_content.find(content_tag)
                if index != -1:
                    insert_index = index + len(content_tag)
                    iml_content = iml_content[:insert_index] + '\n' + new_order_entry + iml_content[insert_index:]
                else:
                    new_entry = f'  <orderEntry type="jdk" jdkName="{sdk_name}" jdkType="Python SDK" />'
                    pos = iml_content.find('</content>') + len('</content>')
                    iml_content = iml_content[:pos] + '\n  ' + new_entry + iml_content[pos:]
            iml_content = remove_blank_lines(iml_content)
            with open(iml_file, 'w', encoding='utf-8') as f:
                f.write(iml_content)

            # 处理misc.xml文件
            xml_content = ''
            if not os.path.exists(misc_file):
                from .config import project_misc_content
                xml_content = project_misc_content.replace(
                    '<component name="ProjectRootManager" version="2" project-jdk-name=""',
                    f'<component name="ProjectRootManager" version="2" project-jdk-name="{sdk_name}"',
                )
            else:
                with open(misc_file, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
                filtered_lines = []
                lines = xml_content.splitlines(keepends=True)
                pattern = '<component name="ProjectRootManager" version="2" project-jdk-name="'
                new_content = f'  <component name="ProjectRootManager" version="2" project-jdk-name="{sdk_name}" project-jdk-type="Python SDK" />\n'
                if pattern not in xml_content:
                    for line in lines:
                        if '<project version="4">' in line:
                            filtered_lines.append(line)
                            filtered_lines.append(new_content)
                        else:
                            filtered_lines.append(line)
                else:
                    for line in lines:
                        if pattern in line:
                            filtered_lines.append(new_content)
                        else:
                            filtered_lines.append(line)
                xml_content = ''.join(filtered_lines)
            xml_content = remove_blank_lines(xml_content)
            with open(misc_file, 'w', encoding='utf-8') as f:
                f.write(xml_content)

        return super().form_valid(form)


class PycharmSdkDeleteView(RedirectView):
    url = reverse_lazy(f'{app_name}:pycharm_sdk_list')

    def post(self, request, *args, **kwargs):
        sdk_name = self.request.POST.get('sdk_name')
        pycharm_sdk_table_file = get_pycharm_option('sdk')
        try:
            # 读取原始文件内容（保留所有原始空白字符）
            with open(pycharm_sdk_table_file, 'r', encoding='utf-8') as f:
                content = f.read()
            # 创建精确匹配的正则表达式（匹配整个 JDK 标签）
            pattern = re.compile(
                r'(\s*)<jdk[^>]*>\s*<name value="' + re.escape(sdk_name) + r'" />[\s\S]*?</jdk>(\s*)',
                re.DOTALL
            )
            new_content = re.sub(pattern, r'\1\2', content)
            # 检查是否实际删除了内容
            if new_content == content:
                messages.warning(self.request, f"警告: 未找到 name 什为 '{sdk_name}' 的配置标签，文件未修改")     
            # 清理 new_content 中的空白行
            new_content = remove_blank_lines(new_content)
            # 保存修改后的内容（保持原始格式）
            with open(pycharm_sdk_table_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            messages.success(self.request, f"成功: 已删除 name 为 '{sdk_name}' 的配置标签")
        except Exception as e:
            messages.warning(self.request, f'操作错误：{e}')
        return super().get(request, *args, **kwargs)


from apps.envs_python.views import (
    PythonRunMixin, PackageListMixin, PackageInstallMixin, PackageUninstallMixin, PackageUpgradeMixin
)

class ProjectPythonPackageMixin(PythonRunMixin):
    app_namespace = app_name

    def get_python_path(self):
        uid = self.request.GET.get('uid')
        if uid and os.path.exists(uid):
            return get_pycharm_project(uid)['sdk_path']
        return None

    def get_python_env(self):
        uid = self.request.GET.get('uid')
        if uid and os.path.exists(uid):
            pycharm_project = get_pycharm_project(uid)
            return {'name': pycharm_project['project_name'], 'version': pycharm_project['sdk_version'], 'folder': pycharm_project['sdk_path']}
        return None

class PackageListView(ProjectPythonMixin, ProjectPythonPackageMixin, PackageListMixin):
    template_name = f'{app_name}/package_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '包管理'
        context['breadcrumb'] = [
            {'title': 'Pycharm 项目', 'href': reverse_lazy(f'{app_name}:index')},
            {'title': '包管理', 'href':'', 'active': True},
        ]
        context['env_info'] = self.get_python_env()
        context['uid'] = self.request.GET.get('uid')
        return context


class PackageInstallView(ProjectPythonMixin, ProjectPythonPackageMixin, PackageInstallMixin):
    template_name = f'{app_name}/package_install.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '包安装'
        context['breadcrumb'] = [
            {'title': 'Pycharm 项目', 'href': reverse(f'{app_name}:index')},
            {'title': '包管理', 'href': reverse(f'{app_name}:package_list', query={'uid': self.request.GET.get('uid')})},
            {'title': '包安装', 'href':'', 'active': True},
        ]
        context['env_info'] = self.get_python_env()
        context['uid'] = self.request.GET.get('uid')
        return context

class PackageUninstallView(ProjectPythonPackageMixin, PackageUninstallMixin):
    pass

class PackageUpgradeView(ProjectPythonPackageMixin, PackageUpgradeMixin):
    pass
