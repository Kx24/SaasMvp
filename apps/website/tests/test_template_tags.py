"""BOLT-38 (CONS-11): cobertura de tenant_tags, website_tags y cloudinary_tags."""
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from django.template import Context, Template
from django.test import SimpleTestCase, TestCase, override_settings

from apps.tenants.models import Client, FormConfig
from apps.website.models import GalleryItem, Section, Service
from apps.website.templatetags import website_tags


def render(source, **ctx):
    return Template(source).render(Context(ctx))


def req(client):
    return SimpleNamespace(client=client)


# ============================================================================
# tenant_tags
# ============================================================================

class TenantTagsTests(SimpleTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.media = Path(self.tmp.name)
        (self.media / 'tenants' / 'acme').mkdir(parents=True)
        (self.media / 'tenants' / 'acme' / 'logo.png').write_bytes(b'x')
        self.acme = SimpleNamespace(slug='acme')

    def r(self, source, **ctx):
        with override_settings(MEDIA_ROOT=str(self.media), MEDIA_URL='/m/', STATIC_URL='/s/'):
            return render('{% load tenant_tags %}' + source, **ctx)

    def test_tenant_static_existente_en_media(self):
        self.assertEqual(self.r("{% tenant_static 'logo.png' %}", client=self.acme),
                         '/m/tenants/acme/logo.png')

    def test_tenant_static_fallback_a_static(self):
        self.assertEqual(self.r("{% tenant_static 'nada.png' %}", client=self.acme), '/s/nada.png')

    def test_tenant_static_sin_tenant(self):
        self.assertEqual(self.r("{% tenant_static 'logo.png' %}"), '/s/logo.png')

    def test_tenant_static_cliente_desde_request(self):
        out = self.r("{% tenant_static 'logo.png' %}", request=req(self.acme))
        self.assertEqual(out, '/m/tenants/acme/logo.png')

    def test_tenant_media(self):
        self.assertEqual(self.r("{% tenant_media 'x.png' %}", client=self.acme), '/m/tenants/acme/x.png')
        self.assertEqual(self.r("{% tenant_media 'x.png' %}"), '/m/x.png')

    def test_get_tenant_media_url(self):
        src = "{% get_tenant_media_url 'logo.png' as u %}[{{ u }}]"
        self.assertEqual(self.r(src, client=self.acme), '[/m/tenants/acme/logo.png]')
        self.assertEqual(self.r("{% get_tenant_media_url 'nada.png' as u %}[{{ u }}]",
                                client=self.acme), '[]')
        self.assertEqual(self.r(src), '[]')

    def test_get_tenant_slug(self):
        self.assertEqual(self.r('{% get_tenant_slug %}', client=self.acme), 'acme')
        self.assertEqual(self.r('{% get_tenant_slug %}'), 'default')

    def test_tenant_include_prioriza_template_del_tenant(self):
        from apps.tenants.templatetags import tenant_tags
        vistos = []

        def fake(name, ctx):
            vistos.append(name)
            return 'OK' if name == 'tenants/acme/c.html' else (_ for _ in ()).throw(
                tenant_tags.TemplateDoesNotExist(name))

        with mock.patch.object(tenant_tags, 'render_to_string', side_effect=fake):
            out = render("{% load tenant_tags %}{% tenant_include 'c.html' %}", client=self.acme)
        self.assertEqual(out, 'OK')
        self.assertEqual(vistos, ['tenants/acme/c.html'])

    def test_tenant_include_cae_a_default_y_luego_a_normal(self):
        from apps.tenants.templatetags import tenant_tags
        vistos = []

        def fake(name, ctx):
            vistos.append(name)
            if name == 'c.html':
                return 'NORMAL'
            raise tenant_tags.TemplateDoesNotExist(name)

        with mock.patch.object(tenant_tags, 'render_to_string', side_effect=fake):
            out = render("{% load tenant_tags %}{% tenant_include 'c.html' %}", client=self.acme)
        self.assertEqual(vistos, ['tenants/acme/c.html', 'tenants/_default/c.html', 'c.html'])
        self.assertEqual(out, 'NORMAL')

    def test_tenant_include_sin_tenant_ni_templates(self):
        out = render("{% load tenant_tags %}{% tenant_include 'no/existe.html' %}")
        self.assertEqual(out, '<!-- Template not found: no/existe.html -->')

    def test_tenant_template_exists(self):
        from apps.tenants.templatetags import tenant_tags
        src = "{% load tenant_tags %}{% tenant_template_exists 'x.html' as e %}{{ e }}"
        with mock.patch.object(tenant_tags, 'get_template'):
            self.assertEqual(render(src, client=self.acme), 'True')
        with mock.patch.object(tenant_tags, 'get_template',
                               side_effect=tenant_tags.TemplateDoesNotExist('x')):
            self.assertEqual(render(src, client=self.acme), 'False')
        self.assertEqual(render(src), 'False')


# ============================================================================
# website_tags (simples, sin DB)
# ============================================================================

class WebsiteTagsPureTests(SimpleTestCase):
    def test_slot_template_conocido_y_desconocido(self):
        self.assertEqual(website_tags.slot_template('hero'), 'components/slots/hero_overlay.html')
        self.assertEqual(website_tags.slot_template(''), 'components/slots/empty.html')
        with self.assertLogs(website_tags.logger, level='WARNING'):
            self.assertEqual(website_tags.slot_template('raro'), 'components/slots/empty.html')

    def test_google_fonts_query_delegado(self):
        with mock.patch.object(website_tags, '_google_fonts_query', return_value='Inter') as g:
            self.assertEqual(render('{% load website_tags %}{% google_fonts_query "Inter" %}'), 'Inter')
        g.assert_called_once_with('Inter')

    def test_filtros(self):
        self.assertEqual(render('{% load website_tags %}{{ t|split:"-"|join:"+" }}', t='a-b-c'), 'a+b+c')
        self.assertEqual(render('{% load website_tags %}{{ t|split|length }}', t=None), '0')
        self.assertEqual(render('{% load website_tags %}{{ t|first }}', t=[1, 2]), '1')
        self.assertEqual(render('{% load website_tags %}[{{ t|first }}]', t=[]), '[]')
        self.assertEqual(render('{% load website_tags %}{{ t|last }}', t=[1, 2]), '2')
        self.assertEqual(render('{% load website_tags %}[{{ t|last }}]', t=None), '[]')

    def test_tags_sin_request_devuelven_vacio(self):
        out = render(
            '{% load website_tags %}'
            '{% get_section "hero" as s %}{% get_services as sv %}'
            '{% get_featured_services as fs %}{% client_settings as cs %}'
            '{% get_gallery as g %}{% get_hero_images as h %}'
            '{{ s }}|{{ sv }}|{{ fs }}|{{ cs }}|{{ g }}|{{ h }}'
        )
        self.assertEqual(out, 'None|[]|[]|None|[]|[]')

    def test_tags_de_testimonios_eliminados(self):
        """Testimonial ya no existe (CONS-05): los tags huérfanos lanzaban ImportError."""
        self.assertNotIn('get_testimonials', website_tags.register.tags)
        self.assertNotIn('get_featured_testimonials', website_tags.register.tags)

    def test_form_config_default_sin_cliente(self):
        fc = render('{% load website_tags %}{% get_form_config as fc %}{{ fc.submit_button_text }}'
                    '|{{ fc.name_label }}', request=SimpleNamespace(client=None))
        self.assertEqual(fc, 'Enviar mensaje|Nombre completo')

    def test_default_form_config_listas(self):
        d = website_tags.DefaultFormConfig()
        self.assertEqual(d.get_subject_options_list()[0], 'Consulta general')
        self.assertEqual(len(d.get_subject_options_list()), 4)
        self.assertEqual(d.get_budget_options_list()[-1], 'Más de $1.000.000')
        self.assertEqual(d.get_urgency_options_list(), ['Normal', 'Urgente', 'Muy urgente (24h)'])
        self.assertIn('Google', d.get_source_options_list())


# ============================================================================
# website_tags (con DB)
# ============================================================================

class WebsiteTagsDbTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = Client.objects.create(name='A', slug='tags-a', contact_email='a@a.test',
                                      template='themes/default')
        cls.b = Client.objects.create(name='B', slug='tags-b', contact_email='b@b.test',
                                      template='themes/default')
        cls.hero_a = Section.objects.create(client=cls.a, section_type='hero', title='Hero A')
        cls.hero_b = Section.objects.create(client=cls.b, section_type='hero', title='Hero B')
        cls.gal_a = Section.objects.create(client=cls.a, section_type='gallery', title='Gal A')

    def test_get_section_filtra_por_tenant(self):
        ctx = {'request': req(self.a)}
        out = render('{% load website_tags %}{% get_section "hero" as s %}{{ s.title }}', **ctx)
        self.assertEqual(out, 'Hero A')

    def test_get_section_inexistente_o_inactiva(self):
        out = render('{% load website_tags %}{% get_section "about" as s %}{{ s }}', request=req(self.a))
        self.assertEqual(out, 'None')
        Section.objects.filter(pk=self.hero_a.pk).update(is_active=False)
        out = render('{% load website_tags %}{% get_section "hero" as s %}{{ s }}', request=req(self.a))
        self.assertEqual(out, 'None')

    def test_get_section_duplicadas_devuelve_la_primera(self):
        """La BD lo impide con UNIQUE; se simula la rama defensiva."""
        with mock.patch.object(website_tags.Section.objects, 'get',
                               side_effect=Section.MultipleObjectsReturned):
            with self.assertLogs(website_tags.logger, level='WARNING'):
                out = render('{% load website_tags %}{% get_section "hero" as s %}{{ s.title }}',
                             request=req(self.a))
        self.assertEqual(out, 'Hero A')

    def _service(self, client, name, order, featured=False, active=True):
        return Service.objects.create(client=client, name=name, slug=name.lower(), description='d',
                                      order=order, is_featured=featured, is_active=active)

    def test_servicios_ordenados_activos_y_del_tenant(self):
        self._service(self.a, 'Dos', 2, featured=True)
        self._service(self.a, 'Uno', 1)
        self._service(self.a, 'Off', 3, active=False)
        self._service(self.b, 'Ajeno', 1, featured=True)
        r = req(self.a)
        out = render('{% load website_tags %}{% get_services as s %}'
                     '{% for x in s %}{{ x.name }},{% endfor %}', request=r)
        self.assertEqual(out, 'Uno,Dos,')
        out = render('{% load website_tags %}{% get_featured_services as s %}'
                     '{% for x in s %}{{ x.name }},{% endfor %}', request=r)
        self.assertEqual(out, 'Dos,')

    def test_client_settings(self):
        out = render('{% load website_tags %}{% client_settings as cs %}{{ cs.client.slug }}',
                     request=req(self.a))
        self.assertEqual(out, 'tags-a')
        out = render('{% load website_tags %}{% client_settings as cs %}{{ cs }}',
                     request=req(SimpleNamespace()))
        self.assertEqual(out, 'None')

    def _gallery_item(self, client, section, order=0, active=True):
        return GalleryItem.objects.create(client=client, section=section, image='pid',
                                          order=order, is_active=active, title=f'g{order}')

    def test_get_gallery_respeta_flag(self):
        self._gallery_item(self.a, self.gal_a, 1)
        self._gallery_item(self.a, self.gal_a, 2, active=False)
        src = '{% load website_tags %}{% get_gallery as g %}{% for i in g %}{{ i.title }},{% endfor %}'
        self.a.settings.enable_gallery = True
        self.a.settings.save()
        self.assertEqual(render(src, request=req(Client.objects.get(pk=self.a.pk))), 'g1,')
        self.a.settings.enable_gallery = False
        self.a.settings.save()
        self.assertEqual(render(src, request=req(Client.objects.get(pk=self.a.pk))), '')

    def test_get_gallery_sin_settings(self):
        cli = SimpleNamespace(settings=None)
        out = render('{% load website_tags %}{% get_gallery as g %}{{ g }}', request=req(cli))
        self.assertEqual(out, '[]')

    def test_get_hero_images(self):
        item = self._gallery_item(self.a, self.hero_a, 1)
        s = self.a.settings
        src = '{% load website_tags %}{% get_hero_images as h %}{% for i in h %}{{ i.title|default:"DEF" }},{% endfor %}'

        # galería apagada → solo el hero default
        s.enable_gallery = False
        s.save()
        self.assertEqual(render(src, request=req(Client.objects.get(pk=self.a.pk))), 'DEF,')

        # galería activa + show_default_hero → default + imágenes
        s.enable_gallery = True
        s.show_default_hero = True
        s.save()
        self.assertEqual(render(src, request=req(Client.objects.get(pk=self.a.pk))), 'DEF,g1,')

        # sin default → solo imágenes
        s.show_default_hero = False
        s.save()
        self.assertEqual(render(src, request=req(Client.objects.get(pk=self.a.pk))), 'g1,')

        # sin imágenes activas → default aunque show_default_hero=False
        GalleryItem.objects.filter(pk=item.pk).update(is_active=False)
        self.assertEqual(render(src, request=req(Client.objects.get(pk=self.a.pk))), 'DEF,')

    def test_get_hero_images_sin_settings(self):
        out = render('{% load website_tags %}{% get_hero_images as h %}{{ h|length }}',
                     request=req(SimpleNamespace(settings=None)))
        self.assertEqual(out, '1')

    def test_get_form_config_existente_y_creado(self):
        fc = FormConfig.objects.get(client=self.a)
        out = render('{% load website_tags %}{% get_form_config as fc %}{{ fc.pk }}', request=req(self.a))
        self.assertEqual(out, str(fc.pk))
        fc.delete()
        cli = Client.objects.get(pk=self.a.pk)
        out = render('{% load website_tags %}{% get_form_config as fc %}{{ fc.client.slug }}',
                     request=req(cli))
        self.assertEqual(out, 'tags-a')
        self.assertTrue(FormConfig.objects.filter(client=self.a).exists())


# ============================================================================
# cloudinary_tags
# ============================================================================

class FakeImage:
    def __init__(self, url='https://cdn.test/i.jpg'):
        self.url = url

    def build_url(self, **kw):
        return self.url

    def __bool__(self):
        return True


class CloudinaryTagsTests(SimpleTestCase):
    L = '{% load cloudinary_tags %}'

    def test_url_vacio_y_con_imagen(self):
        self.assertEqual(render(self.L + "{% cloudinary_url img 'hero' %}", img=None), '')
        self.assertEqual(render(self.L + "{% cloudinary_url img 'hero' %}", img=FakeImage()),
                         'https://cdn.test/i.jpg')

    def test_url_error_del_sdk_devuelve_vacio(self):
        bad = FakeImage()
        bad.build_url = mock.Mock(side_effect=RuntimeError('x'))
        with self.assertLogs('apps.core.cloudinary_utils', level='ERROR'):
            self.assertEqual(render(self.L + "{% cloudinary_url img %}", img=bad), '')

    def test_img_placeholder(self):
        out = render(self.L + "{% cloudinary_img img 'hero' alt='Banner' css_class='w-full' %}", img=None)
        self.assertIn('src="/static/img/placeholder.jpg"', out)
        self.assertIn('alt="Banner"', out)
        self.assertIn('loading="lazy"', out)

    def test_img_url_fallida_usa_placeholder(self):
        with mock.patch('apps.website.templatetags.cloudinary_tags.get_cloudinary_url', return_value=None):
            out = render(self.L + "{% cloudinary_img img %}", img=FakeImage())
        self.assertIn('placeholder.jpg', out)

    def test_img_con_dimensiones_del_preset_y_extras(self):
        out = render(self.L + "{% cloudinary_img img 'hero' alt='B' css_class='x' loading='eager' %}",
                     img=FakeImage())
        self.assertIn('src="https://cdn.test/i.jpg"', out)
        self.assertIn('width="1440"', out)
        self.assertIn('height="700"', out)
        self.assertIn('loading="eager"', out)

    def test_img_dimensiones_explicitas_y_atributos_extra_escapados(self):
        out = render(self.L + "{% cloudinary_img img 'hero' width=10 height=20 data_x=v %}",
                     img=FakeImage(), v='"><script>')
        self.assertIn('width="10"', out)
        self.assertIn('height="20"', out)
        self.assertNotIn('<script>', out)
        self.assertIn('data_x="&quot;&gt;&lt;script&gt;"', out)

    def test_img_preset_sin_dimensiones_omite_atributos_vacios(self):
        with mock.patch.dict('apps.website.templatetags.cloudinary_tags.CLOUDINARY_PRESETS',
                             {'sin_dim': {'crop': 'fill'}}), \
                mock.patch('apps.website.templatetags.cloudinary_tags.get_cloudinary_url',
                           return_value='https://cdn.test/z'):
            out = render(self.L + "{% cloudinary_img img 'sin_dim' %}", img=FakeImage())
        self.assertNotIn('width=', out)
        self.assertNotIn('class=', out)

    def test_picture_placeholder(self):
        out = render(self.L + "{% cloudinary_picture img alt='A' %}", img=None)
        self.assertTrue(out.startswith('<picture><img src="/static/img/placeholder.jpg"'))

    def test_picture_sin_urls(self):
        with mock.patch('apps.website.templatetags.cloudinary_tags.get_srcset_urls',
                        return_value={'mobile': None, 'tablet': None, 'desktop': None, 'srcset': ''}):
            out = render(self.L + "{% cloudinary_picture img %}", img=FakeImage())
        self.assertIn('placeholder.jpg', out)

    def test_picture_completo(self):
        out = render(self.L + "{% cloudinary_picture img 'hero' alt='A' loading='eager' %}", img=FakeImage())
        self.assertIn('<source media="(max-width: 480px)" srcset="https://cdn.test/i.jpg">', out)
        self.assertIn('<source media="(max-width: 768px)"', out)
        self.assertIn('src="https://cdn.test/i.jpg"', out)
        self.assertIn('width="1440"', out)
        self.assertTrue(out.endswith('</picture>'))

    def test_picture_solo_desktop_usa_fallback(self):
        with mock.patch('apps.website.templatetags.cloudinary_tags.get_srcset_urls',
                        return_value={'mobile': None, 'tablet': None, 'desktop': 'D', 'srcset': 'D'}):
            out = render(self.L + "{% cloudinary_picture img %}", img=FakeImage())
        self.assertNotIn('<source', out)
        self.assertIn('src="D"', out)

    def test_bg(self):
        self.assertEqual(render(self.L + "{% cloudinary_bg img %}", img=None), '/static/img/placeholder.jpg')
        self.assertEqual(render(self.L + "{% cloudinary_bg img %}", img=FakeImage()), 'https://cdn.test/i.jpg')
        with mock.patch('apps.website.templatetags.cloudinary_tags.get_cloudinary_url', return_value=None):
            self.assertEqual(render(self.L + "{% cloudinary_bg img %}", img=FakeImage()),
                             '/static/img/placeholder.jpg')

    def test_video_vacio_o_sin_fuentes(self):
        self.assertEqual(render(self.L + "{% cloudinary_video v %}", v=None), '')
        with mock.patch('apps.website.templatetags.cloudinary_tags.get_video_sources', return_value=[]):
            self.assertEqual(render(self.L + "{% cloudinary_video v %}", v='vid'), '')

    def _video(self, source, **extra):
        srcs = [{'url': 'https://cdn.test/v.webm', 'type': 'video/webm'},
                {'url': 'https://cdn.test/v.mp4', 'type': 'video/mp4'}]
        with mock.patch('apps.website.templatetags.cloudinary_tags.get_video_sources', return_value=srcs), \
                mock.patch('apps.website.templatetags.cloudinary_tags.get_video_thumbnail_url',
                           return_value='https://cdn.test/poster.jpg'):
            return render(self.L + source, v='vid', p=extra.get('p'))

    def test_video_por_defecto(self):
        out = self._video("{% cloudinary_video v css_class='w-full' %}")
        self.assertIn('class="w-full"', out)
        self.assertIn('poster="https://cdn.test/poster.jpg"', out)
        self.assertIn('<source src="https://cdn.test/v.webm" type="video/webm">', out)
        self.assertIn('<source src="https://cdn.test/v.mp4" type="video/mp4">', out)
        self.assertIn('muted controls playsinline', out)
        self.assertNotIn('autoplay', out)

    def test_video_autoplay_loop_sin_controles(self):
        out = self._video('{% cloudinary_video v autoplay=True loop=True controls=False playsinline=False %}')
        self.assertIn('muted autoplay loop', out)
        self.assertNotIn('controls', out)
        self.assertNotIn('playsinline', out)

    def test_video_con_poster_propio(self):
        with mock.patch('apps.website.templatetags.cloudinary_tags.get_cloudinary_url',
                        return_value='https://cdn.test/mi-poster.jpg'):
            out = self._video('{% cloudinary_video v poster_image=p %}', p=FakeImage())
        self.assertIn('poster="https://cdn.test/mi-poster.jpg"', out)

    def test_video_sin_muted(self):
        out = self._video('{% cloudinary_video v muted=False controls=False playsinline=False %}')
        self.assertNotIn('muted', out)

    def test_embed(self):
        self.assertEqual(render(self.L + "{% cloudinary_embed u %}", u=''), '')
        out = render(self.L + "{% cloudinary_embed u title='Demo' css_class='rounded' aspect_ratio='4/3' %}",
                     u='https://www.youtube.com/embed/abc')
        self.assertIn('class="relative w-full overflow-hidden rounded"', out)
        self.assertIn('aspect-ratio: 4/3', out)
        self.assertIn('src="https://www.youtube.com/embed/abc"', out)
        self.assertIn('title="Demo"', out)

    def test_embed_escapa_url(self):
        out = render(self.L + "{% cloudinary_embed u %}", u='x"onload="y')
        self.assertNotIn('"onload=', out)
        self.assertIn('&quot;', out)

    def test_filtros(self):
        self.assertEqual(render(self.L + "{{ img|cloudinary:'hero' }}", img=None), '')
        self.assertEqual(render(self.L + "{{ img|cloudinary:'hero' }}", img=FakeImage()),
                         'https://cdn.test/i.jpg')
        self.assertEqual(render(self.L + "{{ v|cloudinary_video_url }}", v=None), '')
        with mock.patch('apps.website.templatetags.cloudinary_tags.get_video_url',
                        return_value='https://cdn.test/v.mp4') as g:
            self.assertEqual(render(self.L + "{{ v|cloudinary_video_url:'mobile' }}", v='vid'),
                             'https://cdn.test/v.mp4')
        g.assert_called_once_with('vid', 'mobile')

    def test_listas_de_presets(self):
        out = render(self.L + "{% cloudinary_presets as p %}{% cloudinary_video_presets as v %}"
                              "{{ p.hero.width }}-{{ v.web_hd.width }}")
        self.assertEqual(out, '1440-1280')
