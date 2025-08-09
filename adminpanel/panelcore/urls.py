from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.HomeView.as_view()),
    path('home/index/', views.HomeView.as_view(), name='home'),
]
