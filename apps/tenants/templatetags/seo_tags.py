import json
from django import template
from django.utils.safestring import mark_safe
from django.core.cache import cache

from apps.marketing.models import SEOConfig

register = template.Library()


def _get_seo_config(client, page_key):
    """
    Busca SEOConfig activo para el tenant+página.
    Usa cache por 5 minutos para no golpear la DB en cada request.
    """
    if not client:
        return None

    cache_key = f"seo_config_{client.pk}_{page_key}"
    config = cache.get(cache_key)

    if config is None:
        try:
            config = SEOConfig.objects.select_related("client__settings").get(
                client=client,
                page_key=page_key,
                is_active=True,
            )
        except SEOConfig.DoesNotExist:
            config = False  # Guardar "no existe" en cache también

        cache.set(cache_key, config, timeout=300)  # 5 minutos

    return config if config is not False else None


@register.simple_tag(takes_context=True)
def seo_tags(context, page_key="home"):
    """
    Inyecta todos los meta tags SEO en el <head>.

    Uso en template:
        {% load seo_tags %}
        {% seo_tags "home" %}

    Reemplaza:
        <title>{% block title %}{{ client.name }}{% endblock %}</title>
        <meta name="description" ...>
        <meta name="keywords" ...>
    """
    request = context.get("request")
    client = getattr(request, "client", None)

    config = _get_seo_config(client, page_key)

    # Valores con fallback al cliente
    client_name = getattr(client, "name", "") if client else ""

    if config:
        title = config.get_title() or client_name
        description = config.meta_description or ""
        keywords = config.meta_keywords or ""
        robots = config.robots or "index, follow"
        canonical = config.canonical_url or ""
        og_title = config.get_og_title() or title
        og_description = config.get_og_description() or description
        og_image = str(config.og_image.url) if config.og_image else ""
        google_verification = config.google_site_verification or ""
        bing_verification = config.bing_site_verification or ""
        schema_data = config.get_schema_json()
    else:
        # Fallback mínimo usando datos del cliente
        title = client_name
        description = ""
        keywords = ""
        robots = "index, follow"
        canonical = ""
        og_title = client_name
        og_description = ""
        og_image = ""
        google_verification = ""
        bing_verification = ""
        schema_data = None

    # Construir URL canónica automática si no está definida
    if not canonical and request:
        try:
            canonical = request.build_absolute_uri(request.path)
        except Exception:
            canonical = ""

    # Construir OG URL
    og_url = canonical

    # ── Generar HTML ─────────────────────────────────────────────
    tags = []

    # Title
    tags.append(f"<title>{_esc(title)}</title>")

    # Charset y viewport (si no están en base.html se agregan)
    # — No los duplicamos, asumimos que ya están en base.html

    # Meta básicos
    if description:
        tags.append(f'<meta name="description" content="{_esc(description)}">')
    if keywords:
        tags.append(f'<meta name="keywords" content="{_esc(keywords)}">')

    # Robots
    tags.append(f'<meta name="robots" content="{robots}">')

    # Canonical
    if canonical:
        tags.append(f'<link rel="canonical" href="{_esc(canonical)}">')

    # Open Graph
    tags.append(f'<meta property="og:type" content="website">')
    tags.append(f'<meta property="og:title" content="{_esc(og_title)}">')
    if og_description:
        tags.append(f'<meta property="og:description" content="{_esc(og_description)}">')
    if og_url:
        tags.append(f'<meta property="og:url" content="{_esc(og_url)}">')
    if og_image:
        tags.append(f'<meta property="og:image" content="{_esc(og_image)}">')
        tags.append(f'<meta property="og:image:width" content="1200">')
        tags.append(f'<meta property="og:image:height" content="630">')

    # Twitter Card
    tags.append('<meta name="twitter:card" content="summary_large_image">')
    tags.append(f'<meta name="twitter:title" content="{_esc(og_title)}">')
    if og_description:
        tags.append(f'<meta name="twitter:description" content="{_esc(og_description)}">')
    if og_image:
        tags.append(f'<meta name="twitter:image" content="{_esc(og_image)}">')

    # Verificación
    if google_verification:
        tags.append(
            f'<meta name="google-site-verification" content="{_esc(google_verification)}">'
        )
    if bing_verification:
        tags.append(
            f'<meta name="msvalidate.01" content="{_esc(bing_verification)}">'
        )

    # Schema.org JSON-LD
    if schema_data:
        schema_str = json.dumps(schema_data, ensure_ascii=False, indent=2)
        tags.append(
            f'<script type="application/ld+json">\n{schema_str}\n</script>'
        )

    return mark_safe("\n    ".join(tags))


def _esc(value):
    """Escapa comillas dobles para atributos HTML."""
    return str(value).replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
