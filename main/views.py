# main/views.py
from django.shortcuts import render

def index(request):
    return render(request, 'main/index.html')  # Подаём шаблон для главной страницы
