"""
Management Command: provision_tenant
=====================================

Crea un tenant completo con:
- Cliente en DB
- Dominios asociados
- Carpeta de templates copiada del template base
- Contenido inicial (secciones, servicios)

Uso:
    python manage.py provision_tenant servelec-ingenieria --template=electricidad
    python manage.py provision_tenant mi-empresa --template=servicios_profesionales --domain=miempresa.com
"""

import os
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apps.tenants.models import Client, Domain, ClientSettings


class Command(BaseCommand):
    help = 'Provisiona un tenant completo con templates y contenido inicial'
    
    # Templates disponibles por industria
    TEMPLATE_CONFIGS = {
        'electricidad': {
            'name': 'Servicios Eléctricos',
            'services': [
                ('Instalaciones Eléctricas', '⚡', 'Instalaciones residenciales, comerciales e industriales'),
                ('Mantención Preventiva', '🔧', 'Programas de mantención para evitar fallas'),
                ('Emergencias 24/7', '🚨', 'Servicio de urgencias las 24 horas'),
                ('Certificaciones SEC', '📋', 'Certificación de instalaciones eléctricas'),
            ],
            'colors': {'primary': '#f59e0b', 'secondary': '#fef3c7'},
        },
        'construccion': {
            'name': 'Construcción',
            'services': [
                ('Construcción', '🏗️', 'Obras nuevas residenciales y comerciales'),
                ('Remodelación', '🔨', 'Ampliaciones y remodelaciones'),
                ('Obras Menores', '🧱', 'Trabajos de albañilería y terminaciones'),
                ('Proyectos', '📐', 'Diseño y gestión de proyectos'),
            ],
            'colors': {'primary': '#dc2626', 'secondary': '#fef2f2'},
        },
        'servicios_profesionales': {
            'name': 'Servicios Profesionales',
            'services': [
                ('Consultoría', '💼', 'Asesoría especializada para tu negocio'),
                ('Capacitación', '📚', 'Programas de formación y desarrollo'),
                ('Soporte', '🛠️', 'Asistencia técnica continua'),
            ],
            'colors': {'primary': '#0ea5e9', 'secondary': '#f0f9ff'},
        },
        'portafolio': {
            'name': 'Portafolio',
            'services': [
                ('Desarrollo Web', '🌐', 'Sitios web modernos y responsivos'),
                ('Diseño', '🎨', 'Identidad visual y branding'),
                ('Marketing Digital', '📱', 'Estrategias de marketing online'),
            ],
            'colors': {'primary': '#8b5cf6', 'secondary': '#f5f3ff'},
        },
    }
    
    def add_arguments(self, parser):
        parser.add_argument(
            'slug',
            type=str,
            help='Slug del tenant (ej: servelec-ingenieria)'
        )
        parser.add_argument(
            '--name',
            type=str,
            help='Nombre del cliente (si no se proporciona, se genera del slug)'
        )
        parser.add_argument(
            '--template',
            type=str,
            default='servicios_profesionales',
            choices=list(self.TEMPLATE_CONFIGS.keys()) + ['custom'],
            help='Template de industria a aplicar'
        )
        parser.add_argument(
            '--domain',
            type=str,
            help='Dominio principal (opcional)'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email de contacto'
        )
        parser.add_argument(
            '--copy-templates',
            action='store_true',
            default=True,
            help='Copiar carpeta de templates (default: True)'
        )
        parser.add_argument(
            '--no-copy-templates',
            action='store_false',
            dest='copy_templates',
            help='No copiar templates (usar _default)'
        )
        parser.add_argument(
            '--source-template',
            type=str,
            default='_default',
            help='Carpeta de templates origen (default: _default)'
        )
    
    def handle(self, *args, **options):
        slug = options['slug'].lower().strip()
        template_type = options['template']
        
        self.stdout.write(self.style.HTTP_INFO('\n' + '='*60))
        self.stdout.write(self.style.HTTP_INFO(f'  PROVISIONING TENANT: {slug}'))
        self.stdout.write(self.style.HTTP_INFO('='*60 + '\n'))
        
        # 1. Verificar que no existe
        if Client.objects.filter(slug=slug).exists():
            raise CommandError(f'El tenant "{slug}" ya existe')
        
        # 2. Crear cliente
        client = self._create_client(slug, options, template_type)
        
        # 3. Crear dominio si se proporciona
        if options.get('domain'):
            self._create_domain(client, options['domain'])
        
        # 4. Aplicar configuración de template
        self._apply_template_config(client, template_type)
        
        # 5. Crear contenido inicial
        self._create_initial_content(client, template_type)
        
        # 6. Copiar templates si aplica
        if options['copy_templates']:
            self._copy_templates(slug, options['source_template'])
        
        self.stdout.write(self.style.HTTP_INFO('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS(f'  ✅ TENANT "{slug}" CREADO EXITOSAMENTE'))
        self.stdout.write(self.style.HTTP_INFO('='*60 + '\n'))
        
        # Resumen
        self.stdout.write(f'  📋 Slug: {client.slug}')
        self.stdout.write(f'  🏢 Nombre: {client.name}')
        self.stdout.write(f'  📧 Email: {client.contact_email}')
        self.stdout.write(f'  🎨 Template: {template_type}')
        if client.primary_domain:
            self.stdout.write(f'  🌐 Dominio: {client.primary_domain.domain}')
        self.stdout.write('')
    
    def _create_client(self, slug, options, template_type):
        """Crear el cliente en la base de datos."""
        self.stdout.write('📦 Creando cliente...')
        
        name = options.get('name') or slug.replace('-', ' ').title()
        email = options.get('email') or f'contacto@{slug}.cl'
        
        client = Client.objects.create(
            name=name,
            slug=slug,
            company_name=name,
            contact_email=email,
            template=template_type,
            is_active=True,
        )
        
        self.stdout.write(self.style.SUCCESS(f'   ✅ Cliente "{name}" creado'))
        return client
    
    def _create_domain(self, client, domain):
        """Crear dominio para el cliente."""
        self.stdout.write('🌐 Configurando dominio...')
        
        domain = domain.lower().strip()
        
        # Dominio principal
        Domain.objects.create(
            client=client,
            domain=domain,
            domain_type='custom',
            is_primary=True,
            is_active=True,
            is_verified=True,
        )
        
        # Si no tiene www, agregarlo también
        if not domain.startswith('www.'):
            Domain.objects.create(
                client=client,
                domain=f'www.{domain}',
                domain_type='custom',
                is_primary=False,
                is_active=True,
                is_verified=True,
            )
        
        self.stdout.write(self.style.SUCCESS(f'   ✅ Dominio "{domain}" configurado'))
    
    def _apply_template_config(self, client, template_type):
        """Aplicar colores y configuración del template."""
        self.stdout.write('🎨 Aplicando configuración de template...')
        
        config = self.TEMPLATE_CONFIGS.get(template_type, {})
        colors = config.get('colors', {'primary': '#2563eb', 'secondary': '#dbeafe'})
        
        settings_obj = client.settings
        settings_obj.primary_color = colors['primary']
        settings_obj.secondary_color = colors['secondary']
        settings_obj.meta_title = client.name
        settings_obj.meta_description = f'Bienvenido a {client.name}'
        settings_obj.save()
        
        self.stdout.write(self.style.SUCCESS(f'   ✅ Colores aplicados: {colors["primary"]}'))
    
    def _create_initial_content(self, client, template_type):
        """Crear secciones y servicios iniciales."""
        from apps.website.models import Section, Service
        
        self.stdout.write('📝 Creando contenido inicial...')
        
        # Secciones base
        sections = [
            ('hero', f'Bienvenido a {client.name}', 'Soluciones profesionales para tu negocio'),
            ('about', 'Quiénes Somos', 'Conoce nuestra historia y valores'),
            ('contact', 'Contáctanos', 'Estamos aquí para ayudarte'),
        ]
        
        for order, (section_type, title, subtitle) in enumerate(sections, 1):
            Section.objects.create(
                client=client,
                section_type=section_type,
                title=title,
                subtitle=subtitle,
                order=order * 10,
                is_active=True,
            )
        
        self.stdout.write(f'   ✅ {len(sections)} secciones creadas')
        
        # Servicios según template
        config = self.TEMPLATE_CONFIGS.get(template_type, {})
        services = config.get('services', [
            ('Servicio 1', '⭐', 'Descripción del servicio'),
            ('Servicio 2', '✨', 'Descripción del servicio'),
        ])
        
        for order, (name, icon, description) in enumerate(services, 1):
            Service.objects.create(
                client=client,
                name=name,
                icon=icon,
                description=description,
                order=order * 10,
                is_active=True,
                is_featured=(order <= 3),
            )
        
        self.stdout.write(f'   ✅ {len(services)} servicios creados')
    
    def _copy_templates(self, slug, source_template):
        """Copiar carpeta de templates para el tenant."""
        self.stdout.write('📁 Copiando templates...')
        
        templates_base = Path(settings.BASE_DIR) / 'templates' / 'tenants'
        source_path = templates_base / source_template
        dest_path = templates_base / slug
        
        if not source_path.exists():
            self.stdout.write(self.style.WARNING(f'   ⚠️ Template origen "{source_template}" no existe'))
            return
        
        if dest_path.exists():
            self.stdout.write(f'   ℹ️ Carpeta "{slug}" ya existe, omitiendo copia')
            return
        
        # Copiar carpeta completa
        shutil.copytree(source_path, dest_path)
        
        # Contar archivos copiados
        file_count = sum(1 for _ in dest_path.rglob('*.html'))
        
        self.stdout.write(self.style.SUCCESS(f'   ✅ {file_count} templates copiados a /templates/tenants/{slug}/'))