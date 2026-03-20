from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("marketing", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="seoconfig",
            name="google_verification_file",
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name="Google Verification File",
                help_text=(
                    "Solo el código sin 'google' ni '.html'. "
                    "Ej: si Google te da 'google1a2b3c4d.html', escribe solo '1a2b3c4d'. "
                    "Genera la URL: /google1a2b3c4d.html"
                ),
            ),
        ),
    ]
