# =============================================================================
# apps/core/management/commands/audit_cloudinary_assets.py
# =============================================================================
# Auditoría y limpieza de assets huérfanos en Cloudinary.
#
# Un asset huérfano es un archivo que existe en Cloudinary pero no tiene
# ningún CloudinaryField en la base de datos que lo referencie.
#
# MODOS DE USO:
#
#   Reportar huérfanos sin eliminar nada (seguro, recomendado primero):
#     python manage.py audit_cloudinary_assets --dry-run
#
#   Purgar huérfanos detectados:
#     python manage.py audit_cloudinary_assets --fix
#
#   Exportar reporte CSV:
#     python manage.py audit_cloudinary_assets --report
#     python manage.py audit_cloudinary_assets --report --output=reporte.csv
#
#   Combinar flags:
#     python manage.py audit_cloudinary_assets --dry-run --report
#     python manage.py audit_cloudinary_assets --fix --report
#
#   Limitar a un tenant específico:
#     python manage.py audit_cloudinary_assets --dry-run --tenant=andesscale
#
# LÓGICA:
#   1. Listar todos los public_ids en Cloudinary bajo prefix 'tenants/'
#      (o 'tenants/{slug}/' si se pasa --tenant)
#   2. Recolectar todos los public_ids referenciados en CloudinaryFields de DB
#   3. Los que están en Cloudinary pero NO en DB son candidatos a purga
#   4. --fix los elimina usando cloudinary.uploader.destroy()
# =============================================================================

import csv
import os
import logging
from datetime import datetime

import cloudinary
import cloudinary.api
import cloudinary.uploader

from django.core.management.base import BaseCommand, CommandError
from django.apps import apps

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Audita assets en Cloudinary y detecta huérfanos (sin referencia en DB). "
        "Usar --dry-run para reportar, --fix para purgar, --report para exportar CSV."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Detectar y reportar huérfanos sin eliminar nada (default seguro).',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            default=False,
            help='Purgar assets huérfanos de Cloudinary. IRREVERSIBLE.',
        )
        parser.add_argument(
            '--report',
            action='store_true',
            default=False,
            help='Exportar reporte CSV con todos los assets auditados.',
        )
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help='Ruta del archivo CSV de salida (default: cloudinary_audit_<timestamp>.csv).',
        )
        parser.add_argument(
            '--tenant',
            type=str,
            default=None,
            help='Limitar auditoría a un tenant específico (slug). Audita todos si no se especifica.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        fix = options['fix']
        report = options['report']
        tenant_slug = options.get('tenant')
        output_path = options.get('output')

        # Validación: al menos un flag de acción
        if not dry_run and not fix and not report:
            self.stdout.write(self.style.WARNING(
                "No se especificó ningún flag. Ejecutando --dry-run por defecto.\n"
                "Uso: manage.py audit_cloudinary_assets [--dry-run] [--fix] [--report]\n"
            ))
            dry_run = True

        if fix and dry_run:
            raise CommandError("--fix y --dry-run son mutuamente excluyentes.")

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Auditoría Cloudinary Assets ==="))

        # 1. Obtener public_ids de Cloudinary
        prefix = f"tenants/{tenant_slug}/" if tenant_slug else ""
        label = prefix if prefix else "(todos los assets)"
        self.stdout.write(f"  Listando assets en Cloudinary bajo: {label}")
        cloudinary_ids = self._list_cloudinary_assets(prefix)
        self.stdout.write(f"  Assets en Cloudinary: {len(cloudinary_ids)}")

        # 2. Obtener public_ids referenciados en DB
        self.stdout.write("  Recolectando referencias en base de datos...")
        db_ids = self._collect_db_references(tenant_slug)
        self.stdout.write(f"  Referencias en DB: {len(db_ids)}")

        # 3. Calcular huérfanos
        orphan_ids = cloudinary_ids - db_ids
        referenced_ids = cloudinary_ids & db_ids

        self.stdout.write(f"\n  Referenciados:  {len(referenced_ids)}")
        self.stdout.write(
            f"  Huérfanos:      "
            + (self.style.ERROR(str(len(orphan_ids))) if orphan_ids
               else self.style.SUCCESS(str(len(orphan_ids))))
        )

        # 4. Acción según flags
        purged = []
        purge_errors = []

        if dry_run:
            self._report_orphans(orphan_ids)

        if fix:
            purged, purge_errors = self._purge_orphans(orphan_ids)

        # 5. Exportar CSV
        if report:
            output_path = output_path or f"cloudinary_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            self._export_csv(
                output_path=output_path,
                cloudinary_ids=cloudinary_ids,
                db_ids=db_ids,
                orphan_ids=orphan_ids,
                purged=purged,
                purge_errors=purge_errors,
            )

        # 6. Resumen final
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Resumen ==="))
        self.stdout.write(f"  Total en Cloudinary: {len(cloudinary_ids)}")
        self.stdout.write(f"  Referenciados en DB: {len(referenced_ids)}")
        self.stdout.write(f"  Huérfanos detectados: {len(orphan_ids)}")
        if fix:
            self.stdout.write(self.style.SUCCESS(f"  Purgados exitosamente: {len(purged)}"))
            if purge_errors:
                self.stdout.write(self.style.ERROR(f"  Errores al purgar: {len(purge_errors)}"))
        if report:
            self.stdout.write(self.style.SUCCESS(f"  Reporte CSV: {output_path}"))

    # =========================================================================
    # HELPERS PRIVADOS
    # =========================================================================

    def _list_cloudinary_assets(self, prefix: str) -> set:
        """
        Lista todos los public_ids en Cloudinary bajo un prefix dado.
        Maneja paginación con next_cursor.
        """
        public_ids = set()
        next_cursor = None

        while True:
            try:
                params = {
                    'type': 'upload',
                    'max_results': 500,
                    'resource_type': 'image',
                }
                if prefix:
                    params['prefix'] = prefix
                if next_cursor:
                    params['next_cursor'] = next_cursor

                result = cloudinary.api.resources(**params)
                for resource in result.get('resources', []):
                    public_ids.add(resource['public_id'])

                next_cursor = result.get('next_cursor')
                if not next_cursor:
                    break

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Error listando Cloudinary: {e}"))
                break

        return public_ids

    def _collect_db_references(self, tenant_slug=None) -> set:
        """
        Recorre todos los modelos registrados en Django y extrae los public_ids
        de campos que son CloudinaryField o CharFields con valores 'tenants/...'.

        Filtra por tenant_slug si se especifica.
        """
        db_ids = set()

        for model in apps.get_models():
            cloudinary_fields = []

            for field in model._meta.get_fields():
                if not hasattr(field, 'attname'):
                    continue
                # Detectar por nombre de tipo para evitar problemas de import
                # entre distintas versiones/rutas de CloudinaryField
                if type(field).__name__ == 'CloudinaryField':
                    cloudinary_fields.append(field.attname)
                # Detectar CharFields legacy con public_ids de Cloudinary
                elif (hasattr(field, 'get_internal_type') and
                      field.get_internal_type() == 'CharField'):
                    cloudinary_fields.append(field.attname)

            if not cloudinary_fields:
                continue

            try:
                qs = model.objects.all()
                # Filtrar por tenant si el modelo tiene campo client__slug
                if tenant_slug:
                    if hasattr(model, 'client'):
                        qs = qs.filter(client__slug=tenant_slug)
                    elif model.__name__ == 'ClientSettings':
                        qs = qs.filter(client__slug=tenant_slug)

                for obj in qs.only(*cloudinary_fields).iterator(chunk_size=200):
                    for attname in cloudinary_fields:
                        value = getattr(obj, attname, None)
                        if not value:
                            continue

                        public_id = None
                        if hasattr(value, 'public_id') and value.public_id:
                            # CloudinaryResource — cubre todos los prefijos legacy
                            public_id = value.public_id
                        elif isinstance(value, str) and value.strip():
                            # CharField legacy con public_id directo
                            public_id = value.strip()

                        if public_id:
                            db_ids.add(public_id)

            except Exception as e:
                logger.warning(f"Error leyendo {model.__name__}: {e}")

        return db_ids

    def _report_orphans(self, orphan_ids: set):
        """Imprime la lista de huérfanos en consola."""
        if not orphan_ids:
            self.stdout.write(self.style.SUCCESS("\n  No se encontraron assets huérfanos."))
            return

        self.stdout.write(self.style.WARNING(f"\n  Huérfanos encontrados ({len(orphan_ids)}):"))
        for public_id in sorted(orphan_ids):
            self.stdout.write(f"    - {public_id}")

    def _purge_orphans(self, orphan_ids: set):
        """
        Elimina todos los assets huérfanos de Cloudinary.
        Retorna (purged_list, error_list).
        """
        if not orphan_ids:
            self.stdout.write(self.style.SUCCESS("\n  No hay huérfanos que purgar."))
            return [], []

        purged = []
        errors = []

        self.stdout.write(self.style.WARNING(f"\n  Purgando {len(orphan_ids)} assets huérfanos..."))

        for public_id in sorted(orphan_ids):
            try:
                result = cloudinary.uploader.destroy(public_id, resource_type='image')
                if result.get('result') == 'ok':
                    purged.append(public_id)
                    self.stdout.write(f"    ✓ {public_id}")
                else:
                    errors.append((public_id, str(result)))
                    self.stdout.write(self.style.WARNING(f"    ? {public_id} → {result}"))
            except Exception as e:
                errors.append((public_id, str(e)))
                self.stdout.write(self.style.ERROR(f"    ✗ {public_id} → {e}"))

        return purged, errors

    def _export_csv(self, output_path, cloudinary_ids, db_ids,
                    orphan_ids, purged, purge_errors):
        """Exporta reporte completo en CSV."""
        purged_set = set(purged)
        error_dict = dict(purge_errors)

        rows = []
        for public_id in sorted(cloudinary_ids):
            in_db = public_id in db_ids
            is_orphan = public_id in orphan_ids
            was_purged = public_id in purged_set
            error = error_dict.get(public_id, '')

            if is_orphan:
                status = 'purgado' if was_purged else ('error_purga' if error else 'huerfano')
            else:
                status = 'referenciado'

            rows.append({
                'public_id': public_id,
                'en_db': 'si' if in_db else 'no',
                'estado': status,
                'error': error,
            })

        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=['public_id', 'en_db', 'estado', 'error'],
                )
                writer.writeheader()
                writer.writerows(rows)
        except IOError as e:
            self.stdout.write(self.style.ERROR(f"  No se pudo escribir CSV: {e}"))
