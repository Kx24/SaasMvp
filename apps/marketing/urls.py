from django.urls import path, re_path
from . import views_sitemap
from . import views_robots
from . import views_verification

app_name = "marketing"

urlpatterns = [
    # ── Sitemap ──────────────────────────────────────────────────
    path(
        "sitemap.xml",
        views_sitemap.tenant_sitemap_simple,
        name="sitemap",
    ),
    path(
        "sitemap-<str:section>.xml",
        views_sitemap.tenant_sitemap_section,
        name="sitemap_section",
    ),

    # ── Robots.txt ───────────────────────────────────────────────
    path(
        "robots.txt",
        views_robots.robots_txt,
        name="robots_txt",
    ),

    # ── Google Search Console — Archivo HTML ─────────────────────
    # Google visita /google<code>.html para verificar el dominio
    re_path(
        r"^google(?P<code>[a-zA-Z0-9_-]+)\.html$",
        views_verification.google_verification_file,
        name="google_verification",
    ),
]
