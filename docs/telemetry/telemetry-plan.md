# HealthCore Telemetry Design — contrato vigente1.2.0 y registro de revisiones

**Estado vigente2026-11-01, rama feature/telemetryEventCapture:** contrato1.2.0 con39 tipos (14 admiten null,25 sóloUS/UK), copias JSON backend/frontend idénticas. Captura local implementada con19 tipos al menos parciales y20 productores DEFERRED_NO_SOURCE aprobado. Evidencia y brechas: [delivery-status.md](../specs/telemetry-event-capture/delivery-status.md). No cobertura integral original ni producción.

## Registro histórico del diseño de Fase1 y revisiones

Las versiones/rama/estados PROPOSED y decisiones de infraestructura que siguen describen su revisión histórica; para operación actual prevalecen contrato1.2.0, código y expediente de entrega enlazado. El catálogo conserva requisitos no implementados, sin convertirlos en éxitos.

Fecha: 2026-11-01. Rama: `features/telemetryDesignPlan`. Hito exclusivamente documental. Todos los eventos son **PROPOSED como instrumentación**; el estado de cada componente se indica aparte. No hay decisiones de infraestructura ni tratamiento personal aprobadas. Prototipo sintético pre-MVP, sin autorización de piloto o producción.

## Revisión 1.1.0 — decisiones autorizadas y alcance de Fase 2

El desarrollador aprobó en esta sesión HMAC en servidor, clínica como fuente de jurisdicción, null para eventos generales, lotes de 20 o 10 segundos, la propuesta inicial de instalaciones regionales separadas (sustituida por backend compartido en la revisión actual) y fetch con Bearer/keepalive como sustitución de Beacon. Autorizó consolidar SDD y actualizar/validar el contrato. Es aprobación de estas decisiones y de la modificación documental; no atribuye una revisión a Claire ni autoriza datos reales, producción, configuración de despliegue o código.

**Contrato vigente de esta revisión documental:** schemaVersion 1.1.0. Es sustitución de una propuesta no desplegada; consumidores futuros deben validar esa versión. El catálogo conserva 39 nombres y sus allowlists. Se permite jurisdiction null únicamente en navigation_viewed, frontend_timing_measured, application_error_observed, session_started y session_ended. La propiedad es requerida. Los otros 34 eventos conservan US/UK obligatorio. Un evento de clínica con región desconocida se rechaza; NaN se rechaza antes de JSON.stringify, nunca se normaliza a null. Null indica ausencia genuina de clínica, no falta de configuración.

Decisión vigente, validada por Tecnología y solicitada por el desarrollador: un frontend y un backend compartidos. Sustituye la propuesta anterior de instalaciones regionales separadas. La API resuelve la clínica y selecciona en servidor las claves HMAC US/UK; firma y revalida el contexto con ese ámbito. Los eventos generales sin clínica conservan jurisdiction null y claves propias, sin atribuirles US o UK. Un contexto clínico no admite eventos de otra jurisdicción. El stub sigue local y no persistente; las referencias de destino regional no implementan forwarding ni aprueban procesamiento/almacenamiento externo. La ubicación del backend y ambos flujos requiere evaluación de Cumplimiento antes de activación real.

HMAC-SHA256 en servidor sobre UUID autenticado, con claves distintas por entorno/región/finalidad y salida ps_+64 hex. La misma identidad puede tener seudónimos distintos US/UK. No entregar claves ni UUID operativo al cliente de telemetría; no confiar en userId suministrado sin comprobarlo frente al actor autenticado/contexto. Gestión de claves, rotación y revisión de Cumplimiento siguen pendientes. Dedup futuro debe usar región de procesamiento confiable + eventId, no jurisdiction null como partición global. No dedup durable en el stub.

Perfil UI Fase 2: cola en memoria, lote máximo 20, deadline 10 s desde primer pendiente sin debounce; fetch con Bearer y keepalive al ocultar, siempre best-effort. Sustituye Beacon en requisitos de esta fase; no modifica política de autenticación ni CORS durante esta entrega. STREAM/sondas/reporting fuente siguen fuera de este transporte UI y no se declaran cubiertos.

**Cobertura inicial propuesta para revisión final:** navegación, errores frontend y Web Vitals compatibles en backoffice existente; session_started/ended sólo tras contexto autorizado. Incidencias/auditoría/auth/cache son productores servidor que requieren autorización concreta posterior; inventario/sondas/alertas/KPI/agregadores ausentes quedan aplazados, sin declarar satisfechas sus obligaciones. No crear fuentes ficticias para cerrar matriz.

Pruebas documentales: positivos US/UK en 39 eventos; null válido sólo en cinco, null inválido en 34, missing/NaN/string NaN/región inválida rechazados. Clasificación structural no comprueba clínica, autenticación o destino: esas invariantes necesitan tests de contexto del servidor al implementar. Staging sigue sin enum autorizado y no exporta hasta decisión de contrato.


## Executive Summary

39 eventos: 5 del ejercicio, 6 del briefing y 28 oportunidades. 17 STREAM y 22 BATCH; 11 categorías; 5 descartados. Clasificación primaria evita doble conteo. Cinco contratos del ejercicio cubren entradas/salidas, validación, rechazo stock y umbral; no hay lista académica adicional adjunta.

## Business Context / Telemetry Goals / Business & Technical Questions

HealthCore opera 12 clínicas (9 US,3 UK). Queremos decidir reposición futura, detectar interrupciones antes de llamadas, reducir fricción del operador y proporcionar KPIs fiables por región. ¿Qué operaciones fracasan? ¿Qué vistas son lentas? ¿Se detectan fallos? ¿Cuánto tarda resolución? ¿Cambian no-shows, rechazo, cobros y satisfacción? Cada pregunta tiene eventos/fórmulas y una fuente diferenciada. No integrar historias clínicas en este hito.

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

## Inventory Instrumentation Map

Flujo lógico **futuro**: identidad autenticada → consulta → selección → inicio de operación → validación → confirmación → movimiento persistido → stock calculado por suma firmada → evaluación de umbral → consulta del resultado. No representa diez pantallas/endpoints actuales.

1. Acceso: authentication_failed/succeeded, reutilización conceptual de dependencias vigentes tras aprobar permisos inventario.
2. Consulta y selección: inventory_viewed, product_selected.
3. Inicio: order_started con flowId; API mapea a operationId al confirmar.
4. Validación: inventory_validation_failed y stock_direct_update_rejected; incluir intento de stock en allowlist de entrada prohibida explícita, no aceptar silenciosamente campo desconocido.
5. Confirmación/commit: inbound_order_completed / outbound_order_completed; éxito implica movimiento trazable, no intención ni HTTP recibido por UI.
6. Cálculo: stock(ámbito)=sum(movimientos válidos firmados); ajuste siempre movimiento. No emitir un segundo «stock updated» por cada orden que duplicaría actividad.
7. Umbral: inventory_threshold_activated/cleared una vez por episodio/ámbito, sin incluir cantidad o umbral de negocio no aprobados.
8. Resultado o abandono: inventory_viewed / order_abandoned. Rechazos no registran movimiento; concurrencia debe preservar stock >=0 en futura implementación. El esquema no proporciona esa garantía por sí mismo.

## Cross-Application Event Catalog / Event Taxonomy

Taxonomía snake_case entidad_acción. P0 exige fuente íntegra; P1 es analítica/mejora. Frecuencias son por trigger, sin volumen productivo conocido.

### `inbound_order_completed`

Descripción/disparador: Commit confirmado de movimiento de entrada asociado a operación lógica de entrada. Categoría: Inventory. Prioridad: P0. Clase: MANDATORY_EXERCISE. Componente: PLANNED; evento PROPOSED. Origen/punto futuro: `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`.

Capturamos inbound_order_completed porque necesitamos conocer si la demanda de movimientos varía por periodo, lo que nos permite planificar reposición y carga de operaciones. Métrica: Entradas aceptadas por día. Requisito: TEL-FR-001.

Allowlist (todos requeridos): jurisdiction, environment, operationId, movementId, itemId. Tipos específicos: `{"operationId": "p", "movementId": "p", "itemId": "p"}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: BATCH. Analítica de tendencia; consumidor responsable de categoría, ventana diaria/horaria; demora de flush no cambia operación y reduce coste de transporte. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `outbound_order_completed`

Descripción/disparador: Commit confirmado de movimiento de salida asociado a operación lógica de salida. Categoría: Inventory. Prioridad: P0. Clase: MANDATORY_EXERCISE. Componente: PLANNED; evento PROPOSED. Origen/punto futuro: `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`.

Capturamos outbound_order_completed porque necesitamos conocer si la demanda de movimientos varía por periodo, lo que nos permite planificar reposición y carga de operaciones. Métrica: Salidas aceptadas por día. Requisito: TEL-FR-002.

Allowlist (todos requeridos): jurisdiction, environment, operationId, movementId, itemId. Tipos específicos: `{"operationId": "p", "movementId": "p", "itemId": "p"}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: BATCH. Analítica de tendencia; consumidor responsable de categoría, ventana diaria/horaria; demora de flush no cambia operación y reduce coste de transporte. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `inventory_validation_failed`

Descripción/disparador: Validador rechaza una operación antes de persistir. Categoría: Inventory. Prioridad: P0. Clase: MANDATORY_EXERCISE. Componente: PLANNED; evento PROPOSED. Origen/punto futuro: `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`.

Capturamos inventory_validation_failed porque necesitamos conocer si referencias o cantidades impiden completar movimientos, lo que nos permite corregir validaciones o formación. Métrica: Rechazos / intentos de movimiento. Requisito: TEL-FR-003.

Allowlist (todos requeridos): jurisdiction, environment, operationId, reasonCode. Tipos específicos: `{"operationId": "p", "reasonCode": ["reference", "quantity", "unit", "scope", "lot", "insufficient_stock", "conflict"]}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: STREAM. Urgencia operativa; consumidor responsable de categoría, ventana <=60 s propuesta; demora impide reacción y coste se justifica por criticidad. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `stock_direct_update_rejected`

Descripción/disparador: Detector explícito de campo stock rechaza escritura sin movimiento; nunca inferirlo de cualquier 422. Categoría: Inventory. Prioridad: P0. Clase: MANDATORY_EXERCISE. Componente: PLANNED; evento PROPOSED. Origen/punto futuro: `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`.

Capturamos stock_direct_update_rejected porque necesitamos conocer si clientes intentan vulnerar el invariante, lo que nos permite bloquear cliente defectuoso y revisar seguridad. Métrica: Intentos prohibidos por día. Requisito: TEL-FR-004.

Allowlist (todos requeridos): jurisdiction, environment, operationId, channel. Tipos específicos: `{"operationId": "p", "channel": ["api", "ui"]}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: STREAM. Urgencia operativa; consumidor responsable de categoría, ventana <=60 s propuesta; demora impide reacción y coste se justifica por criticidad. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `inventory_threshold_activated`

Descripción/disparador: Stock derivado cruza de >= a < umbral aprobado, después de commit. Categoría: Inventory. Prioridad: P0. Clase: MANDATORY_EXERCISE. Componente: PLANNED; evento PROPOSED. Origen/punto futuro: `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`.

Capturamos inventory_threshold_activated porque necesitamos conocer si una existencia entra en riesgo de falta, lo que nos permite priorizar reposición del ámbito. Métrica: Cruces bajo umbral / día. Requisito: TEL-FR-005.

Allowlist (todos requeridos): jurisdiction, environment, itemId, scopeId, episodeId. Tipos específicos: `{"itemId": "p", "scopeId": "p", "episodeId": "p"}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: STREAM. Urgencia operativa; consumidor responsable de categoría, ventana <=60 s propuesta; demora impide reacción y coste se justifica por criticidad. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `inventory_viewed`

Descripción/disparador: Consulta autorizada de existencias finaliza. Categoría: Inventory. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: PLANNED; evento PROPOSED. Origen/punto futuro: `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`.

Capturamos inventory_viewed porque necesitamos conocer si operaciones consulta con frecuencia determinadas vistas, lo que nos permite optimizar consultas de inventario. Métrica: Consultas / día. Requisito: TEL-FR-006.

Allowlist (todos requeridos): jurisdiction, environment, view. Tipos específicos: `{"view": ["items", "stock", "reorder", "movements"]}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: BATCH. Analítica de tendencia; consumidor responsable de categoría, ventana diaria/horaria; demora de flush no cambia operación y reduce coste de transporte. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `product_selected`

Descripción/disparador: Selección explícita de artículo en futuro flujo UI. Categoría: Inventory. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: PROPOSED; evento PROPOSED. Origen/punto futuro: `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`.

Capturamos product_selected porque necesitamos conocer si la selección no conduce siempre a una operación, lo que nos permite simplificar transición a movimientos. Métrica: Selecciones / sesiones. Requisito: TEL-FR-007.

Allowlist (todos requeridos): jurisdiction, environment, flowId. Tipos específicos: `{"flowId": "p"}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: BATCH. Analítica de tendencia; consumidor responsable de categoría, ventana diaria/horaria; demora de flush no cambia operación y reduce coste de transporte. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `order_started`

Descripción/disparador: Inicio explícito de flujo lógico de entrada/salida; no equivale a pedido comercial. Categoría: Inventory. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: PROPOSED; evento PROPOSED. Origen/punto futuro: `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`.

Capturamos order_started porque necesitamos conocer si operaciones inicia flujos que no completa, lo que nos permite mejorar confirmación y validación. Métrica: Inicios / día. Requisito: TEL-FR-008.

Allowlist (todos requeridos): jurisdiction, environment, flowId, direction. Tipos específicos: `{"flowId": "p", "direction": ["inbound", "outbound"]}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: BATCH. Analítica de tendencia; consumidor responsable de categoría, ventana diaria/horaria; demora de flush no cambia operación y reduce coste de transporte. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `order_abandoned`

Descripción/disparador: Procesador cierra flujo sin terminal tras 30 min de inactividad propuesta. Categoría: Inventory. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: PROPOSED; evento PROPOSED. Origen/punto futuro: `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`.

Capturamos order_abandoned porque necesitamos conocer si fricciones generan abandono, lo que nos permite revisar ux del paso más abandonado. Métrica: Flujos abandonados / iniciados maduros. Requisito: TEL-FR-009.

Allowlist (todos requeridos): jurisdiction, environment, flowId, lastStep, durationMs. Tipos específicos: `{"flowId": "p", "lastStep": ["selection", "validation", "confirmation"], "durationMs": "d"}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: BATCH. Analítica de tendencia; consumidor responsable de categoría, ventana diaria/horaria; demora de flush no cambia operación y reduce coste de transporte. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `inventory_adjustment_completed`

Descripción/disparador: Commit de ajuste materializado como movimiento. Categoría: Inventory. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: PLANNED; evento PROPOSED. Origen/punto futuro: `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`.

Capturamos inventory_adjustment_completed porque necesitamos conocer si muchos ajustes indican errores de registro, lo que nos permite reconciliar procesos de conteo. Métrica: Ajustes / movimientos aceptados. Requisito: TEL-FR-010.

Allowlist (todos requeridos): jurisdiction, environment, movementId, operationId. Tipos específicos: `{"movementId": "p", "operationId": "p"}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: BATCH. Analítica de tendencia; consumidor responsable de categoría, ventana diaria/horaria; demora de flush no cambia operación y reduce coste de transporte. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `inventory_threshold_cleared`

Descripción/disparador: Cruce de < a >= umbral comparable tras movimiento. Categoría: Inventory. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: PROPOSED; evento PROPOSED. Origen/punto futuro: `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`.

Capturamos inventory_threshold_cleared porque necesitamos conocer si alertas permanecen activas tras reposición, lo que nos permite cerrar episodio de reorden. Métrica: Tiempo de episodio bajo umbral. Requisito: TEL-FR-011.

Allowlist (todos requeridos): jurisdiction, environment, episodeId, itemId, scopeId. Tipos específicos: `{"episodeId": "p", "itemId": "p", "scopeId": "p"}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: STREAM. Urgencia operativa; consumidor responsable de categoría, ventana <=60 s propuesta; demora impide reacción y coste se justifica por criticidad. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `inventory_reconciliation_failed`

Descripción/disparador: Verificador encuentra proyección distinta a suma de movimientos comparables. Categoría: DataQuality. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: PROPOSED; evento PROPOSED. Origen/punto futuro: `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`.

Capturamos inventory_reconciliation_failed porque necesitamos conocer si una futura proyección puede divergir, lo que nos permite reconstruir proyección y suspender su uso. Métrica: Inconsistencias / comprobaciones. Requisito: TEL-FR-012.

Allowlist (todos requeridos): jurisdiction, environment, checkId, check. Tipos específicos: `{"checkId": "p", "check": ["stock_projection"]}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: STREAM. Urgencia operativa; consumidor responsable de categoría, ventana <=60 s propuesta; demora impide reacción y coste se justifica por criticidad. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `authentication_failed`

Descripción/disparador: Dependencia rechaza credenciales; código reducido, sin error JWT literal. Categoría: Authentication. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: IMPLEMENTED; evento PROPOSED. Origen/punto futuro: `backend/app/auth/dependencies.py:get_current_actor; backend/app/auth/security.py:decode_access_token`.

Capturamos authentication_failed porque necesitamos conocer si aumentan fallos de identidad, lo que nos permite investigar abuso o configuración. Métrica: 401 / solicitudes protegidas. Requisito: TEL-FR-013.

Allowlist (todos requeridos): jurisdiction, environment, reasonCode. Tipos específicos: `{"reasonCode": ["missing", "invalid", "expired"]}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: STREAM. Urgencia operativa; consumidor responsable de categoría, ventana <=60 s propuesta; demora impide reacción y coste se justifica por criticidad. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `authentication_succeeded`

Descripción/disparador: Primera validación satisfactoria de identidad en una sesión conceptual; no login real. Categoría: Authentication. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: IMPLEMENTED; evento PROPOSED. Origen/punto futuro: `backend/app/auth/dependencies.py:get_current_actor; backend/app/auth/security.py:decode_access_token`.

Capturamos authentication_succeeded porque necesitamos conocer si no se conoce uso autenticado, lo que nos permite dimensionar soporte al operador. Métrica: Sesiones autenticadas únicas. Requisito: TEL-FR-014.

Allowlist (todos requeridos): jurisdiction, environment, channel. Tipos específicos: `{"channel": ["api", "backoffice", "internal"]}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: BATCH. Analítica de tendencia; consumidor responsable de categoría, ventana diaria/horaria; demora de flush no cambia operación y reduce coste de transporte. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `session_started`

Descripción/disparador: UI conecta credenciales en memoria y primera lectura autorizada confirma acceso. Categoría: Authentication. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: PARTIAL; evento PROPOSED. Origen/punto futuro: `uis/backoffice/operational-incidents/app.js; frontend/app/internal/incident-history/workspace.js`.

Capturamos session_started porque necesitamos conocer si uso de herramientas cambia por semana, lo que nos permite planificar capacidad de soporte. Métrica: Sesiones / semana. Requisito: TEL-FR-015.

Allowlist (todos requeridos): jurisdiction, environment, application. Tipos específicos: `{"application": ["incidents", "management", "internal_history"]}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: BATCH. Analítica de tendencia; consumidor responsable de categoría, ventana diaria/horaria; demora de flush no cambia operación y reduce coste de transporte. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `session_ended`

Descripción/disparador: Desconexión explícita de UI; cierre del navegador es desconocido, no logout servidor. Categoría: Authentication. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: PARTIAL; evento PROPOSED. Origen/punto futuro: `frontend/app/internal/incident-history/workspace.js; README del backoffice`.

Capturamos session_ended porque necesitamos conocer si sesiones terminan por causas distintas, lo que nos permite mejorar mensajes de reconexión. Métrica: Finales explícitos / sesiones. Requisito: TEL-FR-016.

Allowlist (todos requeridos): jurisdiction, environment, reasonCode. Tipos específicos: `{"reasonCode": ["disconnect", "expired_observed"]}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: BATCH. Analítica de tendencia; consumidor responsable de categoría, ventana diaria/horaria; demora de flush no cambia operación y reduce coste de transporte. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `authorization_denied`

Descripción/disparador: Dependencia o política devuelve denegación de capacidad/ámbito. Categoría: Authorization. Prioridad: P0. Clase: IDENTIFIED_OPPORTUNITY. Componente: IMPLEMENTED; evento PROPOSED. Origen/punto futuro: `backend/app/auth/dependencies.py; backend/app/auth/policies.py`.

Capturamos authorization_denied porque necesitamos conocer si la matriz de permisos provoca bloqueos o abuso, lo que nos permite revisar alcance con tecnología y cumplimiento. Métrica: 403 / solicitudes protegidas. Requisito: TEL-FR-017.

Allowlist (todos requeridos): jurisdiction, environment, reasonCode, operation. Tipos específicos: `{"reasonCode": ["capability", "area_scope", "jurisdiction_scope"], "operation": ["read", "create", "update", "transition", "assign", "manage"]}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: STREAM. Urgencia operativa; consumidor responsable de categoría, ventana <=60 s propuesta; demora impide reacción y coste se justifica por criticidad. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `navigation_viewed`

Descripción/disparador: Vista lógica cambia y queda visible; excluir UUID y query string. Categoría: Navigation. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: IMPLEMENTED; evento PROPOSED. Origen/punto futuro: `uis/backoffice/operational-incidents/app.js; uis/backoffice/management/index.html; frontend/app/page.js`.

Capturamos navigation_viewed porque necesitamos conocer si algunas secciones concentran uso, lo que nos permite priorizar mejoras de navegación. Métrica: Vistas / sesión. Requisito: TEL-FR-018.

Allowlist (todos requeridos): jurisdiction, environment, view. Tipos específicos: `{"view": ["landing", "incident_queue", "incident_create", "incident_detail", "management", "internal_history"]}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: BATCH. Analítica de tendencia; consumidor responsable de categoría, ventana diaria/horaria; demora de flush no cambia operación y reduce coste de transporte. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `frontend_timing_measured`

Descripción/disparador: API Performance reporta métrica completa de navegación visible. Categoría: Performance. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: PROPOSED; evento PROPOSED. Origen/punto futuro: `frontend/app/layout.js; audit/README.md (evidencia de auditoría, no RUM)`.

Capturamos frontend_timing_measured porque necesitamos conocer si la latencia perjudica al operador, lo que nos permite optimizar recursos y respuesta. Métrica: p75 LCP/INP; p75 CLS. Requisito: TEL-FR-019.

Allowlist (todos requeridos): jurisdiction, environment, metric, value, view. Tipos específicos: `{"metric": ["lcp_ms", "inp_ms", "cls"], "value": "d", "view": ["landing", "incidents", "management", "internal_history"]}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: BATCH. Analítica de tendencia; consumidor responsable de categoría, ventana diaria/horaria; demora de flush no cambia operación y reduce coste de transporte. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `api_request_completed`

Descripción/disparador: Respuesta ASGI finaliza; middleware futuro calcula duración monotónica. Categoría: Performance. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: IMPLEMENTED; evento PROPOSED. Origen/punto futuro: `backend/app/main.py; routers montados`.

Capturamos api_request_completed porque necesitamos conocer si hay rutas lentas o fallidas, lo que nos permite priorizar optimización de rutas. Métrica: p95 duración; 5xx / respuestas. Requisito: TEL-FR-020.

Allowlist (todos requeridos): jurisdiction, environment, route, statusCode, durationMs. Tipos específicos: `{"route": ["health", "status", "auth", "catalogs", "incidents", "management", "compliance", "unknown"], "statusCode": "http", "durationMs": "d"}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: BATCH. Analítica de tendencia; consumidor responsable de categoría, ventana diaria/horaria; demora de flush no cambia operación y reduce coste de transporte. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `application_error_observed`

Descripción/disparador: Excepción no controlada clasificada en frontera; no duplicar HTTP esperado. Categoría: Errors. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: PARTIAL; evento PROPOSED. Origen/punto futuro: `backend/app/main.py; frontend/app/internal/incident-history/lazy-error-boundary.js`.

Capturamos application_error_observed porque necesitamos conocer si errores repetidos interrumpen flujos, lo que nos permite priorizar corrección por componente. Métrica: Errores no controlados / día. Requisito: TEL-FR-021.

Allowlist (todos requeridos): jurisdiction, environment, component, reasonCode. Tipos específicos: `{"component": ["api", "frontend", "backoffice"], "reasonCode": ["timeout", "database", "render", "load", "unexpected"]}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: STREAM. Urgencia operativa; consumidor responsable de categoría, ventana <=60 s propuesta; demora impide reacción y coste se justifica por criticidad. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `catalog_cache_observed`

Descripción/disparador: Corte agregado de contadores por worker cada 5 min. Categoría: Performance. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: IMPLEMENTED; evento PROPOSED. Origen/punto futuro: `backend/app/catalogs/cache.py:CatalogCache`.

Capturamos catalog_cache_observed porque necesitamos conocer si caché puede evadir o fallar demasiado, lo que nos permite ajustar límites tras benchmark. Métrica: hits / (hits + misses). Requisito: TEL-FR-022.

Allowlist (todos requeridos): jurisdiction, environment, hits, misses, bypasses, windowSeconds. Tipos específicos: `{"hits": "n", "misses": "n", "bypasses": "n", "windowSeconds": "n"}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: BATCH. Analítica de tendencia; consumidor responsable de categoría, ventana diaria/horaria; demora de flush no cambia operación y reduce coste de transporte. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `service_health_checked`

Descripción/disparador: Sonda futura invoca /health o /status con timeout. Categoría: Reliability. Prioridad: P0. Clase: MANDATORY_BRIEFING. Componente: PARTIAL; evento PROPOSED. Origen/punto futuro: `CONTEXT.md Tecnología; backend/app/main.py:health,status`.

Capturamos service_health_checked porque necesitamos conocer si fallos se detectan actualmente por llamadas, lo que nos permite abrir incidente tras fallo sostenido. Métrica: Sondas satisfactorias / sondas válidas. Requisito: TEL-FR-023.

Allowlist (todos requeridos): jurisdiction, environment, check, outcome, durationMs. Tipos específicos: `{"check": ["liveness", "database"], "outcome": ["ok", "failed", "timeout"], "durationMs": "d"}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: STREAM. Urgencia operativa; consumidor responsable de categoría, ventana <=60 s propuesta; demora impide reacción y coste se justifica por criticidad. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `alert_triggered`

Descripción/disparador: Regla aprobada cruza umbral y crea episodio. Categoría: Operations. Prioridad: P0. Clase: MANDATORY_BRIEFING. Componente: PLANNED; evento PROPOSED. Origen/punto futuro: `CONTEXT.md Tecnología y Dirección`.

Capturamos alert_triggered porque necesitamos conocer si no existe reacción proactiva sistemática, lo que nos permite asignar respuesta a tecnología. Métrica: Alertas nuevas / periodo. Requisito: TEL-FR-024.

Allowlist (todos requeridos): jurisdiction, environment, episodeId, rule. Tipos específicos: `{"episodeId": "p", "rule": ["availability", "inventory", "security", "telemetry_quality", "business"]}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: STREAM. Urgencia operativa; consumidor responsable de categoría, ventana <=60 s propuesta; demora impide reacción y coste se justifica por criticidad. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `notification_delivery_completed`

Descripción/disparador: Proveedor futuro confirma entrega o fallo terminal sin destinatario. Categoría: Operations. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: PROPOSED; evento PROPOSED. Origen/punto futuro: `CONTEXT.md Experiencia del Paciente y Acceso; no integración en código`.

Capturamos notification_delivery_completed porque necesitamos conocer si alertas no llegan siempre a responsables, lo que nos permite reintentar o cambiar canal autorizado. Métrica: Entregas / intentos terminales. Requisito: TEL-FR-025.

Allowlist (todos requeridos): jurisdiction, environment, notificationId, channel, outcome. Tipos específicos: `{"notificationId": "p", "channel": ["email", "sms", "app"], "outcome": ["delivered", "failed"]}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: STREAM. Urgencia operativa; consumidor responsable de categoría, ventana <=60 s propuesta; demora impide reacción y coste se justifica por criticidad. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `job_run_completed`

Descripción/disparador: Job futuro termina con resultado o timeout. Categoría: Operations. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: PROPOSED; evento PROPOSED. Origen/punto futuro: `CONTEXT.md Tecnología; data/pipelines/README.md`.

Capturamos job_run_completed porque necesitamos conocer si automatización puede fallar sin visibilidad, lo que nos permite reprocesar lote fallido. Métrica: Éxitos / ejecuciones terminales. Requisito: TEL-FR-026.

Allowlist (todos requeridos): jurisdiction, environment, runId, job, outcome, durationMs. Tipos específicos: `{"runId": "p", "job": ["health_checks", "aggregation", "reconciliation", "weekly_report"], "outcome": ["ok", "failed", "timeout"], "durationMs": "d"}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: STREAM. Urgencia operativa; consumidor responsable de categoría, ventana <=60 s propuesta; demora impide reacción y coste se justifica por criticidad. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `data_integrity_checked`

Descripción/disparador: Validador de referencias o futura comprobación completa un resultado. Categoría: DataQuality. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: PARTIAL; evento PROPOSED. Origen/punto futuro: `backend/app/reference_data/validation.py; backend/app/management/router.py`.

Capturamos data_integrity_checked porque necesitamos conocer si referencias incoherentes bloquean incidencias, lo que nos permite corregir maestros con propietario. Métrica: Fallos / verificaciones. Requisito: TEL-FR-027.

Allowlist (todos requeridos): jurisdiction, environment, check, outcome. Tipos específicos: `{"check": ["references", "historical_coverage", "event_contract"], "outcome": ["ok", "failed"]}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: STREAM. Urgencia operativa; consumidor responsable de categoría, ventana <=60 s propuesta; demora impide reacción y coste se justifica por criticidad. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `incident_created`

Descripción/disparador: Commit de incidencia creada. Categoría: Operations. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: IMPLEMENTED; evento PROPOSED. Origen/punto futuro: `backend/app/incidents/router.py; backend/app/incidents/history.py`.

Capturamos incident_created porque necesitamos conocer si crece el volumen de interrupciones, lo que nos permite repartir trabajo de tecnología. Métrica: Incidencias creadas / día. Requisito: TEL-FR-028.

Allowlist (todos requeridos): jurisdiction, environment, incidentId, auditId. Tipos específicos: `{"incidentId": "p", "auditId": "p"}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: BATCH. Analítica de tendencia; consumidor responsable de categoría, ventana diaria/horaria; demora de flush no cambia operación y reduce coste de transporte. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `incident_transitioned`

Descripción/disparador: Commit de transición autorizada. Categoría: Operations. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: IMPLEMENTED; evento PROPOSED. Origen/punto futuro: `backend/app/incidents/router.py; backend/app/incidents/history.py`.

Capturamos incident_transitioned porque necesitamos conocer si las incidencias tardan en resolverse, lo que nos permite revisar cuellos de botella. Métrica: Tiempo desde creación a estado terminal aprobado. Requisito: TEL-FR-029.

Allowlist (todos requeridos): jurisdiction, environment, incidentId, auditId. Tipos específicos: `{"incidentId": "p", "auditId": "p"}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: BATCH. Analítica de tendencia; consumidor responsable de categoría, ventana diaria/horaria; demora de flush no cambia operación y reduce coste de transporte. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `incident_assigned`

Descripción/disparador: Commit de asignación autorizada. Categoría: Operations. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: IMPLEMENTED; evento PROPOSED. Origen/punto futuro: `backend/app/incidents/router.py; backend/app/incidents/history.py`.

Capturamos incident_assigned porque necesitamos conocer si cambios de área retrasan atención, lo que nos permite clarificar propiedad operativa. Métrica: Asignaciones / incidencia. Requisito: TEL-FR-030.

Allowlist (todos requeridos): jurisdiction, environment, incidentId, auditId. Tipos específicos: `{"incidentId": "p", "auditId": "p"}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: BATCH. Analítica de tendencia; consumidor responsable de categoría, ventana diaria/horaria; demora de flush no cambia operación y reduce coste de transporte. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `management_mutation_completed`

Descripción/disparador: Commit de mutación con ManagementAuditEvent persistido. Categoría: Compliance. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: IMPLEMENTED; evento PROPOSED. Origen/punto futuro: `backend/app/management/router.py; backend/app/management/service.py`.

Capturamos management_mutation_completed porque necesitamos conocer si maestros cambian con impacto histórico, lo que nos permite revisar cambios con auditoría autorizada. Métrica: Mutaciones / día. Requisito: TEL-FR-031.

Allowlist (todos requeridos): jurisdiction, environment, auditId, resource, action. Tipos específicos: `{"auditId": "p", "resource": ["catalog", "reference", "coverage", "compliance_review"], "action": ["created", "updated", "activated", "deactivated", "coverage_changed", "state_changed", "associated"]}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: STREAM. Urgencia operativa; consumidor responsable de categoría, ventana <=60 s propuesta; demora impide reacción y coste se justifica por criticidad. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `audit_accessed`

Descripción/disparador: Consulta autorizada de auditoría finaliza, sin exportar snapshots. Categoría: Compliance. Prioridad: P0. Clase: MANDATORY_BRIEFING. Componente: PARTIAL; evento PROPOSED. Origen/punto futuro: `CONTEXT.md Cumplimiento; backend/app/incidents/router.py:incident_audit; backend/app/management/router.py:list_management_audit_events`.

Capturamos audit_accessed porque necesitamos conocer si la auditoría se consulta sin monitorización transversal, lo que nos permite revisar patrones de acceso autorizado. Métrica: Consultas de auditoría / periodo. Requisito: TEL-FR-032.

Allowlist (todos requeridos): jurisdiction, environment, surface. Tipos específicos: `{"surface": ["incident", "management"]}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: STREAM. Urgencia operativa; consumidor responsable de categoría, ventana <=60 s propuesta; demora impide reacción y coste se justifica por criticidad. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `telemetry_contract_rejected`

Descripción/disparador: Validador futuro rechaza envelope o propiedades; diagnóstico sin payload. Categoría: DataQuality. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: PROPOSED; evento PROPOSED. Origen/punto futuro: `Diseño conceptual de este hito`.

Capturamos telemetry_contract_rejected porque necesitamos conocer si productores envían contratos incompatibles, lo que nos permite detener versión defectuosa del productor. Métrica: Rechazados / recibidos. Requisito: TEL-FR-033.

Allowlist (todos requeridos): jurisdiction, environment, reasonCode, producer. Tipos específicos: `{"reasonCode": ["schema", "version", "privacy", "timestamp"], "producer": ["api", "frontend", "worker"]}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: STREAM. Urgencia operativa; consumidor responsable de categoría, ventana <=60 s propuesta; demora impide reacción y coste se justifica por criticidad. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `telemetry_delivery_failed`

Descripción/disparador: Productor futuro agota reintentos acotados. Categoría: Reliability. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: PROPOSED; evento PROPOSED. Origen/punto futuro: `Diseño conceptual de este hito`.

Capturamos telemetry_delivery_failed porque necesitamos conocer si pérdidas producen métricas falsas, lo que nos permite restaurar colector y marcar hueco. Métrica: Entregas fallidas / intentos. Requisito: TEL-FR-034.

Allowlist (todos requeridos): jurisdiction, environment, producer, reasonCode. Tipos específicos: `{"producer": ["api", "frontend", "worker"], "reasonCode": ["timeout", "queue_full", "unavailable"]}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: STREAM. Urgencia operativa; consumidor responsable de categoría, ventana <=60 s propuesta; demora impide reacción y coste se justifica por criticidad. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `appointment_period_aggregated`

Descripción/disparador: Adaptador local aprobado cierra día con totales reconciliados. Categoría: BusinessAnalytics. Prioridad: P1. Clase: MANDATORY_BRIEFING. Componente: PLANNED; evento PROPOSED. Origen/punto futuro: `CONTEXT.md Experiencia del Paciente, Facturación, Operaciones, Personas y Dirección; sin módulos integrados`.

Capturamos appointment_period_aggregated porque necesitamos conocer si no-shows del 22% y reservas requieren seguimiento, lo que nos permite priorizar recordatorios y capacidad. Métrica: noShows / eligibleAppointments; attended / eligibleAppointments. Requisito: TEL-FR-035.

Allowlist (todos requeridos): jurisdiction, environment, aggregateId, periodStart, periodEnd, eligibleAppointments, noShows, attended, booked. Tipos específicos: `{"aggregateId": "p", "periodStart": "t", "periodEnd": "t", "eligibleAppointments": "n", "noShows": "n", "attended": "n", "booked": "n"}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: BATCH. Analítica de tendencia; consumidor responsable de categoría, ventana diaria/horaria; demora de flush no cambia operación y reduce coste de transporte. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `billing_period_aggregated`

Descripción/disparador: Adaptador local cierra periodo contable con cohorte reconciliada. Categoría: BusinessAnalytics. Prioridad: P1. Clase: MANDATORY_BRIEFING. Componente: PLANNED; evento PROPOSED. Origen/punto futuro: `CONTEXT.md Experiencia del Paciente, Facturación, Operaciones, Personas y Dirección; sin módulos integrados`.

Capturamos billing_period_aggregated porque necesitamos conocer si rechazo del 14% y cobros carecen de visión unificada, lo que nos permite corregir patrones de rechazo y seguimiento. Métrica: rejectedClaims / adjudicatedClaims; collectedMinor / dueMinor. Requisito: TEL-FR-036.

Allowlist (todos requeridos): jurisdiction, environment, aggregateId, periodStart, periodEnd, adjudicatedClaims, rejectedClaims, collectedMinor, dueMinor, currency, stream. Tipos específicos: `{"aggregateId": "p", "periodStart": "t", "periodEnd": "t", "adjudicatedClaims": "n", "rejectedClaims": "n", "collectedMinor": "n", "dueMinor": "n", "currency": ["USD", "GBP"], "stream": ["us_claims", "uk_private", "uk_nhs"]}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: BATCH. Analítica de tendencia; consumidor responsable de categoría, ventana diaria/horaria; demora de flush no cambia operación y reduce coste de transporte. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `experience_period_aggregated`

Descripción/disparador: Encuestas locales aprobadas cierran día con agregado protegido. Categoría: BusinessAnalytics. Prioridad: P1. Clase: MANDATORY_BRIEFING. Componente: PLANNED; evento PROPOSED. Origen/punto futuro: `CONTEXT.md Experiencia del Paciente, Facturación, Operaciones, Personas y Dirección; sin módulos integrados`.

Capturamos experience_period_aggregated porque necesitamos conocer si satisfacción no es visible por sede, lo que nos permite priorizar mejora de acceso. Métrica: satisfiedResponses / validResponses. Requisito: TEL-FR-037.

Allowlist (todos requeridos): jurisdiction, environment, aggregateId, periodStart, periodEnd, validResponses, satisfiedResponses. Tipos específicos: `{"aggregateId": "p", "periodStart": "t", "periodEnd": "t", "validResponses": "n", "satisfiedResponses": "n"}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: BATCH. Analítica de tendencia; consumidor responsable de categoría, ventana diaria/horaria; demora de flush no cambia operación y reduce coste de transporte. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `workforce_period_aggregated`

Descripción/disparador: Fuente RRHH autorizada produce cohorte semanal agregada. Categoría: BusinessAnalytics. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: PLANNED; evento PROPOSED. Origen/punto futuro: `CONTEXT.md Experiencia del Paciente, Facturación, Operaciones, Personas y Dirección; sin módulos integrados`.

Capturamos workforce_period_aggregated porque necesitamos conocer si contratación tarda 47 días y cme se registra manualmente, lo que nos permite reforzar contratación y formación. Métrica: hiringDaysSum / filledRoles; expiredTraining / trainingEligible. Requisito: TEL-FR-038.

Allowlist (todos requeridos): jurisdiction, environment, aggregateId, periodStart, periodEnd, hiringDaysSum, filledRoles, departures, averageHeadcount, absenceHours, scheduledHours, expiredTraining, trainingEligible. Tipos específicos: `{"aggregateId": "p", "periodStart": "t", "periodEnd": "t", "hiringDaysSum": "n", "filledRoles": "n", "departures": "n", "averageHeadcount": "n", "absenceHours": "n", "scheduledHours": "n", "expiredTraining": "n", "trainingEligible": "n"}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: BATCH. Analítica de tendencia; consumidor responsable de categoría, ventana diaria/horaria; demora de flush no cambia operación y reduce coste de transporte. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

### `clinical_workload_aggregated`

Descripción/disparador: Fuente clínica autorizada produce sumas diarias sin notas ni personas. Categoría: BusinessAnalytics. Prioridad: P1. Clase: IDENTIFIED_OPPORTUNITY. Componente: PLANNED; evento PROPOSED. Origen/punto futuro: `CONTEXT.md Experiencia del Paciente, Facturación, Operaciones, Personas y Dirección; sin módulos integrados`.

Capturamos clinical_workload_aggregated porque necesitamos conocer si documentación consume 35 minutos diarios, lo que nos permite evaluar asistencia documental con aprobación. Métrica: documentationMinutes / operatorDays. Requisito: TEL-FR-039.

Allowlist (todos requeridos): jurisdiction, environment, aggregateId, periodStart, periodEnd, documentationMinutes, operatorDays. Tipos específicos: `{"aggregateId": "p", "periodStart": "t", "periodEnd": "t", "documentationMinutes": "n", "operatorDays": "n"}`. Privacidad: identificadores p seudónimos regionales; sin contenido libre; aplicación de política común.

Entrega: BATCH. Analítica de tendencia; consumidor responsable de categoría, ventana diaria/horaria; demora de flush no cambia operación y reduce coste de transporte. Frecuencia: una emisión por disparador descrito, agregados por periodo; volumen/coste UNKNOWN hasta medir tráfico y bytes. Duplicidad: reintentos de productor, dedup eventId; operationId/episodeId/aggregateId cuando existe para reconciliación semántica.

## Event Envelope

Todos los campos son obligatorios: eventId UUID generado por productor una vez; timestamp fecha ISO 8601 con zona (UTC recomendada); sessionId UUID aleatorio por conexión, null para worker/API sin sesión; userId seudónimo HMAC local, null para anónimo/worker; event_type entidad_acción snake_case; schemaVersion `1.1.0`; requestId UUID de correlación o null si no hay petición; properties allowlist. Ausente no equivale a null. No usar tokens para sessionId. Backend valida/genera requestId en frontera, con futura propagación permitida entre Next.js y API; no confiar en identificadores de cliente para autorizar. Sin cambio de CORS en este hito.

En properties todos llevan jurisdiction requerida: US/UK derivada de clínica, o null sólo en los cinco eventos generales clasificados en revisión 1.1.0; y environment (`development`, `test`, `production`). Un evento general sólo se exporta con instalación y contexto de procesamiento autorizados; null no habilita un receptor global ni sustituye contexto ausente. No usar geolocalización/IP como sustituto de jurisdicción. Production es opción conceptual, no autorización.

userId y referencias con sufijo Id salvo UUID de correlación son `ps_` + 64 hex, HMAC-SHA256 con clave regional y de propósito, nunca hash simple de emails. Resolución solo para servicio autorizado; claves/rotación requieren aprobación. Mantener clave estable en ventana analítica aprobada y evitar unión entre países. Datos seudonimizados siguen siendo personales; conteos pequeños pueden reidentificar. Agregados solo anónimos tras evaluación de riesgo y supresión, no por eliminar nombres.

Inmutabilidad: mismo eventId conserva payload en reintentos; deduplicación futura por (región de procesamiento confiable,eventId), ventana propuesta 7 días; mismo Id con contenido distinto se rechaza y alerta sin contenido. Operaciones lógicas usan operationId independiente de requestId; reintentos de petición no deben duplicar movimientos. Eventos fuente distintos no se fusionan por similitud. Agregados usan aggregateId estable por periodo/fuente; revisión de datos produce nueva versión de periodo y requiere protocolo futuro aprobado, no sumar revisiones como nuevos hechos.

Tiempo del hecho, no tiempo de ingestión. Duraciones por reloj monotónico. Colector conserva receivedAt fuera del envelope. Tolerancia propuesta +/-5 min para eventos recientes; batch histórico permite timestamp del cierre y periodo explícito. Eventos fuera de orden se procesan por tiempo del hecho y no sobrescriben estado reciente; watermarks propuestos 24 h, correcciones visibles tras ventana. Reglas semánticas adicionales: inicio < fin, contadores de subconjuntos <= denominador, ventanas positivas, CLS adimensional, noShows+attended <= eligibleAppointments, jurisdiction compatible con stream de facturación, sessionId/userId null para agregados y jobs; humano autenticado exige userId no nulo. JSON estructural no demuestra estas invariantes: se exigen en validador futuro.

## Event Properties & Allowlist

JSON es la fuente del contrato de tipos; catálogo repite campos exactamente. Todos son requeridos en esta versión, no hay opcionales arbitrarios. p = seudónimo `ps_` +64 hex; n = entero >=0; d = número >=0 (duración ms salvo CLS); t = ISO con zona; http = entero 100–599; listas entre corchetes = enum. Ningún código enum afirma catálogo empresarial aprobado; son clasificación técnica propuesta y cambios requieren versión. `properties` rechaza extras al igual que envelope.

## Catálogo de métricas: fórmulas y calidad

Periodo técnico diario UTC y comparación contra día/semana anterior equivalente; negocio por calendario local de jurisdicción pendiente de aprobación. Deduplicar eventId; excluir cuarentena y periodos incompletos, señalando cobertura. Nulo/denominador cero = unavailable, nunca 0. Sin muestreo en numeradores críticos; latencia/RUM muestreados se etiquetan y comparan solo con cobertura equivalente. p95/p75 por distribución de muestras, no promedio de percentiles. Duración de episodio = cleared.timestamp - activated.timestamp con episodeId; episodios abiertos censurados. Abandono: iniciados sin terminal después de 30 min y watermark, separar desconexión técnica de abandono intencional desconocido.

Para tasa de validación usar un terminal de éxito o fallo por operationId, no sumar reintentos. Tiempo de resolución usa estados terminales **aprobados** y joins con fuente de incidencia, no inventar enum de estados. Alertas/errores son conteos deduplicados, no usuarios afectados. Disponibilidad medida por sonda no prueba disponibilidad clínica de EHR.

No-shows: noShows/eligibleAppointments (excluir cancelados de cohorte definida); reservas = booked/periodo; volumen = attended/periodo. Rechazo: rejectedClaims/adjudicatedClaims de la misma cohorte, separado de pendiente; tasa cobro collectedMinor/dueMinor, ingresos = collectedMinor por currency/stream/periodo sin sumar USD+GBP ni equivaler automáticamente cobros e ingresos devengados. Satisfacción = satisfiedResponses/validResponses con definición de satisfecho a aprobar. Rotación = departures/averageHeadcount; absentismo = absenceHours/scheduledHours; formación caducada = expiredTraining/trainingEligible; contratación = hiringDaysSum/filledRoles (cohorte cerrada); documentación = documentationMinutes/operatorDays. Todos son ratios ponderados sumando numerador y denominador, no promedio entre clínicas. Fuentes y sesgos requieren acuerdo del responsable. Valores 22%,14%,47 días,35 min son baseline de briefing, no medidas ejecutadas aquí.

## Stream vs Batch Strategy

STREAM: consumidor operativo Tecnología/Cumplimiento/Operaciones, decisión en segundos/minutos; llegar tarde prolonga interrupción, falta de stock o pérdida de visibilidad. Objetivo propuesto p95 <=10 s desde hecho a colector y detección sostenida en <=60 s. Disponibilidad de colector propuesta 99.9% mensual, sin SLA aprobado. Conservar hechos críticos íntegros, sin sampling.

BATCH: consumidor producto/operaciones/analítica, revisión de tendencias, ventana de decisión horaria o diaria; demora de 15 min no altera transacción. Para productores BATCH servidor, flush propuesto cada 15 min y caché cada 5 min; el transporte UI Fase 2 aprobado usa 20 eventos/10 s; agregados de negocio por día cerrado y RRHH semanal. Briefing pide KPIs en tiempo real: agregados diarios son fase inicial **sin satisfacer todavía ese objetivo**; streaming de agregados incrementales requiere fuentes y evaluación de privacidad aprobadas. Informe lunes 7am requiere decidir zona horaria (Austin/Londres), DST y fuente, no se inventa un horario UTC.

Frecuencia y costes: no hay tráfico productivo medido. Cada evento se vincula a trigger en catálogo; volumen mensual = triggers/día ×30× fracción retenida × bytes promedio, almacenamiento = volumen × retención × factor índices/réplicas; sumar reintentos de transporte aparte de hechos únicos. Medir bytes con ejemplos no estima tráfico real. Guardar métricas de coste antes de habilitar; presupuesto y cuotas pendientes del CTO. No prometer escalabilidad sin benchmark.

## Throttling, Debouncing & Sampling

Navegación: debounce propuesto 300 ms por vista y sesión; máximo 1 mismo view por segundo. RUM y latencias: sampling determinista por requestId/sesión inicialmente 10% propuesto, conservar fracción para estimación; histogramas con buckets fijos, no percentiles promedio. Cache agrega contadores por worker/ventana y reinicio no se interpreta como delta negativo. Estado de sonda se sondea propuesto cada 30 s, alerta tras 2 fallos y recuperación tras 2 éxitos. Incidentes, movimientos, ajustes, auditoría, denegaciones, stock prohibido, cruces de umbral y calidad se conservan íntegros; ráfagas activan cuotas por productor con contador de pérdida visible, nunca reducción silenciosa ni sampling de auditoría.

No usar userId/itemId/incidentId como etiquetas de series; se reservan para joins autorizados. route/view/reasonCode son enums acotados. Debounce jamás junta dos mutaciones distintas. Deduplicar reenvíos por eventId y episodios de alerta por episodeId. Telemetría de rechazo/entrega se registra por canal de diagnóstico separado y acotado para evitar recursión al fallar el propio colector.

## Data Privacy & Security / Data Retention & Governance

No PHI, pacientes, notas, nombres de empleado, email, IP, user-agent completo, tokens, cookies, Authorization, cuerpos, respuestas, URLs, querystrings, stack traces, títulos, descripciones, motivos libres ni snapshots before/after. Allowlist se construye explícitamente antes de serializar; sanitización no consiste solo en regex. Diagnóstico de rechazo no conserva payload inválido. Catálogos técnicos no incorporan claves reales de clínica como ejemplos.

Particiones y claves separadas US/UK. Cumplimiento y Gobierno del Dato (Claire Whitfield) debe aprobar finalidad, bases legales, minimización, evaluación de impacto, acceso, auditoría, retención y posibles transferencias; HIPAA y UK GDPR se evalúan separadamente. No enviar eventos personales a proveedor externo ni compartir países sin base legal/técnica validada. Suprimir agregados con <10 contribuyentes es propuesta inicial, no garantía de anonimato; evitar diferenciar celdas o combinar periodos para reconstruir personas. Se requiere agregador local y evaluación de reidentificación antes de publicar.

Retención propuesta no aprobada: eventos técnicos 30 días; seudónimos de UX 7 días; agregados evaluados 13 meses; auditoría operacional **sin plazo inventado**, según política que Claire debe definir. Retención analítica no cambia auditoría fuente. Borrado por partición/plazo y resolución autorizada de solicitudes personales, incluyendo backups según política y retenciones legales; exportación/eliminación requiere evaluación antes de implementar. TTL de dedup debe ser coherente con reintentos/reprocesamientos y retención. Acceso least privilege por rol y región; cifrado/transporte, claves y log de accesos requieren revisión de infraestructura futura. No se certifica cumplimiento.

## Riesgos & Exclusions

| ID | Riesgo | Probabilidad / impacto | Mitigación | Responsable propuesto | Estado |
|---|---|---|---|---|---|
| R01 | PHI en campos de origen y auditoría | Alta / crítico | Proyección explícita; nunca copiar snapshots | Claire | Pendiente revisión |
| R02 | Inventario no construido ni ámbito aprobado | Alta / alto | Condicionar instrumentación a aprobación de artículos, unidades, lotes, ajuste y reorden | Operaciones/CTO | Abierto |
| R03 | Pérdida commit→envío y duplicados | Media / alto | Outbox futuro y dedup; reconciliación | Tecnología | Propuesto |
| R04 | Reidentificación y transferencia regional | Media / crítico | Separación y evaluación jurídica | Claire | Pendiente revisión |
| R05 | Coste y cardinalidad desconocidos | Alta / medio | Presupuesto y carga sintética antes de habilitar | CTO | Abierto |
| R06 | KPIs con fuentes ausentes / denominador sesgado | Alta / alto | Cohortes y reconciliación local; unavailable | Responsables de área | Abierto |
| R07 | Navegador falsifica identidad, éxito o región | Media / alto | Autoridad API para mutaciones; validación de origen | Tecnología | Propuesto |
| R08 | Metadatos temporales duplicados o tardíos | Media / medio | Watermarks, revisión de periodos, timestamps fiables | Gobierno del Dato | Propuesto |
| R09 | Agregado diario no satisface tiempo real empresarial | Alta / alto | Fase incremental tras aprobación; marcar cobertura parcial | CTO/Dirección | Abierto |

| Evento descartado | Hipótesis inicial | Motivo / riesgo evitado | Reconsideración |
|---|---|---|---|
| patient_record_viewed | Auditar uso de EHR | Fuentes ausentes y referencia paciente; PHI | Proyecto clínico autorizado y revisión Claire |
| request_body_captured | Depurar validaciones | Secretos y texto sensible | Mantener únicamente reasonCode cerrado |
| session_token_recorded | Correlacionar sesiones | Credencial reutilizable | Nunca; usar UUID de sesión |
| operator_keystroke_recorded | Detectar fricción | Vigilancia laboral y contenido libre | Métrica agregada consentida/aprobada si procede |
| stock_value_set | Medir cambios | Legitima edición directa prohibida | Nunca; movimientos autorizados |

## Future Instrumentation Roadmap y Open Decisions

Fuera de alcance: aprobar dominio de inventario y matriz de roles; aprobar gobernanza Claire; elegir collector/almacenamiento y presupuesto; probar contratos con fuentes sintéticas; instrumentar API primero, UI después; habilitar adaptadores regionales con aprobación. Nada de ello es tarea ejecutada aquí. Toda propuesta futura sobre autenticación, auditoría, migraciones o infra requiere autorización expresa.

Pendientes: dimensión stock y precisión/unidad; semántica ajuste/lote; umbral y episodios al reconfigurar; orden vs movimiento; roles/jurisdicción individual no presentes en JWT; protocolo de versión de agregados; zona informe ejecutivo; targets SLO, volumen y coste; política de borrado/backups; supresión estadística; eventos de login SSO real no diseñados como existentes.

## Conceptual Architecture



Productores existentes (API FastAPI, Next.js y backoffice) → sanitización local → validación → colección por jurisdicción → procesamiento/deduplicación → almacenamiento separado → agregados/alertas autorizados. Todos los elementos posteriores a productores son futuros. La auditoría persistente existente sigue siendo fuente operacional independiente y no se reemplaza por eventos de navegador.

La decisión difícil es combinar inmediatez con exactitud transaccional sin incorporar PHI. Se propone outbox transaccional futuro para hechos críticos de movimientos y auditoría, y entrega best-effort acotada para navegación. Esto requiere futura migración/aprobación, no se implementa aquí. Emitir solo después del commit evita éxitos falsos pero deja ventana de pérdida entre commit y envío; outbox resuelve esa ventana, no los duplicados. Una cola durable permitiría reintentos/consumidores, con operación y coste extra. OpenTelemetry ayuda con trazas/métricas técnicas, pero no sustituye catálogo de negocio ni outbox; sus atributos/baggage deben sanitizarse. Un broker distribuido es prematuro sin volumen demostrado. Batch periódico es adecuado para agregados; no suficiente para alertas críticas. No se selecciona proveedor, Supabase, cloud ni nuevo microservicio.

Límites de confianza: navegador no acredita identidad, jurisdicción ni éxito de una mutación. Colector autentica productores, limita cuota y valida; API determina identidad y ámbito. Worker local agrega con acceso mínimo. Analistas reciben agregados, nunca tabla de resolución de seudónimos. Eventos críticos se reconcilian con fuente operacional para medir pérdidas.


## Traceability & Validation / Requirements & Sources

Ver specs.md, traceability-matrix.md y validation-report.md. Quality Gates 0–3 documentales; ninguna aprobación de operación real implícita.

## Reajuste a backend compartido — 2026-11-01

Tecnología validó un frontend y un backend; el desarrollador pidió «reajusta teniendo en cuenta esto». Implementados juegos de claves US/UK seleccionados por Clinic/Jurisdiction validados en servidor, contextos firmados y revalidados por ámbito y productores post-commit con HMAC regional. Contrato público 1.1.0 sin cambios ni claves frontend. Generales sin clínica: null y claves generales independientes. La sesión puede renovarse al cambiar ámbito; cambia el seudónimo. Cola servidor particionada por región y binding clínico. No nuevas dependencias, auth policies, migraciones, Memory Bank, Rules, secretos, despliegue ni forwarding.

.env.example documenta TELEMETRY_PROCESSING_REGION vacío para backend compartido, cuatro claves generales y cinco por región. TELEMETRY_RESOURCE_KEY antigua no se usa en modo compartido; sus equivalentes son TELEMETRY_US_RESOURCE_KEY y TELEMETRY_UK_RESOURCE_KEY. TELEMETRY_US_ENDPOINT/UK_ENDPOINT son referencias opcionales, no transporte activo. Las configuraciones antiguas US/UK fijas se conservan sólo por compatibilidad. Producción, retención y ubicación de procesamiento/almacenamiento siguen pendientes de Cumplimiento. Los otros 31 eventos no se cierran.

## Contrato vigente1.2.0 — ámbito técnico general

Esta revisión sustituye1.1.0 en los modelos actuales; las evidencias anteriores son históricas. jurisdiction requerida admite null también en authentication_succeeded, authentication_failed, authorization_denied, api_request_completed, catalog_cache_observed, service_health_checked, data_integrity_checked, telemetry_contract_rejected y telemetry_delivery_failed. Total14 tipos nullable,25 US/UK obligatorio. Ausencia genuina de clínica, nunca fallback de resolución fallida. Los cinco tipos browser son los únicos que puede enviar el frontend; nulabilidad no es autorización de productor. Identidad no verificada mantiene userId=null. Regla y límites en docs/specs/telemetry-event-capture/general-technical-scope.md. Sin nuevos productores ni despliegue; actualizar frontend/API coordinadamente.
