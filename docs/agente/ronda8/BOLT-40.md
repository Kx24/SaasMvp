# BOLT-40 — `CONS-12`: guardia de objetos de tenant extendida a `orders` y `accounts`

## Contexto verificado (2026-11-15)

- `CONS-06` (`BOLT-28`) creó `apps/core/tenant_objects.py::tenant_object_or_404` y una guardia
  estática (`apps/core/tests/test_tenant_objects.py`) que impide `.objects.get(` /
  `get_object_or_404(` sin tenant en `apps/website/views/`. No cubre `orders` ni `accounts`.
- Usos actuales fuera de la guardia:
  - `apps/orders/views.py:43` y `:142`: `Plan` por `slug` (`Plan` es global, no tiene tenant).
  - `apps/orders/views.py:317`: `get_object_or_404(Order, uuid=order_uuid)` (página pública de
    resultado; el `uuid` es el secreto).
  - `apps/orders/views.py:407` y `:414`: `Order` por `order_number` / `mp_payment_id` dentro del
    webhook de MercadoPago (sin `request.client`: el webhook llega al dominio de la plataforma).
  - `apps/orders/signals.py:27`: `Order.objects.get(pk=instance.pk)`.
  - `apps/accounts/views.py:117`: `User.objects.get(email=email)` (recuperar contraseña).

## Qué hacer

1. Extiende la guardia estática a `apps/orders/` y `apps/accounts/` (vistas, signals, servicios;
   no tests ni migraciones). Cada uso de `.objects.get(` o `get_object_or_404(` debe ser
   `tenant_object_or_404`, filtrar por `client`, o figurar en una **lista explícita de
   excepciones** dentro del test, cada una con su justificación en una línea (modelo global,
   búsqueda por secreto, webhook sin tenant…).
2. Revisa cada uso de la lista de arriba y decide: ¿falta un filtro por tenant? Atención especial
   a `accounts/views.py:117`: un usuario del tenant A no debe poder disparar la recuperación de
   contraseña de un usuario del tenant B desde el dominio de A. Si hoy es posible, corrígelo
   (respuesta idéntica exista o no el usuario, sin enumeración) con un test que lo demuestre.
3. No cambies el comportamiento de los caminos que ya son correctos; solo decláralos.

## Tests de rojo

`apps.core.tests.test_tenant_objects` (la guardia extendida falla contra el código original si
encuentra un uso sin declarar; si todos resultan legítimos, el rojo es que la lista de excepciones
no existía: el test debe exigirla).

## No tocar

El orden de `apps/orders/urls.py`. La lógica del webhook (firma, idempotencia). Modelos.

## DoD

- [ ] La guardia cubre `website`, `orders` y `accounts`; un `.objects.get(` nuevo sin declarar
      rompe el test.
- [ ] Cada excepción tiene justificación escrita.
- [ ] Suite de aislamiento y suite completa verdes.
- [ ] Cierre documental (`CONS-12`). En `revisar_humano`: la lista de excepciones y cualquier
      fuga corregida.
