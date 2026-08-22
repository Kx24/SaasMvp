"""
Tests de índices compuestos (#MED-03).

No reemplazan un EXPLAIN ANALYZE real contra Supabase (eso queda como
verificación manual del usuario, no es automatizable desde SQLite) --
pero sí congelan qué índices espera el patrón de consulta real de cada
vista, para que nadie los borre sin darse cuenta en un refactor.
"""
from django.test import SimpleTestCase

from apps.website.models import Service


def _has_index(model, fields):
    return any(list(idx.fields) == list(fields) for idx in model._meta.indexes)


class ServiceIndexTestCase(SimpleTestCase):
    def test_service_is_indexed_for_home_query_shape(self):
        """
        apps/website/views.py::home hace
        Service.objects.filter(client=X, is_active=True).order_by('order')
        -- el índice (client, is_active) cubre el filtro pero no el
        order_by; agregar 'order' permite un index scan que también
        resuelve el orden sin un sort aparte.
        """
        self.assertTrue(
            _has_index(Service, ['client', 'is_active', 'order']),
            f"Service._meta.indexes no tiene (client, is_active, order); "
            f"tiene: {[list(i.fields) for i in Service._meta.indexes]}",
        )
