# =============================================================================
# apps/core/cloudinary_utils.py
# =============================================================================
# Utilidades para trabajar con Cloudinary de forma consistente
# Card C2: Helper de URLs y uploads con tenant isolation
# =============================================================================

import logging
from django.conf import settings
import cloudinary
import cloudinary.uploader

logger = logging.getLogger(__name__)


# =============================================================================
# PRESETS DE TRANSFORMACIÓN
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
    'hero_mobile': {
        'crop': 'fill',
        'width': 768,
        'height': 400,
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
    'service_detail': {
        'crop': 'fill',
        'width': 800,
        'height': 500,
        'format': 'auto',
        'quality': 'auto',
    },
    'logo': {
        'crop': 'fit',
        'width': 200,
        'height': 80,
        'format': 'auto',
    },
    'logo_footer': {
        'crop': 'fit',
        'width': 150,
        'height': 60,
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
    'gallery': {
        'crop': 'fill',
        'width': 600,
        'height': 400,
        'format': 'auto',
        'quality': 'auto',
    },
    'og_image': {  # Para Open Graph / Social Media
        'crop': 'fill',
        'width': 1200,
        'height': 630,
        'format': 'auto',
        'quality': 'auto',
    },
}


# =============================================================================
# FUNCIONES DE URL
# =============================================================================

def get_cloudinary_url(image_field, preset='thumbnail', **extra_options):
    """
    Genera URL de Cloudinary con transformaciones aplicadas.
    """
    if not image_field:
        return None
    
    # Obtener preset
    if preset not in CLOUDINARY_PRESETS:
        logger.warning(f"Preset '{preset}' no encontrado, usando 'thumbnail'")
        preset = 'thumbnail'
    
    transformation = CLOUDINARY_PRESETS[preset].copy()
    transformation.update(extra_options)
    
    try:
        # Si es CloudinaryResource, usar build_url directamente
        if hasattr(image_field, 'build_url'):
            # Remover 'format': 'auto' para evitar extensión .auto
            transform_for_url = {k: v for k, v in transformation.items() if k != 'format'}
            transform_for_url['fetch_format'] = 'auto'  # Usar fetch_format en vez de format
            return image_field.build_url(**transform_for_url)
        
        # Si es string (public_id), usar cloudinary directamente
        if isinstance(image_field, str):
            import cloudinary
            transform_for_url = {k: v for k, v in transformation.items() if k != 'format'}
            transform_for_url['fetch_format'] = 'auto'
            return cloudinary.CloudinaryImage(image_field).build_url(**transform_for_url)
        
        return str(image_field)
        
    except Exception as e:
        logger.error(f"Error generando URL de Cloudinary: {e}")
        return None

# =============================================================================
# FUNCIONES DE UPLOAD
# =============================================================================

def upload_to_cloudinary(file, tenant_slug, category, filename=None, **options):
    """
    Sube archivo a Cloudinary con carpeta de tenant.
    
    Args:
        file: Archivo a subir (file object o path)
        tenant_slug: Slug del cliente (ej: 'servelec-ingenieria')
        category: Categoría ('sections', 'services', 'branding')
        filename: Nombre del archivo (opcional, se auto-genera)
        **options: Opciones adicionales de Cloudinary
    
    Returns:
        Dict con resultado de upload (public_id, secure_url, etc.)
    
    Raises:
        ValueError: Si tenant_slug o category son inválidos
    """
    # Validaciones
    if not tenant_slug:
        raise ValueError("tenant_slug es requerido para uploads")
    
    valid_categories = ['sections', 'services', 'branding', 'gallery']
    if category not in valid_categories:
        raise ValueError(f"category debe ser uno de: {', '.join(valid_categories)}")
    
    # Construir folder
    folder = f"{tenant_slug}/{category}"
    
    # Opciones de upload
    upload_options = {
        'folder': folder,
        'resource_type': 'auto',
        'overwrite': True,
        'unique_filename': True,
    }
    
    if filename:
        upload_options['public_id'] = filename
    
    upload_options.update(options)
    
    # Log (sin secrets)
    logger.info(f"Uploading to Cloudinary: folder={folder}")
    
    try:
        result = cloudinary.uploader.upload(file, **upload_options)
        logger.info(f"Upload exitoso: public_id={result.get('public_id')}")
        return result
    except Exception as e:
        logger.error(f"Error en upload a Cloudinary: {e}")
        raise


def delete_from_cloudinary(public_id, resource_type='image'):
    """
    Elimina un recurso de Cloudinary.
    
    ⚠️ USAR CON PRECAUCIÓN - No hay undo
    
    Args:
        public_id: ID del recurso a eliminar
        resource_type: Tipo de recurso ('image', 'video', 'raw')
    
    Returns:
        Dict con resultado de eliminación
    """
    if not public_id:
        return None
    
    logger.warning(f"Eliminando de Cloudinary: {public_id}")
    
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        logger.info(f"Eliminación completada: {result}")
        return result
    except Exception as e:
        logger.error(f"Error eliminando de Cloudinary: {e}")
        raise


# =============================================================================
# VALIDACIONES
# =============================================================================

def validate_image_file(file, max_size_mb=10, allowed_formats=None):
    """
    Valida un archivo de imagen antes de subir.
    
    Args:
        file: Archivo a validar
        max_size_mb: Tamaño máximo en MB
        allowed_formats: Lista de extensiones permitidas
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if allowed_formats is None:
        allowed_formats = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']
    
    # Verificar tamaño
    if hasattr(file, 'size'):
        size_mb = file.size / (1024 * 1024)
        if size_mb > max_size_mb:
            return False, f"Archivo muy grande: {size_mb:.1f}MB (máx: {max_size_mb}MB)"
    
    # Verificar formato
    if hasattr(file, 'name'):
        ext = file.name.split('.')[-1].lower()
        if ext not in allowed_formats:
            return False, f"Formato no permitido: .{ext} (permitidos: {', '.join(allowed_formats)})"
    
    return True, None


def get_tenant_usage(tenant_slug):
    """
    Obtiene estadísticas de uso de Cloudinary para un tenant.
    
    Args:
        tenant_slug: Slug del cliente
    
    Returns:
        Dict con count y size de recursos
    """
    try:
        # Buscar recursos en la carpeta del tenant
        result = cloudinary.api.resources(
            type='upload',
            prefix=f"{tenant_slug}/",
            max_results=500
        )
        
        resources = result.get('resources', [])
        total_size = sum(r.get('bytes', 0) for r in resources)
        
        return {
            'count': len(resources),
            'size_bytes': total_size,
            'size_mb': total_size / (1024 * 1024),
            'resources': resources
        }
    except Exception as e:
        logger.error(f"Error obteniendo uso de tenant {tenant_slug}: {e}")
        return {
            'count': 0,
            'size_bytes': 0,
            'size_mb': 0,
            'resources': [],
            'error': str(e)
        }
