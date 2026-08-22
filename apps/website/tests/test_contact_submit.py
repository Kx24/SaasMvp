"""
Tests de apps/website/views.py::contact_submit.

Hallazgo (#TOOL-01, al construir el smoke E2E): `partials/contact_form.html`
-- usado por servelec, themes/default y themes/electricidad -- no manda
`intent` ni `form_source`, dos ChoiceField requeridos por ContactForm.
Toda esa plantilla envía un POST nativo (`$el.submit()`, sin fetch/JS que
complete esos campos, a diferencia de `components/contact_multistep.html`
que sí los agrega). Resultado: el formulario de contacto SIEMPRE
devuelve 400 en cualquier tenant que use esa plantilla -- servelec
(producción real) incluido. Nadie podía enviar un mensaje desde ahí.
"""
from django.test import TestCase
from django.urls import reverse

from apps.tenants.models import Client, Domain
from apps.website.models import ContactSubmission


class ContactFormSimplePartialSubmissionTestCase(TestCase):
    """
    Reproduce exactamente el POST que hoy manda
    templates/partials/contact_form.html: name/email/phone/company/
    subject/message, SIN intent ni form_source.
    """

    @classmethod
    def setUpTestData(cls):
        cls.client_obj = Client.objects.create(
            name='Servelec Test', contact_email='contacto@servelec.test',
        )
        Domain.objects.create(
            client=cls.client_obj, domain='servelec.test', domain_type='custom',
            is_primary=True, is_active=True, is_verified=True,
        )

    def _post(self, data):
        return self.client.post(
            reverse('contact_submit'), data=data, HTTP_HOST='servelec.test',
        )

    def test_form_as_rendered_by_simple_partial_succeeds(self):
        """
        Estos son EXACTAMENTE los campos que
        templates/partials/contact_form.html envía en su <form> --
        name, email, phone, company, subject, message, más los hidden
        intent/form_source agregados por el fix. Antes del fix, faltaban
        intent/form_source, ContactForm.is_valid() era False y la vista
        devolvía 400 sin crear ningún ContactSubmission (rojo confirmado).

        Es un POST nativo sin headers de AJAX/HTMX, así que la vista
        usa el patrón clásico Post/Redirect/Get (redirect a home con un
        mensaje de éxito vía el framework de messages) -- no JSON. Eso
        es el comportamiento normal para este flujo, no parte del bug.
        """
        response = self._post({
            'name': 'Juan Pérez',
            'email': 'juan@test.com',
            'phone': '+56912345678',
            'company': 'Mi Empresa',
            'subject': 'Consulta general',
            'message': 'Hola, quisiera más información.',
            'intent': 'general',
            'form_source': 'page',
        })

        self.assertEqual(
            response.status_code, 302,
            f"content: {response.content}",
        )
        self.assertEqual(response.url, '/')
        self.assertEqual(ContactSubmission.objects.count(), 1)

        submission = ContactSubmission.objects.get()
        self.assertEqual(submission.client, self.client_obj)
        self.assertEqual(submission.email, 'juan@test.com')
        self.assertEqual(submission.status, 'new')

    def test_rendered_home_page_includes_intent_and_form_source_fields(self):
        """
        Ancla el fix a la plantilla real (no solo al POST hecho a mano
        arriba): si alguien vuelve a borrar los hidden de
        partials/contact_form.html, este test lo detecta sin depender de
        que el test anterior adivine bien los campos actuales.
        """
        response = self.client.get('/', HTTP_HOST='servelec.test')

        self.assertContains(response, 'name="intent" value="general"')
        self.assertContains(response, 'name="form_source" value="page"')
