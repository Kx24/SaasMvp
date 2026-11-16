# BOLT-37 — `CONS-11` (parte 2 de 4): cobertura de `apps/orders/` ≥ 80 %

## Contexto verificado (2026-11-15)

- Contrato: `apps/orders/` ≥ 80 %. Hoy 70,41 % (943 sentencias, 279 sin cubrir).
- Dónde está el hueco (sentencias sin cubrir): `services/mercadopago_service.py` 98 de 145 (32 %),
  `views.py` 56 de 166 (66 %), `models.py` 37, `admin.py` 28, `views_onboarding.py` 26.
- `MercadoPagoService` envuelve el SDK `mercadopago`: `process_payment`, `get_payment`,
  `validate_webhook_signature`, `refund_payment`, `_get_status_message`,
  `_get_rejection_message`, `get_payment_methods`.

## Qué hacer

1. Tests de `MercadoPagoService` **sin red**: el SDK se sustituye con `unittest.mock` (parchea el
   objeto `sdk` de la instancia o `mercadopago.SDK`). Cubre: pago aprobado, rechazado (con el
   mensaje de `_get_rejection_message` para al menos tres `status_detail`), pendiente, respuesta
   de error del SDK → `MercadoPagoError`, excepción de red → `MercadoPagoError`;
   `get_payment` encontrado y no encontrado; `refund_payment` total y parcial;
   `validate_webhook_signature` con firma válida, inválida, sin cabecera y sin secreto
   configurado.
2. Tests de las ramas sin cubrir de `views.py` (errores de validación del checkout, plan
   inexistente, JSON inválido, página de éxito/error con `uuid` inexistente) y de
   `views_onboarding.py`. Antes de escribir, mira qué líneas faltan con
   `python -m coverage run --source=apps/orders manage.py test apps.orders` +
   `python -m coverage report -m`.
3. `models.py`: propiedades y métodos de `Order`/`Plan`/`PaymentLog` no ejercitados.
4. Tests de comportamiento con aserciones reales; nada de llamadas sin afirmar.
5. Bug real destapado: se arregla y se reporta como hallazgo incidental.
6. Al final, con todo verde: `python scripts/gatekeeper.py --strict --update-baseline`.

## No tocar

El orden de `apps/orders/urls.py` (el patrón `<slug:plan_slug>/` va al final). Ninguna llamada
real a MercadoPago ni a SMTP. `COVERAGE_OMIT`, `# pragma: no cover`. El código de producción
salvo bug demostrado.

## DoD

- [ ] `orders` ≥ 80 % en `scripts/gate_baseline.json`; `tenants_core` y `total` no bajan.
- [ ] Los tests no hacen red (correrlos sin conexión da el mismo resultado).
- [ ] Cierre documental: `CONS-11` **parcial**. En `revisar_humano`: porcentajes antes y después y
      cualquier bug encontrado.
