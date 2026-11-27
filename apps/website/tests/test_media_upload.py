"""MOD-01 parte 1b: firma de subida, confirmación y alta de embeds (sin red)."""
from unittest import mock

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.website.models import MediaAsset

from .test_support_dashboard import PASSWORD, DashboardTestCase

SIGN = 'cloudinary.utils.api_sign_request'
RESOURCE = 'cloudinary.api.resource'
DELETE = 'apps.website.views.media.delete_from_cloudinary'
YT = 'dQw4w9WgXcQ'


def cloud_resource(public_id, **extra):
    data = {'public_id': public_id, 'bytes': 2048, 'width': 800, 'height': 600, 'format': 'jpg'}
    data.update(extra)
    return data


class MediaEndpointsBase(DashboardTestCase):
    slug = 'med-up'

    def setUp(self):
        super().setUp()
        cache.clear()
        self.folder = f'tenants/{self.slug}/media'

    def sign(self, **data):
        with mock.patch(SIGN, return_value='firma-falsa'):
            return self.post(reverse('media_upload_signature'), data)

    def confirm(self, public_id, resource=None):
        resource = resource if resource is not None else cloud_resource(public_id)
        with mock.patch(RESOURCE, return_value=resource), mock.patch(DELETE) as delete:
            response = self.post(reverse('media_upload_confirm'), {'public_id': public_id})
        return response, delete


class SignatureTests(MediaEndpointsBase):
    def test_returns_tenant_folder_and_server_public_id(self):
        response = self.sign()
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['folder'], self.folder)
        self.assertRegex(body['public_id'], r'^[0-9a-f]{32}$')
        self.assertEqual(body['signature'], 'firma-falsa')
        self.assertEqual(body['allowed_formats'], 'jpg,jpeg,png,webp,heic')
        self.assertIn('upload_url', body)
        self.assertNotIn('api_secret', body)

    def test_signs_only_server_chosen_params(self):
        with mock.patch(SIGN, return_value='x') as sign:
            self.post(reverse('media_upload_signature'),
                      {'folder': 'tenants/otro/media', 'public_id': 'elegido'})
        signed = sign.call_args.args[0]
        self.assertEqual(signed['folder'], self.folder)
        self.assertNotEqual(signed['public_id'], 'elegido')
        self.assertEqual(set(signed), {'folder', 'public_id', 'timestamp', 'allowed_formats'})

    def test_ignores_folder_sent_by_browser(self):
        body = self.sign(folder='tenants/otro/media').json()
        self.assertEqual(body['folder'], self.folder)

    def test_secret_never_in_response(self):
        with override_settings(), mock.patch('cloudinary.config') as config:
            config.return_value.api_secret = 'SUPER-SECRETO'
            config.return_value.api_key = 'k'
            config.return_value.cloud_name = 'c'
            response = self.sign()
        self.assertNotIn('SUPER-SECRETO', response.content.decode())

    def test_limit_reached_is_403(self):
        self.tenant.max_images = 1
        self.tenant.save(update_fields=['max_images'])
        MediaAsset.objects.create(client=self.tenant, kind='image', image='x/y')
        response = self.sign()
        self.assertEqual(response.status_code, 403)
        self.assertIn('error', response.json())

    def test_rate_limit_is_429(self):
        for _ in range(30):
            self.assertEqual(self.sign().status_code, 200)
        self.assertEqual(self.sign().status_code, 429)


class ConfirmTests(MediaEndpointsBase):
    def test_creates_asset_with_cloudinary_metadata(self):
        pid = f'{self.folder}/abc123'
        response, _ = self.confirm(pid, cloud_resource(pid, bytes=5000, width=1024, height=768,
                                                       format='png'))
        self.assertEqual(response.status_code, 201)
        asset = MediaAsset.objects.get(client=self.tenant)
        self.assertEqual(response.json()['id'], asset.id)
        self.assertEqual(response.json()['kind'], 'image')
        self.assertIn('thumbnail_url', response.json())
        self.assertEqual((asset.kind, asset.bytes, asset.width, asset.height, asset.format),
                         ('image', 5000, 1024, 768, 'png'))
        self.assertEqual(asset.uploaded_by, self.owner)
        self.assertIn(pid, str(asset.image))

    def test_rejects_other_tenant_folder(self):
        pid = f'tenants/{self.other.slug}/media/abc'
        with mock.patch(RESOURCE) as resource, mock.patch(DELETE) as delete:
            response = self.post(reverse('media_upload_confirm'), {'public_id': pid})
        self.assertEqual(response.status_code, 400)
        resource.assert_not_called()
        delete.assert_not_called()
        self.assertFalse(MediaAsset.objects.exists())

    def test_rejects_folder_prefix_lookalike(self):
        pid = f'{self.folder}-evil/abc'
        response, _ = self.confirm(pid)
        self.assertEqual(response.status_code, 400)

    def test_missing_in_cloudinary_is_400(self):
        pid = f'{self.folder}/nada'
        with mock.patch(RESOURCE, side_effect=Exception('Resource not found')):
            response = self.post(reverse('media_upload_confirm'), {'public_id': pid})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(MediaAsset.objects.exists())

    def test_rejects_and_deletes_oversize(self):
        pid = f'{self.folder}/grande'
        response, delete = self.confirm(pid, cloud_resource(pid, bytes=10 * 1024 * 1024 + 1))
        self.assertEqual(response.status_code, 400)
        self.assertIn('10', response.json()['error'])
        delete.assert_called_once_with(pid)
        self.assertFalse(MediaAsset.objects.exists())

    def test_accepts_exactly_the_cap(self):
        pid = f'{self.folder}/justo'
        response, _ = self.confirm(pid, cloud_resource(pid, bytes=10 * 1024 * 1024))
        self.assertEqual(response.status_code, 201)

    def test_rejects_and_deletes_disallowed_format(self):
        pid = f'{self.folder}/raro'
        response, delete = self.confirm(pid, cloud_resource(pid, format='gif'))
        self.assertEqual(response.status_code, 400)
        delete.assert_called_once_with(pid)
        self.assertFalse(MediaAsset.objects.exists())

    def test_is_idempotent(self):
        pid = f'{self.folder}/dup'
        first, _ = self.confirm(pid)
        second, _ = self.confirm(pid)
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json()['id'], second.json()['id'])
        self.assertEqual(MediaAsset.objects.filter(client=self.tenant).count(), 1)

    def test_limit_reached_between_sign_and_confirm(self):
        self.tenant.max_images = 1
        self.tenant.save(update_fields=['max_images'])
        MediaAsset.objects.create(client=self.tenant, kind='image', image='x/y')
        pid = f'{self.folder}/tarde'
        response, delete = self.confirm(pid)
        self.assertEqual(response.status_code, 403)
        delete.assert_called_once_with(pid)
        self.assertEqual(MediaAsset.objects.filter(client=self.tenant).count(), 1)


class EmbedTests(MediaEndpointsBase):
    def add(self, url):
        return self.post(reverse('media_embed_add'), {'url': url})

    def test_creates_embed(self):
        response = self.add(f'https://youtu.be/{YT}')
        self.assertEqual(response.status_code, 201)
        body = response.json()
        asset = MediaAsset.objects.get(client=self.tenant)
        self.assertEqual((asset.kind, asset.provider, asset.video_id), ('embed', 'youtube', YT))
        self.assertEqual(body['id'], asset.id)
        self.assertEqual(body['kind'], 'embed')
        self.assertIn(YT, body['embed_url'])
        self.assertIn('thumbnail_url', body)

    def test_rejects_invalid_url(self):
        response = self.add('https://evil.test/watch?v=' + YT)
        self.assertEqual(response.status_code, 400)
        self.assertIn('YouTube', response.json()['error'])
        self.assertFalse(MediaAsset.objects.exists())

    def test_does_not_duplicate(self):
        first = self.add(f'https://youtu.be/{YT}')
        second = self.add(f'https://www.youtube.com/watch?v={YT}')
        self.assertEqual(first.json()['id'], second.json()['id'])
        self.assertEqual(MediaAsset.objects.filter(client=self.tenant).count(), 1)

    def test_same_video_allowed_in_other_tenant(self):
        MediaAsset.objects.create(client=self.other, kind='embed', provider='youtube', video_id=YT)
        self.assertEqual(self.add(f'https://youtu.be/{YT}').status_code, 201)

    @override_settings(MEDIA_MAX_EMBEDS=1)
    def test_respects_cap(self):
        MediaAsset.objects.create(client=self.tenant, kind='embed', provider='youtube',
                                  video_id='AAAAAAAAAAA')
        response = self.add(f'https://youtu.be/{YT}')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(MediaAsset.objects.filter(client=self.tenant).count(), 1)


class AccessTests(MediaEndpointsBase):
    URLS = ('media_upload_signature', 'media_upload_confirm', 'media_embed_add')

    def test_anonymous_redirected_to_login(self):
        self.client.logout()
        for name in self.URLS:
            with self.subTest(name=name):
                response = self.post(reverse(name))
                self.assertEqual(response.status_code, 302)
                self.assertIn('login', response['Location'])

    def test_user_of_other_tenant_rejected(self):
        outsider = User.objects.create_user(username='intruso', password=PASSWORD)
        UserProfile.objects.filter(user=outsider).update(client=self.other, role='owner')
        self.client.force_login(outsider)
        for name in self.URLS:
            with self.subTest(name=name):
                response = self.post(reverse(name), {'url': f'https://youtu.be/{YT}'})
                self.assertIn(response.status_code, (302, 403))
        self.assertFalse(MediaAsset.objects.exists())

    def test_role_without_edit_content_rejected(self):
        viewer = User.objects.create_user(username='lector', password=PASSWORD)
        UserProfile.objects.filter(user=viewer).update(client=self.tenant, role='viewer')
        self.client.force_login(viewer)
        for name in self.URLS:
            with self.subTest(name=name):
                response = self.post(reverse(name), {'url': f'https://youtu.be/{YT}'})
                self.assertEqual(response.status_code, 403)
        self.assertFalse(MediaAsset.objects.exists())

    def test_get_is_405(self):
        for name in self.URLS:
            with self.subTest(name=name):
                self.assertEqual(self.get(reverse(name)).status_code, 405)

    def test_csrf_is_enforced(self):
        from django.test import Client as TestClient
        strict = TestClient(enforce_csrf_checks=True)
        strict.force_login(self.owner)
        response = strict.post(reverse('media_embed_add'), {'url': f'https://youtu.be/{YT}'},
                               HTTP_HOST=self.host)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(MediaAsset.objects.exists())
