"""
#AUD-11 Paso 3: font_family pasa a ser una lista curada (0020). Los
valores existentes (ej. el default viejo 'Inter, sans-serif', un stack
CSS completo en vez de un nombre de fuente) no matchean ningún choice
-- normalizarlos acá para que ningún ClientSettings quede con un valor
fuera de la lista curada tras el deploy.

Se toma la parte antes de la primera coma (';Inter, sans-serif' ->
'Inter'); si el resultado no está en la lista curada, cae a 'Inter'
-- mismo fallback que ya usaban todos los temas antes de esta card.
"""
from django.db import migrations

CURATED = {'Inter', 'Outfit', 'Fraunces', 'Space Grotesk'}


def normalize_font_family(apps, schema_editor):
    ClientSettings = apps.get_model('tenants', 'ClientSettings')
    for settings_obj in ClientSettings.objects.exclude(font_family__in=CURATED):
        bare_name = settings_obj.font_family.split(',')[0].strip()
        settings_obj.font_family = bare_name if bare_name in CURATED else 'Inter'
        settings_obj.save(update_fields=['font_family'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0020_alter_clientsettings_font_family'),
    ]

    operations = [
        migrations.RunPython(normalize_font_family, noop_reverse),
    ]
