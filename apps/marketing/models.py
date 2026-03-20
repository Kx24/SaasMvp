from django.db import models
from django.core.validators import MaxLengthValidator
from cloudinary.models import CloudinaryField


class RobotsChoices(models.TextChoices):
    INDEX_FOLLOW = "index, follow", "Index + Follow (default)"
    NOINDEX_FOLLOW = "noindex, follow", "No indexar, sí seguir links"
    INDEX_NOFOLLOW = "index, nofollow", "Indexar, no seguir links"
    NOINDEX_NOFOLLOW = "noindex, nofollow", "No indexar, no seguir links"


class SchemaTypeChoices(models.TextChoices):
    NONE = "", "Sin Schema"
    LOCAL_BUSINESS = "LocalBusiness", "Local Business"
    ORGANIZATION = "Organization", "Organización"
    SERVICE = "Service", "Servicio"
    PROFESSIONAL_SERVICE = "ProfessionalService", "Servicio Profesional"
    ELECTRICIAN = "Electrician", "Electricista"
    CONTRACTOR = "GeneralContractor", "Contratista"
    PLUMBER = "Plumber", "Gasfiter"


class SEOConfig(models.Model):
    """
    Configuración SEO por tenant y por página.
    Cubre:
      - Indexación: robots, canonical
      - Visibilidad: title, description, keywords, OG, Schema.org
      - Tracking: verification tags (Google meta tag + archivo HTML, Bing)
    """

    # Relación tenant
    client = models.ForeignKey(
        "tenants.Client",
        on_delete=models.CASCADE,
        related_name="seo_configs",
        verbose_name="Cliente / Tenant",
    )
    page_key = models.CharField(
        max_length=60,
        verbose_name="Clave de página",
        help_text="Identificador único de la página. Ej: home, services, contact, about",
    )

    # SEO básico
    title = models.CharField(
        max_length=70, blank=True, verbose_name="Title (SEO)",
        help_text="Recomendado: 50–70 caracteres.",
        validators=[MaxLengthValidator(70)],
    )
    meta_description = models.TextField(
        max_length=160, blank=True, verbose_name="Meta Description",
        help_text="Recomendado: 120–160 caracteres.",
        validators=[MaxLengthValidator(160)],
    )
    meta_keywords = models.CharField(
        max_length=255, blank=True, verbose_name="Meta Keywords",
        help_text="Separadas por comas.",
    )

    # Indexación
    robots = models.CharField(
        max_length=30, choices=RobotsChoices.choices,
        default=RobotsChoices.INDEX_FOLLOW, verbose_name="Robots",
        help_text="Controla cómo los bots de Google indexan esta página.",
    )
    canonical_url = models.URLField(
        blank=True, verbose_name="URL Canónica",
        help_text="Opcional. Usar si esta página tiene duplicados.",
    )

    # Open Graph
    og_title = models.CharField(max_length=95, blank=True, verbose_name="OG Title",
        help_text="Título al compartir en redes sociales.")
    og_description = models.TextField(max_length=200, blank=True, verbose_name="OG Description")
    og_image = CloudinaryField(
        folder="seo/og_images", blank=True, null=True,
        verbose_name="OG Image",
        help_text="Tamaño recomendado: 1200x630px.",
    )

    # Schema.org
    schema_type = models.CharField(
        max_length=50, choices=SchemaTypeChoices.choices,
        default=SchemaTypeChoices.NONE, blank=True, verbose_name="Tipo de Schema",
        help_text="Permite rich snippets en Google.",
    )
    schema_json = models.JSONField(
        blank=True, null=True, verbose_name="Schema JSON-LD",
        help_text="Personalizado. Se genera automáticamente si dejas vacío.",
    )

    # Verificación Google — Meta tag
    google_site_verification = models.CharField(
        max_length=100, blank=True,
        verbose_name="Google Verification (meta tag)",
        help_text=(
            "Método 1: Solo el valor del content. "
            "Ej: si Google te da content='abc123', escribe solo 'abc123'."
        ),
    )

    # Verificación Google — Archivo HTML
    google_verification_file = models.CharField(
        max_length=100, blank=True,
        verbose_name="Google Verification (archivo HTML)",
        help_text=(
            "Método 2: Solo el código sin 'google' ni '.html'. "
            "Ej: si Google te da 'google1a2b3c4d.html', escribe solo '1a2b3c4d'. "
            "Genera la URL: /google1a2b3c4d.html"
        ),
    )

    # Verificación Bing
    bing_site_verification = models.CharField(
        max_length=100, blank=True, verbose_name="Bing Site Verification",
    )

    # Control
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración SEO"
        verbose_name_plural = "Configuraciones SEO"
        unique_together = ("client", "page_key")
        ordering = ["client", "page_key"]
        indexes = [
            models.Index(fields=["client", "page_key", "is_active"]),
        ]

    def __str__(self):
        return f"{self.client.name} — {self.page_key}"

    def get_title(self):
        return self.title or self.client.name

    def get_og_title(self):
        return self.og_title or self.get_title()

    def get_og_description(self):
        return self.og_description or self.meta_description

    def has_schema(self):
        return bool(self.schema_type or self.schema_json)

    def get_verification_file_url(self):
        if self.google_verification_file:
            return f"/google{self.google_verification_file}.html"
        return None

    def get_schema_json(self):
        if self.schema_json:
            return self.schema_json
        if not self.schema_type:
            return None

        client = self.client
        schema = {
            "@context": "https://schema.org",
            "@type": self.schema_type,
            "name": client.name,
        }
        settings = getattr(client, "settings", None)
        if settings:
            if getattr(settings, "phone", None):
                schema["telephone"] = settings.phone
            if getattr(settings, "address", None):
                schema["address"] = {
                    "@type": "PostalAddress",
                    "addressLocality": settings.address,
                    "addressCountry": "CL",
                }
            if getattr(settings, "description", None):
                schema["description"] = settings.description
        try:
            domain = client.domains.filter(is_primary=True).first()
            if domain:
                schema["url"] = f"https://{domain.domain}"
        except Exception:
            pass
        return schema
