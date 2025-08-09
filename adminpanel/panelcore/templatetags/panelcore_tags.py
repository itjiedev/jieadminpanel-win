import socket
from django import template


register = template.Library()


@register.simple_tag
def get_server_name():
    return socket.gethostname()

@register.simple_tag
def get_server_ip():
    return socket.gethostbyname(socket.gethostname())