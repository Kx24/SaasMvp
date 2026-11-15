"""
SEC-11 / BOLT-13: toda subida de imagen del dashboard se valida en el
servidor antes de llegar a Cloudinary.

Antes, `validate_image_file` existía en apps/core/cloudinary_utils.py pero
ninguna vista lo llamaba: cualquier archivo (un .txt renombrado, un SVG con
JavaScript, un archivo enorme) se enviaba a Cloudinary tal cual. Además el
validador solo miraba la extensión y aceptaba SVG por defecto.

Cloudinary se mockea siempre: ningún test hace red.
"""
import io
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from apps.accounts.models import UserProfile
from apps.core.cloudinary_utils import validate_image_file
from apps.tenants.models import Client, Domain
from apps.website.models import GalleryItem, Section, Service

HOST = 'subidas.test'
UPLOAD = 'cloudinary.uploader.upload'


def png_file(name='foto.png', size=(8, 8)):
    buf = io.BytesIO()
    Image.new('RGB', size, (200, 30, 30)).save(buf, format='PNG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/png')


def fake_jpg():
    # Texto con extensión de imagen: pasa un control solo-por-extensión.
    return SimpleUploadedFile('foto.jpg', b'esto no es una imagen', content_type='image/jpeg')


def svg_file():
    return SimpleUploadedFile(
        'logo.svg', b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
        content_type='image/svg+xml')


def huge_png():
    # Bytes reales sobre el máximo de 10 MB (un .size falso no sobrevive al
    # multipart del cliente de pruebas).
    content = png_file().read() + bytes(1) * (11 * 1024 * 1024)
    return SimpleUploadedFile('grande.png', content, content_type='image/png')


INVALID_FILES = {'texto renombrado': fake_jpg, 'svg': svg_file, 'sobre el límite': huge_png}


class ValidateImageFileTests(TestCase):
    def test_accepts_real_image(self):
        self.assertEqual(validate_image_file(png_file()), (True, None))

    def test_rejects_invalid_files(self):
        for label, make in INVALID_FILES.items():
            with self.subTest(label):
                ok, err = validate_image_file(make())
                self.assertFalse(ok)
                self.assertTrue(err)

    def test_leaves_file_ready_to_upload(self):
        f = png_file()
        validate_image_file(f)
        self.assertEqual(f.tell(), 0)


class DashboardUploadValidationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Client.objects.create(name='Subidas', slug='subidas', contact_email='c@subidas.test')
        Domain.objects.create(client=cls.tenant, domain=HOST, domain_type='custom',
                              is_primary=True, is_active=True, is_verified=True)
        cls.tenant.settings.enable_gallery = True
        cls.tenant.settings.save(update_fields=['enable_gallery'])
        cls.owner = User.objects.create_user(username='owner_subidas', password='pass12345')
        UserProfile.objects.filter(user=cls.owner).update(client=cls.tenant, role='owner')
        cls.section = Section.objects.create(client=cls.tenant, section_type='about', title='Sobre', order=1)
        cls.service = Service.objects.create(client=cls.tenant, name='Servicio', description='d')

    def setUp(self):
        self.client.force_login(self.owner)

    def _post(self, url, data):
        return self.client.post(url, data, HTTP_HOST=HOST)

    # Cada caso: (nombre, url, datos sin archivo, campo del archivo)
    def _cases(self):
        item = GalleryItem.objects.create(client=self.tenant, section=Section.objects.get_or_create(
            client=self.tenant, section_type='gallery', defaults={'title': ''})[0],
            image='subidas/gallery/existente')
        return [
            ('editar sección', reverse('edit_section_dashboard', args=[self.section.id]),
             {'title': 'Sobre', 'subtitle': '', 'description': '', 'is_active': 'on'}, 'image'),
            ('crear servicio', reverse('create_service'),
             {'name': 'Nuevo', 'description': 'd', 'is_active': 'on'}, 'image'),
            ('editar servicio', reverse('edit_service_dashboard', args=[self.service.id]),
             {'name': 'Servicio', 'description': 'd', 'is_active': 'on'}, 'image'),
            ('agregar a galería', reverse('gallery_item_add'), {'gallery_type': 'gallery'}, 'image'),
            ('reemplazar imagen de galería', reverse('gallery_item_edit', args=[item.id]),
             {'title': 't', 'order': '0'}, 'image'),
            ('fondo de portada', reverse('dashboard_portada'), {'action': 'save_hero_config'}, 'background_image'),
        ]

    def test_invalid_files_never_reach_cloudinary(self):
        for name, url, data, field in self._cases():
            for label, make in INVALID_FILES.items():
                with self.subTest(vista=name, archivo=label), \
                        mock.patch(UPLOAD, return_value={'public_id': 'subidas/x'}) as upload:
                    response = self._post(url, {**data, field: make()})
                    self.assertIn(response.status_code, (200, 302))
                    upload.assert_not_called()

    def test_invalid_file_shows_error_message(self):
        for name, url, data, field in self._cases():
            with self.subTest(vista=name), mock.patch(UPLOAD, return_value={'public_id': 'subidas/x'}):
                response = self.client.post(url, {**data, field: fake_jpg()}, HTTP_HOST=HOST, follow=True)
                texts = [str(m) for m in response.context['messages']]
                self.assertTrue(any('imagen' in t.lower() for t in texts), texts)

    def test_valid_image_is_uploaded(self):
        for name, url, data, field in self._cases():
            with self.subTest(vista=name), mock.patch(UPLOAD, return_value={'public_id': 'subidas/x'}) as upload:
                self._post(url, {**data, field: png_file()})
                upload.assert_called_once()

    def test_gallery_add_rejected_file_creates_no_item(self):
        before = GalleryItem.objects.filter(client=self.tenant).count()
        with mock.patch(UPLOAD, return_value={'public_id': 'subidas/x'}):
            self._post(reverse('gallery_item_add'), {'gallery_type': 'gallery', 'image': svg_file()})
        self.assertEqual(GalleryItem.objects.filter(client=self.tenant).count(), before)


class BrandingUploadValidationTests(TestCase):
    """El logo pasa por BrandingForm (CloudinaryField), no por una subida manual."""

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Client.objects.create(name='Marca', slug='marca', contact_email='c@marca.test')
        Domain.objects.create(client=cls.tenant, domain='marca.test', domain_type='custom',
                              is_primary=True, is_active=True, is_verified=True)
        cls.owner = User.objects.create_user(username='owner_marca', password='pass12345')
        UserProfile.objects.filter(user=cls.owner).update(client=cls.tenant, role='owner')

    def _form(self, files):
        from apps.tenants.forms import BrandingForm
        settings_obj = self.tenant.settings
        data = {f: getattr(settings_obj, f) or '' for f in BrandingForm.Meta.fields
                if f not in ('logo', 'logo_footer')}
        return BrandingForm(data, files, instance=settings_obj)

    def test_invalid_logo_is_rejected_by_the_form(self):
        for label, make in INVALID_FILES.items():
            for field in ('logo', 'logo_footer'):
                with self.subTest(campo=field, archivo=label):
                    form = self._form({field: make()})
                    self.assertFalse(form.is_valid())
                    self.assertIn(field, form.errors)

    def test_valid_logo_passes_validation(self):
        form = self._form({'logo': png_file('logo.png')})
        form.is_valid()
        self.assertNotIn('logo', form.errors)
