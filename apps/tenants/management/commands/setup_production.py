"""
Management command para setup inicial en producción
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.tenants.models import Client
import os

User = get_user_model()


class Command(BaseCommand):
    help = 'Setup inicial de producción: superusuario y cliente default'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Iniciando setup de producción...\n')
        
        # 1. Crear superusuario
        if not User.objects.filter(username='admin').exists():
            self.stdout.write('👤 Creando superusuario...')
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'  # CAMBIAR DESPUÉS
            )
            self.stdout.write(self.style.SUCCESS('✅ Superusuario creado'))
            self.stdout.write(self.style.WARNING('⚠️  Usuario: admin / Password: admin123'))
            self.stdout.write(self.style.WARNING('⚠️  CAMBIA LA CONTRASEÑA INMEDIATAMENTE EN /admin/'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Superusuario ya existe'))
        
        # 2. Crear cliente default
        if not Client.objects.exists():
            self.stdout.write('\n🏢 Creando cliente default...')
            
            # Obtener el dominio de Render desde variable de entorno o usar default
            domain = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'saasmvp.onrender.com')
            
            client = Client.objects.create(
                name="Cliente Default",
                slug="default",
                domain=domain,
                is_active=True
            )
            
            # Configurar settings
            client.settings.company_name = "Mi Empresa"
            client.settings.primary_color = "#2563eb"
            client.settings.secondary_color = "#1e40af"
            client.settings.contact_email = "contacto@example.com"
            client.settings.contact_phone = "+56912345678"
            client.settings.save()
            
            self.stdout.write(self.style.SUCCESS(f'✅ Cliente creado: {client.name}'))
            self.stdout.write(f'   🌐 Dominio: {client.domain}')
            self.stdout.write(f'   🎨 Color: {client.settings.primary_color}')
        else:
            self.stdout.write(self.style.WARNING('⚠️  Cliente ya existe'))
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('🎉 Setup completado'))
        self.stdout.write('='*50)