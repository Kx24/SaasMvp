"""CONS-09: menú y acceso del dashboard derivan del registro de módulos."""
from pathlib import Path

from django.conf import settings as dj_settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.accounts.permissions import DASHBOARD_PERMISSIONS
from apps.tenants import modules
from apps.tenants.models import Client, ClientSettings, Domain
from apps.website.models import ContactSubmission, GalleryItem, Section, Service

ROLES = [code for code, _ in UserProfile.ROLE_CHOICES]
HOST_A = 'modacc-a.test'
HOST_B = 'modacc-b.test'


def _mk_client(name, domain):
    c = Client.objects.create(
        name=name, company_name=f'{name} SpA', contact_email=f'{domain}@test.com',
        contact_phone='+56900000001', is_active=True,
    )
    Domain.objects.create(
        client=c, domain=domain, domain_type='custom',
        is_primary=True, is_active=True, is_verified=True,
    )
    return c


class ModuleAccessBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_a = _mk_client('Mod Access A', HOST_A)
        cls.client_b = _mk_client('Mod Access B', HOST_B)
        cls.users = {}
        for role in ROLES:
            u = User.objects.create_user(username=f'ma_{role}', password='pass12345')
            UserProfile.objects.filter(user=u).update(client=cls.client_a, role=role)
            cls.users[role] = u
        cls.owner_b = User.objects.create_user(username='ma_owner_b', password='pass12345')
        UserProfile.objects.filter(user=cls.owner_b).update(client=cls.client_b, role='owner')
        cls.section = Section.objects.create(
            client=cls.client_a, section_type='gallery', title='G', order=1)
        cls.service = Service.objects.create(client=cls.client_a, name='S')
        cls.item = GalleryItem.objects.create(client=cls.client_a, section=cls.section, title='I')
        cls.contact = ContactSubmission.objects.create(
            client=cls.client_a, name='Ana', email='ana@test.com', message='Hola')

    def set_flags(self, **flags):
        for c in (self.client_a, self.client_b):
            ClientSettings.objects.filter(client=c).update(**flags)

    def login(self, role='owner'):
        self.client.force_login(self.users[role])

    def gallery_urls(self):
        kw = {'item_id': self.item.id}
        return {
            'dashboard_portada': reverse('dashboard_portada'),
            'dashboard_gallery': reverse('dashboard_gallery'),
            'gallery_item_add': reverse('gallery_item_add'),
            'gallery_item_edit': reverse('gallery_item_edit', kwargs=kw),
            'gallery_item_delete': reverse('gallery_item_delete', kwargs=kw),
            'gallery_item_toggle': reverse('gallery_item_toggle', kwargs=kw),
        }

    def menu_urls(self, host=HOST_A):
        html = self.client.get(reverse('dashboard'), HTTP_HOST=host).content.decode()
        start = html.index('<nav')
        return html[start:html.index('</nav>', start)]


class GalleryModuleAccessTests(ModuleAccessBase):
    def test_galeria_apagada_todas_las_urls_404_y_sin_enlaces(self):
        self.set_flags(enable_gallery=False)
        self.login('owner')
        gallery_keys = set(modules.get_module('gallery').url_names)
        urls = self.gallery_urls()
        self.assertEqual(set(urls), gallery_keys)
        for name, url in urls.items():
            for method in (self.client.get, self.client.post):
                self.assertEqual(method(url, HTTP_HOST=HOST_A).status_code, 404, name)
        html = self.menu_urls()
        self.assertNotIn(reverse('dashboard_gallery'), html)
        self.assertNotIn(reverse('dashboard_portada'), html)

    def test_galeria_encendida_200_y_enlaces(self):
        self.set_flags(enable_gallery=True)
        self.login('owner')
        for name in ('dashboard_portada', 'dashboard_gallery'):
            self.assertEqual(
                self.client.get(self.gallery_urls()[name], HTTP_HOST=HOST_A).status_code, 200, name)
        html = self.menu_urls()
        self.assertIn(reverse('dashboard_gallery'), html)
        self.assertIn(reverse('dashboard_portada'), html)

    def test_otro_tenant_recibe_403_y_no_404_en_modulo_apagado(self):
        self.set_flags(enable_gallery=False)
        self.client.force_login(self.owner_b)
        for name, url in self.gallery_urls().items():
            self.assertEqual(self.client.get(url, HTTP_HOST=HOST_A).status_code, 403, name)


class ContactModuleAccessTests(ModuleAccessBase):
    def _post_contact(self):
        return self.client.post(
            reverse('contact_submit'),
            {'name': 'X', 'email': 'x@test.com', 'message': 'hola'},
            HTTP_HOST=HOST_A,
        )

    def test_contacto_apagado(self):
        self.set_flags(enable_contact_form=False)
        self.assertEqual(self._post_contact().status_code, 404)
        home = self.client.get(reverse('home'), HTTP_HOST=HOST_A)
        self.assertEqual(home.status_code, 200)
        self.assertNotContains(home, reverse('contact_submit'))
        self.login('owner')
        resp = self.client.get(reverse('dashboard_contacts'), HTTP_HOST=HOST_A)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(reverse('dashboard_contacts'), self.menu_urls())
        for name in ('mark_contact_read', 'mark_contact_replied'):
            r = self.client.post(
                reverse(name, kwargs={'contact_id': self.contact.id}), HTTP_HOST=HOST_A)
            self.assertEqual(r.status_code, 302, name)

    def test_contacto_encendido_renderiza_formulario(self):
        self.set_flags(enable_contact_form=True)
        home = self.client.get(reverse('home'), HTTP_HOST=HOST_A)
        self.assertContains(home, reverse('contact_submit'))
        self.assertNotEqual(self._post_contact().status_code, 404)


class MenuPerRoleTests(ModuleAccessBase):
    def test_menu_de_cada_rol_coincide_con_la_matriz(self):
        self.set_flags(enable_gallery=True, enable_contact_form=True)
        entries = [e for m in modules.MODULES for e in m.menu]
        for role in ROLES:
            self.login(role)
            html = self.menu_urls()
            for entry in entries:
                allowed = role in DASHBOARD_PERMISSIONS[entry.permission]
                self.assertEqual(
                    f'href="{reverse(entry.url_name)}"' in html, allowed,
                    f'{role}: {entry.url_name}',
                )

    def test_base_html_sin_enlaces_fijos(self):
        src = (Path(dj_settings.BASE_DIR) / 'templates' / 'dashboard' / 'base.html').read_text(
            encoding='utf-8')
        for name in ('dashboard_gallery', 'dashboard_portada', 'dashboard_branding',
                     'dashboard_sections', 'dashboard_contacts'):
            self.assertNotIn("{% url '" + name + "' %}", src)
        self.assertIn('dash_menu', src)
