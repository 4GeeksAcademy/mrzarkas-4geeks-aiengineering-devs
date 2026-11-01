# HealthCore Telemetry Design — 0.1

Fecha: 2026-11-01. Rama: `features/telemetryDesignPlan`. Hito exclusivamente documental. Todos los eventos son **PROPOSED como instrumentación**; el estado de cada componente se indica aparte. No hay decisiones de infraestructura ni tratamiento personal aprobadas. Prototipo sintético pre-MVP, sin autorización de piloto o producción.

# Plan documental

Secuencia: baseline → requisitos → catálogo → envelope → contratos → tareas → validación. Solo siete archivos en docs/telemetry/. Criterios: cobertura del prompt, >=8 oportunidades y >=3 categorías, contratos cerrados, inventario explícitamente pendiente, controles y trazabilidad.

## Ubicación vigente y continuidad de la API central

La confirmación del desarrollador y el checkout establecen el traslado `services/central-api/` → `backend/`, con paquete de aplicación en `backend/app/`. `backend/app/main.py` monta auth, catalogs, compliance, incidents y management. `docker-compose.yml` usa `context: ./backend`; `backend/Dockerfile` copia `app` y arranca Uvicorn con `app.main:app`. El historial muestra `8570d01 refactor: align Docker assignment with frontend and backend directories`.

Las referencias históricas a `services/central-api/app/` se interpretan como referencias al servicio hoy ubicado en `backend/app/`. Las migraciones están en `backend/alembic/versions/`, las pruebas en `backend/tests/` y la configuración del paquete en `backend/pyproject.toml`. Los puntos futuros de instrumentación pertenecen a los módulos vigentes de `backend/app/`; no se propone recrear el directorio anterior ni crear otra API. La ausencia de inventario se determina inspeccionando el árbol actual y los routers montados en `backend/app/main.py`, no buscando solamente en la ruta antigua. Inventario sigue PLANNED, mientras auth, incidencias y Management tienen evidencia de implementación en la ubicación actual.

## Technical Baseline y matriz de fuentes

| Requisito / capacidad | Fuente | Clase | Estado | Evidencia / discrepancia |
|---|---|---|---|---|
| API central FastAPI y PostgreSQL/SQLAlchemy | `backend/app/main.py`, `backend/app/db/session.py`, `backend/alembic/versions/`, README raíz «Dockerization assignment» | IDENTIFIED_OPPORTUNITY | IMPLEMENTED | API central trasladada desde `services/central-api/` a `backend/`; código vigente en `backend/app/` y entrada `backend/app/main.py` (`app.main:app`). El traslado conserva el servicio y sus módulos; la ausencia de la ruta anterior no significa ausencia de API. |
| Incidencias, historial y Management | `backend/app/incidents/router.py`, `history.py`, `management/router.py`, `service.py` | IDENTIFIED_OPPORTUNITY | IMPLEMENTED | Auditoría transaccional presente; no equivale a telemetría transversal. |
| Identidad JWT y permisos | `backend/app/auth/{router,security,dependencies,policies,roles}.py` | IDENTIFIED_OPPORTUNITY | IMPLEMENTED | Tokens de desarrollo; no login SSO, revocación ni sesión servidor demostrados. |
| Sesiones humanas | README backoffice; `frontend/app/internal/incident-history/workspace.js` | IDENTIFIED_OPPORTUNITY | PARTIAL | Conexión y desconexión en memoria; cerrar pestaña no demuestra logout. |
| Web pública e historial interno | `frontend/app/page.js`, `app/api/incident-history/route.js`, README | IDENTIFIED_OPPORTUNITY | IMPLEMENTED | Next.js; proxy privado con autorización backend; web pública separada. |
| Backoffice | `uis/backoffice/operational-incidents/app.js`, `management/index.html`, sus README | IDENTIFIED_OPPORTUNITY | IMPLEMENTED | Incidencias incluye alta y editor limitado; Management de lectura. |
| Artículos, movimientos, stock, reorden | `memory-bank/specs/inventory-manager/spec.md` RF-001–008 | MANDATORY_EXERCISE | PLANNED | Borrador; búsqueda stock/inventory en Python no muestra módulo, modelo ni ruta de inventario. Órdenes son operaciones lógicas futuras, no compras. |
| Entradas, salidas, fallos, escritura stock prohibida, umbral | Prompt §§3 y 5.2; INV-AC-006,007,010,014,017 | MANDATORY_EXERCISE | PLANNED | Obligatorios académicos; inventario no figura en CONTEXT.md. No hay lista externa de métricas más allá del prompt aportado. |
| Monitorización, sondas, alertas y auditoría | CONTEXT.md Tecnología, Cumplimiento, Dirección | MANDATORY_BRIEFING | PARTIAL | `/health` y `/status` presentes; no scheduler, colector ni centralización. |
| KPIs de citas, no-shows, reclamaciones, ingresos, satisfacción | CONTEXT.md áreas y Dirección | MANDATORY_BRIEFING | PLANNED | EHR, citas y facturación no integrados en este checkout. |
| RRHH, CME y carga documental | CONTEXT.md Personas y Operaciones | IDENTIFIED_OPPORTUNITY | PLANNED | Necesidades empresariales; ampliación futura, sin fuente operativa conectada. |
| Logging y procesos | `backend/app/main.py`, `error_contracts.py`, `catalogs/cache.py`, seeds | IDENTIFIED_OPPORTUNITY | PARTIAL | Excepciones HTTP y status manejadas, contadores caché locales; no middleware de telemetría ni bus encontrado. Logging runtime de Uvicorn no es pipeline aprobado. |
| Cumplimiento HIPAA/UK GDPR | CONTEXT.md, AGENTS.md | MANDATORY_BRIEFING | PLANNED | Restricciones obligatorias; cumplimiento certificado UNKNOWN. |

`memory-bank/technology-stack.md` y README de plantilla contienen afirmaciones obsoletas sobre ausencia de apps. `current-state.md` (2026-09-28) no incorpora la ubicación posterior ni todas las mejoras frontend. Se conserva discrepancia sin editar esas fuentes. Las evidencias de pruebas históricas no se presentan como ejecuciones de esta entrega. Revisión del árbol: `rg --files backend`; `rg -n 'stock|order|inventory' backend --glob '*.py'`; routers y modelos inspeccionados.

Quality Gate 0: arquitectura, seguridad, entidades y métricas identificadas; incógnitas no bloqueantes documentadas. Stock derivado es requisito **PLANNED**, no invariante implementado. No hay stock real que instrumentar.

## Decisión arquitectónica propuesta

Productores existentes (API FastAPI, Next.js y backoffice) → sanitización local → validación → colección por jurisdicción → procesamiento/deduplicación → almacenamiento separado → agregados/alertas autorizados. Todos los elementos posteriores a productores son futuros. La auditoría persistente existente sigue siendo fuente operacional independiente y no se reemplaza por eventos de navegador.

La decisión difícil es combinar inmediatez con exactitud transaccional sin incorporar PHI. Se propone outbox transaccional futuro para hechos críticos de movimientos y auditoría, y entrega best-effort acotada para navegación. Esto requiere futura migración/aprobación, no se implementa aquí. Emitir solo después del commit evita éxitos falsos pero deja ventana de pérdida entre commit y envío; outbox resuelve esa ventana, no los duplicados. Una cola durable permitiría reintentos/consumidores, con operación y coste extra. OpenTelemetry ayuda con trazas/métricas técnicas, pero no sustituye catálogo de negocio ni outbox; sus atributos/baggage deben sanitizarse. Un broker distribuido es prematuro sin volumen demostrado. Batch periódico es adecuado para agregados; no suficiente para alertas críticas. No se selecciona proveedor, Supabase, cloud ni nuevo microservicio.

Límites de confianza: navegador no acredita identidad, jurisdicción ni éxito de una mutación. Colector autentica productores, limita cuota y valida; API determina identidad y ámbito. Worker local agrega con acceso mínimo. Analistas reciben agregados, nunca tabla de resolución de seudónimos. Eventos críticos se reconcilian con fuente operacional para medir pérdidas.

## Estrategia de elaboración y revisión

Usar fuentes del checkout, generar catálogo antes de JSON, contrastar nombres/allowlists y ejemplos sintéticos, revisar estado Git al finalizar. Incógnitas del dominio no autorizan implementar ni emitir eventos. Consolidación en telemetry-plan.md de **propuestas revisables**, no decisiones aprobadas. Quality Gate 2 exige catálogo accionable y separación explícita de estados.
