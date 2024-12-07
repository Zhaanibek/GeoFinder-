# main/urls.py
from django.urls import path
from . import views  # Импортируем views из текущего приложения

urlpatterns = [
    path('', views.index, name='index'),  # Главная страница
]
