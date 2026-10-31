# SPEC — Auditoría de serialización

**Estado:** aprobado para implementación; avance parcial en `TASK-SER-006`, sin considerar completa la auditoría global.
**Alcance técnico observado:** 28 handlers de aplicación FastAPI en `backend/app`; ver [auditoría](../../../docs/serialization-audit.md). La auditoría documenta aparte las rutas automáticas de OpenAPI/Docs.

## Contexto y problema

La API actual está implementada en `backend/app`, a pesar de que documentación histórica y `memory-bank/technology-stack.md` mencionan `services/central-api/` y dicen que aún no existe una API. El código/configuración son la evidencia del estado técnico. El servicio está en etapa de prototipo pre-MVP y no está autorizado para piloto ni producción (`memory-bank/current-state.md`).

26 de 28 handlers de aplicación declaran `response_model`. Los dos restantes son `GET /health` y `GET /status`. Entre los modelos existentes se encontraron contratos explícitos y allowlists Pydantic; también acoplamiento de `IncidentResponse`/`ComplianceReviewRead` a modelos de entrada, listados administrativos con esquemas de salida amplios y payloads de auditoría con JSON arbitrario. La descripción de una incidencia puede terminar en un snapshot de auditoría.

La ejecución local no permitió confirmar payloads ni OpenAPI: no están disponibles `uv`, pytest o las dependencias Python. Los requisitos siguientes son objetivos para implementación posterior, no capacidades ya demostradas.

## Objetivos

- Establecer un contrato explícito y verificable para toda respuesta de aplicación, incluidas respuestas alternativas y excepciones de transporte.
- Limitar la salida ORM mediante modelos de respuesta con campos autorizados por dominio y propósito.
- Separar responsabilidades de entrada, listado y detalle donde la evidencia muestre acoplamiento, sin retirar campos publicados sin evaluación de compatibilidad.
- Hacer verificables la clasificación de datos, la política de atributos desconocidos y el contenido de auditoría.
- Mantener códigos HTTP, permisos, paginación, semántica y consumidores actuales salvo cambio justificado y aprobado.

## Alcance y exclusiones

Incluye auth token temporal, catálogos, ComplianceReview, incidencias, Management, health/status, sus esquemas Pydantic, response models/OpenAPI, pruebas y consumidores locales identificados.

Excluye migraciones innecesarias, cambios de negocio/autorización, rediseño frontend, nuevas integraciones, creación de login/registro/perfil/recuperación no existentes, reemplazo de framework/ORM, actualización de dependencias y optimizaciones no medidas. No se modifica la auditoría persistida ni su retención sin revisión de Cumplimiento y Gobierno del Dato. No se usan datos reales de pacientes.

## Hallazgos de auditoría

- Inventario: 28 handlers en cinco routers y `main.py`; routers registrados estáticamente, sin subaplicaciones encontradas. 26 contratos explícitos, dos ausentes. Cuatro rutas docs se derivan de defaults FastAPI y quedan como respuesta especial documentada.
- Estado inicial: 14 ✅, 13 ⚠️, 1 ❌; detalle por método/ruta, entrada/salida/códigos/consumidor/riesgo en [serialization-audit.md](../../../docs/serialization-audit.md). `/health` tenía un schema inferido abierto; `/status` carecía de schema de éxito y contenido documentado para 503.
- Avance: `TASK-SER-006` añade modelos explícitos de health/status y documentación del 503. El OpenAPI previo y actual registra 28 operaciones; los tests previos pasaron 3 y los actuales 5. La suite global y la comprobación manual `/docs` siguen pendientes.
- Entidades no declaran relaciones ORM navegables en los modelos revisados. Los endpoints de lista usan paginación; la lista de incidencias proyecta `IncidentListItem`, aunque SQL selecciona la entidad completa. No hay evidencia de N+1; cualquier optimización requiere medición.
- Seguridad: no se hallaron campos password/hash ni flujos email/password en el backend revisado. `POST /auth/tokens` es un emisor JWT temporal de desarrollo con token previsto en la respuesta y 404 fuera de entornos permitidos. Auditoría ofrece actor IDs y mapas JSON; la descripción puede quedar en `before_data`/`after_data`.
- Consumidores identificados: backoffice de incidencias, backoffice Management y página web que consulta `/status`. No se encontraron llamadas locales a Compliance, endpoint audit de incidencias o mutaciones Management; clientes externos son desconocidos.
- Línea base: `uv 0.8.22` y `uv sync --frozen` se ejecutaron con entorno/caché temporales; versiones bloqueadas: FastAPI 0.141.1, Pydantic 2.13.5, SQLAlchemy 2.1.1 y Uvicorn 0.54.0; Python 3.12.16. `test_status.py` pasó 3 tests en el snapshot previo y 5 en el código actual. La suite de integración no se ejecutó porque requiere PostgreSQL y modifica fixtures sintéticos; `/docs` no se verificó manualmente.

## Requisitos EARS

Cada requisito incluye fundamento, evidencia, endpoints afectados, prioridad, criterios verificables y pruebas previstas. Las referencias `T-SER-*` son identificadores de pruebas futuras, no pruebas ya existentes.

### Funcionales

#### SER-FR-001 — Contrato de respuesta explícito

**EARS:** THE system SHALL define an explicit typed response contract for every JSON application endpoint, and a documented semantic contract for special responses where `response_model` is not applicable.
**Justificación/evidencia:** 26 endpoints ya usan `response_model`; `/health` y `/status` carecen de modelo completo. FastAPI también publica documentación mediante rutas especiales.
**Endpoints:** EP-001–EP-028; rutas docs automáticas como excepciones técnicas.
**Prioridad:** P1.
**Aceptación:** cada ruta de aplicación muestra modelo de éxito y alternativas relevantes en OpenAPI; `/health` y `/status` tienen esquema verificable; rutas docs están identificadas como excepciones de contenido.
**Pruebas:** `T-SER-OPENAPI-001`, `T-SER-HEALTH-001`.

#### SER-FR-002 — Proyección ORM controlada

**EARS:** WHEN an endpoint retrieves an ORM entity, THE system SHALL serialize only attributes explicitly declared by its authorized response contract.
**Justificación/evidencia:** modelos de respuesta usan `from_attributes=True`; eso no limita por sí mismo la lectura, pero las clases enumeran campos. La lista de incidencias selecciona entidades completas y luego las valida contra `IncidentListItem`.
**Endpoints:** EP-002–EP-007, EP-009–EP-026.
**Prioridad:** P1.
**Aceptación:** tests de payload verifican allowlist de claves para cada modelo que serializa ORM; agregar una columna ORM no cambia JSON sin edición deliberada del schema.
**Pruebas:** `T-SER-SHAPE-001`, `T-SER-ORM-001`.

#### SER-FR-003 — Proyección de listados

**EARS:** WHEN an endpoint returns a collection, THE system SHALL use a list-specific response projection that preserves the approved public fields and excludes unapproved detail-only attributes.
**Justificación/evidencia:** EP-007 ya utiliza `IncidentListItem`; EP-017 y EP-021 usan modelos de respuesta administrativa más amplios. No se presume que campos no usados por la UI sean innecesarios.
**Endpoints:** EP-002, EP-007, EP-008, EP-013–EP-017, EP-021, EP-025–EP-026.
**Prioridad:** P2.
**Aceptación:** la especificación de cada colección identifica el modelo de item y sus campos; no se quitan campos publicados sin aprobación de compatibilidad.
**Pruebas:** `T-SER-LIST-001`, pruebas de contrato Management.

#### SER-FR-004 — Relaciones deliberadas

**EARS:** WHERE related entity information is required, THE system SHALL expose an explicitly defined nested, identifier-based or flattened projection.
**Justificación/evidencia:** los modelos revisados no declaran relaciones ORM navegables y los contratos actuales usan UUID de referencias; la pertenencia de sistemas-jurisdicciones se consulta como asociación.
**Endpoints:** EP-002, EP-006–EP-025.
**Prioridad:** P2.
**Aceptación:** la matriz del plan describe cada referencia como ID/flattened/nested y no hay serialización implícita de relaciones ORM.
**Pruebas:** `T-SER-REL-001` y tests de shape.

#### SER-FR-005 — Entrada y salida separadas

**EARS:** WHEN a client submits POST, PUT or PATCH data, THE system SHALL validate writable attributes through a dedicated input schema distinct from the response schema.
**Justificación/evidencia:** `IncidentResponse` deriva de `IncidentCreate`; `ComplianceReviewRead` deriva de `ComplianceReviewCreate`. Otros endpoints ya usan modelos de entrada separados.
**Endpoints:** EP-001, EP-003, EP-005–EP-006, EP-010–EP-012, EP-018–EP-025.
**Prioridad:** P1.
**Aceptación:** entrada y salida tienen clases de contrato distintas; los campos gestionados por servidor no son escribibles; los modelos no admiten asignación masiva.
**Pruebas:** `T-SER-INPUT-001`, `T-SER-WRITE-001`.

#### SER-FR-006 — Respuesta de escritura limitada

**EARS:** WHEN a write operation succeeds, THE system SHALL return only fields declared by the endpoint's response contract.
**Justificación/evidencia:** escrituras devuelven entidades ORM tras `refresh`; FastAPI response models limitan campos, salvo que faltan modelos en health/status (solo GET).
**Endpoints:** EP-001, EP-003, EP-005–EP-006, EP-010–EP-012, EP-018–EP-025.
**Prioridad:** P1.
**Aceptación:** pruebas de cada grupo de escritura comparan claves y comprueban que columnas internas añadidas a ORM no aparecen.
**Pruebas:** `T-SER-WRITE-001`, `T-SER-ORM-001`.

### Seguridad

#### SER-SEC-001 — Secretos y credenciales

**EARS:** IF an API response contains a plaintext password, password hash, internal credential or secret, THEN THE system SHALL prevent that value from appearing in the response payload.
**Justificación/evidencia:** el backend inspeccionado no contiene modelos de contraseña/usuario; `POST /auth/tokens` devuelve el bearer token que su flujo temporal prevé expresamente.
**Endpoints:** EP-001–EP-028.
**Prioridad:** P0.
**Aceptación:** tests sensibles no encuentran campos/valores password/hash/secret; EP-001 permite exclusivamente `access_token` y `token_type` en respuesta.
**Pruebas:** `T-SER-SECRET-001`.

#### SER-SEC-002 — Flujos de autenticación existentes

**EARS:** WHEN the development token endpoint returns a response, THE system SHALL return only its documented token contract and SHALL remain unavailable outside the permitted development/test environment.
**Justificación/evidencia:** EP-001 acepta actor_id/role/area_id y responde `TokenResponse`; `test_auth.py` comprueba el 404 en producción. No existen registro/login de email/password ni recuperación.
**Endpoints:** EP-001.
**Prioridad:** P1.
**Aceptación:** 201 conserva exactamente los campos previstos; entorno no permitido mantiene 404; no se añaden flujos no existentes.
**Pruebas:** test actual `test_token_endpoint_is_not_exposed_in_production`; `T-SER-SECRET-001`.

#### SER-SEC-003 — Identificadores internos

**EARS:** WHILE an endpoint returns actor identifiers or administrative metadata, THE system SHALL expose those attributes only under an explicitly reviewed response contract and the endpoint's existing authorization policy.
**Justificación/evidencia:** actor UUIDs aparecen en detalle/historial/auditoría y metadata en Management; requisitos locales no clasifican formalmente esos identificadores.
**Endpoints:** EP-003–EP-006, EP-009–EP-026.
**Prioridad:** P1.
**Aceptación:** cada actor ID/metadata queda clasificado y asociado a permiso existente; el trabajo no amplía permisos.
**Pruebas:** `T-SER-ACCESS-001`, `T-SER-SHAPE-001`.

#### SER-SEC-004 — Snapshots de auditoría

**EARS:** IF audit snapshot data contains an attribute not approved for disclosure, THEN THE system SHALL omit or safely redact that attribute from the response according to a policy reviewed by Compliance and tested against persisted audit cases.
**Justificación/evidencia:** EP-015 y EP-026 devuelven `dict | None`; la edición de incidencia captura valores de cambios y puede incluir `description`. El sistema indica no incluir PHI y sólo usar datos sintéticos.
**Endpoints:** EP-010, EP-015, EP-018–EP-026.
**Prioridad:** P0; bloqueado por revisión de Compliance antes de decidir cambios de contenido/retención.
**Aceptación:** política aprobada identifica claves y tratamiento; tests prueban snapshots autorizados/no autorizados y no exponen dato sensible; no se alteran registros históricos sin aprobación.
**Pruebas:** `T-SER-AUDIT-001`, `T-SER-SECRET-001`.

#### SER-SEC-005 — Atributos no autorizados de entrada

**EARS:** IF a client submits an attribute that is not writable for the endpoint or actor, THEN THE system SHALL reject it or ignore it according to an explicit, documented and tested validation policy.
**Justificación/evidencia:** varios schemas carecen de configuración `extra`; por defecto Pydantic ignora extras. El PATCH de incidencias limita los campos conocidos para responsibleArea y devuelve 403.
**Endpoints:** EP-001, EP-003, EP-005–EP-006, EP-010–EP-012.
**Prioridad:** P1.
**Aceptación:** la política (preservar ignore o cambiar a forbid) está documentada; campos conocidos fuera de rol siguen rechazados; campos del servidor nunca mutan por payload.
**Pruebas:** `T-SER-INPUT-001`, `T-SER-ACCESS-001`.

### Compatibilidad, rendimiento y pruebas

#### SER-COMP-001 — Compatibilidad contractual

**EARS:** WHEN a response schema is changed, THE system SHALL preserve documented and actively consumed response fields unless a breaking change is explicitly approved.
**Justificación/evidencia:** dos UIs consumen subconjuntos, existen tipos TS de Management y los consumidores externos son desconocidos. OpenAPI actual no se pudo generar localmente.
**Endpoints:** EP-001–EP-028.
**Prioridad:** P1.
**Aceptación:** comparación OpenAPI antes/después, consumers tests, breaking changes listados y aprobados; códigos, permisos, paginación y errores no cambian incidentalmente.
**Pruebas:** `T-SER-COMPAT-001`, `T-SER-OPENAPI-001`.

#### SER-NFR-001 — Rendimiento medido

**EARS:** WHERE evidence shows a collection retrieves unnecessary database columns, relations or payload fields, THE system SHALL apply a justified projection/loading optimization only after recording a comparable baseline.
**Justificación/evidencia:** EP-007 selecciona entidades completas aunque la proyección omite description/actor metadata; no hay relaciones ORM navegables ni mediciones de consultas/latencia.
**Endpoints:** EP-002, EP-007, EP-016–EP-017, EP-021, EP-026.
**Prioridad:** P3.
**Aceptación:** registrar payload bytes, consultas SQL y latencia antes/después con la misma fixture sintética; no afirmar mejora sin medidas.
**Pruebas:** `T-SER-PERF-001` (si existe optimización aprobada).

#### SER-TEST-001 — Verificación automatizada

**EARS:** WHEN serialization contracts are implemented, THE system SHALL verify response shape, field exposure, input validation, status alternatives and functional compatibility through automated tests.
**Justificación/evidencia:** tests actuales cubren flujos, autorización y algunos payloads, pero no una allowlist completa para los modelos de salida.
**Endpoints:** EP-001–EP-028.
**Prioridad:** P1.
**Aceptación:** pruebas unitarias/HTTP relevantes pasan; los campos sensibles y extras siguen la política; OpenAPI incluye respuesta exitosa y errores alternativos documentados.
**Pruebas:** `T-SER-SHAPE-001`, `T-SER-INPUT-001`, `T-SER-OPENAPI-001`, `T-SER-COMPAT-001`.

#### SER-TEST-002 — Verificación manual documentada

**EARS:** WHEN an application environment and authorized synthetic credentials are available, THE system SHALL record manual verification of at least one auth/profile-equivalent route, one list route and one write/detail route in `/docs`, including expected and observed status/payload.
**Justificación/evidencia:** no hay endpoint de perfil; `POST /auth/tokens` sólo en desarrollo y las pruebas manuales no se ejecutaron en esta auditoría.
**Endpoints:** EP-001 (o constancia de ausencia de perfil), EP-007 o EP-021, EP-006/EP-009/EP-018.
**Prioridad:** P2.
**Aceptación:** registrar fecha/entorno, endpoint, código, payload sintético esperado/observado y resultado; no declarar ejecución antes de disponer del entorno.
**Pruebas:** `T-SER-MANUAL-001`.

## Criterios de aceptación de esta SPEC

- Inventario trazable con todos los 28 handlers reales y rutas de documentación separadas como excepciones técnicas.
- Cada endpoint tiene estado inicial, entrada, salida, consumidor conocido, campos, códigos relevantes, riesgo y prueba propuesta.
- Los requisitos EARS tienen identificador, prioridad, evidencia y aceptación verificable.
- `TASK-SER-006` es el único avance de implementación registrado; no se declara completado ningún requisito global de serialización. Toda reducción de campos y cambio de snapshots queda sujeta a compatibilidad/revisión.
- Entorno, versiones, falta de ejecución y riesgos se describen sin atribuir pruebas no realizadas.

## Matriz de trazabilidad

| Requisito | Endpoints | Diseño | Tasks | Pruebas/evidencia futura |
| --- | --- | --- | --- | --- |
| SER-FR-001 | EP-027–EP-028; todos | Respuestas explícitas + excepciones documentadas | TASK-SER-006, TASK-SER-015 | T-SER-HEALTH-001, T-SER-OPENAPI-001 |
| SER-FR-002 | EP-002–EP-007, EP-009–EP-026 | Whitelist de salida por schema | TASK-SER-007–TASK-SER-011 | T-SER-ORM-001, T-SER-SHAPE-001 |
| SER-FR-003 | EP-002, EP-007–EP-008, EP-013–EP-017, EP-021, EP-025–EP-026 | Item schemas preservando campos vigentes hasta aprobación | TASK-SER-008, TASK-SER-010 | T-SER-LIST-001 |
| SER-FR-004 | EP-002, EP-006–EP-025 | IDs/flattened; no carga anidada implícita | TASK-SER-007–TASK-SER-010 | T-SER-REL-001 |
| SER-FR-005 | EP-001, EP-003, EP-005–EP-006, EP-010–EP-012, EP-018–EP-025 | Contratos de escritura dedicados | TASK-SER-005, TASK-SER-007, TASK-SER-009 | T-SER-INPUT-001 |
| SER-FR-006 | Writes EP-001, EP-003, EP-005–EP-006, EP-010–EP-012, EP-018–EP-025 | Salida limitada por schema | TASK-SER-007, TASK-SER-009, TASK-SER-010 | T-SER-WRITE-001 |
| SER-SEC-001 | EP-001–EP-028 | Allowlist + pruebas de secretos | TASK-SER-004, TASK-SER-013 | T-SER-SECRET-001 |
| SER-SEC-002 | EP-001 | Preservar token temporal y gate ambiental | TASK-SER-004 | test existente + T-SER-SECRET-001 |
| SER-SEC-003 | EP-003–EP-006, EP-009–EP-026 | Clasificación de actor IDs y permisos sin ampliarlos | TASK-SER-003, TASK-SER-013 | T-SER-ACCESS-001 |
| SER-SEC-004 | EP-010, EP-015, EP-018–EP-026 | Snapshot allowlist/redacción sólo con aprobación | TASK-SER-003, TASK-SER-011 | T-SER-AUDIT-001 |
| SER-SEC-005 | Entradas EP-001, EP-003, EP-005–EP-006, EP-010–EP-012 | Política explícita de extras | TASK-SER-005 | T-SER-INPUT-001, T-SER-ACCESS-001 |
| SER-COMP-001 | EP-001–EP-028 | Comparación de OpenAPI y consumer contract | TASK-SER-002, TASK-SER-014–TASK-SER-015 | T-SER-COMPAT-001 |
| SER-NFR-001 | EP-002, EP-007, EP-016–EP-017, EP-021, EP-026 | Optimizar sólo tras medida | TASK-SER-012 | T-SER-PERF-001 |
| SER-TEST-001 | EP-001–EP-028 | Suite shape/security/input/OpenAPI | TASK-SER-013–TASK-SER-015 | T-SER-SHAPE-001, T-SER-INPUT-001, T-SER-OPENAPI-001 |
| SER-TEST-002 | EP-001, EP-007/EP-021, EP-006/EP-009/EP-018 | Evidencia manual con datos sintéticos | TASK-SER-016 | T-SER-MANUAL-001 |

## Definition of Done

La Definition of Done global sólo se satisface en la fase posterior y no se marca como cumplida ahora: inventario completo; contratos aplicables/excepciones documentados; sin proyecciones ORM no controladas; entradas/salidas separadas donde corresponda; ausencia verificada de secretos; listados y relaciones justificadas; compatibilidad revisada; suite/OpenAPI y tres pruebas manuales ejecutadas; auditoría inicial/final; requisitos y tareas trazables; revisión de Cumplimiento para auditoría/PHI; y bloqueos restantes descritos. Esta iteración sólo prepara documentos para aprobación.