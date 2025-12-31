"""
Management Command: setup_production
====================================

Configura los datos iniciales necesarios para producción.
Este comando es idempotente (puede ejecutarse múltiples veces sin problemas).

Uso:
    python manage.py setup_production
    
    # Con opciones:
    python manage.py setup_production --domain=miapp.com --tenant=miempresa
"""

import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


class Command(BaseCommand):
    help = 'Configura datos iniciales para producción (idempotente)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            default=None,
            help='Dominio principal a configurar'
        )
        parser.add_argument(
            '--tenant',
            type=str,
            default='servelec',
            help='Slug del tenant por defecto'
        )
        parser.add_argument(
            '--superuser',
            type=str,
            default='admin',
            help='Username del superusuario'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@example.com',
            help='Email del superusuario'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('\n' + '='*60))
        self.stdout.write(self.style.HTTP_INFO('  SETUP PRODUCCIÓN - SaaS MVP'))
        self.stdout.write(self.style.HTTP_INFO('='*60 + '\n'))
        
        # Obtener dominio de Render o usar el proporcionado
        domain = options['domain']
        if not domain:
            domain = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')
        
        tenant_slug = options['tenant']
        
        self._setup_tenant(tenant_slug, domain)
        self._setup_domains(tenant_slug, domain)
        self._setup_superuser(options['superuser'], options['email'])
        self._setup_initial_content(tenant_slug)
        
        self.stdout.write(self.style.HTTP_INFO('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('  ✅ SETUP COMPLETADO'))
        self.stdout.write(self.style.HTTP_INFO('='*60 + '\n'))
    
    def _setup_tenant(self, slug, domain):
        """Crear o verificar tenant principal."""
        from apps.tenants.models import Client
        
        self.stdout.write('🏢 Configurando tenant...')
        
        client, created = Client.objects.get_or_create(
            slug=slug,
            defaults={
                'name': slug.replace('-', ' ').title(),
                'company_name': slug.replace('-', ' ').title(),
                'contact_email': f'contacto@{domain}',
                'contact_phone': '',
                'is_active': True,
            }
        )
        
        if created:
            # Configurar settings
            client.settings.primary_color = '#2563eb'
            client.settings.secondary_color = '#1e40af'
            client.settings.meta_title = client.name
            client.settings.meta_description = f'Bienvenido a {client.name}'
            client.settings.save()
            self.stdout.write(self.style.SUCCESS(f'   ✅ Tenant "{slug}" creado'))
        else:
            self.stdout.write(f'   ℹ️  Tenant "{slug}" ya existe')
        
        return client
    
    def _setup_domains(self, tenant_slug, primary_domain):
        """Configurar dominios para el tenant."""
        from apps.tenants.models import Client, Domain
        
        self.stdout.write('🌐 Configurando dominios...')
        
        try:
            client = Client.objects.get(slug=tenant_slug)
        except Client.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'   ❌ Tenant {tenant_slug} no existe'))
            return
        
        # Lista de dominios a configurar
        domains_to_create = [
            (primary_domain, 'primary', True),
            ('localhost', 'development', False),
            ('127.0.0.1', 'development', False),
        ]
        
        # Agregar dominio de Render si es diferente
        render_domain = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
        if render_domain and render_domain != primary_domain:
            domains_to_create.append((render_domain, 'subdomain', False))
        
        for domain_name, domain_type, is_primary in domains_to_create:
            domain, created = Domain.objects.get_or_create(
                domain=domain_name,
                defaults={
                    'client': client,
                    'domain_type': domain_type,
                    'is_primary': is_primary,
                    'is_active': True,
                    'is_verified': True,
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'   ✅ Dominio "{domain_name}" creado'))
            else:
                # Asegurar que está vinculado al cliente correcto
                if domain.client_id != client.id:
                    domain.client = client
                    domain.save()
                    self.stdout.write(f'   🔄 Dominio "{domain_name}" actualizado')
                else:
                    self.stdout.write(f'   ℹ️  Dominio "{domain_name}" ya existe')
        
        # Mostrar resumen
        self.stdout.write('\n   📋 Dominios configurados:')
        for d in Domain.objects.filter(client=client):
            status = '✓' if d.is_active else '✗'
            self.stdout.write(f'      {status} {d.domain}')
    
    def _setup_superuser(self, username, email):
        """Crear superusuario si no existe."""
        self.stdout.write('👤 Configurando superusuario...')
        
        if User.objects.filter(is_superuser=True).exists():
            superuser = User.objects.filter(is_superuser=True).first()
            self.stdout.write(f'   ℹ️  Superusuario ya existe: {superuser.username}')
            return
        
        # Password desde variable de entorno o default
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123456')
        
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        
        self.stdout.write(self.style.SUCCESS(f'   ✅ Superusuario "{username}" creado'))
        self.stdout.write(self.style.WARNING(f'   ⚠️  Password: {password} (cambiar en producción!)'))
    
    def _setup_initial_content(self, tenant_slug):
        """Crear contenido inicial si no existe."""
        from apps.tenants.models import Client
        from apps.website.models import Section, Service
        
        self.stdout.write('📝 Verificando contenido inicial...')
        
        try:
            client = Client.objects.get(slug=tenant_slug)
        except Client.DoesNotExist:
            return
        
        # Secciones
        sections_count = Section.objects.filter(client=client).count()
        if sections_count == 0:
            sections = [
                ('hero', 'Bienvenido', 'Soluciones profesionales', 10),
                ('about', 'Quiénes Somos', 'Nuestra historia', 20),
                ('contact', 'Contáctanos', 'Estamos para ayudarte', 30),
            ]
            for section_type, title, subtitle, order in sections:
                Section.objects.create(
                    client=client,
                    section_type=section_type,
                    title=title,
                    subtitle=subtitle,
                    order=order,
                    is_active=True
                )
            self.stdout.write(self.style.SUCCESS(f'   ✅ {len(sections)} secciones creadas'))
        else:
            self.stdout.write(f'   ℹ️  Ya existen {sections_count} secciones')
        
        # Servicios
        services_count = Service.objects.filter(client=client).count()
        if services_count == 0:
            services = [
                ('Servicio 1', '⚡', 'Descripción del servicio', True),
                ('Servicio 2', '🔧', 'Descripción del servicio', True),
                ('Servicio 3', '📋', 'Descripción del servicio', False),
            ]
            for idx, (name, icon, desc, featured) in enumerate(services):
                Service.objects.create(
                    client=client,
                    name=name,
                    icon=icon,
                    description=desc,
                    order=idx * 10,
                    is_active=True,
                    is_featured=featured
                )
            self.stdout.write(self.style.SUCCESS(f'   ✅ {len(services)} servicios creados'))
        else:
            self.stdout.write(f'   ℹ️  Ya existen {services_count} servicios')