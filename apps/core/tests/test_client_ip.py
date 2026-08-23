"""
Tests de resolución de IP confiable detrás del proxy de Render.

#MED-05 (a) / BOLT-03: get_client_ip() confiaba en el PRIMER valor de
X-Forwarded-For — un atacante que manda "X-Forwarded-For: 1.2.3.4" evade
el rate limit por IP eligiendo una IP distinta por request. Render (único
proxy real delante de la app) APPENDEA la IP del cliente que se le conectó
al final del header, así que el único valor confiable es el que está a
TRUSTED_PROXY_COUNT posiciones desde la derecha (default 1 = el último).
"""
from django.test import RequestFactory, TestCase, override_settings

from apps.core.rate_limit import RateLimiter, get_client_ip

SPOOFED = '1.2.3.4'
REAL_CLIENT = '5.6.7.8'
RENDER_ADDR = '10.0.0.1'


class GetClientIpTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _request(self, xff=None, remote_addr=RENDER_ADDR):
        headers = {'REMOTE_ADDR': remote_addr}
        if xff is not None:
            headers['HTTP_X_FORWARDED_FOR'] = xff
        return self.factory.get('/', **headers)

    def test_spoofed_xff_chain_does_not_change_effective_ip(self):
        """
        El atacante controla todos los valores del XFF menos el último
        (que lo escribe Render). La IP efectiva debe ser la del último
        salto confiable, no la primera de la cadena.
        """
        request = self._request(xff=f'{SPOOFED}, {REAL_CLIENT}')
        self.assertEqual(get_client_ip(request), REAL_CLIENT)

    def test_long_spoofed_chain_still_resolves_last_hop(self):
        request = self._request(xff=f'{SPOOFED}, 9.9.9.9, 8.8.8.8, {REAL_CLIENT}')
        self.assertEqual(get_client_ip(request), REAL_CLIENT)

    def test_without_xff_falls_back_to_remote_addr(self):
        request = self._request(xff=None)
        self.assertEqual(get_client_ip(request), RENDER_ADDR)

    @override_settings(TRUSTED_PROXY_COUNT=2)
    def test_trusted_proxy_count_is_configurable(self):
        # Con 2 proxies confiables (p. ej. CDN delante de Render), el valor
        # confiable es el penúltimo: el último lo escribió el 2º proxy sobre
        # la IP del 1º, y el 1º escribió la IP real del cliente.
        request = self._request(xff=f'{SPOOFED}, {REAL_CLIENT}, 172.16.0.1')
        self.assertEqual(get_client_ip(request), REAL_CLIENT)

    def test_xff_shorter_than_trusted_count_does_not_crash(self):
        with override_settings(TRUSTED_PROXY_COUNT=5):
            request = self._request(xff=REAL_CLIENT)
            self.assertEqual(get_client_ip(request), REAL_CLIENT)


class CanonicalFunctionConsumersTestCase(TestCase):
    """Ambos consumidores (contacto y checkout) deben usar la función canónica."""

    def test_website_views_uses_canonical(self):
        from apps.website import views as website_views
        self.assertIs(website_views.get_client_ip, get_client_ip)

    def test_orders_views_uses_canonical(self):
        from apps.orders import views as orders_views
        self.assertIs(orders_views.get_client_ip, get_client_ip)

    def test_rate_limiter_resolves_last_hop_ip(self):
        # La 3ª copia de la lógica vivía en RateLimiter._get_ip — la key del
        # limiter debe construirse con la IP del último salto confiable.
        factory = RequestFactory()
        request = factory.get(
            '/',
            REMOTE_ADDR=RENDER_ADDR,
            HTTP_X_FORWARDED_FOR=f'{SPOOFED}, {REAL_CLIENT}',
        )
        limiter = RateLimiter(request, scope='test-bolt03')
        self.assertIn(f':{REAL_CLIENT}', limiter.key)
        limiter.reset()
