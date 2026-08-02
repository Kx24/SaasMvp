"""
URLs principales del proyecto
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 1. Tenants (superadmin custom) — prioridad alta
    path('', include('apps.tenants.urls')),

    # 2. Django Admin
    path('superadmin/', admin.site.urls),

    # 3. Auth CANÓNICO (email + onboarding por token) — sistema único
    #    Retirado apps.website.auth_urls (client_login/client_logout).
    path('auth/', include('apps.accounts.urls')),   # app_name='accounts'

    # 4. Marketing & SEO
    path('', include('apps.marketing.urls', namespace='marketing')),

    # 5. Website (catch-all) — prioridad baja
    path('', include('apps.website.urls')),

    # 6. Orders & checkout
    path('checkout/', include('apps.orders.urls', namespace='orders')),
    path('webhook/', include('apps.orders.urls_webhooks')),
    path('onboarding/', include('apps.orders.urls_onboarding')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = "SaaS MVP - Administración"
admin.site.site_title = "SaaS Admin"
admin.site.index_title = "Panel de Administración de Tenants"