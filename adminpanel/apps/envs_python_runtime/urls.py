from django.urls import path, include

from . import views

app_name = 'envs_python_runtime'

urlpatterns = [
    path('config/check/', views.CheckConfigView.as_view(), name='config_check'),
    path('config/form/', views.InstallConfigView.as_view(), name='config'),
    path('python/list/', views.PythonListView.as_view(), name='python_list'),
    path('versions/list/', views.VersionsListView.as_view(), name='versions_list'),
    path('versions/refresh/', views.VersionsRefreshView.as_view(), name='versions_refresh'),
    path('python/download/', views.DownloadView.as_view(), name='download'),
    path('python/install/', views.InstallView.as_view(), name='install'),
    path('python/uninstall/<str:version>/', views.UninstallView.as_view(), name='uninstall'),
    path('clearcache/', views.ClearCacheView.as_view(), name='clearcache'),
    path('default/set/<str:version>/', views.SetDefaultView.as_view(), name='default_set'),
    path('default/reset/', views.ResetDefaultView.as_view(), name='default_reset'),
    path('python/import/', views.ImportView.as_view(), name='import'),
    path('package/<str:version>/list/', views.PackageListView.as_view(), name='package_list'),
    path('package/<str:version>/install/', views.PackageInstallView.as_view(), name='package_install'),
    # path('package/search/<str:version>/', views.PackageSearchView.as_view(), name='package_search'),
    path('package/uninstall/<str:version>/', views.PackageUninstallView.as_view(), name='package_uninstall'),
    path('package/upgrade/<str:version>/<str:package>/', views.PackageUpgradeView.as_view(), name='package_upgrade')
]