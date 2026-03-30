# =============================================================================
# apps/core/management/commands/cloudinary_usage.py
# =============================================================================
# Management command para ver el uso actual de créditos de Cloudinary
# Uso: python manage.py cloudinary_usage
# =============================================================================

from django.core.management.base import BaseCommand
from datetime import datetime
import cloudinary
import cloudinary.api


class Command(BaseCommand):
    help = 'Muestra el uso actual de créditos y recursos de Cloudinary'

    def add_arguments(self, parser):
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output en formato JSON',
        )

    def handle(self, *args, **options):
        output_json = options['json']
        
        try:
            usage = cloudinary.api.usage()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error obteniendo uso: {e}'))
            return
        
        if output_json:
            import json
            self.stdout.write(json.dumps(usage, indent=2, default=str))
            return
        
        # Output formateado
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        self.stdout.write(self.style.HTTP_INFO('☁️  CLOUDINARY USAGE REPORT'))
        self.stdout.write(self.style.HTTP_INFO(f'   Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'))
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        
        # Créditos
        credits = usage.get('credits', {})
        credits_used = credits.get('used', 0)
        credits_limit = credits.get('limit', 25)
        credits_percent = (credits_used / credits_limit * 100) if credits_limit > 0 else 0
        
        self.stdout.write('\n💰 CRÉDITOS')
        self.stdout.write(f'   Usados:    {credits_used:.2f}')
        self.stdout.write(f'   Límite:    {credits_limit}')
        
        # Barra de progreso visual
        bar_length = 30
        filled = int(bar_length * credits_percent / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        if credits_percent >= 85:
            style = self.style.ERROR
        elif credits_percent >= 70:
            style = self.style.WARNING
        else:
            style = self.style.SUCCESS
        
        self.stdout.write(style(f'   Uso:       [{bar}] {credits_percent:.1f}%'))
        
        # Transformaciones
        transformations = usage.get('transformations', {})
        self.stdout.write('\n🔄 TRANSFORMACIONES')
        self.stdout.write(f'   Usadas:    {transformations.get("usage", 0):,}')
        self.stdout.write(f'   Límite:    {transformations.get("limit", "N/A")}')
        
        # Storage
        storage = usage.get('storage', {})
        storage_bytes = storage.get('usage', 0)
        storage_mb = storage_bytes / (1024 * 1024)
        self.stdout.write('\n💾 ALMACENAMIENTO')
        self.stdout.write(f'   Usado:     {storage_mb:.2f} MB ({storage_bytes:,} bytes)')
        
        # Bandwidth
        bandwidth = usage.get('bandwidth', {})
        bandwidth_bytes = bandwidth.get('usage', 0)
        bandwidth_mb = bandwidth_bytes / (1024 * 1024)
        self.stdout.write('\n📡 ANCHO DE BANDA')
        self.stdout.write(f'   Usado:     {bandwidth_mb:.2f} MB ({bandwidth_bytes:,} bytes)')
        
        # Requests
        requests = usage.get('requests', 0)
        self.stdout.write('\n🌐 REQUESTS')
        self.stdout.write(f'   Total:     {requests:,}')
        
        # Resources
        resources = usage.get('resources', 0)
        derived = usage.get('derived_resources', 0)
        self.stdout.write('\n📁 RECURSOS')
        self.stdout.write(f'   Originales: {resources:,}')
        self.stdout.write(f'   Derivados:  {derived:,}')
        
        # Alertas
        self.stdout.write('\n' + '=' * 60)
        
        if credits_percent >= 95:
            self.stdout.write(self.style.ERROR('🚨 ALERTA: Uso crítico de créditos (>95%)'))
            self.stdout.write(self.style.ERROR('   Considerar upgrade o reducir uploads'))
        elif credits_percent >= 85:
            self.stdout.write(self.style.ERROR('⚠️  ALERTA: Uso alto de créditos (>85%)'))
            self.stdout.write(self.style.WARNING('   Monitorear de cerca'))
        elif credits_percent >= 70:
            self.stdout.write(self.style.WARNING('⚠️  ATENCIÓN: Uso moderado-alto (>70%)'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Uso de créditos saludable'))
        
        self.stdout.write('=' * 60 + '\n')
