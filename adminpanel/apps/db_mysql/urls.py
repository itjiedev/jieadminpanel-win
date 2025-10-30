from django.urls import path, include

from . import views

app_name = 'db_mysql'

urlpatterns = [
    path('software/', views.SoftwareView.as_view(), name='software'),
    path('checkconfig/', views.CheckConfigView.as_view(), name='checkconfig'),
    path('config/', views.ConfigView.as_view(), name='config'),
    path('index/', views.IndexView.as_view(), name='index'),
    path('detail/<str:id>/', views.ServerDetailView.as_view(), name='detail'),
    path('install/version/list/', views.VersionListView.as_view(), name='version_list'),
    path('install/version/refresh/', views.VersionsRefreshView.as_view(), name='versions_refresh'),
    path('install/download/', views.DownloadView.as_view(), name='download'),
    path('install/unzip/', views.UnzipView.as_view(), name='unzip'),
    path("install/initialize/", views.InitializeView.as_view(), name="initialize"),
    path('check/port/', views.CheckPortView.as_view(), name='check_port'),
    path('check/service/', views.CheckServernameView.as_view(), name='check_service'),
    path('uninstall/<str:id>/', views.UninstallView.as_view(), name='uninstall'),
    path('server/status/<str:id>/<str:action>/', views.StatusActionView.as_view(), name='server_status'),
    path('install/password/<str:id>/', views.InitRootPasswordView.as_view(),name='init_root_password'),
    path('mysql/login/<str:id>/', views.LoginMysqlView.as_view(), name='login_mysql'),
    path('clean-cache/', views.CleanCacheView.as_view(), name='clean_cache'),
    path('config/edit/<str:id>/', views.EditConfigView.as_view(), name='edit_config'),
    path('import/', views.ImportView.as_view(), name='import'),
    path('import/analyze/', views.AnalyzeConfigView.as_view(), name='analyze_config'),
    path('import/service/<str:id>/', views.ImportServiceView.as_view(), name='import_service'),
]