# TASKS — Ejecución futura de serialización

**Estado:** TASK-SER-001–017 completadas para el entorno sintético aprobado. Véase cierre final y límites; el baseline anterior se conserva como histórico.
Referencias: [SPEC](./spec.md), [PLAN](./plan.md), [auditoría técnica](../../../docs/serialization-audit.md).

Cada tarea detalla criterios, pruebas y evidencia que se deben adjuntar al cerrarla. IDs de prueba `T-SER-*` son futuros. `uv 0.8.22` y las dependencias bloqueadas se instalaron en `/tmp`; el entorno del repositorio y el lockfile no se modificaron.

## Grupo A — Preparación y auditoría

- [x] TASK-SER-001 — Preparar entorno y línea base reproducible
  - **Evidencia de cierre/seguimiento (2026-10-31):** La ejecución actual con Podman y PostgreSQL local sintética supera la suite completa: 74 passed in 1.57s. El build conserva uv 0.8.22 y el lockfile; Python observado en la imagen: 3.12.13.
  - **Objetivo:** habilitar verificaciones sin cambiar versiones ni datos de aplicación.
  - **Requisitos:** SER-TEST-001, SER-COMP-001.
  - **Archivos previstos:** `backend/README.md`, `backend/pyproject.toml`, `backend/uv.lock`, tests (sólo si resultan necesarios); no editar dependencias en esta tarea sin autorización.
  - **Dependencias:** aprobación de implementación; entorno Python 3.12, `uv` fijado en Dockerfile y PostgreSQL sintético disponible para integración.
  - **Acciones:** verificar versión de Python/uv/lock; ejecutar `uv sync --frozen`; ejecutar primero `uv run --no-sync pytest tests/test_status.py -q`; registrar disponibilidad de DB; ejecutar suite integración sólo en DB local sintética autorizada.
  - **Aceptación:** comandos, versiones y resultado quedan registrados; no se usa DB con datos ajenos ni se modifica lockfile.
  - **Tests:** status test; integración sólo con aprobación y entorno adecuado.
  - **Evidencia:** Python 3.12.16, `uv 0.8.22`, `uv sync --frozen` con entorno/caché en `/tmp`; test_status del snapshot `HEAD` previo pasó 3 tests. No había Docker/Podman disponible, por lo que la suite con PostgreSQL no se ejecutó.

- [x] TASK-SER-002 — Fijar OpenAPI y consumidores de referencia
  - **Objetivo:** producir baseline ejecutado de los contratos antes de cambios.
  - **Requisitos:** SER-FR-001, SER-COMP-001, SER-TEST-001.
  - **Archivos previstos:** auditoría y artefacto de OpenAPI de prueba no sensible; `packages/shared/types/management.ts` sólo como fuente comparada.
  - **Dependencias:** TASK-SER-001.
  - **Acciones:** obtener `/openapi.json`; contrastar los 28 handlers, códigos, request/response, defaults de Docs y consumidores locales; pedir confirmación de clientes externos sin inferir su ausencia.
  - **Aceptación:** inventario coincide con la app ejecutada y cada cambio propuesto tiene consumidor/compatibilidad anotados.
  - **Tests:** `T-SER-OPENAPI-001`, `T-SER-COMPAT-001`.
  - **Evidencia:** OpenAPI previo y actual generados: 28 operaciones cada uno. SHA-256 canónico previo `dfc2177fc03e2cdc127f8584635790cb4ae7413abc68bdc20bd3ad806737eaa0`; actual `74b01908b230fdc84c5498f44395c75341ea1a894b07c3db64b32a6bb4672850`. Mapa local de frontends/tests revisado; el responsable confirma el 2026-10-31 que no hay consumidores externos conocidos por ahora y que health se usa internamente para el estado de contenedores. Ver discrepancia de `/health` y `/status` en la auditoría.

- [x] TASK-SER-003 — Revisar clasificación con Compliance
  - **Evidencia de cierre/seguimiento (2026-10-31):** El responsable aprueba explícitamente la política específica propuesta y autoriza continuar para datos sintéticos. Política audit-output-v1 detallada en docs/serialization-audit.md: IDs/referencias/timestamps conservados, texto libre redactado, claves no autorizadas excluidas y persistencia intacta. TASK-SER-003 queda completada para este alcance.
  - **Objetivo:** decidir clasificación de actor IDs y payloads de auditoría antes de restringirlos.
  - **Requisitos:** SER-SEC-003, SER-SEC-004, SER-COMP-001.
  - **Archivos previstos:** schemas/servicios audit sólo tras aprobación; ninguna modificación a `memory-bank` o Rules está incluida.
  - **Dependencias:** TASK-SER-002; aprobación de Claire Whitfield y Gobierno del Dato.
  - **Acciones:** clasificar cada clave de `before_data`/`after_data`, reason y actor IDs; decidir output vs storage, redacción, acceso y compatibilidad; no usar PHI real.
  - **Aceptación:** decisión escrita y aprobada; sin ella, cambios audit quedan bloqueados.
  - **Tests:** casos sintéticos definidos como `T-SER-AUDIT-001` y `T-SER-ACCESS-001`.
  - **Evidencia:** matriz de campos y aprobación; no declarar cumplimiento legal.

## Grupo B — Seguridad

- [x] TASK-SER-004 — Verificar contrato JWT de desarrollo
  - **Evidencia de cierre/seguimiento (2026-10-31):** La suite completa actual incluye test_auth.py y supera 74 pruebas sin fallos ni omisiones; el fallo histórico por falta de DATABASE_URL queda resuelto.
  - **Objetivo:** demostrar que el único flujo de token conserva su propósito limitado.
  - **Requisitos:** SER-SEC-001, SER-SEC-002.
  - **Archivos previstos:** `backend/app/auth/router.py`, `backend/tests/test_auth.py`.
  - **Dependencias:** TASK-SER-001/002.
  - **Acciones:** comprobar `TokenRequest`/`TokenResponse`, 201 en entorno permitido, 404 fuera de dev/test, y no reflejar actor/role/area en respuesta. No crear flujos de email/password inexistentes.
  - **Aceptación:** sólo `access_token` y `token_type` en respuesta exitosa; sin secretos internos; producción sigue sin endpoint.
  - **Tests:** test actual de producción más `T-SER-SECRET-001`.
  - **Evidencia:** dos tests enfocados de producción pasaron (`self_issued_tokens_are_disabled_outside_development` y `token_endpoint_is_not_exposed_in_production`). Petición sintética en `development`: 201, claves exactas `access_token`/`token_type`, tipo `bearer`; el JWT no se imprimió. El módulo `test_auth.py` completo dio 13 passed y 1 fallo en el test de rutas de incidencias por falta de `DATABASE_URL`; esa ruta no forma parte del endpoint de emisión y queda pendiente validar con DB.

- [x] TASK-SER-005 — Hacer explícita la política de atributos extra
  - **Evidencia de cierre/seguimiento (2026-10-31):** Los 13 casos de política de entrada y los workflows HTTP de permisos se ejecutaron dentro de la suite PostgreSQL actual: 74 passed in 1.57s. Se conserva ignore/forbid y no se ampliaron permisos.
  - **Objetivo:** documentar y probar rechazo/ignorancia de campos no declarados y restricciones por rol.
  - **Requisitos:** SER-FR-005, SER-SEC-005.
  - **Archivos previstos:** `backend/app/auth/router.py`, `backend/app/compliance/router.py`, `backend/app/incidents/schemas.py`, `backend/app/management/schemas.py`, tests HTTP.
  - **Dependencias:** TASK-SER-002; decisión de compatibilidad sobre default actual `ignore`.
  - **Acciones:** elegir explícitamente `ignore` (compatible con estado actual) o `forbid` tras revisar clientes; mantener rechazo 403 de campos conocidos no permitidos por rol; comprobar no hay asignación de server-owned attrs.
  - **Aceptación:** comportamiento documentado por modelo de escritura; payload extra produce resultado determinista y no cambia ORM; ninguna ampliación de permisos.
  - **Tests:** `T-SER-INPUT-001`, `T-SER-ACCESS-001` con campos sintéticos.
  - **Evidencia:** pruebas para cada familia de schemas y lista de posibles breaking changes.
  - **Avance (2026-10-31):** `extra="ignore"` explícito en requests que usaban el default; se conservó `extra="forbid"` en los modelos Management que ya lo declaraban. `backend/tests/test_input_schema_policy.py`: 13 passed con payloads sintéticos.
  - **Pendiente histórico, resuelto por la evidencia de cierre anterior:** ejecutar las verificaciones HTTP 403 de `test_http_authorization.py::test_http_authorization_enforces_area_capability_and_audit_access` y `test_incident_workflows.py::test_incident_update_transition_history_and_audit`. Requieren una PostgreSQL aislada accesible mediante `DATABASE_URL` con dialecto `postgresql+asyncpg`, `alembic upgrade head` y catálogos/referencias sintéticos requeridos por los tests. En el entorno actual no hay `DATABASE_URL` ni Podman; se comprobará en el otro entorno indicado antes de decidir si hay bloqueo. No se modificaron permisos.

- [x] TASK-SER-011 — Acotar respuestas de auditoría
  - **Evidencia de cierre (2026-10-31):** política audit-output-v1 aplicada mediante proyección centralizada, TypeAdapters Pydantic por evento y validators de modelos de respuesta. Incluye auditoría Incident/Management y motivos de historiales. Tests unitarios y HTTP PostgreSQL verifican contenido permitido, exclusión, texto libre, fechas históricas, permisos, referencias y lectura SQL sin cambios de snapshots/motivos. Suite: 117 passed in 1.61s; JSON Schemas de las cuatro respuestas iguales a HEAD be2bad5; 28 operaciones.
  - **Objetivo:** establecer proyección segura para snapshots una vez exista aprobación de Compliance.
  - **Requisitos:** SER-SEC-001, SER-SEC-003, SER-SEC-004, SER-FR-002.
  - **Archivos previstos:** `backend/app/incidents/schemas.py`, `backend/app/management/schemas.py`, routers audit, servicio/modelos sólo si el diseño aprobado afecta escritura.
  - **Dependencias:** TASK-SER-003 es bloqueante. Sin aprobación no cambiar contenido persistido, permisos ni retención.
  - **Acciones:** traducir decisión aprobada a tipos explícitos/allowlists o redacción de salida; mantener la trazabilidad obligatoria de cambios; comparar formatos existentes y consumers; incluir descripción sensible sintética.
  - **Aceptación:** claves aprobadas visibles, claves prohibidas ausentes/redactadas, eventos históricos tratados según decisión y autorización sin cambio accidental.
  - **Tests:** `T-SER-AUDIT-001`, `T-SER-ACCESS-001`, `T-SER-SECRET-001`.
  - **Evidencia:** decisión Compliance, matriz antes/después de campos y tests sobre valores totalmente sintéticos.

## Grupo C — Serialización por dominio

- [x] TASK-SER-006 — Tipar health y status
  - **Objetivo:** cerrar las dos rutas sin contrato de salida completo.
  - **Requisitos:** SER-FR-001, SER-SEC-001, SER-TEST-001.
  - **Archivos previstos:** `backend/app/main.py`, `backend/tests/test_status.py`.
  - **Dependencias:** TASK-SER-001/002.
  - **Acciones:** declarar esquema de `/health`, respuesta normal de `/status` y alternativa 503 en OpenAPI; conservar respuesta JSON, status codes y protección contra detalle SQL.
  - **Aceptación:** OpenAPI describe 200 y 503; runtime conserva `{"status":"ok"}` y contratos de status actuales.
  - **Tests:** `T-SER-HEALTH-001` para 200/503 y no filtración; suite test_status.
  - **Evidencia:** OpenAPI del snapshot previo y del código actual; ambos con 28 operaciones. El actual declara `HealthResponse`, `StatusConnectedResponse` y `StatusUnavailableResponse`. `test_status.py`: 3 passed antes y 5 passed después, sin PostgreSQL. Los payloads 200/503 y los códigos existentes se mantienen.

- [x] TASK-SER-007 — Separar contratos de incidencia
  - **Evidencia de cierre/seguimiento (2026-10-31):** IncidentResponse deriva directamente de BaseModel y conserva su JSON Schema idéntico al de HEAD be2bad5. Las cinco rutas mantienen contrato y códigos; pruebas de proyección ORM, OpenAPI y workflows superadas en la suite completa.
  - **Objetivo:** desacoplar salida de incidencia del esquema de creación manteniendo el contrato publicado.
  - **Requisitos:** SER-FR-002, SER-FR-005, SER-FR-006, SER-SEC-003, SER-COMP-001.
  - **Archivos previstos:** `backend/app/incidents/schemas.py`, `backend/app/incidents/router.py`, tests HTTP/workflows.
  - **Dependencias:** TASK-SER-002/003 y aprobación de compatibility para actor IDs.
  - **Acciones:** crear Detail/Response independiente y usarlo en EP-006, EP-009–EP-012; mantener `IncidentListItem`; identificar propiedades server-managed y referencias por UUID; no alterar filtros, permisos ni workflow.
  - **Aceptación:** salidas de POST/GET/PATCH/transición/asignación coinciden campo a campo con contrato aprobado; entrada no controla reporter/status/fechas/IDs de servidor.
  - **Tests:** `T-SER-INC`, `T-SER-WRITE-001`, `T-SER-ORM-001` y workflows.
  - **Evidencia:** OpenAPI diff, tests de cinco endpoints y consumer map.

- [x] TASK-SER-008 — Confirmar proyección de listados
  - **Evidencia de cierre/seguimiento (2026-10-31):** Las pruebas HTTP de catálogo y las cuatro familias de referencias verifican claves exactas y wrappers items/total; paginación comprobada con offset=1, limit=1. Suite completa: 74 passed in 1.57s.
  - **Objetivo:** registrar `ListItem` específico para las listas administrativas sin romper campos vigentes.
  - **Requisitos:** SER-FR-003, SER-FR-004, SER-COMP-001.
  - **Archivos previstos:** `backend/app/management/schemas.py`, router Management y tests; `backend/app/incidents/schemas.py` sólo si se detecta regresión.
  - **Dependencias:** TASK-SER-002 y consumer/contrato externo confirmado.
  - **Acciones:** separar tipos nominales de EP-017/EP-021; preservar todas las claves actuales hasta aprobación para reducirlas; confirmar relaciones como IDs, no carga implícita.
  - **Aceptación:** shape/códigos/paginación iguales al contrato aprobado; ningún campo quitado por inferencia desde UI.
  - **Tests:** `T-SER-LIST-001`, casos para cada `resource`, comparación de OpenAPI.
  - **Evidencia:** schema de lista, snapshot de contrato y resultado tests.
  - **Avance (2026-10-31):** añadidos `CatalogValueListItem` y `ReferenceValueListItem`; propiedades y requireds idénticos a los schemas de detalle, wrappers `{items,total}` sin cambios. `backend/tests/test_management_openapi.py`: 2 passed. OpenAPI conserva 28 operaciones; hash actual `85853ecb622ad4ef412e0977d62db67c3193dade22fa8db1c5d150665336214f`.
  - **Pendiente histórico, resuelto por la evidencia de cierre anterior:** validar payloads runtime de catálogo y referencia con PostgreSQL aislada mediante `test_http_authorization.py::test_admin_manages_catalog_values_with_audit_and_no_physical_delete` y `test_http_authorization.py::test_admin_manages_reference_data_without_invalidating_history`; requiere `DATABASE_URL`, migraciones y seeds sintéticos.

- [x] TASK-SER-009 — Separar contratos de ComplianceReview
  - **Evidencia de cierre/seguimiento (2026-10-31):** ComplianceReviewRead deriva directamente de BaseModel y conserva su JSON Schema idéntico al de HEAD be2bad5. Las tres rutas mantienen contrato y permisos; lifecycle, proyección ORM y OpenAPI superados en la suite completa.
  - **Objetivo:** diferenciar input create/update de response read.
  - **Requisitos:** SER-FR-005, SER-FR-006, SER-SEC-003, SER-COMP-001.
  - **Archivos previstos:** `backend/app/compliance/router.py`, schemas/modelos y `backend/tests/test_http_authorization.py`.
  - **Dependencias:** TASK-SER-002/003; campos `created_by` revisados.
  - **Acciones:** crear respuesta independiente y aplicarla a EP-003–EP-005; preservar status, policy jurisdiccional, errores y reason semantics.
  - **Aceptación:** request no hereda de response; response mantiene sólo propiedades aprobadas; permisos no cambian.
  - **Tests:** `T-SER-COMP`, `T-SER-ACCESS-001`, ciclo de Compliance existente.
  - **Evidencia:** OpenAPI diff y tests lifecycle.

- [x] TASK-SER-010 — Formalizar respuestas Management
  - **Evidencia de cierre/seguimiento (2026-10-31):** Completada conservando contratos vigentes en el entorno no productivo aprobado. Las 11 operaciones Management tienen comprobación OpenAPI de output, input aplicable y límites de paginación. HTTP comprueba claves exactas de listados/escrituras/auditoría, paginación y filtros, cobertura UUID y rechazo 422 de id/created_by/updated_by/created_at/updated_at en PATCH de catálogo y clínica. Permisos y trazabilidad se verifican con workflows existentes. No se modificaron metadata, snapshots, schemas Management ni tipos TS sin consumidor. Suite completa: 74 passed in 1.57s; TASK-SER-011 sigue independiente y pendiente.
  - **Objetivo:** verificar campos administrativos de salida y alinear schemas sin quitar propiedades sin aprobación.
  - **Requisitos:** SER-FR-002, SER-FR-003, SER-FR-006, SER-SEC-003, SER-COMP-001.
  - **Archivos previstos:** `backend/app/management/schemas.py`, `backend/app/management/router.py`, `packages/shared/types/management.ts` sólo si hay consumidor/contrato validado, tests HTTP.
  - **Dependencias:** TASK-SER-002/003.
  - **Acciones:** revisar create/update/activation/reference/system coverage y paginados; asegurar IDs/timestamps server-managed; mantener fields/casing, role capability y `items/total`.
  - **Aceptación:** cada respuesta tiene shape probado y corresponde al OpenAPI; cualquier TS type actualizado sólo con uso comprobado.
  - **Tests:** `T-SER-MGMT`, `T-SER-LIST-001`, compatibilidad Management.
  - **Evidencia:** contrato por ruta y outputs sintéticos.

## Grupo D — Optimización

- [x] TASK-SER-012 — Medir proyecciones y consultas
  - **Objetivo:** decidir si la lectura completa de entidades en listados amerita optimización.
  - **Requisitos:** SER-NFR-001, SER-FR-003.
  - **Archivos previstos:** `backend/app/incidents/router.py`, `backend/app/management/router.py`, tests/fixtures de rendimiento sólo si la medición lo justifica.
  - **Dependencias:** TASK-SER-001/002 y forma contractual aprobada.
  - **Acciones:** capturar tamaño response, SQL statement/columnas, query count, relación loads y latencia p50/p95 con fixtures sintéticas y paginación idéntica; optimizar solamente si el dato demuestra ventaja.
  - **Aceptación:** informe antes/después; si no hay mejora relevante, documentar no-change; sin porcentajes no medidos.
  - **Tests:** `T-SER-PERF-001` o test de regresión query-count sólo con baseline estable.
  - **Evidencia:** dataset sintético y metodología reproducible.

## Grupo E — Testing

- [x] TASK-SER-013 — Añadir tests de shape y exposición
  - **Objetivo:** verificar allowlists, secretos y respuestas ORM en modelos tocados.
  - **Requisitos:** SER-FR-002, SER-FR-006, SER-SEC-001, SER-SEC-003, SER-TEST-001.
  - **Archivos previstos:** tests existentes en `backend/tests/`; preferir añadirlos en archivos actuales.
  - **Dependencias:** TASK-SER-004, TASK-SER-007/009/010/011.
  - **Acciones:** probar sólo endpoints/modelos modificados; usar datos sintéticos y asegurar que no se fuga una columna ORM añadida fuera del schema.
  - **Aceptación:** claves esperadas exactas, secretos/valores prohibidos ausentes, actor UUID sólo en rutas aprobadas.
  - **Tests:** `T-SER-SHAPE-001`, `T-SER-ORM-001`, `T-SER-SECRET-001`.
  - **Evidencia:** comandos y resultados asociados a cada endpoint ID.

- [x] TASK-SER-014 — Probar entradas y compatibilidad funcional
  - **Objetivo:** demostrar validación de escritura y mantener consumidores/semántica.
  - **Requisitos:** SER-FR-005/006, SER-SEC-005, SER-COMP-001, SER-TEST-001.
  - **Archivos previstos:** `backend/tests/test_http_authorization.py`, `test_incident_workflows.py`, `test_auth.py`, tests de catálogo/Compliance; consumers sólo con cambios aprobados.
  - **Dependencias:** TASK-SER-005/007–TASK-SER-010.
  - **Acciones:** payloads desconocidos, campos server-managed, campos restringidos por rol; comprobar 201/200/4xx, paginación y vistas locales. No cambiar errores/códigos por consistencia estética.
  - **Aceptación:** prueba de regresión demuestra contrato y comportamiento previo autorizado; diff breaking queda aprobado o no se aplica.
  - **Tests:** `T-SER-INPUT-001`, `T-SER-WRITE-001`, `T-SER-ACCESS-001`, `T-SER-COMPAT-001`.
  - **Evidencia:** resultados backend + consumer test/build pertinente.

- [x] TASK-SER-015 — Verificar OpenAPI completo
  - **Objetivo:** asegurar que OpenAPI refleja handlers, schemas y errores reales.
  - **Requisitos:** SER-FR-001, SER-COMP-001, SER-TEST-001.
  - **Archivos previstos:** `backend/tests/test_auth.py` (test OpenAPI existente) y tests actuales, sin crear excesivas carpetas.
  - **Dependencias:** TASK-SER-006–TASK-SER-010 y entorno TASK-SER-001.
  - **Acciones:** assert de métodos/rutas, requestBody, success response, schemas de error, operaciones especiales y cuatro rutas docs; visitar `/docs` si servicio disponible.
  - **Aceptación:** todos los 28 handlers aparecen; alternativas 200/201/503/errores esperados están documentadas; excepciones de docs anotadas.
  - **Tests:** `T-SER-OPENAPI-001`, `T-SER-COMPAT-001`.
  - **Evidencia:** tests pass y artefacto/resumen OpenAPI comparado.

- [x] TASK-SER-016 — Verificar tres endpoints en `/docs`
  - **Objetivo:** registrar verificación manual de auth o equivalente, lista y escritura/detalle.
  - **Requisitos:** SER-TEST-002.
  - **Archivos previstos:** evidencia de entrega autorizada; no requiere cambios de código.
  - **Dependencias:** entorno levantado, credenciales JWT sintéticas autorizadas, TASK-SER-015.
  - **Acciones:** probar `/auth/tokens` en dev o consignar que no hay perfil; probar `GET /incidents` o `/management/reference-data/{resource}`; probar creación/detalle con fixture sintética; registrar status y payload esperado/observado.
  - **Aceptación:** tres rutas documentadas con fecha, entorno, payload sin datos reales y resultado; no marcar si no se dispone del entorno.
  - **Tests:** `T-SER-MANUAL-001` (manual, no sustituye tests automáticos).
  - **Evidencia:** tabla con endpoint, status, payload sintético y observación; nunca tokens utilizables.

## Grupo F — Cierre

- [x] TASK-SER-017 — Cerrar trazabilidad y auditoría final
  - **Objetivo:** emitir inventario final y verificar Definition of Done antes de declarar fin.
  - **Requisitos:** todos los SER-FR/SEC/COMP/NFR/TEST aplicables.
  - **Archivos previstos:** `docs/serialization-audit.md`, `memory-bank/specs/serialization-audit/spec.md`, `plan.md`, `tasks.md`; no actualizar otros documentos protegidos sin autorización.
  - **Dependencias:** tareas anteriores, aprobación de Compliance pendiente resuelta, pruebas y validación de compatibilidad completadas.
  - **Acciones:** actualizar estado final endpoint por endpoint; ligar Requirement → Endpoint → Design → Task → Test → Evidence; documentar limitaciones, resultados manuales, revisiones y breaking changes; ejecutar revisión de entrega antes de commit si se solicita.
  - **Aceptación:** todo endpoint queda ✅ o con bloqueo aprobado/documentado; requisitos/tareas verificables; no se presenta BLOCKED como PASS ni se marcan requisitos implementados antes de pasar tests.
  - **Tests:** gates aprobados de `backend/tests`, OpenAPI, consumers y `/docs`.
  - **Evidencia:** diff revisado, resumen de pruebas y matriz de trazabilidad completada.

## Trazabilidad de tareas

| Requisitos | Tareas principales |
| --- | --- |
| SER-FR-001 | TASK-SER-002, 006, 015 |
| SER-FR-002/003/004 | TASK-SER-007, 008, 010, 011, 012, 013 |
| SER-FR-005/006, SER-SEC-005 | TASK-SER-005, 007, 009, 010, 014 |
| SER-SEC-001/002 | TASK-SER-004, 013 |
| SER-SEC-003/004 | TASK-SER-003, 011, 013 |
| SER-COMP-001 | TASK-SER-002, 007–010, 014–017 |
| SER-NFR-001 | TASK-SER-012 |
| SER-TEST-001 | TASK-SER-001, 013–015 |
| SER-TEST-002 | TASK-SER-016 |

## Control de implementación y commits

La implementación posterior sólo comienza tras aprobación expresa. Para cada tarea: referenciar requisito; observar baseline; cambio mínimo; tests; verificación de consumidores; evidencia; marcar completada sólo con aceptación demostrada. No modificar códigos HTTP, permisos, paginación ni semántica de error sin razón documentada y aprobación. No crear commits automáticamente; si el desarrollador los autoriza, separar auditoría/documentación, contratos de serialización, tests y cierre en cambios coherentes revisables.

## Evidencia histórica consolidada hasta 010 — 2026-10-31

Autorización expresa del responsable para sincronizar estos documentos. Comando ejecutado por el agente: `podman compose --profile test run --build --rm test`, salida 0, **74 passed in 1.57s**, PostgreSQL local con datos no productivos. Imagen test: `8e32984c05cc`. Las validaciones parciales anteriores se conservan como historial. La comparación de JSON Schemas de IncidentResponse y ComplianceReviewRead contra HEAD `be2bad5` fue idéntica; OpenAPI conserva 28 operaciones. No se ejecutó la verificación manual en `/docs`, medición de rendimiento ni cierre global.

## Política audit-output-v1 aprobada e implementada — 2026-10-31

El responsable aprueba expresamente la propuesta específica de TASK-SER-003 y autoriza continuar con TASK-SER-011 para el entorno sintético. Esta decisión sustituye el seguimiento previo que indicaba falta de política por campo; no constituye aprobación para datos reales o producción. La política completa, categorías, compatibilidad y decisiones técnicas constan en docs/serialization-audit.md.

Implementación: backend/app/audit_serialization.py y validators de AuditEventResponse, ManagementAuditEventResponse, StatusHistoryResponse y AssignmentHistoryResponse. Permisos, escritores, tablas, migraciones y retención permanecen sin cambios. Las respuestas mantienen campos/tipos generales; cambian deliberadamente valores de texto y contenido de snapshots. La redacción se señala mediante _redacted dentro del snapshot; los motivos se sustituyen por [REDACTED].

Validación actual: `podman compose --profile test run --build --rm test`, salida 0, **117 passed in 1.61s**, imagen test `bdcee65a60db`, PostgreSQL local sintética. Comparación ejecutada en imagen test: los JSON Schemas de las cuatro respuestas de auditoría/historial son idénticos a HEAD `be2bad5`; OpenAPI conserva 28 operaciones. Pruebas de lectura SQL posterior confirman snapshots y motivos originales intactos; las nuevas fixtures de integración se insertan en una transacción aislada que se revierte. Los resultados 74/63 anteriores son históricos. TASK-SER-012–017 siguen pendientes, incluida compatibilidad global y comprobación manual en /docs.

## Cierre final de TASK-SER-012–017 — 2026-10-31

Las 17 tareas quedan completadas exclusivamente para el entorno sintético aprobado. Evidencia actual: `podman compose --profile test run --build --rm test`, salida 0, **145 passed in 1.75s**, imagen `a98a68ae2ca0`; 28 operaciones y cuatro rutas especiales verificadas. OpenAPI documenta errores existentes mediante ErrorResponse sin cambiar su ejecución. Los JSON Schemas de IncidentResponse, ComplianceReviewRead y cuatro respuestas de auditoría/historial se conservaron contra HEAD be2bad5; los valores redactados siguen la política aprobada.

TASK-SER-012 registra dos rondas sin modificación funcional: incidencias p50 1,401/1,389 ms, p95 1,645/1,566 ms, 17.598 bytes; clínicas p50 0,893/0,931 ms, p95 1,147/1,295 ms, 755 bytes. Ambas rutas: 2 SELECT, 0 cargas de relaciones. No se justifica optimización; método/SQL/columnas y script reproducible en docs/serialization-measurement.py y JSON asociado. ASGI con PostgreSQL local, sin medición de concurrencia/red.

TASK-SER-013–015: shapes/extras/roles/históricos/persistencia, 28 rutas/requestBody/respuestas/errores y documentación especial probados. Build Compose backend/frontend/backoffice salida 0, producción Next.js desde caché válida. Chrome autenticado verifica Management y estado vacío de incidencias; detalle/escritura de incidencias queda probado por HTTP.

TASK-SER-016: Chrome /docs observó POST /auth/tokens 201 (20:58:36 UTC), GET /management/reference-data/clinics offset=0 limit=1 200 (20:59:01 UTC), POST /compliance-reviews 201 (21:01:44 UTC). La última escritura usa jurisdicción US sintética e ignora id/created_by cliente. Su revisión 7850de3d-7194-49f1-b8b5-ad775d8e7ec4 y evento created permanecen como fixture local autorizada. No se registran tokens.

TASK-SER-017: inventario final 28/28 ✅ y matriz Requirement → Endpoint → Design → Task → Test → Evidence en docs/serialization-audit.md. Los resultados 117/74/63 y afirmaciones de pendientes anteriores son históricos, sustituidos por este cierre. No se modifican datos previos, retención, migraciones, permisos, dependencias ni contratos de payload incidentalmente. No se certifica HIPAA/UK GDPR ni autorización de datos reales/piloto/producción. No se crean commits.
