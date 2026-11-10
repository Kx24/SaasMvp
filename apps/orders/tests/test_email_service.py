"""
Tests de EmailService: URL del sitio del tenant.

#AUD-07: send_welcome/send_site_ready hardcodeaban
f"https://{client.slug}.andesscale.cl", ignorando BASE_DOMAIN y
dominios personalizados -- el link del correo apuntaba al dominio
equivocado para cualquier tenant con dominio propio (ej. Rancho
Cachimba con ranchocachimba.cl).
"""
from django.contrib.auth.models import User
from django.core import mail
from django.template.loader import render_to_string
from django.test import TestCase, override_settings

from apps.orders.models import Order, Plan
from apps.orders.services.email_service import EmailService
from apps.tenants.models import Client, Domain


class EmailServiceSiteUrlTestCase(TestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(
            name='Rancho Cachimba',
            slug='rancho-cachimba',
        )

    def test_site_url_uses_primary_domain_when_present(self):
        Domain.objects.create(
            client=self.client_obj,
            domain='ranchocachimba.cl',
            domain_type='custom',
            is_primary=True,
            is_active=True,
            is_verified=True,
        )

        url = EmailService()._site_url(self.client_obj)

        self.assertEqual(url, 'https://ranchocachimba.cl')

    @override_settings(BASE_DOMAIN='andesscale.test')
    def test_site_url_falls_back_to_base_domain_without_domain_record(self):
        url = EmailService()._site_url(self.client_obj)

        self.assertEqual(url, 'https://rancho-cachimba.andesscale.test')


class EmailServiceTemplatesRenderTestCase(TestCase):
    """
    #AUD-07: los 6 emails transaccionales deben renderizar sin errores con
    contexto real. Un typo de variable en un template no se nota si los
    tests solo mockean _send_email; acá se renderiza de verdad.
    """

    def setUp(self):
        self.plan = Plan.objects.create(
            name='Plan Test', slug='plan-test', price=10000,
        )
        self.client_obj = Client.objects.create(
            name='Empresa Test', slug='empresa-test',
        )
        self.client_obj.settings.contact_email = 'contacto@empresa-test.cl'
        self.client_obj.settings.save()
        self.user = User.objects.create_user(
            username='owner', email='owner@test.com',
        )

    def _paid_order(self):
        order = Order.objects.create(
            plan=self.plan, email='comprador@test.com', amount=10000,
            status='paid',
        )
        order.generate_onboarding_token()
        return order

    def test_payment_success_renders(self):
        self.assertTrue(EmailService().send_payment_success(self._paid_order()))

    def test_welcome_renders(self):
        self.assertTrue(
            EmailService().send_welcome(self.client_obj, self.user, 'sometoken')
        )

    def test_site_ready_renders(self):
        self.assertTrue(EmailService().send_site_ready(self.client_obj, self.user))

    def test_token_expiring_renders(self):
        self.assertTrue(
            EmailService().send_token_expiring(self._paid_order(), hours_remaining=24)
        )

    def test_set_password_renders(self):
        self.assertTrue(EmailService().send_set_password(self.user, 'sometoken'))

    def test_contact_received_renders(self):
        self.assertTrue(EmailService().send_contact_received(self.client_obj, {
            'name': 'Comprador Test',
            'email': 'comprador@test.com',
            'message': 'Hola, tengo una consulta.',
        }))


class EmailServicePlainTextTestCase(TestCase):
    """
    #MED-04 (mitad automatizable, BOLT-09): `strip_tags()` no es
    consciente de `<style>` -- deja el CSS completo de base_email.html
    (150+ líneas: "mso-table-lspace", "-webkit-text-size-adjust", etc.)
    como texto visible al principio de CADA email de texto plano, antes
    de cualquier contenido real. Verificado en vivo con un render directo
    antes de este fix. `apps/tenants/services/email_dispatcher.py` ya
    resuelve esto bien (renderiza un `.txt` dedicado) -- este test exige
    el mismo patrón acá.
    """

    def setUp(self):
        self.plan = Plan.objects.create(
            name='Plan Test', slug='plan-test-txt', price=10000,
        )
        self.client_obj = Client.objects.create(
            name='Empresa Test', slug='empresa-test-txt',
        )
        self.client_obj.settings.contact_email = 'contacto@empresa-test.cl'
        self.client_obj.settings.save()
        self.user = User.objects.create_user(
            username='owner-txt', email='owner-txt@test.com',
        )

    def _paid_order(self):
        order = Order.objects.create(
            plan=self.plan, email='comprador-txt@test.com', amount=10000,
            status='paid',
        )
        order.generate_onboarding_token()
        return order

    def _assert_plain_text_clean(self):
        self.assertTrue(mail.outbox)
        body = mail.outbox[-1].body
        self.assertNotIn('mso-table-lspace', body)
        self.assertNotIn('-webkit-text-size-adjust', body)
        self.assertNotIn('font-family:', body)

    def test_payment_success_plain_text_has_no_css(self):
        EmailService().send_payment_success(self._paid_order())
        self._assert_plain_text_clean()

    def test_welcome_plain_text_has_no_css(self):
        EmailService().send_welcome(self.client_obj, self.user, 'sometoken')
        self._assert_plain_text_clean()

    def test_site_ready_plain_text_has_no_css(self):
        EmailService().send_site_ready(self.client_obj, self.user)
        self._assert_plain_text_clean()

    def test_token_expiring_plain_text_has_no_css(self):
        EmailService().send_token_expiring(self._paid_order(), hours_remaining=24)
        self._assert_plain_text_clean()

    def test_set_password_plain_text_has_no_css(self):
        EmailService().send_set_password(self.user, 'sometoken')
        self._assert_plain_text_clean()

    def test_contact_received_plain_text_has_no_css(self):
        EmailService().send_contact_received(self.client_obj, {
            'name': 'Comprador Test',
            'email': 'comprador-txt@test.com',
            'message': 'Hola, tengo una consulta.',
        })
        self._assert_plain_text_clean()


class EmailFooterLinkTestCase(TestCase):
    """
    #MED-04 (BOLT-09): el link de soporte del footer de base_email.html
    apuntaba a `/cdn-cgi/l/email-protection#<hex>` -- artefacto de
    ofuscación de Cloudflare que sin su JS del lado del navegador (nunca
    corre dentro de un cliente de correo) es un link muerto en el 100%
    de los casos. Verificado en vivo antes de este fix.
    """

    def test_footer_mailto_link_is_not_broken(self):
        html = render_to_string('emails/payment_success.html', {
            'order': type('O', (), {'order_number': '1', 'amount': 1, 'email': 'a@b.cl'})(),
            'plan': type('P', (), {'name': 'x'})(),
            'onboarding_url': 'https://example.test/x',
            'token_expires_hours': 1,
            'support_email': 'soporte@andesscale.cl',
            'company_name': 'Andesscale',
            'base_url': 'https://example.test',
        })
        self.assertNotIn('cdn-cgi', html)
        self.assertIn('mailto:soporte@andesscale.cl', html)
