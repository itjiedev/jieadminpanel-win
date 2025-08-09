import json
import os, shutil
from pathlib import Path

app_name = 'envs_python_installer'
start_url = f"{app_name}:python_list"

panel_root = Path(__file__).resolve().parent.parent.parent.parent
project_root = panel_root.parent
project_config_dir = panel_root / 'config'

app_list_json = project_config_dir / 'app_list.json'
with open(app_list_json, 'r', encoding='utf-8') as f:
    app_list = json.load(f)

if f'apps.{app_name}' not in app_list:
    print(f'{app_name} 没有安装~')
    exit()

# ----------------------------------------------
menu_main_json = project_config_dir / 'menu_main.json'
with open(menu_main_json, 'r', encoding='utf-8') as f:
    menu_main = json.load(f)
    # 如果只有当前一个功能模块，彻底删除python环境管理菜单
if app_name in menu_main['runtime_envs']['children']['envs_python']['children']['category']:
    if len(menu_main['runtime_envs']['children']['envs_python']['children']['category']) == 1:
        menu_main['runtime_envs']['children'].pop('envs_python')
    else:
        envs_python_url = menu_main['runtime_envs']['children']['envs_python']['url']
        next_category = {}
        if envs_python_url ==  start_url:
            tag_index = 0
            for name, item in menu_main['runtime_envs']['children']['envs_python']['children']['category'].items():
                if tag_index == 1:
                    next_category = item
                    break
                tag_index += 1
            menu_main['runtime_envs']['children']['envs_python']['url'] = next_category['url']
        menu_main['runtime_envs']['children']['envs_python']['children']['category'].pop(app_name)
with open(menu_main_json, 'w', encoding='utf-8') as f:
    json.dump(menu_main, f, indent=4)

# ----------------------------------------------
urls_json = project_config_dir / 'urls.json'
with open(urls_json, 'r', encoding='utf-8') as f:
    urls = json.load(f)
if f'apps.{app_name}' in urls:
    urls.pop(f'apps.{app_name}')
with open(urls_json, 'w', encoding='utf-8') as f:
    json.dump(urls, f, indent=4)

# ------------- 卸载应用注册 -----------------------
app_list_json = project_config_dir / 'app_list.json'
with open(app_list_json, 'r', encoding='utf-8') as f:
    app_list = json.load(f)
if f'apps.{app_name}' in app_list:
    app_list.remove(f'apps.{app_name}')
with open(app_list_json, 'w', encoding='utf-8') as f:
    json.dump(app_list, f, indent=4)

print('卸载完成。。')