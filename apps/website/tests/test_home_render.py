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


class HeroDefaultsTest(_HomeRenderMixin, TestCase):
    """
    DEUDA-08 / BOLT-19: con slot_key='hero' la portada muestra su titular
    aunque la galería esté apagada; slot_key='empty' (elegido a mano) sigue
    significando "sin overlay". Los altas crean la hero con slot_key='hero'.
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

    def test_hero_slot_without_gallery_shows_title_default_theme(self):
        response = self._home_html('hd-default', 'themes/default', 'hddefault.test',
                                   gallery=False, slot_key='hero')
        self.assertContains(response, HERO_TITLE)

    def test_hero_slot_without_gallery_shows_title_servelec_theme(self):
        response = self._home_html('hd-servelec', 'themes/servelec', 'hdservelec.test',
                                   gallery=False, slot_key='hero')
        self.assertContains(response, HERO_TITLE)

    def test_hero_slot_with_gallery_shows_title(self):
        for slug, template, host in (('hd-gd', 'themes/default', 'hdgd.test'),
                                     ('hd-gs', 'themes/servelec', 'hdgs.test')):
            response = self._home_html(slug, template, host, gallery=True, slot_key='hero')
            self.assertContains(response, HERO_TITLE)

    def test_empty_slot_hides_title_with_and_without_gallery(self):
        n = 0
        for template in ('themes/default', 'themes/servelec'):
            for gallery in (False, True):
                n += 1
                response = self._home_html(f'hd-e{n}', template, f'hde{n}.test',
                                           gallery=gallery, slot_key='empty')
                self.assertNotContains(response, HERO_TITLE)

    def test_provision_tenant_creates_hero_with_slot_key_and_shows_title(self):
        from django.core.management import call_command
        for theme in ('themes/default', 'themes/servelec'):
            slug = 'prov-' + theme.split('/')[1]
            call_command('provision_tenant', slug, '--theme=' + theme, verbosity=0)
            client = Client.objects.get(slug=slug)
            hero = Section.objects.get(client=client, section_type='hero')
            self.assertEqual(hero.slot_key, 'hero')
            host = f'{slug}.test'
            Domain.objects.create(client=client, domain=host, domain_type='custom',
                                  is_primary=True, is_active=True, is_verified=True)
            self.assertContains(self._get_home(host), hero.title)

    def test_dashboard_hero_get_or_create_defaults_slot_key_hero(self):
        import inspect

        from apps.website.views import dashboard_portada
        self.assertIn("'slot_key': 'hero'", inspect.getsource(dashboard_portada))


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
