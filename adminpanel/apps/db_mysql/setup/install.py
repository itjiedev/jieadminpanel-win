import json
from pathlib import Path

print('安装 数据库MySQL 管理组件')

app_name = 'db_mysql'

panel_root = Path(__file__).resolve().parent.parent.parent.parent
project_root = panel_root.parent
project_data_dir = project_root / 'data'
project_config_dir = panel_root / 'config'
app_list_path = project_config_dir / 'app_list.json'
version_json_path = Path(__file__).resolve().parent.parent / 'version.json'

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

(project_data_dir / app_name).mkdir(exist_ok=True)
(Path(__file__).resolve().parent.parent / 'cache').mkdir(exist_ok=True)

with open(app_list_path, 'w', encoding='utf-8') as f:
    json.dump(main_list, f, indent=4)

user_config_json = project_data_dir / app_name / 'config.json'
if not user_config_json.exists():
    with open(user_config_json, 'w', encoding='utf-8') as f:
        json.dump({'install_folder': ''}, f, ensure_ascii=False, indent=4)

installed_json = project_data_dir / app_name / 'installed.json'
if not installed_json.exists():
    with open(installed_json, 'w', encoding='utf-8') as f:
        json.dump({}, f, ensure_ascii=False, indent=4)

print(' 数据库MySQL管理 组件 安装完成。。。')