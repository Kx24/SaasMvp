"""
Management command para actualizar el dominio principal de un tenant.

Actualiza (o crea, si no existe) el Domain marcado como is_primary=True
del cliente indicado. No toca a otros tenants -- cada uno tiene su propio
dominio, no se comparte uno solo entre todos (#FLOW-01: la versión previa
tomaba RENDER_EXTERNAL_HOSTNAME y sobreescribía el dominio de TODOS los
clientes con el mismo valor, además de escribir en Client.domain, un
campo que no existe -- el dominio vive en el modelo Domain -- así que
en la práctica no hacía nada salvo el riesgo de mezclar dominios si el
campo hubiera existido).
"""
from django.core.management.base import BaseCommand, CommandError

from apps.tenants.models import Client, Domain


class Command(BaseCommand):
    help = 'Actualiza el dominio principal de un tenant específico'

    def add_arguments(self, parser):
        parser.add_argument(
            'slug',
            type=str,
            help='Slug del tenant a actualizar (ej: servelec-ingenieria)'
        )
        parser.add_argument(
            '--domain',
            type=str,
            required=True,
            help='Nuevo dominio principal (ej: miempresa.cl)'
        )

    def handle(self, *args, **options):
        slug = options['slug'].lower().strip()
        new_domain = options['domain'].lower().strip()

        try:
            client = Client.objects.get(slug=slug)
        except Client.DoesNotExist:
            raise CommandError(f'El tenant "{slug}" no existe')

        primary = client.primary_domain

        if primary:
            old_domain = primary.domain
            primary.domain = new_domain
            primary.is_primary = True
            primary.is_active = True
            primary.save()
            self.stdout.write(self.style.SUCCESS(
                f'Cliente "{client.name}": dominio actualizado de "{old_domain}" a "{new_domain}"'
            ))
        else:
            Domain.objects.create(
                client=client,
                domain=new_domain,
                domain_type='custom',
                is_primary=True,
                is_active=True,
                is_verified=True,
            )
            self.stdout.write(self.style.SUCCESS(
                f'Cliente "{client.name}": dominio "{new_domain}" creado (no tenía ninguno)'
            ))
