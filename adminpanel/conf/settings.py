import json
from importlib import import_module
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

from conf.secret_key import SECRET_KEY
from conf.db import *
from conf.skin import *

DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    # 'django.contrib.admin',
    # 'django.contrib.auth',
    # 'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'jiefoundation',
    'panelcore',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # 'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                # 'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]



DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
ROOT_URLCONF = 'conf.urls'
WSGI_APPLICATION = 'conf.wsgi.application'

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_L10N = False
USE_TZ = False

# DATE_FORMAT = 'Y-m-d'
# SHORT_DATE_FORMAT = 'Y/m/d'
# TIME_FORMAT = 'H:i:s'
# DATETIME_FORMAT = 'Y-m-d H:i:s'
# SHORT_DATETIME_FORMAT = 'Y-m-d H:i'

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'

# MEDIA_URL = '/media/'
# MEDIA_ROOT = BASE_DIR / 'media'

# -------------------------------------------------------------
SESSION_ENGINE = 'django.contrib.sessions.backends.file'
SESSION_FILE_PATH = BASE_DIR / 'tmp' / 'session'
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

X_FRAME_OPTIONS = 'SAMEORIGIN'
LOGIN_REDIRECT_URL = '/panelcore/home/'
#-----------------------------------------------------
with open(BASE_DIR / 'config' / 'app_list.json') as f:
    app_list = json.load(f)
    for app in app_list:
        INSTALLED_APPS.append(app)
        if Path(BASE_DIR / 'apps' / app.replace('apps.', '') / 'settings.py').exists():
            try:
                settings_module = import_module(f"{app}.settings")
                globals().update(vars(settings_module))
            except ImportError:
                pass

with open(BASE_DIR / 'config' / 'settings.json') as f:
    var_list = json.load(f)
    for var in var_list:
        globals()[var] = var_list[var]

# ---- 自定义添加的配置项 -------------------------------

SYSTEM_NAME = 'Jie开发管理面板win'
PYTHON_VERSION = "3.12.10"

PROJECT_ROOT = BASE_DIR.parent
PYTHON_ROOT = PROJECT_ROOT / 'python'
DATA_ROOT = PROJECT_ROOT / 'data'
CONFIG_ROOT = BASE_DIR / 'config'
TMP_ROOT = BASE_DIR / 'tmp'

APP_LIST_JSON = CONFIG_ROOT / 'app_list.json'
MENU_MAIN_JSON = CONFIG_ROOT / 'menu_main.json'
MENU_NAVBAR_JSON = CONFIG_ROOT / 'menu_navbar.json'
MENU_USER_JSON = CONFIG_ROOT / 'menu_user.json'
SETTINGS_JSON = CONFIG_ROOT / 'settings.json'
URLS_JSON = CONFIG_ROOT / 'urls.json'
