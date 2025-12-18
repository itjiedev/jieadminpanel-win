from django.urls import path, include

from . import views

app_name = 'envs_python_installer'

urlpatterns = [
    path("check/config/", views.CheckConfigView.as_view(), name='check_config'),
    path('list/', views.PythonListView.as_view(), name='python_list'),
    path('config/', views.ConfigView.as_view(), name='config'),
    path('set/pydefault/<str:version>/', views.SetPyDefaultView.as_view(), name='set_py_default_python'),
    path('set/envdefault/<str:version>/', views.SetEnvironDefaultView.as_view(), name='set_env_default_python'),
    path('set/default/', views.ResetDefaultView.as_view(), name='reset_default_python'),
    path('uninstall/<str:version>/', views.PythonUninstallView.as_view(), name='python_uninstall'),
    path('install/form/', views.PythonInstallView.as_view(), name='python_install'),
    path('install/download/', views.PythonDownloadView.as_view(), name='python_download'),
    path('install/run/', views.RunPythonInstallView.as_view(), name='python_run_install'),

    path('package/list/', views.PackageListView.as_view(), name='package_list'),
    path('package/install/', views.PackageInstallView.as_view(), name='package_install'),
    path('package/uninstall/<str:package>/', views.PackageUninstallView.as_view(), name='package_uninstall'),
    path('package/upgrade/<str:package>/', views.PackageUpgradeView.as_view(), name='package_upgrade'),

    # path('package/list/<str:version>/', views.PackageListView.as_view(), name='package_list'),
    # path('package/install/<str:version>/', views.PackageInstallView.as_view(), name='package_install'),
    # path('package/uninstall/<str:version>/', views.PackageUninstallView.as_view(), name='package_uninstall'),
    # path('package/upgrade/<str:version>/<str:package>/', views.PackageUpgradeView.as_view(), name='package_upgrade'),

    path('clearcache/', views.ClearCacheView.as_view(), name='clear_cache'),


]
