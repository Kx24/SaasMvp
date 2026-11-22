# BIZ-04 (2/3): copia el slug de texto al FK. Slug sin Plan -> FK null (y se informa).
from django.db import migrations


def slug_to_fk(apps, schema_editor):
    Client = apps.get_model('tenants', 'Client')
    Plan = apps.get_model('orders', 'Plan')
    plans = {p.slug: p for p in Plan.objects.all()}
    for client in Client.objects.all():
        plan = plans.get(client.plan)
        if plan is None:
            print(
                f"\n  [BIZ-04] Client '{client.slug}': no existe Plan con slug "
                f"'{client.plan}'; plan queda en null."
            )
        client.plan_fk = plan
        client.save(update_fields=['plan_fk'])


def fk_to_slug(apps, schema_editor):
    Client = apps.get_model('tenants', 'Client')
    for client in Client.objects.select_related('plan_fk'):
        client.plan = client.plan_fk.slug if client.plan_fk else 'essential'
        client.save(update_fields=['plan'])


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0033_client_plan_fk_temp'),
    ]

    operations = [
        migrations.RunPython(slug_to_fk, fk_to_slug),
    ]
