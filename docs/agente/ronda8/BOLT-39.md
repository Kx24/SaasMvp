# BOLT-39 — `CONS-11` (parte 4 de 4): total ≥ 70 % y cierre

## Contexto verificado (2026-11-15)

- Contrato: total ≥ 70 %. Mira el número de entrada en `scripts/gate_baseline.json` (las cards
  `BOLT-36` a `BOLT-38` ya lo subieron) y calcula cuánto falta.
- Huecos que quedan (sentencias sin cubrir al 2026-11-15):
  `apps/website/admin.py` 87, `apps/accounts/admin.py` 34, `apps/accounts/views.py` 29,
  `apps/accounts/mixins.py` 27, `apps/marketing/sitemaps.py` 38, `apps/marketing/admin.py` 27,
  `apps/marketing/models.py` 23, `apps/tenants/views.py` 30, `apps/tenants/models.py` 59,
  `apps/website/views/gallery.py` 32.
- Comandos de gestión con 0 %: `core/…/audit_cloudinary_assets.py` (166),
  `tenants/…/create_tenant.py` (110), `core/…/check_cloudinary.py` (89),
  `core/…/cloudinary_usage.py` (72), `marketing/…/verify_search_console.py` (52),
  `tenants/…/setup_cloudinary_folders.py` (44), `tenants/…/setup_dev_env.py` (31),
  `tenants/…/seed_e2e_tenants.py` (20).

## Qué hacer

1. Prioriza el código que corre en producción: vistas de `accounts` (login, set-password,
   forgot-password: caminos de error), `tenants/views.py`, `sitemaps.py` (un sitemap por tenant,
   sin URLs de otro tenant), admins (`changelist` y `change` con un staff de tenant y con
   superuser, vía el cliente de test), métodos de modelo sin ejercitar.
2. Comandos de gestión: testea con `call_command` los que tienen lógica propia y se usan
   (`cloudinary_usage` con la API parcheada, `setup_production`, `provision_tenant` en sus ramas
   sin cubrir). **No borres comandos** en esta card; si alguno parece muerto (por ejemplo
   `create_tenant` frente a `provision_tenant`), repórtalo en `hallazgos` con la evidencia.
3. Sin red: Cloudinary, Search Console y SMTP siempre parcheados.
4. Tests de comportamiento con aserciones reales. Bug real destapado: se arregla y se reporta.
5. Al final, con todo verde: `python scripts/gatekeeper.py --strict --update-baseline`.

## No tocar

`COVERAGE_OMIT`, `# pragma: no cover`, borrado de código para subir el porcentaje.

## DoD

- [ ] `total` ≥ 70 %, `orders` ≥ 80 %, `tenants_core` ≥ 90 % en `scripts/gate_baseline.json`.
      Si `total` no llega a 70 con tests razonables, **no fuerces**: deja el mejor número, no
      cierres `CONS-11` y explica en `revisar_humano` qué falta y por qué.
- [ ] Cierre documental: `CONS-11` cerrada (fila borrada) solo si los tres umbrales se cumplen;
      si no, parcial con los números nuevos.
