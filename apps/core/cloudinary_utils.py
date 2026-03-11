# =============================================================================
# apps/core/cloudinary_utils.py
# =============================================================================
# Utilidades centralizadas para Cloudinary con soporte multi-tenant.
#
# ESTRUCTURA DE CARPETAS EN CLOUDINARY:
#   tenants/{tenant_slug}/sections/     ← imágenes de secciones (hero, about, etc.)
#   tenants/{tenant_slug}/services/     ← imágenes de servicios
#   tenants/{tenant_slug}/branding/     ← logo, favicon, logo_footer
#   tenants/{tenant_slug}/gallery/      ← galería de fotos
#   tenants/{tenant_slug}/catalog/      ← catálogo de productos
#   tenants/{tenant_slug}/videos/       ← videos propios (Cloudinary)
#   tenants/{tenant_slug}/documents/    ← PDFs, archivos descargables
#
# PARA AGREGAR UN NUEVO TIPO DE RECURSO:
#   1. Agregar la categoría a VALID_RESOURCE_TYPES
#   2. Agregar presets relevantes en CLOUDINARY_PRESETS o VIDEO_PRESETS
#   3. Usar cloudinary_upload_path('nueva_categoria') como upload_to en el modelo
#   4. Agregar template tag en cloudinary_tags.py si se necesita HTML especial
# =============================================================================

import logging
from django.conf import settings
import cloudinary
import cloudinary.uploader

logger = logging.getLogger(__name__)


# =============================================================================
# TIPOS DE RECURSOS VÁLIDOS
# Ampliar esta lista cuando se agreguen nuevas secciones/apps
# =============================================================================

VALID_RESOURCE_TYPES = [
    'sections',     # Secciones CMS (hero, about, contact)
    'services',     # Tarjetas de servicios
    'branding',     # Logo, favicon, logo_footer
    'gallery',      # Galería de fotos
    'catalog',      # Catálogo de productos
    'videos',       # Videos propios subidos a Cloudinary
    'documents',    # PDFs y archivos descargables
]


# =============================================================================
# BREAKPOINTS PARA RESPONSIVE (srcset)
# Usados por get_srcset_urls() y el template tag cloudinary_picture
# =============================================================================

BREAKPOINTS = {
    'mobile':  480,
    'tablet':  768,
    'desktop': 1200,
}


# =============================================================================
# PRESETS DE TRANSFORMACIÓN - IMÁGENES
#
# Cada preset define cómo Cloudinary transforma la imagen al servir.
# f_auto → entrega webp/avif según el navegador automáticamente
# q_auto → calidad óptima según el contenido de la imagen
# =============================================================================

CLOUDINARY_PRESETS = {

    # --- HERO / BANNER ---
    'hero': {
        'crop': 'fill', 'width': 1440, 'height': 700,
        'fetch_format': 'auto', 'quality': 'auto',
        'gravity': 'auto',
    },
    'hero_tablet': {
        'crop': 'fill', 'width': 768, 'height': 450,
        'fetch_format': 'auto', 'quality': 'auto',
        'gravity': 'auto',
    },
    'hero_mobile': {
        'crop': 'fill', 'width': 480, 'height': 320,
        'fetch_format': 'auto', 'quality': 'auto',
        'gravity': 'auto',
    },

    # --- SERVICIOS ---
    'service_card': {
        'crop': 'fill', 'width': 600, 'height': 400,
        'fetch_format': 'auto', 'quality': 'auto',
    },
    'service_card_mobile': {
        'crop': 'fill', 'width': 480, 'height': 320,
        'fetch_format': 'auto', 'quality': 'auto',
    },
    'service_detail': {
        'crop': 'fill', 'width': 1000, 'height': 600,
        'fetch_format': 'auto', 'quality': 'auto',
    },

    # --- ABOUT / SECCIONES GENÉRICAS ---
    'about': {
        'crop': 'fill', 'width': 900, 'height': 600,
        'fetch_format': 'auto', 'quality': 'auto',
        'gravity': 'auto',
    },
    'about_mobile': {
        'crop': 'fill', 'width': 480, 'height': 360,
        'fetch_format': 'auto', 'quality': 'auto',
        'gravity': 'auto',
    },

    # --- GALERÍA ---
    'gallery_full': {
        'crop': 'fill', 'width': 1200, 'height': 800,
        'fetch_format': 'auto', 'quality': 'auto',
    },
    'gallery_thumb': {
        'crop': 'fill', 'width': 400, 'height': 300,
        'fetch_format': 'auto', 'quality': 'auto',
    },
    'gallery_mobile': {
        'crop': 'fill', 'width': 480, 'height': 320,
        'fetch_format': 'auto', 'quality': 'auto',
    },

    # --- CATÁLOGO ---
    'catalog_card': {
        'crop': 'fill', 'width': 500, 'height': 500,
        'fetch_format': 'auto', 'quality': 'auto',
    },
    'catalog_detail': {
        'crop': 'limit', 'width': 1000, 'height': 1000,
        'fetch_format': 'auto', 'quality': 'auto',
    },
    'catalog_thumb': {
        'crop': 'fill', 'width': 200, 'height': 200,
        'fetch_format': 'auto', 'quality': 'auto',
    },

    # --- BRANDING ---
    'logo': {
        'crop': 'fit', 'width': 300, 'height': 100,
        'fetch_format': 'auto',
    },
    'logo_footer': {
        'crop': 'fit', 'width': 200, 'height': 80,
        'fetch_format': 'auto',
    },
    'favicon': {
        'crop': 'fill', 'width': 64, 'height': 64,
        'fetch_format': 'auto',
    },

    # --- SOCIAL MEDIA ---
    'og_image': {
        'crop': 'fill', 'width': 1200, 'height': 630,
        'fetch_format': 'auto', 'quality': 'auto',
    },

    # --- GENÉRICO / FALLBACK ---
    'thumbnail': {
        'crop': 'fill', 'width': 300, 'height': 200,
        'fetch_format': 'auto', 'quality': 'auto',
    },
    'avatar': {
        'crop': 'fill', 'width': 120, 'height': 120,
        'fetch_format': 'auto', 'quality': 'auto',
        'radius': 'max', 'gravity': 'face',
    },
}


# Mapa de preset base → variantes responsive
# Usado por get_srcset_urls() para saber qué presets corresponden a cada contexto
RESPONSIVE_PRESET_MAP = {
    'hero':         ('hero_mobile',        'hero_tablet',         'hero'),
    'service_card': ('service_card_mobile', 'service_card',        'service_detail'),
    'about':        ('about_mobile',        'about',               'about'),
    'gallery_full': ('gallery_mobile',      'gallery_thumb',       'gallery_full'),
    'catalog_card': ('catalog_thumb',       'catalog_card',        'catalog_detail'),
}


# =============================================================================
# PRESETS DE TRANSFORMACIÓN - VIDEOS
# =============================================================================

VIDEO_PRESETS = {
    'web_hd': {
        'quality': 'auto',
        'fetch_format': 'auto',      # Entrega mp4/webm según soporte del browser
        'video_codec': 'auto',
        'width': 1280, 'height': 720,
        'crop': 'limit',
    },
    'web_sd': {
        'quality': 'auto',
        'fetch_format': 'auto',
        'video_codec': 'auto',
        'width': 854, 'height': 480,
        'crop': 'limit',
    },
    'mobile': {
        'quality': 'auto',
        'fetch_format': 'auto',
        'video_codec': 'auto',
        'width': 480, 'height': 270,
        'crop': 'limit',
    },
    'thumbnail': {
        # Genera imagen estática del frame 0 del video
        'resource_type': 'video',
        'crop': 'fill', 'width': 640, 'height': 360,
        'fetch_format': 'auto', 'quality': 'auto',
    },
}


# =============================================================================
# FUNCIONES DE CARPETAS
# =============================================================================

def get_cloudinary_folder(tenant_slug: str, resource_type: str) -> str:
    """
    Genera la ruta de carpeta en Cloudinary para un tenant y tipo de recurso.

    Estructura: tenants/{tenant_slug}/{resource_type}/

    Args:
        tenant_slug: Slug único del cliente (ej: 'andesscale')
        resource_type: Tipo de recurso (debe estar en VALID_RESOURCE_TYPES)

    Returns:
        String con la ruta de carpeta (sin slash final)

    Raises:
        ValueError: Si algún argumento es inválido

    Ejemplo:
        get_cloudinary_folder('andesscale', 'sections')
        → 'tenants/andesscale/sections'
    """
    if not tenant_slug:
        raise ValueError("tenant_slug es requerido")

    if resource_type not in VALID_RESOURCE_TYPES:
        raise ValueError(
            f"resource_type '{resource_type}' inválido. "
            f"Opciones: {', '.join(VALID_RESOURCE_TYPES)}"
        )

    return f"tenants/{tenant_slug}/{resource_type}"


def cloudinary_upload_path(resource_type: str):
    """
    Factory que retorna una función upload_to compatible con CloudinaryField.

    Uso en modelos:
        from apps.core.cloudinary_utils import cloudinary_upload_path

        class Section(models.Model):
            image = CloudinaryField('image', folder=cloudinary_upload_path('sections'))

        class Service(models.Model):
            image = CloudinaryField('image', folder=cloudinary_upload_path('services'))

        class GalleryItem(models.Model):  # modelo futuro
            image = CloudinaryField('image', folder=cloudinary_upload_path('gallery'))

    IMPORTANTE: CloudinaryField usa el argumento 'folder' (no 'upload_to').
    La función retornada recibe (instance, filename) y devuelve la carpeta.

    Args:
        resource_type: Tipo de recurso (ej: 'sections', 'services', 'gallery')

    Returns:
        Función que recibe (instance, filename) y retorna la carpeta de Cloudinary
    """
    if resource_type not in VALID_RESOURCE_TYPES:
        raise ValueError(
            f"resource_type '{resource_type}' inválido. "
            f"Opciones: {', '.join(VALID_RESOURCE_TYPES)}"
        )

    def _get_folder(instance, filename):
        # Intentar obtener tenant_slug desde el modelo
        # Soporta: instance.client.slug, instance.slug (si el modelo ES el tenant)
        tenant_slug = None

        if hasattr(instance, 'client') and hasattr(instance.client, 'slug'):
            tenant_slug = instance.client.slug
        elif hasattr(instance, 'slug'):
            tenant_slug = instance.slug
        else:
            logger.warning(
                f"No se pudo obtener tenant_slug de {instance.__class__.__name__}. "
                f"Usando carpeta 'tenants/unknown/{resource_type}'"
            )
            tenant_slug = 'unknown'

        return get_cloudinary_folder(tenant_slug, resource_type)

    _get_folder.__name__ = f'upload_to_{resource_type}'
    return _get_folder


# =============================================================================
# FUNCIONES DE URL - IMÁGENES
# =============================================================================

def get_cloudinary_url(image_field, preset: str = 'thumbnail', **extra_options) -> str | None:
    """
    Genera URL de Cloudinary con transformaciones aplicadas.

    Args:
        image_field: CloudinaryField, CloudinaryResource o string (public_id)
        preset: Nombre del preset en CLOUDINARY_PRESETS
        **extra_options: Opciones adicionales que sobreescriben el preset

    Returns:
        URL completa de Cloudinary o None si hay error
    """
    if not image_field:
        return None

    if preset not in CLOUDINARY_PRESETS:
        logger.warning(f"Preset '{preset}' no encontrado, usando 'thumbnail'")
        preset = 'thumbnail'

    transformation = CLOUDINARY_PRESETS[preset].copy()
    transformation.update(extra_options)

    try:
        if hasattr(image_field, 'build_url'):
            return image_field.build_url(**transformation)

        if isinstance(image_field, str):
            return cloudinary.CloudinaryImage(image_field).build_url(**transformation)

        return str(image_field)

    except Exception as e:
        logger.error(f"Error generando URL de Cloudinary: {e}")
        return None


def get_srcset_urls(image_field, preset_base: str = 'hero') -> dict:
    """
    Genera URLs para los tres breakpoints responsive (mobile, tablet, desktop).

    Usa RESPONSIVE_PRESET_MAP para determinar qué presets corresponden a cada
    breakpoint. Si el preset_base no está en el mapa, genera las tres URLs con
    el mismo preset (útil para thumbnails genéricos).

    Args:
        image_field: CloudinaryField o string (public_id)
        preset_base: Preset base (ej: 'hero', 'service_card', 'gallery_full')

    Returns:
        Dict con keys 'mobile', 'tablet', 'desktop' y sus URLs.
        Incluye también 'srcset' listo para usar en el atributo HTML.

    Ejemplo de retorno:
        {
            'mobile':  'https://res.cloudinary.com/...480...',
            'tablet':  'https://res.cloudinary.com/...768...',
            'desktop': 'https://res.cloudinary.com/...1440...',
            'srcset':  'https://...480... 480w, https://...768... 768w, https://...1440... 1200w',
        }
    """
    if not image_field:
        return {'mobile': None, 'tablet': None, 'desktop': None, 'srcset': ''}

    # Obtener variantes del mapa, o usar el mismo preset para los tres
    if preset_base in RESPONSIVE_PRESET_MAP:
        mobile_p, tablet_p, desktop_p = RESPONSIVE_PRESET_MAP[preset_base]
    else:
        mobile_p = tablet_p = desktop_p = preset_base

    mobile_url  = get_cloudinary_url(image_field, mobile_p)
    tablet_url  = get_cloudinary_url(image_field, tablet_p)
    desktop_url = get_cloudinary_url(image_field, desktop_p)

    srcset_parts = []
    if mobile_url:
        srcset_parts.append(f"{mobile_url} {BREAKPOINTS['mobile']}w")
    if tablet_url:
        srcset_parts.append(f"{tablet_url} {BREAKPOINTS['tablet']}w")
    if desktop_url:
        srcset_parts.append(f"{desktop_url} {BREAKPOINTS['desktop']}w")

    return {
        'mobile':  mobile_url,
        'tablet':  tablet_url,
        'desktop': desktop_url,
        'srcset':  ', '.join(srcset_parts),
    }


# =============================================================================
# FUNCIONES DE URL - VIDEOS
# =============================================================================

def get_video_url(video_field, preset: str = 'web_hd') -> str | None:
    """
    Genera URL de video de Cloudinary con optimizaciones automáticas.

    Solo para videos almacenados en Cloudinary (no embeds de YouTube/Vimeo).
    Para embeds externos, usar directamente el URL del iframe.

    Args:
        video_field: CloudinaryField de video o string (public_id)
        preset: Nombre del preset en VIDEO_PRESETS

    Returns:
        URL optimizada del video o None
    """
    if not video_field:
        return None

    if preset not in VIDEO_PRESETS:
        logger.warning(f"Video preset '{preset}' no encontrado, usando 'web_hd'")
        preset = 'web_hd'

    transformation = VIDEO_PRESETS[preset].copy()
    transformation.pop('resource_type', None)  # No va en la URL

    try:
        if hasattr(video_field, 'build_url'):
            return video_field.build_url(resource_type='video', **transformation)

        if isinstance(video_field, str):
            return cloudinary.CloudinaryVideo(video_field).build_url(**transformation)

        return str(video_field)

    except Exception as e:
        logger.error(f"Error generando URL de video Cloudinary: {e}")
        return None


def get_video_thumbnail_url(video_field, width: int = 640, height: int = 360) -> str | None:
    """
    Genera URL de thumbnail (imagen) a partir de un video de Cloudinary.

    Cloudinary extrae automáticamente el primer frame del video.

    Args:
        video_field: CloudinaryField de video o string (public_id)
        width: Ancho del thumbnail
        height: Alto del thumbnail

    Returns:
        URL de imagen estática del primer frame del video
    """
    if not video_field:
        return None

    try:
        public_id = str(video_field) if not isinstance(video_field, str) else video_field

        return cloudinary.CloudinaryVideo(public_id).build_url(
            resource_type='video',
            crop='fill',
            width=width,
            height=height,
            fetch_format='auto',
            quality='auto',
            format='jpg',  # Forzar imagen
        )
    except Exception as e:
        logger.error(f"Error generando thumbnail de video: {e}")
        return None


def get_video_sources(video_field) -> list[dict]:
    """
    Genera múltiples fuentes de video para el elemento <video> HTML.

    Retorna mp4 y webm para máxima compatibilidad entre browsers.

    Args:
        video_field: CloudinaryField de video o string (public_id)

    Returns:
        Lista de dicts con 'url' y 'type' para usar en <source> tags.

    Ejemplo de uso en template:
        {% cloudinary_video_sources service.video as sources %}
        <video>
            {% for source in sources %}
                <source src="{{ source.url }}" type="{{ source.type }}">
            {% endfor %}
        </video>
    """
    if not video_field:
        return []

    sources = []

    # WebM: mejor compresión en Chrome/Firefox
    webm_url = get_video_url(video_field, 'web_hd')
    if webm_url:
        # Reemplazar formato para forzar webm
        try:
            public_id = str(video_field) if not isinstance(video_field, str) else video_field
            webm = cloudinary.CloudinaryVideo(public_id).build_url(
                resource_type='video',
                quality='auto',
                video_codec='auto',
                width=1280, height=720,
                crop='limit',
                format='webm',
            )
            sources.append({'url': webm, 'type': 'video/webm'})
        except Exception:
            pass

    # MP4: fallback universal
    mp4_url = get_video_url(video_field, 'web_hd')
    if mp4_url:
        sources.append({'url': mp4_url, 'type': 'video/mp4'})

    return sources


# =============================================================================
# FUNCIONES DE UPLOAD
# =============================================================================

def upload_to_cloudinary(file, tenant_slug: str, resource_type: str,
                         filename: str = None, **options) -> dict:
    """
    Sube archivo a Cloudinary en la carpeta correcta del tenant.

    Args:
        file: Archivo a subir (file object, path o URL)
        tenant_slug: Slug del cliente (ej: 'andesscale')
        resource_type: Tipo (debe estar en VALID_RESOURCE_TYPES)
        filename: Nombre personalizado (opcional, se auto-genera si no se provee)
        **options: Opciones adicionales para cloudinary.uploader.upload()

    Returns:
        Dict con resultado de Cloudinary (public_id, secure_url, width, height, etc.)

    Raises:
        ValueError: Si los argumentos son inválidos
        Exception: Si el upload falla en Cloudinary
    """
    folder = get_cloudinary_folder(tenant_slug, resource_type)

    upload_options = {
        'folder': folder,
        'resource_type': 'auto',
        'overwrite': True,
        'unique_filename': True,
        'use_filename': bool(filename),
    }

    if filename:
        upload_options['public_id'] = filename

    upload_options.update(options)

    logger.info(f"Upload Cloudinary → folder={folder}")

    try:
        result = cloudinary.uploader.upload(file, **upload_options)
        logger.info(f"Upload exitoso: public_id={result.get('public_id')}")
        return result
    except Exception as e:
        logger.error(f"Error en upload a Cloudinary: {e}")
        raise


def delete_from_cloudinary(public_id: str, resource_type: str = 'image') -> dict | None:
    """
    Elimina un recurso de Cloudinary.

    ⚠️ IRREVERSIBLE — usar con precaución.

    Args:
        public_id: ID del recurso (ej: 'tenants/andesscale/sections/hero')
        resource_type: 'image', 'video' o 'raw'

    Returns:
        Dict con resultado o None si public_id está vacío
    """
    if not public_id:
        return None

    logger.warning(f"Eliminando de Cloudinary: {public_id} [{resource_type}]")

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

def validate_image_file(file, max_size_mb: float = 10,
                        allowed_formats: list = None) -> tuple[bool, str | None]:
    """
    Valida un archivo de imagen antes de subirlo.

    Args:
        file: Archivo a validar (debe tener atributos .size y .name)
        max_size_mb: Tamaño máximo permitido en MB
        allowed_formats: Extensiones permitidas (default: jpg, jpeg, png, gif, webp, svg)

    Returns:
        Tuple (is_valid: bool, error_message: str | None)
    """
    if allowed_formats is None:
        allowed_formats = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']

    if hasattr(file, 'size'):
        size_mb = file.size / (1024 * 1024)
        if size_mb > max_size_mb:
            return False, f"Archivo muy grande: {size_mb:.1f}MB (máx: {max_size_mb}MB)"

    if hasattr(file, 'name'):
        ext = file.name.rsplit('.', 1)[-1].lower()
        if ext not in allowed_formats:
            return False, f"Formato no permitido: .{ext} (permitidos: {', '.join(allowed_formats)})"

    return True, None


def validate_video_file(file, max_size_mb: float = 200,
                        allowed_formats: list = None) -> tuple[bool, str | None]:
    """
    Valida un archivo de video antes de subirlo.

    Args:
        file: Archivo a validar
        max_size_mb: Tamaño máximo en MB (default: 200MB)
        allowed_formats: Extensiones permitidas

    Returns:
        Tuple (is_valid: bool, error_message: str | None)
    """
    if allowed_formats is None:
        allowed_formats = ['mp4', 'mov', 'avi', 'webm', 'mkv']

    if hasattr(file, 'size'):
        size_mb = file.size / (1024 * 1024)
        if size_mb > max_size_mb:
            return False, f"Video muy grande: {size_mb:.1f}MB (máx: {max_size_mb}MB)"

    if hasattr(file, 'name'):
        ext = file.name.rsplit('.', 1)[-1].lower()
        if ext not in allowed_formats:
            return False, f"Formato de video no permitido: .{ext} (permitidos: {', '.join(allowed_formats)})"

    return True, None


# =============================================================================
# ESTADÍSTICAS DE USO POR TENANT
# =============================================================================

def get_tenant_usage(tenant_slug: str) -> dict:
    """
    Obtiene estadísticas de uso de Cloudinary para un tenant.

    Busca todos los recursos bajo 'tenants/{tenant_slug}/'

    Args:
        tenant_slug: Slug del cliente

    Returns:
        Dict con count, size_bytes, size_mb, resources y breakdown por categoría
    """
    try:
        result = cloudinary.api.resources(
            type='upload',
            prefix=f"tenants/{tenant_slug}/",
            max_results=500
        )

        resources = result.get('resources', [])
        total_size = sum(r.get('bytes', 0) for r in resources)

        # Breakdown por categoría
        breakdown = {}
        for resource in resources:
            public_id = resource.get('public_id', '')
            # Extraer categoría: tenants/{slug}/{category}/...
            parts = public_id.split('/')
            category = parts[2] if len(parts) > 2 else 'other'
            if category not in breakdown:
                breakdown[category] = {'count': 0, 'size_bytes': 0}
            breakdown[category]['count'] += 1
            breakdown[category]['size_bytes'] += resource.get('bytes', 0)

        return {
            'count': len(resources),
            'size_bytes': total_size,
            'size_mb': round(total_size / (1024 * 1024), 2),
            'breakdown': breakdown,
            'resources': resources,
        }
    except Exception as e:
        logger.error(f"Error obteniendo uso de tenant {tenant_slug}: {e}")
        return {
            'count': 0, 'size_bytes': 0, 'size_mb': 0,
            'breakdown': {}, 'resources': [], 'error': str(e),
        }