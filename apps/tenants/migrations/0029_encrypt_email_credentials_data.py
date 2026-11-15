"""
#SEC-06: cifra en reposo las credenciales ya guardadas en texto plano
(ClientEmailSettings.smtp_password / api_key). Reversible: el reverso las
descifra de vuelta a texto plano (necesario para volver a 0027).
"""
from django.db import migrations
from django.db.models import Value

FIELDS = ('smtp_password', 'api_key')


def encrypt_existing(apps, schema_editor):
    # Leer pasa por from_db_value (texto plano o ya cifrado -> claro) y
    # guardar pasa por get_prep_value (claro -> fernet:...). Idempotente.
    Model = apps.get_model('tenants', 'ClientEmailSettings')
    for obj in Model.objects.iterator():
        if any(getattr(obj, f) for f in FIELDS):
            obj.save(update_fields=list(FIELDS))


def decrypt_existing(apps, schema_editor):
    # update() con Value(...) no pasa por get_prep_value del campo, así que
    # queda texto plano en la base.
    Model = apps.get_model('tenants', 'ClientEmailSettings')
    for obj in Model.objects.iterator():
        values = {f: Value(getattr(obj, f) or '') for f in FIELDS}
        Model._base_manager.filter(pk=obj.pk).update(**values)


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0028_encrypt_email_credentials'),
    ]

    operations = [
        migrations.RunPython(encrypt_existing, decrypt_existing),
    ]
