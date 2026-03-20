from django.contrib.sitemaps.views import sitemap, index as sitemap_index
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone

from .sitemaps import TenantStaticSitemap, TenantSectionsSitemap


def get_tenant_sitemaps(request):
    """
    Construye el diccionario de sitemaps para el tenant activo.
    Cada instancia recibe el request para poder filtrar por client.
    """
    return {
        "pages": TenantStaticSitemap(request),
        "sections": TenantSectionsSitemap(request),
    }


def tenant_sitemap_index(request):
    """
    Vista para /sitemap.xml
    Retorna el índice con los sub-sitemaps del tenant.
    """
    sitemaps = get_tenant_sitemaps(request)
    return sitemap_index(
        request,
        sitemaps=sitemaps,
        sitemap_url_name="marketing:sitemap_section",
    )


def tenant_sitemap_section(request, section):
    """
    Vista para /sitemap-<section>.xml
    Retorna el sitemap de una sección específica (pages, sections).
    """
    sitemaps = get_tenant_sitemaps(request)

    if section not in sitemaps:
        from django.http import Http404
        raise Http404(f"Sitemap section '{section}' not found.")

    return sitemap(
        request,
        sitemaps={section: sitemaps[section]},
    )


def tenant_sitemap_simple(request):
    """
    Vista alternativa para /sitemap.xml cuando no se quiere índice.
    Devuelve un único sitemap con todas las páginas del tenant.
    Más simple para tenants con pocos contenidos.
    """
    sitemaps = get_tenant_sitemaps(request)
    return sitemap(request, sitemaps=sitemaps)
