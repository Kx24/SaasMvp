"""
Management Command: setup_production
====================================

Configura los datos iniciales necesarios para producción.
Este comando es idempotente (puede ejecutarse múltiples veces sin problemas).

Uso:
    python manage.py setup_production
    
    # Con opciones:
    python manage.py setup_production --domain=miapp.com --tenant=miempresa

Variables de entorno relevantes:
    TENANT_DOMAINS  = servelec:servelec-ingenieria.cl,www.servelec-ingenieria.cl|andesscale:andesscale.com,www.andesscale.com
    EXTRA_DOMAINS   = servelec-ingenieria.cl,www.servelec-ingenieria.cl,...
    BASE_DOMAIN     = andesscale.com
"""

import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


class Command(BaseCommand):
    help = 'Configura datos iniciales para producción (idempotente)'

    def add_arguments(self, parser):
        parser.add_argument('--domain', type=str, default=None)
        parser.add_argument('--tenant', type=str, default='servelec')
        parser.add_argument('--superuser', type=str, default='admin')
        parser.add_argument('--email', type=str, default='admin@example.com')

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('\n' + '='*60))
        self.stdout.write(self.style.HTTP_INFO('  SETUP PRODUCCIÓN - SaaS MVP'))
        self.stdout.write(self.style.HTTP_INFO('='*60 + '\n'))

        domain = options['domain'] or os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')
        tenant_slug = options['tenant']

        self._setup_tenant(tenant_slug, domain)
        self._setup_all_tenant_domains()        # ← nuevo: lee TENANT_DOMAINS
        self._setup_domains(tenant_slug, domain)  # ← mantiene compatibilidad
        self._setup_superuser(options['superuser'], options['email'])
        self._setup_initial_content(tenant_slug)

        self.stdout.write(self.style.HTTP_INFO('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('  ✅ SETUP COMPLETADO'))
        self.stdout.write(self.style.HTTP_INFO('='*60 + '\n'))

    # ------------------------------------------------------------------
    # NUEVO: registra dominios para TODOS los tenants desde TENANT_DOMAINS
    # ------------------------------------------------------------------
    def _setup_all_tenant_domains(self):
        """
        Lee TENANT_DOMAINS y registra cada dominio en su tenant.

        Formato de la variable:
            slug1:dom1,dom2|slug2:dom3,dom4

        Ejemplo:
            servelec:servelec-ingenieria.cl,www.servelec-ingenieria.cl|andesscale:andesscale.com,www.andesscale.com
        """
        from apps.tenants.models import Client, Domain

        tenant_domains_env = os.environ.get('TENANT_DOMAINS', '').strip()
        if not tenant_domains_env:
            return

        self.stdout.write('🌐 Registrando dominios desde TENANT_DOMAINS...')

        # Parsear: "slug1:d1,d2|slug2:d3,d4"
        for tenant_block in tenant_domains_env.split('|'):
            tenant_block = tenant_block.strip()
            if ':' not in tenant_block:
                continue

            slug, domains_str = tenant_block.split(':', 1)
            slug = slug.strip()
            domains = [d.strip() for d in domains_str.split(',') if d.strip()]

            try:
                client = Client.objects.get(slug=slug)
            except Client.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f'   ⚠️  Tenant "{slug}" no existe — omitiendo sus dominios'
                ))
                continue

            for i, domain_name in enumerate(domains):
                domain_obj, created = Domain.objects.get_or_create(
                    domain=domain_name,
                    defaults={
                        'client': client,
                        'domain_type': 'primary' if i == 0 else 'alias',
                        'is_primary': i == 0,
                        'is_active': True,
                        'is_verified': True,
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f'   ✅ [{slug}] Dominio "{domain_name}" registrado'
                    ))
                else:
                    # Si ya existía pero apunta a otro tenant, corregirlo
                    if domain_obj.client_id != client.id:
                        domain_obj.client = client
                        domain_obj.save()
                        self.stdout.write(self.style.WARNING(
                            f'   🔄 [{slug}] Dominio "{domain_name}" reasignado'
                        ))
                    else:
                        self.stdout.write(
                            f'   ℹ️  [{slug}] Dominio "{domain_name}" ya existe'
                        )

    # ------------------------------------------------------------------
    # ORIGINAL (mantenido para compatibilidad)
    # ------------------------------------------------------------------
    def _setup_tenant(self, slug, domain):
        from apps.tenants.models import Client

        self.stdout.write('🏢 Configurando tenant...')

        client, created = Client.objects.get_or_create(
            slug=slug,
            defaults={
                'name': slug.replace('-', ' ').title(),
                'company_name': slug.replace('-', ' ').title(),
                'contact_email': f'contacto@{domain}',
                'is_active': True,
            }
        )

        if created:
            client.settings.primary_color = '#1DB954'
            client.settings.secondary_color = '#15803d'
            client.settings.meta_title = client.name
            client.settings.meta_description = f'Bienvenido a {client.name}'
            client.settings.save()
            self.stdout.write(self.style.SUCCESS(f'   ✅ Tenant "{slug}" creado'))
        else:
            self.stdout.write(f'   ℹ️  Tenant "{slug}" ya existe')

        return client

    def _setup_domains(self, tenant_slug, primary_domain):
        """Dominios base: render hostname, localhost, 127.0.0.1."""
        from apps.tenants.models import Client, Domain

        self.stdout.write('🌐 Configurando dominios base...')

        try:
            client = Client.objects.get(slug=tenant_slug)
        except Client.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'   ❌ Tenant {tenant_slug} no existe'))
            return

        base_domains = [
            (primary_domain, 'primary', True),
            ('localhost', 'development', False),
            ('127.0.0.1', 'development', False),
        ]

        render_domain = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
        if render_domain and render_domain != primary_domain:
            base_domains.append((render_domain, 'subdomain', False))

        for domain_name, domain_type, is_primary in base_domains:
            domain_obj, created = Domain.objects.get_or_create(
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
                if domain_obj.client_id != client.id:
                    domain_obj.client = client
                    domain_obj.save()
                    self.stdout.write(f'   🔄 Dominio "{domain_name}" actualizado')
                else:
                    self.stdout.write(f'   ℹ️  Dominio "{domain_name}" ya existe')

        self.stdout.write('\n   📋 Dominios configurados:')
        for d in Domain.objects.filter(client=client):
            status = '✓' if d.is_active else '✗'
            self.stdout.write(f'      {status} {d.domain}')

    def _setup_superuser(self, username, email):
        self.stdout.write('👤 Configurando superusuario...')

        if User.objects.filter(is_superuser=True).exists():
            superuser = User.objects.filter(is_superuser=True).first()
            self.stdout.write(f'   ℹ️  Superusuario ya existe: {superuser.username}')
            return

        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123456')
        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f'   ✅ Superusuario "{username}" creado'))
        self.stdout.write(self.style.WARNING(f'   ⚠️  Password: {password} (cambiar en producción!)'))

    def _setup_initial_content(self, tenant_slug):
        from apps.tenants.models import Client
        from apps.website.models import Section, Service

        self.stdout.write('📝 Verificando contenido inicial...')

        try:
            client = Client.objects.get(slug=tenant_slug)
        except Client.DoesNotExist:
            return

        sections_count = Section.objects.filter(client=client).count()
        if sections_count == 0:
            for section_type, title, subtitle, order in [
                ('hero',    'Bienvenido',    'Soluciones profesionales', 10),
                ('about',   'Quiénes Somos', 'Nuestra historia',         20),
                ('contact', 'Contáctanos',   'Estamos para ayudarte',    30),
            ]:
                Section.objects.create(
                    client=client, section_type=section_type,
                    title=title, subtitle=subtitle,
                    order=order, is_active=True
                )
            self.stdout.write(self.style.SUCCESS('   ✅ 3 secciones creadas'))
        else:
            self.stdout.write(f'   ℹ️  Ya existen {sections_count} secciones')

        services_count = Service.objects.filter(client=client).count()
        if services_count == 0:
            for idx, (name, icon, desc, featured) in enumerate([
                ('Servicio 1', '⚡', 'Descripción del servicio', True),
                ('Servicio 2', '🔧', 'Descripción del servicio', True),
                ('Servicio 3', '📋', 'Descripción del servicio', False),
            ]):
                Service.objects.create(
                    client=client, name=name, icon=icon,
                    description=desc, order=idx * 10,
                    is_active=True, is_featured=featured
                )
            self.stdout.write(self.style.SUCCESS('   ✅ 3 servicios creados'))
        else:
            self.stdout.write(f'   ℹ️  Ya existen {services_count} servicios')