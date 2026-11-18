"""CONS-13 (parte 2): SEOConfigAdmin (changelist, previews, aislamiento por tenant)."""
from django.contrib import admin
from django.contrib.auth.models import Permission, User
from django.test import TestCase

from apps.accounts.models import UserProfile
from apps.marketing.admin import SEOConfigAdmin
from apps.marketing.models import SEOConfig
from apps.tenants.models import Client, Domain


def _tenant(slug):
    client = Client.objects.create(name='T ' + slug, slug=slug, company_name=slug)
    Domain.objects.create(client=client, domain=slug + '.test', is_primary=True,
                          is_active=True, is_verified=True)
    return client


class SEOConfigAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = _tenant('seoadm-a')
        cls.b = _tenant('seoadm-b')
        cls.seo_a = SEOConfig.objects.create(client=cls.a, page_key='home', title='A' * 60,
                                             meta_description='d' * 130)
        cls.seo_b = SEOConfig.objects.create(client=cls.b, page_key='home', title='SEO-B-UNICO')
        cls.root = User.objects.create_superuser(username='seo_root', password='x', email='r@x.test')
        cls.staff_a = User.objects.create_user(username='seo_staff_a', password='x', is_staff=True)
        UserProfile.objects.filter(user=cls.staff_a).update(client=cls.a, role='admin')
        cls.staff_a.user_permissions.set(Permission.objects.filter(
            codename__in=['view_seoconfig', 'change_seoconfig']))

    @property
    def model_admin(self):
        return SEOConfigAdmin(SEOConfig, admin.site)

    def test_superuser_changelist_ok_with_all_rows(self):
        self.client.force_login(self.root)
        resp = self.client.get('/superadmin/marketing/seoconfig/', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'SEO-B-UNICO')

    def test_staff_does_not_see_other_tenant_rows(self):
        self.client.force_login(User.objects.get(pk=self.staff_a.pk))
        resp = self.client.get('/superadmin/marketing/seoconfig/', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'SEO-B-UNICO')

    def test_change_form_renders_previews(self):
        self.client.force_login(self.root)
        resp = self.client.get('/superadmin/marketing/seoconfig/%d/change/' % self.seo_a.pk, HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'seoadm-a.test')
        self.assertContains(resp, 'Ideal')

    def test_title_preview_lengths(self):
        ma = self.model_admin
        self.assertIn('sin título', str(ma.title_preview(SEOConfig(title=''))))
        self.assertIn('#e67e22', str(ma.title_preview(SEOConfig(title='corto'))))
        self.assertIn('#2ecc71', str(ma.title_preview(SEOConfig(title='x' * 60))))
        long_preview = str(ma.title_preview(SEOConfig(title='x' * 80)))
        self.assertIn('#e74c3c', long_preview)
        self.assertIn('...', long_preview)

    def test_char_counters_messages(self):
        ma = self.model_admin
        self.assertIn('Muy corto', str(ma.char_count_title(SEOConfig(title=''))))
        self.assertIn('Ideal', str(ma.char_count_title(SEOConfig(title='x' * 60))))
        self.assertIn('Muy largo', str(ma.char_count_title(SEOConfig(title='x' * 90))))
        self.assertIn('Muy corta', str(ma.char_count_description(SEOConfig(meta_description=''))))
        self.assertIn('Ideal', str(ma.char_count_description(SEOConfig(meta_description='x' * 130))))
        self.assertIn('Muy larga', str(ma.char_count_description(SEOConfig(meta_description='x' * 200))))

    def test_previews_without_domain_use_placeholder(self):
        Domain.objects.filter(client=self.a).delete()
        seo = SEOConfig.objects.get(pk=self.seo_a.pk)
        self.assertIn('https://tudominio.cl', str(self.model_admin.google_preview(seo)))
        self.assertIn('tudominio.cl', str(self.model_admin.og_preview(seo)))
