"""
#DEUDA-02 (Fase 1): gallery_type (hero/gallery) -> section (FK).

Cada GalleryItem existente queda linkeado a la Section del section_type
correspondiente. La Section 'hero' ya la crea provision_tenant.py, pero
'gallery' no (hallazgo de la investigacion de esta card) -- se usa
get_or_create para no fallar contra datos reales que nunca tuvieron esa
Section.

Cualquier gallery_type que no sea 'hero'/'gallery' (no deberia haber, pero
el campo era CharField libre a nivel DB) cae a 'gallery' -- mismo fallback
que ya usaba gallery_item_add() en la vista para valores invalidos.
"""
from django.db import migrations


def migrate_forward(apps, schema_editor):
    GalleryItem = apps.get_model('website', 'GalleryItem')
    Section = apps.get_model('website', 'Section')

    for item in GalleryItem.objects.select_related('client').all():
        section_type = item.gallery_type if item.gallery_type in ('hero', 'gallery') else 'gallery'
        section, _ = Section.objects.get_or_create(
            client=item.client,
            section_type=section_type,
            defaults={'title': '', 'subtitle': '', 'description': '', 'order': 0},
        )
        item.section_id = section.id
        item.save(update_fields=['section'])


def migrate_backward(apps, schema_editor):
    GalleryItem = apps.get_model('website', 'GalleryItem')
    for item in GalleryItem.objects.select_related('section').all():
        if item.section_id:
            item.gallery_type = item.section.section_type
            item.section_id = None
            item.save(update_fields=['gallery_type', 'section'])


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0020_galleryitem_add_owner_fks'),
    ]

    operations = [
        migrations.RunPython(migrate_forward, migrate_backward),
    ]
