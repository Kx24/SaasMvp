"""
Soporte compartido de los tests de comportamiento del dashboard (DASH-05).

Arma un tenant real con dominio, un usuario `owner` y un cliente de pruebas ya
autenticado. Cloudinary se parchea siempre en cada test (nada hace red).
"""
import io

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from apps.accounts.models import UserProfile
from apps.tenants.models import Client, Domain

PASSWORD = 'pass12345-dash05'
UPLOAD = 'cloudinary.uploader.upload'
DESTROY = 'cloudinary.uploader.destroy'


def png_file(name='foto.png'):
    buf = io.BytesIO()
    Image.new('RGB', (8, 8), (30, 90, 200)).save(buf, format='PNG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/png')


def svg_file():
    return SimpleUploadedFile(
        'logo.svg', b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
        content_type='image/svg+xml')


def make_tenant(slug, *, gallery=False, **client_kwargs):
    """Crea Client + Domain primario `<slug>.test` y activa la galería si se pide."""
    tenant = Client.objects.create(
        name=f'Tenant {slug}', slug=slug, contact_email=f'c@{slug}.test', **client_kwargs)
    host = f'{slug}.test'
    Domain.objects.create(client=tenant, domain=host, domain_type='custom',
                          is_primary=True, is_active=True, is_verified=True)
    if gallery:
        tenant.settings.enable_gallery = True
        tenant.settings.save(update_fields=['enable_gallery'])
    return tenant


def make_owner(tenant, username=None):
    user = User.objects.create_user(username=username or f'owner_{tenant.slug}', password=PASSWORD)
    UserProfile.objects.filter(user=user).update(client=tenant, role='owner')
    return user


class DashboardTestCase(TestCase):
    """Base: tenant `slug` con owner logueado. Subclases fijan `slug` y `gallery`."""

    slug = 'dash'
    gallery = False

    @classmethod
    def setUpTestData(cls):
        cls.tenant = make_tenant(cls.slug, gallery=cls.gallery)
        cls.host = f'{cls.slug}.test'
        cls.owner = make_owner(cls.tenant)
        cls.other = make_tenant(f'{cls.slug}-otro', gallery=cls.gallery)

    def setUp(self):
        self.client.force_login(self.owner)

    def get(self, url, **kwargs):
        return self.client.get(url, HTTP_HOST=self.host, **kwargs)

    def post(self, url, data=None, **kwargs):
        return self.client.post(url, data or {}, HTTP_HOST=self.host, **kwargs)

    @staticmethod
    def message_texts(response):
        return [str(m) for m in response.context['messages']]
