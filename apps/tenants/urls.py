"""
URLs para la app Tenants.
"""
from django.urls import path
from . import views

app_name = 'tenants'

urlpatterns = [
    # Vista de debug (útil para desarrollo)
    path('tenant-debug/', views.tenant_debug, name='debug'),
    
    # Lista de tenants (solo staff)
    path('tenants/', views.tenant_list, name='list'),
]