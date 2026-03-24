# =============================================================================
# apps/website/migrations/0007_contactsubmission_form_source_spam.py
# =============================================================================
# Agrega:
#   - form_source: identifica desde qué sección del sitio llegó el mensaje
#                  (hero, footer, page, modal). Reemplaza el campo source genérico.
#   - is_spam:     marcado por el honeypot. No elimina el registro, lo oculta.
#
# NOTA: El campo `source` original se mantiene para compatibilidad.
#       form_source es más específico y controlado.
# =============================================================================

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        # Ajustar al número real de la última migración del proyecto
        ('website', '0006_delete_testimonial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactsubmission',
            name='form_source',
            field=models.CharField(
                max_length=20,
                default='page',
                choices=[
                    ('hero',   'Hero / Banner principal'),
                    ('footer', 'Footer del sitio'),
                    ('page',   'Página de contacto'),
                    ('modal',  'Modal emergente'),
                ],
                help_text='Sección del sitio desde donde se envió el formulario',
            ),
        ),
        migrations.AddField(
            model_name='contactsubmission',
            name='is_spam',
            field=models.BooleanField(
                default=False,
                help_text='Marcado como spam por el honeypot. El registro se conserva para auditoría.',
            ),
        ),
        migrations.AddIndex(
            model_name='contactsubmission',
            index=models.Index(
                fields=['client', 'is_spam'],
                name='website_con_client_spam_idx',
            ),
        ),
    ]
