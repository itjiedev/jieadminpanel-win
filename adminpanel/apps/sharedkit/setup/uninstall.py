import os, shutil, json
from pathlib import Path

app_name = 'sharedkit'

project_dir = Path(__file__).resolve().parent.parent.parent.parent
current_dir = os.path.dirname(__file__)
config_dir =  project_dir / 'config'


app_list_path = config_dir / 'app_list.json'
with open(app_list_path, 'r', encoding='utf-8') as f:
    app_list = json.load(f)
if f'apps.{app_name}' not in app_list:
    print(f'{app_name} 没有安装~')
    exit()

url_path = config_dir / 'urls.json'
with open(url_path, 'r', encoding='utf-8') as f:
    urls = json.load(f)
    if 'apps.sharedkit' in urls:
        urls.pop('apps.sharedkit')
with open(url_path, 'w', encoding='utf-8') as f:
    json.dump(urls, f, ensure_ascii=False, indent=4)

# app_list_path = config_dir / 'app_list.json'
with open(app_list_path, 'r', encoding='utf-8') as f:
    app_list = json.load(f)
    if 'apps.sharedkit' in app_list:
        app_list.remove('apps.sharedkit')
with open(app_list_path, 'w', encoding='utf-8') as f:
    json.dump(app_list, f, ensure_ascii=False, indent=4)

print(f'{app_name} 卸载成功~')

