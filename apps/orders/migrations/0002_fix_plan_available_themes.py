"""
#DEUDA-03: Plan.available_themes se poblaba con setup_plans.py, que
ofrecia slugs ('electricidad', 'industrial', 'custom') que nunca
coincidieron con una carpeta real de templates/ (ver
apps/orders/tests/test_plan_themes.py). Un Plan ya creado con esos
valores queda con el bug aunque se corrija setup_plans.py, porque los
Plan no se recrean solos -- normalizarlo acá.
"""
from django.db import migrations

# Mapea cualquier slug viejo/roto a un valor real de Client.THEME_CHOICES.
# 'custom' (Enterprise, diseno 100% a medida) se retira: nunca tuvo
# carpeta y el plan de disenio a medida no se resuelve via el picker.
RENAMES = {
    'default': 'themes/default',
    'electricidad': 'themes/servelec',
    'servelec': 'themes/servelec',
}
DROP = {'industrial', 'construccion', 'servicios', 'custom'}


def fix_available_themes(apps, schema_editor):
    Plan = apps.get_model('orders', 'Plan')
    for plan in Plan.objects.all():
        themes = plan.available_themes if isinstance(plan.available_themes, list) else []
        fixed = []
        for slug in themes:
            if slug in DROP:
                continue
            fixed.append(RENAMES.get(slug, slug))
        # De-duplicar preservando orden.
        fixed = list(dict.fromkeys(fixed))
        if fixed != themes:
            plan.available_themes = fixed
            plan.save(update_fields=['available_themes'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(fix_available_themes, noop_reverse),
    ]
