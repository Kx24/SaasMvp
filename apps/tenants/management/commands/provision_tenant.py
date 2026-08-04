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

    # Con branding completo (logo, contacto, redes) en un solo paso:
    python manage.py provision_tenant mi-empresa \
        --template=servicios_profesionales --domain=miempresa.com \
        --logo=/ruta/local/logo.png --phone="+56912345678" \
        --facebook=https://facebook.com/miempresa --instagram=https://instagram.com/miempresa \
        --whatsapp=56912345678 --under-construction
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
            '--under-construction',
            action='store_true',
            default=False,
            help='Crea el cliente en modo "En construcción" (sirve la landing temporal en vez del sitio)'
        )
        parser.add_argument(
            '--logo',
            type=str,
            help='Ruta local o URL del logo a subir a Cloudinary'
        )
        parser.add_argument(
            '--phone',
            type=str,
            help='Teléfono de contacto (se guarda en ClientSettings.contact_phone)'
        )
        parser.add_argument(
            '--address',
            type=str,
            help='Dirección del cliente'
        )
        parser.add_argument(
            '--tagline',
            type=str,
            help='Frase corta / tagline del cliente'
        )
        parser.add_argument('--facebook', type=str, help='URL de Facebook')
        parser.add_argument('--instagram', type=str, help='URL de Instagram')
        parser.add_argument('--twitter', type=str, help='URL de Twitter/X')
        parser.add_argument('--linkedin', type=str, help='URL de LinkedIn')
        parser.add_argument('--youtube', type=str, help='URL de YouTube')
        parser.add_argument(
            '--whatsapp',
            type=str,
            help='Número de WhatsApp en formato internacional (ej: 56912345678)'
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

        # 4b. Aplicar branding (logo, contacto, redes sociales) si se proporcionó
        self._apply_branding(client, options)

        # 5. Crear contenido inicial
        self._create_initial_content(client, template_type)

        # 6. Copiar templates si aplica
        if options['copy_templates']:
            self._copy_templates(slug, options['source_template'])
        
        self.stdout.write(self.style.HTTP_INFO('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS(f'  TENANT "{slug}" CREADO EXITOSAMENTE'))
        self.stdout.write(self.style.HTTP_INFO('='*60 + '\n'))

        # Resumen
        self.stdout.write(f'  Slug: {client.slug}')
        self.stdout.write(f'  Nombre: {client.name}')
        self.stdout.write(f'  Email: {client.contact_email}')
        self.stdout.write(f'  Template: {template_type}')
        if client.primary_domain:
            self.stdout.write(f'  Dominio: {client.primary_domain.domain}')
        if client.mode_under_construction:
            self.stdout.write(self.style.WARNING(
                '  Modo construcción ACTIVO: se sirve la landing temporal, no el sitio.'
            ))
        self.stdout.write('')
    
    def _create_client(self, slug, options, template_type):
        """Crear el cliente en la base de datos."""
        self.stdout.write('Creando cliente...')
        
        name = options.get('name') or slug.replace('-', ' ').title()
        email = options.get('email') or f'contacto@{slug}.cl'
        
        client = Client.objects.create(
            name=name,
            slug=slug,
            company_name=name,
            contact_email=email,
            template=template_type,
            is_active=True,
            mode_under_construction=options.get('under_construction', False),
        )

        self.stdout.write(self.style.SUCCESS(f'   Cliente "{name}" creado'))
        return client
    
    def _create_domain(self, client, domain):
        """Crear dominio para el cliente."""
        self.stdout.write('Configurando dominio...')
        
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
        
        self.stdout.write(self.style.SUCCESS(f'   Dominio "{domain}" configurado'))
    
    def _apply_template_config(self, client, template_type):
        """Aplicar colores y configuración del template."""
        self.stdout.write('Aplicando configuración de template...')
        
        config = self.TEMPLATE_CONFIGS.get(template_type, {})
        colors = config.get('colors', {'primary': '#2563eb', 'secondary': '#dbeafe'})
        
        settings_obj = client.settings
        settings_obj.primary_color = colors['primary']
        settings_obj.secondary_color = colors['secondary']
        settings_obj.meta_title = client.name
        settings_obj.meta_description = f'Bienvenido a {client.name}'
        settings_obj.save()
        
        self.stdout.write(self.style.SUCCESS(f'   Colores aplicados: {colors["primary"]}'))

    def _apply_branding(self, client, options):
        """
        Aplica a ClientSettings los datos de branding ya provistos por el
        cliente (logo, teléfono, dirección, redes sociales), si se pasaron
        por línea de comandos. Todo es opcional: si no se pasa nada, no hace nada.
        """
        settings_obj = client.settings
        applied = []

        social_fields = {
            'phone': 'contact_phone',
            'address': 'address',
            'tagline': 'tagline',
            'facebook': 'facebook_url',
            'instagram': 'instagram_url',
            'twitter': 'twitter_url',
            'linkedin': 'linkedin_url',
            'youtube': 'youtube_url',
            'whatsapp': 'whatsapp_number',
        }

        for option_key, field_name in social_fields.items():
            value = options.get(option_key)
            if value:
                setattr(settings_obj, field_name, value)
                applied.append(field_name)

        logo = options.get('logo')
        if logo:
            self.stdout.write('Subiendo logo...')
            try:
                import cloudinary.uploader
                result = cloudinary.uploader.upload(
                    logo,
                    folder=f'tenants/{client.slug}/branding',
                    resource_type='image',
                )
                settings_obj.logo = result['public_id']
                applied.append('logo')
                self.stdout.write(self.style.SUCCESS('   Logo subido correctamente'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   No se pudo subir el logo: {e}'))

        if applied:
            settings_obj.save()
            self.stdout.write(self.style.SUCCESS(f'   Branding aplicado: {", ".join(applied)}'))

    def _create_initial_content(self, client, template_type):
        """Crear secciones y servicios iniciales."""
        from apps.website.models import Section, Service

        self.stdout.write('Creando contenido inicial...')
        
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
        
        self.stdout.write(f'   {len(sections)} secciones creadas')
        
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
        
        self.stdout.write(f'   {len(services)} servicios creados')
    
    def _copy_templates(self, slug, source_template):
        """Copiar carpeta de templates para el tenant."""
        self.stdout.write('Copiando templates...')
        
        templates_base = Path(settings.BASE_DIR) / 'templates' / 'tenants'
        source_path = templates_base / source_template
        dest_path = templates_base / slug
        
        if not source_path.exists():
            self.stdout.write(self.style.WARNING(f'   Template origen "{source_template}" no existe'))
            return
        
        if dest_path.exists():
            self.stdout.write(f'   Carpeta "{slug}" ya existe, omitiendo copia')
            return
        
        # Copiar carpeta completa
        shutil.copytree(source_path, dest_path)
        
        # Contar archivos copiados
        file_count = sum(1 for _ in dest_path.rglob('*.html'))
        
        self.stdout.write(self.style.SUCCESS(f'   {file_count} templates copiados a /templates/tenants/{slug}/'))