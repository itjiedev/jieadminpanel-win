import json
from pathlib import Path


print('安装 Python Runtime环境管理 组件...')

app_name = 'envs_python_runtime'

panel_root = Path(__file__).resolve().parent.parent.parent.parent
project_root = panel_root.parent
project_data_dir = project_root / 'data'
project_config_dir = panel_root / 'config'
app_list_path = project_config_dir / 'app_list.json'
version_json_path = Path(__file__).resolve().parent.parent / 'version.json'

#------------------------------------------------------------------------
(project_data_dir / app_name).mkdir(exist_ok=True)
print(project_data_dir / app_name)
(Path(__file__).resolve().parent.parent / 'cache').mkdir(exist_ok=True)

#------------------------------------------------------------------------
with open(app_list_path, 'r', encoding='utf-8') as f:
    main_list = json.load(f)
with open(version_json_path, 'r', encoding='utf-8') as f:
    sub_list = json.load(f)['dependency']
main_set = set(main_list)
check_dependency = []
seen = set()
for item in sub_list:
    if item not in main_set and item not in seen:
        check_dependency.append(item)
        seen.add(item)
if check_dependency:
    dependency_str = ', '.join(check_dependency)
    print(f'缺失依赖应用，请先安装 { dependency_str }')
    input('安装中止...')
    exit()
#------------------------------------------------------------------------
with open(app_list_path, 'r', encoding='utf-8') as f:
    app_list = json.load(f)
    if f'apps.{app_name}' not in app_list:
        app_list.append(f'apps.{app_name}')
with open(app_list_path, 'w', encoding='utf-8') as f:
    json.dump(app_list, f, ensure_ascii=False, indent=4)

url_path = project_config_dir / 'urls.json'
with open(url_path, 'r', encoding='utf-8') as f:
    urls = json.load(f)
    urls[f'apps.{app_name}'] = {
        "path": f"{app_name}/",
        "include": f"apps.{app_name}.urls",
        "namespace": app_name
    }
with open(url_path, 'w', encoding='utf-8') as f:
    json.dump(urls, f, ensure_ascii=False, indent=4)


menu_main_path = project_config_dir / 'menu_main.json'
this_menu = {
    "id": "envs_python",
    "title": "Python",
    "url": f"{app_name}:config_check",
    "rules": [],
    "children": {
        "category": {
            app_name: {
                "id": app_name,
                "title": "Runtime环境管理",
                "url": f"{app_name}:config_check",
                "rules": [],
            }
        }
    }
}
with open(menu_main_path, 'r', encoding='utf-8') as f:
    menu_main = json.load(f)
if 'envs_python' in menu_main['runtime_envs']['children']:
    # 检测 分类 是否只有当前这一个应用，如果只有当前应用，全部删除重建
    if (len(menu_main['runtime_envs']['children']['envs_python']['children']['category']) == 1
        and (app_name in menu_main['runtime_envs']['children']['envs_python']['children']['category'])):
        # 重建所有 python 环境下属栏目
        menu_main['runtime_envs']['children'].pop('envs_python')
        menu_main['runtime_envs']['children']['envs_python'] = this_menu
    else:
        # 否则只重建栏目分类中自己的信息
        if app_name in menu_main['runtime_envs']['children']['envs_python']['children']['category']:
            menu_main['runtime_envs']['children']['envs_python']['children']['category'].pop(app_name)
        this_menu = {
            "id": f"{app_name}",
            "title": "Runtime环境管理",
            "url": f"{app_name}:config_check",
            "rules": [],
        }
        menu_main['runtime_envs']['children']['envs_python']['children']['category'][app_name] = this_menu
else:
    menu_main['runtime_envs']['children']['envs_python'] = this_menu

with open(menu_main_path, 'w', encoding='utf-8') as f:
    json.dump(menu_main, f, ensure_ascii=False, indent=4)

user_config_json = project_data_dir / app_name / 'user_config.json'
if not user_config_json.exists():
    with open(user_config_json, 'w', encoding='utf-8') as f:
        json.dump({}, f, ensure_ascii=False, indent=4)

installed_json = project_data_dir / app_name / 'installed.json'
if not installed_json.exists():
    with open(installed_json, 'w', encoding='utf-8') as f:
        json.dump({}, f, ensure_ascii=False, indent=4)

print('安装完成。。。')