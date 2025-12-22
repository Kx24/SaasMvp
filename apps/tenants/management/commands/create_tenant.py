"""
Management command - VERSIÓN SIMPLIFICADA QUE FUNCIONA
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from apps.tenants.models import Client
from apps.website.models import Section, Service

User = get_user_model()

class Command(BaseCommand):
    help = 'Crea un tenant completo'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str)
        parser.add_argument('domain', type=str)
        parser.add_argument('--username', type=str, default=None)
        parser.add_argument('--email', type=str, default='admin@example.com')
        parser.add_argument('--password', type=str, default='changeme123')
        parser.add_argument('--color', type=str, default='#2563eb')

    def handle(self, *args, **options):
        name = options['name']
        domain = options['domain']
        slug = slugify(name)
        username = options['username'] or f"admin_{slug}"
        
        if Client.objects.filter(domain=domain).exists():
            raise CommandError(f'Ya existe dominio: {domain}')
        if User.objects.filter(username=username).exists():
            raise CommandError(f'Ya existe usuario: {username}')
        
        self.stdout.write('🏢 Creando cliente...')
        client = Client.objects.create(name=name, slug=slug, domain=domain, is_active=True)
        
        self.stdout.write('⚙️  Configurando...')
        client.settings.primary_color = options['color']
        client.settings.secondary_color = '#1e40af'
        client.settings.save()
        
        self.stdout.write('👤 Creando usuario...')
        User.objects.create_user(username=username, email=options['email'], password=options['password'])
        
        self.stdout.write('📄 Creando secciones...')
        for i, (t, title, sub) in enumerate([
            ('hero', f'Bienvenido a {name}', 'Soluciones profesionales'),
            ('about', 'Quiénes Somos', 'Conoce nuestra empresa'),
            ('services', 'Nuestros Servicios', 'Todo lo que necesitas'),
            ('contact', 'Contáctanos', 'Estamos para ayudarte'),
        ], 1):
            Section.objects.create(client=client, section_type=t, title=title, subtitle=sub, order=i*10, is_active=True)
        
        self.stdout.write('🛠️  Creando servicios...')
        for i, (n, ic, desc, price, feat) in enumerate([
            ('Consultoría', '💼', 'Asesoramiento profesional', 'Desde $100.000', True),
            ('Desarrollo', '💻', 'Soluciones tecnológicas', 'Cotizar', True),
            ('Soporte', '🛠️', 'Asistencia técnica', '$50.000/mes', False),
        ], 1):
            Service.objects.create(
                client=client, 
                name=n, 
                icon=ic, 
                description=desc,
                full_description=desc,  # ← AGREGAR
                price_text=price, 
                order=i*10, 
                is_active=True, 
                is_featured=feat
            )
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ LISTO! Dominio: {domain} | Usuario: {username} | Pass: {options["password"]}'))