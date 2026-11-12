# =============================================================================
# apps/core/management/commands/check_cloudinary.py
# =============================================================================
# Management command para verificar configuración de Cloudinary
# Uso: python manage.py check_cloudinary
# =============================================================================

import cloudinary
import cloudinary.api
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Verifica la configuración de Cloudinary y prueba la conexión'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Muestra información detallada',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        self.stdout.write(self.style.HTTP_INFO('☁️  CLOUDINARY CONFIGURATION CHECK'))
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        
        # 1. Verificar variables de entorno
        self.stdout.write('\n📋 Verificando variables de entorno...')
        
        cloud_name = getattr(settings, 'CLOUDINARY_CLOUD_NAME', '')
        api_key = getattr(settings, 'CLOUDINARY_API_KEY', '')
        api_secret = getattr(settings, 'CLOUDINARY_API_SECRET', '')
        
        checks = []
        
        if cloud_name:
            self.stdout.write(self.style.SUCCESS(f'   ✅ CLOUDINARY_CLOUD_NAME: {cloud_name}'))
            checks.append(True)
        else:
            self.stdout.write(self.style.ERROR('   ❌ CLOUDINARY_CLOUD_NAME: No configurado'))
            checks.append(False)
        
        if api_key:
            # Mostrar solo los primeros/últimos caracteres
            masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else '****'
            self.stdout.write(self.style.SUCCESS(f'   ✅ CLOUDINARY_API_KEY: {masked_key}'))
            checks.append(True)
        else:
            self.stdout.write(self.style.ERROR('   ❌ CLOUDINARY_API_KEY: No configurado'))
            checks.append(False)
        
        if api_secret:
            self.stdout.write(self.style.SUCCESS('   ✅ CLOUDINARY_API_SECRET: ******** (oculto)'))
            checks.append(True)
        else:
            self.stdout.write(self.style.ERROR('   ❌ CLOUDINARY_API_SECRET: No configurado'))
            checks.append(False)
        
        # 2. Verificar configuración del SDK
        self.stdout.write('\n📋 Verificando SDK de Cloudinary...')
        
        config = cloudinary.config()
        if config.cloud_name:
            self.stdout.write(self.style.SUCCESS(f'   ✅ SDK configurado: cloud_name={config.cloud_name}'))
            checks.append(True)
        else:
            self.stdout.write(self.style.ERROR('   ❌ SDK no configurado correctamente'))
            checks.append(False)
        
        # 3. Probar conexión (ping)
        self.stdout.write('\n📋 Probando conexión con Cloudinary...')
        
        try:
            result = cloudinary.api.ping()
            self.stdout.write(self.style.SUCCESS(f'   ✅ Ping exitoso: {result}'))
            checks.append(True)
        except cloudinary.exceptions.AuthorizationRequired as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error de autenticación: {e}'))
            checks.append(False)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error de conexión: {e}'))
            checks.append(False)
        
        # 4. Obtener uso actual (si conexión exitosa)
        if all(checks):
            self.stdout.write('\n📋 Obteniendo información de uso...')
            
            try:
                usage = cloudinary.api.usage()
                
                credits_used = usage.get('credits', {}).get('used', 0)
                credits_limit = usage.get('credits', {}).get('limit', 25)
                credits_percent = (credits_used / credits_limit * 100) if credits_limit > 0 else 0
                
                self.stdout.write(f'   📊 Créditos usados: {credits_used:.2f} / {credits_limit}')
                
                if credits_percent >= 85:
                    self.stdout.write(self.style.ERROR(f'   ⚠️  Uso: {credits_percent:.1f}% - CRÍTICO'))
                elif credits_percent >= 70:
                    self.stdout.write(self.style.WARNING(f'   ⚠️  Uso: {credits_percent:.1f}% - Atención'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Uso: {credits_percent:.1f}% - OK'))
                
                if verbose:
                    self.stdout.write('\n   📈 Detalles de uso:')
                    self.stdout.write(f'      - Transformations: {usage.get("transformations", {}).get("usage", 0)}')
                    self.stdout.write(f'      - Storage: {usage.get("storage", {}).get("usage", 0)} bytes')
                    self.stdout.write(f'      - Bandwidth: {usage.get("bandwidth", {}).get("usage", 0)} bytes')
                    self.stdout.write(f'      - Requests: {usage.get("requests", 0)}')
                
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠️  No se pudo obtener uso: {e}'))
        
        # 5. Verificar presets configurados
        self.stdout.write('\n📋 Verificando presets de transformación...')
        
        presets = getattr(settings, 'CLOUDINARY_PRESETS', {})
        if presets:
            self.stdout.write(self.style.SUCCESS(f'   ✅ {len(presets)} presets configurados:'))
            for name in presets.keys():
                self.stdout.write(f'      - {name}')
        else:
            self.stdout.write(self.style.WARNING('   ⚠️  No hay presets configurados'))
        
        # 6. Resumen final
        self.stdout.write('\n' + '=' * 60)
        
        if all(checks):
            self.stdout.write(self.style.SUCCESS('✅ CLOUDINARY CONFIGURADO CORRECTAMENTE'))
            self.stdout.write(self.style.SUCCESS(f'   Cloud: {cloud_name}'))
            self.stdout.write(self.style.SUCCESS('   Estado: Listo para usar'))
        else:
            self.stdout.write(self.style.ERROR('❌ CLOUDINARY TIENE PROBLEMAS DE CONFIGURACIÓN'))
            self.stdout.write(self.style.ERROR('   Revisar: /docs/CLOUDINARY.md'))
        
        self.stdout.write('=' * 60 + '\n')
        
        # Return code para scripts
        return None if all(checks) else 'Configuration error'
