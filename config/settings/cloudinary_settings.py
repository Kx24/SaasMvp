# =============================================================================
# config/settings/cloudinary_settings.py
# =============================================================================
# Configuración centralizada de Cloudinary
# Importar en base.py: from .cloudinary_settings import *
# =============================================================================

import cloudinary
import cloudinary.uploader
import cloudinary.api
from decouple import config
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# CLOUDINARY CORE CONFIGURATION
# =============================================================================

CLOUDINARY_CLOUD_NAME = config('CLOUDINARY_CLOUD_NAME', default='')
CLOUDINARY_API_KEY = config('CLOUDINARY_API_KEY', default='')
CLOUDINARY_API_SECRET = config('CLOUDINARY_API_SECRET', default='')
CLOUDINARY_SECURE = config('CLOUDINARY_SECURE', default=True, cast=bool)

# Configurar Cloudinary SDK
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=CLOUDINARY_SECURE
)

# =============================================================================
# VALIDATION AT STARTUP
# =============================================================================

def validate_cloudinary_config():
    """
    Valida que Cloudinary esté correctamente configurado.
    Llamar desde AppConfig.ready() o al inicio de la app.
    """
    missing = []
    
    if not CLOUDINARY_CLOUD_NAME:
        missing.append('CLOUDINARY_CLOUD_NAME')
    if not CLOUDINARY_API_KEY:
        missing.append('CLOUDINARY_API_KEY')
    if not CLOUDINARY_API_SECRET:
        missing.append('CLOUDINARY_API_SECRET')
    
    if missing:
        logger.error(f"❌ Cloudinary config incompleta. Faltan: {', '.join(missing)}")
        return False
    
    # Log solo el cloud_name (nunca secrets)
    logger.info(f"☁️  Cloudinary configurado: cloud_name={CLOUDINARY_CLOUD_NAME}")
    return True


def ping_cloudinary():
    """
    Verifica conexión con Cloudinary.
    Útil para health checks y diagnóstico.
    """
    try:
        result = cloudinary.api.ping()
        logger.info(f"☁️  Cloudinary ping exitoso: {result}")
        return True
    except Exception as e:
        logger.error(f"❌ Cloudinary ping fallido: {e}")
        return False


# =============================================================================
# FOLDER CONVENTIONS
# =============================================================================

CLOUDINARY_FOLDERS = {
    'sections': 'sections',
    'services': 'services',
    'testimonials': 'testimonials',
    'branding': 'branding',
    'gallery': 'gallery',
}


def get_cloudinary_folder(tenant_slug: str, category: str) -> str:
    """
    Construye la ruta de carpeta para un tenant y categoría.
    
    Args:
        tenant_slug: Slug del cliente (ej: 'servelec-ingenieria')
        category: Categoría del asset (ej: 'sections', 'services')
    
    Returns:
        Ruta completa (ej: 'servelec-ingenieria/sections')
    
    Raises:
        ValueError: Si la categoría no es válida
    """
    if category not in CLOUDINARY_FOLDERS:
        valid = ', '.join(CLOUDINARY_FOLDERS.keys())
        raise ValueError(f"Categoría '{category}' no válida. Usar: {valid}")
    
    return f"{tenant_slug}/{CLOUDINARY_FOLDERS[category]}"


# =============================================================================
# TRANSFORMATION PRESETS
# =============================================================================

CLOUDINARY_PRESETS = {
    'thumbnail': {
        'crop': 'fill',
        'width': 300,
        'height': 200,
        'format': 'auto',
        'quality': 'auto',
    },
    'hero': {
        'crop': 'fill',
        'width': 1200,
        'height': 600,
        'format': 'auto',
        'quality': 'auto',
    },
    'service_card': {
        'crop': 'fill',
        'width': 400,
        'height': 300,
        'format': 'auto',
        'quality': 'auto',
    },
    'logo': {
        'crop': 'fit',
        'width': 200,
        'height': 80,
        'format': 'auto',
    },
    'avatar': {
        'crop': 'fill',
        'width': 100,
        'height': 100,
        'format': 'auto',
        'quality': 'auto',
        'radius': 'max',
    },
}


def get_preset(preset_name: str) -> dict:
    """
    Obtiene un preset de transformación por nombre.
    
    Args:
        preset_name: Nombre del preset (ej: 'thumbnail', 'hero')
    
    Returns:
        Dict con parámetros de transformación
    
    Raises:
        ValueError: Si el preset no existe
    """
    if preset_name not in CLOUDINARY_PRESETS:
        valid = ', '.join(CLOUDINARY_PRESETS.keys())
        raise ValueError(f"Preset '{preset_name}' no existe. Usar: {valid}")
    
    return CLOUDINARY_PRESETS[preset_name].copy()


# =============================================================================
# TENANT LIMITS (Soft Limits)
# =============================================================================

CLOUDINARY_DEFAULT_LIMITS = {
    'max_media_items': 50,      # Máximo de archivos por tenant
    'max_media_size_mb': 100,   # Tamaño total máximo en MB
    'max_file_size_mb': 10,     # Tamaño máximo por archivo en MB
    'allowed_formats': ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'],
}


# =============================================================================
# USAGE ALERTS
# =============================================================================

CLOUDINARY_ALERT_THRESHOLDS = {
    'warning': 70,   # % de créditos para warning
    'critical': 85,  # % de créditos para alerta crítica
    'block': 95,     # % de créditos para bloquear uploads
}
