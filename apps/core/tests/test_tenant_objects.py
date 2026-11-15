import re
from pathlib import Path

from django.http import Http404
from django.test import RequestFactory, TestCase

from apps.core.tenant_objects import tenant_object_or_404
from apps.tenants.models import Client
from apps.website.models import GalleryItem, Section, Service


def _make_client(name, email):
    return Client.objects.create(
        name=name, company_name=f'{name} SpA',
        contact_email=email, contact_phone='+56900000000', is_active=True,
    )


class TenantObjectOr404Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_a = _make_client('Tenant A', 'a@test.com')
        cls.client_b = _make_client('Tenant B', 'b@test.com')
        cls.service_a = Service.objects.create(client=cls.client_a, name='Servicio A')
        cls.service_b = Service.objects.create(client=cls.client_b, name='Servicio B')

    def _request(self, client):
        request = RequestFactory().get('/')
        request.client = client
        return request

    def test_returns_object_of_request_tenant(self):
        obj = tenant_object_or_404(
            self._request(self.client_a), Service, id=self.service_a.id)
        self.assertEqual(obj, self.service_a)

    def test_404_for_object_of_other_tenant(self):
        with self.assertRaises(Http404):
            tenant_object_or_404(
                self._request(self.client_a), Service, id=self.service_b.id)

    def test_404_when_request_client_is_none(self):
        with self.assertRaises(Http404):
            tenant_object_or_404(
                self._request(None), Service, id=self.service_a.id)

    def test_client_field_for_indirect_model(self):
        section_a = Section.objects.create(
            client=self.client_a, section_type='about', title='A', order=1)
        item = GalleryItem.objects.create(client=self.client_a, section=section_a)
        found = tenant_object_or_404(
            self._request(self.client_a), GalleryItem,
            client_field='section__client', id=item.id)
        self.assertEqual(found, item)
        with self.assertRaises(Http404):
            tenant_object_or_404(
                self._request(self.client_b), GalleryItem,
                client_field='section__client', id=item.id)


class ViewsStaticGuardTests(TestCase):
    PATTERN = re.compile(r'get_object_or_404\(|\.objects\.get\(')

    def test_website_views_use_the_helper(self):
        root = Path(__file__).resolve().parents[2] / 'website'
        package = root / 'views'
        files = sorted(package.rglob('*.py')) if package.is_dir() else [root / 'views.py']
        self.assertTrue(files)
        offenders = []
        for path in files:
            for n, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
                if self.PATTERN.search(line) and '# tenant-ok:' not in line:
                    offenders.append(f'{path.name}:{n}: {line.strip()}')
        self.assertEqual(offenders, [], 'Usa tenant_object_or_404 en vez de get/get_object_or_404')
