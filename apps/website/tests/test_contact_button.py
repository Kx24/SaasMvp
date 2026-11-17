"""
BOLT-42 (COMP-03): el estado "Enviando..." se liga al envío real (submit),
no al clic del botón; si la validación HTML5 bloquea el envío, el botón
no debe quedar deshabilitado.
"""
import re

from django.conf import settings
from django.test import SimpleTestCase

TEMPLATES = [
    'components/contact_multistep.html',
    'partials/contact_form.html',
    'partials/contact_form_dynamic.html',
]
# Formularios que son un <form> nativo con estado Alpine ligado al evento submit.
FORM_TEMPLATES = TEMPLATES[1:]

CLICK_SETS_STATE = re.compile(r'@click(\.\w+)*\s*=\s*"[^"]*submitting\s*=\s*true')


def _read(rel):
    return (settings.BASE_DIR / 'templates' / rel).read_text(encoding='utf-8')


class ContactButtonStateTests(SimpleTestCase):
    def test_ningun_formulario_marca_enviando_en_el_clic(self):
        for rel in TEMPLATES:
            with self.subTest(template=rel):
                self.assertIsNone(CLICK_SETS_STATE.search(_read(rel)))

    def test_formularios_nativos_ligan_el_estado_al_submit(self):
        for rel in FORM_TEMPLATES:
            with self.subTest(template=rel):
                self.assertRegex(_read(rel), r'@submit(\.prevent)?\s*=\s*"[^"]*submitting\s*=\s*true')

    def test_formularios_nativos_se_recuperan_al_volver_a_la_pagina(self):
        for rel in FORM_TEMPLATES:
            with self.subTest(template=rel):
                self.assertRegex(_read(rel), r'@pageshow\.window\s*=\s*"submitting\s*=\s*false"')

    def test_multistep_resetea_el_estado_tras_error(self):
        src = _read('components/contact_multistep.html')
        self.assertIn('finally {', src)
        self.assertIn('this.submitting = false;', src)
