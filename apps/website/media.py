"""Parser de embeds de video (MOD-01): solo YouTube y Vimeo, se guarda el ID."""
import re
from urllib.parse import parse_qs, urlparse

from django.core.exceptions import ValidationError

_YOUTUBE_ID = re.compile(r'^[A-Za-z0-9_-]{11}$')
_VIMEO_ID = re.compile(r'^[0-9]+$')
_YOUTUBE_HOSTS = {'youtube.com', 'www.youtube.com', 'm.youtube.com'}
_MENSAJE = (
    'Pega un enlace válido de YouTube o Vimeo '
    '(por ejemplo https://youtu.be/XXXXXXXXXXX o https://vimeo.com/123456789).'
)


def _segments(path):
    return [p for p in path.split('/') if p]


def _second_segment(path, prefix):
    parts = _segments(path)
    if len(parts) == 2 and parts[0] == prefix:
        return parts[1]
    return None


def _only_segment(path):
    parts = _segments(path)
    return parts[0] if len(parts) == 1 else None


def parse_video_url(url):
    """Devuelve ``(provider, video_id)`` o lanza ``ValidationError``."""
    if not isinstance(url, str):
        raise ValidationError(_MENSAJE)
    try:
        parsed = urlparse(url.strip())
        host = (parsed.hostname or '').lower()
    except ValueError:
        raise ValidationError(_MENSAJE)
    if parsed.scheme not in ('http', 'https') or not host:
        raise ValidationError(_MENSAJE)

    provider = None
    candidate = None
    if host in _YOUTUBE_HOSTS:
        provider = 'youtube'
        if parsed.path.rstrip('/') == '/watch':
            candidate = (parse_qs(parsed.query).get('v') or [None])[0]
        else:
            candidate = (
                _second_segment(parsed.path, 'shorts')
                or _second_segment(parsed.path, 'embed')
            )
    elif host == 'youtu.be':
        provider = 'youtube'
        candidate = _only_segment(parsed.path)
    elif host in ('vimeo.com', 'www.vimeo.com'):
        provider = 'vimeo'
        candidate = _only_segment(parsed.path)
    elif host == 'player.vimeo.com':
        provider = 'vimeo'
        candidate = _second_segment(parsed.path, 'video')

    if provider == 'youtube' and candidate and _YOUTUBE_ID.match(candidate):
        return provider, candidate
    if provider == 'vimeo' and candidate and _VIMEO_ID.match(candidate):
        return provider, candidate
    raise ValidationError(_MENSAJE)
