# BOLT-80 — `BIZ-04`: `Client.plan` como FK a `Plan`

> Va **al final de la ronda**: es la única con migración.

## Decisión del dueño (2026-11-22)

`Client.plan` pasa a ser FK a `orders.Plan` ahora, antes del despliegue, aprovechando que hay pocos
tenants. Los límites copiados en `Client` (`max_images`, `max_services`) se quedan donde están; que
sigan al plan es otra card.

## Contexto verificado (2026-11-22)

- `apps/tenants/models.py:69`: `plan = models.CharField(max_length=20, choices=PLAN_CHOICES,
  default='essential')`, con `PLAN_CHOICES` `essential` / `pro` / `enterprise`. Son **los mismos
  slugs** que crean `setup_plans` y que tiene `Plan` en la base de desarrollo.
- En la base de desarrollo los 3 tenants tienen `plan='essential'`.
- Usos: `apps/orders/views_onboarding.py:210` (`plan=plan.slug`), `apps/tenants/management/commands/
  setup_dev_env.py` (líneas ~30, 56 y 104, con `'enterprise'` y `'pro'`) y 2 archivos de tests que
  crean `Client` con `plan='...'` (búscalos con `grep -rn "plan=['\"]" apps`). `apps/orders/admin.py`
  usa `plan` en `Order`, no en `Client`: confírmalo antes de tocarlo.
- Grafo de migraciones: `orders 0001` depende de `tenants 0009`; la última de orders es `0004`
  (depende de `orders 0003`) y la de tenants es `0032`. La migración nueva de tenants depende de
  `orders 0004`: el grafo sigue acíclico. Referencia el modelo por cadena (`'orders.Plan'`) para no
  crear un import circular.

## Qué hacer

1. Migraciones en `apps/tenants/migrations/`, en este orden: agregar un FK temporal nullable
   (`on_delete=PROTECT`); `RunPython` que copie el slug de texto al FK buscando `Plan` por `slug`
   (con `reverse` que vuelva a escribir el slug); borrar el `CharField` y renombrar el FK a `plan`.
   Puede ser una migración o varias.
2. **Si un `Client` tiene un slug sin `Plan` correspondiente, el FK queda en `null`** y la migración
   lo informa por `stdout`. No crees `Plan` dentro de la migración (tienen precios y features que
   define `setup_plans`).
3. Deja el campo final `null=True, blank=True` y borra `PLAN_CHOICES` si ya nadie lo usa.
4. Actualiza los usos: onboarding asigna el objeto `plan`; `setup_dev_env` busca el `Plan` por slug
   (si no existe, mensaje claro); los tests crean o reutilizan un `Plan`.
5. Comprueba la migración y su `reverse` contra la base de desarrollo con datos.

## Tests de rojo

`apps.tenants.tests_client_plan_fk` (archivo nuevo): `Client._meta.get_field('plan')` es un
`ForeignKey` a `orders.Plan`; un cliente creado por el onboarding queda con `client.plan.slug ==
order.plan.slug`. Debe fallar contra el código actual.

## No tocar

`Client.max_images` / `max_services`, `Plan` y sus migraciones, `BIZ-01` (límites), `render.yaml`.

## DoD

- [ ] `Client.plan` es FK a `Plan`, con los datos migrados y `reverse` probado.
- [ ] `makemigrations --check` limpio, suite en verde.
- [ ] En `revisar_humano`: "Antes de migrar en Neon, comprobar que existen los 3 `Plan`
      (si no, correr `setup_plans` antes del deploy)".
- [ ] Cierre documental: borra la fila `BIZ-04` y agrega la línea al histórico.
