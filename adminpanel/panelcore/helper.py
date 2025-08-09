import json
# from django.conf import settings

def check_dependency_app(app_list_json, version_json_path):
    """
    检查依赖的app
    :param version_json_path:
    :return:
    """
    from jiefoundation.utils import get_unique_missing_elements

    # app_list_json = settings.BASE_DIR / 'config' / 'app_list.json'
    with open(version_json_path, 'r', encoding='utf-8') as f:
        dependency_app_list = json.load(f)['dependency']
    return get_unique_missing_elements(dependency_app_list, json.load(app_list_json))
