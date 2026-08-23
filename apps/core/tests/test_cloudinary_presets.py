"""
#AUD-10 (absorbe el pendiente de #DEUDA-01): CLOUDINARY_PRESETS tuvo una
clave duplicada en el pasado -- un dict literal de Python no la rechaza,
simplemente se queda con el último valor en silencio (ni ImportError ni
excepción; el preset "perdido" desaparece sin aviso). Para cuando ya se
evaluó el literal, esa información ya se perdió -- inspeccionar el dict
resultante en runtime no puede detectar una clave duplicada reintroducida,
así que este test parsea el *código fuente* con `ast`, igual que hace
ruff (regla F601, ya seleccionada en ruff.toml) -- pero como test propio
del proyecto, corre con `manage.py test` sin depender de que alguien
acuerde de correr ruff en ese archivo puntual.
"""
import ast
from collections import Counter
from pathlib import Path

from django.test import SimpleTestCase

CLOUDINARY_UTILS_PATH = (
    Path(__file__).resolve().parent.parent / 'cloudinary_utils.py'
)

DICTS_TO_CHECK = ('CLOUDINARY_PRESETS', 'VIDEO_PRESETS')


def _duplicate_keys_by_dict_name(source: str) -> dict:
    tree = ast.parse(source)
    duplicates = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Dict):
            continue

        target_names = {
            target.id for target in node.targets if isinstance(target, ast.Name)
        }
        matched = target_names & set(DICTS_TO_CHECK)
        if not matched:
            continue

        key_literals = [
            key.value for key in node.value.keys
            if isinstance(key, ast.Constant)
        ]
        counts = Counter(key_literals)
        repeated = [key for key, count in counts.items() if count > 1]
        if repeated:
            duplicates[matched.pop()] = repeated

    return duplicates


class CloudinaryPresetsNoDuplicateKeysTestCase(SimpleTestCase):
    def test_no_dict_has_repeated_top_level_keys(self):
        source = CLOUDINARY_UTILS_PATH.read_text(encoding='utf-8')
        duplicates = _duplicate_keys_by_dict_name(source)

        self.assertFalse(
            duplicates,
            f"Clave(s) duplicada(s) en {CLOUDINARY_UTILS_PATH.name}: {duplicates} "
            "-- un preset se pisa en silencio (#DEUDA-01).",
        )

    def test_both_preset_dicts_were_actually_found(self):
        """
        Si renombran CLOUDINARY_PRESETS/VIDEO_PRESETS, este test lo dice
        en vez de que el de arriba pase en falso por no encontrar nada.
        """
        source = CLOUDINARY_UTILS_PATH.read_text(encoding='utf-8')
        tree = ast.parse(source)
        found_names = {
            target.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict)
            for target in node.targets
            if isinstance(target, ast.Name)
        }
        for name in DICTS_TO_CHECK:
            self.assertIn(name, found_names)
