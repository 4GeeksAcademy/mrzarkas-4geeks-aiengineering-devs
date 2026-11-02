# Evidencias de implementación — migrationBackoffice

## Task y referencia

Implementar el SDD Next.js en `migration/backofficeMigration`, únicamente para desarrollo sintético. Fecha de ejecución: 2026-11-02. Sin commit, push, PR ni despliegue. La autorización expresa del desarrollador fue «Autorizo ese alcance para desarrollo sintético» para dependencias, JWT memoria, permisos existentes, proxy/convivencia local, NEW UI Inventory y evidencias de estos SDD.

La implementación está disponible en `/uis/backoffice`; el cierre global del SDD no está aceptado. Este registro documenta resultados de ejecución, no cumplimiento HIPAA/UK GDPR ni aprobación de Claire Whitfield.

## Archivos y fuentes inspeccionados

`changed-files.json` enumera exhaustivamente archivos nuevos y SHA-256, excluyendo su propio hash. Git no tenía cambios tracked staged/unstaged al inicio ni al final; se revisaron los archivos untracked además de `git diff`. Sólo se añaden runtime/tests/docs del backoffice, override local y SDD autorizados.

Contexto leído: CONTEXT, AGENTS, product-context, technology-stack, current-state, índice Memory Bank/conventions; Rules README y 01/02/05/06/07/08/09; README raíz/uis/frontend/Management/incidencias, SDD Inventory D-01–08 y migrationBackoffice. Se contrastó código `/backend` y legacy; no se corrigieron silenciosamente discrepancias históricas. Snapshot/generated.ts se verificaron mecánicamente contra OpenAPI actual y generación reproducible, incluyendo parámetros, schemas y seguridad.

## Validaciones ejecutadas

Los comandos se ejecutaron desde raíz salvo indicación. Las variables descritas son ficticias o secretos aleatorios en memoria; ningún comando lee `.env` ni apunta a BD compartida. Las dependencias se resolvieron con pnpm frozen lockfile. Node de QA: 24.21.0; Python backend: 3.12.11; Chrome headless del sistema: 156; Next16.4.3/React19.3.1/TS5.9.3/pnpm10.18.3.

| ID | Comando/entorno | Resultado observado |
| --- | --- | --- |
| E-00 | Lectura contextual + `git branch --show-current`, `git status --short`, `git diff`, `git diff --cached` | Rama correcta, legacy/backend/stack default intactos; alcance explícito registrado. |
| E-01 | `backend/.venv/bin/python` importó `app.main:app` con APP_ENVIRONMENT=test, DATABASE_URL vacío, clave JWT ficticia; comparación JSON `app.openapi()` con contracts/openapi.json | PASS, exit0; sin conexión DB, snapshot actual idéntico. |
| E-02 | `podman run --rm -v <repo>/uis/backoffice:/work -w /work -e NEXT_TELEMETRY_DISABLED=1 node:24-alpine sh -c 'corepack enable && pnpm types:check && pnpm typecheck && pnpm test && pnpm build'` | PASS, exit0; tipos sin drift, TS strict, 40 tests/5 archivos y build de todas las rutas. `pnpm types:generate` también se ejecutó y types:check repitió PASS. |
| E-03 | En uis/backoffice: `HC_SYNTHETIC_TESTS=1 BACKOFFICE_TEST_URL=http://127.0.0.1:8081 /private/tmp/healthcore-backoffice-toolchain/node_modules/node/bin/node node_modules/@playwright/test/cli.js test` | PASS, exit0, 15 escenarios/12.1s, sin skips/retries. Nginx temporal -> contenedor standalone directo -> API fixture18190. 12 escenarios previos también pasaron directamente contra Next13100. |
| E-04 | `/private/tmp/healthcore-inventory-py312/bin/python uis/backoffice/scripts/validation-regression.py` | PASS, exit0, 64 tests/1.47s sin skips. PostgreSQL nuevo inventory_validation_backoffice, migraciones head y seeds sintéticos; cleanup stop. Tests auth/http_authorization/incident_workflows/inventory/inventory_demo/inventory_audit_policy/management_openapi existentes. |
| E-05 | `node --test uis/backoffice/operational-incidents/telemetry/tests/*.test.mjs` | PASS, exit0, 74 tests nativos; no modificación de ese runtime/contrato. Esto no sustituye ensayo del adaptador React opt-in. |
| E-06 | `podman build -t hc-backoffice-next:validation uis/backoffice` y `podman run --rm ... hc-backoffice-next:validation` | PASS, exit0 build; imagen 3dd676437669, standalone listo, USER node. Runtime temporal con API sintética, no despliegue. Arranque nativo `node scripts/start.mjs` también listo en13101. |
| E-07 | Compose `--env-file /dev/null -f docker-compose.yml -f docker-compose.backoffice-next.yml config --format json`, variables ficticias; `podman exec hc-backoffice-proxy-validation nginx -t` | PASS, exit0. Un único target de template, servicio Next sin puerto público añadido, mismo volumen DB. Nginx sintaxis correcta. `/`, `/management/`, `/next`, deep links y SVG200; alias API401 y auth issuer404. Tras detener proxy, legacy `/` y `/management/` siguieron200 mediante fixture read-only8080. |
| E-08 | Revisión de archivos nuevos, patrón private keys/cloud tokens, storage/network sintéticos, `git diff --check` y verificación de whitespace de untracked | Sin secretos/PHI reales encontrados ni tracked changes; tokens de QA en memoria, no trace/video/screenshots de E2E. No es certificación de escáner especializado. |
| E-09 | En backoffice: `HC_SYNTHETIC_TESTS=1 /private/tmp/healthcore-backoffice-toolchain/node_modules/node/bin/node scripts/measure.mjs ../../memory-bank/specs/migrationBackoffice/nextjs-migration/performance.json` | PASS exit0; Management sólo, tres cold/warm por1350/393px, misma API fixture, producción standalone. Métricas completas en performance.json. No presupuesto aprobado. |

Las rondas iniciales detectaron aserciones demasiado amplias (`alert` incluía anunciador Next), una lectura antes del rerender de lotes, status esperado201 cuando configuration devuelve200 y cabecera Cache-Control duplicada. Se corrigieron y repitieron las pruebas; no se ocultan como PASS. El ensayo Nginx por puertos del host Podman tuvo fallos intermitentes de conexión upstream502; el ensayo final usó conexión directa entre contenedores y pasó íntegramente. No se introdujeron retries de escrituras para ocultar fallos.

La captura visual sintética móvil se inspeccionó en `/private/tmp/hc-next-mobile.png`, sin campo JWT visible. Verificó marca, reflow, tabla desplazable y formulario en393px; no se añade al repositorio ni se presenta como validación manual completa WCAG.

## Matriz de aceptación del SDD

Cada fila evalúa el criterio original del SDD, no sólo presencia de código. BLOCKED significa evidencia/revisión insuficiente para cerrar ese criterio; no significa que no exista implementación.

| Requisito | Estado | Método y evidencia |
| --- | --- | --- |
| REQ-ARCH-001 | PASS | Rutas App Router/strict TS/features; build y typecheck E-02. |
| REQ-ARCH-002 | PASS | Sin SQL/políticas ni claves JWT en Next; allowlist y backend intacto. |
| REQ-MIG-001 | BLOCKED | 15 escenarios verifican paridad seleccionada; falta matriz completa antes de activar todos los módulos. |
| REQ-MIG-002 | PASS | Raíz/Management/Next/deep links coexistieron en Nginx; filtros/atrás/adelante E2E. |
| REQ-MIG-003 | PASS | No se solicitó ni ejecutó retirada; legacy sin diff y gate conservado. |
| REQ-MIG-004 | PASS | NEW UI autorizada expresamente; E-03 contra API vigente y E-04 conserva invariantes INV-AC. |
| REQ-UI-001 | BLOCKED | Tokens y pantalla móvil inspeccionados; aprobación visual comparativa completa pendiente. |
| REQ-UI-002 | PASS | Loading/empty/error y recuperación; cliente10/ui3 y Management/422/403 en E-03. |
| REQ-UI-003 | PASS | Filtros/orden/offset en URL, página20 y retorno detalle; E2E Queue filters. |
| REQ-AUTH-001 | PASS | JWT memoria, input borrado, firma manipulada401, storage/cookies vacíos; E-03 y auth E-04. |
| REQ-AUTH-002 | PASS | Disconnect abort/epoch, late response y reload probados; cleanup telemetría en provider. |
| REQ-AUTH-003 | PASS | Aviso de reconexión y enlaces legacy; ningún transporte automático de token. |
| REQ-RBAC-001 | PASS | 403 área ajena, asignación no admin y clínica UK reales; sin éxito falso. |
| REQ-RBAC-002 | PASS | Editor title/description área propia; ajena403 y severidad403 reales. |
| REQ-RBAC-003 | PASS | Direction sin detalle/catalogs/prefetch ni mutaciones; E2E y presentation14. |
| REQ-RBAC-004 | PASS | Cinco roles independientes y scopes UI/API; inventoryAdmin sin stock; E-03/E-04. |
| REQ-API-001 | PASS | Snapshot igual a backend actual; tipos compilados y requests E-03 preservan métodos/DTO. |
| REQ-API-002 | PASS | OpenAPI 7.13.0 generado/repetible, aliases transportados separados de presentación; E-01/E-02. |
| REQ-API-003 | PASS | Arrays offset/limit sin total; botón Siguiente sigue habilitado, ui3. |
| REQ-API-004 | PASS | Opciones vigentes/activas, clínica por jurisdicción, reporter omitido; alta E2E. |
| REQ-DATA-001 | PASS | POST aplicado y respuesta abortada: un artículo/una escritura, bloqueo y consulta autoritativa. |
| REQ-DATA-002 | PASS | useQuery path/session id + abort; late response descartada al logout, session2. |
| REQ-DATA-003 | PASS | Sin optimistic update; detalle/history/stock se releen tras confirmación; E-03. |
| REQ-DATA-004 | PASS | Pack2x10, count19 delta-1, correction20/409, igualdad y lotes; E-03/E-04. |
| REQ-SEC-001 | PASS | Fixtures sintéticos, JWT sólo memoria, sin trace/video; escaneo/revisión E-08, access_log off. |
| REQ-SEC-002 | PASS | React texto escapado; prueba HTML malicioso de DataTable, sin dangerouslySetInnerHTML. |
| REQ-SEC-003 | PASS | Proxy no-store, sin cookies, sin auth data en estático/prefetch; forward11 y E-03. |
| REQ-SEC-004 | BLOCKED | Default false y runtime nativo74 PASS; falta ensayo nuevo opt-in/StrictMode y D-07. |
| REQ-ACC-001 | BLOCKED | Skip/Tab semántico y native dialog presentes; verificación manual completa de acciones por QA pendiente. |
| REQ-ACC-002 | BLOCKED | FieldErrors/aria y retorno dialog implementados; revisión manual integral de foco/errores pendiente. |
| REQ-ACC-003 | BLOCKED | Axe WCAG2.2 sin violaciones en Management/Inventory a 320/393/1350; falta revisión manual/zoom completa. |
| REQ-PERF-001 | BLOCKED | Management medido tres cold/warm, dos anchuras; falta baseline del resto de módulos. |
| REQ-PERF-002 | BLOCKED | D-08 sin presupuesto aprobado; ninguna ruta reemplazada ni retirada. |
| REQ-PERF-003 | BLOCKED | Timeline lazy/memo acotado al merge; falta comparación Profiler 20/200/2000 para aceptar optimización. |
| REQ-TEST-001 | BLOCKED | Suite seleccionada PASS; la matriz íntegra Q y gates por módulo no se declaran cerrados. |
| REQ-TEST-002 | PASS | 64 pruebas backend actuales ejecutadas en BD nueva; no se cuentan como pruebas UI. |
| REQ-OPS-001 | BLOCKED | Disponibilidad legacy tras apagar proxy ensayada; falta rollback de activación por módulo/versión aprobada. |
| REQ-OPS-002 | BLOCKED | Configuración local preparada, sin despliegue; D-05/D-07 siguen pendientes para activación. |
| REQ-OPS-003 | PASS | API dev/test y fresh PostgreSQL, datos sintéticos, sin shared stack ni entorno real. |

### Inventory y tareas

INV-AC-001–020 conservan la aceptación contra API existente: el frontend no cambia invariantes. E-04 ejecutó las pruebas backend de altas/edición/baja, cantidades enteras, lotes, no negativos, stock SUM(delta), concurrencia, pack snapshots, reorden y roles; E-03 añadió aceptación UI de alta/lotes/baja, configuración/pack/conteo/corrección única, denegaciones por país y auditoría. No atribuir todas las pruebas negativas backend a la UI. La aprobación de exposición real sigue pendiente D-07.

Los 34 criterios de tareas están evaluados individualmente en las filas Estado/Evidencia de tasks.md. IN_PROGRESS/BLOCKED no equivalen a DONE. Las tareas implementadas pueden revisarse por responsabilidad: runtime/contratos, sesión/proxy, Management, incidencias, Inventory, validación/docs. No se creó ningún commit.

## Rendimiento observado

Medianas combinando las dos anchuras (6 observaciones por app/cache):

| Management | Datos listos frío | Datos listos warm | JS gzip recomprimido |
| --- | --- | --- | --- |
| Legado | 46.5ms | 57ms | 9,070 bytes |
| Next | 105.5ms | 48.5ms | 151,868 bytes |

TTFB frío: legado0.45ms/Next2.35ms; LCP frío40ms/44ms; CLS observado0 en ambos. Red loopback sin throttling; no extrapolar a producción ni a otras vistas. Datos listos incluye click de conexión y la validación adicional de JWT en Next. JS gzip se recomprime desde scripts realmente solicitados, no mide compresión de red; incluye telemetría nativa cargada aunque desactivada. Next añade142,798 bytes (139.5KiB). D-08 necesita budgets aprobados antes de reemplazar rutas; este resultado no afirma mejora global.

## Riesgos y recomendaciones correctivas

1. D-07: revisión de Claire Whitfield/Cumplimiento y Gobierno del Dato pendiente para auditoría/telemetría/exposición y cualquier uso real. El permiso sintético del desarrollador no la sustituye.
2. Completar comparación visual/keyboard/zoom manual WCAG2.2AA, caracterización íntegra por roles y matriz Q antes de activación.
3. Medir cola/detalle/forms/Inventory y Profiler 20/200/2000, revisar coste JS y aprobar D-08. Lazy/memo del timeline no tiene todavía evidencia suficiente para aceptar REQ-PERF-003.
4. Ensayar opt-in/StrictMode del adaptador nuevo con contexto regional validado; default permanece false y no hay eventos nuevos Inventory.
5. D-05: ensayar rollback y aprobar activación por módulo/versiones antes de despliegue; Inventory no tiene fallback previo. No se solicita retirar archivos ni tocar volúmenes.
6. La API no tiene idempotency key, total Inventory, clinic lookup Inventory ni GET configuration: se mantienen los límites; resultado incierto requiere verificación manual, sin promesa de conciliación inequívoca para alta sin ID.

## Revisión validate-delivery

Skill consultada explícitamente: `.agents/skills/validate-delivery/SKILL.md`; revisión de sólo lectura del código/configuración. Este registro se guarda únicamente por la autorización separada de actualizar los SDD con evidencias. No se presenta descubrimiento automático ni autorización de commit/despliegue.

| Criterio | Estado | Método y evidencia |
| --- | --- | --- |
| AC-01 | PASS | CONTEXT/AGENTS/tres Memory Bank obligatorios e índices/conventions/Rules leídos en sesión y contrastados otra vez al cierre. |
| AC-02 | PASS | UI operativa/inventario sintético; no EHR/IA/PHI/claims de piloto o cumplimiento, CONTEXT y spec §15. |
| AC-03 | PASS | Nuevo runtime en uis/backoffice, web frontend/backend existentes intactos; Compose opt-in raíz sin segundo árbol API. |
| AC-04 | PASS | Rules01/02/05/06/07/08/09 aplicables: arquitectura, fuentes de negocio, auditoría API, docs bilingües, no secretos, sin commits. |
| AC-05 | PASS | Permiso expreso del desarrollador para deps/JWT/proxy/convivencia/Inventory/SDDs; no cambios CONTEXT/Rules/.env/CI/API/migraciones existentes. |
| AC-06 | PASS | 79 archivos revisados/inventariados antes del propio inventario; patrones claves/tokens cloud0, sólo fixtures sintéticos. E-08. |
| AC-07 | BLOCKED | E-01–09 ejecutados con resultados descritos PASS; falta validación manual/performance/opt-in completa exigida por Q del SDD. No se declara ejecutada. |
| AC-08 | BLOCKED | Matriz de39 EARS y34 tareas conserva criterios IN_PROGRESS/BLOCKED; D-07/D-08 y cierre por módulo pendientes. |
| AC-09 | PASS | Inventario exhaustivo changed-files.json: sólo runtime/tests/docs backoffice, override y migrationBackoffice autorizados; tracked/staged diff vacíos. |
| AC-10 | PASS | Cada resultado trazado a comando, código/tests, autorización o limitación explícita. Casos iniciales fallidos descritos y reruns finales sin skips. |

**Resultado de la skill: BLOCKED.** Según su instrucción: «BLOCKED is not PASS. Never claim readiness on a blocked or failed result.» Es un bloqueo del cierre integral por evidencia/revisión faltante; no se ha encontrado una modificación no autorizada ni se presenta la migración completa como terminada.

## Estado de cierre

**BLOCKED para cierre integral del SDD y activación.** El código sintético está implementado y las validaciones ejecutadas pasan, pero las evidencias/revisiones restantes de la matriz son obligatorias antes de declarar completa la migración. No hay autorización de datos reales, piloto, producción ni retirada. Todos los servidores/contendedores de QA iniciados por esta tarea fueron detenidos; PostgreSQL temporal se cerró sin eliminar archivos/volúmenes legacy.
