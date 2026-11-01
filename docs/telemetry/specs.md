# HealthCore Telemetry Design — 0.1

Fecha: 2026-11-01. Rama: `features/telemetryDesignPlan`. Hito exclusivamente documental. Todos los eventos son **PROPOSED como instrumentación**; el estado de cada componente se indica aparte. No hay decisiones de infraestructura ni tratamiento personal aprobadas. Prototipo sintético pre-MVP, sin autorización de piloto o producción.

# Specs SDD + EARS

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

## TEL-FR-001 — inbound_order_completed

Tipo EARS: Event-driven. Prioridad: P0. Fuente: MANDATORY_EXERCISE; `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`. Estado componente: PLANNED; instrumentación: PROPOSED.

WHEN Commit confirmado de movimiento de entrada asociado a operación lógica de entrada, THE telemetry design SHALL definir `inbound_order_completed` con envelope común y allowlist cerrado.

Justificación: La demanda de movimientos varía por periodo; decisión: Planificar reposición y carga de Operaciones. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-002 — outbound_order_completed

Tipo EARS: Event-driven. Prioridad: P0. Fuente: MANDATORY_EXERCISE; `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`. Estado componente: PLANNED; instrumentación: PROPOSED.

WHEN Commit confirmado de movimiento de salida asociado a operación lógica de salida, THE telemetry design SHALL definir `outbound_order_completed` con envelope común y allowlist cerrado.

Justificación: La demanda de movimientos varía por periodo; decisión: Planificar reposición y carga de Operaciones. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-003 — inventory_validation_failed

Tipo EARS: Event-driven. Prioridad: P0. Fuente: MANDATORY_EXERCISE; `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`. Estado componente: PLANNED; instrumentación: PROPOSED.

WHEN Validador rechaza una operación antes de persistir, THE telemetry design SHALL definir `inventory_validation_failed` con envelope común y allowlist cerrado.

Justificación: Referencias o cantidades impiden completar movimientos; decisión: Corregir validaciones o formación. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-004 — stock_direct_update_rejected

Tipo EARS: Event-driven. Prioridad: P0. Fuente: MANDATORY_EXERCISE; `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`. Estado componente: PLANNED; instrumentación: PROPOSED.

WHEN Detector explícito de campo stock rechaza escritura sin movimiento; nunca inferirlo de cualquier 422, THE telemetry design SHALL definir `stock_direct_update_rejected` con envelope común y allowlist cerrado.

Justificación: Clientes intentan vulnerar el invariante; decisión: Bloquear cliente defectuoso y revisar seguridad. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-005 — inventory_threshold_activated

Tipo EARS: Event-driven. Prioridad: P0. Fuente: MANDATORY_EXERCISE; `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`. Estado componente: PLANNED; instrumentación: PROPOSED.

WHEN Stock derivado cruza de >= a < umbral aprobado, después de commit, THE telemetry design SHALL definir `inventory_threshold_activated` con envelope común y allowlist cerrado.

Justificación: Una existencia entra en riesgo de falta; decisión: Priorizar reposición del ámbito. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-006 — inventory_viewed

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`. Estado componente: PLANNED; instrumentación: PROPOSED.

WHEN Consulta autorizada de existencias finaliza, THE telemetry design SHALL definir `inventory_viewed` con envelope común y allowlist cerrado.

Justificación: Operaciones consulta con frecuencia determinadas vistas; decisión: Optimizar consultas de inventario. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-007 — product_selected

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`. Estado componente: PROPOSED; instrumentación: PROPOSED.

WHEN Selección explícita de artículo en futuro flujo UI, THE telemetry design SHALL definir `product_selected` con envelope común y allowlist cerrado.

Justificación: La selección no conduce siempre a una operación; decisión: Simplificar transición a movimientos. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-008 — order_started

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`. Estado componente: PROPOSED; instrumentación: PROPOSED.

WHEN Inicio explícito de flujo lógico de entrada/salida; no equivale a pedido comercial, THE telemetry design SHALL definir `order_started` con envelope común y allowlist cerrado.

Justificación: Operaciones inicia flujos que no completa; decisión: Mejorar confirmación y validación. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-009 — order_abandoned

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`. Estado componente: PROPOSED; instrumentación: PROPOSED.

WHEN Procesador cierra flujo sin terminal tras 30 min de inactividad propuesta, THE telemetry design SHALL definir `order_abandoned` con envelope común y allowlist cerrado.

Justificación: Fricciones generan abandono; decisión: Revisar UX del paso más abandonado. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-010 — inventory_adjustment_completed

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`. Estado componente: PLANNED; instrumentación: PROPOSED.

WHEN Commit de ajuste materializado como movimiento, THE telemetry design SHALL definir `inventory_adjustment_completed` con envelope común y allowlist cerrado.

Justificación: Muchos ajustes indican errores de registro; decisión: Reconciliar procesos de conteo. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-011 — inventory_threshold_cleared

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`. Estado componente: PROPOSED; instrumentación: PROPOSED.

WHEN Cruce de < a >= umbral comparable tras movimiento, THE telemetry design SHALL definir `inventory_threshold_cleared` con envelope común y allowlist cerrado.

Justificación: Alertas permanecen activas tras reposición; decisión: Cerrar episodio de reorden. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-012 — inventory_reconciliation_failed

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2`. Estado componente: PROPOSED; instrumentación: PROPOSED.

WHEN Verificador encuentra proyección distinta a suma de movimientos comparables, THE telemetry design SHALL definir `inventory_reconciliation_failed` con envelope común y allowlist cerrado.

Justificación: Una futura proyección puede divergir; decisión: Reconstruir proyección y suspender su uso. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-013 — authentication_failed

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `backend/app/auth/dependencies.py:get_current_actor; backend/app/auth/security.py:decode_access_token`. Estado componente: IMPLEMENTED; instrumentación: PROPOSED.

WHEN Dependencia rechaza credenciales; código reducido, sin error JWT literal, THE telemetry design SHALL definir `authentication_failed` con envelope común y allowlist cerrado.

Justificación: Aumentan fallos de identidad; decisión: Investigar abuso o configuración. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-014 — authentication_succeeded

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `backend/app/auth/dependencies.py:get_current_actor; backend/app/auth/security.py:decode_access_token`. Estado componente: IMPLEMENTED; instrumentación: PROPOSED.

WHEN Primera validación satisfactoria de identidad en una sesión conceptual; no login real, THE telemetry design SHALL definir `authentication_succeeded` con envelope común y allowlist cerrado.

Justificación: No se conoce uso autenticado; decisión: Dimensionar soporte al operador. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-015 — session_started

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `uis/backoffice/operational-incidents/app.js; frontend/app/internal/incident-history/workspace.js`. Estado componente: PARTIAL; instrumentación: PROPOSED.

WHEN UI conecta credenciales en memoria y primera lectura autorizada confirma acceso, THE telemetry design SHALL definir `session_started` con envelope común y allowlist cerrado.

Justificación: Uso de herramientas cambia por semana; decisión: Planificar capacidad de soporte. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-016 — session_ended

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `frontend/app/internal/incident-history/workspace.js; README del backoffice`. Estado componente: PARTIAL; instrumentación: PROPOSED.

WHEN Desconexión explícita de UI; cierre del navegador es desconocido, no logout servidor, THE telemetry design SHALL definir `session_ended` con envelope común y allowlist cerrado.

Justificación: Sesiones terminan por causas distintas; decisión: Mejorar mensajes de reconexión. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-017 — authorization_denied

Tipo EARS: Event-driven. Prioridad: P0. Fuente: IDENTIFIED_OPPORTUNITY; `backend/app/auth/dependencies.py; backend/app/auth/policies.py`. Estado componente: IMPLEMENTED; instrumentación: PROPOSED.

WHEN Dependencia o política devuelve denegación de capacidad/ámbito, THE telemetry design SHALL definir `authorization_denied` con envelope común y allowlist cerrado.

Justificación: La matriz de permisos provoca bloqueos o abuso; decisión: Revisar alcance con Tecnología y Cumplimiento. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-018 — navigation_viewed

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `uis/backoffice/operational-incidents/app.js; uis/backoffice/management/index.html; frontend/app/page.js`. Estado componente: IMPLEMENTED; instrumentación: PROPOSED.

WHEN Vista lógica cambia y queda visible; excluir UUID y query string, THE telemetry design SHALL definir `navigation_viewed` con envelope común y allowlist cerrado.

Justificación: Algunas secciones concentran uso; decisión: Priorizar mejoras de navegación. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-019 — frontend_timing_measured

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `frontend/app/layout.js; audit/README.md (evidencia de auditoría, no RUM)`. Estado componente: PROPOSED; instrumentación: PROPOSED.

WHEN API Performance reporta métrica completa de navegación visible, THE telemetry design SHALL definir `frontend_timing_measured` con envelope común y allowlist cerrado.

Justificación: La latencia perjudica al operador; decisión: Optimizar recursos y respuesta. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-020 — api_request_completed

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `backend/app/main.py; routers montados`. Estado componente: IMPLEMENTED; instrumentación: PROPOSED.

WHEN Respuesta ASGI finaliza; middleware futuro calcula duración monotónica, THE telemetry design SHALL definir `api_request_completed` con envelope común y allowlist cerrado.

Justificación: Hay rutas lentas o fallidas; decisión: Priorizar optimización de rutas. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-021 — application_error_observed

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `backend/app/main.py; frontend/app/internal/incident-history/lazy-error-boundary.js`. Estado componente: PARTIAL; instrumentación: PROPOSED.

WHEN Excepción no controlada clasificada en frontera; no duplicar HTTP esperado, THE telemetry design SHALL definir `application_error_observed` con envelope común y allowlist cerrado.

Justificación: Errores repetidos interrumpen flujos; decisión: Priorizar corrección por componente. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-022 — catalog_cache_observed

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `backend/app/catalogs/cache.py:CatalogCache`. Estado componente: IMPLEMENTED; instrumentación: PROPOSED.

WHEN Corte agregado de contadores por worker cada 5 min, THE telemetry design SHALL definir `catalog_cache_observed` con envelope común y allowlist cerrado.

Justificación: Caché puede evadir o fallar demasiado; decisión: Ajustar límites tras benchmark. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-023 — service_health_checked

Tipo EARS: Event-driven. Prioridad: P0. Fuente: MANDATORY_BRIEFING; `CONTEXT.md Tecnología; backend/app/main.py:health,status`. Estado componente: PARTIAL; instrumentación: PROPOSED.

WHEN Sonda futura invoca /health o /status con timeout, THE telemetry design SHALL definir `service_health_checked` con envelope común y allowlist cerrado.

Justificación: Fallos se detectan actualmente por llamadas; decisión: Abrir incidente tras fallo sostenido. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-024 — alert_triggered

Tipo EARS: Event-driven. Prioridad: P0. Fuente: MANDATORY_BRIEFING; `CONTEXT.md Tecnología y Dirección`. Estado componente: PLANNED; instrumentación: PROPOSED.

WHEN Regla aprobada cruza umbral y crea episodio, THE telemetry design SHALL definir `alert_triggered` con envelope común y allowlist cerrado.

Justificación: No existe reacción proactiva sistemática; decisión: Asignar respuesta a Tecnología. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-025 — notification_delivery_completed

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `CONTEXT.md Experiencia del Paciente y Acceso; no integración en código`. Estado componente: PROPOSED; instrumentación: PROPOSED.

WHEN Proveedor futuro confirma entrega o fallo terminal sin destinatario, THE telemetry design SHALL definir `notification_delivery_completed` con envelope común y allowlist cerrado.

Justificación: Alertas no llegan siempre a responsables; decisión: Reintentar o cambiar canal autorizado. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-026 — job_run_completed

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `CONTEXT.md Tecnología; data/pipelines/README.md`. Estado componente: PROPOSED; instrumentación: PROPOSED.

WHEN Job futuro termina con resultado o timeout, THE telemetry design SHALL definir `job_run_completed` con envelope común y allowlist cerrado.

Justificación: Automatización puede fallar sin visibilidad; decisión: Reprocesar lote fallido. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-027 — data_integrity_checked

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `backend/app/reference_data/validation.py; backend/app/management/router.py`. Estado componente: PARTIAL; instrumentación: PROPOSED.

WHEN Validador de referencias o futura comprobación completa un resultado, THE telemetry design SHALL definir `data_integrity_checked` con envelope común y allowlist cerrado.

Justificación: Referencias incoherentes bloquean incidencias; decisión: Corregir maestros con propietario. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-028 — incident_created

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `backend/app/incidents/router.py; backend/app/incidents/history.py`. Estado componente: IMPLEMENTED; instrumentación: PROPOSED.

WHEN Commit de incidencia creada, THE telemetry design SHALL definir `incident_created` con envelope común y allowlist cerrado.

Justificación: Crece el volumen de interrupciones; decisión: Repartir trabajo de Tecnología. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-029 — incident_transitioned

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `backend/app/incidents/router.py; backend/app/incidents/history.py`. Estado componente: IMPLEMENTED; instrumentación: PROPOSED.

WHEN Commit de transición autorizada, THE telemetry design SHALL definir `incident_transitioned` con envelope común y allowlist cerrado.

Justificación: Las incidencias tardan en resolverse; decisión: Revisar cuellos de botella. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-030 — incident_assigned

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `backend/app/incidents/router.py; backend/app/incidents/history.py`. Estado componente: IMPLEMENTED; instrumentación: PROPOSED.

WHEN Commit de asignación autorizada, THE telemetry design SHALL definir `incident_assigned` con envelope común y allowlist cerrado.

Justificación: Cambios de área retrasan atención; decisión: Clarificar propiedad operativa. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-031 — management_mutation_completed

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `backend/app/management/router.py; backend/app/management/service.py`. Estado componente: IMPLEMENTED; instrumentación: PROPOSED.

WHEN Commit de mutación con ManagementAuditEvent persistido, THE telemetry design SHALL definir `management_mutation_completed` con envelope común y allowlist cerrado.

Justificación: Maestros cambian con impacto histórico; decisión: Revisar cambios con auditoría autorizada. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-032 — audit_accessed

Tipo EARS: Event-driven. Prioridad: P0. Fuente: MANDATORY_BRIEFING; `CONTEXT.md Cumplimiento; backend/app/incidents/router.py:incident_audit; backend/app/management/router.py:list_management_audit_events`. Estado componente: PARTIAL; instrumentación: PROPOSED.

WHEN Consulta autorizada de auditoría finaliza, sin exportar snapshots, THE telemetry design SHALL definir `audit_accessed` con envelope común y allowlist cerrado.

Justificación: La auditoría se consulta sin monitorización transversal; decisión: Revisar patrones de acceso autorizado. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-033 — telemetry_contract_rejected

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `Diseño conceptual de este hito`. Estado componente: PROPOSED; instrumentación: PROPOSED.

WHEN Validador futuro rechaza envelope o propiedades; diagnóstico sin payload, THE telemetry design SHALL definir `telemetry_contract_rejected` con envelope común y allowlist cerrado.

Justificación: Productores envían contratos incompatibles; decisión: Detener versión defectuosa del productor. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-034 — telemetry_delivery_failed

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `Diseño conceptual de este hito`. Estado componente: PROPOSED; instrumentación: PROPOSED.

WHEN Productor futuro agota reintentos acotados, THE telemetry design SHALL definir `telemetry_delivery_failed` con envelope común y allowlist cerrado.

Justificación: Pérdidas producen métricas falsas; decisión: Restaurar colector y marcar hueco. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-035 — appointment_period_aggregated

Tipo EARS: Event-driven. Prioridad: P1. Fuente: MANDATORY_BRIEFING; `CONTEXT.md Experiencia del Paciente, Facturación, Operaciones, Personas y Dirección; sin módulos integrados`. Estado componente: PLANNED; instrumentación: PROPOSED.

WHEN Adaptador local aprobado cierra día con totales reconciliados, THE telemetry design SHALL definir `appointment_period_aggregated` con envelope común y allowlist cerrado.

Justificación: No-shows del 22% y reservas requieren seguimiento; decisión: Priorizar recordatorios y capacidad. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-036 — billing_period_aggregated

Tipo EARS: Event-driven. Prioridad: P1. Fuente: MANDATORY_BRIEFING; `CONTEXT.md Experiencia del Paciente, Facturación, Operaciones, Personas y Dirección; sin módulos integrados`. Estado componente: PLANNED; instrumentación: PROPOSED.

WHEN Adaptador local cierra periodo contable con cohorte reconciliada, THE telemetry design SHALL definir `billing_period_aggregated` con envelope común y allowlist cerrado.

Justificación: Rechazo del 14% y cobros carecen de visión unificada; decisión: Corregir patrones de rechazo y seguimiento. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-037 — experience_period_aggregated

Tipo EARS: Event-driven. Prioridad: P1. Fuente: MANDATORY_BRIEFING; `CONTEXT.md Experiencia del Paciente, Facturación, Operaciones, Personas y Dirección; sin módulos integrados`. Estado componente: PLANNED; instrumentación: PROPOSED.

WHEN Encuestas locales aprobadas cierran día con agregado protegido, THE telemetry design SHALL definir `experience_period_aggregated` con envelope común y allowlist cerrado.

Justificación: Satisfacción no es visible por sede; decisión: Priorizar mejora de acceso. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-038 — workforce_period_aggregated

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `CONTEXT.md Experiencia del Paciente, Facturación, Operaciones, Personas y Dirección; sin módulos integrados`. Estado componente: PLANNED; instrumentación: PROPOSED.

WHEN Fuente RRHH autorizada produce cohorte semanal agregada, THE telemetry design SHALL definir `workforce_period_aggregated` con envelope común y allowlist cerrado.

Justificación: Contratación tarda 47 días y CME se registra manualmente; decisión: Reforzar contratación y formación. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-FR-039 — clinical_workload_aggregated

Tipo EARS: Event-driven. Prioridad: P1. Fuente: IDENTIFIED_OPPORTUNITY; `CONTEXT.md Experiencia del Paciente, Facturación, Operaciones, Personas y Dirección; sin módulos integrados`. Estado componente: PLANNED; instrumentación: PROPOSED.

WHEN Fuente clínica autorizada produce sumas diarias sin notas ni personas, THE telemetry design SHALL definir `clinical_workload_aggregated` con envelope común y allowlist cerrado.

Justificación: Documentación consume 35 minutos diarios; decisión: Evaluar asistencia documental con aprobación. Aceptación: existe exactamente un contrato con este nombre, disparador y métrica; ejemplo sintético válido; campo extra y tipo incorrecto rechazados. Dependencias: TEL-DATA-001, TEL-SEC-001; aprobación del componente si PLANNED/PROPOSED. Validación: V01–V05 y revisión de catálogo.

## TEL-DATA-001

Título: Envelope y allowlists. Tipo EARS: Ubiquitous. Prioridad: P0. Fuente: prompt §§4–7 y AGENTS.md; objetivos numéricos son PROPOSED.

THE telemetry design SHALL exigir los ocho campos del envelope y un allowlist estricto en cada evento.

Justificación: integridad, seguridad y decisiones fiables. Aceptación: JSON rechaza campo extra, campo ausente y versión distinta; V01–V03. Dependencias: baseline y aprobación de Tecnología/Cumplimiento antes de implementación. Estado actual: PROPOSED. Método: validación de contratos y revisión documental.

## TEL-DATA-002

Título: Deduplicación e inmutabilidad. Tipo EARS: Event-driven. Prioridad: P0. Fuente: prompt §§4–7 y AGENTS.md; objetivos numéricos son PROPOSED.

WHEN un productor reintenta entrega, THE telemetry design SHALL conservar eventId, timestamp y contenido inmutable.

Justificación: integridad, seguridad y decisiones fiables. Aceptación: Mismo eventId deduplicado por jurisdicción y versión; V06 revisión conceptual. Dependencias: baseline y aprobación de Tecnología/Cumplimiento antes de implementación. Estado actual: PROPOSED. Método: validación de contratos y revisión documental.

## TEL-DATA-003

Título: Calidad temporal. Tipo EARS: Unwanted behavior. Prioridad: P0. Fuente: prompt §§4–7 y AGENTS.md; objetivos numéricos son PROPOSED.

IF timestamp está fuera de tolerancia o un agregado tiene periodo invertido, THEN THE telemetry design SHALL ponerlo en cuarentena sin payload en diagnósticos.

Justificación: integridad, seguridad y decisiones fiables. Aceptación: Zona horaria exigida; reglas semánticas enumeradas y casos límite revisados; V03,V06. Dependencias: baseline y aprobación de Tecnología/Cumplimiento antes de implementación. Estado actual: PROPOSED. Método: validación de contratos y revisión documental.

## TEL-SEC-001

Título: Exclusión de PHI y secretos. Tipo EARS: Unwanted behavior. Prioridad: P0. Fuente: prompt §§4–7 y AGENTS.md; objetivos numéricos son PROPOSED.

IF un dato contiene PHI, secreto o texto libre, THEN THE telemetry design SHALL excluirlo antes de salir del productor.

Justificación: integridad, seguridad y decisiones fiables. Aceptación: No cuerpos, URLs, JWT, snapshots ni identificadores de pacientes en contratos; V05. Dependencias: baseline y aprobación de Tecnología/Cumplimiento antes de implementación. Estado actual: PROPOSED. Método: validación de contratos y revisión documental.

## TEL-SEC-002

Título: Separación jurisdiccional. Tipo EARS: State-driven. Prioridad: P0. Fuente: prompt §§4–7 y AGENTS.md; objetivos numéricos son PROPOSED.

WHILE una jurisdicción no está validada, THE telemetry design SHALL impedir la exportación del evento.

Justificación: integridad, seguridad y decisiones fiables. Aceptación: US/UK separados; alcance inferido no aceptado; V06. Dependencias: baseline y aprobación de Tecnología/Cumplimiento antes de implementación. Estado actual: PROPOSED. Método: validación de contratos y revisión documental.

## TEL-SEC-003

Título: Seudonimización. Tipo EARS: Optional feature. Prioridad: P0. Fuente: prompt §§4–7 y AGENTS.md; objetivos numéricos son PROPOSED.

WHERE existe identidad autenticada, THE telemetry design SHALL usar seudónimo local y restringir su resolución.

Justificación: integridad, seguridad y decisiones fiables. Aceptación: Sin JWT sub literal; eventos anónimos con userId null; revisión Claire pendiente antes de instrumentar; V05,V06. Dependencias: baseline y aprobación de Tecnología/Cumplimiento antes de implementación. Estado actual: PROPOSED. Método: validación de contratos y revisión documental.

## TEL-SEC-004

Título: Gobernanza y mínimo privilegio. Tipo EARS: Ubiquitous. Prioridad: P0. Fuente: prompt §§4–7 y AGENTS.md; objetivos numéricos son PROPOSED.

THE telemetry design SHALL separar autorización de telemetría y requerir revisión de Claire Whitfield antes de aplicar retención, auditoría o transferencias.

Justificación: integridad, seguridad y decisiones fiables. Aceptación: Fallo analítico no permite bypass; decisiones pendientes identificadas; V06. Dependencias: baseline y aprobación de Tecnología/Cumplimiento antes de implementación. Estado actual: PROPOSED. Método: validación de contratos y revisión documental.

## TEL-NFR-001

Título: Latencia y cadencia propuestas. Tipo EARS: Ubiquitous. Prioridad: P0. Fuente: prompt §§4–7 y AGENTS.md; objetivos numéricos son PROPOSED.

THE telemetry design SHALL proponer entrega STREAM p95 <= 10 s y BATCH cada 15 min, sujetos a medición y aprobación.

Justificación: integridad, seguridad y decisiones fiables. Aceptación: Objetivos identificados como propuesta; no SLA empresarial inventado; V06. Dependencias: baseline y aprobación de Tecnología/Cumplimiento antes de implementación. Estado actual: PROPOSED. Método: validación de contratos y revisión documental.

## TEL-NFR-002

Título: Resiliencia y fallos de entrega. Tipo EARS: Unwanted behavior. Prioridad: P0. Fuente: prompt §§4–7 y AGENTS.md; objetivos numéricos son PROPOSED.

IF colección no está disponible, THEN THE telemetry design SHALL limitar reintentos y memoria sin bloquear lecturas operativas.

Justificación: integridad, seguridad y decisiones fiables. Aceptación: Backoff, buffer, pérdida y outbox crítico definidos; V06. Dependencias: baseline y aprobación de Tecnología/Cumplimiento antes de implementación. Estado actual: PROPOSED. Método: validación de contratos y revisión documental.

## TEL-NFR-003

Título: Coste, volumen y cardinalidad. Tipo EARS: Ubiquitous. Prioridad: P0. Fuente: prompt §§4–7 y AGENTS.md; objetivos numéricos son PROPOSED.

THE telemetry design SHALL definir presupuesto, sampling y cardinalidad antes de habilitar productores.

Justificación: integridad, seguridad y decisiones fiables. Aceptación: Fórmula de volumen y eventos íntegros enumerados; V06. Dependencias: baseline y aprobación de Tecnología/Cumplimiento antes de implementación. Estado actual: PROPOSED. Método: validación de contratos y revisión documental.

## TEL-NFR-004

Título: Evolución de contratos. Tipo EARS: Event-driven. Prioridad: P0. Fuente: prompt §§4–7 y AGENTS.md; objetivos numéricos son PROPOSED.

WHEN cambia un contrato, THE telemetry design SHALL publicar versión nueva con pruebas de compatibilidad antes de promoverla.

Justificación: integridad, seguridad y decisiones fiables. Aceptación: Allowlist no evoluciona silenciosamente; V03,V06. Dependencias: baseline y aprobación de Tecnología/Cumplimiento antes de implementación. Estado actual: PROPOSED. Método: validación de contratos y revisión documental.

## TEL-NFR-005

Título: Calidad de KPIs. Tipo EARS: Optional feature. Prioridad: P0. Fuente: prompt §§4–7 y AGENTS.md; objetivos numéricos son PROPOSED.

WHERE un KPI tiene fuente aprobada, THE telemetry design SHALL definir cohorte, periodo, nulos y denominador antes de publicar resultados.

Justificación: integridad, seguridad y decisiones fiables. Aceptación: Agregados sin fuente se muestran unavailable y nunca cero; V06. Dependencias: baseline y aprobación de Tecnología/Cumplimiento antes de implementación. Estado actual: PROPOSED. Método: validación de contratos y revisión documental.

Quality Gate 1: cada evento posee requisito y fuente; controles cubren envelope, correlación, calidad, coste, resiliencia y privacidad.
