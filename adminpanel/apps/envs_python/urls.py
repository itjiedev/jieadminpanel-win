from django.urls import path, include

from . import views

app_name = 'envs_python'

urlpatterns = [
    path('pypi/list/', views.PypiListView.as_view(), name='pypi_list'),
    path('pypi/set/<str:name>/', views.SetPypiDefaultView.as_view(), name='set_pypi'),
    path('package/search/<str:version>/', views.PackageSearchView.as_view(), name='package_search'),
    path('package/detail/<str:package>/<str:version>/', views.PackageDetailView.as_view(), name='package_detail'),

]