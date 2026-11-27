"""Registro de módulos (CONS-08)."""
import dataclasses
from types import SimpleNamespace

from django.test import SimpleTestCase, TestCase
from django.urls import get_resolver, reverse

from apps.accounts.permissions import DASHBOARD_PERMISSIONS
from apps.tenants import modules
from apps.tenants.models import Client, ClientSettings

# Rutas de apps/website/urls.py que no son del dashboard (públicas).
_PUBLIC_URLS = {'home', 'privacy_policy', 'data_subject_request', 'contact_submit'}


def _website_url_names():
    from apps.website import urls as website_urls
    return [p.name for p in website_urls.urlpatterns if getattr(p, 'name', None)]


def _dashboard_url_names():
    return [n for n in _website_url_names() if n not in _PUBLIC_URLS]


class ModuleRegistryDeclarationTests(SimpleTestCase):
    def test_cada_ruta_del_dashboard_pertenece_a_exactamente_un_modulo(self):
        for name in _dashboard_url_names():
            owners = [m.key for m in modules.MODULES if name in m.url_names]
            self.assertEqual(len(owners), 1, f'{name} -> {owners}')

    def test_ningun_url_name_apunta_a_ruta_inexistente_o_publica(self):
        known = set(_dashboard_url_names())
        for m in modules.MODULES:
            for name in m.url_names:
                self.assertIn(name, known, f'{m.key}: {name}')

    def test_url_names_y_menu_resuelven_con_reverse(self):
        from apps.website import urls as website_urls
        args_by_name = {}
        for p in website_urls.urlpatterns:
            if getattr(p, 'name', None):
                n = len(p.pattern.converters)
                args_by_name[p.name] = [1] * n
        for m in modules.MODULES:
            for name in m.url_names:
                reverse(name, args=args_by_name[name])
            for entry in m.menu:
                reverse(entry.url_name, args=args_by_name[entry.url_name])
                self.assertIn(entry.url_name, m.url_names)
        self.assertTrue(get_resolver())

    def test_permisos_existen(self):
        for m in modules.MODULES:
            for entry in m.menu:
                self.assertIn(entry.permission, DASHBOARD_PERMISSIONS)

    def test_flags_son_booleanos_de_clientsettings(self):
        for m in modules.MODULES:
            if m.flag is None:
                continue
            field = ClientSettings._meta.get_field(m.flag)
            self.assertEqual(field.get_internal_type(), 'BooleanField', m.flag)

    def test_limit_fields_son_campos_de_client(self):
        for m in modules.MODULES:
            if m.limit_field is not None:
                Client._meta.get_field(m.limit_field)

    def test_claves_unicas_e_inmutables(self):
        keys = [m.key for m in modules.MODULES]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(set(keys), {'core', 'services', 'gallery', 'media', 'contact'})
        self.assertIsInstance(modules.MODULES, tuple)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            modules.MODULES[0].key = 'x'

    def test_contacto_mantiene_menu_visible_apagado(self):
        self.assertTrue(modules.get_module('contact').menu_visible_when_disabled)
        self.assertFalse(modules.get_module('gallery').menu_visible_when_disabled)

    def test_get_module_y_module_for_url(self):
        self.assertEqual(modules.get_module('gallery').flag, 'enable_gallery')
        with self.assertRaises(KeyError):
            modules.get_module('nope')
        self.assertEqual(modules.module_for_url('dashboard_gallery').key, 'gallery')
        self.assertEqual(modules.module_for_url('create_service').key, 'services')
        self.assertIsNone(modules.module_for_url('home'))


class IsEnabledTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_obj = Client.objects.create(name='Mod', slug='mod-test')
        ClientSettings.objects.update_or_create(client=cls.client_obj)

    def _set(self, **kw):
        ClientSettings.objects.filter(client=self.client_obj).update(**kw)
        return Client.objects.get(pk=self.client_obj.pk)

    def test_galeria_apagada(self):
        c = self._set(enable_gallery=False)
        self.assertFalse(modules.is_enabled(c, 'gallery'))
        self.assertNotIn('gallery', [m.key for m in modules.enabled_modules(c)])

    def test_galeria_encendida(self):
        c = self._set(enable_gallery=True)
        self.assertTrue(modules.is_enabled(c, 'gallery'))

    def test_contacto_apagado(self):
        c = self._set(enable_contact_form=False)
        self.assertFalse(modules.is_enabled(c, 'contact'))

    def test_core_y_services_siempre(self):
        c = self._set(enable_gallery=False, enable_contact_form=False)
        self.assertTrue(modules.is_enabled(c, 'core'))
        self.assertTrue(modules.is_enabled(c, 'services'))

    def test_sin_cliente_o_sin_settings_solo_modulos_sin_flag(self):
        for c in (None, SimpleNamespace()):
            self.assertEqual(
                [m.key for m in modules.enabled_modules(c)], ['core', 'services', 'media']
            )
