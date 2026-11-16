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


APPS_DIR = Path(__file__).resolve().parents[2]

# Excepciones declaradas fuera de `website` (que usa `tenant_object_or_404` o el
# marcador `# tenant-ok:`). Clave: (archivo relativo a apps/, fragmento exacto de la línea).
# Cada una con su justificación; un uso nuevo sin declarar rompe el test.
TENANT_EXCEPTIONS = {
    ('orders/views.py', 'get_object_or_404(Plan, slug=plan_slug, is_active=True)'):
        'Plan es un modelo global (catálogo de la plataforma), sin tenant.',
    ('orders/views.py', 'Plan.objects.get(slug=plan_slug, is_active=True)'):
        'Plan es un modelo global (catálogo de la plataforma), sin tenant.',
    ('orders/views.py', 'get_object_or_404(Order, uuid=order_uuid)'):
        'Página pública de resultado de compra: el uuid (no adivinable) es el secreto; compra previa a que exista tenant.',
    ('orders/views.py', 'Order.objects.get(order_number=external_reference)'):
        'Webhook de MercadoPago: llega al dominio de la plataforma, sin request.client; la firma se valida antes.',
    ('orders/views.py', 'Order.objects.get(mp_payment_id=data_id)'):
        'Webhook de MercadoPago: llega al dominio de la plataforma, sin request.client; la firma se valida antes.',
    ('orders/signals.py', 'Order.objects.get(pk=instance.pk)'):
        'Signal sobre la propia instancia que se guarda (pk propio): no hay entrada externa.',
    ('website/templatetags/website_tags.py', 'return Section.objects.get('):
        'La consulta filtra por client=request.client en las líneas siguientes (verificado en CONS-12).',
    ('accounts/views.py', 'User.objects.get(email=email)'):
        'User es global (auth); la vista valida a continuación que profile.client coincida con request.client.',
}


class ViewsStaticGuardTests(TestCase):
    PATTERN = re.compile(r'get_object_or_404\(|\.objects\.get\(')
    SCANNED = ('website', 'orders', 'accounts')

    def _source_files(self, app):
        root = APPS_DIR / app
        files = []
        for path in sorted(root.rglob('*.py')):
            rel = path.relative_to(root).parts
            if 'tests' in rel or 'migrations' in rel:
                continue
            if path.name == 'tests.py' or path.name.startswith(('test_', 'tests_')):
                continue
            files.append(path)
        return files

    def test_views_use_the_helper_or_declared_exception(self):
        offenders, used = [], set()
        for app in self.SCANNED:
            files = self._source_files(app)
            self.assertTrue(files)
            for path in files:
                rel = path.relative_to(APPS_DIR).as_posix()
                for n, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
                    if not self.PATTERN.search(line) or '# tenant-ok:' in line:
                        continue
                    key = next((k for k in TENANT_EXCEPTIONS
                                if k[0] == rel and k[1] in line), None)
                    if key:
                        used.add(key)
                    else:
                        offenders.append(f'{rel}:{n}: {line.strip()}')
        self.assertEqual(
            offenders, [],
            'Usa tenant_object_or_404, filtra por client o declara la excepción en TENANT_EXCEPTIONS')
        self.assertEqual(set(TENANT_EXCEPTIONS) - used, set(), 'Excepciones obsoletas en TENANT_EXCEPTIONS')

    def test_every_exception_has_a_justification(self):
        for key, why in TENANT_EXCEPTIONS.items():
            self.assertGreater(len(why.strip()), 20, key)


class PasswordResetTenantIsolationTests(TestCase):
    def test_reset_from_tenant_a_does_not_touch_user_of_tenant_b(self):
        from django.contrib.auth.models import User
        from django.core import mail
        from django.urls import reverse

        from apps.accounts.models import UserProfile
        from apps.tenants.models import Domain

        a = _make_client('Reset A', 'ra@test.com')
        b = _make_client('Reset B', 'rb@test.com')
        Domain.objects.create(client=a, domain='reset-a.test', domain_type='custom',
                              is_primary=True, is_active=True, is_verified=True)
        victim = User.objects.create_user(username='vb', email='vb@test.com', password='x')
        UserProfile.objects.update_or_create(user=victim, defaults={'client': b, 'role': 'owner'})
        self.client.post(reverse('accounts:forgot_password'), {'email': 'vb@test.com'},
                         HTTP_HOST='reset-a.test')
        self.assertEqual(len(mail.outbox), 0)
        victim.profile.refresh_from_db()
        self.assertIsNone(victim.profile.invitation_token)
