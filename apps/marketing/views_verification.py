from django.http import HttpResponse, Http404


def google_verification_file(request, code):
    """
    Sirve el archivo de verificación HTML de Google Search Console.

    Google visita: /google<code>.html
    y espera encontrar: google-site-verification: <code>

    El código se valida contra el SEOConfig del tenant activo,
    asegurando que cada tenant solo pueda verificar su propio dominio.

    Uso:
        En Google Search Console → Verificar propiedad → Archivo HTML
        Google te da: google1a2b3c4d.html
        Tú ingresas en SEOConfig.google_verification_file: 1a2b3c4d
    """
    client = getattr(request, "client", None)

    if not client:
        raise Http404("Tenant no encontrado.")

    # Buscar el código en cualquier SEOConfig activo del tenant
    # (no importa el page_key, el archivo de verificación es a nivel de dominio)
    try:
        from apps.marketing.models import SEOConfig
        config = SEOConfig.objects.filter(
            client=client,
            google_verification_file=code,
            is_active=True,
        ).first()
    except Exception:
        config = None

    if not config:
        raise Http404("Archivo de verificación no encontrado.")

    # Contenido exacto que Google espera
    content = f"google-site-verification: google{code}.html"

    return HttpResponse(content, content_type="text/html; charset=utf-8")
