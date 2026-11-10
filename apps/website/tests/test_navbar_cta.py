"""
CTA del navbar compartido configurable por tenant (BOLT-07, del análisis
de diseño #RC-20).

templates/components/navbar.html (consumido por themes/default y
themes/electricidad) solo tenía links de auth — el CTA principal debe ser
configurable por tenant (texto + destino, incluyendo anclas '#contacto'),
no fijo por tema. Sin navbar_cta_text seteado, el navbar no cambia.
"""
from django.test import TestCase
from django.urls import reverse

from apps.tenants.models import Client, ClientSettings, Domain

CTA_TEXT = 'Reservar visita'
CTA_URL = '#contacto'


class NavbarCtaTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_obj = Client.objects.create(
            name='CTA Test Co', contact_email='contacto@ctatest.test',
            template='themes/default',
        )
        Domain.objects.create(
            client=cls.client_obj, domain='ctatest.test', domain_type='custom',
            is_primary=True, is_active=True, is_verified=True,
        )

    def _get_home(self):
        return self.client.get(reverse('home'), HTTP_HOST='ctatest.test')

    def test_configured_cta_renders_text_and_href(self):
        ClientSettings.objects.filter(client=self.client_obj).update(
            navbar_cta_text=CTA_TEXT, navbar_cta_url=CTA_URL,
        )
        response = self._get_home()
        self.assertContains(response, CTA_TEXT)
        self.assertContains(response, f'href="{CTA_URL}"')

    def test_cta_uses_brand_tokens_not_hardcoded_colors(self):
        ClientSettings.objects.filter(client=self.client_obj).update(
            navbar_cta_text=CTA_TEXT, navbar_cta_url=CTA_URL,
        )
        response = self._get_home()
        content = response.content.decode()
        cta_index = content.find(CTA_TEXT)
        # El botón (desktop) debe estilizarse con tokens del contrato, no hex
        surrounding = content[max(cta_index - 400, 0):cta_index]
        self.assertIn('var(--color-', surrounding)

    def test_unset_cta_renders_no_new_button(self):
        response = self._get_home()
        self.assertNotContains(response, CTA_TEXT)
        self.assertNotContains(response, 'navbar-cta')

    def test_cta_appears_in_desktop_and_mobile_menus(self):
        ClientSettings.objects.filter(client=self.client_obj).update(
            navbar_cta_text=CTA_TEXT, navbar_cta_url=CTA_URL,
        )
        response = self._get_home()
        # Una vez en el nav desktop y otra en el menú móvil
        self.assertContains(response, CTA_TEXT, count=2)
