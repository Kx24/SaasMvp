# BIZ-04 (3/3): borra el CharField y renombra el FK a `plan`.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0034_client_plan_fk_data'),
    ]

    operations = [
        migrations.RemoveField(model_name='client', name='plan'),
        migrations.RenameField(model_name='client', old_name='plan_fk', new_name='plan'),
        migrations.AlterField(
            model_name='client',
            name='plan',
            field=models.ForeignKey(
                blank=True, null=True,
                help_text='Plan contratado por el cliente',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='clients', to='orders.plan',
            ),
        ),
    ]
