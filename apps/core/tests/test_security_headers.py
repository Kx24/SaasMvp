"""
#SEC-02: CSP y Permissions-Policy. Los diccionarios reales viven en
config/settings/security_headers.py (import directo, sin subprocess --
a diferencia de production.py, este módulo no exige env vars).

Estos tests confirman dos cosas separadas:
1. El diccionario en sí tiene la forma esperada (hosts reales auditados
   en el código, no una lista inventada).
2. Con el middleware real activo, una respuesta real de Django lleva el
   header -- y /checkout/ (SDK de MercadoPago, ver el docstring del
   módulo) queda afuera a propósito.
"""
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.tenants.models import Client, Domain
from config.settings.security_headers import CONTENT_SECURITY_POLICY, PERMISSIONS_POLICY

CSP_MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware',
    'django_permissions_policy.PermissionsPolicyMiddleware',
    'apps.tenants.middleware.TenantMiddleware',
]


class SecurityHeadersDictTestCase(TestCase):
    def test_checkout_is_excluded_from_csp(self):
        self.assertIn('/checkout/', CONTENT_SECURITY_POLICY['EXCLUDE_URL_PREFIXES'])

    def test_known_external_hosts_are_allowlisted(self):
        directives = CONTENT_SECURITY_POLICY['DIRECTIVES']
        self.assertIn('https://fonts.googleapis.com', directives['style-src'])
        self.assertIn('https://fonts.gstatic.com', directives['font-src'])
        self.assertIn('https://cdn.jsdelivr.net', directives['script-src'])
        self.assertIn('https://unpkg.com', directives['script-src'])
        self.assertIn('https://res.cloudinary.com', directives['img-src'])

    def test_frame_ancestors_matches_x_frame_options_deny(self):
        self.assertEqual(CONTENT_SECURITY_POLICY['DIRECTIVES']['frame-ancestors'], ["'none'"])

    def test_unused_browser_features_are_disabled(self):
        for feature in ('camera', 'microphone', 'geolocation', 'usb'):
            self.assertEqual(PERMISSIONS_POLICY[feature], [])

    def test_payment_feature_is_not_restricted(self):
        """
        Checkout Bricks podría necesitar la Payment Request API en un
        iframe cross-origin -- no está en la lista curada, a propósito
        (ver docstring de security_headers.py).
        """
        self.assertNotIn('payment', PERMISSIONS_POLICY)


@override_settings(
    MIDDLEWARE=CSP_MIDDLEWARE,
    CONTENT_SECURITY_POLICY=CONTENT_SECURITY_POLICY,
    PERMISSIONS_POLICY=PERMISSIONS_POLICY,
)
class SecurityHeadersLiveResponseTestCase(TestCase):
    """
    Con el middleware real activo (no solo el diccionario) -- confirma
    que Django efectivamente manda el header en una respuesta real.
    """

    @classmethod
    def setUpTestData(cls):
        cls.client_obj = Client.objects.create(
            name='CSP Test Co', contact_email='contacto@csptest.test',
        )
        Domain.objects.create(
            client=cls.client_obj, domain='csptest.test', domain_type='custom',
            is_primary=True, is_active=True, is_verified=True,
        )

    def test_home_page_carries_csp_header(self):
        response = self.client.get(reverse('home'), HTTP_HOST='csptest.test')
        self.assertIn('Content-Security-Policy', response.headers)
        self.assertIn("frame-ancestors 'none'", response.headers['Content-Security-Policy'])

    def test_home_page_carries_permissions_policy_header(self):
        response = self.client.get(reverse('home'), HTTP_HOST='csptest.test')
        self.assertIn('Permissions-Policy', response.headers)
        self.assertIn('camera=()', response.headers['Permissions-Policy'])

    def test_checkout_path_has_no_csp_header(self):
        response = self.client.get('/checkout/', HTTP_HOST='csptest.test')
        self.assertNotIn('Content-Security-Policy', response.headers)
