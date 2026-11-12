"""
SEC-05 / BOLT-15: el Django Admin (/superadmin/) y las vistas internas no
deben mostrar datos de otros tenants a un usuario staff que no es superuser.

Antes, solo SectionAdmin/ServiceAdmin/ContactSubmissionAdmin usaban
TenantAdminMixin. Un staff del tenant A con permisos de lectura veía las
órdenes (RUT, razón social, dirección), los pagos, las credenciales SMTP,
los dominios y la configuración de todos los clientes. /superadmin/nuevo/ y
/tenants/ solo pedían is_staff.
"""
from decimal import Decimal

from django.contrib import admin
from django.contrib.auth.models import Permission, User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.marketing.models import SEOConfig
from apps.orders.models import Order, PaymentLog, Plan
from apps.tenants.models import Client, ClientEmailSettings, ClientSettings, Domain, FormConfig


def _tenant(slug):
    client = Client.objects.create(name=f'Tenant {slug}', slug=slug, contact_email=f'c@{slug}.test')
    Domain.objects.create(client=client, domain=f'{slug}.test', domain_type='custom',
                          is_primary=True, is_active=True, is_verified=True)
    SEOConfig.objects.create(client=client, page_key='home', title=f'SEO {slug}')
    return client


class AdminTenantScopeTests(TestCase):
    MODELS = (Order, PaymentLog, Domain, ClientSettings, ClientEmailSettings, FormConfig,
              SEOConfig, UserProfile)

    @classmethod
    def setUpTestData(cls):
        cls.a = _tenant('scope-a')
        cls.b = _tenant('scope-b')
        plan = Plan.objects.create(name='Plan', slug='plan-scope', price=Decimal('100000'))
        cls.order_a = Order.objects.create(plan=plan, client=cls.a, email='comprador@a.test',
                                           amount=Decimal('100000'))
        cls.order_b = Order.objects.create(plan=plan, client=cls.b, email='comprador@b.test',
                                           amount=Decimal('100000'), billing_rut='11.111.111-1')
        cls.order_unassigned = Order.objects.create(plan=plan, email='sin-sitio@x.test',
                                                    amount=Decimal('100000'))
        PaymentLog.objects.create(order=cls.order_a, action='webhook', status='approved')
        PaymentLog.objects.create(order=cls.order_b, action='webhook', status='approved')

        cls.staff_a = User.objects.create_user(username='staff_a', password='x', is_staff=True)
        UserProfile.objects.filter(user=cls.staff_a).update(client=cls.a, role='admin')
        cls.staff_a.user_permissions.set(Permission.objects.filter(
            codename__regex=r'^(view|change|delete)_',
            content_type__app_label__in=['orders', 'tenants', 'marketing', 'accounts']))
        cls.root = User.objects.create_superuser(username='root_scope', password='x', email='r@x.test')
        cls.b_profile_user = User.objects.create_user(username='user_b', password='x')
        UserProfile.objects.filter(user=cls.b_profile_user).update(client=cls.b)

    def _request(self, user):
        request = RequestFactory().get('/superadmin/')
        request.user = User.objects.get(pk=user.pk)  # perfil fresco
        return request

    def _tenant_of(self, obj):
        return obj.order.client if isinstance(obj, PaymentLog) else obj.client

    def test_staff_sees_only_own_tenant_in_every_admin(self):
        request = self._request(self.staff_a)
        for model in self.MODELS:
            with self.subTest(model=model.__name__):
                qs = admin.site._registry[model].get_queryset(request)
                tenants = {self._tenant_of(o) for o in qs}
                self.assertTrue(qs.exists())
                self.assertEqual(tenants, {self.a})

    def test_staff_cannot_change_other_tenant_object(self):
        request = self._request(self.staff_a)
        others = {
            Order: self.order_b, PaymentLog: PaymentLog.objects.get(order=self.order_b),
            Domain: self.b.domains.first(), ClientSettings: self.b.settings,
            ClientEmailSettings: self.b.email_settings, FormConfig: self.b.form_config,
            SEOConfig: self.b.seo_configs.first(), UserProfile: self.b_profile_user.profile,
        }
        for model, obj in others.items():
            with self.subTest(model=model.__name__):
                model_admin = admin.site._registry[model]
                self.assertFalse(model_admin.has_change_permission(request, obj))
                self.assertFalse(model_admin.has_delete_permission(request, obj))

    def test_orders_without_site_are_hidden_from_tenant_staff(self):
        qs = admin.site._registry[Order].get_queryset(self._request(self.staff_a))
        self.assertNotIn(self.order_unassigned, qs)

    def test_superuser_sees_everything(self):
        request = self._request(self.root)
        self.assertEqual(admin.site._registry[Order].get_queryset(request).count(), 3)
        self.assertEqual(admin.site._registry[PaymentLog].get_queryset(request).count(), 2)

    def test_client_admin_is_superuser_only(self):
        # ClientAdmin muestra en línea las credenciales SMTP de cada cliente.
        client_admin = admin.site._registry[Client]
        self.assertFalse(client_admin.has_module_permission(self._request(self.staff_a)))
        self.assertFalse(client_admin.has_view_permission(self._request(self.staff_a), self.b))
        self.assertTrue(client_admin.has_module_permission(self._request(self.root)))

    def test_order_changelist_over_http_hides_other_tenant(self):
        self.client.force_login(self.staff_a)
        response = self.client.get(reverse('admin:orders_order_changelist'), HTTP_HOST='localhost')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.order_a.order_number)
        self.assertNotContains(response, self.order_b.order_number)

    def test_other_tenant_order_change_page_is_not_reachable(self):
        self.client.force_login(self.staff_a)
        url = reverse('admin:orders_order_change', args=[self.order_b.pk])
        response = self.client.get(url, HTTP_HOST='localhost')
        self.assertIn(response.status_code, (302, 403, 404))
        self.assertNotContains(response, '11.111.111-1', status_code=response.status_code)


class InternalTenantViewsTests(TestCase):
    """/superadmin/nuevo/ (alta de tenant) y /tenants/ (lista de todos los clientes)."""

    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user(username='staff_only', password='x', is_staff=True)
        cls.root = User.objects.create_superuser(username='root_views', password='x', email='rv@x.test')

    def test_staff_is_rejected(self):
        self.client.force_login(self.staff)
        for name in ('superadmin_onboarding', 'tenant_list'):
            with self.subTest(view=name):
                response = self.client.get(reverse(name), HTTP_HOST='localhost')
                self.assertEqual(response.status_code, 302)
                self.assertIn('login', response['Location'])

    def test_superuser_is_allowed(self):
        self.client.force_login(self.root)
        for name in ('superadmin_onboarding', 'tenant_list'):
            with self.subTest(view=name):
                self.assertEqual(self.client.get(reverse(name), HTTP_HOST='localhost').status_code, 200)
