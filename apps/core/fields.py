"""
Campos de modelo reutilizables.

EncryptedTextField (#SEC-06): cifra el valor en reposo con MultiFernet.
Las claves vienen de ``settings.FIELD_ENCRYPTION_KEYS`` (lista de claves
Fernet; la primera cifra, todas descifran, lo que permite rotar sin downtime).
Se lee en cada uso para que ``override_settings`` funcione en tests.
"""
from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models

PREFIX = 'fernet:'


def _multifernet():
    keys = getattr(settings, 'FIELD_ENCRYPTION_KEYS', None) or []
    if not keys:
        raise ImproperlyConfigured(
            "FIELD_ENCRYPTION_KEY no está configurada: no se pueden "
            "cifrar/descifrar campos protegidos."
        )
    try:
        return MultiFernet([Fernet(k) for k in keys])
    except (ValueError, TypeError) as exc:
        raise ImproperlyConfigured(
            "FIELD_ENCRYPTION_KEY contiene una clave Fernet inválida."
        ) from exc


def encrypt_value(value):
    """Devuelve ``fernet:<token>``; None/'' y valores ya cifrados pasan tal cual."""
    if value is None or value == '' or str(value).startswith(PREFIX):
        return value
    token = _multifernet().encrypt(str(value).encode('utf-8')).decode('ascii')
    return PREFIX + token


def decrypt_value(value):
    """Descifra ``fernet:<token>``; cualquier otro valor (texto plano) pasa tal cual."""
    if not isinstance(value, str) or not value.startswith(PREFIX):
        return value
    try:
        return _multifernet().decrypt(value[len(PREFIX):].encode('ascii')).decode('utf-8')
    except InvalidToken as exc:
        raise ImproperlyConfigured(
            "No se pudo descifrar un campo: FIELD_ENCRYPTION_KEY no coincide "
            "con la clave usada para cifrarlo."
        ) from exc


class EncryptedTextField(models.TextField):
    """TextField que guarda ``fernet:<token>`` en la base y expone texto plano."""

    def get_prep_value(self, value):
        return encrypt_value(value)

    def from_db_value(self, value, expression, connection):
        return decrypt_value(value)

    def to_python(self, value):
        return decrypt_value(value)
