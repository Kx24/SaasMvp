"""
Management command para listar todos los tenants
VERSIÓN FINAL - Adaptada a campos reales de ClientSettings
"""
from django.core.management.base import BaseCommand
from apps.tenants.models import Client
from apps.website.models import Section, Service, ContactSubmission


class Command(BaseCommand):
    help = 'Lista todos los tenants con su información'

    def add_arguments(self, parser):
        parser.add_argument(
            '--active-only',
            action='store_true',
            help='Mostrar solo tenants activos'
        )

    def handle(self, *args, **options):
        clients = Client.objects.all().order_by('name')
        
        if options['active_only']:
            clients = clients.filter(is_active=True)
        
        total = clients.count()
        active = clients.filter(is_active=True).count()
        inactive = total - active
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(f' LISTA DE TENANTS ({total} total, {active} activos, {inactive} inactivos)')
        self.stdout.write('='*70 + '\n')
        
        if not clients.exists():
            self.stdout.write(self.style.WARNING('   No hay tenants registrados'))
            self.stdout.write('')
            return
        
        for i, client in enumerate(clients, 1):
            # Status
            status = 'ACTIVO' if client.is_active else 'INACTIVO'

            # Dominio (no existe Client.domain -- vive en el modelo Domain)
            domain = client.primary_domain.domain if client.primary_domain else '(sin dominio asignado)'

            # Contar contenido
            sections = Section.objects.filter(client=client).count()
            services = Service.objects.filter(client=client).count()
            contacts = ContactSubmission.objects.filter(client=client).count()
            new_contacts = ContactSubmission.objects.filter(
                client=client,
                status='new'
            ).count()

            # Imprimir información
            self.stdout.write(f'{i}. {client.name}')
            self.stdout.write(f'   Estado: {status}')
            self.stdout.write(f'   Dominio: {domain}')
            self.stdout.write(f'   Tema: {client.template}')
            self.stdout.write(f'   Colores: {client.settings.primary_color} / {client.settings.secondary_color}')
            self.stdout.write(f'   Contenido: {sections} secciones, {services} servicios')

            if contacts > 0:
                contact_info = f'{contacts} contactos'
                if new_contacts > 0:
                    contact_info += f' ({new_contacts} nuevos)'
                self.stdout.write(f'   Mensajes: {contact_info}')

            # Features habilitadas
            features = []
            if client.settings.enable_blog:
                features.append('Blog')
            if client.settings.enable_testimonials:
                features.append('Testimonios')
            if client.settings.enable_gallery:
                features.append('Galería')

            if features:
                self.stdout.write(f'   Features: {", ".join(features)}')

            self.stdout.write(f'   Creado: {client.created_at.strftime("%d/%m/%Y %H:%M")}')
            self.stdout.write('')

        self.stdout.write('='*70 + '\n')