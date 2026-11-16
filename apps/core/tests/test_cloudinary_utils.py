"""BOLT-38 (CONS-11): cobertura de apps/core/cloudinary_utils.py — sin red."""
import io
from types import SimpleNamespace
from unittest import mock

from django.test import SimpleTestCase

from apps.core import cloudinary_utils as cu


class FakeResource:
    """Imita CloudinaryResource: build_url devuelve los kwargs serializados."""

    def __init__(self, fail=False):
        self.fail = fail
        self.calls = []

    def build_url(self, **kwargs):
        if self.fail:
            raise RuntimeError('boom')
        self.calls.append(kwargs)
        return 'https://cdn.test/img?' + ','.join(sorted(kwargs))

    def __bool__(self):
        return True


class FolderTests(SimpleTestCase):
    def test_folder_ok(self):
        self.assertEqual(cu.get_cloudinary_folder('acme', 'sections'), 'tenants/acme/sections')

    def test_folder_slug_vacio(self):
        with self.assertRaises(ValueError):
            cu.get_cloudinary_folder('', 'sections')

    def test_folder_tipo_invalido(self):
        with self.assertRaises(ValueError):
            cu.get_cloudinary_folder('acme', 'nada')

    def test_upload_path_tipo_invalido(self):
        with self.assertRaises(ValueError):
            cu.cloudinary_upload_path('nada')

    def test_upload_path_con_client(self):
        fn = cu.cloudinary_upload_path('gallery')
        inst = SimpleNamespace(client=SimpleNamespace(slug='acme'))
        self.assertEqual(fn(inst, 'x.jpg'), 'tenants/acme/gallery')
        self.assertEqual(fn.__name__, 'upload_to_gallery')

    def test_upload_path_instancia_es_tenant(self):
        fn = cu.cloudinary_upload_path('branding')
        self.assertEqual(fn(SimpleNamespace(slug='solo'), 'x.png'), 'tenants/solo/branding')

    def test_upload_path_desconocido(self):
        fn = cu.cloudinary_upload_path('services')
        with self.assertLogs(cu.logger, level='WARNING'):
            self.assertEqual(fn(object(), 'x.png'), 'tenants/unknown/services')


class UrlTests(SimpleTestCase):
    def test_vacio_devuelve_none(self):
        self.assertIsNone(cu.get_cloudinary_url(None))
        self.assertIsNone(cu.get_cloudinary_url(''))

    def test_preset_separa_fetch_format(self):
        res = FakeResource()
        url = cu.get_cloudinary_url(res, 'hero')
        self.assertTrue(url.startswith('https://cdn.test/'))
        kwargs = res.calls[0]
        self.assertEqual(kwargs['fetch_format'], 'auto')
        transformation = kwargs['transformation'][0]
        self.assertNotIn('fetch_format', transformation)
        self.assertEqual(transformation['width'], 1440)
        self.assertEqual(transformation['crop'], 'fill')

    def test_extra_options_sobreescriben(self):
        res = FakeResource()
        cu.get_cloudinary_url(res, 'hero', width=100, fetch_format='webp')
        kwargs = res.calls[0]
        self.assertEqual(kwargs['transformation'][0]['width'], 100)
        self.assertEqual(kwargs['fetch_format'], 'webp')

    def test_sin_fetch_format_no_se_pasa(self):
        res = FakeResource()
        cu.get_cloudinary_url(res, 'hero', fetch_format=None)
        self.assertNotIn('fetch_format', res.calls[0])

    def test_preset_desconocido_cae_a_thumbnail(self):
        res = FakeResource()
        with self.assertLogs(cu.logger, level='WARNING'):
            cu.get_cloudinary_url(res, 'inexistente')
        self.assertEqual(res.calls[0]['transformation'][0]['width'], 300)

    def test_string_usa_cloudinary_image(self):
        with mock.patch.object(cu.cloudinary, 'CloudinaryImage') as img:
            img.return_value.build_url.return_value = 'https://cdn.test/pid'
            self.assertEqual(cu.get_cloudinary_url('pid', 'logo'), 'https://cdn.test/pid')
        img.assert_called_once_with('pid')

    def test_objeto_sin_build_url_se_castea(self):
        self.assertEqual(cu.get_cloudinary_url(12345), '12345')

    def test_error_devuelve_none(self):
        with self.assertLogs(cu.logger, level='ERROR'):
            self.assertIsNone(cu.get_cloudinary_url(FakeResource(fail=True), 'hero'))

    def test_presets_no_se_mutan(self):
        before = dict(cu.CLOUDINARY_PRESETS['hero'])
        cu.get_cloudinary_url(FakeResource(), 'hero', width=1)
        self.assertEqual(cu.CLOUDINARY_PRESETS['hero'], before)


class SrcsetTests(SimpleTestCase):
    def test_vacio(self):
        self.assertEqual(
            cu.get_srcset_urls(None),
            {'mobile': None, 'tablet': None, 'desktop': None, 'srcset': ''},
        )

    def test_preset_mapeado_usa_variantes(self):
        res = FakeResource()
        out = cu.get_srcset_urls(res, 'hero')
        widths = [c['transformation'][0]['width'] for c in res.calls]
        self.assertEqual(widths, [480, 768, 1440])
        self.assertEqual(out['srcset'].count(' 480w'), 1)
        self.assertIn(' 768w', out['srcset'])
        self.assertTrue(out['srcset'].endswith(' 1200w'))

    def test_preset_no_mapeado_repite(self):
        res = FakeResource()
        cu.get_srcset_urls(res, 'logo')
        widths = {c['transformation'][0]['width'] for c in res.calls}
        self.assertEqual(widths, {300})

    def test_urls_fallidas_se_omiten(self):
        with self.assertLogs(cu.logger, level='ERROR'):
            out = cu.get_srcset_urls(FakeResource(fail=True), 'hero')
        self.assertEqual(out['srcset'], '')
        self.assertIsNone(out['mobile'])


class VideoTests(SimpleTestCase):
    def test_video_url_vacio(self):
        self.assertIsNone(cu.get_video_url(None))

    def test_video_url_objeto(self):
        res = FakeResource()
        cu.get_video_url(res, 'web_sd')
        kwargs = res.calls[0]
        self.assertEqual(kwargs['resource_type'], 'video')
        self.assertEqual(kwargs['width'], 854)

    def test_video_url_preset_desconocido(self):
        res = FakeResource()
        with self.assertLogs(cu.logger, level='WARNING'):
            cu.get_video_url(res, 'nope')
        self.assertEqual(res.calls[0]['width'], 1280)

    def test_video_url_thumbnail_preset_quita_resource_type(self):
        res = FakeResource()
        cu.get_video_url(res, 'thumbnail')
        # resource_type viene del llamado, no del preset
        self.assertEqual(res.calls[0]['resource_type'], 'video')

    def test_video_url_string(self):
        with mock.patch.object(cu.cloudinary, 'CloudinaryVideo') as vid:
            vid.return_value.build_url.return_value = 'https://cdn.test/v'
            self.assertEqual(cu.get_video_url('vid', 'mobile'), 'https://cdn.test/v')

    def test_video_url_otro_tipo(self):
        self.assertEqual(cu.get_video_url(99), '99')

    def test_video_url_error(self):
        with self.assertLogs(cu.logger, level='ERROR'):
            self.assertIsNone(cu.get_video_url(FakeResource(fail=True)))

    def test_thumbnail_vacio(self):
        self.assertIsNone(cu.get_video_thumbnail_url(''))

    def test_thumbnail_ok(self):
        with mock.patch.object(cu.cloudinary, 'CloudinaryVideo') as vid:
            vid.return_value.build_url.return_value = 'https://cdn.test/t.jpg'
            self.assertEqual(cu.get_video_thumbnail_url('vid', 100, 50), 'https://cdn.test/t.jpg')
        vid.assert_called_once_with('vid')
        kwargs = vid.return_value.build_url.call_args.kwargs
        self.assertEqual((kwargs['width'], kwargs['height'], kwargs['format']), (100, 50, 'jpg'))

    def test_thumbnail_castea_no_string(self):
        with mock.patch.object(cu.cloudinary, 'CloudinaryVideo') as vid:
            vid.return_value.build_url.return_value = 'u'
            cu.get_video_thumbnail_url(FakeResource())
        self.assertIsInstance(vid.call_args.args[0], str)

    def test_thumbnail_error(self):
        with mock.patch.object(cu.cloudinary, 'CloudinaryVideo', side_effect=RuntimeError('x')):
            with self.assertLogs(cu.logger, level='ERROR'):
                self.assertIsNone(cu.get_video_thumbnail_url('vid'))

    def test_sources_vacio(self):
        self.assertEqual(cu.get_video_sources(None), [])

    def test_sources_webm_y_mp4(self):
        with mock.patch.object(cu.cloudinary, 'CloudinaryVideo') as vid:
            vid.return_value.build_url.return_value = 'https://cdn.test/v'
            sources = cu.get_video_sources('vid')
        self.assertEqual([s['type'] for s in sources], ['video/webm', 'video/mp4'])

    def test_sources_webm_falla_queda_mp4(self):
        vid = mock.Mock()
        vid.build_url.side_effect = [None, RuntimeError('x')]
        with mock.patch.object(cu, 'get_video_url', return_value='https://cdn.test/mp4'), \
                mock.patch.object(cu.cloudinary, 'CloudinaryVideo', return_value=mock.Mock(
                    build_url=mock.Mock(side_effect=RuntimeError('x')))):
            sources = cu.get_video_sources('vid')
        self.assertEqual(sources, [{'url': 'https://cdn.test/mp4', 'type': 'video/mp4'}])

    def test_sources_sin_url_devuelve_vacio(self):
        with mock.patch.object(cu, 'get_video_url', return_value=None):
            self.assertEqual(cu.get_video_sources('vid'), [])


class UploadTests(SimpleTestCase):
    def test_upload_defaults_y_carpeta(self):
        with mock.patch.object(cu.cloudinary.uploader, 'upload',
                               return_value={'public_id': 'tenants/acme/gallery/x'}) as up:
            result = cu.upload_to_cloudinary(b'data', 'acme', 'gallery')
        self.assertEqual(result['public_id'], 'tenants/acme/gallery/x')
        opts = up.call_args.kwargs
        self.assertEqual(opts['folder'], 'tenants/acme/gallery')
        self.assertEqual(opts['quality'], 'auto')
        self.assertEqual(opts['width'], 2000)
        self.assertFalse(opts['use_filename'])
        self.assertNotIn('public_id', opts)

    def test_upload_filename_y_overrides(self):
        with mock.patch.object(cu.cloudinary.uploader, 'upload', return_value={}) as up:
            cu.upload_to_cloudinary(b'd', 'acme', 'branding', filename='logo', crop='fit')
        opts = up.call_args.kwargs
        self.assertEqual(opts['public_id'], 'logo')
        self.assertTrue(opts['use_filename'])
        self.assertEqual(opts['crop'], 'fit')

    def test_upload_error_del_sdk_se_propaga(self):
        with mock.patch.object(cu.cloudinary.uploader, 'upload', side_effect=RuntimeError('sdk')):
            with self.assertLogs(cu.logger, level='ERROR'):
                with self.assertRaisesMessage(RuntimeError, 'sdk'):
                    cu.upload_to_cloudinary(b'd', 'acme', 'gallery')

    def test_upload_tipo_invalido_no_llama_al_sdk(self):
        with mock.patch.object(cu.cloudinary.uploader, 'upload') as up:
            with self.assertRaises(ValueError):
                cu.upload_to_cloudinary(b'd', 'acme', 'nada')
        up.assert_not_called()

    def test_delete_vacio(self):
        with mock.patch.object(cu.cloudinary.uploader, 'destroy') as d:
            self.assertIsNone(cu.delete_from_cloudinary(''))
            self.assertIsNone(cu.delete_from_cloudinary(None))
        d.assert_not_called()

    def test_delete_ok(self):
        with mock.patch.object(cu.cloudinary.uploader, 'destroy', return_value={'result': 'ok'}) as d:
            with self.assertLogs(cu.logger, level='WARNING'):
                self.assertEqual(cu.delete_from_cloudinary('a/b', 'video'), {'result': 'ok'})
        d.assert_called_once_with('a/b', resource_type='video')

    def test_delete_error_se_propaga(self):
        with mock.patch.object(cu.cloudinary.uploader, 'destroy', side_effect=RuntimeError('x')):
            with self.assertLogs(cu.logger, level='ERROR'):
                with self.assertRaises(RuntimeError):
                    cu.delete_from_cloudinary('a/b')


def _png_bytes():
    from PIL import Image
    buf = io.BytesIO()
    Image.new('RGB', (2, 2), 'red').save(buf, 'PNG')
    return buf.getvalue()


class NamedBytes(io.BytesIO):
    def __init__(self, data, name, size=None):
        super().__init__(data)
        self.name = name
        if size is not None:
            self.size = size


class ValidateImageTests(SimpleTestCase):
    def test_png_valido_y_rebobinado(self):
        f = NamedBytes(_png_bytes(), 'a.png')
        self.assertEqual(cu.validate_image_file(f), (True, None))
        self.assertEqual(f.tell(), 0)

    def test_demasiado_grande(self):
        f = NamedBytes(_png_bytes(), 'a.png', size=11 * 1024 * 1024)
        ok, msg = cu.validate_image_file(f)
        self.assertFalse(ok)
        self.assertIn('muy grande', msg)

    def test_extension_no_permitida(self):
        ok, msg = cu.validate_image_file(NamedBytes(b'x', 'a.svg'))
        self.assertFalse(ok)
        self.assertIn('.svg', msg)

    def test_sin_extension(self):
        ok, msg = cu.validate_image_file(NamedBytes(b'x', 'archivo'))
        self.assertFalse(ok)
        self.assertIn('.?', msg)

    def test_contenido_falso(self):
        ok, msg = cu.validate_image_file(NamedBytes(b'esto no es imagen', 'a.jpg'))
        self.assertFalse(ok)
        self.assertEqual(msg, 'El archivo no es una imagen válida.')

    def test_formato_real_distinto_al_permitido(self):
        ok, msg = cu.validate_image_file(NamedBytes(_png_bytes(), 'a.png'), allowed_formats=['jpg'])
        self.assertFalse(ok)
        self.assertIn('no permitido', msg)

    def test_contenido_png_con_extension_jpg_pasa_si_png_permitido(self):
        # Extensión jpg permitida, pero el contenido es PNG y PNG también.
        self.assertEqual(cu.validate_image_file(NamedBytes(_png_bytes(), 'a.jpg')), (True, None))

    def test_contenido_png_no_permitido_si_solo_jpg(self):
        ok, msg = cu.validate_image_file(NamedBytes(_png_bytes(), 'a.jpg'), allowed_formats=['jpg'])
        self.assertFalse(ok)
        self.assertEqual(msg, 'El contenido del archivo no corresponde a una imagen permitida.')


class ValidateVideoTests(SimpleTestCase):
    def test_ok(self):
        f = SimpleNamespace(size=1024, name='v.mp4')
        self.assertEqual(cu.validate_video_file(f), (True, None))

    def test_grande(self):
        ok, msg = cu.validate_video_file(SimpleNamespace(size=300 * 1024 * 1024, name='v.mp4'))
        self.assertFalse(ok)
        self.assertIn('muy grande', msg)

    def test_formato(self):
        ok, msg = cu.validate_video_file(SimpleNamespace(size=1, name='v.flv'))
        self.assertFalse(ok)
        self.assertIn('.flv', msg)

    def test_sin_atributos(self):
        self.assertEqual(cu.validate_video_file(object()), (True, None))


class UsageTests(SimpleTestCase):
    def test_modulo_importa_cloudinary_api_por_si_solo(self):
        """Bug: get_tenant_usage usaba cloudinary.api sin importarlo."""
        import subprocess
        import sys
        from pathlib import Path

        code = (
            "import importlib.util, sys, cloudinary;"
            f"spec = importlib.util.spec_from_file_location('cu', r'{cu.__file__}');"
            "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m);"
            "sys.exit(0 if hasattr(cloudinary, 'api') else 1)"
        )
        proc = subprocess.run([sys.executable, '-I', '-c', code],
                              cwd=Path(cu.__file__).parent, capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())

    def test_usage_agrega_por_categoria(self):
        resources = [
            {'public_id': 'tenants/acme/gallery/a', 'bytes': 1024 * 1024},
            {'public_id': 'tenants/acme/gallery/b', 'bytes': 1024 * 1024},
            {'public_id': 'tenants/acme/branding/logo', 'bytes': 512},
            {'public_id': 'suelto', 'bytes': 1},
        ]
        with mock.patch.object(cu.cloudinary, 'api', create=True) as api:
            api.resources.return_value = {'resources': resources}
            out = cu.get_tenant_usage('acme')
        api.resources.assert_called_once_with(type='upload', prefix='tenants/acme/', max_results=500)
        self.assertEqual(out['count'], 4)
        self.assertEqual(out['breakdown']['gallery'], {'count': 2, 'size_bytes': 2 * 1024 * 1024})
        self.assertEqual(out['breakdown']['branding']['count'], 1)
        self.assertEqual(out['breakdown']['other']['count'], 1)
        self.assertEqual(out['size_mb'], 2.0)

    def test_usage_error_devuelve_estructura_vacia(self):
        with mock.patch.object(cu.cloudinary, 'api', create=True) as api:
            api.resources.side_effect = RuntimeError('sin red')
            with self.assertLogs(cu.logger, level='ERROR'):
                out = cu.get_tenant_usage('acme')
        self.assertEqual(out['count'], 0)
        self.assertEqual(out['error'], 'sin red')
        self.assertEqual(out['resources'], [])
