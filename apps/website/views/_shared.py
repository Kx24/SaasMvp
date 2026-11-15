import logging

from django.contrib import messages

from apps.core.cloudinary_utils import validate_image_file

logger = logging.getLogger(__name__)


def _image_upload_ok(request, uploaded_file) -> bool:
    """
    Valida una imagen subida desde el dashboard antes de enviarla a
    Cloudinary (SEC-11). Si no sirve, deja el motivo en messages y
    devuelve False; la vista decide qué hacer con el resto del formulario.
    """
    ok, error = validate_image_file(uploaded_file)
    if not ok:
        messages.error(request, f'No se subió la imagen: {error}')
    return ok
