"""DASH-06: el dashboard usa el token --color-primary, no el inexistente --primary."""
from pathlib import Path

from django.conf import settings as dj_settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.tenants.models import Client, ClientSettings, Domain

HOST = 'brandtoken.test'


class DashboardBrandTokenTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Client.objects.create(
            name='Brand Token', company_name='Brand Token SpA',
            contact_email='bt@test.com', contact_phone='+56900000001', is_active=True,
        )
        Domain.objects.create(
            client=cls.tenant, domain=HOST, domain_type='custom',
            is_primary=True, is_active=True, is_verified=True,
        )
        ClientSettings.objects.filter(client=cls.tenant).update(primary_color='#0b5fa5')
        cls.owner = User.objects.create_user(username='bt_owner', password='pass12345')
        UserProfile.objects.filter(user=cls.owner).update(client=cls.tenant, role='owner')

    def test_ningun_template_del_dashboard_usa_var_primary(self):
        root = Path(dj_settings.BASE_DIR) / 'templates' / 'dashboard'
        files = [p for p in root.rglob('*') if p.is_file()]
        self.assertTrue(files)
        for path in files:
            text = path.read_text(encoding='utf-8')
            self.assertNotIn('var(--primary)', text, str(path))

    def test_home_usa_color_primary_en_el_avatar(self):
        self.client.force_login(self.owner)
        html = self.client.get(reverse('dashboard'), HTTP_HOST=HOST).content.decode()
        self.assertIn('#0b5fa5', html)
        self.assertIn('background: var(--color-primary)', html)
        self.assertNotIn('var(--primary)', html)
