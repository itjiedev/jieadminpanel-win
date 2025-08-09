from django.urls import path, include
from . import views

app_name = 'sharedkit'

urlpatterns = [
    path('pickerfile/<str:picker_type>/list/', views.PickerFileDirView.as_view(), name='picker_file_dir'),
    path('pickerfile/createdir/', views.CreateDirView.as_view(), name='picker_dir_create'),
    path('open/explorer/', views.OpenInExplorerView.as_view(), name='open_explorer'),
    path('open/system/', views.open_system_properties, name='open_system_properties'),
    path('open/services/', views.open_system_services, name='open_system_services'),
    path('open/cmd/', views.open_system_cmd, name='open_system_cmd'),
]