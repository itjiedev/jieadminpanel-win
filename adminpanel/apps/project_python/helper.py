import json
import os
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET


def get_dict_subkey_value_list(obj_dict, sub_key):
    return_list = []
    if obj_dict:
        for k, v in obj_dict.items():
            if sub_key in v: return_list.append(v[sub_key])
    return return_list

def get_pycharm_download():
    from .config import pycharm_download_json
    with open(pycharm_download_json, 'r', encoding='utf-8') as f:
        return json.load(f)
    return {}


def get_pycharm_install(key_name=None):
    import winreg
    pycharm = {}
    try:
        reg_key_list = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")

        ]
        found = False
        for item in reg_key_list:
            with winreg.OpenKey(item[0], item[1]) as key:
                subkey_count = winreg.QueryInfoKey(key)[0]
                for i in range(subkey_count):
                    subkey_name = winreg.EnumKey(key, i)
                    if "PyCharm" in subkey_name:
                        found = True
                        pycharm_reg_key = (item, subkey_name)
                        break
                if found:break

        if found:
            with winreg.OpenKey(pycharm_reg_key[0][0], pycharm_reg_key[0][1]+"\\"+pycharm_reg_key[1]) as key:
                pycharm['installType'] = 'installer'
                pycharm['DisplayName'] = winreg.QueryValueEx(key, "DisplayName")[0]
                pycharm['DisplayVersion']  = winreg.QueryValueEx(key, "DisplayVersion")[0]
                pycharm['InstallLocation'] = winreg.QueryValueEx(key, "InstallLocation")[0]
                pycharm['UninstallString'] = winreg.QueryValueEx(key, "UninstallString")[0]
                pycharm['version'] = ''
                pycharm['dataDirectoryName'] = ''
                pycharm['launcherPath'] = ''

            pycharm_info_file = f"{pycharm['InstallLocation']}/product-info.json"
            if os.path.exists(pycharm_info_file):
                with open(pycharm_info_file, 'r', encoding='utf-8') as json_file:
                    project_info = json.load(json_file)
                    pycharm['version'] = project_info['version']
                    pycharm['dataDirectoryName'] = project_info['dataDirectoryName']
                    pycharm['launcherPath'] = project_info['launch'][0]['launcherPath']
    except Exception as e:
        print(f'发生错误：{e}')
    return pycharm


def get_pycharm_option(dir_name=None):
    pycharm = get_pycharm_install()
    option_dir = os.path.join(os.environ.get('APPDATA'), 'JetBrains', pycharm['dataDirectoryName'], 'options')
    if not os.path.exists(option_dir): return {}
    if dir_name == 'project':
        file_path = os.path.join(option_dir, 'recentProjects.xml')
        if not os.path.exists(file_path):
            from .config import app_data_dir
            shutil.copy(app_data_dir / 'recentProjects.xml', file_path)
        return file_path
    if dir_name == 'sdk':
        file_path = os.path.join(option_dir, 'jdk.table.xml')
        if not os.path.exists(file_path):
            from .config import app_data_dir
            shutil.copy(os.path.join(app_data_dir, 'jdk.table.xml'), file_path)
        return file_path
    return option_dir

def get_pycharm_sdk(sdk_name=None):
    pycharm_sdk_table_file = get_pycharm_option('sdk')
    sdk_tableS = {}

    if not os.path.exists(pycharm_sdk_table_file):
        with open(pycharm_sdk_table_file, 'w', encoding='utf-8') as f:
            from .config import emplty_sdk_xml_content
            f.write(emplty_sdk_xml_content)

    if os.path.exists(pycharm_sdk_table_file):
        sdk_tree = ET.parse(pycharm_sdk_table_file)
        sdk_root = sdk_tree.getroot()
        sdk_table_elem = sdk_root.find('.//component[@name="ProjectJdkTable"]')        
        for sdk in sdk_table_elem.findall('jdk'):
            name = sdk.find('name').get('value')
            sdk_uuid = sdk.find("additional").get('SDK_UUID') if sdk.find('additional') is not None else None
            sdk_path = sdk.find('homePath').get('value') if sdk.find('homePath') is not None else None
            sdk_path_dir = ''
            sdk_path_exists = False
            if sdk_path and  os.path.exists(sdk_path):
                sdk_path_exists = True
                sdk_path_dir = os.path.dirname(sdk_path)
            sdk_tableS[name] = {
                'sdk_name': name,
                'sdk_version': sdk.find('version').get('value') if sdk.find('version') is not None else None,
                'sdk_path': sdk_path,
                'sdk_path_exists': sdk_path_exists,
                'sdk_path_dir': sdk_path_dir,
                'sdk_uuid': sdk_uuid,
            }
    if sdk_name:
        if sdk_name in sdk_tableS: return sdk_tableS[sdk_name]
        return {}
    return sdk_tableS


def get_pycharm_project(search_project_path= None):
    pycharm_info =  get_pycharm_install()
    pycharm_projects = {}
    if pycharm_info:
        pycharm_project_file = get_pycharm_option('project')
        if not pycharm_project_file: return pycharm_projects

        tree = ET.parse(pycharm_project_file)
        root = tree.getroot()
        pycharm_projects = {}

        component = root.find('.//component[@name="RecentProjectsManager"]')
        if component is None:
            return pycharm_projects
        additional_info = component.find('.//option[@name="additionalInfo"]')
        if additional_info is None: return pycharm_projects

        sdk_table = get_pycharm_sdk()
        map_element = additional_info.find('map')

        for entry in map_element.findall('entry'):             
            project_path = entry.get('key')
            
            value_element = entry.find('value')        
            meta_info = value_element.find('RecentProjectMetaInfo')
            frame_title = meta_info.get('frameTitle')        
            project_name = frame_title
            pycharm_projects[project_path] = {
                'project_path': project_path, 'project_path_exists': False, 'project_name': project_name, 
                'old_name': project_name, 'sdk_name':'', 'sdk_path':'', 'sdk_path_exists':False, 'sdk_uuid':''
            }
            old_project_path = project_path
            if '$USER_HOME$' in project_path:
                project_path = os.environ.get('USERPROFILE').replace('\\','/') + '/' +project_path.replace('$USER_HOME$/', '')

            if os.path.exists(project_path): pycharm_projects[old_project_path]['project_path_exists'] = True
            # 获取sdk信息
            project_idea_dir = os.path.join(project_path, '.idea')
            if not os.path.exists(project_idea_dir):
                print('项目里的.idea配置文件夹不存在！')
            else:
                is_found = False
                for root, dirs, files in os.walk(project_idea_dir):
                    for file in files:
                        if file.endswith('.iml'):
                            is_found = True
                            pycharm_projects[old_project_path]['project_name'] = file.replace('.iml', '')
                            break
                    if is_found:break

                project_rename_file = os.path.join(project_idea_dir, '.name')
                if os.path.exists(project_rename_file):
                    with open(project_rename_file, 'r', encoding='utf-8') as f:
                        pycharm_projects[old_project_path]['project_name'] = f.read()

                misc_file = os.path.join(project_idea_dir, 'misc.xml')
                if os.path.exists(misc_file):
                    misc_tree = ET.parse(misc_file)
                    misc_root = misc_tree.getroot()
                    component = misc_root.find('.//component[@name="ProjectRootManager"]')
                    if component is not None:
                        pycharm_projects[old_project_path]['sdk_name'] = component.get('project-jdk-name') if component.get('project-jdk-name') else ''
                    if pycharm_projects[old_project_path]['sdk_name'] in sdk_table:
                        pycharm_projects[old_project_path]['sdk_version'] =  sdk_table[pycharm_projects[old_project_path]['sdk_name']]['sdk_version']
                        pycharm_projects[old_project_path]['sdk_path'] =  sdk_table[pycharm_projects[old_project_path]['sdk_name']]['sdk_path']
                        pycharm_projects[old_project_path]['sdk_path_exists'] =  sdk_table[pycharm_projects[old_project_path]['sdk_name']]['sdk_path_exists']
                        pycharm_projects[old_project_path]['sdk_uuid'] = sdk_table[pycharm_projects[old_project_path]['sdk_name']]['sdk_uuid']
                    
        if search_project_path:
            if search_project_path in pycharm_projects:
                return pycharm_projects[search_project_path]
            return {}
    return pycharm_projects


def get_project_file_path(project_path, file_name):
    # 获取当前项目里的指定文件路径
    if not os.path.exists(project_path):
        print(f'没有找到项目目录{project_path}')
        return ''
    if file_name:
        if file_name == 'iml':
            dir_path = Path(project_path) / '.idea'
            iml_files = [str(file) for file in dir_path.rglob('*.iml') if file.is_file()]
            if len(iml_files)>1 or len(iml_files) == 0:
                print(f'当前项目{project_path}配置iml文件异常~')
                return ''
            return iml_files[0]
        else:
            file_path = os.path.join(project_path, '.idea', file_name)
        return file_path


def get_project_idea_info(project_dir):
    if os.path.exists(project_dir):
        project_name = project_dir.split('/')[-1]
        project = {
            'project_name': project_name, 'project_dir': project_dir, 'sdk_name': '', 'sdk_version':'', 'sdk_path': '', 'sdk_uuid':''
            }
        name_file = os.path.join(project_dir, '.idea', '.name')
        if os.path.exists(name_file):
            with open(name_file, 'r', encoding='utf-8') as f:
                project['project_name'] = f.read()

        modules_file = get_project_file_path(project_dir, 'misc.xml')
        if os.path.exists(modules_file):
            tree = ET.parse(modules_file)
            root = tree.getroot()
            component = root.find('.//component[@name="ProjectRootManager"]')
            if component:
                project['sdk_name'] = component.get('project-jdk-name')
                pycharm_sdk = get_pycharm_sdk(project['sdk_name'])
                if pycharm_sdk:
                    project['sdk_version'] = pycharm_sdk['sdk_version']
                    project['sdk_path'] = pycharm_sdk['sdk_path']
                    project['sdk_uuid'] = pycharm_sdk['sdk_uuid']
        return project
    return {}

def sort_python_versions(versions_dict):
    def get_version_key(version_str):
        version_part = version_str.replace("Python-", "")
        return tuple(map(int, version_part.split('.')))
    sorted_items = sorted(
        versions_dict.items(),
        key=lambda item: get_version_key(item[1]['version']),
        reverse=True
    )
    return dict(sorted_items)


def get_python_sdk():
    from apps.envs_python_runtime.helper import get_installed as get_runtime_installed
    from apps.envs_python_installer.helper import get_installed as get_installed_installed

    python_sdk = {}
    runtime_installed = get_runtime_installed()
    installer_installed = get_installed_installed()
    if runtime_installed:
        for autoid, python in runtime_installed.items():
            path_exists = os.path.exists(python['folder'])
            python_sdk[python['folder']] = {
                'from': '压缩包安装',
                'name': python['name'],
                'install_dir': python['folder'],
                'path_exists': path_exists,
                'version': f'{python['version_major']}.{python['version_minor']}.{python['version_patch']}',
            }
    if installer_installed:
        for version, python in installer_installed.items():
            path_exists = os.path.exists(python['folder'])
            python_sdk[python['folder']] = {
                'from': '安装程序安装',
                'name': python['name'],
                'install_dir': python['folder'],
                'path_exists': path_exists,
                'version': f'{python['version_major']}.{python['version_minor']}.{python['version_patch']}',
            }
    python_sdk = sort_python_versions(python_sdk)
    return python_sdk

