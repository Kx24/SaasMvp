# BOLT-50 — `LEY-02` (parte 2 de 2): exportar, suprimir y bloquear los datos de una persona

> **Decisión del dueño (2026-11-15):** suprimir borra los mensajes de contacto y anonimiza lo
> demás; las órdenes se conservan por obligación legal. Esta card **puede crear una migración**.

## Contexto verificado (2026-11-15)

- `BOLT-49` dejó el modelo `DataSubjectRequest` y el canal. Falta la herramienta para cumplir
  cada solicitud.
- Datos personales de terceros en la base, por correo electrónico:
  `website.ContactSubmission` (`name`, `email`, `phone`, `company`, `subject`, `message`,
  IP y consentimiento), `orders.Order` (`email`, `buyer_name`, `buyer_phone`, `billing_rut`,
  `ip_address`) con sus `PaymentLog` (`raw_data`, `ip_address`), `core.EmailOutbox`
  (`to_email`, asunto, cuerpo) y `website.DataSubjectRequest`. Antes de escribir, busca con
  `git grep -n "EmailField"` si hay más modelos con correos de terceros y agrégalos.
- Los usuarios del dashboard (`auth.User` + `UserProfile`) son cuentas del cliente, no titulares
  externos: quedan **fuera** de esta card (repórtalo).

## Qué hacer

Comando `apps/core/management/commands/data_subject.py`:

```
python manage.py data_subject export  --email a@b.cl --tenant <slug> [--output archivo.json]
python manage.py data_subject erase   --email a@b.cl --tenant <slug> [--dry-run] [--request-id N]
python manage.py data_subject block   --email a@b.cl --tenant <slug> [--request-id N]
python manage.py data_subject unblock --email a@b.cl --tenant <slug>
```

1. **Siempre acotado a un tenant** (`--tenant` obligatorio; el correo se compara sin distinguir
   mayúsculas). Nunca toca datos de otro tenant.
2. **`export`**: JSON con todo lo que hay de esa persona en ese tenant, agrupado por tipo de
   dato, con fechas. Es la respuesta a acceso y portabilidad. Sin `--output` va a stdout.
3. **`erase`**: borra sus `ContactSubmission` y sus `EmailOutbox`; en `Order` **no borra**:
   sustituye nombre, teléfono, RUT e IP por un marcador (`[suprimido]` / `None`) y el correo por
   un valor no reversible (`suprimido-<hash corto>@invalid`), y vacía los campos personales de
   `raw_data` en sus `PaymentLog` conservando montos, estados e identificadores de pago. Imprime
   un resumen con conteos. Con `--dry-run` solo cuenta. Todo en una transacción.
4. **`block` / `unblock`** (bloqueo temporal, art. 8 ter): modelo `BlockedSubject`
   (`client`, `email`, `blocked_at`, `reason`), único por tenant y correo. Mientras exista, los
   mensajes de contacto de ese correo **no aparecen** en el dashboard de mensajes, ni en el
   digest, ni en los contadores, y no se purgan (se conservan intactos para cuando se resuelva).
   `unblock` lo revierte.
5. Con `--request-id`, la operación deja constancia en `DataSubjectRequest.response_notes`
   (qué se hizo y cuándo) sin cambiar su estado: cerrarla es decisión de una persona.
6. `Documentacion/SEGURIDAD.md` §3: procedimiento paso a paso para atender cada tipo de
   solicitud con este comando.

## Tests de rojo

`apps.core.tests.test_data_subject_command` (archivo nuevo con ese nombre exacto). Casos:
`export` incluye datos del tenant pedido y **ninguno** del mismo correo en otro tenant; `erase`
borra contactos y outbox, anonimiza la orden y la deja con su monto y estado, y no toca al otro
tenant; `erase --dry-run` no cambia nada; `block` oculta los mensajes del dashboard, del digest
y de los contadores, y la purga de 365 días no los borra; `unblock` los devuelve; sin
`--tenant` el comando falla; `--request-id` de otro tenant es rechazado.

## No tocar

El formulario y el admin de `BOLT-49`. Cuentas de usuario. El tope de 365 días para mensajes no
bloqueados.

## DoD

- [ ] Las cuatro operaciones funcionan, acotadas por tenant y probadas.
- [ ] Suite de aislamiento verde.
- [ ] Cierre documental: `LEY-02` cerrada.
- [ ] En `revisar_humano`: que `erase` es irreversible; qué campos exactos de `Order` y
      `PaymentLog` se anonimizan; y los modelos con datos personales que quedaron fuera.
