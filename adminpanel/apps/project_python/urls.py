from django.urls import path, include

from . import views

app_name = 'project_python'

urlpatterns = [
    path('index/', views.IndexView.as_view(), name='index'),
    path('software/', views.SoftWareView.as_view(), name='software'),
    path('pycharm/download/', views.PycharmDownloadView.as_view(), name='pycharm_download'),
    path('pycharm/install/', views.PycharmInstallFormView.as_view(), name='pycharm_install'),
    path('pycharm/install/run/', views.PycharmInstallRunView.as_view(), name='pycharm_install_run'),
    path('pycharm/reset/', views.PycharmResetView.as_view(), name='pycharm_reset'),
    path('pycharm/detail/', views.PycharmDetailView.as_view(), name='pycharm_detail'),
    path('pycharm/uninstall/run/', views.PycharmUninstallRunView.as_view(), name='pycharm_uninstall_run'),
    path('pycharm/run/<str:runtype>/', views.PycharmRunView.as_view(), name="pycharm_run"),
    path('pycharm/project/open/', views.PycharmProjectOpenView.as_view(), name='pycharm_project_open'),
    path('pycharm/sdk/list/', views.PycharmSdkListView.as_view(), name='pycharm_sdk_list'),
    path('project/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('project/checkpath/', views.ProjectCheckPathView.as_view(), name='project_checkpath'),
    path('project/del/', views.ProjectDelView.as_view(), name='project_del'),
    path('project/sdk/set/', views.ProjectSetSdkView.as_view(), name='project_set_sdk'),
    path('pycharm/sdk/del/', views.PycharmSdkDeleteView.as_view(), name='pycharm_sdk_del'),

    path('package/list/', views.PackageListView.as_view(), name='package_list'),
    path('package/install/', views.PackageInstallView.as_view(), name='package_install'),
    path('package/uninstall/<str:package>/', views.PackageUninstallView.as_view(), name='package_uninstall'),
    path('package/upgrade/<str:package>/', views.PackageUpgradeView.as_view(), name='package_upgrade'),

    # path('pycharm/install/get/', views.PycharmGetInstallView.as_view(), name='pycharm_get_install'),
    # path('pycharm/uninstall/', views.PycharmUninstallView.as_view(), name='pycharm_uninstall'),
    # path("pycharm/project/", views.PycharmProjectView.as_view(), name='pycharm_project'),
    # path('pycharm/sdk/', views.PycharmSdkView.as_view(), name='pycharm_sdk'),
    # path('check/pycharm/', views.CheckPycharmView.as_view(), name='check_pycharm'),

    
]