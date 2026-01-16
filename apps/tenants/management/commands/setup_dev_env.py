from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.tenants.models import Client, ClientSettings, Domain
from apps.website.models import Section, Service

User = get_user_model()

class Command(BaseCommand):
    help = 'Configura el entorno SaaS completo (Marketing + Tenant Demo)'

    def handle(self, *args, **kwargs):
        self.stdout.write("🏗️  Iniciando construcción del entorno Multi-Tenant...")

        # 1. Superusuario
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@saas.cl', 'admin123')
            self.stdout.write(self.style.SUCCESS('✅ Superusuario creado (admin/admin123)'))

        # =================================================================
        # TENANT 1: ANDES SCALE (Tu Landing Page de Ventas)
        # =================================================================
        # Nota: Aunque el template sea 'default', el TemplateLoader detectará
        # el slug 'andesscale' y cargará la carpeta 'marketing/'.
        self.create_tenant(
            name='Andes Scale SaaS',
            slug='andesscale',
            domain='andesscale.localhost',
            template='default',
            plan='enterprise',
            primary_color='#0ea5e9', # Azul Stripe
            secondary_color='#0284c7',
            sections=[
                {
                    'type': 'hero', 
                    'title': 'Crea tu sitio web profesional en minutos', 
                    'desc': 'La plataforma SaaS definitiva para electricistas y contratistas.'
                },
                {
                    'type': 'services', # Features
                    'title': 'Características',
                    'desc': 'Todo lo que necesitas para crecer.'
                }
            ],
            services=[] # El sitio de marketing quizás no usa el modelo Service igual, pero lo dejamos vacío
        )

        # =================================================================
        # TENANT 2: SERVELEC (Tu Cliente Demo)
        # =================================================================
        self.create_tenant(
            name='Servelec Ingeniería',
            slug='servelec-ingenieria',
            domain='servelec.localhost',
            template='electricidad', # <--- Usa themes/electricidad/
            plan='pro',
            primary_color='#16a34a', # Verde
            secondary_color='#15803d',
            sections=[
                {
                    'type': 'hero', 
                    'title': 'Soluciones Eléctricas Profesionales', 
                    'desc': 'Especialistas en instalaciones industriales y certificación SEC.'
                },
                {
                    'type': 'about',
                    'title': 'Sobre Nosotros',
                    'desc': 'Más de 20 años de experiencia en el rubro eléctrico nacional.'
                },
                {
                    'type': 'contact',
                    'title': 'Contáctanos',
                    'desc': 'Solicita tu visita técnica hoy mismo.'
                }
            ],
            services=[
                {
                    'name': 'Instalaciones Industriales',
                    'desc': 'Tableros de fuerza y control.',
                    'icon': 'fa-industry', 'price': 'A convenir'
                },
                {
                    'name': 'Certificación TE1',
                    'desc': 'Trámites y regularizaciones SEC.',
                    'icon': 'fa-file-signature', 'price': 'Desde $150.000'
                }
            ]
        )

        self.stdout.write(self.style.SUCCESS('🚀 ¡Entorno Nivel 3 listo!'))

    def create_tenant(self, name, slug, domain, template, plan, primary_color, secondary_color, sections, services):
        """Helper para crear un tenant completo de forma limpia"""
        
        self.stdout.write(f"⚙️  Configurando: {name} ({slug})...")

        # 1. Cliente
        client, _ = Client.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'company_name': name,
                'template': template,
                'plan': plan
            }
        )
        
        # 2. Dominio
        Domain.objects.get_or_create(
            client=client,
            domain=domain,
            defaults={'is_primary': True, 'is_active': True}
        )

        # 3. Settings (Branding)
        settings, _ = ClientSettings.objects.get_or_create(client=client)
        settings.primary_color = primary_color
        settings.secondary_color = secondary_color
        settings.save()

        # 4. Limpiar contenido viejo
        Section.objects.filter(client=client).delete()
        Service.objects.filter(client=client).delete()

        # 5. Crear Secciones
        for idx, sec in enumerate(sections):
            Section.objects.create(
                client=client,
                section_type=sec['type'],
                title=sec['title'],
                description=sec['desc'],
                order=idx,
                is_active=True
            )

        # 6. Crear Servicios
        for idx, svc in enumerate(services):
            Service.objects.create(
                client=client,
                name=svc['name'],
                description=svc['desc'],
                icon=svc['icon'],
                price_text=svc['price'],
                order=idx,
                is_active=True,
                is_featured=True
            )

        self.stdout.write(self.style.SUCCESS('✅ Contenido creado exitosamente'))
        self.stdout.write(self.style.SUCCESS('🚀 ¡Entorno listo! Ejecuta: python manage.py runserver'))