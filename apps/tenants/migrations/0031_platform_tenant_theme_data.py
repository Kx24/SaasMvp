"""
COMP-02 / BOLT-56: el tenant de la plataforma pasa a `themes/andesscale`.

Migración solo de datos. Si existe el Client cuyo slug es
`settings.PLATFORM_TENANT_SLUG`, su `template` se fija en
'themes/andesscale'. Reversible: devuelve a 'themes/default'.
El loader conserva un fallback por slug, así que una base sin migrar
sigue abriendo la home de la plataforma.
"""
from django.conf import settings
from django.db import migrations

PLATFORM_THEME = 'themes/andesscale'
DEFAULT_THEME = 'themes/default'


def set_platform_theme(apps, schema_editor):
    Client = apps.get_model('tenants', 'Client')
    slug = getattr(settings, 'PLATFORM_TENANT_SLUG', 'andesscale')
    Client.objects.filter(slug=slug).update(template=PLATFORM_THEME)


def unset_platform_theme(apps, schema_editor):
    Client = apps.get_model('tenants', 'Client')
    Client.objects.filter(template=PLATFORM_THEME).update(template=DEFAULT_THEME)


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0030_platform_theme_choice'),
    ]

    operations = [
        migrations.RunPython(set_platform_theme, unset_platform_theme),
    ]
