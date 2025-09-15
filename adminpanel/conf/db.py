from pathlib import Path

DATABASES = {
    # sqlite
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': Path.joinpath(Path(__file__).resolve().parent.parent, 'data', 'db')
    # }

    # MySQL. 需要安装 mysqlcient
    # 'default': {
    #     'ENGINE': 'django.db.backends.mysql',
    #     'HOST': 'localhost',
    #     'NAME': '',
    #     'USER': '',
    #     'PASSWORD': '',
    #     'PORT': '',
    # }

    # postgresql 需要安装 psycopg
    # 'default': {
    #     'ENGINE': 'django.db.backends.postgresql',
    #     'HOST': 'localhost',
    #     'NAME': '',
    #     'USER': '',
    #     'PASSWORD': '',
    #     'PORT': '',
    # }

    # Oracle 需要安装 cx_Oracle
    # 'default': {
    #     'ENGINE': 'django.db.backends.oracle',
    #     'NAME': '',
    #     'USER': '',
    #     'PASSWORD': '',
    #     'HOST': '',
    #     'PORT': '',
    # }
}