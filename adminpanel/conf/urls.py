# from django.contrib import admin
import json
from django.conf import settings
from django.urls import path, include

urlpatterns = [
    path('', include('panelcore.urls')),
]

with open(settings.BASE_DIR / 'config' / 'urls.json', 'r', encoding='utf-8') as f:
    apps_url = json.load(f)

for app_name, app_url in apps_url.items():
    if app_url['namespace']:
        urlpatterns.append(
            path(app_url['path'], include(app_url['include'], namespace=app_url['namespace']))
        )
    else:
        urlpatterns.append(
            path(app_url['path'], include(app_url['include']))
        )