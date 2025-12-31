"""
Management Command: create_tenant
=================================

Crea un tenant completo con:
- Client + ClientSettings
- Domain (múltiples dominios soportados)
- Usuario admin vinculado al tenant
- Carpeta de media
- Secciones y servicios iniciales

Uso:
    python manage.py create_tenant "Mi Empresa" miempresa.cl --email=admin@miempresa.cl
    python manage.py create_tenant "Otra Empresa" otra.cl --extra-domain=www.otra.cl --color=#ff0000
"""
import shutil
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.conf import settings

from apps.tenants.models import Client, Domain
from apps.website.models import Section, Service

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea un tenant completo con usuario, templates y contenido inicial'

    def add_arguments(self, parser):
        # Argumentos requeridos
        parser.add_argument('name', type=str, help='Nombre de la empresa')
        parser.add_argument('domain', type=str, help='Dominio principal (ej: empresa.cl)')
        
        # Argumentos opcionales
        parser.add_argument(
            '--extra-domain',
            type=str,
            action='append',
            default=[],
            help='Dominios adicionales (puede repetirse)'
        )
        parser.add_argument(
            '--username',
            type=str,
            default=None,
            help='Username del admin (default: admin_{slug})'
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
            '--phone',
            type=str,
            default='',
            help='Teléfono de contacto'
        )
        parser.add_argument(
            '--copy-templates',
            action='store_true',
            default=False,
            help='Copiar templates de _default a carpeta del tenant'
        )
        parser.add_argument(
            '--no-content',
            action='store_true',
            default=False,
            help='No crear secciones ni servicios de ejemplo'
        )

    def handle(self, *args, **options):
        name = options['name']
        domain = options['domain'].lower().strip()
        slug = slugify(name)
        username = options['username'] or f"admin_{slug}"
        
        self.stdout.write(self.style.HTTP_INFO(f'\n{"="*60}'))
        self.stdout.write(self.style.HTTP_INFO(f'  CREANDO TENANT: {name}'))
        self.stdout.write(self.style.HTTP_INFO(f'{"="*60}\n'))
        
        # ============================================================
        # VALIDACIONES
        # ============================================================
        if Client.objects.filter(slug=slug).exists():
            raise CommandError(f'❌ Ya existe un cliente con slug: {slug}')
        
        # Validar dominio en tabla Domain (no en Client)
        if Domain.objects.filter(domain=domain).exists():
            raise CommandError(f'❌ Ya existe el dominio: {domain}')
        
        if User.objects.filter(username=username).exists():
            raise CommandError(f'❌ Ya existe el usuario: {username}')
        
        # Validar dominios extra
        for extra in options['extra_domain']:
            if Domain.objects.filter(domain=extra.lower()).exists():
                raise CommandError(f'❌ Ya existe el dominio: {extra}')
        
        # ============================================================
        # 1. CREAR CLIENT (sin campo domain)
        # ============================================================
        self.stdout.write('🏢 Creando cliente...')
        client = Client.objects.create(
            name=name,
            slug=slug,
            company_name=name,
            contact_email=options['email'],
            contact_phone=options['phone'],
            is_active=True
        )
        self.stdout.write(self.style.SUCCESS(f'   ✓ Cliente creado: {client.name} (slug: {slug})'))
        
        # ============================================================
        # 2. CONFIGURAR CLIENT SETTINGS
        # ============================================================
        self.stdout.write('⚙️  Configurando settings...')
        client.settings.primary_color = options['color']
        client.settings.secondary_color = self._darken_color(options['color'])
        client.settings.meta_title = f'{name} - Sitio Oficial'
        client.settings.meta_description = f'Bienvenido a {name}. Soluciones profesionales para tu negocio.'
        client.settings.save()
        self.stdout.write(self.style.SUCCESS(f'   ✓ Settings configurados'))
        
        # ============================================================
        # 3. CREAR DOMINIOS
        # ============================================================
        self.stdout.write('🌐 Creando dominios...')
        
        # Dominio principal
        Domain.objects.create(
            client=client,
            domain=domain,
            domain_type='primary',
            is_primary=True,
            is_active=True,
            is_verified=True
        )
        self.stdout.write(self.style.SUCCESS(f'   ✓ Dominio principal: {domain}'))
        
        # Dominios adicionales
        for extra in options['extra_domain']:
            extra = extra.lower().strip()
            Domain.objects.create(
                client=client,
                domain=extra,
                domain_type='alias',
                is_primary=False,
                is_active=True,
                is_verified=True
            )
            self.stdout.write(self.style.SUCCESS(f'   ✓ Dominio adicional: {extra}'))
        
        # Subdominio automático
        base_domain = getattr(settings, 'BASE_DOMAIN', 'tuapp.cl')
        subdomain = f'{slug}.{base_domain}'
        
        # Solo crear si no existe ya
        if not Domain.objects.filter(domain=subdomain).exists():
            Domain.objects.create(
                client=client,
                domain=subdomain,
                domain_type='subdomain',
                is_primary=False,
                is_active=True,
                is_verified=True
            )
            self.stdout.write(self.style.SUCCESS(f'   ✓ Subdominio: {subdomain}'))
        
        # ============================================================
        # 4. CREAR USUARIO ADMIN
        # ============================================================
        self.stdout.write('👤 Creando usuario admin...')
        user = User.objects.create_user(
            username=username,
            email=options['email'],
            password=options['password'],
            is_staff=True  # Puede acceder al admin
        )
        
        # Vincular usuario al tenant (UserProfile se crea automáticamente por signal)
        if hasattr(user, 'profile'):
            user.profile.client = client
            user.profile.role = 'owner'
            user.profile.save()
            self.stdout.write(self.style.SUCCESS(f'   ✓ Usuario: {username} (vinculado a {client.name})'))
        else:
            self.stdout.write(self.style.WARNING(f'   ⚠ Usuario creado pero sin UserProfile'))
        
        # ============================================================
        # 5. CREAR CARPETA DE MEDIA
        # ============================================================
        self.stdout.write('📁 Creando carpeta de media...')
        media_path = Path(settings.MEDIA_ROOT) / 'tenants' / slug
        media_path.mkdir(parents=True, exist_ok=True)
        (media_path / 'images').mkdir(exist_ok=True)
        (media_path / 'documents').mkdir(exist_ok=True)
        self.stdout.write(self.style.SUCCESS(f'   ✓ Carpeta: media/tenants/{slug}/'))
        
        # ============================================================
        # 6. COPIAR TEMPLATES (opcional)
        # ============================================================
        if options['copy_templates']:
            self.stdout.write('📄 Copiando templates...')
            templates_src = Path(settings.BASE_DIR) / 'templates' / 'tenants' / '_default'
            templates_dst = Path(settings.BASE_DIR) / 'templates' / 'tenants' / slug
            
            if templates_src.exists():
                if templates_dst.exists():
                    self.stdout.write(self.style.WARNING(f'   ⚠ Ya existe carpeta de templates, omitiendo'))
                else:
                    shutil.copytree(templates_src, templates_dst)
                    self.stdout.write(self.style.SUCCESS(f'   ✓ Templates copiados a: templates/tenants/{slug}/'))
            else:
                self.stdout.write(self.style.WARNING(f'   ⚠ No existe _default, omitiendo'))
        
        # ============================================================
        # 7. CREAR CONTENIDO INICIAL
        # ============================================================
        if not options['no_content']:
            self.stdout.write('📝 Creando contenido inicial...')
            
            # Secciones
            sections_data = [
                ('hero', f'Bienvenido a {name}', 'Soluciones profesionales para tu negocio', 10),
                ('about', 'Quiénes Somos', 'Conoce nuestra historia y valores', 20),
                ('contact', 'Contáctanos', 'Estamos aquí para ayudarte', 30),
            ]
            
            for section_type, title, subtitle, order in sections_data:
                Section.objects.create(
                    client=client,
                    section_type=section_type,
                    title=title,
                    subtitle=subtitle,
                    order=order,
                    is_active=True
                )
            self.stdout.write(self.style.SUCCESS(f'   ✓ {len(sections_data)} secciones creadas'))
            
            # Servicios
            services_data = [
                ('Consultoría', '💼', 'Asesoramiento profesional para tu negocio', 'Desde $100.000', True),
                ('Desarrollo', '💻', 'Soluciones tecnológicas a medida', 'Cotizar', True),
                ('Soporte', '🛠️', 'Asistencia técnica continua', '$50.000/mes', False),
            ]
            
            for idx, (name_svc, icon, desc, price, featured) in enumerate(services_data):
                Service.objects.create(
                    client=client,
                    name=name_svc,
                    icon=icon,
                    description=desc,
                    full_description=desc,
                    price_text=price,
                    order=idx * 10,
                    is_active=True,
                    is_featured=featured
                )
            self.stdout.write(self.style.SUCCESS(f'   ✓ {len(services_data)} servicios creados'))
        
        # ============================================================
        # RESUMEN FINAL
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO(f'\n{"="*60}'))
        self.stdout.write(self.style.SUCCESS('  ✅ TENANT CREADO EXITOSAMENTE'))
        self.stdout.write(self.style.HTTP_INFO(f'{"="*60}'))
        self.stdout.write(f'''
  📋 Resumen:
     • Cliente: {client.name}
     • Slug: {slug}
     • Dominio: {domain}
     • Subdominio: {subdomain}
     
  👤 Credenciales:
     • Usuario: {username}
     • Password: {options['password']}
     • Email: {options['email']}
     
  🔗 URLs:
     • Producción: https://{domain}
     • Desarrollo: http://127.0.0.1:8000/?tenant={slug}
     • Admin: http://127.0.0.1:8000/superadmin/
     
  📁 Archivos:
     • Media: media/tenants/{slug}/
     • Templates: templates/tenants/{slug}/ {"(creado)" if options['copy_templates'] else "(usar _default)"}
''')
        self.stdout.write(self.style.HTTP_INFO(f'{"="*60}\n'))
    
    def _darken_color(self, hex_color):
        """Oscurece un color hex para el color secundario"""
        try:
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            r = max(0, int(r * 0.7))
            g = max(0, int(g * 0.7))
            b = max(0, int(b * 0.7))
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            return '#1e40af'