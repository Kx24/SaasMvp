"""
#PREV-01: process_onboarding usaba BASE_DOMAIN para el subdominio del
tenant. En producción BASE_DOMAIN="onrender.com" (dominio de la
plataforma, no de este servicio) -- todo cliente que pagaba terminaba
con un Domain primario en <slug>.onrender.com, inalcanzable. Fix:
PREVIEW_DOMAIN, separado de BASE_DOMAIN; si no está configurado, no se
crea un Domain roto.
"""
from django.test import TestCase, override_settings

from apps.orders.models import Order, Plan
from apps.orders.views_onboarding import process_onboarding
from apps.tenants.models import Domain


class PreviewDomainOnboardingTestCase(TestCase):
    def setUp(self):
        self.plan = Plan.objects.create(
            name='Plan Test', slug='plan-test', price=10000,
        )
        self.order = Order.objects.create(
            plan=self.plan, email='comprador@test.com', amount=10000,
            status='paid',
        )
        self.onboarding_data = {
            'company_name': 'Empresa Test',
            'slug': 'empresa-test',
            'template': 'default',
        }

    @override_settings(BASE_DOMAIN='onrender.com', PREVIEW_DOMAIN='andesscale.com')
    def test_domain_uses_preview_domain_not_base_domain(self):
        client, _user = process_onboarding(self.order, self.onboarding_data)

        domain = Domain.objects.get(client=client)
        self.assertEqual(domain.domain, 'empresa-test.andesscale.com')
        self.assertTrue(domain.is_primary)

    @override_settings(BASE_DOMAIN='onrender.com', PREVIEW_DOMAIN=None)
    def test_no_preview_domain_configured_does_not_create_broken_domain(self):
        client, _user = process_onboarding(self.order, self.onboarding_data)

        self.assertFalse(Domain.objects.filter(client=client).exists())
