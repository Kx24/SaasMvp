# apps/orders/management/commands/setup_plans.py
"""
Management command para crear los planes iniciales.

Uso:
    python manage.py setup_plans
    python manage.py setup_plans --force  # Sobrescribe existentes
"""

from django.core.management.base import BaseCommand
from apps.orders.models import Plan


class Command(BaseCommand):
    help = 'Crea los planes iniciales de Andesscale'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Sobrescribe planes existentes',
        )
    
    def handle(self, *args, **options):
        force = options['force']
        
        plans_data = [
            {
                'name': 'Plan Esencial',
                'slug': 'essential',
                'price': 150000,  # Ajustar según tu pricing
                'renewal_price': 15000,
                'tagline': 'Ideal para comenzar',
                'description': 'Todo lo que necesitas para tener presencia web profesional.',
                'features': [
                    'Sitio web profesional',
                    'Hosting por 1 año',
                    'Subdominio incluido (tunegocio.andesscale.cl)',
                    'Formulario de contacto',
                    'Diseño responsive',
                    'Soporte por email',
                    '2 meses de garantía',
                ],
                'available_themes': ['default'],
                'max_pages': 5,
                'max_services': 10,
                'max_images': 30,
                'max_storage_mb': 50,
                'has_custom_domain': False,
                'has_analytics': False,
                'has_priority_support': False,
                'has_white_label': False,
                'is_active': True,
                'is_featured': False,
                'display_order': 1,
            },
            {
                'name': 'Plan Pro',
                'slug': 'pro',
                'price': 250000,  # Ajustar según tu pricing
                'renewal_price': 25000,
                'tagline': 'Para negocios en crecimiento',
                'description': 'Más personalización y funcionalidades para destacar.',
                'features': [
                    'Todo lo del Plan Esencial',
                    'Dominio propio (.cl incluido primer año)',
                    'Selección de temas premium',
                    'Logo personalizado',
                    'Integración WhatsApp',
                    'Google Analytics',
                    'Soporte prioritario',
                    'Capacitación incluida',
                ],
                'available_themes': ['default', 'electricidad', 'industrial'],
                'max_pages': 10,
                'max_services': 20,
                'max_images': 100,
                'max_storage_mb': 200,
                'has_custom_domain': True,
                'has_analytics': True,
                'has_priority_support': True,
                'has_white_label': False,
                'is_active': True,
                'is_featured': True,  # Plan destacado
                'display_order': 2,
            },
            {
                'name': 'Plan Enterprise',
                'slug': 'enterprise',
                'price': 450000,  # Ajustar según tu pricing
                'renewal_price': 45000,
                'tagline': 'Solución completa a medida',
                'description': 'Diseño personalizado y soporte dedicado para tu empresa.',
                'features': [
                    'Todo lo del Plan Pro',
                    'Diseño 100% personalizado',
                    'Sin marca Andesscale',
                    'Múltiples dominios',
                    'Integración email corporativo',
                    'SEO avanzado',
                    'Soporte telefónico',
                    'Actualizaciones prioritarias',
                    'Backup diario',
                ],
                'available_themes': ['default', 'electricidad', 'industrial', 'custom'],
                'max_pages': 50,
                'max_services': 100,
                'max_images': 500,
                'max_storage_mb': 1000,
                'has_custom_domain': True,
                'has_analytics': True,
                'has_priority_support': True,
                'has_white_label': True,
                'is_active': True,
                'is_featured': False,
                'display_order': 3,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for plan_data in plans_data:
            slug = plan_data['slug']
            
            if Plan.objects.filter(slug=slug).exists():
                if force:
                    Plan.objects.filter(slug=slug).update(**plan_data)
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Plan actualizado: {plan_data["name"]}')
                    )
                else:
                    self.stdout.write(
                        self.style.NOTICE(f'Plan ya existe (omitido): {plan_data["name"]}')
                    )
            else:
                Plan.objects.create(**plan_data)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Plan creado: {plan_data["name"]}')
                )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Completado: {created_count} creados, {updated_count} actualizados'
            )
        )
        self.stdout.write('')
        self.stdout.write('Planes disponibles:')
        for plan in Plan.objects.filter(is_active=True).order_by('display_order'):
            featured = ' ⭐' if plan.is_featured else ''
            self.stdout.write(f'  - {plan.name}: ${plan.price:,.0f} CLP{featured}')
