from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
import cloudinary.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tenants", "0009_alter_client_plan"),
    ]

    operations = [
        migrations.CreateModel(
            name="SEOConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("page_key", models.CharField(
                    help_text="Identificador único de la página. Ej: home, services, contact, about",
                    max_length=60,
                    verbose_name="Clave de página",
                )),
                ("title", models.CharField(
                    blank=True,
                    help_text="Recomendado: 50–70 caracteres. Aparece en el tab del navegador y en Google.",
                    max_length=70,
                    validators=[django.core.validators.MaxLengthValidator(70)],
                    verbose_name="Title (SEO)",
                )),
                ("meta_description", models.TextField(
                    blank=True,
                    help_text="Recomendado: 120–160 caracteres. Texto que aparece bajo el título en Google.",
                    max_length=160,
                    validators=[django.core.validators.MaxLengthValidator(160)],
                    verbose_name="Meta Description",
                )),
                ("meta_keywords", models.CharField(
                    blank=True,
                    help_text="Separadas por comas. Ej: electricista, instalaciones eléctricas, Puerto Montt",
                    max_length=255,
                    verbose_name="Meta Keywords",
                )),
                ("robots", models.CharField(
                    choices=[
                        ("index, follow", "Index + Follow (default)"),
                        ("noindex, follow", "No indexar, sí seguir links"),
                        ("index, nofollow", "Indexar, no seguir links"),
                        ("noindex, nofollow", "No indexar, no seguir links"),
                    ],
                    default="index, follow",
                    help_text="Controla cómo los bots de Google indexan esta página.",
                    max_length=30,
                    verbose_name="Robots",
                )),
                ("canonical_url", models.URLField(
                    blank=True,
                    help_text="Opcional. Usar si esta página tiene duplicados.",
                    verbose_name="URL Canónica",
                )),
                ("og_title", models.CharField(
                    blank=True,
                    help_text="Título que aparece al compartir en Facebook, LinkedIn, WhatsApp.",
                    max_length=95,
                    verbose_name="OG Title",
                )),
                ("og_description", models.TextField(
                    blank=True,
                    help_text="Descripción al compartir en redes sociales.",
                    max_length=200,
                    verbose_name="OG Description",
                )),
                ("og_image", cloudinary.models.CloudinaryField(
                    blank=True,
                    null=True,
                    verbose_name="OG Image",
                )),
                ("schema_type", models.CharField(
                    blank=True,
                    choices=[
                        ("", "Sin Schema"),
                        ("LocalBusiness", "Local Business"),
                        ("Organization", "Organización"),
                        ("Service", "Servicio"),
                        ("ProfessionalService", "Servicio Profesional"),
                        ("Electrician", "Electricista"),
                        ("GeneralContractor", "Contratista"),
                        ("Plumber", "Gasfiter"),
                    ],
                    default="",
                    max_length=50,
                    verbose_name="Tipo de Schema",
                )),
                ("schema_json", models.JSONField(
                    blank=True,
                    help_text="JSON-LD personalizado. Se genera automáticamente si dejas vacío.",
                    null=True,
                    verbose_name="Schema JSON-LD",
                )),
                ("google_site_verification", models.CharField(
                    blank=True,
                    help_text="Solo el valor del atributo content del meta tag de Google Search Console.",
                    max_length=100,
                    verbose_name="Google Site Verification",
                )),
                ("bing_site_verification", models.CharField(
                    blank=True,
                    max_length=100,
                    verbose_name="Bing Site Verification",
                )),
                ("is_active", models.BooleanField(
                    default=True,
                    help_text="Desactivar para que esta página use los valores por defecto del tenant.",
                    verbose_name="Activo",
                )),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("client", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="seo_configs",
                    to="tenants.client",
                    verbose_name="Cliente / Tenant",
                )),
            ],
            options={
                "verbose_name": "Configuración SEO",
                "verbose_name_plural": "Configuraciones SEO",
                "ordering": ["client", "page_key"],
            },
        ),
        migrations.AddConstraint(
            model_name="seoconfig",
            constraint=models.UniqueConstraint(
                fields=["client", "page_key"],
                name="unique_seo_per_page",
            ),
        ),
        migrations.AddIndex(
            model_name="seoconfig",
            index=models.Index(
                fields=["client", "page_key", "is_active"],
                name="marketing_seo_client_page_idx",
            ),
        ),
    ]
