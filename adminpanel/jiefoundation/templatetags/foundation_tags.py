import json
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.html import format_html

from django.urls import reverse, reverse_lazy
from jiefoundation.utils import url_reverse_lazy

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
def menu_navbar():
    """
    顶端左侧菜单
    """
    html = ''
    file_path = settings.BASE_DIR / 'config' / 'menu_navbar.json'
    if not file_path.exists():
        return html
    with open(file_path, 'r', encoding='utf-8') as f:
        menus = json.load(f)
    if menus:
        for v in menus.values():
            html += format_html(
                '<li class="nav-item d-none d-sm-inline-block"><a href="{}" class="nav-link">{}</a></li>',
                url_reverse_lazy(v),
                v['title']
            )
    return html

@register.simple_tag
def menu_user(request_user):
    """
    用户菜单，此菜单由注册权限模块添加
    """
    user_menu_json_path = settings.BASE_DIR / 'config' / 'menu_user.json'
    html = ''
    if not user_menu_json_path.exists():
        return html
    with open(user_menu_json_path, 'r', encoding='utf-8') as f:
        menus = json.load(f)
    menu_html = ''
    if request_user:
        menu_html = '<li class="nav-item dropdown"><a class="nav-link'
        if menus: menu_html += ' dropdown-toggle'
        menu_html += '" href="#" data-toggle="dropdown" id="navbarDropdown" aria-expanded="false">'
        if request_user.name:
            menu_html += request_user.name
        else:
            menu_html += request_user.username
        menu_html += '</a>'
        if menus:
            menu_html += '<div class="dropdown-menu dropdown-menu-right p-1">'
            for menu in menus.values():
                menu_html += '<a class="dropdown-item" href="' + url_reverse_lazy(menu) + '">' + menu['title'] + '</a>'
            menu_html += '</div>'
        menu_html += '</li>'
    return mark_safe(menu_html)

@register.simple_tag
def menu_main(parent_menu, current_menu):
    menu_html = ''
    menu_main_path = settings.BASE_DIR / 'config' / 'menu_main.json'
    if not menu_main_path.exists():
        return menu_html
    with open(menu_main_path, 'r', encoding='utf-8') as f:
        menu_main = json.load(f)
        for menu_id, menu in menu_main.items():
            if not menu['children']:
                menu_html += '<li class="nav-item"><a href="'
                if 'url' in menu and menu['url']['route_name']:
                    menu_html += url_reverse_lazy(menu['url'])
                menu_html += '" class="nav-link'
                if parent_menu == menu_id: menu_html += ' active'
                menu_html += f'"><i class="nav-icon { menu["icon"] }"></i><p>{menu["title"]}</p></a>'
                menu_html += '</li>'
            else:
                menu_html += '<li class="nav-item'
                if parent_menu == menu_id: menu_html += ' menu-open'
                menu_html += '"><a href="'
                if menu['url']: menu_html += url_reverse_lazy(menu["url"])
                menu_html += '" class="nav-link'
                if parent_menu == menu_id: menu_html += ' active'
                menu_html += f'"><i class="nav-icon { menu["icon"] }"></i><p>{menu["title"]}'
                if menu['children']:
                    menu_html += '<i class="right fas fa-angle-left"></i></p></a>'
                    menu_html += '<ul class="nav nav-treeview">'
                    for child_id, child in menu['children'].items():
                        menu_html += '<li class="nav-item"><a href="'
                        if child['url']: menu_html += url_reverse_lazy(child["url"])
                        menu_html += '" class="nav-link'
                        if parent_menu == menu_id and current_menu == child_id: menu_html += ' active'
                        menu_html += f'"><i class="far fa-circle nav-icon"></i><p>{child["title"]}</p></a>'
                        menu_html += '</li>'
                    menu_html += '</ul>'
                else:
                    menu_html += '</p></a>'
                menu_html += '</li>'

    return mark_safe(menu_html)