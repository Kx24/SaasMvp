"""
Management command: alta de un dominio de preview/contingencia para un
tenant existente (#PREV-04).

Crea <slug>.{PREVIEW_DOMAIN} con is_preview=True. Idempotente -- no
duplica el Domain si ya existe, y nunca toca el dominio primario actual
del cliente (a diferencia de update_domain.py, que sí lo reemplaza). Si
el cliente no tiene ningún dominio todavía, Domain.save() lo marca
is_primary=True automáticamente (mismo comportamiento que cualquier otro
alta de dominio) -- en ese caso el preview ES el dominio público real
(Plan Esencial sin dominio propio), no solo un alias.

Decisión de #PREV-00 (wildcard vs. alta manual) todavía pendiente: este
comando no la asume. Si ".{PREVIEW_DOMAIN}" ya está en ALLOWED_HOSTS
(wildcard configurado), no imprime nada más. Si no, imprime los pasos
manuales que faltan -- ver Documentacion/Procedimiento_Nuevo_Tenant.md
§4 "Contingencia sin acceso a NIC". El comando se pone al día solo
cuando se decida el wildcard, sin tocar este archivo.
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.tenants.models import Client, Domain


class Command(BaseCommand):
    help = 'Alta (idempotente) del dominio de preview/contingencia de un tenant'

    def add_arguments(self, parser):
        parser.add_argument(
            'slug',
            type=str,
            help='Slug del tenant (ej: servelec-ingenieria)',
        )

    def handle(self, *args, **options):
        slug = options['slug'].lower().strip()

        preview_domain = getattr(settings, 'PREVIEW_DOMAIN', None)
        if not preview_domain:
            raise CommandError(
                'PREVIEW_DOMAIN no está configurado en este entorno '
                '(settings.PREVIEW_DOMAIN) -- ver config/settings/production.py.'
            )

        try:
            client = Client.objects.get(slug=slug)
        except Client.DoesNotExist:
            raise CommandError(f'El tenant "{slug}" no existe')

        target = f'{client.slug}.{preview_domain}'

        domain, created = Domain.objects.get_or_create(
            domain=target,
            defaults={
                'client': client,
                'domain_type': 'subdomain',
                'is_active': True,
                'is_verified': True,
                'is_preview': True,
            },
        )

        if created:
            suffix = ' (primario: el cliente no tenía otro dominio)' if domain.is_primary else ''
            self.stdout.write(self.style.SUCCESS(
                f'Cliente "{client.name}": dominio de preview "{target}" creado{suffix}'
            ))
        else:
            if domain.client_id != client.id:
                raise CommandError(
                    f'"{target}" ya existe pero pertenece a otro cliente '
                    f'({domain.client.slug})'
                )
            if not domain.is_preview:
                domain.is_preview = True
                domain.save(update_fields=['is_preview'])
            self.stdout.write(self.style.WARNING(
                f'Cliente "{client.name}": "{target}" ya existía, sin cambios'
            ))

        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        wildcard_ready = f'.{preview_domain}' in allowed_hosts
        if not wildcard_ready:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                f'Faltan los pasos manuales para que "{target}" resuelva de verdad '
                '(Documentacion/Procedimiento_Nuevo_Tenant.md §4, '
                '"Contingencia sin acceso a NIC"):'
            ))
            self.stdout.write(
                f'  1. render.yaml: agregar "{target}" a EXTRA_DOMAINS (los 3 servicios) y deployar.'
            )
            self.stdout.write(
                f'  2. Cloudflare, zona {preview_domain}: '
                f'CNAME {client.slug} -> saasmvp-kajv.onrender.com, DNS only.'
            )
            self.stdout.write(
                f'  3. Render -> Custom Domains -> agregar "{target}" y esperar el certificado.'
            )

        self.stdout.write('')
        self.stdout.write(
            f'Verificar con: python manage.py check_tenant_setup {client.slug} '
            '--check-dns --settings=config.settings.production'
        )
