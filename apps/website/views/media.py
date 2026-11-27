"""MOD-01 parte 1b: subida firmada a Cloudinary y alta de embeds (endpoints JSON).

El servidor fija carpeta y public_id, y no confía en el aviso del navegador:
consulta a Cloudinary antes de crear el ``MediaAsset``.
"""
import logging
import time
import uuid

import cloudinary
import cloudinary.api
import cloudinary.utils
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.accounts.decorators import tenant_permission_required
from apps.core.cloudinary_utils import delete_from_cloudinary, get_cloudinary_folder
from apps.core.rate_limit import RateLimiter
from apps.tenants.modules import ModuleLimitReached, check_limit, module_required

from ..media import parse_video_url
from ..models import MediaAsset

logger = logging.getLogger(__name__)

ALLOWED_FORMATS = ('jpg', 'jpeg', 'png', 'webp', 'heic')
SIGNATURE_LIMIT = 30
SIGNATURE_PERIOD = 600


def _error(message, status):
    return JsonResponse({'error': message}, status=status)


def _limit_error(client):
    try:
        check_limit(client, 'media')
    except ModuleLimitReached as exc:
        return _error(exc.message, 403)
    return None


def _discard(public_id):
    try:
        delete_from_cloudinary(public_id)
    except Exception:
        logger.exception('No se pudo borrar %s de Cloudinary', public_id)


def _asset_payload(asset):
    return {
        'id': asset.id,
        'kind': asset.kind,
        'thumbnail_url': asset.thumbnail_url(),
    }


@require_POST
@tenant_permission_required('edit_content')
@module_required('media')
def media_upload_signature(request):
    client = request.client
    limiter = RateLimiter(
        request, scope='media_sign', limit=SIGNATURE_LIMIT, period=SIGNATURE_PERIOD
    )
    if limiter.is_exceeded():
        return _error('Demasiados intentos. Espera unos minutos.', 429)
    limiter.increment()

    blocked = _limit_error(client)
    if blocked:
        return blocked

    params = {
        'folder': get_cloudinary_folder(client.slug, 'media'),
        'public_id': uuid.uuid4().hex,
        'timestamp': int(time.time()),
        'allowed_formats': ','.join(ALLOWED_FORMATS),
    }
    config = cloudinary.config()
    signature = cloudinary.utils.api_sign_request(params, config.api_secret)
    return JsonResponse({
        'signature': signature,
        'timestamp': params['timestamp'],
        'api_key': config.api_key,
        'cloud_name': config.cloud_name,
        'folder': params['folder'],
        'public_id': params['public_id'],
        'allowed_formats': params['allowed_formats'],
        'upload_url': f'https://api.cloudinary.com/v1_1/{config.cloud_name}/image/upload',
    })


@require_POST
@tenant_permission_required('edit_content')
@module_required('media')
def media_upload_confirm(request):
    client = request.client
    public_id = (request.POST.get('public_id') or '').strip()
    folder = get_cloudinary_folder(client.slug, 'media')
    if not public_id.startswith(f'{folder}/') or '..' in public_id:
        return _error('Archivo no válido.', 400)

    existing = MediaAsset.objects.filter(
        client=client, kind=MediaAsset.KIND_IMAGE, image=public_id
    ).first()
    if existing:
        return JsonResponse(_asset_payload(existing), status=200)

    try:
        resource = cloudinary.api.resource(public_id)
    except Exception:
        return _error('No se encontró el archivo subido.', 400)

    max_mb = settings.MEDIA_MAX_IMAGE_MB
    size = resource.get('bytes') or 0
    fmt = (resource.get('format') or '').lower()
    if size > max_mb * 1024 * 1024:
        _discard(public_id)
        return _error(f'La imagen supera el máximo de {max_mb} MB.', 400)
    if fmt not in ALLOWED_FORMATS:
        _discard(public_id)
        return _error('Formato no permitido. Usa JPG, PNG, WebP o HEIC.', 400)

    blocked = _limit_error(client)
    if blocked:
        _discard(public_id)
        return blocked

    asset = MediaAsset.objects.create(
        client=client,
        kind=MediaAsset.KIND_IMAGE,
        image=public_id,
        bytes=size,
        width=resource.get('width'),
        height=resource.get('height'),
        format=fmt,
        uploaded_by=request.user,
    )
    return JsonResponse(_asset_payload(asset), status=201)


@require_POST
@tenant_permission_required('edit_content')
@module_required('media')
def media_embed_add(request):
    client = request.client
    try:
        provider, video_id = parse_video_url(request.POST.get('url'))
    except ValidationError as exc:
        return _error(' '.join(exc.messages), 400)

    def payload(asset):
        return {**_asset_payload(asset), 'embed_url': asset.embed_url()}

    existing = MediaAsset.objects.filter(
        client=client, kind=MediaAsset.KIND_EMBED, provider=provider, video_id=video_id
    ).first()
    if existing:
        return JsonResponse(payload(existing), status=200)

    embeds = MediaAsset.objects.filter(client=client, kind=MediaAsset.KIND_EMBED).count()
    if embeds >= settings.MEDIA_MAX_EMBEDS:
        return _error('Alcanzaste el máximo de videos embebidos.', 403)

    asset = MediaAsset.objects.create(
        client=client,
        kind=MediaAsset.KIND_EMBED,
        provider=provider,
        video_id=video_id,
        uploaded_by=request.user,
    )
    return JsonResponse(payload(asset), status=201)
