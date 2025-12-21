"""
URLs principales del proyecto
Django Admin ahora en /superadmin/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin - SOLO para superadmin
    path('superadmin/', admin.site.urls),
    
    # Auth URLs para clientes
    path('auth/', include('apps.website.auth_urls')),  # Login/Logout custom
    
    # Website URLs (incluye dashboard)
    path('', include('apps.website.urls')),
]

# Servir media files en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Personalizar Django Admin
admin.site.site_header = "SaaS MVP - Administración"
admin.site.site_title = "SaaS Admin"
admin.site.index_title = "Panel de Administración de Tenants"