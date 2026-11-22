import ast
from pathlib import Path

from django.test import SimpleTestCase

import apps.tenants.management.commands.setup_cloudinary_folders as command_module


class SetupCloudinaryFoldersImportTests(SimpleTestCase):
    def test_comando_importa_cloudinary_api_por_si_mismo(self):
        tree = ast.parse(Path(command_module.__file__).read_text(encoding='utf-8'))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
                imported.update(f'{node.module}.{alias.name}' for alias in node.names)
        self.assertIn('cloudinary.api', imported)
