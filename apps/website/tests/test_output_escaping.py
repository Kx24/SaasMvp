"""
SEC-14 / BOLT-23: salidas sin escapar (`mark_safe`) y JSON-LD.

Los datos que llegan a los tags (títulos, alt, nombres, SEO) los escribe el
cliente desde su dashboard: son entrada no confiable.
"""
import json
import re
from html.parser import HTMLParser
from unittest import mock

from django.core.cache import cache
from django.template import Context, Template
from django.test import RequestFactory, TestCase

from apps.marketing.models import SEOConfig
from apps.tenants.models import Client

PAYLOAD = '</script><script>alert(1)</script>'
ATTR_BREAK = '"><script>alert(1)</script>'
ATTR_EVENT = '" onerror="alert(1)'

TAGS = 'apps.website.templatetags.cloudinary_tags'
URLS = {
    'mobile': 'https://res.example.com/m.jpg',
    'tablet': 'https://res.example.com/t.jpg',
    'desktop': 'https://res.example.com/d.jpg',
}


class _Collector(HTMLParser):
    """Junta los tags y atributos que un navegador realmente vería."""

    def __init__(self):
        super().__init__()
        self.tags = []
        self.attrs = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attrs.extend(name for name, _ in attrs)


def _parse(html):
    parser = _Collector()
    parser.feed(html)
    return parser


def _render(source, **ctx):
    return Template(source).render(Context(ctx))


class JsonLdEscapingTest(TestCase):

    def setUp(self):
        cache.clear()
        self.client_obj = Client.objects.create(
            name=f'Acme {PAYLOAD}', slug='esc-jsonld', contact_email='a@esc.test',
        )
        SEOConfig.objects.create(
            client=self.client_obj, page_key='home', title='Home',
            schema_type='LocalBusiness',
            schema_json={
                '@context': 'https://schema.org',
                '@type': 'LocalBusiness',
                'name': f'Acme {PAYLOAD}',
                'description': f'Desc {PAYLOAD} & <b>x</b>',
            },
        )

    def test_json_ld_no_cierra_el_bloque(self):
        request = RequestFactory().get('/')
        request.client = self.client_obj
        html = _render('{% load seo_tags %}{% seo_tags "home" %}', request=request)

        match = re.search(
            r'<script type="application/ld\+json">(.*?)</script>', html, re.S,
        )
        self.assertIsNotNone(match)
        block = match.group(1)
        self.assertNotIn('</script>', block.lower())
        self.assertEqual(_parse(html).tags.count('script'), 1)
        data = json.loads(block)
        self.assertEqual(data['name'], f'Acme {PAYLOAD}')
        self.assertEqual(data['description'], f'Desc {PAYLOAD} & <b>x</b>')


@mock.patch(f'{TAGS}.get_srcset_urls', return_value=URLS)
@mock.patch(f'{TAGS}.get_video_thumbnail_url', return_value='https://res.example.com/p.jpg')
@mock.patch(f'{TAGS}.get_video_sources',
            return_value=[{'url': 'https://res.example.com/v.mp4', 'type': 'video/mp4'}])
@mock.patch(f'{TAGS}.get_cloudinary_url', return_value='https://res.example.com/i.jpg')
class CloudinaryTagsEscapingTest(TestCase):

    def _assert_safe(self, html):
        parsed = _parse(html)
        self.assertNotIn('script', parsed.tags)
        self.assertNotIn('onerror', parsed.attrs)

    def test_img(self, *_):
        for img in ('pid', ''):
            html = _render(
                '{% load cloudinary_tags %}'
                '{% cloudinary_img img "hero" alt=alt css_class=cls loading=load %}',
                img=img, alt=ATTR_BREAK, cls=ATTR_EVENT, load=ATTR_EVENT,
            )
            self._assert_safe(html)

    def test_img_extra_attrs(self, *_):
        html = _render(
            '{% load cloudinary_tags %}{% cloudinary_img "pid" "hero" title=t %}',
            t=ATTR_BREAK + ATTR_EVENT,
        )
        self._assert_safe(html)

    def test_picture(self, *_):
        for img in ('pid', ''):
            html = _render(
                '{% load cloudinary_tags %}'
                '{% cloudinary_picture img "hero" alt=alt css_class=cls loading=load %}',
                img=img, alt=ATTR_BREAK, cls=ATTR_EVENT, load=ATTR_EVENT,
            )
            self._assert_safe(html)

    def test_picture_urls(self, urls_mock, *_):
        urls_mock.return_value = {k: v + ATTR_BREAK + ATTR_EVENT for k, v in URLS.items()}
        html = _render('{% load cloudinary_tags %}{% cloudinary_picture "pid" "hero" %}')
        self._assert_safe(html)

    def test_video(self, *_):
        html = _render(
            '{% load cloudinary_tags %}{% cloudinary_video "vid" css_class=cls %}',
            cls=ATTR_BREAK + ATTR_EVENT,
        )
        self._assert_safe(html)

    def test_embed(self, *_):
        html = _render(
            '{% load cloudinary_tags %}'
            '{% cloudinary_embed u title=t css_class=c aspect_ratio=a %}',
            u='https://x.test/' + ATTR_BREAK + ATTR_EVENT,
            t=ATTR_BREAK + ATTR_EVENT, c=ATTR_BREAK + ATTR_EVENT, a=ATTR_EVENT,
        )
        self._assert_safe(html)

    def test_entrada_normal_no_cambia(self, *_):
        html = _render(
            '{% load cloudinary_tags %}{% cloudinary_img "pid" "hero" alt="Foto" css_class="w-full" %}',
        )
        self.assertIn('src="https://res.example.com/i.jpg"', html)
        self.assertIn('alt="Foto"', html)
        self.assertIn('class="w-full"', html)
