# BOLT-48 — `LEY-03` (resto): plazos de `Order`, `PaymentLog` y `EmailOutbox`

> **Decisión del dueño (2026-11-15):** `Order` y `PaymentLog` se conservan 6 años (obligación
> tributaria); `EmailOutbox` 90 días. Esta card puede crear migraciones solo si las necesita.

## Contexto verificado (2026-11-15)

- Ya existe la purga de mensajes de contacto con tope legal de 365 días
  (`settings.CONTACT_MAX_RETENTION_DAYS`, `send_contact_digest._purge_all` →
  `_purge_beyond_legal_cap`). Corre para todo tenant activo cada vez que corre el digest.
- Sin plazo hoy: `apps/orders/models.py::Order` (datos del comprador: `email`, `buyer_name`,
  `buyer_phone`, `billing_rut`, `ip_address`, `consent_at`; `created_at`, `paid_at`),
  `PaymentLog` (`raw_data` JSON, `ip_address`, `created_at`; FK a `Order`) y
  `apps/core/models.py::EmailOutbox` (`to_email`, `subject`, cuerpo; `status`, `created_at`,
  `sent_at`).
- La política publicada (`templates/legal/privacy_tenant_body.html` y
  `privacy_platform_body.html`, sección "5. Cuánto tiempo los conservamos") solo nombra el plazo
  de los mensajes de contacto.

## Qué hacer

1. Settings en `config/settings/base.py`, junto a `CONTACT_MAX_RETENTION_DAYS`:
   `ORDER_RETENTION_DAYS = 2190` (6 años) y `EMAIL_OUTBOX_RETENTION_DAYS = 90`, con un comentario
   que cite la razón (tributaria / proporcionalidad, Ley 21.719 art. 14 d).
2. Nuevo comando `apps/core/management/commands/purge_expired_data.py` con `--dry-run`:
   - `EmailOutbox` en estado final (enviado o fallido definitivo; **no** los pendientes) con más de
     90 días desde `created_at` → se borran.
   - `Order` con más de 6 años desde `created_at` → se borran con sus `PaymentLog` (verifica el
     `on_delete`; si una orden tiene un `Client` vivo asociado, borrar la orden **no** debe borrar
     el tenant).
   - Imprime y registra en el log cuántas filas borró de cada tipo, sin datos personales
     (usa `apps/core/logging_utils.py`).
3. Para que corra en producción sin un cron nuevo: `send_contact_digest` invoca esta purga una vez
   por ejecución (después de `_purge_all`), respetando su `--dry-run`. Un fallo de esta purga no
   debe impedir el envío del digest (se registra y sigue).
4. Política: en la sección 5 de **ambos** cuerpos legales agrega los plazos nuevos en lenguaje
   llano (comprobantes de compra y pago: 6 años por obligación tributaria; registros de correos
   enviados: 90 días). No cambies `PRIVACY_POLICY_VERSION` (la política aún no entra en vigencia
   y está pendiente de abogado); repórtalo.
5. `Documentacion/SEGURIDAD.md` §3: tabla de plazos por tipo de dato.

## Tests de rojo

`apps.core.tests.test_purge_expired_data` (archivo nuevo con ese nombre exacto). Casos:
`EmailOutbox` enviado a 91 días → borrado; a 89 días → se queda; pendiente a 200 días → se queda;
`Order` a 6 años + 1 día → borrada con sus `PaymentLog`; a 5 años → se queda; el `Client` de una
orden borrada sigue existiendo; `--dry-run` no borra nada; `send_contact_digest` llama a la purga
y sigue si esta lanza una excepción; la política renderizada menciona los dos plazos nuevos.

## No tocar

La purga de contactos existente. `PRIVACY_POLICY_VERSION`. El webhook y el checkout.

## DoD

- [ ] Los tres tipos de dato tienen plazo, en settings, con purga probada.
- [ ] La política publica los plazos.
- [ ] Cierre documental: `LEY-03` queda **parcial** solo por "cron en Render (`OPS-06`)", que es
      del dueño; acota la fila a eso.
- [ ] En `revisar_humano`: que el borrado de órdenes es irreversible; que las órdenes **impagas**
      (pendientes, fallidas, expiradas) también se guardan 6 años y podría convenir un plazo menor;
      y que los textos legales cambiaron.
