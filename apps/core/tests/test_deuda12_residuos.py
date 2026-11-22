"""
DEUDA-12 / BOLT-66: residuos de las rondas 10 y 11.

(a) el footer default muestra el año actual, no `2024` fijo;
(b) un plan sin temas ofrece `themes/default` en el onboarding (valor válido
    de `Client.THEME_CHOICES`, no el slug inválido `default`);
(c) guardia: sin `themes/andesscale` en el plan, el formulario no lo ofrece.
"""
from datetime import date
from types import SimpleNamespace as NS

from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from apps.orders.forms import ClientOnboardingForm
from apps.orders.models import Order, Plan
from apps.tenants.models import Client


class FooterDefaultYearTest(SimpleTestCase):
    def test_footer_default_shows_current_year(self):
        client = NS(name='X', settings=NS(company_name='Empresa SA'))
        html = render_to_string('components/slots/footer_default.html', {'client': client})
        self.assertIn('© %s' % date.today().year, html)
        self.assertNotIn('2024', html)


class OnboardingThemeFallbackTest(TestCase):
    def test_plan_without_themes_offers_valid_default_theme(self):
        plan = Plan.objects.create(name='Sin temas', slug='sin-temas', price=10000,
                                   available_themes=[])
        order = Order.objects.create(plan=plan, email='c@test.com', amount=10000, status='paid')
        order.generate_onboarding_token()

        response = self.client.get(reverse('onboarding', kwargs={'token': order.onboarding_token}),
                                   HTTP_HOST='localhost')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['available_themes'], ['themes/default'])
        valid = {value for value, _ in Client.THEME_CHOICES}
        choices = [value for value, _ in response.context['form'].fields['template'].choices]
        self.assertEqual(choices, ['themes/default'])
        self.assertTrue(set(choices) <= valid)


class OnboardingFormAndesscaleGuardTest(SimpleTestCase):
    def test_form_does_not_offer_andesscale_unless_plan_lists_it(self):
        form = ClientOnboardingForm(available_themes=['themes/default', 'themes/servelec'])
        choices = [value for value, _ in form.fields['template'].choices]
        self.assertNotIn('themes/andesscale', choices)
