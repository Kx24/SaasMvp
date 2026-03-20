from django.http import HttpResponse


# Rutas que nunca deben indexar los bots
DISALLOW_PATHS = [
    "/dashboard/",
    "/superadmin/",
    "/auth/",
    "/checkout/",
    "/onboarding/",
    "/webhook/",
]


def robots_txt(request):
    """
    Genera robots.txt dinámico por tenant.

    - Lee request.client inyectado por TenantMiddleware
    - Construye la URL del sitemap con el dominio real del tenant
    - Bloquea rutas privadas comunes a todos los tenants
    - Retorna text/plain (formato requerido por Google)
    """
    client = getattr(request, "client", None)

    # Construir URL base del tenant
    # En producción: https://andesscale.com
    # En local:      http://andesscale.localhost:8000
    try:
        domain = None
        if client:
            domain = client.domains.filter(is_primary=True).first()

        if domain:
            scheme = "https" if not request.get_host().startswith("localhost") else "http"
            base_url = f"{scheme}://{domain.domain}"
        else:
            base_url = request.build_absolute_uri("/").rstrip("/")
    except Exception:
        base_url = request.build_absolute_uri("/").rstrip("/")

    sitemap_url = f"{base_url}/sitemap.xml"

    # Construir contenido
    lines = [
        "User-agent: *",
        "Allow: /",
        "",
    ]

    # Rutas bloqueadas
    for path in DISALLOW_PATHS:
        lines.append(f"Disallow: {path}")

    # Sitemap
    lines += [
        "",
        f"Sitemap: {sitemap_url}",
    ]

    content = "\n".join(lines)

    return HttpResponse(content, content_type="text/plain; charset=utf-8")
