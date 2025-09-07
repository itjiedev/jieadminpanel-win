import os, json
from pathlib import Path

print('安装 python环境管理基础（envs_python） 组件...')

app_name = 'envs_python'

project_dir = Path(__file__).resolve().parent.parent.parent.parent
config_dir =  project_dir / 'config'
app_list_path = config_dir / 'app_list.json'

with open(app_list_path, 'r', encoding='utf-8') as f:
    main_list = json.load(f)

sub_list = ['apps.sharedkit']

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

with open(app_list_path, 'r', encoding='utf-8') as f:
    app_list = json.load(f)
    if 'apps.envs_python' not in app_list:
        app_list.append(f'apps.{app_name}')
with open(app_list_path, 'w', encoding='utf-8') as f:
    json.dump(app_list, f, ensure_ascii=False, indent=4)

url_path = config_dir / 'urls.json'
with open(url_path, 'r', encoding='utf-8') as f:
    urls = json.load(f)
    urls[f'apps.{app_name}'] = {
        "path": f"{app_name}/",
        "include": f"apps.{app_name}.urls",
        "namespace": app_name
    }
with open(url_path, 'w', encoding='utf-8') as f:
    json.dump(urls, f, ensure_ascii=False, indent=4)


print('安装完成。。。')

