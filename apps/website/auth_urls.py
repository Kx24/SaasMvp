"""
URLs de autenticación para clientes
apps/website/auth_urls.py
"""
from django.urls import path
from . import auth_views

urlpatterns = [
    path('login/', auth_views.client_login, name='client_login'),
    path('logout/', auth_views.client_logout, name='client_logout'),
]