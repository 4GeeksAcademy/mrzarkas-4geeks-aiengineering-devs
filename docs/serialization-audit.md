# Auditoría de serialización del backend

**Estado:** TASK-SER-001–017 completadas para el entorno sintético aprobado. Evidencia final y limitaciones en el apartado de cierre; los apartados iniciales conservan el baseline histórico.
**Fecha de inspección:** 2026-10-31
**Alcance:** handlers FastAPI registrados en código y contratos consumidos dentro del monorepo. Los clientes externos no están identificados.

Documentos SDD relacionados: [SPEC](../memory-bank/specs/serialization-audit/spec.md), [PLAN](../memory-bank/specs/serialization-audit/plan.md) y [TASKS](../memory-bank/specs/serialization-audit/tasks.md).

## Hallazgos principales — baseline histórico

- La única aplicación FastAPI hallada está en `backend/app/main.py`; los cinco routers registrados son auth, catalogs, compliance, incidents y management. `services/central-api/`, citado por documentos previos, no existe en el árbol inspeccionado. No se hallaron subaplicaciones ni registro dinámico de routers.
- Se identificaron **28 handlers de aplicación**: 26 declaran `response_model`; `GET /health` y `GET /status` no lo hacen. FastAPI habilita además `/openapi.json`, `/docs`, `/docs/oauth2-redirect` y `/redoc` mediante sus valores por defecto. Son rutas especiales de documentación, no handlers de negocio; su activación se infiere de `FastAPI(title=...)` y no se pudo inspeccionar el OpenAPI ejecutado en este entorno.
- Clasificación inicial de los 28 handlers de aplicación: **14 ✅, 13 ⚠️, 1 ❌**. La clasificación indica adecuación del contrato de serialización observado; no certifica autorización ni cumplimiento normativo.
- Las respuestas ORM usan modelos Pydantic con campos declarados, por lo que `from_attributes=True` no expone automáticamente todas las columnas. No se encontraron propiedades de relaciones ORM declaradas en los modelos revisados. Aun así, varios contratos de detalle/administración se reutilizan en escritura o listado.
- Riesgo prioritario: las respuestas de auditoría exponen `before_data` y `after_data` como diccionarios JSON sin esquema de contenido. `PATCH /incidents/{incident_id}` escribe los campos modificados, incluido `description`, en esos snapshots; si alguien introduce PHI accidentalmente, el dato puede reaparecer en la API de auditoría. Los ejemplos y datos del proyecto deben seguir siendo sintéticos. Cualquier decisión sobre contenido/retención requiere revisión de Cumplimiento y Gobierno del Dato.
- `TokenRequest`, los modelos de escritura de Compliance e incidencias y `ActivationRequest` declaran explícitamente `extra="ignore"`, preservando el default previo. Los modelos Management que ya declaraban `extra="forbid"` lo mantienen. La prueba sintética de política pasó 13 casos; la verificación HTTP de 403 con DB sigue pendiente.
- No se encontraron rutas de registro, login con email/contraseña, perfil ni recuperación de contraseña. El único endpoint auth es la emisión temporal de JWT para desarrollo/pruebas; entrega `access_token` y `token_type`, y está desactivado fuera de esos entornos. No se debe inventar trabajo de rediseño de login.
- Los listados de incidencias tienen `IncidentListItem`; los listados administrativos de valores de catálogo y datos de referencia reutilizan modelos de respuesta más amplios. Esto se marca como parcial por forma del contrato, no porque el frontend local consuma pocos campos: otros clientes pueden depender del contrato OpenAPI.

## Entorno, stack y pruebas

| Evidencia | Resultado |
| --- | --- |
| Rama y Git | `feature/serialization-audit`; estado inicial limpio, sin cambios staged/unstaged. |
| Python disponible | 3.12.16. |
| Versiones resueltas en `backend/uv.lock` | FastAPI 0.141.1, Pydantic 2.13.5, SQLAlchemy 2.1.1 y Uvicorn 0.54.0. Se instalaron en el entorno temporal indicado abajo; no se cambió el lockfile. |
| Restricciones declaradas en `backend/pyproject.toml` | FastAPI `>=0.115,<1`; Pydantic Settings `>=2.7,<3`; SQLAlchemy asyncio `>=2.0,<3`; Python `>=3.12,<3.13`. Pydantic llega como dependencia de FastAPI. |
| Entorno de verificación | `uv==0.8.22` instalado bajo `/tmp`; `uv sync --frozen` instaló 31 paquetes del lockfile en un virtualenv/caché temporales. Python 3.12.16; sin cambios en `pyproject.toml` o `uv.lock`. |
| Tests enfocados | Snapshot `HEAD` previo al cambio: `backend/tests/test_status.py`, **3 passed**. Código actual: mismo archivo, **5 passed**. Ambos se ejecutaron sin PostgreSQL. |
| OpenAPI | `app.openapi()` devuelve 28 operaciones en cada versión. SHA-256 canónico (JSON con claves ordenadas y separadores compactos): snapshot inicial `dfc2177fc03e2cdc127f8584635790cb4ae7413abc68bdc20bd3ad806737eaa0`; después de `TASK-SER-006` y antes de separar schemas de listas `74b01908b230fdc84c5498f44395c75341ea1a894b07c3db64b32a6bb4672850`; actual tras `TASK-SER-008` `85853ecb622ad4ef412e0977d62db67c3193dade22fa8db1c5d150665336214f`. El cambio reciente sólo separa las referencias nominales de EP-017/021. En el snapshot inicial, `/health` tenía schema inferido `object` con `additionalProperties: string`; `/status` tenía schema de éxito vacío y 503 sin `content`. |
| Consumidores | Mapa local de frontends/tests revisado. Confirmación del responsable (2026-10-31): no hay consumidores externos conocidos por ahora; la aplicación correrá en contenedores Docker y el health se usa internamente para comprobar estado. No se infiere ausencia futura de clientes. |
| Verificación manual | No se inició un servidor ni se verificó `/docs` manualmente. El registro de rutas confirma las rutas automáticas `/openapi.json`, `/docs`, `/docs/oauth2-redirect` y `/redoc`. |
| Suite registrada | `backend/tests/`: auth, autorización HTTP, workflows, catálogos, fixtures de Compliance y status. El README documenta `uv run --no-sync pytest tests/test_status.py -q` y `docker compose --profile test run --rm test`. |
| Suite de integración | No ejecutada: Docker y Podman no están disponibles. Según `backend/README.md`, requiere PostgreSQL y modifica registros sintéticos; no se alteró una base de datos. `memory-bank/current-state.md` informa 27 pruebas pasadas el 2026-09-28, evidencia histórica no revalidada aquí. |

## Inventario de endpoints de aplicación

Los códigos de error de validación son los observados en el handler/dependencias o los generados por FastAPI/Pydantic. En general, los errores `HTTPException` y de validación usan el envelope FastAPI `{"detail": ...}`; la mayoría no declara modelos de respuesta de error propios. La ausencia de una mención de error no garantiza que el código sea imposible.

| ID | Método y ruta | Propósito; handler (archivo) | Entrada | Salida y campos actuales | Éxito; errores relevantes | Consumidor | Relaciones / seguridad | Estado y mejora necesaria; pruebas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EP-001 | POST `/auth/tokens` | Emisión temporal de token; `issue_token` (`backend/app/auth/router.py`) | `TokenRequest`: actor_id, role, area_id opcional | `TokenResponse`: access_token, token_type | 201; 404 si desactivado, 422 rol o payload inválido | No hay llamada desde UI; token introducido manualmente | El bearer token es una credencial prevista, no un secreto interno que deba quitarse del contrato. No acepta email/contraseña. | ✅ Contrato explícito y acotado. Mantener el gate por entorno; validar forma y ausencia de otros datos de entrada en la respuesta. `test_auth.py`; test futuro T-SER-SEC. |
| EP-002 | GET `/catalogs/{catalog_name}` | Catálogo activo; `get_catalog` (`backend/app/catalogs/router.py`) | Path `catalog_name` | `CatalogResponse`: catalog_name, version, values; value: id, key, label, description, is_open, sort_order, effective_from, effective_to | 200; 401/403, 404 | Backoffice de incidencias carga incidentStatus, severity, entryChannel e incidentType | Consulta dos entidades, arma una lista explícita; no devuelve columnas ORM sin declarar. Sin relaciones anidadas. | ✅ Salida declarada y apropiada. `test_catalogs.py`, `test_http_authorization.py`. |
| EP-003 | POST `/compliance-reviews` | Crear revisión; `create_review` (`backend/app/compliance/router.py`) | `ComplianceReviewCreate`: jurisdiction_id, status | `ComplianceReviewRead`: jurisdiction_id, status, id, review_identifier, created_at, created_by | 201; 401/403, 422 | No se encontró consumidor frontend; prueba HTTP | Respuesta hereda del esquema de entrada. `created_by` es un identificador interno; política de visibilidad existente limita lectura a admin/Compliance. | ⚠️ Separar modelo de escritura/lectura sin romper campos; confirmar clasificación de actor ID. `test_http_authorization.py`; T-SER-COMP. |
| EP-004 | GET `/compliance-reviews/{review_id}` | Detalle de revisión; `get_review` (mismo router) | UUID `review_id` | `ComplianceReviewRead`, mismos campos que EP-003 | 200; 401/403, 404 | Prueba HTTP; no se halló consumidor frontend | Sin relación anidada. Restringido por rol, pendiente validar si `created_by` es visible. | ⚠️ Esquema de lectura ligado al de escritura. Mantener policy y probar payload/campos. `test_http_authorization.py`; T-SER-COMP. |
| EP-005 | PATCH `/compliance-reviews/{review_id}/status` | Cambiar estado; `update_review_status` (mismo router) | `ComplianceReviewStatusUpdate`: status, reason opcional | `ComplianceReviewRead` | 200; 401/403, 404, 409, 422 | Prueba HTTP; no se halló consumidor frontend | `reason` se registra en auditoría administrativa; no aparece en la respuesta del Review. | ⚠️ Mismo modelo de salida derivado del input de alta. Separar y probar el contrato; no cambiar transiciones/códigos. `test_http_authorization.py`; T-SER-COMP. |
| EP-006 | POST `/incidents` | Crear incidencia; `create_incident` (`backend/app/incidents/router.py`) | `IncidentCreate`: title, description, clinic_id, jurisdiction_id, affected_system_id, entry_channel_value_id, incident_type_value_id, severity_value_id, responsible_area_id, compliance_review_id opcional | `IncidentResponse`: esos campos más id, incident_identifier, reporter_id, status_value_id, created_at/created_by, updated_at/updated_by | 201; 401/403, 422, 503 si no hay status inicial | Backoffice de incidencias, formulario de alta | Devuelve metadatos de actor y detalle. `IncidentResponse` hereda de `IncidentCreate`; `reporter_id` deriva del actor autenticado, no del cliente. | ⚠️ Separar entrada y salida. Confirmar autorización de actor IDs y tratamiento de description en auditoría. `test_http_authorization.py`, `test_incident_workflows.py`; T-SER-INC. |
| EP-007 | GET `/incidents` | Cola paginada/filtrada; `list_incidents` (mismo router) | Filtros status/severity/área, sort, offset, limit 1–100 | `IncidentListResponse`: items (`IncidentListItem`: id, incident_identifier, title, clinic_id, jurisdiction_id, affected_system_id, entry_channel_value_id, incident_type_value_id, severity_value_id, status_value_id, responsible_area_id, created_at, updated_at), total | 200; 401/403, 422 query | Backoffice de incidencias, cola | Proyección específica, excluye `description` y auditoría; query carga entidades ORM completas antes de proyectar. No hay prueba de N+1; no se observan relaciones ORM. | ✅ Proyección controlada y paginación. Medir carga de columnas antes de optimizar. `test_http_authorization.py`; T-SER-LIST. |
| EP-008 | GET `/incidents/metrics/open-by-severity` | Conteo agregado; `open_incidents_by_severity` (mismo router) | Sin body ni parámetros | Lista de `OpenIncidentsBySeverityResponse`: severity_value_id, severity_key, severity_label, open_incident_count | 200; 401/403 | Resumen del backoffice de incidencias | Proyección SQL escalar; respeta el ámbito de área; sin entidad ORM anidada. | ✅ Contrato tipado agregado. Verificar forma y ámbito por rol. `test_http_authorization.py`; T-SER-TEST. |
| EP-009 | GET `/incidents/{incident_id}` | Detalle; `get_incident` (mismo router) | UUID `incident_id` | `IncidentResponse` (campos de EP-006) | 200; 401/403, 404 | Backoffice, detalle | Carga entidad completa; response model limita la salida. Expone description y actor IDs a roles con permiso de lectura. | ⚠️ Salida comparte base con Create. Definir contrato Detail y clasificar actor IDs. `test_http_authorization.py`; T-SER-INC. |
| EP-010 | PATCH `/incidents/{incident_id}` | Editar incidencia; `update_incident` (mismo router) | `IncidentUpdate`: title, description, severity_value_id, responsible_area_id, compliance_review_id opcionales | `IncidentResponse` | 200; 401/403, 404, 422 | Backoffice, edición de title/description | Rol responsibleArea sólo puede cambiar title/description de su área; campos desconocidos se ignoran por default. Snapshot de cambios puede incluir description. | ⚠️ Separar output; definir y probar política `extra`; revisar snapshot con Cumplimiento. `test_http_authorization.py`, workflows; T-SER-INC y T-SER-SEC. |
| EP-011 | POST `/incidents/{incident_id}/transitions` | Transición de estado; `transition_incident` (mismo router) | `StatusTransitionRequest`: status_value_id, reason opcional | `IncidentResponse` | 200; 401/403, 404, 409, 422, 500 | Backoffice, acción de estado | Registra transición e identificador de actor; devuelve detalle completo de incidencia. | ⚠️ Contrato de salida acoplado a Create; evaluar esquema compartido sin alterar workflow. `test_incident_workflows.py`, `test_http_authorization.py`; T-SER-INC. |
| EP-012 | POST `/incidents/{incident_id}/assignments` | Reasignación; `assign_incident` (mismo router) | `IncidentAssignmentRequest`: responsible_area_id, reason opcional | `IncidentResponse` | 200; 401/403, 404, 409, 422 | Backoffice, acción de asignación | Historial conserva actor, áreas y motivo; respuesta de detalle usa el contrato común. | ⚠️ Contrato de salida acoplado. Probar respuesta y no modificar semántica/auditoría. `test_http_authorization.py`; T-SER-INC. |
| EP-013 | GET `/incidents/{incident_id}/history` | Historial de estados; `incident_history` (mismo router) | UUID `incident_id` | Lista `StatusHistoryResponse`: id, from_status_value_id, to_status_value_id, changed_by, reason, changed_at | 200; 401/403, 404 | Backoffice, cronología | Proyección explícita; expone UUID interno de actor y motivo bajo permiso de lectura. | ✅ Esquema dedicado. Confirmar clasificación del actor ID y probar campos. `test_incident_workflows.py`; T-SER-SEC. |
| EP-014 | GET `/incidents/{incident_id}/assignment-history` | Historial de asignaciones; `incident_assignment_history` (mismo router) | UUID `incident_id` | Lista `AssignmentHistoryResponse`: id, from/to responsible area, changed_by, reason, changed_at | 200; 401/403, 404 | Backoffice, cronología | Proyección explícita; UUID de actor. Sin relación anidada. | ✅ Esquema dedicado; probar campos y autorización. `test_http_authorization.py`; T-SER-SEC. |
| EP-015 | GET `/incidents/{incident_id}/audit` | Auditoría de incidencia; `incident_audit` (mismo router) | UUID `incident_id` | Lista `AuditEventResponse`: id, entity_type/id, action, actor_id, before_data, after_data, occurred_at | 200; 401/403, 404 | No se halló llamada desde UI; pruebas HTTP de acceso | `before_data`/`after_data` son JSON arbitrario. `description` puede estar en el snapshot de PATCH. Requiere `audit:read`. | ⚠️ Contrato de contenido no acotado y riesgo de PHI incidental. Definir allowlist/redacción con Compliance antes de alterar payload persistido o expuesto. `test_http_authorization.py`; T-SER-AUDIT. |
| EP-016 | GET `/management/catalogs` | Listar catálogos; `list_catalogs` (`backend/app/management/router.py`) | offset, limit 1–100 | `CatalogListResponse`: items (`id`, `catalog_name`, `version`, `is_active`), total | 200; 401/403, 422 | Backoffice Management | Proyección de lista explícita. | ✅ Acorde al consumidor Management. `test_http_authorization.py`; T-SER-MGMT. |
| EP-017 | GET `/management/catalogs/{catalog_name}/values` | Listar valores administrables; `list_catalog_values` (mismo router) | catalog_name, offset, limit | `CatalogValueListResponse` ahora referencia `CatalogValueListItem`, con los mismos campos que `ManagedCatalogValueResponse`: id, key, label, description, active/open, sort_order, effective dates y created/updated actor/timestamps | 200; 401/403, 404, 422 | No llamado por UI actual; contrato OpenAPI y tipo compartido existen | Lista conserva metadata administrativa completa; el responsable confirma que no hay clientes externos conocidos por ahora. | ⚠️ Tipo nominal separado en `TASK-SER-008`; no se redujeron campos. Clasificación de metadata y verificación runtime con DB pendientes. `test_http_authorization.py`; T-SER-LIST. |
| EP-018 | POST `/management/catalogs/{catalog_name}/values` | Crear valor; `create_catalog_value` (mismo router) | `CatalogValueCreate` (`extra=forbid`) | `ManagedCatalogValueResponse`: id/key/label/description/active/open/sort/effective dates y auditoría de creación/actualización | 201; 401/403, 404, 409, 422 | No llamado por UI actual; pruebas HTTP | Respuesta contiene metadata administrativa apropiada a capability. | ✅ Contrato explícito; asegurar prueba de salida y compatibilidad. `test_http_authorization.py`; T-SER-MGMT. |
| EP-019 | PATCH `/management/catalogs/{catalog_name}/values/{value_id}` | Editar valor; `update_catalog_value` (mismo router) | `CatalogValueUpdate` (`extra=forbid`) | `ManagedCatalogValueResponse` | 200; 401/403, 404, 422 | No llamado por UI actual; pruebas HTTP | No expone columnas fuera del modelo; key no es editable según esquema. | ✅ Entrada/salida explícitas; probar campos. `test_http_authorization.py`; T-SER-MGMT. |
| EP-020 | POST `/management/catalogs/{catalog_name}/values/{value_id}/activation` | Activar/desactivar valor; `set_catalog_value_activation` (mismo router) | `ActivationRequest` (`extra=ignore` explícito; conserva default inicial), razón requerida al desactivar | `ManagedCatalogValueResponse` | 200; 401/403, 404, 422 | No llamado por UI actual; pruebas HTTP | Respuesta administrativa; no altera permiso ni semántica. | ✅ Contrato explícito; probar payload de estado y motivo. `backend/tests/test_input_schema_policy.py`; T-SER-MGMT. |
| EP-021 | GET `/management/reference-data/{resource}` | Listar datos maestros; `list_reference_values` (mismo router) | resource, offset, limit | `ReferenceValueListResponse` ahora referencia `ReferenceValueListItem`, con los mismos campos que `ReferenceValueResponse`: id/key/label/is_active, created/updated actor/timestamps y jurisdiction_id opcional; total | 200; 401/403, 404, 422 | Incidencias usa referencias para formularios; Management UI muestra key/label/jurisdiction_id/is_active | Las UIs observadas usan un subconjunto; el responsable confirma que no hay clientes externos conocidos por ahora. Restringido por `referenceData:read`. | ⚠️ Tipo nominal separado en `TASK-SER-008`; no se redujeron campos. Clasificación de metadata y verificación runtime con DB pendientes. `test_http_authorization.py`; T-SER-LIST. |
| EP-022 | POST `/management/reference-data/{resource}` | Crear dato maestro; `create_reference_value` (mismo router) | `ReferenceValueCreate` (`extra=forbid`) | `ReferenceValueResponse`: campos maestros, auditoría de creación/actualización y jurisdiction_id | 201; 401/403, 404, 409, 422 | No llamado por UI actual; pruebas HTTP | Respuesta incluye metadata interna de actor; permiso `referenceData:manage`. | ✅ Proyección explícita; decidir si metadata forma parte del contrato Management. `test_http_authorization.py`; T-SER-MGMT. |
| EP-023 | PATCH `/management/reference-data/{resource}/{resource_id}` | Editar maestro; `update_reference_value` (mismo router) | `ReferenceValueUpdate` (`extra=forbid`) | `ReferenceValueResponse` | 200; 401/403, 404, 409, 422 | No llamado por UI actual; pruebas HTTP | Rechaza cambios que invalidarían incidencias históricas. | ✅ Entrada/salida explícita; mantener errores y probar contrato. `test_http_authorization.py`; T-SER-MGMT. |
| EP-024 | POST `/management/reference-data/{resource}/{resource_id}/activation` | Activar/desactivar maestro; `set_reference_value_activation` (mismo router) | `ActivationRequest` (`extra=ignore` explícito; conserva default inicial) | `ReferenceValueResponse` | 200; 401/403, 404, 422 | No llamado por UI actual | Response incluye actor IDs y timestamps. | ✅ Esquema explícito; verificar clasificación de metadata. `backend/tests/test_input_schema_policy.py`; T-SER-MGMT. |
| EP-025 | PUT `/management/affected-systems/{system_id}/jurisdictions` | Reemplazar cobertura; `set_system_jurisdictions` (mismo router) | `SystemJurisdictionsUpdate` (`extra=forbid`): jurisdiction_ids | Lista UUID de jurisdicciones | 200; 401/403, 404, 409, 422 | No llamado por UI actual; pruebas HTTP | Proyección escalar; consulta asociación sin relaciones ORM. | ✅ Contrato tipado. Validar forma y compatibilidad de lista. `test_http_authorization.py`; T-SER-MGMT. |
| EP-026 | GET `/management/audit-events` | Consultar auditoría de Management; `list_management_audit_events` (mismo router) | resource_type/resource_id opcionales, offset/limit | `ManagementAuditEventListResponse`: id, resource_type/id, action, actor_id, before_data/after_data, reason, correlation_id, occurred_at; total | 200; 401/403, 422 | Management UI muestra occurred_at, resource_type, action, actor_id, reason; tipos TS compartidos | `before_data`/`after_data` son JSON arbitrario; rol requiere `audit:read`. | ⚠️ Definir shape de snapshots con revisión de Compliance; preservar contrato hasta aprobar cambio. `test_http_authorization.py`; T-SER-AUDIT. |
| EP-027 | GET `/health` | Liveness; `health` (`backend/app/main.py`) | Ninguna | Inicial: `dict[str, str]` infería un objeto abierto (`additionalProperties: string`); sin `response_model` | 200 | No se encontró llamada desde UIs | Sin datos ORM ni error declarado; el schema inferido no restringía las claves. | ⚠️ Sustituir el objeto abierto por un modelo explícito. Implementado después en `TASK-SER-006`; ver avance. T-SER-HEALTH. |
| EP-028 | GET `/status` | Conectividad de DB; `status` (`backend/app/main.py`) | Ninguna | Éxito `{"status":"ok","database":"connected"}`; 503 `{"status":"error","database":"unavailable"}`. `responses` sólo declara descripción para 503, sin modelo/contenido tipado | 200/503; errors DB se ocultan | `frontend/app/page.js` consulta `/status` | El 503 usa `JSONResponse`, fuera de validación `response_model`; prueba existente asegura que no se filtran detalles SQL. | ❌ Declarar ambos contratos HTTP sin cambiar códigos ni payload. `test_status.py`; T-SER-HEALTH. |

### Rutas automáticas de documentación

`FastAPI(title="HealthCore API")` no desactiva los valores por defecto de documentación. Se esperan `GET /openapi.json`, `GET /docs`, `GET /docs/oauth2-redirect` y `GET /redoc`. Son respuestas especiales gestionadas por FastAPI/Starlette, no respuestas JSON de recursos ORM, por lo que `response_model` no corresponde. Se documentan como excepción técnica; su presencia/configuración requiere confirmación cuando pueda generarse OpenAPI en el entorno de la aplicación. No se cuentan entre los 28 handlers de negocio.

## Consumidores locales comprobados

| Consumidor | Endpoints y uso observado |
| --- | --- |
| `uis/backoffice/operational-incidents/app.js` | GET `/catalogs/{catalog_name}` para cuatro catálogos; GET `/management/reference-data/{resource}` para clinics, jurisdictions, affected-systems y responsible-areas; POST/GET/PATCH `/incidents`; GET list, métricas, detalle, historial de estado y asignación; POST transitions y assignments. La cola usa `items`, `total`, title e IDs; el detalle usa `description`, IDs de catálogo/maestros y fechas; formularios envían sólo sus campos correspondientes. No llama `/incidents/{id}/audit`. |
| `uis/backoffice/management/index.html` | GET `/management/catalogs`, `/management/reference-data/{resource}` y `/management/audit-events`; presenta las columnas catalog_name/version/is_active, key/label/jurisdiction_id/is_active y occurred_at/resource_type/action/actor_id/reason. No llama actualmente las mutaciones Management ni `/catalogs/{name}/values`. |
| `frontend/app/page.js` | GET `/status` como señal del backend. No se encontraron llamadas a otros endpoints desde `frontend/app/`. |
| `packages/shared/types/management.ts` | Declara tipos Management/Reference/Audit. No se hallaron importaciones o referencias a estos tipos en los consumidores TypeScript del monorepo; no se presume que describan todos los clientes externos. |
| Tests backend | Verifican permisos, flujos y algunos campos/colecciones; `test_auth.py` consulta `app.openapi()`. No hay prueba dedicada que recorra los 28 response models y compruebe allowlists/ausencia de secretos. |

No se halló consumo desde UIs de los endpoints de Compliance ni de `/auth/tokens`; las pruebas HTTP sí consumen rutas de Compliance. El responsable confirmó el 2026-10-31 que no hay clientes externos conocidos por ahora, que la aplicación correrá en contenedores Docker y que health se usa internamente para comprobar estado. Esto no descarta integraciones futuras.

## Resumen de conteo y prioridad

| Estado | Cantidad | Evidencia/criterio |
| --- | ---: | --- |
| ✅ | 14 | Contrato explícito, campos de respuesta declarados y proyección/lista adecuada para el comportamiento observado. |
| ⚠️ | 13 | Schema existe, pero se acopla a entrada, reusa detalle en listado, expone metadata cuya clasificación requiere confirmación, deja snapshots arbitrarios sin contrato de campo o usa un schema inferido demasiado amplio. |
| ❌ | 1 | Handler JSON de aplicación sin schema de éxito ni modelo de respuesta alternativo completo (`GET /status`, en el estado inicial). |

## Avance posterior del baseline

`TASK-SER-006` añade `HealthResponse`, `StatusConnectedResponse` y `StatusUnavailableResponse` en `backend/app/main.py`, conserva códigos y payloads previos, y documenta el 503 alternativo. `backend/tests/test_status.py` valida los cuerpos actuales y las referencias OpenAPI. Resultado: 5 tests pasados; la línea base anterior del mismo archivo pasó 3 tests. Esto no significa que el resto de requisitos de serialización esté implementado.

Prioridad propuesta para el baseline inicial: **P0** auditar snapshots de auditoría y exposición de campos internos con Compliance; **P1** añadir contratos explícitos a health/status (cubierto por `TASK-SER-006`) y separar contratos Review/Incident; **P2** definir proyecciones específicas para listados Management preservando compatibilidad; **P3** medir selección SQL/tamaño antes de optimizar. Los endpoints no son de autenticación de usuario; el único JWT se limita a dev/test.

## Avance de contratos — 2026-10-31

- `TASK-SER-007`: `IncidentResponse` ahora deriva directamente de `BaseModel`, independiente de `IncidentCreate`. Conserva campos, restricciones, defaults y configuración ORM. Las cinco rutas de creación, detalle, edición, transición y asignación conservan el mismo modelo y códigos HTTP.
- `TASK-SER-009`: `ComplianceReviewRead` ahora deriva directamente de `BaseModel`, independiente de `ComplianceReviewCreate`. Conserva jurisdicción, estados, default, identificadores y metadata. Las tres rutas mantienen sus contratos y permisos.
- `TASK-SER-010`: completada conservando los contratos y metadata vigentes en el entorno no productivo aprobado. Las 11 operaciones Management tienen comprobación de contratos OpenAPI; HTTP verifica claves exactas, paginación, filtros de auditoría y rechazo de campos gestionados por servidor. Los snapshots permanecen pendientes de una política específica en `TASK-SER-011`.
- `backend/tests/test_response_contracts.py` añade 15 casos: seis proyecciones desde objetos con atributos ORM, independencia de input/output y contratos OpenAPI de ocho rutas. Las proyecciones verifican claves exactas y exclusión de un atributo interno sintético ajeno al schema.
- Validación ejecutada por el agente: `podman compose --profile test run --build --rm test`, **63 passed in 1.55s**, código de salida 0, contra PostgreSQL local no productiva. La imagen de pruebas fue reconstruida con los cambios actuales.
- Comparación ejecutada en la imagen de pruebas contra los archivos de `HEAD` (`be2bad5`): `IncidentResponse.model_json_schema()` y `ComplianceReviewRead.model_json_schema()` son idénticos antes/después; OpenAPI conserva **28 operaciones**. No se redujeron campos publicados ni se cambiaron permisos, persistencia o retención.
- Los README del backend se actualizaron en ambos idiomas. Este avance no equivale al cierre de `TASK-SER-013`–`TASK-SER-017` ni de la auditoría global. SPEC/PLAN/TASKS se sincronizaron con autorización expresa del responsable; las otras fuentes históricas del Memory Bank no se modificaron.

### Cierre de TASK-SER-010

La formalización conserva metadata administrativa como parte del contrato vigente, sin ampliación de permisos ni retirada de campos. Los esquemas existentes ya enumeran los campos de salida; las comprobaciones añadidas permiten cerrar la tarea sin alterar handlers o tipos TS sin consumidor verificado.

| Operaciones Management | Contrato verificado | Evidencia |
| --- | --- | --- |
| GET catálogos | CatalogListResponse; id/catalog_name/version/is_active | OpenAPI y HTTP, claves exactas, items/total y paginación |
| GET valores; POST/PATCH/activación de valor | CatalogValueListResponse / ManagedCatalogValueResponse | OpenAPI y HTTP, claves exactas; metadata conservada; campos gestionados por servidor rechazados con 422 en PATCH |
| GET referencias; POST/PATCH/activación de referencia | ReferenceValueListResponse / ReferenceValueResponse | OpenAPI y HTTP, cuatro familias, claves exactas y paginación; campos gestionados por servidor rechazados con 422 en PATCH de clínica |
| PUT cobertura | Lista UUID de jurisdicciones | OpenAPI y HTTP; respuesta escalar exacta y rechazo de cambios que invalidan historia |
| GET eventos de auditoría | ManagementAuditEventListResponse | OpenAPI y HTTP con eventos no vacíos; claves exactas, filtro por recurso, paginación y permisos existentes |

`backend/tests/test_management_openapi.py` añade 11 casos de método/ruta, respuesta, entrada aplicable y límites de paginación. `test_http_authorization.py` comprueba rechazos de `id`, `created_by`, `updated_by`, `created_at` y `updated_at` como campos de PATCH, además de los workflows existentes de autorización y trazabilidad. La proyección ORM y exclusión de atributos internos se verifican en `test_response_contracts.py`.

Validación final ejecutada: `podman compose --profile test run --build --rm test`, salida 0, **74 passed in 1.57s**, sin fallos ni omisiones. Imagen test `8e32984c05cc`, Python 3.12.13 y uv 0.8.22, dependencias bloqueadas conservadas. Una ejecución previa falló en colección por usar el nombre reservado `request` de pytest; se corrigió a `input_schema` antes de obtener este resultado. `git diff --check` se incluye en la revisión final.

Trazabilidad: SER-FR-002/003/006 → EP-016–EP-026 → contratos Management existentes → TASK-SER-010 → pruebas OpenAPI/HTTP/ORM → resultado anterior. SER-SEC-003 y SER-COMP-001 se verifican para conservación del contrato y permisos del entorno no productivo; no se declara una política nueva de snapshots ni cumplimiento legal.

## Inventario técnico preliminar para Compliance

Este inventario describe lo que escriben los servicios y se conserva sin cambios de persistencia. La clasificación y proyección aprobadas posteriormente para el entorno sintético se detallan en audit-output-v1, al final del documento.

| Escritor/acción | `before_data` | `after_data` | Otros campos de auditoría relevantes |
| --- | --- | --- | --- |
| Management, valores de catálogo | `null` en alta; snapshot previo en actualización/activación | snapshot con `key`, `label`, `description`, `is_active`, `is_open`, `sort_order`, `effective_from`, `effective_to` | `actor_id`, recurso/acción, `reason` para activar/desactivar, `correlation_id`, `occurred_at` |
| Management, datos de referencia | `null` en alta; snapshot previo en actualización/activación | `key`, `label`, `is_active`; añade `jurisdiction_id` para clínicas | `actor_id`, recurso/acción, `reason` para activar/desactivar, `correlation_id`, `occurred_at` |
| Management, cobertura de sistemas | lista ordenada `jurisdiction_ids` previa | lista ordenada `jurisdiction_ids` solicitada | `actor_id`, `resource_id`, acción `coverageChanged`, `correlation_id`, `occurred_at` |
| Compliance review | `null` en alta; estado previo en cambio de estado | alta: `jurisdiction_id`, `status`; cambio: nuevo `status` | `actor_id`, `resource_id`, acción, `reason` al cambiar estado, `correlation_id`, `occurred_at` |
| Incidencia, creación | `null` | `status_value_id` inicial | `actor_id`, `entity_id`, acción `created`, `occurred_at`; la historia inicial también tiene `changed_by` y reason fijo |
| Incidencia, actualización | Mapa de campos modificados antes del cambio | Mapa de campos modificados después del cambio, serializados como texto; campos posibles: `title`, `description`, `severity_value_id`, `responsible_area_id`, `compliance_review_id` | `actor_id`, `entity_id`, acción, `occurred_at`; `description` es texto libre. Al asociar/desasociar revisión se registra también `incident_id` en Management audit. |
| Incidencia, transición/asignación | transición: `status_value_id`; asignación: `responsible_area_id` | transición: nuevo `status_value_id`; asignación: nuevo `responsible_area_id` | `actor_id`, `entity_id`, acción, `occurred_at`; las tablas de historia guardan `changed_by` y `reason` |

`ManagementAuditEvent` y `AuditEvent` son tablas distintas; ambas guardan `actor_id` y snapshots JSON, mientras que sólo Management incluye `reason` y `correlation_id` en su evento. Esta distinción también requiere confirmación del responsable de datos.

## Aprobación inicial de Cumplimiento y Gobierno del Dato — 2026-10-31

El responsable del proyecto confirma en esta sesión que se dispone de aprobación de Cumplimiento y Gobierno del Dato para continuar la auditoría de serialización en el entorno de desarrollo y pruebas. También confirma que los datos de este entorno son no productivos. Esta aprobación se registra según su comunicación; no se adjuntó un acta independiente ni una política detallada por campo.

La aprobación permite continuar la revisión técnica de identificadores, metadata y snapshots en este entorno no productivo. El uso de datos exclusivamente sintéticos sigue siendo el criterio del proyecto. No se extrapola esta aprobación a datos reales, piloto o producción, ni se interpreta como una certificación de cumplimiento o ausencia general de riesgo técnico.

La comunicación no especifica una nueva política de redacción, exclusión de claves, tratamiento de eventos históricos o retención. Esas decisiones no se dan por aprobadas implícitamente. Se conservarán los contratos y controles existentes durante los cambios de separación de esquemas; cualquier cambio de exposición o persistencia deberá corresponder a una decisión expresa.

### Validación con PostgreSQL reportada por el responsable

El responsable aporta la salida de la ejecución del perfil `test` de Podman Compose: imagen `healthcore-stack-test` construida correctamente y **48 pruebas superadas en 1,59 segundos**, sin fallos reportados. Esta evidencia procede de su ejecución local y resuelve el bloqueo de integración por falta de PostgreSQL para esa ejecución. No se aportó el comando exacto ni el commit probado; la evidencia no se presenta como una reejecución del agente.

## Incertidumbres históricas anteriores a audit-output-v1

- `uv==0.8.22` y dependencias bloqueadas se instalaron en `/tmp`; los tests enfocados de status pasaron 5 casos, los de política de campos extra 13, y los tests enfocados de JWT en producción 2. El módulo `test_auth.py` completo dio 13 passed y un fallo en una ruta de incidencias por falta de `DATABASE_URL`.
- El bloqueo anterior por falta de PostgreSQL queda resuelto por la ejecución local reportada de 48 pruebas. Los resultados parciales anteriores se conservan como evidencia histórica.
- La aprobación de Cumplimiento y Gobierno del Dato para continuar en el entorno no productivo está confirmada por el responsable y registrada arriba. Sigue pendiente concretar la política por campo para cambios de redacción, retención, persistencia o exposición de snapshots.
- No se modificaron snapshots, permisos ni retención. Los cambios funcionales incluyen contratos health/status, política explícita de campos extra compatible con la previa, tipos nominales de listas Management y separación de contratos de salida de Incident/ComplianceReview.

## Política audit-output-v1 — aprobación específica y cierre de TASK-SER-003/011

**Aprobación (2026-10-31):** tras revisar la propuesta de clasificación, estrategia, compatibilidad y criterios de aceptación, el responsable declara «doy aprobación explícita, ya que ahora mismo los datos son sintéticos. continua». Se registra como aprobación de la política propuesta y autorización para implementar en ese entorno. Sustituye el bloqueo histórico de falta de decisión específica; no autoriza datos reales, piloto o producción ni certifica cumplimiento.

### Clasificación aprobada

| Campos | Categoría y tratamiento de salida |
| --- | --- |
| id, entity_type/entity_id, resource_type/resource_id, action, actor_id, occurred_at | Permitidos en respuesta autorizada por audit:read; se conservan |
| correlation_id de Management | Identificador técnico permitido; se conserva incluso si es null, sin inventar correlación de petición o entre tablas |
| reporter_id, created_by, updated_by y metadata administrativa ya publicada | Restringidos por las capabilities de lectura/escritura de cada endpoint existente; se conservan sin expansión de identidad |
| changed_by, changed_at y referencias from/to de historiales | Restringidos por incident:read y alcance por área existentes; se conservan |
| status_value_id, severity_value_id, responsible_area_id, compliance_review_id, jurisdiction_id, incident_id y jurisdiction_ids | Permitidos exclusivamente en el recurso/acción correspondiente; UUID como string y lista de strings validados, sin expansión de entidades |
| status, is_active, is_open, sort_order, effective_from/effective_to | Valores técnicos permitidos por evento con validación estricta; se conserva representación válida |
| key | Identificador técnico permitido, con sintaxis de clave y límite de longitud existentes; no es un detector semántico de secretos incrustados en identificadores |
| title, description y label en snapshots | Texto libre: cada valor no nulo se sustituye por [REDACTED]; null se conserva |
| reason de Management y de ambos historiales de incidencias | Texto libre bajo su permiso existente: no nulo se sustituye por [REDACTED]; null se conserva |
| Claves desconocidas, incluyendo password/token/secret, o valores con estructura/tipo inválidos | Exclusión de salida; no se devuelven nombres de campos excluidos ni valores originales |
| Todos los valores y eventos persistidos | Persistencia protegida: no se actualizan, eliminan o migran; no cambia retención |

La clasificación no amplía roles. Auditoría permanece accesible a admin/compliance mediante audit:read; los historiales siguen accesibles mediante incident:read, incluida responsibleArea sólo para su área. Los IDs de actor y metadata ya publicados en detalle/Management se conservan bajo las capabilities existentes.

### Proyección por evento y estructuras históricas

- Incidencias: created/status_changed permiten status_value_id; assigned permite responsible_area_id; updated permite title, description, severity_value_id, responsible_area_id y compliance_review_id.
- Management: catálogo permite key, label, description, is_active, is_open, sort_order y vigencias; referencias permiten key, label, is_active y jurisdiction_id sólo para clínicas. Aplica a created/updated/activated/deactivated.
- Cobertura: coverageChanged permite únicamente jurisdiction_ids como lista de UUID strings. Una lista con elementos inválidos se excluye como campo completo para no presentar una cobertura parcial como si fuese la original.
- ComplianceReview: created permite jurisdiction_id/status; statusChanged permite status; associated/disassociated permiten incident_id.
- null permanece null. Un objeto vacío válido permanece vacío. Cada valor técnico válido conserva su representación; compliance_review_id histórico "None" se conserva como string, sin normalización silenciosa.
- Una lista raíz, escalar, recurso/acción desconocido o contenido totalmente no permitido produce un objeto de señalización cuando se oculta contenido: {"_redacted": true}. Las listas raíz no se exponen ni se convierten en snapshots técnicos inventados. Los escritores actuales generan objetos y la lista jurisdiction_ids está anidada; no se presupone qué formas existen en históricos reales.
- Si se redacta texto o excluye algún campo, se incorpora _redacted: true dentro del snapshot. Las referencias válidas restantes se conservan. Este marcador distingue contenido ocultado de ausencia (null) o snapshot vacío original; no enumera nombres potencialmente sensibles.
- La política es idéntica para eventos actuales e históricos, sin condición por fecha ni reescritura.

### Estrategia aplicada y compatibilidad

Se aplica la alternativa C: función pura centralizada project_snapshot, allowlist recurso/acción y TypeAdapters Pydantic estrictos por campo; validators de los modelos de respuesta ejecutan la proyección antes de validar before_data/after_data. Los motivos se redactan en los modelos de salida. No se modifican los escritores ni se asignan datos transformados a los objetos ORM.

Los campos generales de los eventos, wrappers, tipos de snapshot publicados (objeto/null), códigos, filtros, orden y paginación permanecen. Cambian deliberadamente valores de texto y claves internas de snapshots; _redacted es una clave de señalización dentro del objeto JSON ya publicado. Son cambios de contenido autorizados para este entorno, aunque los JSON Schemas permanezcan iguales. El backoffice Management y la cronología de incidencias muestran ahora [REDACTED] como motivo; no requieren cambios de código porque siguen recibiendo string/null. Tipos TS existentes siguen representando objetos/null y no tienen consumidor verificado. No se afirma validación global de consumidores externos o de TASK-SER-014/015.

### Evidencia y criterios de aceptación

`backend/tests/test_audit_serialization.py` añade 43 casos a la suite: matrices de eventos Management, referencias técnicas, nulos/sentinel histórico, estructuras desconocidas, claves prohibidas anidadas, texto libre y permisos. La prueba PostgreSQL inserta fixtures dentro de una transacción aislada y la revierte; lee por HTTP ambas auditorías y ambos historiales, después ejecuta SELECT de snapshots/motivos para comprobar que siguen intactos.

| Criterios preparados para TASK-SER-011 | Evidencia |
| --- | --- |
| AC-011-01/02/03: claves técnicas, prohibidas y texto libre | Pruebas parametrizadas por evento, invalid/nested fields, proyección de modelos y HTTP |
| AC-011-04/05: eventos históricos y formas variables | Fixtures 2020/2026; null, objeto vacío, listas raíz, listas internas inválidas, "None" y acción desconocida |
| AC-011-06/07: permisos existentes | HTTP 401 sin token; 403 para technology/responsibleArea/direction en ambas auditorías; 200 para admin/compliance |
| AC-011-08/09: actor/referencias/fecha/correlation | Proyección de modelos y HTTP; correlation_id Management preservado y no añadido a Incident |
| AC-011-10: persistencia | SELECT posterior comprueba snapshots y motivos originales de ambas auditorías/historiales; rollback de fixtures; sin cambios de escritores/migraciones |
| AC-011-11/12: contratos y comportamiento | Suite completa de paginación/filtros/workflows; JSON Schemas de las cuatro respuestas idénticos a HEAD; revisión de consumidores locales |
| AC-011-13: historiales y área | HTTP de history/assignment-history para roles permitidos; responsibleArea de otra área mantiene 403 en history; ambos motivos redactados |

Validación: `podman compose --profile test run --build --rm test`, salida 0, **117 passed in 1.61s**, sin fallos ni omisiones; imagen test bdcee65a60db. Comparación en esa imagen: AuditEventResponse, ManagementAuditEventResponse, StatusHistoryResponse y AssignmentHistoryResponse conservan JSON Schemas idénticos a HEAD be2bad5; OpenAPI mantiene 28 operaciones. git diff --check forma parte de la revisión final.

TASK-SER-003 y TASK-SER-011 quedan completadas para el alcance aprobado. TASK-SER-012–017 siguen pendientes. La política no garantiza detectar secretos semánticos introducidos en claves técnicas válidas; el entorno continúa limitado a fixtures sintéticas y sin credenciales reales en payloads. No se cambian retención, almacenamiento, permisos o despliegue.

## Cierre de TASK-SER-012–017 — 2026-10-31

Este apartado es el estado final y sustituye las conclusiones de disponibilidad, pendientes y clasificación inicial de los apartados históricos anteriores. **17/17 tareas completadas; 28/28 operaciones ✅ para el alcance sintético aprobado.** No es una certificación normativa ni autorización para datos reales, piloto o producción. La aprobación expresa del responsable para implementar y sincronizar estas evidencias se conserva en la conversación; no se atribuye una firma documental independiente a Claire Whitfield.

### Medición de TASK-SER-012

Método reproducible: [script](serialization-measurement.py) y [resultado JSON](serialization-measurement.json). Ejecutar desde la raíz, con PostgreSQL local sintética y seeds existentes:

```sh
podman compose --profile test run --no-deps --rm -v "$PWD/docs:/baseline:ro" test uv run --no-sync python /baseline/serialization-measurement.py
```

La ejecución registrada utilizó el mismo script montado desde /private/tmp/healthcore-serialization-baseline como measure.py. Fixture: 100 incidencias nuevas, descripción de 9.200 caracteres, página de 25; Management devuelve las dos clínicas del seed. Inserción mediante flush en una transacción aislada, lecturas por override de get_session y rollback final. Cinco calentamientos y 50 muestras por ronda; p50 mediana, p95 nearest-rank. SQL capturado sin parámetros. ASGI en contenedor y SQL a PostgreSQL: no mide latencia de red/Uvicorn ni carga concurrente. Dos rondas sobre el mismo código y fixture, **sin optimización aplicada**; no son un antes/después de una modificación funcional.

| Listado | p50 antes / después (ms) | p95 antes / después (ms) | Bytes antes / después | SELECT / cargas de relaciones |
| --- | --- | --- | --- | --- |
| Incidencias, limit=25, title asc | 1,401 / 1,389 | 1,645 / 1,566 | 17.598 / 17.598 | 2 / 0 en ambas rondas |
| Management clinics, limit=25 | 0,893 / 0,931 | 1,147 / 1,295 | 755 / 755 | 2 / 0 en ambas rondas |

Incidencias selecciona count + las 18 columnas de OperationalIncident, incluida description omitida en el listado; clínicas count + sus 9 columnas. El JSON adjunto enumera columnas y SQL. Existe lectura de columnas que no salen en la lista de incidencias, pero estas medidas sintéticas no demuestran una ventaja relevante que justifique cambiar consultas. No se afirma mejora ni ausencia universal de N+1; se registran cero cargas en estas dos rutas y fixture. No se añade test de rendimiento con umbral inestable.

### Pruebas y compatibilidad de TASK-SER-013–015

Comando final: `podman compose --profile test run --build --rm test`, salida **0**, **145 passed in 1.75s**; imagen test `a98a68ae2ca0`, Python 3.12.13. El resultado previo de 145 en 1.67s y las suites 117/74/63 son históricos.

- test_response_contracts.py comprueba claves exactas de los contratos ORM modificados, exclusión de atributos internos sintéticos añadidos y separación de entrada/salida.
- test_audit_serialization.py verifica allowlists de eventos, campos prohibidos, redacción, casos históricos, roles, trazabilidad y lectura SQL posterior intacta; las nuevas fixtures aisladas se revierten.
- test_input_schema_policy.py mantiene ignore/forbid y prueba en los cinco modelos forbid los extras id, created_by, updated_by, created_at y updated_at. test_http_authorization.py comprueba además por HTTP que id/reporter_id/actor/timestamp enviados a crear incidencia no prevalecen; conserva paginación, errores y restricciones de rol.
- test_auth.py inventaría exactamente las 28 operaciones, modelos de éxito, requestBody requerido en escrituras, errores documentados y cuatro rutas especiales. TokenResponse expone sólo access_token/token_type y descarta un password sintético desconocido; se conserva el 404 fuera de desarrollo/test.
- Se añadieron **anotaciones OpenAPI** de errores ya existentes mediante ErrorResponse: detail es string para negocio o lista para validación FastAPI. No se modificaron handlers de excepciones, cuerpos, códigos ni permisos. La documentación ahora incluye 401/403, 404/409/422 donde corresponden, 500 de transición y 503 de creación/status. Las rutas /openapi.json (JSON), /docs, /docs/oauth2-redirect y /redoc (HTML) son respuestas especiales, fuera de las 28 operaciones.

[OpenAPI final](serialization-openapi.json), SHA-256 `4f9e1e356c57927fafe9b711236cf33fd41febdfe124e48cc71555c74bba6a23`, capturado desde backend en ejecución. Las comparaciones contra HEAD be2bad5 conservaron JSON Schemas de IncidentResponse, ComplianceReviewRead y las cuatro respuestas de auditoría/historial. Los listados Management sólo separan el nombre de item y mantienen campos/tipos; health/status incorporan los modelos explícitos ya descritos. OpenAPI global cambia deliberadamente para completar documentación de errores y esos contratos: no se afirma igualdad byte a byte.

Los valores de auditoría sí cambian conforme a audit-output-v1 aprobado: [REDACTED], omisión de claves no permitidas y marcador _redacted. Puede afectar consumidores que interpreten textos o claves arbitrarias; la UI Management lee reason como texto y conserva actor/fecha/acción. No se redujeron otros campos publicados ni se cambiaron tipos TS, permisos, códigos, orden/paginación o reglas de workflow.

Validación de consumidores: `podman compose up --build -d backend frontend backoffice` terminó con salida 0; build de producción Next.js reutilizó la capa válida de caché, sin cambios frontend. Chrome local autenticado mostró cuatro catálogos, jurisdicciones US/UK y evento complianceReview/created en Management. Incidencias mostró conexión admin, filtros de catálogos/área y estado vacío correcto 0–0 de 0. El detalle/escritura de incidencias se verifica en las pruebas HTTP; no se afirma haber recorrido ese detalle manualmente. La web conserva el contrato /status probado por test_status.py.

### Verificación manual de TASK-SER-016 en Swagger

Chrome nativo, http://localhost:8000/docs, Podman local con PostgreSQL 16 y datos sintéticos, 2026-10-31. Horas UTC observadas en respuestas; Europe/Madrid = UTC+1. No se incluyen JWT utilizables.

| Endpoint | Hora UTC | Entrada / resultado esperado | Observado |
| --- | --- | --- | --- |
| EP-001 POST /auth/tokens | 20:58:36 | actor_id 11111111-1111-4111-8111-111111111111, role admin; 201 y sólo access_token/token_type | 201; bearer y dos claves exactas; token omitido |
| EP-021 GET /management/reference-data/clinics | 20:59:01 | offset=0, limit=1; 200, items de una clínica y total=2 | 200; una clínica sintética UK con metadatos autorizados, total=2 |
| EP-003 POST /compliance-reviews | 21:01:44 | jurisdiction_id US ...0001, status open; id y created_by extra aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa; 201 con valores gestionados por servidor | 201; id 7850de3d-7194-49f1-b8b5-ad775d8e7ec4, review_identifier CR-20261031-1ED41852, created_by actor autenticado y created_at actual |

La tercera ruta cumple la categoría escritura/detalle de SER-TEST-002 mediante ComplianceReview existente, sin inventar un perfil. Tras reconstruir backend se volvió a observar Swagger con ErrorResponse y 401/403/422. La revisión y su evento created de esta prueba manual **quedan persistidos como fixture sintética local**; no se borraron ni modificaron registros previos. Las mediciones y pruebas de redacción revierten sus fixtures aisladas.

### Inventario final de TASK-SER-017

Los campos/entradas/códigos/consumidores se conservan en el inventario inicial; la tabla siguiente sustituye su clasificación de adecuación y enlaza cada operación con tareas y pruebas reales. Todas las filas tienen además test_all_28_operations_have_explicit_contracts_and_documented_errors y el artefacto OpenAPI final. ✅ significa aceptación de serialización en este alcance, no permiso de producción.

| ID | Operación | Estado final | TASK-SER | Evidencia en backend/tests |
| --- | --- | --- | --- | --- |
| EP-001 | POST `/auth/tokens` | ✅ | 004, 014–015 | test_auth.py |
| EP-002 | GET `/catalogs/{catalog_name}` | ✅ | 010, 015 | test_catalogs.py; test_http_authorization.py |
| EP-003 | POST `/compliance-reviews` | ✅ | 009, 013–015 | test_response_contracts.py; test_http_authorization.py |
| EP-004 | GET `/compliance-reviews/{review_id}` | ✅ | 009, 013–015 | test_response_contracts.py; test_http_authorization.py |
| EP-005 | PATCH `/compliance-reviews/{review_id}/status` | ✅ | 009, 013–015 | test_response_contracts.py; test_http_authorization.py |
| EP-006 | POST `/incidents` | ✅ | 007–008, 013–015 | test_response_contracts.py; test_incident_workflows.py; test_http_authorization.py |
| EP-007 | GET `/incidents` | ✅ | 007–008, 013–015 | test_response_contracts.py; test_incident_workflows.py; test_http_authorization.py |
| EP-008 | GET `/incidents/metrics/open-by-severity` | ✅ | 007–008, 013–015 | test_response_contracts.py; test_incident_workflows.py; test_http_authorization.py |
| EP-009 | GET `/incidents/{incident_id}` | ✅ | 007–008, 013–015 | test_response_contracts.py; test_incident_workflows.py; test_http_authorization.py |
| EP-010 | PATCH `/incidents/{incident_id}` | ✅ | 007–008, 013–015 | test_response_contracts.py; test_incident_workflows.py; test_http_authorization.py |
| EP-011 | POST `/incidents/{incident_id}/transitions` | ✅ | 007–008, 013–015 | test_response_contracts.py; test_incident_workflows.py; test_http_authorization.py |
| EP-012 | POST `/incidents/{incident_id}/assignments` | ✅ | 007–008, 013–015 | test_response_contracts.py; test_incident_workflows.py; test_http_authorization.py |
| EP-013 | GET `/incidents/{incident_id}/history` | ✅ | 003, 011, 013–015 | test_audit_serialization.py |
| EP-014 | GET `/incidents/{incident_id}/assignment-history` | ✅ | 003, 011, 013–015 | test_audit_serialization.py |
| EP-015 | GET `/incidents/{incident_id}/audit` | ✅ | 003, 011, 013–015 | test_audit_serialization.py |
| EP-016 | GET `/management/catalogs` | ✅ | 008, 010–011, 013–015 | test_management_openapi.py; test_http_authorization.py; test_audit_serialization.py |
| EP-017 | GET `/management/catalogs/{catalog_name}/values` | ✅ | 008, 010–011, 013–015 | test_management_openapi.py; test_http_authorization.py; test_audit_serialization.py |
| EP-018 | POST `/management/catalogs/{catalog_name}/values` | ✅ | 008, 010–011, 013–015 | test_management_openapi.py; test_http_authorization.py; test_audit_serialization.py |
| EP-019 | PATCH `/management/catalogs/{catalog_name}/values/{value_id}` | ✅ | 008, 010–011, 013–015 | test_management_openapi.py; test_http_authorization.py; test_audit_serialization.py |
| EP-020 | POST `/management/catalogs/{catalog_name}/values/{value_id}/activation` | ✅ | 008, 010–011, 013–015 | test_management_openapi.py; test_http_authorization.py; test_audit_serialization.py |
| EP-021 | GET `/management/reference-data/{resource}` | ✅ | 008, 010–011, 013–015 | test_management_openapi.py; test_http_authorization.py; test_audit_serialization.py |
| EP-022 | POST `/management/reference-data/{resource}` | ✅ | 008, 010–011, 013–015 | test_management_openapi.py; test_http_authorization.py; test_audit_serialization.py |
| EP-023 | PATCH `/management/reference-data/{resource}/{resource_id}` | ✅ | 008, 010–011, 013–015 | test_management_openapi.py; test_http_authorization.py; test_audit_serialization.py |
| EP-024 | POST `/management/reference-data/{resource}/{resource_id}/activation` | ✅ | 008, 010–011, 013–015 | test_management_openapi.py; test_http_authorization.py; test_audit_serialization.py |
| EP-025 | PUT `/management/affected-systems/{system_id}/jurisdictions` | ✅ | 008, 010–011, 013–015 | test_management_openapi.py; test_http_authorization.py; test_audit_serialization.py |
| EP-026 | GET `/management/audit-events` | ✅ | 008, 010–011, 013–015 | test_management_openapi.py; test_http_authorization.py; test_audit_serialization.py |
| EP-027 | GET `/health` | ✅ | 006, 015 | test_status.py |
| EP-028 | GET `/status` | ✅ | 006, 015 | test_status.py |

### Trazabilidad final de requisitos

| Requirement | Endpoint | Diseño / TASK-SER | Test → evidencia |
| --- | --- | --- | --- |
| SER-FR-001 | EP-001–028 + docs especiales | response_model y errores explícitos / 006, 015 | test_auth.py, test_status.py → 145 pass + OpenAPI final |
| SER-FR-002 | ORM EP-002–007, 009–026 | allowlist Pydantic / 007–011, 013 | test_response_contracts.py, test_http_authorization.py, test_audit_serialization.py → claves exactas y atributos internos excluidos |
| SER-FR-003 | Colecciones EP-002, 007–008, 013–017, 021, 025–026 | items explícitos, campos conservados / 008, 010 | test_management_openapi.py, test_http_authorization.py → contratos y items/total |
| SER-FR-004 | Referencias EP-002, 006–025 | UUID/flattened, sin relación ORM implícita / 007–010 | shapes y cobertura en test_http_authorization.py; medición EP-007/021 sin cargas de relaciones |
| SER-FR-005 | Escrituras | contratos input/output independientes / 005, 007, 009 | test_response_contracts.py, test_input_schema_policy.py → clases separadas y extras |
| SER-FR-006 | Escrituras | salida limitada / 007, 009–010, 013 | test_response_contracts.py + workflows HTTP → claves declaradas |
| SER-SEC-001 | EP-001–028 | allowlists, proyección snapshots / 004, 011, 013 | test_auth.py, test_response_contracts.py, test_audit_serialization.py → marcadores secretos excluidos; bearer previsto |
| SER-SEC-002 | EP-001 | gate ambiental sin cambios / 004, 014 | test_auth.py → 201 exacto y 404 en producción |
| SER-SEC-003 | Metadatos EP-003–006, 009–026 | clasificación aprobada y permisos actuales / 003, 013 | política audit-output-v1 + test_http_authorization.py/test_audit_serialization.py → roles y trazabilidad |
| SER-SEC-004 | EP-013–015, 026 y escritores | proyección por evento, redacción de salida / 003, 011 | test_audit_serialization.py → históricos/motivos/snapshots, SQL original intacto |
| SER-SEC-005 | Entradas | ignore/forbid y restricciones existentes / 005, 014 | test_input_schema_policy.py, test_http_authorization.py → extra rechazado/ignorado y 403 |
| SER-COMP-001 | EP-001–028 | campos conservados; redacción aprobada / 002, 014–017 | comparación schemas, OpenAPI final, build y vistas locales; cambios de valores documentados |
| SER-NFR-001 | EP-007, 021 medidos | medición antes/después sin cambio / 012 | serialization-measurement.py/json → bytes, columnas, SQL, p50/p95; no optimización |
| SER-TEST-001 | EP-001–028 | suite focalizada / 013–015 | comando final → 145 pass, salida 0 |
| SER-TEST-002 | EP-001, 021, 003 | auth + lista + escritura en /docs / 016 | tabla manual → 201, 200, 201 observados |

### Límites de cierre

No se modifican migraciones, persistencia de negocio, retención, permisos, dependencias, secretos ni configuración de entorno. La sintaxis de una key técnica válida no permite detectar un secreto arbitrario colocado allí; tampoco hay detector universal de PHI en texto de detalle autorizado o en errores de validación que reflejan entradas. Esta entrega verifica contratos y política específica de auditoría con datos sintéticos. Clientes externos no conocidos y aprobación M0/datos reales siguen fuera del alcance. No se crearon commits, push, PR ni despliegues externos.
