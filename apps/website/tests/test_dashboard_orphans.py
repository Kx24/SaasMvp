"""DEUDA-09: sin vistas `dashboard_*` huérfanas y estado vacío de galería renderizado."""
from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.tenants.models import Client, ClientSettings, Domain
from apps.website import urls, views


class DashboardOrphansTests(SimpleTestCase):
    def test_every_exported_dashboard_view_has_a_route(self):
        routed = {getattr(p.callback, '__name__', None) for p in urls.urlpatterns}
        orphans = [
            name for name in views.__all__
            if name.startswith('dashboard_')
            and getattr(views, name).__name__ not in routed
        ]
        self.assertEqual(orphans, [])


class GalleryEmptyStateTests(TestCase):
    def test_empty_gallery_renders_without_raw_template_tags(self):
        c = Client.objects.create(
            name='G', company_name='G SpA', contact_email='g@test.com',
            contact_phone='+56900000009', is_active=True,
        )
        Domain.objects.create(
            client=c, domain='gallery-empty.test', domain_type='custom',
            is_primary=True, is_active=True, is_verified=True,
        )
        ClientSettings.objects.filter(client=c).update(enable_gallery=True)
        user = User.objects.create_user(username='gown', password='pass12345')
        UserProfile.objects.filter(user=user).update(client=c, role='owner')
        self.client.force_login(user)
        resp = self.client.get(reverse('dashboard_gallery'), HTTP_HOST='gallery-empty.test')
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertNotIn('{%', html)
        self.assertNotIn('%}', html)
        self.assertIn('No hay imágenes en la galería', html)
