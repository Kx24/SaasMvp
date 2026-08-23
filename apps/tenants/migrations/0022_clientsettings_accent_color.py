# Cherry-pick de AUD-11 Paso 3 a develop: accent_color existia en el
# modelo de feature/RanchocachimbaEtapa1 desde RC-03 (migracion 0018 ahi),
# pero esa migracion (RC-especifica) nunca llego a develop. BrandingForm
# ahora declara accent_color en Meta.fields -- sin esta columna, el
# ModelForm ni siquiera puede importarse en develop.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0021_normalize_font_family_values'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientsettings',
            name='accent_color',
            field=models.CharField(default='#F59E0B', max_length=7),
        ),
    ]
