Actúa como un arquitecto de software principal y agente de desarrollo autónomo bajo la metodología de Desarrollo Guiado por Pruebas (TDD) y "Confianza por Pruebas" (Uncle Bob's Safety Harness). 

Necesito que realices un análisis integral del repositorio local, la arquitectura del sistema y la documentación existente en `Documentacion/` para diseñar y ejecutar un plan maestro de desarrollo en el stack **Django + Tailwind/Alpine + Supabase/Render + Cloudinary**.

Aprovechando tus capacidades de razonamiento profundo y ejecución en bucle (Reason → Act → Verify), lleva a cabo las siguientes etapas:

---

### ETAPA 1: AUDITORÍA Y DIAGNÓSTICO PROFUNDO DE CÓDIGO
1. **Análisis de Arquitectura y Salud del Proyecto:**
   - Inspecciona las apps Django (`accounts`, `core`, `orders`, `tenants`, `website`, `marketing`) y el módulo de configuración (`config/`).
   - Evalúa el cumplimiento de patrones de diseño, separación de responsabilidades y manejo de seguridad (aislamiento multi-tenant, sanitización de inputs y gestión de credenciales/entorno).
   - Analiza el rendimiento del ORM: identifica posibles cuellos de botella `N+1`, falta de índices en modelos clave y eficiencia de consultas en Supabase.

2. **Mapeo de Módulos Críticos:**
   - **Flujos Transaccionales:** Inspecciona `orders/views_onboarding.py`, `urls_onboarding.py` y el manejo de atomicidad (`@transaction.atomic`).
   - **Pasarela de Pagos:** Revisa `orders/services/mercadopago_service.py` y los endpoints de webhooks para verificar idempotencia y control de excepciones.
   - **Contenido y Assets:** Verifica la integración de Cloudinary en `website` y la compilación/optimizaciones de Tailwind CSS.
   - **SEO y Visibilidad:** Evalúa `tenants/templatetags/seo_tags.py`, sitemaps y Open Graph.

---

### ETAPA 2: CONFIGURACIÓN DEL ARNÉS DE SEGURIDAD (SAFETY HARNESS / TDD)
Diseña el marco de trabajo para asegurar que **todo código generado en el futuro pueda ser aceptado sin revisión manual**, basándote en verificaciones automáticas duras:
1. **Definición de Reglas de Testing:** Establece la estrategia de pruebas unitarias y de integración necesarias antes de dar por completada cualquier tarea (cobertura mínima, aislamiento de DB).
2. **Métricas de Calidad y Restricciones:** Identifica y sugiere los hooks/linters a ejecutar (`ruff`, `mypy`, `bandit`, `pytest/manage.py test`).
3. **Bucle Autónomo de Reparación:** Define las instrucciones para que, en cada tarea futura, ejecutes el ciclo: *Escribir Spec/Test (Rojo) → Implementar Código mínimo → Verificar con Tests/Linter (Verde) → Autoreparar si falla*.

---

### ETAPA 3: GENERACIÓN DEL TABLERO KANBAN AVANZADO (`Documentacion/KANBAN_PROYECTO.md`)
Estructura un tablero Kanban técnico dividido en 3 horizontes temporales, asignando a cada tarea etiquetas de Prioridad (`[P0-Crítica]`, `[P1-Alta]`, `[P2-Media]`), Esfuerzo (`[S]`, `[M]`, `[L]`, `[XL]`) y Capa Técnica (`[Backend]`, `[Frontend]`, `[DevOps]`, `[Database]`):

1. **Corto Plazo (MVP / Lanzamiento Rancho Cachimba):**
   - Correo transaccional de bienvenida, confirmación de pago y reset de contraseña.
   - Integración robusta e idempotente de webhooks de Mercado Pago.
   - Onboarding atómico de nuevos tenants.
   - Auditoría y refinamiento UI/UX de componentes (Galería, formularios, listados).
   - Configuración SEO/GEO local, Open Graph dinámico y `sitemap.xml`.
   - Pipeline de build de Tailwind CSS + Cloudinary en Render.
   - Verificación de variables de entorno y preparación para despliegue.

2. **Mediano Plazo (Estabilidad, Seguridad y Performance):**
   - Manejo asíncrono de envíos de correo para evitar bloqueos del hilo HTTP.
   - Pruebas unitarias de aislamiento multi-tenant para evitar fuga de datos entre clientes.
   - Optimización de consultas ORM (`select_related`, `prefetch_related`).
   - Diseño de plantillas HTML transaccionales responsive.

3. **Largo Plazo (Escalabilidad y Operaciones):**
   - Dashboard de administración independiente/self-service para el cliente.
   - Estrategia de backups automatizados en Supabase.
   - Refactorización modular de deuda técnica.

---

### ETAPA 4: DESGLOSE TÉCNICO DE HISTORIAS DE USUARIO Y PRUEBAS AUTOMATIZADAS
Para cada historia de usuario del **Corto Plazo** y **Mediano Plazo**, incluye:
- **Contexto y Objetivo:** Qué problema resuelve.
- **Archivos Modificados/Involucrados:** Rutas exactas en la estructura del proyecto.
- **Criterios de Aceptación Técnicos:** Lista de verificación estricta basada en comportamiento esperado.
- **Estrategia de Verificación y Testing (Obligatoria):** Comandos exactos de ejecución (`python manage.py test ...`) y escenarios de prueba automáticos que deben pasar en verde.

---

### ETAPA 5: VERIFICACIÓN Y EJECUCIÓN AUTÓNOMA DE INICIO
Una vez creado el archivo `Documentacion/KANBAN_PROYECTO.md`:
1. Muestra un resumen ejecutivo con los 3 primeros bloqueadores clave identificados en la auditoría.
2. Genera una batería de pruebas sugerida para ejecutar inmediatamente y validar la salud actual de la suite de tests del proyecto.