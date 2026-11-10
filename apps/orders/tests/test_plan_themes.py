"""
#DEUDA-03: Plan.available_themes debe ofrecer solo temas que existen de verdad.

Bug real encontrado en apps/orders/views_onboarding.py::process_onboarding:
Client.objects.create(template=data['template']) no valida contra
Client.THEME_CHOICES (no llama full_clean()). El Plan Pro (destacado,
$250.000, is_active=True) ofrecia 'electricidad'/'industrial' en
available_themes -- ninguno de los dos resolvia a una carpeta real, asi
que un cliente que pagaba y elegia esas opciones terminaba con un sitio
roto (TenantTemplateLoader cae al fallback global generico).
"""
import io

from django.core.management import call_command
from django.test import TestCase

from apps.orders.forms import ClientOnboardingForm
from apps.orders.models import Plan
from apps.tenants.models import Client


class PlanAvailableThemesConsistencyTestCase(TestCase):

    def test_setup_plans_command_only_offers_real_themes(self):
        # stdout=StringIO: el comando imprime un emoji que revienta cp1252 en Windows.
        call_command('setup_plans', stdout=io.StringIO())
        valid_values = dict(Client.THEME_CHOICES)
        broken = []
        for plan in Plan.objects.all():
            for theme in plan.get_available_themes_list():
                if theme not in valid_values:
                    broken.append((plan.slug, theme))
        self.assertEqual(
            broken, [],
            f"Plan(es) ofreciendo temas sin carpeta real: {broken}"
        )

    def test_onboarding_form_labels_match_real_theme_choices(self):
        """Las opciones del form de onboarding deben mostrar un label real,
        no el fallback generico theme_slug.title() (senal de que el slug
        no esta en el diccionario de labels del form)."""
        real_values = [value for value, _label in Client.THEME_CHOICES]
        form = ClientOnboardingForm(available_themes=real_values)
        rendered_labels = dict(form.fields['template'].choices)
        for value in real_values:
            self.assertNotEqual(
                rendered_labels[value], value.title(),
                f"'{value}' cae al label generico — falta en theme_labels de ClientOnboardingForm"
            )
