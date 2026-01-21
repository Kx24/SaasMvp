"""
URLs principales del proyecto
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 1. URLs de Tenants (Custom Superadmin) - PRIORIDAD ALTA
    # Las ponemos primero para que 'superadmin/nuevo/' no sea "comido" por el admin de Django
    path('', include('apps.tenants.urls')),

    # 2. Django Admin (Panel clásico) - PRIORIDAD MEDIA
    # Ahora vive en /superadmin/, pero solo responderá si no hubo coincidencia arriba
    path('superadmin/', admin.site.urls),
    
    # 3. Auth URLs para clientes
    path('auth/', include('apps.website.auth_urls')),  # Login/Logout custom
    
    # 4. Website URLs (Catch-all) - PRIORIDAD BAJA
    # Al final porque suele tener rutas genéricas
    path('', include('apps.website.urls')),

    # Orders & Checkout
    path('checkout/', include('apps.orders.urls', namespace='orders')),
    
    # Webhooks (sin namespace para URLs públicas simples)
    path('webhook/', include('apps.orders.urls_webhooks')),

    # ===== ONBOARDINGS =====
    path('onboarding/', include('apps.orders.urls_onboarding')),
    # ========================================
]

# Servir media files en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Personalizar Django Admin
admin.site.site_header = "SaaS MVP - Administración"
admin.site.site_title = "SaaS Admin"
admin.site.index_title = "Panel de Administración de Tenants"