"""MOD-01 parte 1a: modelo MediaAsset, parser de embeds y módulo `media`."""
from unittest import mock

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase

from apps.tenants.models import Client
from apps.tenants.modules import usage_for
from apps.website.media import parse_video_url
from apps.website.models import MediaAsset

YT = 'dQw4w9WgXcQ'


class ParseVideoUrlTests(SimpleTestCase):
    def test_youtube_forms(self):
        urls = [
            f'https://www.youtube.com/watch?v={YT}',
            f'https://youtube.com/watch?v={YT}&t=30s',
            f'https://m.youtube.com/watch?feature=share&v={YT}',
            f'https://youtu.be/{YT}',
            f'https://youtu.be/{YT}?si=abc123',
            f'https://www.youtube.com/shorts/{YT}',
            f'https://youtube.com/embed/{YT}',
            f'http://www.youtube.com/embed/{YT}?rel=0',
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(parse_video_url(url), ('youtube', YT))

    def test_vimeo_forms(self):
        for url in ('https://vimeo.com/123456789', 'https://www.vimeo.com/123456789?x=1',
                    'https://player.vimeo.com/video/123456789'):
            with self.subTest(url=url):
                self.assertEqual(parse_video_url(url), ('vimeo', '123456789'))

    def test_rejects_invalid(self):
        bad = [
            f'https://evil.test/watch?v={YT}',
            f'https://youtube.com.evil.test/watch?v={YT}',
            f'https://evil.test/youtube.com/watch?v={YT}',
            f'javascript:alert(1)//youtube.com/watch?v={YT}',
            f'ftp://youtu.be/{YT}',
            'https://youtu.be/corto',
            'https://youtu.be/dQw4w9WgXcQxx',
            'https://youtu.be/dQw4w9WgX!Q',
            'https://vimeo.com/abc',
            'https://vimeo.com/',
            'esto no es una url',
            '',
        ]
        for url in bad:
            with self.subTest(url=url):
                with self.assertRaises(ValidationError):
                    parse_video_url(url)

    def test_rejects_non_string(self):
        with self.assertRaises(ValidationError):
            parse_video_url(None)


class MediaAssetModelTests(TestCase):
    def setUp(self):
        self.client_a = Client.objects.create(name='A', slug='media-a')
        self.client_b = Client.objects.create(name='B', slug='media-b')

    def test_clean_rejects_image_without_file(self):
        with self.assertRaises(ValidationError):
            MediaAsset(client=self.client_a, kind='image').clean()

    def test_clean_rejects_image_with_embed_data(self):
        asset = MediaAsset(client=self.client_a, kind='image', image='x',
                           provider='youtube', video_id=YT)
        with self.assertRaises(ValidationError):
            asset.clean()

    def test_clean_rejects_embed_without_video_id(self):
        with self.assertRaises(ValidationError):
            MediaAsset(client=self.client_a, kind='embed', provider='youtube').clean()

    def test_clean_rejects_embed_with_image(self):
        asset = MediaAsset(client=self.client_a, kind='embed', provider='youtube',
                           video_id=YT, image='x')
        with self.assertRaises(ValidationError):
            asset.clean()

    def test_clean_accepts_valid(self):
        MediaAsset(client=self.client_a, kind='image', image='x').clean()
        MediaAsset(client=self.client_a, kind='embed', provider='vimeo',
                   video_id='123').clean()

    def test_embed_and_thumbnail_urls(self):
        yt = MediaAsset(client=self.client_a, kind='embed', provider='youtube', video_id=YT)
        vm = MediaAsset(client=self.client_a, kind='embed', provider='vimeo', video_id='123')
        self.assertEqual(yt.embed_url(), f'https://www.youtube-nocookie.com/embed/{YT}')
        self.assertEqual(vm.embed_url(), 'https://player.vimeo.com/video/123?dnt=1')
        self.assertEqual(yt.thumbnail_url(), f'https://img.youtube.com/vi/{YT}/hqdefault.jpg')
        self.assertIsNone(vm.thumbnail_url())

    def test_image_thumbnail_uses_cloudinary_helper(self):
        asset = MediaAsset(client=self.client_a, kind='image', image='tenants/x/media/a')
        with mock.patch('apps.core.cloudinary_utils.get_cloudinary_url',
                        return_value='https://cdn.test/t.jpg') as m:
            self.assertEqual(asset.thumbnail_url(), 'https://cdn.test/t.jpg')
        self.assertEqual(m.call_args.args[1], 'thumbnail')


class MediaModuleUsageTests(TestCase):
    def test_usage_counts_only_images_of_the_client(self):
        a = Client.objects.create(name='A', slug='usage-a')
        b = Client.objects.create(name='B', slug='usage-b')
        MediaAsset.objects.create(client=a, kind='image', image='a1')
        MediaAsset.objects.create(client=a, kind='image', image='a2')
        MediaAsset.objects.create(client=a, kind='embed', provider='youtube', video_id=YT)
        MediaAsset.objects.create(client=b, kind='image', image='b1')
        self.assertEqual(usage_for(a, 'media'), 2)
        self.assertEqual(usage_for(b, 'media'), 1)
