import os, json
from pathlib import Path

print('安装 共享工具 组件...')

project_root = Path(__file__).resolve().parent.parent.parent.parent
current_dir = os.path.dirname(__file__)
config_root =  project_root / 'config'
app_list_json = config_root / 'app_list.json'

version_json = Path(__file__).resolve().parent.parent / 'version.json'

with open(app_list_json, 'r', encoding='utf-8') as f:
    main_list = json.load(f)
with open(version_json, 'r', encoding='utf-8') as f:
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
    input('安装中止....')
    exit()

with open(app_list_json, 'r', encoding='utf-8') as f:
    app_list = json.load(f)
    if 'apps.sharedkit' not in app_list:
        app_list.append('apps.sharedkit')
with open(app_list_json, 'w', encoding='utf-8') as f:
    json.dump(app_list, f, ensure_ascii=False, indent=4)

url_path = config_root / 'urls.json'
with open(url_path, 'r', encoding='utf-8') as f:
    urls = json.load(f)
    urls['apps.sharedkit'] = {
        "path": "sharedkit/",
        "include": "apps.sharedkit.urls",
        "namespace": "sharedkit"
    }
with open(url_path, 'w', encoding='utf-8') as f:
    json.dump(urls, f, ensure_ascii=False, indent=4)

print('安装完成...')