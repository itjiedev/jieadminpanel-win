import json
from django import template
from django.conf import settings
from django.utils.html import mark_safe

from django.urls import reverse, reverse_lazy

register = template.Library()

@register.simple_tag
def replace_str(value, old_str, new_str):
    """
    模板标签：替换字符串中的指定内容
    使用方式: {% replace_str value "old_str" "new_str" %}
    """
    if not isinstance(value, str):
        return value
    return value.replace(old_str, new_str)


@register.simple_tag
def get_settings(value):
    return getattr(settings, value.upper(), "")


@register.simple_tag
def menu_user(request):
    user_menu_json_path = settings.BASE_DIR / 'config' / 'menu_user.json'
    with open(user_menu_json_path, 'r', encoding='utf-8') as f:
        menus = json.load(f)
    menu_html = ''
    # 判断当前用户是否登录
    if request.user.is_authenticated:
        for menu in menus:
            menu_html += '<a class="dropdown-item" href="' + reverse(menu['url']) + '">' + menu['title'] + '</a>'
            # menu_html += '<div class="dropdown-divider"></div>'
    return mark_safe(menu_html)


@register.simple_tag()
def menu_main(parent_menu, current_menu):
    menu_html = ''
    menu_main_path = settings.BASE_DIR / 'config' / 'menu_main.json'

    with open(menu_main_path, 'r', encoding='utf-8') as f:
        menu_main = json.load(f)
        for menu_id, menu in menu_main.items():
            if 'children' not in menu:
                menu_html += '<li class="nav-item"><a href="'
                if menu['url']: menu_html += reverse(menu["url"])
                menu_html += '" class="nav-link'
                if parent_menu == menu_id: menu_html += ' active'
                menu_html += f'"><i class="nav-icon { menu["icon"] }"></i><p>{menu["title"]}</p></a>'
                menu_html += '</li>'
            elif menu['children']:
                menu_html += '<li class="nav-item'
                if parent_menu == menu_id: menu_html += ' menu-open'
                menu_html += '"><a href="'
                if menu['url']: menu_html += reverse(menu["url"])
                menu_html += '" class="nav-link'
                if parent_menu == menu_id: menu_html += ' active'
                menu_html += f'"><i class="nav-icon { menu["icon"] }"></i><p>{menu["title"]}'
                if menu['children']:
                    menu_html += '<i class="right fas fa-angle-left"></i></p></a>'
                    menu_html += '<ul class="nav nav-treeview">'
                    for child_id, child in menu['children'].items():
                        menu_html += '<li class="nav-item"><a href="'
                        if child['url']: menu_html += reverse(child["url"])
                        menu_html += '" class="nav-link'
                        if parent_menu == menu_id and current_menu == child_id: menu_html += ' active'
                        menu_html += f'"><i class="far fa-circle nav-icon"></i><p>{child["title"]}</p></a>'
                        menu_html += '</li>'
                    menu_html += '</ul>'
                else:
                    menu_html += '</p></a>'
                menu_html += '</li>'

    return mark_safe(menu_html)