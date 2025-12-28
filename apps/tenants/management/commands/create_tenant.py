"""
Management command para crear tenants con soporte multi-dominio

Uso:
    python manage.py create_tenant "Mi Empresa" miempresa.tuapp.cl
    python manage.py create_tenant "Mi Empresa" miempresa.tuapp.cl --extra-domain=www.miempresa.com
    python manage.py create_tenant "Mi Empresa" miempresa.tuapp.cl --template=servicios_profesionales
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.conf import settings

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea un tenant completo con dominio, usuario admin y contenido inicial'

    def add_arguments(self, parser):
        # Argumentos requeridos
        parser.add_argument(
            'name',
            type=str,
            help='Nombre del cliente (ej: "Mi Empresa")'
        )
        parser.add_argument(
            'domain',
            type=str,
            help='Dominio principal (ej: miempresa.tuapp.cl)'
        )
        
        # Argumentos opcionales
        parser.add_argument(
            '--extra-domain',
            type=str,
            action='append',
            dest='extra_domains',
            help='Dominios adicionales (puede repetirse)'
        )
        parser.add_argument(
            '--username',
            type=str,
            default=None,
            help='Username del admin (default: admin_slug)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@example.com',
            help='Email del admin'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='changeme123',
            help='Password del admin'
        )
        parser.add_argument(
            '--color',
            type=str,
            default='#2563eb',
            help='Color primario (hex)'
        )
        parser.add_argument(
            '--template',
            type=str,
            default='custom',
            choices=['electricidad', 'construccion', 'servicios_profesionales', 'portafolio', 'custom'],
            help='Template a aplicar'
        )
        parser.add_argument(
            '--no-content',
            action='store_true',
            help='No crear contenido inicial'
        )
        parser.add_argument(
            '--no-user',
            action='store_true',
            help='No crear usuario admin'
        )

    def handle(self, *args, **options):
        from apps.tenants.models import Client, Domain
        from apps.website.models import Section, Service
        
        name = options['name']
        domain = options['domain'].lower()
        slug = slugify(name)
        username = options['username'] or f"admin_{slug.replace('-', '_')}"
        extra_domains = options.get('extra_domains') or []
        
        self.stdout.write(self.style.WARNING(f'\n🚀 Creando tenant: {name}'))
        self.stdout.write(f'   Slug: {slug}')
        self.stdout.write(f'   Dominio: {domain}')
        if extra_domains:
            self.stdout.write(f'   Dominios extra: {", ".join(extra_domains)}')
        
        # ============================================================
        # VALIDACIONES
        # ============================================================
        
        if Client.objects.filter(slug=slug).exists():
            raise CommandError(f'❌ Ya existe un cliente con slug: {slug}')
        
        if Domain.objects.filter(domain=domain).exists():
            raise CommandError(f'❌ Ya existe el dominio: {domain}')
        
        for extra in extra_domains:
            if Domain.objects.filter(domain=extra.lower()).exists():
                raise CommandError(f'❌ Ya existe el dominio: {extra}')
        
        if not options['no_user'] and User.objects.filter(username=username).exists():
            raise CommandError(f'❌ Ya existe el usuario: {username}')
        
        # ============================================================
        # CREAR CLIENTE
        # ============================================================
        
        self.stdout.write('\n🏢 Creando cliente...')
        
        client = Client.objects.create(
            name=name,
            slug=slug,
            company_name=name,
            contact_email=options['email'],
            template=options['template'],
            is_active=True,
        )
        
        self.stdout.write(self.style.SUCCESS(f'   ✓ Cliente creado: {client}'))
        
        # ============================================================
        # CREAR DOMINIOS
        # ============================================================
        
        self.stdout.write('\n🌐 Configurando dominios...')
        
        # Dominio principal
        base_domain = getattr(settings, 'BASE_DOMAIN', 'tuapp.cl')
        is_subdomain = domain.endswith(f'.{base_domain}')
        
        primary_domain = Domain.objects.create(
            client=client,
            domain=domain,
            domain_type='subdomain' if is_subdomain else 'custom',
            is_primary=True,
            is_active=True,
            is_verified=is_subdomain,  # Subdominios propios están verificados
        )
        
        self.stdout.write(self.style.SUCCESS(f'   ✓ Dominio primario: {primary_domain.domain}'))
        
        # Dominios extra
        for extra in extra_domains:
            extra = extra.lower()
            is_sub = extra.endswith(f'.{base_domain}')
            
            extra_domain = Domain.objects.create(
                client=client,
                domain=extra,
                domain_type='subdomain' if is_sub else 'custom',
                is_primary=False,
                is_active=True,
                is_verified=is_sub,
            )
            self.stdout.write(self.style.SUCCESS(f'   ✓ Dominio extra: {extra_domain.domain}'))
        
        # ============================================================
        # CONFIGURAR SETTINGS
        # ============================================================
        
        self.stdout.write('\n⚙️  Configurando branding...')
        
        client.settings.primary_color = options['color']
        client.settings.secondary_color = '#1e40af'
        client.settings.company_name = name
        client.settings.save()
        
        self.stdout.write(self.style.SUCCESS(f'   ✓ Color primario: {options["color"]}'))
        
        # ============================================================
        # CREAR USUARIO ADMIN
        # ============================================================
        
        if not options['no_user']:
            self.stdout.write('\n👤 Creando usuario admin...')
            
            user = User.objects.create_user(
                username=username,
                email=options['email'],
                password=options['password'],
                is_staff=True,  # Acceso al admin
            )
            
            self.stdout.write(self.style.SUCCESS(f'   ✓ Usuario: {username}'))
            self.stdout.write(self.style.SUCCESS(f'   ✓ Password: {options["password"]}'))
            
            # TODO: Crear UserProfile asociado al cliente
            # if hasattr(user, 'profile'):
            #     user.profile.client = client
            #     user.profile.save()
        
        # ============================================================
        # CREAR CONTENIDO INICIAL
        # ============================================================
        
        if not options['no_content']:
            self.stdout.write('\n📄 Creando contenido inicial...')
            
            # Secciones
            sections_data = [
                ('hero', f'Bienvenido a {name}', 'Soluciones profesionales para tu negocio'),
                ('about', 'Quiénes Somos', 'Conoce nuestra historia y valores'),
                ('contact', 'Contáctanos', 'Estamos aquí para ayudarte'),
            ]
            
            for i, (section_type, title, subtitle) in enumerate(sections_data, 1):
                Section.objects.create(
                    client=client,
                    section_type=section_type,
                    title=title,
                    subtitle=subtitle,
                    order=i * 10,
                    is_active=True,
                )
                self.stdout.write(f'   ✓ Sección: {section_type}')
            
            # Servicios según template
            services_data = self.get_services_for_template(options['template'], name)
            
            for i, service in enumerate(services_data, 1):
                Service.objects.create(
                    client=client,
                    name=service['name'],
                    icon=service['icon'],
                    description=service['description'],
                    price_text=service.get('price_text', ''),
                    order=i * 10,
                    is_active=True,
                    is_featured=i <= 2,  # Primeros 2 destacados
                )
                self.stdout.write(f'   ✓ Servicio: {service["name"]}')
        
        # ============================================================
        # RESUMEN FINAL
        # ============================================================
        
        self.stdout.write(self.style.SUCCESS(f'''
╔══════════════════════════════════════════════════════════════╗
║                    ✅ TENANT CREADO                          ║
╠══════════════════════════════════════════════════════════════╣
║  Nombre:     {name:<47}║
║  Slug:       {slug:<47}║
║  Dominio:    {domain:<47}║
║  Template:   {options['template']:<47}║
╠══════════════════════════════════════════════════════════════╣'''))
        
        if not options['no_user']:
            self.stdout.write(self.style.SUCCESS(f'''║  Usuario:   {username:<47}║
║  Password:  {options['password']:<47}║'''))
        
        self.stdout.write(self.style.SUCCESS(f'''╠══════════════════════════════════════════════════════════════╣
║  URL:       https://{domain:<40}║
║  Dashboard: https://{domain}/dashboard/<25}║
╚══════════════════════════════════════════════════════════════╝
'''))

    def get_services_for_template(self, template, company_name):
        """Retorna servicios según el template seleccionado"""
        
        templates = {
            'electricidad': [
                {'name': 'Instalaciones Eléctricas', 'icon': '⚡', 'description': 'Instalaciones residenciales e industriales', 'price_text': 'Cotizar'},
                {'name': 'Mantención Preventiva', 'icon': '🔧', 'description': 'Mantención y revisión de sistemas eléctricos', 'price_text': 'Desde $50.000'},
                {'name': 'Emergencias 24/7', 'icon': '🚨', 'description': 'Servicio de emergencias las 24 horas', 'price_text': 'Consultar'},
            ],
            'construccion': [
                {'name': 'Construcción Residencial', 'icon': '🏠', 'description': 'Construcción de casas y departamentos', 'price_text': 'Cotizar'},
                {'name': 'Remodelaciones', 'icon': '🔨', 'description': 'Remodelación integral de espacios', 'price_text': 'Desde $500.000'},
                {'name': 'Obras Menores', 'icon': '🧱', 'description': 'Ampliaciones y modificaciones menores', 'price_text': 'Consultar'},
            ],
            'servicios_profesionales': [
                {'name': 'Consultoría', 'icon': '💼', 'description': 'Asesoría profesional especializada', 'price_text': 'Desde $100.000'},
                {'name': 'Capacitación', 'icon': '📚', 'description': 'Cursos y talleres personalizados', 'price_text': 'Cotizar'},
                {'name': 'Soporte Técnico', 'icon': '🛠️', 'description': 'Asistencia técnica especializada', 'price_text': '$50.000/hora'},
            ],
            'portafolio': [
                {'name': 'Diseño Web', 'icon': '🌐', 'description': 'Diseño y desarrollo de sitios web', 'price_text': 'Desde $300.000'},
                {'name': 'Branding', 'icon': '🎨', 'description': 'Identidad visual y branding', 'price_text': 'Cotizar'},
                {'name': 'Marketing Digital', 'icon': '📱', 'description': 'Estrategias de marketing online', 'price_text': 'Desde $150.000/mes'},
            ],
        }
        
        # Default / custom
        default_services = [
            {'name': 'Servicio 1', 'icon': '⭐', 'description': f'Primer servicio de {company_name}', 'price_text': 'Cotizar'},
            {'name': 'Servicio 2', 'icon': '✨', 'description': f'Segundo servicio de {company_name}', 'price_text': 'Consultar'},
            {'name': 'Servicio 3', 'icon': '🎯', 'description': f'Tercer servicio de {company_name}', 'price_text': ''},
        ]
        
        return templates.get(template, default_services)