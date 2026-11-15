# BOLT-20 — `SEC-08`: un solo login y `next` validado

## Contexto verificado (2026-11-14)

- `config/urls.py:19` incluye `apps.website.auth_urls` en `auth/` y la línea 40 incluye
  `apps.accounts.urls` (namespace `accounts`) en el mismo prefijo. `/auth/login/` y
  `/auth/logout/` resuelven siempre a `apps/website/auth_views.py::client_login` /
  `client_logout`; `apps/accounts/views.py::login_view` (línea 148) y `logout_view` (línea 200)
  son inalcanzables por URL, pero `reverse('accounts:login')` sigue devolviendo `/auth/login/`.
- `login_view` hace `redirect(next_url)` con el `next` crudo del querystring (open redirect,
  líneas 157–181). Hoy no se ejecuta, pero queda a una reordenación de URLs de volverse real.
- `client_login` (el login vivo: rate limit, pertenencia al tenant, mensaje único) **ignora
  `next`**: `tenant_member_required` manda a `/auth/login/?next=/dashboard/...` y después del
  login el usuario cae en `home`. Solo hay un caso especial para staff con `superadmin` en `next`
  (líneas 96–99).
- Referencias a `accounts:login`: `templates/accounts/request_password_reset.html:71`,
  `set_password_expired.html:38`, `set_password_invalid.html:31`,
  `apps/accounts/views.py:141` y `:211`.

## Decisión del dueño

`SEC-08` = **un solo login**. Esto levanta la restricción antigua de "no eliminar
`login_view`/`logout_view`": se eliminan.

## Qué hacer

1. Tests nuevos en `apps/website/tests/test_login_next.py` (mira
   `test_login_tenant_authorization.py` para armar tenant, host y usuario):
   - Login correcto con `?next=/dashboard/` → 302 a `/dashboard/`.
   - `?next=https://evil.example/x` → 302 a `home`, nunca al host externo.
   - `?next=//evil.example/x` → 302 a `home`.
   - Sin `next` → 302 a `home` (comportamiento actual).
   - `reverse('accounts:login')` y `reverse('accounts:logout')` levantan `NoReverseMatch`.
   - `resolve('/auth/login/').func` es `client_login`.
   - La página de recuperar contraseña (`accounts:forgot_password`) renderiza y enlaza a
     `/auth/login/`.
2. `client_login`: tras un login válido, si `next` (del querystring, o del POST si el formulario
   lo reenvía) pasa `url_has_allowed_host_and_scheme(next, allowed_hosts={request.get_host()},
   require_https=request.is_secure())`, redirige ahí; si no, a `home`. Reemplaza el caso especial
   de `superadmin` por esta regla. Verifica que `templates/auth/login.html` conserve el `next` al
   enviar el formulario (action vacío o campo oculto) — si no lo conserva, agrégalo.
3. Elimina `login_view` y `logout_view` de `apps/accounts/views.py`, sus dos rutas en
   `apps/accounts/urls.py` y `templates/accounts/login.html` si ya nadie lo usa. Cambia las cinco
   referencias `accounts:login` por `client_login`.
4. Cobertura de `apps/accounts`: mídela
   (`python -m coverage run --source=apps/accounts manage.py test apps.accounts apps.website.tests.test_login_next`
   y `python -m coverage report`). Si queda bajo 70 %, agrega tests de `change_password_view` y
   `set_password_view` en `apps/accounts/tests.py` hasta pasarlo. Reporta el número.

## No tocar

El rate limit, el mensaje genérico y la verificación de tenant de `client_login`; el login del
admin (`/superadmin/`); `LOGIN_URL` de settings.

## Tests de rojo

`apps.website.tests.test_login_next`

## DoD

- [ ] Un solo par de vistas de login/logout en el repo; `grep -rn "accounts:login\|login_view" apps templates`
      sin resultados fuera de tests.
- [ ] `next` interno se respeta; `next` externo o `//host` se descarta (tests).
- [ ] Cobertura de `apps/accounts` ≥ 70 % (cifra en el informe).
- [ ] Playwright 7/7; suite verde.
- [ ] Cierre documental (`SEC-08`).
