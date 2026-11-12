"""
CONS-10 / BOLT-11: red de seguridad para la página pública.

Cada tema arma su `landing/home.html` a mano (`apps/website/views.py::home`
entrega `hero`, `about`, `contact_section`, `services`, `form`). Antes de
separar vistas (CONS-07), generalizar componentes (COMP-01) o migrar
imágenes al pool de medios (MOD-01), estos tests fijan qué debe mostrar la
home de cada tema con datos reales, y que no se cae con datos mínimos.

Se ejercita el camino real: request HTTP con el Host del tenant ->
TenantMiddleware -> vista -> TenantTemplateLoader -> tema.
"""
from django.test import TestCase
from django.urls import reverse

from apps.tenants.models import Client, Domain
from apps.website.models import Section, Service

HERO_TITLE = 'Titular de portada único 7Q'
ABOUT_TITLE = 'Quiénes somos único 7Q'
SERVICE_NAMES = ('Servicio Alfa único 7Q', 'Servicio Beta único 7Q')


class _HomeRenderMixin:
    """Arma un tenant de un tema dado y renderiza su home."""

    slug = None
    template = None
    host = None

    @classmethod
    def _make_client(cls, slug, host, template):
        kwargs = {'name': f'Home {slug}', 'slug': slug, 'contact_email': f'contacto@{host}'}
        if template:
            kwargs['template'] = template
        client = Client.objects.create(**kwargs)
        Domain.objects.create(
            client=client, domain=host, domain_type='custom',
            is_primary=True, is_active=True, is_verified=True,
        )
        return client

    @classmethod
    def _add_full_content(cls, client):
        # La portada de `themes/default` y `themes/servelec` se dibuja con
        # components/media_collection.html: solo muestra el título de la
        # Section hero si el módulo de galería está activo Y la Section tiene
        # slot_key='hero'. Ver HeroDefaultsFindingTest.
        client.settings.enable_gallery = True
        client.settings.save(update_fields=['enable_gallery'])
        Section.objects.create(client=client, section_type='hero', title=HERO_TITLE,
                               subtitle='Subtítulo de portada', slot_key='hero')
        Section.objects.create(client=client, section_type='about', title=ABOUT_TITLE,
                               description='Descripción de la empresa')
        Section.objects.create(client=client, section_type='contact', title='Hablemos')
        for i, name in enumerate(SERVICE_NAMES):
            Service.objects.create(client=client, name=name, description=f'Descripción {i}',
                                   order=i)

    def _get_home(self, host):
        return self.client.get(reverse('home'), HTTP_HOST=host)


class _FullContentTests(_HomeRenderMixin):
    """Home con contenido completo: hero, about, contacto y 2 servicios."""

    @classmethod
    def setUpTestData(cls):
        cls.client_obj = cls._make_client(cls.slug, cls.host, cls.template)
        cls._add_full_content(cls.client_obj)

    def test_home_responds_200(self):
        self.assertEqual(self._get_home(self.host).status_code, 200)

    def test_home_shows_hero_title(self):
        self.assertContains(self._get_home(self.host), HERO_TITLE)

    def test_home_shows_about_title(self):
        self.assertContains(self._get_home(self.host), ABOUT_TITLE)

    def test_home_shows_every_active_service(self):
        response = self._get_home(self.host)
        for name in SERVICE_NAMES:
            self.assertContains(response, name)

    def test_home_hides_inactive_service(self):
        Service.objects.create(client=self.client_obj, name='Servicio Oculto 7Q',
                               description='x', is_active=False)
        self.assertNotContains(self._get_home(self.host), 'Servicio Oculto 7Q')

    def test_home_includes_contact_form(self):
        self.assertContains(self._get_home(self.host), reverse('contact_submit'))


class HeroDefaultsFindingTest(_HomeRenderMixin, TestCase):
    """
    Hallazgo incidental de BOLT-11 (2026-11-12), documentado, NO corregido
    (card DEUDA-08 del kanban maestro): en `themes/default` y `themes/servelec`
    el título de la portada solo aparece si `ClientSettings.enable_gallery`
    es True **y** la Section hero tiene `slot_key='hero'`. Ninguno de los dos
    es el valor por defecto, y ningún camino de alta (`process_onboarding`,
    `provision_tenant`, `create_tenant`, `setup_production`) los fija. Un
    tenant recién creado muestra una portada sin titular.

    Estos tests fijan el comportamiento actual para que el cambio sea
    deliberado: al corregir DEUDA-08 deben invertirse.
    """

    def _home_html(self, slug, template, host, *, gallery, slot_key):
        client = self._make_client(slug, host, template)
        client.settings.enable_gallery = gallery
        client.settings.save(update_fields=['enable_gallery'])
        Section.objects.create(client=client, section_type='hero', title=HERO_TITLE,
                               slot_key=slot_key)
        response = self._get_home(host)
        self.assertEqual(response.status_code, 200)
        return response

    def test_defaults_hide_hero_title_default_theme(self):
        response = self._home_html('hd-default', 'themes/default', 'hddefault.test',
                                   gallery=False, slot_key='empty')
        self.assertNotContains(response, HERO_TITLE)

    def test_defaults_hide_hero_title_servelec_theme(self):
        response = self._home_html('hd-servelec', 'themes/servelec', 'hdservelec.test',
                                   gallery=False, slot_key='empty')
        self.assertNotContains(response, HERO_TITLE)

    def test_gallery_on_but_default_slot_still_hides_title(self):
        response = self._home_html('hd-slot', 'themes/default', 'hdslot.test',
                                   gallery=True, slot_key='empty')
        self.assertNotContains(response, HERO_TITLE)

    def test_hero_slot_without_gallery_still_hides_title(self):
        response = self._home_html('hd-gal', 'themes/default', 'hdgal.test',
                                   gallery=False, slot_key='hero')
        self.assertNotContains(response, HERO_TITLE)


class _MinimalContentTests(_HomeRenderMixin):
    """Home sin about ni servicios ni secciones: no debe caerse."""

    @classmethod
    def setUpTestData(cls):
        cls.client_obj = cls._make_client(f'{cls.slug}-min', f'min.{cls.host}', cls.template)

    def test_home_without_content_responds_200(self):
        self.assertEqual(self._get_home(f'min.{self.host}').status_code, 200)


class DefaultThemeHomeTest(_FullContentTests, TestCase):
    slug, template, host = 'home-default', 'themes/default', 'homedefault.test'


class ServelecThemeHomeTest(_FullContentTests, TestCase):
    slug, template, host = 'home-servelec', 'themes/servelec', 'homeservelec.test'


class AndesscaleHomeTest(_FullContentTests, TestCase):
    # La marca propia se resuelve por slug, no por Client.template.
    slug, template, host = 'andesscale', None, 'homeandesscale.test'


class DefaultThemeMinimalHomeTest(_MinimalContentTests, TestCase):
    slug, template, host = 'home-default', 'themes/default', 'homedefault.test'


class ServelecThemeMinimalHomeTest(_MinimalContentTests, TestCase):
    slug, template, host = 'home-servelec', 'themes/servelec', 'homeservelec.test'


class AndesscaleMinimalHomeTest(_MinimalContentTests, TestCase):
    slug, template, host = 'andesscale', None, 'homeandesscale.test'
