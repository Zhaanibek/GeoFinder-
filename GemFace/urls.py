# GemFace/urls.py
from django.contrib import admin
from django.urls import path, include
from main import views  # Импортируем views из приложения main

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),  # Единственная страница - главная
]
