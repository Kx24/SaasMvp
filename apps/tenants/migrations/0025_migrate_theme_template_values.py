"""
#DEUDA-03: THEME_CHOICES se unifico (0024) -- 'servelec' paso a
'themes/servelec' (carpeta movida bajo templates/themes/), y
'themes/industrial' se retiro (no tenia carpeta real). Cualquier Client
con esos valores viejos queda migrado acá para que
apps/tenants/tests_theme_consistency.py se mantenga verde tras el
deploy.

'default' (el default viejo del campo, invalido desde siempre -- no
existe templates/default/) tambien se normaliza a 'themes/default' por
si algun Client se creo sin pasar template explicito.
"""
from django.db import migrations

RENAMES = {
    'servelec': 'themes/servelec',
    'electricidad': 'themes/servelec',
    'default': 'themes/default',
}


def migrate_theme_values(apps, schema_editor):
    Client = apps.get_model('tenants', 'Client')
    for old_value, new_value in RENAMES.items():
        Client.objects.filter(template=old_value).update(template=new_value)
    # Cualquier otro valor huerfano (ej. 'themes/industrial', 'industrial',
    # 'construccion', 'servicios' -- nunca tuvieron carpeta real) cae al
    # tema base en vez de servir el fallback global generico.
    valid_values = {'themes/default', 'themes/servelec'}
    Client.objects.exclude(template__in=valid_values).update(template='themes/default')


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0024_unify_theme_choices'),
    ]

    operations = [
        migrations.RunPython(migrate_theme_values, noop_reverse),
    ]
