# BIZ-04 (1/3): FK temporal nullable hacia orders.Plan.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_remove_plan_max_pages'),
        ('tenants', '0032_remove_client_max_pages'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='plan_fk',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+', to='orders.plan',
            ),
        ),
    ]
