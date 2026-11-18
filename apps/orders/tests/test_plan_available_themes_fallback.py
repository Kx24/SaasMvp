"""DEUDA-13: Plan.get_available_themes_list nunca devuelve slugs fuera de
Client.THEME_CHOICES (el fallback antiguo era el slug inválido 'default')."""
from django.test import SimpleTestCase

from apps.orders.models import Plan

DEFAULT = ['themes/default']


class PlanAvailableThemesFallbackTests(SimpleTestCase):

    def _themes(self, value):
        return Plan(available_themes=value).get_available_themes_list()

    def test_nulo_string_o_dict_usan_default(self):
        for value in (None, 'themes/default', {'a': 1}):
            with self.subTest(value=value):
                self.assertEqual(self._themes(value), DEFAULT)

    def test_lista_valida_se_conserva(self):
        self.assertEqual(
            self._themes(['themes/default', 'themes/servelec']),
            ['themes/default', 'themes/servelec'],
        )

    def test_filtra_temas_inexistentes(self):
        self.assertEqual(self._themes(['themes/default', 'themes/borrado']), DEFAULT)

    def test_solo_invalidos_usa_default(self):
        self.assertEqual(self._themes(['default', 'themes/borrado']), DEFAULT)

    def test_lista_vacia_usa_default(self):
        self.assertEqual(self._themes([]), DEFAULT)
