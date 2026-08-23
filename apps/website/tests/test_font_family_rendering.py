"""
#AUD-11 Paso 3: el <link> de Google Fonts estaba fijo a Inter en la
mayoría de temas aunque ClientSettings.font_family existiera -- el campo
no estaba conectado a nada real. Este test reproduce el home real de un
tenant y confirma que el <link> carga la fuente elegida, no siempre Inter.
"""
from django.test import TestCase
from django.urls import reverse

from apps.tenants.models import Client, Domain


class HomePageGoogleFontsLinkTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_obj = Client.objects.create(
            name='Font Test Co', contact_email='contacto@fonttest.test',
        )
        Domain.objects.create(
            client=cls.client_obj, domain='fonttest.test', domain_type='custom',
            is_primary=True, is_active=True, is_verified=True,
        )

    def _get_home(self):
        return self.client.get(reverse('home'), HTTP_HOST='fonttest.test')

    def test_default_font_family_loads_inter(self):
        response = self._get_home()
        self.assertContains(response, 'family=Inter:wght@400;500;600;700')

    def test_changing_font_family_changes_google_fonts_link(self):
        settings_obj = self.client_obj.settings
        settings_obj.font_family = 'Outfit'
        settings_obj.save(update_fields=['font_family'])

        response = self._get_home()
        self.assertContains(response, 'family=Outfit:wght@400;500;600;700')
        self.assertNotContains(response, 'family=Inter:wght@400;500;600;700')
