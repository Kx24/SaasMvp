# =============================================================================
# apps/tenants/management/commands/setup_cloudinary_folders.py
# =============================================================================
# Crea la estructura de carpetas en Cloudinary para tenants existentes
# Uso: python manage.py setup_cloudinary_folders
# =============================================================================

from django.core.management.base import BaseCommand
from apps.tenants.models import Client
import cloudinary
import cloudinary.uploader


class Command(BaseCommand):
    help = 'Crea estructura de carpetas en Cloudinary para tenants existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            help='Slug de tenant específico (opcional, si no se indica, procesa todos)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo muestra qué haría, sin crear carpetas',
        )

    def handle(self, *args, **options):
        tenant_slug = options.get('tenant')
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        self.stdout.write(self.style.HTTP_INFO('☁️  SETUP CLOUDINARY FOLDERS'))
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  MODO DRY-RUN: No se crearán carpetas\n'))
        
        # Obtener tenants
        if tenant_slug:
            clients = Client.objects.filter(slug=tenant_slug, is_active=True)
            if not clients.exists():
                self.stderr.write(self.style.ERROR(f'Tenant "{tenant_slug}" no encontrado o inactivo'))
                return
        else:
            clients = Client.objects.filter(is_active=True)
        
        self.stdout.write(f'\n📋 Procesando {clients.count()} tenant(s)...\n')
        
        # Categorías de carpetas a crear
        categories = ['sections', 'services', 'branding', 'gallery']
        
        # Procesar cada tenant
        for client in clients:
            self.stdout.write(f'\n🏢 Tenant: {client.name} ({client.slug})')
            
            for category in categories:
                folder_path = f"{client.slug}/{category}"
                
                if dry_run:
                    self.stdout.write(f'   📁 [DRY-RUN] Crearía: {folder_path}/')
                else:
                    # Crear carpeta subiendo un archivo placeholder y luego eliminándolo
                    # Cloudinary crea carpetas automáticamente al subir archivos
                    try:
                        # Verificar si ya existe contenido en la carpeta
                        result = cloudinary.api.resources(
                            type='upload',
                            prefix=f"{folder_path}/",
                            max_results=1
                        )
                        
                        if result.get('resources'):
                            self.stdout.write(
                                self.style.SUCCESS(f'   ✅ {folder_path}/ (ya existe)')
                            )
                        else:
                            # La carpeta no tiene contenido, pero eso está OK
                            # Las carpetas se crean automáticamente al subir
                            self.stdout.write(
                                self.style.WARNING(f'   📁 {folder_path}/ (vacía, se creará al subir)')
                            )
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'   ⚠️  {folder_path}/: {e}')
                        )
        
        # Resumen
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ Proceso completado'))
        self.stdout.write('\n📝 Nota: Las carpetas en Cloudinary se crean automáticamente')
        self.stdout.write('   al subir el primer archivo. Este comando solo verifica la')
        self.stdout.write('   estructura existente.')
        self.stdout.write('=' * 60 + '\n')
