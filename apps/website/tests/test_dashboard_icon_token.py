"""DASH-09: el ícono de Contactos usa --color-primary, no el inexistente --primary-rgb."""
from pathlib import Path

from django.conf import settings as dj_settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.tenants.models import Client, ClientSettings, Domain

HOST = 'icontoken.test'


class DashboardIconTokenTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Client.objects.create(
            name='Icon Token', company_name='Icon Token SpA',
            contact_email='it@test.com', contact_phone='+56900000002', is_active=True,
        )
        Domain.objects.create(
            client=cls.tenant, domain=HOST, domain_type='custom',
            is_primary=True, is_active=True, is_verified=True,
        )
        ClientSettings.objects.filter(client=cls.tenant).update(primary_color='#0b5fa5')
        cls.owner = User.objects.create_user(username='it_owner', password='pass12345')
        UserProfile.objects.filter(user=cls.owner).update(client=cls.tenant, role='owner')

    def test_ningun_template_usa_primary_rgb(self):
        root = Path(dj_settings.BASE_DIR) / 'templates'
        files = [p for p in root.rglob('*') if p.is_file() and p.suffix in ('.html', '.css', '.js')]
        self.assertTrue(files)
        for path in files:
            text = path.read_text(encoding='utf-8', errors='ignore')
            self.assertNotIn('--primary-rgb', text, str(path))

    def test_home_usa_color_mix_en_contactos(self):
        self.client.force_login(self.owner)
        html = self.client.get(reverse('dashboard'), HTTP_HOST=HOST).content.decode()
        self.assertIn('#0b5fa5', html)
        self.assertIn('color-mix(in srgb, var(--color-primary)', html)
        self.assertNotIn('primary-rgb', html)
