import json
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import SEOConfig


@admin.register(SEOConfig)
class SEOConfigAdmin(admin.ModelAdmin):
    list_display = (
        "client",
        "page_key",
        "title_preview",
        "robots",
        "schema_type",
        "is_active",
        "updated_at",
    )
    list_filter = ("client", "is_active", "robots", "schema_type")
    search_fields = ("client__name", "page_key", "title", "meta_description")
    readonly_fields = (
        "google_preview",
        "og_preview",
        "char_count_title",
        "char_count_description",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "📍 Identificación",
            {
                "fields": ("client", "page_key", "is_active"),
                "description": "Define a qué tenant y página corresponde esta configuración.",
            },
        ),
        (
            "🔍 SEO Básico",
            {
                "fields": (
                    "title",
                    "char_count_title",
                    "meta_description",
                    "char_count_description",
                    "meta_keywords",
                    "google_preview",
                ),
                "description": "Controla cómo aparece tu sitio en los resultados de búsqueda de Google.",
            },
        ),
        (
            "🤖 Indexación",
            {
                "fields": ("robots", "canonical_url"),
                "description": "Controla cómo Google rastrea e indexa esta página.",
            },
        ),
        (
            "📱 Redes Sociales (Open Graph)",
            {
                "fields": ("og_title", "og_description", "og_image", "og_preview"),
                "classes": ("collapse",),
                "description": "Controla cómo se ve al compartir en Facebook, LinkedIn, WhatsApp.",
            },
        ),
        (
            "⚡ Schema.org (Rich Snippets)",
            {
                "fields": ("schema_type", "schema_json"),
                "classes": ("collapse",),
                "description": (
                    "Permite que Google muestre información enriquecida. "
                    "Si seleccionas un tipo y dejas el JSON vacío, se genera automáticamente."
                ),
            },
        ),
        (
            "✅ Verificación de Sitio",
            {
                "fields": (
                    "google_site_verification",
                    "google_verification_file",
                    "bing_site_verification",
                ),
                "classes": ("collapse",),
                "description": (
                    "Método 1 (meta tag): pega solo el valor del content de Google Search Console. "
                    "Método 2 (archivo HTML): pega solo el código sin 'google' ni '.html'. "
                    "Ej: si Google te da 'google1a2b3c4d.html', escribe solo '1a2b3c4d'."
                ),
            },
        ),
        (
            "📅 Registro",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    # ── Helpers visuales ─────────────────────────────────────────

    def title_preview(self, obj):
        if obj.title:
            length = len(obj.title)
            color = "#2ecc71" if 50 <= length <= 70 else "#e67e22" if length < 50 else "#e74c3c"
            return format_html(
                '<span style="color:{}">{}</span> <small style="color:#999">({} chars)</small>',
                color,
                obj.title[:50] + "..." if len(obj.title) > 50 else obj.title,
                length,
            )
        return format_html('<span style="color:#ccc">— sin título —</span>')
    title_preview.short_description = "Title"

    def char_count_title(self, obj):
        length = len(obj.title) if obj.title else 0
        bar_width = min(int((length / 70) * 100), 100)
        color = "#2ecc71" if 50 <= length <= 70 else "#e67e22" if length < 50 else "#e74c3c"
        msg = "✅ Ideal" if 50 <= length <= 70 else ("⚠️ Muy corto" if length < 50 else "❌ Muy largo")
        return format_html(
            '''
            <div style="margin-top:4px">
                <div style="background:#eee;border-radius:4px;height:8px;width:200px">
                    <div style="background:{};height:8px;border-radius:4px;width:{}%"></div>
                </div>
                <small style="color:{}">{} chars — {}</small>
                <small style="color:#999"> (óptimo: 50–70)</small>
            </div>
            ''',
            color, bar_width, color, length, msg,
        )
    char_count_title.short_description = "Contador Title"

    def char_count_description(self, obj):
        length = len(obj.meta_description) if obj.meta_description else 0
        bar_width = min(int((length / 160) * 100), 100)
        color = "#2ecc71" if 120 <= length <= 160 else "#e67e22" if length < 120 else "#e74c3c"
        msg = "✅ Ideal" if 120 <= length <= 160 else ("⚠️ Muy corta" if length < 120 else "❌ Muy larga")
        return format_html(
            '''
            <div style="margin-top:4px">
                <div style="background:#eee;border-radius:4px;height:8px;width:200px">
                    <div style="background:{};height:8px;border-radius:4px;width:{}%"></div>
                </div>
                <small style="color:{}">{} chars — {}</small>
                <small style="color:#999"> (óptimo: 120–160)</small>
            </div>
            ''',
            color, bar_width, color, length, msg,
        )
    char_count_description.short_description = "Contador Description"

    def google_preview(self, obj):
        title = obj.get_title() or "Título de la página"
        description = obj.meta_description or "Descripción de la página en Google..."
        try:
            domain = obj.client.domains.filter(is_primary=True).first()
            url = f"https://{domain.domain}/{obj.page_key}" if domain else "https://tudominio.cl"
        except Exception:
            url = "https://tudominio.cl"

        return format_html(
            '''
            <div style="
                font-family: arial, sans-serif;
                max-width: 600px;
                padding: 12px 16px;
                border: 1px solid #dfe1e5;
                border-radius: 8px;
                background: #fff;
                margin-top: 8px;
            ">
                <div style="font-size:12px; color:#202124; margin-bottom:2px">
                    <span style="color:#1a0dab; font-size:11px">{}</span>
                </div>
                <div style="font-size:20px; color:#1a0dab; margin-bottom:4px; line-height:1.3">
                    {}
                </div>
                <div style="font-size:14px; color:#4d5156; line-height:1.5">
                    {}
                </div>
            </div>
            ''',
            url,
            title[:70],
            description[:160],
        )
    google_preview.short_description = "Vista previa en Google"

    def og_preview(self, obj):
        title = obj.get_og_title() or "Título al compartir"
        description = obj.get_og_description() or "Descripción al compartir en redes..."
        try:
            domain = obj.client.domains.filter(is_primary=True).first()
            url = domain.domain if domain else "tudominio.cl"
        except Exception:
            url = "tudominio.cl"

        return format_html(
            '''
            <div style="
                font-family: -apple-system, sans-serif;
                max-width: 500px;
                border: 1px solid #dddfe2;
                border-radius: 8px;
                overflow: hidden;
                margin-top: 8px;
            ">
                <div style="
                    background: #f0f2f5;
                    padding: 10px 12px;
                    height: 60px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #8a8d91;
                    font-size: 12px;
                ">
                    {}
                </div>
                <div style="padding: 10px 12px; border-top: 1px solid #dddfe2">
                    <div style="font-size:12px; color:#8a8d91; text-transform:uppercase">{}</div>
                    <div style="font-size:16px; font-weight:600; color:#1c1e21; margin:2px 0">{}</div>
                    <div style="font-size:14px; color:#606770">{}</div>
                </div>
            </div>
            ''',
            "[ OG Image — 1200×630px recomendado ]",
            url,
            title[:95],
            description[:200],
        )
    og_preview.short_description = "Vista previa en redes sociales"