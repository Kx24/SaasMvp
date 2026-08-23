# CONTEXTO Y ROL
Actúa como Chief Software Architect y Lead Agentic Systems Engineer. Estás ejecutando directamente en la RAÍZ del repositorio de esta aplicación Django multi-tenant. Tu objetivo es analizar el estado actual del código y redactar una planificación ejecutable en `kanban.md` optimizada para un flujo de desarrollo 100% autónomo desatendido (AI-DLC).

# ENTORNOS Y RESTRICCIONES TÉCNICAS
- Entorno de ejecución: Terminal local en raíz del proyecto.
- Verdad Absoluta: Suite de pruebas local (`python manage.py test` / `pytest`), `ruff check` y `makemigrations --check`. Ninguna tarea se da por hecha sin passing total de estas restricciones.
- WIP Máximo: 1 tarea activa a la vez.

# INSTRUCCIONES DE ANÁLISIS
1. Realiza un escaneo completo de la estructura de archivos, modelos, vistas y tests existentes en el directorio actual.
2. Identifica los bloqueos críticos actuales del sistema (priorizando brechas multi-tenant, webhooks de pago, endpoints estancados y configuración de entorno).
3. Descompón las necesidades del proyecto en "Atomic Bolts" (bloques de desarrollo de 15 a 45 minutos) aislados y de bajo acoplamiento.

# ESTRUCTURA DE LA SALIDA (Escribir directamente en `kanban.md`)
Crea o sobrescribe el archivo `kanban.md` con la siguiente estructura estricta:

## §1. INFRAESTRUCTURA DEL PILOTO AGÉNTICO (Prioridad Inmediata)
Crea 3 tarjetas para la puesta en marcha del sistema desatendido:
- [PILOT-01] Skill de Gatekeeper & Test Runner (script en `scripts/skills/` que ejecute tests + ruff y devuelva JSON determinista).
- [PILOT-02] Prompts de Trabajo (.claude/workflows/ con 01_planificador.md, 02_dev_tester.md, 03_validador.md).
- [PILOT-03] Script Orquestador (orchestrate.py en la raíz con manejo de turnos y límite de 3 reintentos).

## §2. ATOMIC BOLTS DE PRODUCTO (Backlog de Corto Plazo)
Redacta las siguientes 3-5 tareas inmediatas del software con el siguiente formato OBLIGATORIO por tarjeta:

### [TASK-ID] Título Claro y Descriptivo
- **Estado:** TODO
- **Componente:** [Backend / Auth / Multi-tenant / Webhook / UI]
- **Archivos Afectados:** Lista explícita de rutas de archivo.
- **Definición de Terminado (DoD Verificable):**
  - [ ] Test unitario/integración escrito que exprese la funcionalidad (Red -> Green).
  - [ ] Implementación mínima que pase la suite de pruebas.
  - [ ] Cero errores en Linter (`ruff check`).
  - [ ] Sin side-effects fuera del alcance de la tarjeta.

# REGLAS DE EJECUCIÓN DEL PROMPT
- Genera el archivo `kanban.md` listo para ser consumido por el Agente Planificador.
- Asegúrate de que las tareas del producto no tengan ambigüedades; el agente dev debe poder implementar el test directamente leyendo el DoD.