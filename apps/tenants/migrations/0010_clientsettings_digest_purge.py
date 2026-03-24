# =============================================================================
# apps/tenants/migrations/0010_clientsettings_digest_purge.py
# =============================================================================
# Agrega campos de configuración de digest y purga a ClientSettings.
#
# NOTA: Ajustar el número de dependencia al último migration real de tenants.
#       Actualmente el último es 0009_alter_client_plan.py
# =============================================================================

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0009_alter_client_plan'),
    ]

    operations = [
        # ── Digest ────────────────────────────────────────────────────────────
        migrations.AddField(
            model_name='clientsettings',
            name='digest_enabled',
            field=models.BooleanField(
                default=False,
                help_text='Activar resumen periódico de mensajes por email',
            ),
        ),
        migrations.AddField(
            model_name='clientsettings',
            name='digest_frequency',
            field=models.CharField(
                max_length=10,
                default='weekly',
                choices=[
                    ('daily',  'Diario'),
                    ('weekly', 'Semanal'),
                ],
                help_text='Con qué frecuencia enviar el resumen',
            ),
        ),
        # ── Purga ─────────────────────────────────────────────────────────────
        migrations.AddField(
            model_name='clientsettings',
            name='auto_purge_enabled',
            field=models.BooleanField(
                default=False,
                help_text='Eliminar mensajes antiguos ya leídos o respondidos automáticamente',
            ),
        ),
        migrations.AddField(
            model_name='clientsettings',
            name='inbox_retention_days',
            field=models.PositiveIntegerField(
                default=30,
                help_text='Días a retener mensajes leídos/respondidos antes de purgarlos (mínimo 7)',
            ),
        ),
    ]
