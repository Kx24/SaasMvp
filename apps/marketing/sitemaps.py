from django.contrib.sitemaps import Sitemap
from django.urls import reverse


# Páginas estáticas con su configuración
TENANT_STATIC_PAGES = [
    {
        "page_key": "home",
        "url_name": "home",   # sin namespace, coincide con name='home' en website/urls.py
        "priority": 1.0,
        "changefreq": "weekly",
    },
    # Descomentar cuando tengas rutas independientes para servicios y contacto:
    # {
    #     "page_key": "services",
    #     "url_name": "services",
    #     "priority": 0.9,
    #     "changefreq": "weekly",
    # },
    # {
    #     "page_key": "contact",
    #     "url_name": "contact",
    #     "priority": 0.7,
    #     "changefreq": "monthly",
    # },
]


class TenantStaticSitemap(Sitemap):
    """
    Sitemap de páginas estáticas del tenant activo.
    Genera entradas para home, servicios y contacto.
    """
    protocol = "https"

    def __init__(self, request):
        self.request = request
        self.client = getattr(request, "client", None)

    def items(self):
        """
        Retorna solo las páginas que tienen URL registrada.
        Si una URL no existe en el proyecto, se omite silenciosamente.
        """
        available = []
        for page in TENANT_STATIC_PAGES:
            try:
                reverse(page["url_name"])
                available.append(page)
            except Exception:
                pass
        return available

    def location(self, item):
        try:
            return reverse(item["url_name"])
        except Exception:
            return "/"

    def priority(self, item):
        return item["priority"]

    def changefreq(self, item):
        return item["changefreq"]

    def lastmod(self, item):
        """
        Usa la fecha de última modificación del SEOConfig si existe.
        """
        if not self.client:
            return None
        try:
            from apps.marketing.models import SEOConfig
            config = SEOConfig.objects.filter(
                client=self.client,
                page_key=item["page_key"],
                is_active=True,
            ).only("updated_at").first()
            return config.updated_at if config else None
        except Exception:
            return None


class TenantSectionsSitemap(Sitemap):
    """
    Sitemap de secciones activas del CMS del tenant.
    Solo incluye secciones que tengan una URL pública.
    """
    protocol = "https"
    changefreq = "weekly"
    priority = 0.8

    def __init__(self, request):
        self.request = request
        self.client = getattr(request, "client", None)

    def items(self):
        if not self.client:
            return []
        try:
            from apps.website.models import Section
            return Section.objects.filter(
                client=self.client,
                is_active=True,
            ).exclude(
                slug__isnull=True,
            ).exclude(
                slug="",
            ).order_by("order")
        except Exception:
            return []

    def location(self, item):
        try:
            return reverse("website:section_detail", kwargs={"slug": item.slug})
        except Exception:
            return "/"

    def lastmod(self, item):
        return getattr(item, "updated_at", None)