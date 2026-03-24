"""
Management command: verify_search_console

Valida que la configuración de Google Search Console está correctamente
lista antes de ir a Google a solicitar la verificación.

Uso:
    python manage.py verify_search_console --domain andesscale.com
    python manage.py verify_search_console --all
"""
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q


class Command(BaseCommand):
    help = "Valida la configuración de Google Search Console por tenant"

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--domain",
            type=str,
            help="Dominio del tenant a verificar. Ej: andesscale.com",
        )
        group.add_argument(
            "--all",
            action="store_true",
            help="Verificar todos los tenants activos",
        )

    def handle(self, *args, **options):
        from apps.tenants.models import Client
        from apps.marketing.models import SEOConfig

        if options["all"]:
            clients = Client.objects.filter(is_active=True)
        else:
            domain = options["domain"]
            try:
                from apps.tenants.models import Domain
                domain_obj = Domain.objects.select_related("client").get(domain=domain)
                clients = [domain_obj.client]
            except Exception:
                raise CommandError(f"No se encontró ningún tenant con dominio '{domain}'")

        for client in clients:
            self.stdout.write(f"\n{'='*55}")
            self.stdout.write(self.style.HTTP_INFO(f"  Tenant: {client.name}"))
            self.stdout.write(f"{'='*55}")

            # Dominio primario
            try:
                primary = client.domains.filter(is_primary=True).first()
                if primary:
                    self.stdout.write(self.style.SUCCESS(f"  ✅ Dominio primario: {primary.domain}"))
                else:
                    self.stdout.write(self.style.WARNING("  ⚠️  Sin dominio primario configurado"))
            except Exception:
                self.stdout.write(self.style.ERROR("  ❌ Error al leer dominios"))

            # SEOConfig home
            seo = SEOConfig.objects.filter(
                client=client,
                page_key="home",
                is_active=True,
            ).first()

            if not seo:
                self.stdout.write(self.style.WARNING(
                    "  ⚠️  Sin SEOConfig para 'home'. "
                    "Crea uno en /superadmin/marketing/seoconfig/add/"
                ))
                continue

            self.stdout.write(f"  SEOConfig 'home': encontrado (ID {seo.pk})")

            # Método 1: Meta tag
            if seo.google_site_verification:
                self.stdout.write(self.style.SUCCESS(
                    f"  ✅ Meta tag: configurado ({seo.google_site_verification[:20]}...)"
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    "  ⚠️  Meta tag: vacío. "
                    "Completa el campo 'Google Verification (meta tag)' en el admin."
                ))

            # Método 2: Archivo HTML
            if seo.google_verification_file:
                url = seo.get_verification_file_url()
                self.stdout.write(self.style.SUCCESS(
                    f"  ✅ Archivo HTML: configurado → {url}"
                ))
                if primary:
                    self.stdout.write(f"     URL completa: https://{primary.domain}{url}")
            else:
                self.stdout.write(self.style.WARNING(
                    "  ⚠️  Archivo HTML: vacío. "
                    "Completa el campo 'Google Verification (archivo HTML)' en el admin."
                ))

            # Resumen de estado
            has_meta = bool(seo.google_site_verification)
            has_file = bool(seo.google_verification_file)

            self.stdout.write("")
            if has_meta or has_file:
                self.stdout.write(self.style.SUCCESS(
                    "  🟢 LISTO para verificar en Google Search Console"
                ))
                self.stdout.write(
                    "     Ve a: https://search.google.com/search-console/welcome"
                )
            else:
                self.stdout.write(self.style.ERROR(
                    "  🔴 Configura al menos un método de verificación antes de ir a Google"
                ))

        self.stdout.write(f"\n{'='*55}\n")
