# BOLT-71 — `CONS-13` (parte 2 de 2): vistas de accounts, sitemaps y admins

> Card de tests. Sin cambios de comportamiento: si al testear aparece un bug real, arréglalo
> mínimo y regístralo como hallazgo (regla del arnés).

## Contexto verificado (2026-11-18)

- `BOLT-39` dejó sin cubrir, entre otros, varios archivos de vistas y admin. Los porcentajes
  vigentes **hay que medirlos** (ver "Qué hacer", paso 1); el spec no inventa números.
- Candidatos a verificar: `apps/accounts/views.py` (login/logout/reset de contraseña, aislamiento
  por tenant ya probado en `BOLT-40`), `apps/website/sitemaps.py` o equivalente (sitemap por
  tenant y `robots.txt`), `apps/website/admin.py`, `apps/orders/admin.py`,
  `apps/tenants/admin.py` (los admins usan `TenantAdminMixin`, ver `BOLT-41`).
- `apps/accounts` tiene pocos tests propios: es la prioridad.

## Qué hacer

1. Mide: `python -m coverage run --source=apps manage.py test apps` y
   `python -m coverage report --skip-covered --sort=Cover` para escoger los 6 archivos de
   vistas, sitemaps y admin de **menor cobertura** (excluye comandos de gestión: son de
   `BOLT-70`, y excluye migraciones).
2. Escribe tests de comportamiento (no de línea): cliente HTTP con el `HTTP_HOST` del tenant,
   usuario con perfil de ese tenant. Para admins: cada `ModelAdmin` en el changelist con un
   superusuario (200) y que un staff de otro tenant no vea filas ajenas (reusa el patrón de
   `apps/accounts/tests_admin_scope.py`). Para sitemaps: solo URLs del tenant del `Host`.
3. Meta: cada archivo escogido ≥ 70 %, cobertura total sube al menos 1,5 puntos respecto del
   baseline del gate. No bajes ningún umbral.

## Tests de rojo

Ninguno (`red_tests` vacío): solo se agrega cobertura a código existente. Documéntalo en el informe.

## No tocar

Los comandos de gestión (`BOLT-70`), el comportamiento de las vistas, `scripts/gate_baseline.json`
(lo actualiza el gate al subir), la autenticación.

## DoD

- [ ] Los 6 archivos escogidos ≥ 70 %; total sube ≥ 1,5 puntos.
- [ ] Cierre documental: `CONS-13` se cierra: borra la fila del kanban y agrega la línea al
      histórico.
- [ ] En `revisar_humano`: lista de qué archivos escogiste y sus porcentajes antes y después.
