"""
COMP-02 / BOLT-56: árbol de temas ordenado.

- `themes/electricidad` se archivó (el historial de git es el archivo).
- `andesscale` (tema de la plataforma) vive en `templates/themes/andesscale/`.
- Toda carpeta de `templates/themes/` con `base.html` figura en
  `Client.THEME_CHOICES` y viceversa.
- El loader no compara con el literal 'andesscale'.
- La home de la plataforma es idéntica a la anterior al movimiento
  (fixture `tests_data/platform_home.html`, normalizando espacios y CSRF).
"""
import os
import re
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from apps.tenants import template_loader
from apps.tenants.models import Client, Domain

TEMPLATES_DIR = Path(settings.BASE_DIR) / 'templates'
FIXTURE = Path(__file__).parent / 'tests_data' / 'platform_home.html'


def normalize(html):
    html = re.sub(r'(name=["\']csrfmiddlewaretoken["\'] value=["\'])[^"\']*', r'\1X', html)
    html = re.sub(r'(csrf[-_]?token["\']?\s*[:=]\s*["\'])[^"\']*', r'\1X', html, flags=re.I)
    return re.sub(r'\s+', ' ', html).strip()


def _make_client(slug, host, template=None):
    kwargs = {'name': f'Tree {slug}', 'slug': slug, 'contact_email': f'c@{host}'}
    if template:
        kwargs['template'] = template
    client = Client.objects.create(**kwargs)
    Domain.objects.create(client=client, domain=host, domain_type='custom',
                          is_primary=True, is_active=True, is_verified=True)
    return client


class ThemeTreeTest(TestCase):

    def test_electricidad_and_old_andesscale_folders_are_gone(self):
        self.assertFalse((TEMPLATES_DIR / 'themes' / 'electricidad').exists())
        self.assertFalse((TEMPLATES_DIR / 'andesscale').exists())
        self.assertTrue((TEMPLATES_DIR / 'themes' / 'andesscale' / 'base.html').exists())

    def test_theme_folders_match_theme_choices(self):
        folders = {
            f'themes/{p.name}' for p in (TEMPLATES_DIR / 'themes').iterdir()
            if p.is_dir() and (p / 'base.html').exists()
        }
        choices = {value for value, _ in Client.THEME_CHOICES}
        self.assertEqual(folders, choices)

    def test_loader_has_no_hardcoded_platform_slug(self):
        source = Path(template_loader.__file__).read_text(encoding='utf-8')
        code = re.sub(r'""".*?"""', '', source, flags=re.S)
        self.assertNotIn("'andesscale'", code)
        self.assertNotIn('"andesscale"', code)

    def test_home_renders_200_for_each_theme(self):
        _make_client(settings.PLATFORM_TENANT_SLUG, 'plat-tree.test', 'themes/andesscale')
        _make_client('tree-default', 'tree-default.test', 'themes/default')
        _make_client('tree-servelec', 'tree-servelec.test', 'themes/servelec')
        for host in ('plat-tree.test', 'tree-default.test', 'tree-servelec.test'):
            response = self.client.get(reverse('home'), HTTP_HOST=host)
            self.assertEqual(response.status_code, 200, host)

    def test_platform_home_resolves_without_migrated_template_field(self):
        """Base sin migrar: slug de plataforma y template por defecto."""
        _make_client(settings.PLATFORM_TENANT_SLUG, 'plat-old.test')
        response = self.client.get(reverse('home'), HTTP_HOST='plat-old.test')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'js/clients/andesscale/canvas_global.js')

    def test_platform_home_html_identical_to_pre_move_fixture(self):
        _make_client(settings.PLATFORM_TENANT_SLUG, 'plat-fixture.test', 'themes/andesscale')
        html = self.client.get(reverse('home'), HTTP_HOST='plat-fixture.test').content.decode()
        if os.environ.get('GENERATE_PLATFORM_FIXTURE'):
            FIXTURE.parent.mkdir(exist_ok=True)
            FIXTURE.write_text(normalize(html), encoding='utf-8')
        self.assertEqual(normalize(html), FIXTURE.read_text(encoding='utf-8'))
