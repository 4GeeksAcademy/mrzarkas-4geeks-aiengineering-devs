# Especificación — Optimización de rendimiento: Caching

Fecha: 2026-11-01. Estado: propuesta SDD; implementación no autorizada. Documentación en español; requisitos EARS normativos en inglés. MUST identifica entregables del ejercicio; los gates no se eluden para cumplirlos.

## Objetivo, alcance y autorizaciones

Reducir trabajo repetido sólo donde una medición lo justifique, conservando acceso y frescura de la información operativa de HealthCore Digital. HealthCore opera 12 clínicas, nueve US y tres UK, con obligaciones distintas HIPAA/UK GDPR y EHR no unificados: necesidad empresarial, no integración implementada. El sistema sigue siendo prototipo sintético pre-MVP, sin autorización de piloto/producción.

Esta fase crea exactamente spec.md, plan.md y tasks.md aquí. La instrucción posterior del usuario autoriza expresamente esta carpeta protegida del Memory Bank; no autoriza el resto del Memory Bank. No se cambia código, datos, Rules, configuración, contratos ni ramas. No se crea CACHING_REPORT.md. La ejecución espera revisión del usuario.

## Arquitectura y evidencia real

- La API central FastAPI está en `backend/`, no en `services/central-api/`. README raíz, sección Dockerization, documenta una excepción autorizada de ubicación; se conserva. Python 3.12, uv, SQLAlchemy async/asyncpg, PostgreSQL, Alembic y PyJWT verificados en `backend/pyproject.toml` y código.
- `frontend/package.json`: Next.js 16.4.3, React/ReactDOM 19.3.1, pnpm 10.18.3; scripts dev/build/start, sin test/lint. `frontend/app/page.js` es async Server Component, force-dynamic y fetch /status no-store, timeout 5 s. No cálculo costoso React cliente verificado.
- Los dos backoffices son HTML/CSS/JS nativos. Incidencias usa módulo ES `app.js` y `select-field.js`; Management contiene script inline. No son React y no admiten useMemo/React.lazy sin cambio de arquitectura.
- Git inicial limpio, staged/unstaged/untracked vacíos; rama actual `feature/caching-optimisation` ya existe. La primera tarea futura verifica y reutiliza la rama; no la crea otra vez.
- Fuentes consultadas: CONTEXT.md, AGENTS.md, tres documentos obligatorios, memory-bank/README.md y conventions.md; todos los Rules 01–09 y su índice; README raíz, frontend, services, backoffices, backend, docs y skills; skill validate-delivery; especificación previa de serialización y docs/serialization-measurement.json. No hay archivo de arquitectura específico localizado por nombre; las convenciones y README sirven de guía.
- Discrepancias conservadas: technology-stack.md dice que aún no existen aplicaciones; current-state.md sigue refiriéndose a la ruta antigua y pruebas históricas. backend/README.md documenta 145 tests del 2026-10-31: evidencia histórica, no tests ejecutados ahora. No se corrigen esas fuentes en esta entrega.

## Inventario completo de operaciones FastAPI

Inventario estático de decorators; no se ha iniciado la API. GET /docs, /redoc, /openapi.json y /docs/oauth2-redirect son rutas documentales automáticas, no cuatro operaciones de negocio adicionales. Para cada fila: frecuencia y latencia pendientes de medir; número de execute es indicio estático del cuerpo, no consultas reales ni helpers/commit/refresh. Las escrituras son inestables y quedan excluidas. Metadatos tienen estabilidad relativa pendiente; datos privados/auditoría son sensibles. Fuente de datos por dominio: auth usa emisión JWT/config; catálogos usan Catalog/CatalogValue; compliance usa ComplianceReview; incidents usa OperationalIncident/catálogos/historial/auditoría; management usa catálogos, referencias, cobertura y ManagementAuditEvent; status usa SELECT 1; health no DB.

| ID | Método y ruta | Evidencia : línea / handler | Capability/política | execute estático | Sensibilidad/selección |
| --- | --- | --- | --- | --- | --- |
| EP-CACHE-001 | POST `/auth/tokens` | `backend/app/auth/router.py:33` / `issue_token` | público / entorno dev-test para tokens | 0 | No cachear mutación |
| EP-CACHE-002 | GET `/catalogs/{catalog_name}` | `backend/app/catalogs/router.py:17` / `get_catalog` | catalog:read | 2 | Candidato: metadatos autenticados; clasificación pendiente |
| EP-CACHE-003 | POST `/compliance-reviews` | `backend/app/compliance/router.py:47` / `create_review` | complianceReview:manage | 0 | No cachear mutación |
| EP-CACHE-004 | GET `/compliance-reviews/{review_id}` | `backend/app/compliance/router.py:69` / `get_review` | complianceReview:read | 0 | Excluir: datos privados/auditoría |
| EP-CACHE-005 | PATCH `/compliance-reviews/{review_id}/status` | `backend/app/compliance/router.py:78` / `update_review_status` | complianceReview:manage | 0 | No cachear mutación |
| EP-CACHE-006 | POST `/incidents` | `backend/app/incidents/router.py:107` / `create_incident` | incident:create | 1 | No cachear mutación |
| EP-CACHE-007 | GET `/incidents` | `backend/app/incidents/router.py:184` / `list_incidents` | incident:list | 2 | Excluir: datos privados/auditoría |
| EP-CACHE-008 | GET `/incidents/metrics/open-by-severity` | `backend/app/incidents/router.py:225` / `open_incidents_by_severity` | incident:list | 2 | Excluir: datos privados/auditoría |
| EP-CACHE-009 | GET `/incidents/{incident_id}` | `backend/app/incidents/router.py:273` / `get_incident` | incident:read | 0 | Excluir: datos privados/auditoría |
| EP-CACHE-010 | PATCH `/incidents/{incident_id}` | `backend/app/incidents/router.py:286` / `update_incident` | actor + política contextual | 0 | No cachear mutación |
| EP-CACHE-011 | POST `/incidents/{incident_id}/transitions` | `backend/app/incidents/router.py:377` / `transition_incident` | actor + política contextual | 0 | No cachear mutación |
| EP-CACHE-012 | POST `/incidents/{incident_id}/assignments` | `backend/app/incidents/router.py:419` / `assign_incident` | incident:assign | 0 | No cachear mutación |
| EP-CACHE-013 | GET `/incidents/{incident_id}/history` | `backend/app/incidents/router.py:460` / `incident_history` | incident:read | 1 | Excluir: datos privados/auditoría |
| EP-CACHE-014 | GET `/incidents/{incident_id}/assignment-history` | `backend/app/incidents/router.py:475` / `incident_assignment_history` | incident:read | 1 | Excluir: datos privados/auditoría |
| EP-CACHE-015 | GET `/incidents/{incident_id}/audit` | `backend/app/incidents/router.py:492` / `incident_audit` | audit:read | 1 | Excluir: datos privados/auditoría |
| EP-CACHE-016 | GET `/management/catalogs` | `backend/app/management/router.py:78` / `list_catalogs` | catalog:read | 2 | Candidato: metadatos autenticados; clasificación pendiente |
| EP-CACHE-017 | GET `/management/catalogs/{catalog_name}/values` | `backend/app/management/router.py:85` / `list_catalog_values` | catalog:read | 2 | Candidato: metadatos autenticados; clasificación pendiente |
| EP-CACHE-018 | POST `/management/catalogs/{catalog_name}/values` | `backend/app/management/router.py:94` / `create_catalog_value` | catalog:manage | 1 | No cachear mutación |
| EP-CACHE-019 | PATCH `/management/catalogs/{catalog_name}/values/{value_id}` | `backend/app/management/router.py:113` / `update_catalog_value` | catalog:manage | 0 | No cachear mutación |
| EP-CACHE-020 | POST `/management/catalogs/{catalog_name}/values/{value_id}/activation` | `backend/app/management/router.py:139` / `set_catalog_value_activation` | catalog:manage | 0 | No cachear mutación |
| EP-CACHE-021 | GET `/management/reference-data/{resource}` | `backend/app/management/router.py:157` / `list_reference_values` | referenceData:read | 2 | Candidato: metadatos autenticados; clasificación pendiente |
| EP-CACHE-022 | POST `/management/reference-data/{resource}` | `backend/app/management/router.py:165` / `create_reference_value` | referenceData:manage | 1 | No cachear mutación |
| EP-CACHE-023 | PATCH `/management/reference-data/{resource}/{resource_id}` | `backend/app/management/router.py:188` / `update_reference_value` | referenceData:manage | 0 | No cachear mutación |
| EP-CACHE-024 | POST `/management/reference-data/{resource}/{resource_id}/activation` | `backend/app/management/router.py:218` / `set_reference_value_activation` | referenceData:manage | 0 | No cachear mutación |
| EP-CACHE-025 | PUT `/management/affected-systems/{system_id}/jurisdictions` | `backend/app/management/router.py:233` / `set_system_jurisdictions` | referenceData:manage | 3 | No cachear mutación |
| EP-CACHE-026 | GET `/management/audit-events` | `backend/app/management/router.py:259` / `list_management_audit_events` | audit:read | 2 | Excluir: datos privados/auditoría |
| EP-CACHE-027 | GET `/health` | `backend/app/main.py:52` / `health` | público / entorno dev-test para tokens | 0 | Excluir: diagnóstico vivo |
| EP-CACHE-028 | GET `/status` | `backend/app/main.py:66` / `status` | público / entorno dev-test para tokens | 0 | Excluir: diagnóstico vivo |

Todas las lecturas autenticadas dependen de Actor y las que acceden a DB de get_session. Incidencias aplica visible_incident_area_id y políticas de recurso; Compliance limita lectura a admin/compliance y reconoce que JWT no lleva jurisdicción. Management usa capability; no se presume aislamiento clínico/jurisdiccional implementado. Mutaciones usan commit y auditoría: la invalidación nunca debe sustituir esas operaciones.

## Inventario frontend y priorización coste × frecuencia × estabilidad × sensibilidad

| Candidato/ruta real | Trabajo y carga | Frecuencia | Estabilidad | Sensibilidad | Decisión |
| --- | --- | --- | --- | --- | --- |
| frontend/app/page.js `/`: Home, Icon, Brand, SectionHeading | Server render, dos tarjetas, imagen hero next/image preload; /status cada render | Pendiente | Contenido institucional estable; estado vivo | Estado técnico | No deferir hero/LCP ni añadir cliente por dos tarjetas |
| frontend/app/layout.js y section-heading.js | Layout/estructura semántica, sin cálculo no trivial | Pendiente | Alta | No sesión | No useMemo ni dynamic sin beneficio |
| app.js `#/incidents` renderList | Página de 20; búsqueda repetida de labels en arrays; filtros/sort backend | Pendiente | Variable | Operativo autenticado | Baseline inicial; alternativa índices Map si perfil justifica |
| app.js `#/incidents/new` renderCreate | Formulario y catálogos/referencias en memoria | Pendiente | Variable | Autenticado/escritura | Conservar validación/UX; no elegir sobre carga crítica sin medir |
| app.js `#/incidents/{uuid}` renderDetail | Detalle, tres GET, editor/acciones y cronología map+sort O(n log n) | Pendiente | Variable | Texto/historial privado | L1: separar implementación y cargar import() al navegar; candidato nativo válido condicionado a perfil/aceptación |
| app.js `#/summary` renderMetrics, despachada por renderRoute | GET agregado, tarjetas por severidad | Pendiente | Cambia con incidencias | Agregado sujeto a área | L2: separar implementación import() al navegar; candidato nativo condicionado |
| management/index.html `/management/` | Catálogos, referencias y auditoría cargados sólo al click; script inline/table | Pendiente | Mixta | Incluye actor IDs/auditoría | Ya difiere datos; separar script minúsculo no prueba mejora |
| renderDetail: combinación/sort de statusHistory y assignmentHistory | Cálculo no trivial algorítmicamente, coste medido desconocido | Pendiente | Por historial recibido | Histórico privado | M1 alternativo nativo; NO useMemo actual |
| GET /catalogs/{catalog_name} | Dos SELECT, orden y filtro temporal | Al conectar: cuatro llamadas distintas, no tasa real | Catálogo cambia por gestión/tiempo | Labels/descripción autenticados | C1 prioritario, perfil y clasificación obligatorios |
| GET /management/catalogs/{catalog_name}/values | Lookup + count + página | Consumidor de valores local no identificado | Cambia por gestión | Incluye metadata actor | C2 provisional, frecuencia/coste y clasificación aún no acreditados |
| GET /management/reference-data/{resource} | Count + página; cuatro llamadas al conectar | Pendiente | Maestros relativamente estables | IDs/actores/jurisdicción | Alternativa C3; requiere invalidación por recursos y revisión privacidad |
| GET /incidents/metrics/open-by-severity | Dos agregaciones SQL | Pendiente | Cambia en create/update/transition/assignment y catálogos | Agregado por ámbito | Alternativa de mayor coste, gate Compliance; no selección inicial |

L1/L2 no usarán next/dynamic ni React.lazy: ese requisito tecnológico queda B1 si el evaluador no acepta import() nativo. No se inventa componente React, gráfico o dashboard. Memoización de cronología nativa o índices Map NO satisface literalmente useMemo: B2 debe resolverse con ajuste aprobado del ejercicio o una tarea React independiente expresamente autorizada. No se importa el backoffice en la landing.

## Requisitos EARS y aceptación

Cada fila define un requisito atómico, evidencia y prueba. FR-003/004/005/006/007/008/009/010 son MUST del ejercicio con gates explícitos; medición, seguridad y regresión son MUST de entrega. El resto aplica como condición técnica. No hay umbral de mejora inventado: tras baseline se acuerda umbral y variabilidad antes de optimizar, o se rechaza candidato sin coste suficiente.

| ID | Formulación EARS | Evidencia | Criterio de aceptación |
| --- | --- | --- | --- |
| FR-CACHE-001 | THE SYSTEM SHALL preserve the 28 verified API operations and their observable contracts. | backend/app/*/router.py; app/main.py | Comparación OpenAPI y HTTP: mismos campos, orden, wrappers, límites, errores y permisos. |
| FR-CACHE-002 | THE SYSTEM SHALL inventory every API operation and relevant frontend route before selecting optimisations. | Inventarios de esta especificación | 28 operaciones reconciliadas por AST/OpenAPI; consumidores y coste medido documentados. |
| FR-CACHE-003 | WHEN an approved deferred incident-detail route is entered THE SYSTEM SHALL load its implementation on demand. | uis/backoffice/operational-incidents/app.js: renderDetail | Chunk ausente en cola inicial, presente al entrar en detalle; fallback, error y reintento accesibles. |
| FR-CACHE-004 | WHEN an approved deferred metrics route is entered THE SYSTEM SHALL load its implementation on demand. | uis/backoffice/operational-incidents/app.js: renderMetrics | Chunk de métricas ausente inicialmente; ruta y permisos conservados; carga repetida no duplica listeners. |
| FR-CACHE-005 | WHERE a measured non-trivial calculation exists in an approved React client component THE SYSTEM SHALL memoize that calculation with complete dependencies. | Frontend actual: bloqueo B2; cronología nativa como alternativa | Perfil demuestra coste; identidad/valores de todas las dependencias probados; igualdad de resultado; sin prometer menos renders. |
| FR-CACHE-006 | WHEN an authorized active-catalog read misses the cache THE SYSTEM SHALL load and serialize the current catalog before storing a bounded TTL entry. | backend/app/catalogs/router.py: get_catalog | Miss consulta fuente; hit equivalente; auth se ejecuta siempre; 404/errores no almacenados. |
| FR-CACHE-007 | WHEN an authorized managed-catalog-values read misses the cache THE SYSTEM SHALL load the requested page before storing a bounded TTL entry. | backend/app/management/router.py: list_catalog_values | items/total/orden idénticos; páginas y catálogos no colisionan; offset/limit se validan antes del lookup. |
| FR-CACHE-008 | WHEN a catalog mutation commits THE SYSTEM SHALL prevent subsequent reads from using a pre-commit catalog generation. | Management: create/update/activation; Catalog.version | Tres escrituras probadas para ambas lecturas; rollback no invalida; race de refill antiguo no se publica. |
| FR-CACHE-009 | IF an entry expires or crosses a catalog effective-date boundary THEN THE SYSTEM SHALL recompute the response. | CatalogValue.effective_from/effective_to | Reloj controlado en igualdad de frontera, antes/después; un valor futuro aparece y uno expirado desaparece sin escritura. |
| FR-CACHE-010 | THE SYSTEM SHALL produce a reproducible CACHING_REPORT.md after authorised implementation and measurements. | Ubicación futura propuesta: docs/CACHING_REPORT.md | Incluye metodología, before/after, claves, TTL, hit ratio, frescura, exclusiones, riesgos y artefactos; no crear en fase actual. |
| NFR-CACHE-001 | THE SYSTEM SHALL record comparable backend baseline and post-change measurements. | docs/serialization-measurement.py como referencia | p50/p95, SQL/request, llamadas, bytes, hit/miss; mismo dataset, permisos, concurrencia, entorno y warmup. |
| NFR-CACHE-002 | THE SYSTEM SHALL measure frontend load and calculation costs before and after each change. | frontend/; audit/; backoffice app.js | Chunks/bytes/waterfall, marcas de cálculo y UX; Profiler/commits sólo si existe React cliente. |
| NFR-CACHE-003 | WHERE synthetic scaling is authorised THE SYSTEM SHALL seed an isolated local dataset idempotently. | backend/app/reference_data/seed.py; catalogs/seed.py como referencia | Conteos antes/después, relaciones US/UK válidas, límites, segunda ejecución estable y rollback/limpieza aislada. |
| NFR-CACHE-004 | IF caching fails THEN THE SYSTEM SHALL execute the uncached authorised read without masking a source failure. | Lecturas seleccionadas | Fallo/timeout/serialización de caché probado; errores fuente originales; sin 200 vacío ficticio. |
| NFR-CACHE-005 | WHILE requests concurrently target one key THE SYSTEM SHALL bound duplicate fills and reject obsolete generations. | Capa propuesta junto a backend/app/catalogs/ | Single-flight por clave/generación, cancelación y timeout probados; locks liberados; límite global probado. |
| NFR-CACHE-006 | THE SYSTEM SHALL bound cache memory and preserve behaviour after restart and across supported workers. | backend/; despliegue actual pendiente de verificar al ejecutar | LRU con techo bytes/entradas; reinicio vacío; dos workers ven generación nueva; datos inmutables serializados. |
| NFR-CACHE-007 | THE SYSTEM SHALL pass regression and document unresolved performance decisions before delivery. | backend/tests/; frontend/README.md | Suite aislada, builds y revisión manual; sin resultados inventados ni tareas bloqueadas completadas. |
| SEC-CACHE-001 | WHEN a cached read is requested THE SYSTEM SHALL authenticate and authorize the caller before accessing cached content. | backend/app/auth/dependencies.py; policies.py | Token inválido/expirado y rol sin capability denegados tras calentar con actor válido; auth no cacheada. |
| SEC-CACHE-002 | THE SYSTEM SHALL isolate entries by every dimension that can change the authorized response. | Actor(id, role, area_id); catálogos | Dos identidades/roles/áreas no comparten respuesta privada; dimensiones no presentes no se inventan como controles. |
| SEC-CACHE-003 | THE SYSTEM SHALL exclude credentials, PHI and sensitive readable identifiers from cache keys and telemetry. | Ambas capas candidatas | Claves mediante digest no reversible de partición interna; logs sólo ruta plantilla/estado; sin JWT/query/raw body. |
| SEC-CACHE-004 | THE SYSTEM SHALL bypass public intermediary caching for private or session responses. | Lecturas autenticadas; frontend cache:no-store | Sin CDN/browser/proxy público ni caché Next de sesión; revisión de headers sujeta a aprobación si cambia contrato. |
| SEC-CACHE-005 | WHERE privacy, retention, audit or health-data processing is affected THE SYSTEM SHALL require Compliance and Data Governance review before implementation. | AGENTS.md; Claire Whitfield | Gate firmado para cualquier impacto; sin aprobación de producción ni transferencia sanitaria US/UK por este diseño. |

## Política propuesta de caché, aislamiento y frescura

Capa preferida para explorar: cache-aside in-process, sin dependencia nueva, aprobada sólo tras baseline. No functools.lru_cache sin expiración real. Redis no existe en dependencias verificadas: alternativa sujeta a aprobación de dependencia, infraestructura y operación.

| Política | C1 activo | C2 Management values |
| --- | --- | --- |
| TTL inicial propuesto, no observado ni aprobado | Máximo 60 s; reducido por siguiente frontera de vigencia | Máximo 30 s; no filtro temporal: frescura de edición |
| Fundamentación | Lectura estable relativa; nunca sacrificar effective_from/to | Menor tolerancia de vista administrativa; validar con propietario |
| Clave interna | Namespace aplicación/entorno+endpoint+versión contrato+digest catalog_name+generación Catalog.version+partición autorización | Mismo esquema + offset/limit normalizados |
| Partición inicial conservadora | Digest interno de identidad, rol, area_id y revisión de política | Igual; sin compartir metadata privada entre usuarios |
| Invalidación | POST/PATCH/activation de valores tras commit; active/version consultados antes de hit | Mismas mutaciones; generación consultada antes de hit |
| Fuente/serialización | CatalogResponse JSON validado; nunca ORM/session/request | CatalogValueListResponse JSON validado; conservar todos campos |
| Errores/bypass | No almacenar 401/403/404/422/5xx ni resultado de mutación | Igual; parámetros extra relevantes sin normalizador = bypass |

Dimensiones evaluadas: usuario/rol/área son Actor real; clínica, jurisdicción y tenant no son claims actuales ni filtros de estos dos endpoints. Si en el futuro influyen, deshabilitar caché hasta integrar partición validada: no usar un valor global para simular aislamiento. Lenguaje y versión de contrato: no hay locale actual verificado; hoy representación fija, namespace de contrato interno sin cambiar API. Filtros y paginación: C1 sólo catalog_name; C2 catalog_name/offset/limit. Cambios de políticas se aplican cada lectura y cambian namespace; token/cookies nunca entran en clave. Un digest no sustituye permisos ni permite loguear raw inputs. Cache sólo dentro del servicio, no compartida públicamente.

Para múltiples workers, consultar Catalog.version e is_active en DB antes del hit. Así se conserva una consulta por hit y se mide ese coste; no anunciar cero SQL. No leer versión sólo desde memoria. Las escrituras existentes incrementan version; verificar todas las vías, seeders y edición directa: operaciones externas sin version deben vaciar cachés o forzar bypass, no se presumen cubiertas. Cada refill captura generación y la verifica antes de publicarse; un commit concurrente invalida el refill. Las lecturas ya iniciadas antes del commit siguen la semántica de aislamiento DB; una lectura nueva posterior nunca acepta generación anterior. Rollback no publica invalidación ni datos.

C1 requiere descubrir la siguiente effective_from futura y effective_to vigente, incluso de valores aún excluidos; conservar semántica inclusiva effective_to >= now. Prueba frontera exacta y primer instante posterior; ante incertidumbre de reloj bypass. No confiar sólo en resultados activos para calcular próxima activación. Expiración monotónica, timestamps UTC de fuente y verificación temporal antes del hit; no servir stale-while-revalidate. Límites propuestos 256 entradas/8 MiB por worker y 256 KiB por respuesta: hipótesis de operación a ratificar; entrada demasiado grande se omite. LRU y limpieza de expiradas; single-flight/locks limitados con timeout propuesto 2 s, liberación por finally/cancelación. Fallo de caché => lectura origen autorizada; fallo de DB => comportamiento original. Reinicio frío; Redis futuro requiere protocolo coherente de generación, fallos y revisión operacional.

## Medición y datos reproducibles

Observado en artefacto histórico `docs/serialization-measurement.json`: 100 incidencias sintéticas, descripción 9200 caracteres, limit 25, 50 muestras y 5 warmup, ASGI/sesión reutilizada. Dos rondas sin optimización: incidents p50 1.401/1.389 ms, p95 1.645/1.566; clinics p50 0.893/0.931, p95 1.147/1.295; ambas 2 SELECT, 0 relationship loads; 17598/755 bytes. No son baseline del caching ni demuestran beneficio. No se han medido ahora latencias ni tráfico.

Protocolo futuro propuesto: registrar commit/locks/runtime/CPU/worker/DB y dataset, seeds/hash, número de filas por tabla y distribución US/UK por FK real; separar ASGI de HTTP con red. Tres rondas de 200 lecturas por caso tras 20 warmup, concurrencias 1 y 10, orden alternado A/B, mismos usuarios/filtros/páginas. Documentar mediana/p95 mediante percentil nearest-rank, muestras fallidas separadas, variación entre rondas. Medir frío, caliente, TTL, invalidación y bypass; hit ratio=hits/(hits+misses), excluir bypass y explicar denominador; llamadas SQL contadas separando autorización/generación de consulta datos; payload bytes UTF-8. No registrar parámetros SQL/query strings ni cuerpos. Frecuencia medida con contadores ruta plantilla, sin IDs dinámicos, no inferida de tamaño del dataset.

Seeder futuro local idempotente: propuesta escalones 100/1000/10000 incidencias con límite máximo aprobado, catálogos existentes válidos, historias variables y sólo textos sintéticos; distribución 9:3 como escenario declarado, no dato real. No inflar catálogos para fabricar necesidad; reportar filas efectivas. Dry-run/namespace sintético, manifiesto, FK coherentes, transacción aislada y rollback preferido; limpieza sólo de ese namespace con aprobación expresa, nunca truncate ni borrar volúmenes. Seeds actuales no se ejecutan en esta fase.

Frontend: producción Next para landing; servidor estático real para backoffice, caché navegador frío/caliente y red/CPU fijos, desktop/mobile reproducibles. Waterfall/bytes parse/long tasks, tiempos de carga ruta y cálculo mediante performance.mark sin contenido de incidentes. React DevTools Profiler sólo en componente cliente React si se autoriza: commits y actualDuration, dependencias estables, coste de cálculo aislado. Preservar hero/SEO/HTML SSR, headings/anclas y ausencia de errores de hidratación. Fallback de rutas nativas con aria-busy/aria-live, reintento y foco; import() fallido no rompe sesión, ruta ni navegación.

## Negativos, exclusiones y decisiones pendientes

No cachear health/status, JWT, mutaciones, permisos, auditoría, historial, detalle, listas privadas o ComplianceReview. Estado de DB debe detectarse vivo; caché no encubre SELECT 1. No cambiar response_model, HTTP, orden, paginación ni redacción audit-output-v1. Pruebas: catálogo inexistente/inactivo, páginas vacías/límite/422, expirar token después del warmup, roles sin capability, dos áreas/usuarios, clock boundary, update/activation/create/rollback, lectura concurrente con escritura, oversize/memoria/locks, dos workers y reinicio, outage DB/caché. No PHI en logs, muestras o fixtures. No certificación normativa por seguir instrucciones.

- B1: candidatos L1/L2 reales sólo nativos; exigir next/dynamic/React.lazy deja criterio tecnológico bloqueado. Resolver con evaluador antes de implementación.
- B2: no cálculo costoso React ni componente cliente real. useMemo queda bloqueado; medir cronología y aceptar adaptación o autorizar alcance React separado sin duplicar apps.
- B3: C1/C2 son implementables en diseño, pero coste/frecuencia suficientemente altos aún no demostrados; C2 sin consumidor local encontrado. Si baseline no justifica dos, documentar bloqueo y evaluar C3/métricas con nuevos gates.
- B4: clasificación de labels/descriptions/actor metadata y autorización de almacenamiento/invalidation pendientes; revisión Claire para impactos de privacidad/retención/auditoría. JWT sin scope jurisdiccional no permite inventarlo.
- B5: TTL, límites y umbral de mejora requieren aprobación técnica/producto; Redis/dependencias/infra no autorizados. No modificar Memory Bank adicional para resolver convenciones.

## Cobertura 4Geeks y trazabilidad

| Criterio | SPEC | PLAN | TASKS | Evaluación |
| --- | --- | --- | --- | --- |
| Dos Lazy Loading | FR-CACHE-003/004, NFR-CACHE-002 | P3/P4 | 008/009 | Chunks y UX; B1 para tecnología React |
| Un useMemo no trivial | FR-CACHE-005 | P3/P4 | 007/010 | Profiler y dependencias; B2 pendiente |
| Dos endpoints TTL | FR-CACHE-006/007/009 | P3/P5 | 011/012/013/022/015 | Hit/miss/SQL/TTL; B3/B4 |
| Invalidación | FR-CACHE-008 | P5/P6 | 014/016 | Commit/rollback/race/dos workers |
| Datos y benchmark | NFR-CACHE-001/002/003 | P1/P2/P6 | 003–006/018 | Conteos, perfiles y before/after |
| Seguridad y regresión | SEC-CACHE-001–005; FR-CACHE-001; NFR-CACHE-004–007 | P5/P6/P7 | 011/016/017/019/021 | Identidades, resiliencia, contratos |
| CACHING_REPORT.md | FR-CACHE-010 | P7 | 020 | Informe futuro con resultados reales |

Documentos SDD aceptables aunque expliciten bloqueos de implementación. El reto no se declara superado hasta resolver B1/B2/B3 y ejecutar toda validación futura.
