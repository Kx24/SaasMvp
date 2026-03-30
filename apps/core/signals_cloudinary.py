# =============================================================================
# apps/core/signals_cloudinary.py
# =============================================================================
# Signals post_delete para eliminar assets de Cloudinary cuando se borra
# un objeto Django que contiene CloudinaryFields.
#
# MODELOS CUBIERTOS:
#   - apps.tenants.ClientSettings  (logo, logo_footer, favicon)
#   - apps.website.Section         (imagen)
#   - apps.website.Service         (imagen)
#   - apps.marketing.SEOConfig     (og_image)
#
# REGISTRO:
#   Cada AppConfig conecta sus signals en ready():
#     apps/tenants/apps.py  → ClientSettings
#     apps/website/apps.py  → Section, Service
#     apps/marketing/apps.py → SEOConfig
#
# ALCANCE (Fase 1):
#   Solo post_delete. Los reemplazos de imagen (pre_save) quedan para Fase 2.
# =============================================================================

import logging
from cloudinary import CloudinaryResource
from apps.core.cloudinary_utils import delete_from_cloudinary

logger = logging.getLogger(__name__)


def _get_cloudinary_fields(instance):
    """
    Itera los campos del modelo y retorna los que tienen valor en Cloudinary.

    Detecta CloudinaryField inspeccionando si el valor tiene public_id,
    compatible con CloudinaryResource y django-cloudinary-storage.

    Returns:
        List of (field_name, public_id, resource_type) tuples
    """
    fields = []
    for field in instance._meta.get_fields():
        # Solo campos concretos (no relaciones)
        if not hasattr(field, 'attname'):
            continue

        value = getattr(instance, field.attname, None)
        if not value:
            continue

        # CloudinaryField almacena un CloudinaryResource o un string con public_id
        public_id = None
        resource_type = 'image'

        if isinstance(value, CloudinaryResource):
            public_id = value.public_id
            resource_type = getattr(value, 'resource_type', 'image') or 'image'
        elif isinstance(value, str) and value.startswith('tenants/'):
            # CharField legacy con public_id de Cloudinary
            public_id = value

        if public_id:
            fields.append((field.name, public_id, resource_type))

    return fields


def delete_cloudinary_assets_on_delete(sender, instance, **kwargs):
    """
    Handler genérico post_delete.

    Itera todos los CloudinaryFields del modelo eliminado y destruye
    cada asset en Cloudinary usando delete_from_cloudinary().

    Falla silenciosamente por campo (loguea el error pero no interrumpe
    el flujo de Django) para evitar que un fallo de Cloudinary bloquee
    la eliminación del registro de DB.
    """
    model_name = instance.__class__.__name__
    cloudinary_fields = _get_cloudinary_fields(instance)

    if not cloudinary_fields:
        logger.debug(f"[Cloudinary] {model_name} pk={instance.pk}: sin assets que limpiar")
        return

    for field_name, public_id, resource_type in cloudinary_fields:
        try:
            result = delete_from_cloudinary(public_id, resource_type=resource_type)
            if result and result.get('result') == 'ok':
                logger.info(
                    f"[Cloudinary] Asset eliminado — modelo={model_name} "
                    f"pk={instance.pk} campo={field_name} public_id={public_id}"
                )
            else:
                logger.warning(
                    f"[Cloudinary] Respuesta inesperada al eliminar — "
                    f"modelo={model_name} campo={field_name} "
                    f"public_id={public_id} resultado={result}"
                )
        except Exception as e:
            logger.error(
                f"[Cloudinary] Error al eliminar asset — "
                f"modelo={model_name} pk={instance.pk} "
                f"campo={field_name} public_id={public_id} error={e}"
            )


# =============================================================================
# FUNCIÓN DE REGISTRO
# Llamar desde el ready() de cada AppConfig relevante.
# =============================================================================

def register_cloudinary_signals():
    """
    Conecta post_delete para todos los modelos con CloudinaryFields.

    Uso en AppConfig.ready():
        from apps.core.signals_cloudinary import register_cloudinary_signals
        register_cloudinary_signals()

    Se importan los modelos aquí (no en el módulo) para respetar el orden
    de inicialización de Django y evitar AppRegistryNotReady.
    """
    from django.db.models.signals import post_delete

    # apps.tenants
    try:
        from apps.tenants.models import ClientSettings
        post_delete.connect(
            delete_cloudinary_assets_on_delete,
            sender=ClientSettings,
            dispatch_uid='cloudinary_delete_clientsettings',
        )
        logger.debug("[Cloudinary] Signal conectado: ClientSettings")
    except ImportError:
        logger.warning("[Cloudinary] No se pudo importar ClientSettings")

    # apps.website
    try:
        from apps.website.models import Section, Service
        post_delete.connect(
            delete_cloudinary_assets_on_delete,
            sender=Section,
            dispatch_uid='cloudinary_delete_section',
        )
        post_delete.connect(
            delete_cloudinary_assets_on_delete,
            sender=Service,
            dispatch_uid='cloudinary_delete_service',
        )
        logger.debug("[Cloudinary] Signals conectados: Section, Service")
    except ImportError:
        logger.warning("[Cloudinary] No se pudo importar Section o Service")

    # apps.marketing
    try:
        from apps.marketing.models import SEOConfig
        post_delete.connect(
            delete_cloudinary_assets_on_delete,
            sender=SEOConfig,
            dispatch_uid='cloudinary_delete_seoconfig',
        )
        logger.debug("[Cloudinary] Signal conectado: SEOConfig")
    except ImportError:
        logger.warning("[Cloudinary] No se pudo importar SEOConfig")
