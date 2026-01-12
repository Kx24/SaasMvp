# =============================================================================
# apps/website/migrations/XXXX_migrate_to_cloudinary.py
# =============================================================================
# Migración para cambiar de ImageField a CloudinaryField
# 
# ⚠️ INSTRUCCIONES:
# 1. Renombrar este archivo al número de migración correspondiente
# 2. Actualizar 'dependencies' con tu última migración
# 3. Ejecutar: python manage.py migrate
# =============================================================================

from django.db import migrations
import cloudinary.models


class Migration(migrations.Migration):

    dependencies = [
        # ⚠️ ACTUALIZAR CON TU ÚLTIMA MIGRACIÓN
        ('website', '0004_alter_section_section_type'),
    ]

    operations = [
        # Cambiar Section.image de ImageField a CloudinaryField
        migrations.AlterField(
            model_name='section',
            name='image',
            field=cloudinary.models.CloudinaryField(
                'image',
                blank=True,
                null=True,
                help_text='Imagen de la sección (se sube a Cloudinary)'
            ),
        ),
        
        # Cambiar Service.image de ImageField a CloudinaryField
        migrations.AlterField(
            model_name='service',
            name='image',
            field=cloudinary.models.CloudinaryField(
                'image',
                blank=True,
                null=True,
                help_text='Imagen del servicio (se sube a Cloudinary)'
            ),
        ),
        
        # Si tienes Testimonial y quieres mantenerlo, descomentar:
        # migrations.AlterField(
        #     model_name='testimonial',
        #     name='avatar',
        #     field=cloudinary.models.CloudinaryField(
        #         'image',
        #         blank=True,
        #         null=True,
        #         help_text='Foto del cliente (se sube a Cloudinary)'
        #     ),
        # ),
    ]
