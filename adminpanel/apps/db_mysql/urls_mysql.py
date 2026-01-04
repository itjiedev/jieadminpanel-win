from django.urls import path, include

from . import views_mysql as views

app_name = 'mysql_manage'

urlpatterns = [
    path('login/', views.MysqlLoginView.as_view(), name='login'),
    path('db/list/', views.DbListView.as_view(), name='db_list'),
    path('db/create/', views.DbCreateView.as_view(), name='db_create'),
    path('db/delete/', views.DbDeleteView.as_view(), name='db_delete'),
    path('db/edit/<str:db_name>/', views.DbEditView.as_view(), name='db_edit'),
]