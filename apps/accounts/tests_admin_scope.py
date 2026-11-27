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


class AdminClientFilterScopeTests(TestCase):
    """BOLT-24 (SEC-05b): el filtro lateral `client` no lista otros tenants."""

    CHANGELISTS = ('admin:accounts_userprofile_changelist', 'admin:marketing_seoconfig_changelist')

    @classmethod
    def setUpTestData(cls):
        cls.a = _tenant('filtro-a')
        cls.b = _tenant('filtro-b')
        cls.staff_a = User.objects.create_user(username='staff_filtro', password='x', is_staff=True)
        UserProfile.objects.filter(user=cls.staff_a).update(client=cls.a, role='admin')
        cls.staff_a.user_permissions.set(Permission.objects.filter(
            codename__regex=r'^(view|change)_',
            content_type__app_label__in=['marketing', 'accounts']))
        cls.root = User.objects.create_superuser(username='root_filtro', password='x', email='rf@x.test')

    def test_staff_changelist_does_not_list_other_client_name(self):
        self.client.force_login(self.staff_a)
        for name in self.CHANGELISTS:
            with self.subTest(changelist=name):
                response = self.client.get(reverse(name), HTTP_HOST='localhost')
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, self.b.name)

    def test_staff_has_no_client_filter(self):
        request = RequestFactory().get('/superadmin/')
        request.user = User.objects.get(pk=self.staff_a.pk)
        for model in (UserProfile, SEOConfig):
            with self.subTest(model=model.__name__):
                self.assertNotIn('client', admin.site._registry[model].get_list_filter(request))

    def test_superuser_still_sees_client_filter(self):
        self.client.force_login(self.root)
        for name in self.CHANGELISTS:
            with self.subTest(changelist=name):
                response = self.client.get(reverse(name), HTTP_HOST='localhost')
                self.assertContains(response, self.a.name)
                self.assertContains(response, self.b.name)


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


class AdminForeignKeyScopeTests(TestCase):
    """BOLT-32 (SEC-05b): los desplegables FK no ofrecen filas de otros tenants."""

    @classmethod
    def setUpTestData(cls):
        cls.a = _tenant('fk-a')
        cls.b = _tenant('fk-b')
        plan = Plan.objects.create(name='Plan FK', slug='plan-fk', price=Decimal('100000'))
        cls.order_a = Order.objects.create(plan=plan, client=cls.a, email='fk@a.test',
                                           amount=Decimal('100000'))
        cls.order_b = Order.objects.create(plan=plan, client=cls.b, email='fk@b.test',
                                           amount=Decimal('100000'))
        cls.staff_a = User.objects.create_user(username='staff_fk', password='x', is_staff=True)
        UserProfile.objects.filter(user=cls.staff_a).update(client=cls.a, role='admin')
        cls.root = User.objects.create_superuser(username='root_fk', password='x', email='fk@x.test')

    def _order_field_queryset(self, user):
        request = RequestFactory().get('/superadmin/')
        request.user = User.objects.get(pk=user.pk)
        model_admin = admin.site._registry[PaymentLog]
        db_field = PaymentLog._meta.get_field('order')
        return model_admin.formfield_for_foreignkey(db_field, request).queryset

    def test_staff_order_dropdown_excludes_other_tenant(self):
        qs = self._order_field_queryset(self.staff_a)
        self.assertIn(self.order_a, qs)
        self.assertNotIn(self.order_b, qs)

    def test_superuser_order_dropdown_lists_all(self):
        qs = self._order_field_queryset(self.root)
        self.assertIn(self.order_a, qs)
        self.assertIn(self.order_b, qs)


class EveryTenantAdminScopeTests(TestCase):
    """SEC-18 / BOLT-41: recorre `admin.site._registry`; un admin nuevo sin cubrir falla."""

    @classmethod
    def setUpTestData(cls):
        from apps.website.models import (
            ContactSubmission,
            DataSubjectRequest,
            MediaAsset,
            Section,
            Service,
        )

        cls.a = _tenant('all-a')
        cls.b = _tenant('all-b')
        plan = Plan.objects.create(name='Plan All', slug='plan-all', price=Decimal('100000'))
        for tenant, tag in ((cls.a, 'a'), (cls.b, 'b')):
            order = Order.objects.create(plan=plan, client=tenant, email=f'all@{tag}.test',
                                         amount=Decimal('100000'))
            PaymentLog.objects.create(order=order, action='webhook', status='approved')
            Section.objects.create(client=tenant, section_type='hero', title=f'Sec {tag}')
            Service.objects.create(client=tenant, name=f'Srv {tag}', slug=f'srv-{tag}',
                                   description='x')
            ContactSubmission.objects.create(client=tenant, name=f'N {tag}',
                                             email=f'n@{tag}.test', message='hola')
            DataSubjectRequest.objects.create(client=tenant, request_type='access', name=f'D {tag}',
                                              email=f'd@{tag}.test', detail='x')
            MediaAsset.objects.create(client=tenant, kind='embed', provider='youtube',
                                      video_id='dQw4w9WgXcQ', title=f'M {tag}')
            user = User.objects.create_user(username=f'user_all_{tag}', password='x')
            UserProfile.objects.filter(user=user).update(client=tenant)
        cls.staff_a = User.objects.get(username='user_all_a')
        cls.staff_a.is_staff = True
        cls.staff_a.save()
        cls.staff_a.user_permissions.set(Permission.objects.filter(
            codename__regex=r'^(view|change|delete)_',
            content_type__app_label__in=['orders', 'tenants', 'marketing', 'accounts', 'website']))
        cls.staff_none = User.objects.create_user(username='staff_none_all', password='x',
                                                  is_staff=True)
        cls.staff_none.user_permissions.set(cls.staff_a.user_permissions.all())

    def _mixin_admins(self):
        from apps.accounts.mixins import TenantAdminMixin
        return [ma for ma in admin.site._registry.values() if isinstance(ma, TenantAdminMixin)]

    def _is_b(self, obj):
        if isinstance(obj, PaymentLog):
            return obj.order.client == self.b
        if isinstance(obj, User):
            return getattr(getattr(obj, 'profile', None), 'client', None) == self.b
        if hasattr(obj, 'client'):
            return obj.client == self.b
        return False

    def _objects_of_b(self, model):
        return [o for o in model._default_manager.all() if self._is_b(o)]

    def _request(self, user):
        request = RequestFactory().get('/superadmin/')
        request.user = User.objects.get(pk=user.pk)
        return request

    def test_registry_is_covered_by_fixtures(self):
        covered = {Order, PaymentLog, Domain, ClientSettings, ClientEmailSettings, FormConfig,
                   SEOConfig, UserProfile}
        from apps.website.models import (
            ContactSubmission,
            DataSubjectRequest,
            MediaAsset,
            Section,
            Service,
        )
        covered |= {Section, Service, ContactSubmission, DataSubjectRequest, MediaAsset}
        for ma in self._mixin_admins():
            self.assertIn(ma.model, covered, f'{ma.__class__.__name__} sin cobertura de aislamiento')

    def test_changelist_and_change_hide_other_tenant(self):
        self.client.force_login(self.staff_a)
        for ma in self._mixin_admins():
            meta = ma.model._meta
            with self.subTest(admin=ma.__class__.__name__):
                response = self.client.get(
                    reverse(f'admin:{meta.app_label}_{meta.model_name}_changelist'),
                    HTTP_HOST='localhost')
                self.assertEqual(response.status_code, 200)
                listed = list(response.context_data['cl'].queryset)
                self.assertFalse([o for o in listed if self._is_b(o)])
                for obj in self._objects_of_b(ma.model):
                    url = reverse(f'admin:{meta.app_label}_{meta.model_name}_change', args=[obj.pk])
                    got = self.client.get(url, HTTP_HOST='localhost')
                    self.assertIn(got.status_code, (302, 403, 404))

    def test_fk_dropdowns_exclude_other_tenant(self):
        request = self._request(self.staff_a)
        for ma in self._mixin_admins():
            for db_field in ma.model._meta.get_fields():
                if not (db_field.many_to_one and db_field.concrete):
                    continue
                with self.subTest(admin=ma.__class__.__name__, field=db_field.name):
                    qs = ma.formfield_for_foreignkey(db_field, request).queryset
                    self.assertFalse([o for o in qs if self._is_b(o)
                                      and not isinstance(o, Client)])
                    if db_field.related_model is Client:
                        self.assertEqual(list(qs), [self.a])

    def test_staff_without_tenant_gets_nothing(self):
        request = self._request(self.staff_none)
        for ma in self._mixin_admins():
            with self.subTest(admin=ma.__class__.__name__):
                self.assertEqual(ma.get_queryset(request).count(), 0)

    def test_no_tenant_path_filter_for_staff(self):
        request = self._request(self.staff_a)
        for ma in self._mixin_admins():
            with self.subTest(admin=ma.__class__.__name__):
                filters = ma.get_list_filter(request)
                self.assertNotIn('client', filters)
                self.assertNotIn(ma.tenant_field, filters)

    def test_only_one_tenant_admin_mixin_class(self):
        import pathlib

        import apps
        root = pathlib.Path(apps.__file__).resolve().parent
        found = [p for p in root.rglob('*.py')
                 if 'class TenantAdminMixin' in p.read_text(encoding='utf-8')
                 and p.name != 'tests_admin_scope.py']
        self.assertEqual([p.name for p in found], ['mixins.py'])
