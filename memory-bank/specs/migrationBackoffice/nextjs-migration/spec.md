# SDD — Modernización progresiva del backoffice HealthCore

**Fecha:** 2026-11-02 · **Estado actual:** implementación sintética disponible; cierre integral y activación pendientes.
**Checkout de discovery:** `feature/inventory-manager`, commit `38332cc`. **Implementación actual:** `migration/backofficeMigration`; sin commit.
**Autorización inicial:** investigación y estos tres documentos. **Ampliación posterior expresa:** «Autorizo ese alcance para desarrollo sintético»: Next/React/TypeScript y pruebas, JWT sólo en memoria con permisos existentes, proxy/convivencia local, NEW UI Inventory según contratos actuales y evidencias de estos SDD. Excluye commits, despliegues, eliminación del legado, cambios de API/BBDD y datos reales.

## 1. Resumen ejecutivo

HealthCore opera 12 clínicas, 9 US y 3 UK. El backoffice es un prototipo sintético pre-MVP, sin autorización real para piloto ni producción. La modernización pretende conservar comportamiento, contratos, permisos e identidad visual; no implementar las necesidades EHR, facturación o IA del briefing.

Se recomienda evolucionar `uis/backoffice/` con Next.js App Router, React y TypeScript estricto, conservando `operational-incidents/` y `management/` durante la transición. No duplicar la web pública ni trasladar `frontend/`. Management de lectura es el piloto recomendado. Inventory será NEW UI sobre API existente y necesita aprobación explícita de su alcance frontend.

## 2. Situación actual y evidencia

| Fuente | Hallazgo EXISTING |
|---|---|
| `uis/backoffice/operational-incidents/{index.html,app.js,styles.css,select-field.js}` | HTML/CSS/JS nativo, router hash, cola, alta, detalle, edición, transiciones, reasignación, cronología y resumen. |
| `uis/backoffice/management/index.html` | JavaScript inline; consulta de catálogos, cuatro maestros y auditoría; sólo lectura, sin paginador UI. |
| `frontend/app/internal/incident-history/` | Vista React interna ya implementada; consulta manual UUID, cronología y detalle de evento diferidos. |
| `frontend/app/api/incident-history/route.js` | POST interno que reenvía dos GET autorizados, timeout 5 s, private/no-store; no sesión propia. |
| `frontend/{package.json,pnpm-lock.yaml,Dockerfile,next.config.mjs}` | Next 16.4.3, React/DOM 19.3.1, pnpm 10.18.3, Node 24 Alpine, standalone, CSS Modules; JS, sin scripts lint/test. |
| `backend/app/{main.py,auth/,incidents/,management/,inventory/}` | API central FastAPI real, Bearer JWT propio, políticas contextuales, inventario implementado. |
| `backend/alembic/versions/{0010_inventory.py,0011_inventory_audit_policy.py}` | Persistencia y auditoría de inventario; ninguna migración propuesta por esta entrega. |
| `docker-compose.yml` | PostgreSQL 16, API, db-init, web Next, backoffice Nginx 1.27, perfil test. |
| `packages/shared/types/{index.ts,management.ts}` | Tipos compartidos existentes; cobertura de inventario no verificada como completa. |
| `backend/tests/`, `scripts/test_caching_frontend.mjs`, `audit/`, `docs/CACHING_REPORT.md` | Pruebas backend y evidencia previa de rendimiento; no suite integral de paridad Next. |

### Discrepancias sin corrección de fuentes

- AGENTS y reglas prevalecen para autorización; CONTEXT para negocio; código para estado técnico. La jerarquía del prompt no permite ignorar estas restricciones.
- `services/central-api/` y `backoffice/` no existen; API central real en `backend/`. El traslado consta en documentación del backend/Inventory y en el SDD vigente de inventario. No mover ni crear otro servicio.
- `memory-bank/technology-stack.md` y README raíz describen plantilla sin apps: desactualizados frente al árbol. `current-state.md` contiene historia y actualización Inventory; no extrapolar sus antiguas rutas.
- README de Inventory conserva un aviso de SDD antiguo; `memory-bank/specs/inventory-manager/spec.md` ya documenta D-01–D-08 y el estado implementado. Código y especificación vigente se contrastan, sin reparar ese aviso aquí.
- La especificación histórica de incidentes propone transiciones y permisos que difieren de `app.js`, `router.py`, `history.py` y `roles.py`; conservar comportamiento real caracterizado. No inventar endpoint de transiciones permitidas.
- La UI exige motivo al cancelar; `proposals.md` advierte que API admite cancelación sin motivo. PATCH ignora extras. Son BACKEND GAP de alineación, no autorización para arreglar contratos.
- `memory-bank/**` estaba protegido/fuera de alcance genérico; la petición actual autoriza únicamente los entregables en `migrationBackoffice`. No actualizar current-state, proposals, Rules ni otros SDD.

## 3. Objetivos y alcance

MIGRATION: todas las funcionalidades UI verificadas en la matriz siguiente. NEW UI: Inventory usando D-01–D-08, sujeto a D-04. ENHANCEMENT: usuarios/roles CRUD, SSO, login con contraseña, refresh, exportaciones, compras, caducidades, traslados, datos EHR y dashboards empresariales no existentes quedan OUT OF SCOPE. No convertir API administrativa de escritura o ComplianceReview en pantallas nuevas por inferencia.

La vista interna React existente se reutiliza como referencia técnica; su traslado/unificación se propone, no se declara migración pendiente de JavaScript nativo. No se cuenta un módulo como migrado por existir un archivo o una ruta.

## 4. Inventario funcional

Las rutas objetivo son PROPOSED bajo `/next`; prioridad es orden de migración, no urgencia clínica. En Pruebas se distingue evidencia existente de cobertura UI pendiente. Todos los módulos están pendientes de esta modernización.

| ID | Módulo / clase | Ruta actual y tecnología | API | Roles / ámbitos | Dependencias | Complejidad / riesgo | Prioridad | Ruta objetivo | Pruebas disponibles | Estado |
|---|---|---|---|---|---|---|---|---|---|---|
| F-01 | Conexión y desconexión MIGRATION | `/` y `/management/`, nativo; JWT manual | catálogos/maestros para conexión; Management consulta directa | rol/área; token sólo memoria, Management en input DOM | API, políticas | media/alto | 1 | `/next/connect` | test_auth, test_http_authorization; UX pendiente | Pendiente |
| F-02 | Management catálogos MIGRATION | `/management/#catalog-section`, inline JS | GET /management/catalogs | catalog:read; admin/technology/compliance/responsibleArea | F-01 | baja/medio (XSS) | 2 piloto | `/next/management/catalogs` | test_management_openapi; UI pendiente | Pendiente |
| F-03 | Management maestros MIGRATION | `/management/#reference-section` | GET /management/reference-data/{resource} | referenceData:read; mismos cuatro roles | F-01, cuatro recursos | baja/medio | 3 | `/next/management/reference-data` | test_catalogs, test_http_authorization | Pendiente |
| F-04 | Management auditoría MIGRATION | `/management/#audit-section` | GET /management/audit-events | audit:read: admin/compliance | F-01, resource_type | media/alto | 4 | `/next/management/audit` | test_audit_serialization; UI pendiente | Pendiente |
| F-05 | Resumen MIGRATION | `/#/summary`, nativo | GET /incidents/metrics/open-by-severity | cinco roles incidentes; área propia; direction agregado | F-01 | baja/medio | 5 | `/next/summary` | AUDIT.md, test_incident_workflows | Pendiente |
| F-06 | Cola MIGRATION | `/#/incidents`, nativo | GET /incidents | incident:list, direction sólo resumen, responsibleArea propia | F-01, catálogos/maestros excepto direction | media/alto | 6 | `/next/incidents` | test_response_contracts, test_http_authorization | Pendiente |
| F-07 | Alta MIGRATION | `/#/incidents/new` | POST /incidents | admin/technology/responsibleArea propia | F-06, catálogos activos, clínica-jurisdicción | alta/alto | 8 | `/next/incidents/new` | test_incident_workflows, test_input_schema_policy | Pendiente |
| F-08 | Detalle y edición MIGRATION | `/#/incidents/{uuid}` | GET/PATCH /incidents/{id} | lectura admin/technology/compliance/área propia; título/descripcion admin/technology/área propia | F-06, referencias | alta/alto | 7 | `/next/incidents/[id]` | test_http_authorization; UI pendiente | Pendiente |
| F-09 | Estado y reasignación MIGRATION | mismo detalle | POST transitions/assignments | estado admin/technology; área propia closed/cancelled; asignar sólo admin | F-08, grafo real, motivo | alta/crítico | 9 | detalle, secciones acciones | test_incident_workflows | Pendiente |
| F-10 | Cronología MIGRATION | mismo detalle | GET history/assignment-history | incident:read; área propia, direction denegado | F-08; carga parcial recuperable | media/alto | 7 | detalle, cronología | test_audit_serialization, test_incident_workflows | Pendiente |
| F-11 | Historial React EXISTING | `/internal/incident-history` en frontend | POST /api/incident-history → dos GET | autorización independiente de ambas lecturas; token memoria | frontend, lazy, useMemo | media/medio | 10 | conservar; unificación opcional `/next/incidents/[id]/history` | scripts/test_caching_frontend.mjs, CACHING_REPORT | Pendiente de decisión, ya React |
| F-12 | Navegación/estados/telemetría MIGRATION | header, anclas/hash; módulo compartido nativo | POST /telemetry/context,/events si habilitado | contexto autorizado, opt-in | runtime.js, configuración pública | media/alto | transversal | AppShell y adaptador | telemetry/tests, test_telemetry_* | Pendiente |
| F-13 | Inventory catálogo y lotes NEW UI | sin UI; API Python | /inventory/items y lots | inventoryAdmin escribe; cinco roles leen catálogo | D-04, tipos/API | media/alto | 11 | `/next/inventory/items` | test_inventory, test_inventory_audit_policy | Bloqueado por D-04 |
| F-14 | Inventory stock/reorden/historial NEW UI | sin UI | /inventory/stock,/reorder, item stock/movements | operator/manager por clínica; regional/auditor por país | D-04, scopes firmados | alta/alto | 12 | `/next/inventory/stock`, `/reorder`, `/items/[id]` | test_inventory*, aislamiento US/UK | Bloqueado por D-04 |
| F-15 | Inventory configuración/movimientos/conteos/compensación NEW UI | sin UI | configuration, movements, correction | operator in/out; manager además configuración/adjust/correction | F-14, D-04, conciliación | alta/crítico | 13 | `/next/inventory/movements/new`, acciones detalle | test_inventory, test_inventory_demo | Bloqueado por D-04 |
| F-16 | Inventory auditoría y denegaciones NEW UI | sin UI | item audit,/access-denials | inventoryAuditor dentro país, denegaciones desconocidas propias | F-14, D-04, revisión Claire | alta/alto | 14 | `/next/inventory/audit` | test_inventory_audit_policy | Bloqueado por D-04 |

No hay UI de usuarios ni sesión compartida, footer/dashboard empresarial adicional, editor de stock ni reposición automática. La home pública no forma parte de la migración.

## 5. Arquitectura objetivo

Una aplicación Next dentro del límite `uis/backoffice`, sin segundo árbol público. App Router organiza módulos; layouts Server Components muestran estructura no sensible; Client Components gestionan conexión efímera, tablas interactivas y mutaciones. Capa API tipada delimita contratos FastAPI, errores y cancelación; backend conserva autoridad. Sin acceso Next directo a BBDD.

Coexistencia propuesta: Nginx conserva `/` (hash incidents) y `/management/`; enruta `/next/*` al runtime Next con `basePath=/next`. API accesible mediante un prefijo de proxy `/api-core/*` aprobado que elimina dicho prefijo y pasa Authorization; no confundir con `/api/incident-history`. Esto evita ampliar CORS, pero requiere aprobación de infraestructura y pruebas de reescritura/assets. No implementado. Sin proxy aprobado, no activar módulos Next que dependan de esa conectividad.

## 6. Requisitos EARS y trazabilidad

Las filas conservan el diseño original; el estado ejecutado se evalúa individualmente en [execution.md](./execution.md). No interpretar PROPOSED como ausencia del código nuevo ni como aceptación global. P0 = gate de seguridad/paridad; P1 = funcional; P2 = optimización condicionada. Aprobación `PROPOSED` para todos; D-04 condiciona Inventory. Fuentes: C=CONTEXT/AGENTS; I=app.js y routers/schemas incidentes; M=Management UI/router; V=Inventory spec D-01–D-08 + código; H=historial React; T=prompt; O=Compose/telemetría/auditorías. Pruebas Q referidas en plan.md. Dependencias D referidas en §13.

| ID | Descripción EARS | Prioridad | Fuente | Módulo | Criterio de aceptación | Pruebas | Dependencias | Aprobación |
|---|---|---|---|---|---|---|---|---|
| REQ-ARCH-001 | THE system SHALL organizar Next.js App Router con TypeScript estricto en el límite uis/backoffice y separar features, UI, API y auth. | P0 | T/C | todos | Build y typecheck sin errores; sin duplicar frontend ni backend. | Q-01 | D-01,D-02 | PROPOSED |
| REQ-ARCH-002 | THE system SHALL mantener las políticas y persistencia de negocio exclusivamente en la API central existente. | P0 | C/I/V | todos | No SQL ni secretos JWT en Next; operaciones sólo por contratos. | Q-01,Q-03 | D-03 | PROPOSED |
| REQ-MIG-001 | WHEN una funcionalidad existente sea migrada, THE system SHALL conservar comportamiento, validaciones, permisos y contratos API caracterizados. | P0 | T/I/M | F-01–F-12 | Cada escenario de paridad tiene evidencia PASS; excepciones aprobadas por separado. | Q-02–Q-07 | D-01 | PROPOSED |
| REQ-MIG-002 | WHILE existan módulos sin migrar, THE system SHALL mantener accesibles las rutas antiguas y las nuevas mediante el mapa aprobado. | P0 | T/O | todos | Cada enlace legado/nuevo responde y atrás/adelante conserva filtros no sensibles. | Q-07 | D-03 | PROPOSED |
| REQ-MIG-003 | WHEN se solicite retirar un módulo antiguo, THE system SHALL exigir paridad, permisos, pruebas, rollback y aprobación expresa de retirada y despliegue. | P0 | C/T | todos | Checklist por F sin FAIL ni ausencia de evidencia; ningún borrado antes de aprobación. | Q-10 | D-05 | PROPOSED |
| REQ-MIG-004 | WHERE se apruebe Inventory NEW UI, THE system SHALL diferenciar su aceptación contra contratos de la paridad de pantallas preexistentes. | P0 | V/T | F-13–F-16 | No inventar before UI; evidencia por INV-AC-001–020. | Q-08 | D-04 | PROPOSED |
| REQ-UI-001 | THE system SHALL conservar tokens y patrones HealthCore identificados en las hojas de estilo existentes. | P1 | T/I/M | todos | Comparación de marca, botones, forms, tablas, estados y responsive aprobada. | Q-05 | D-01 | PROPOSED |
| REQ-UI-002 | WHEN una lectura esté pendiente, vacía o falle, THE system SHALL mostrar un estado accesible diferenciado y una recuperación explícita cuando proceda. | P1 | I/M/H | todos | Loading/empty/401/403/404/422/503 diferenciados; no éxito falso. | Q-02,Q-05 | D-03 | PROPOSED |
| REQ-UI-003 | WHEN se filtre o pagine la cola, THE system SHALL conservar filtros y orden en la URL sin incluir credenciales ni texto sensible. | P1 | I | F-06 | Página 20, orden/filtros actuales, offset reinicia al cambiar filtros. | Q-04,Q-07 | D-03 | PROPOSED |
| REQ-AUTH-001 | WHEN un usuario conecte un JWT de desarrollo, THE system SHALL usarlo sólo en memoria y delegar su validación definitiva al backend. | P0 | I/H/C | F-01 | Firma inválida/expirada produce 401; sin localStorage/sessionStorage/URL/cookie token. | Q-03 | D-01 | PROPOSED |
| REQ-AUTH-002 | WHEN el usuario desconecte o reciba 401, THE system SHALL limpiar credenciales, datos remotos y contexto de telemetría y cancelar lecturas pendientes. | P0 | H/T | todos | Respuesta tardía no repuebla datos; recarga requiere reconexión. | Q-03,Q-06 | D-01 | PROPOSED |
| REQ-AUTH-003 | WHILE la autenticación siga siendo JWT efímero, THE system SHALL informar que cambiar a la aplicación legacy puede requerir reconexión. | P1 | I/M/H | F-01,F-12 | No transferencia automática de tokens ni promesa de refresh/SSO. | Q-07 | D-01 | PROPOSED |
| REQ-RBAC-001 | IF el backend deniega una operación, THEN THE system SHALL presentar acceso denegado sin asumir éxito ni conceder permisos por claims decodificados. | P0 | I/V/C | todos | 401/403 reales incluso URL/acción directa con controles manipulados. | Q-03 | D-01 | PROPOSED |
| REQ-RBAC-002 | WHEN responsibleArea consulte o edite incidencias, THE system SHALL respetar área propia y limitar su editor a título y descripción. | P0 | I | F-06–F-10 | Área ajena denegada; no severidad/asignación/review por ese editor. | Q-03,Q-04 | D-01 | PROPOSED |
| REQ-RBAC-003 | WHEN direction acceda a incidencias, THE system SHALL ofrecer resúmenes y métricas sin detalle, descripción ni mutaciones. | P0 | I | F-05,F-06 | No prefetch de detalles ni catálogos no autorizados. | Q-03 | D-01 | PROPOSED |
| REQ-RBAC-004 | WHERE Inventory NEW UI esté habilitada, THE system SHALL respetar los cinco roles independientes y sus scopes de clínica o país. | P0 | V | F-13–F-16 | admin antiguo no obtiene inventario; inventoryAdmin sin stock; US/UK y ámbito ajeno cubiertos. | Q-08 | D-04 | PROPOSED |
| REQ-API-001 | WHEN un módulo invoque la API, THE system SHALL usar método, parámetros y schemas vigentes sin alterar su semántica. | P0 | I/M/V | todos | Matriz API §plan y contratos verificables sin endpoints ficticios. | Q-01,Q-04 | D-02 | PROPOSED |
| REQ-API-002 | THE system SHALL derivar tipos transportados de OpenAPI vigente y mantener separado el mapeo snake_case a modelos camelCase de presentación. | P1 | T/C | todos | Generación reproducible sin drift, null/optional/list/envelope correctamente tipados. | Q-01 | D-02 | PROPOSED |
| REQ-API-003 | WHEN se liste Inventory, THE system SHALL paginar arrays por offset/limit sin inventar total ni considerar agotada una página corta de reorden. | P1 | V | F-13,F-14,F-16 | Siguiente explícito y página vacía recuperable; recheck puede acortar página. | Q-08 | D-04 | PROPOSED |
| REQ-API-004 | WHEN se carguen formularios de incidencias, THE system SHALL obtener etiquetas de catálogos y referencias activas manteniendo validación contextual en backend. | P1 | I | F-07–F-09 | Clínicas por jurisdicción, área propia, límites 200/10000 y reporter omitido. | Q-04 | D-01 | PROPOSED |
| REQ-DATA-001 | IF una escritura tenga resultado incierto, THEN THE system SHALL impedir reenvío automático y ofrecer consulta de verificación antes de nueva operación. | P0 | T/V | escrituras | POST perdido no se duplica; creación sin ID no se concilia de forma inequívoca. | Q-06,Q-08 | D-06 | PROPOSED |
| REQ-DATA-002 | WHEN cambie identidad, ámbito o recurso, THE system SHALL cancelar solicitudes previas y aislar o descartar datos del contexto anterior. | P0 | H/V | todos | Abort + epoch; ningún dato de usuario/país anterior tras reconnect. | Q-03,Q-06 | D-01 | PROPOSED |
| REQ-DATA-003 | WHEN una mutación sea confirmada, THE system SHALL releer los recursos afectados antes de mostrar el estado autoritativo actualizado. | P1 | I/V | F-07–F-09,F-15 | Detalle/cola/métricas o stock/reorden/historia refrescados; sin optimistic update crítico. | Q-04,Q-08 | D-06 | PROPOSED |
| REQ-DATA-004 | WHERE Inventory NEW UI esté aprobada, THE system SHALL mostrar stock calculado por API y conservar reglas de unidades, lotes, conteos, compensación y reorden D-01–D-08. | P0 | V | F-13–F-16 | In/out enteros, pack snapshot, adjust base con motivo, compensación única, sin stock editable/negativo, igualdad no alerta. | Q-08 | D-04 | PROPOSED |
| REQ-SEC-001 | THE system SHALL excluir tokens, secretos, PHI y cuerpos libres de logs, telemetría, URLs y artefactos de prueba. | P0 | C/O | todos | Inspección de storage/log/network con fixtures sintéticos, sin valores sensibles. | Q-03,Q-09 | D-01 | PROPOSED |
| REQ-SEC-002 | WHEN se rendericen valores recibidos de API, THE system SHALL tratarlos como texto escapado y evitar interpolación HTML no sanitizada. | P0 | M/I | todos | Payload sintético HTML se muestra como texto sin ejecutar handlers/scripts. | Q-03,Q-05 | D-01 | PROPOSED |
| REQ-SEC-003 | WHEN se sirvan respuestas autenticadas, THE system SHALL impedir caché compartida, render estático y prefetch sensible sin autorización. | P0 | H/T | todos | private/no-store en proxy/handlers; dos identidades nunca comparten respuesta. | Q-03,Q-09 | D-03 | PROPOSED |
| REQ-SEC-004 | WHERE telemetría esté habilitada, THE system SHALL conservar opt-in, contexto validado y separación regional sin enviar claves de servidor al navegador. | P0 | O/C | F-12 | Deshabilitada por defecto; fallo no bloquea negocio; eventos nuevos requieren Claire. | Q-09 | D-07 | PROPOSED |
| REQ-ACC-001 | THE system SHALL permitir todas las acciones esenciales por teclado con foco visible, etiquetas y orden semántico. | P0 | T/I/M | todos | Tab/ShiftTab/Enter/Escape y skip link manuales sin trampas. | Q-05 | D-01 | PROPOSED |
| REQ-ACC-002 | WHEN un formulario sea inválido o un diálogo se abra, THE system SHALL asociar errores a campos y gestionar foco, cierre y retorno accesibles. | P1 | T | formularios | aria-describedby, resumen de error; dialog devuelve foco; status anunciado. | Q-05 | D-01 | PROPOSED |
| REQ-ACC-003 | THE system SHALL adoptar WCAG 2.2 AA como objetivo y verificar contraste, tablas, estados no sólo por color y responsive. | P0 | T | todos | Revisión automática y manual documentada; texto normal ≥4.5:1, grande ≥3:1; 320px y zoom 200%. | Q-05 | D-01 | PROPOSED |
| REQ-PERF-001 | WHEN se evalúe un módulo, THE system SHALL registrar baseline y comparación en producción con mismo dataset, navegador, caché y red. | P1 | O/T | todos | Tres navegaciones por perfil, p50/p95 lecturas y bytes JS gzip documentados. | Q-09 | D-08 | PROPOSED |
| REQ-PERF-002 | WHERE un presupuesto de rendimiento esté aprobado, THE system SHALL cumplirlo antes de sustituir la ruta antigua. | P0 | T/O | todos | Objetivo por módulo D-08; cualquier regresión excedente bloquea retirada. | Q-09 | D-08 | PROPOSED |
| REQ-PERF-003 | WHEN se optimice una vista, THE system SHALL justificar límites cliente, carga diferida y memoización con mediciones del trabajo real. | P2 | H/O | F-10,F-11,tablas | Comparación Profiler/chunks; no memo indiscriminado ni virtualización sin evidencia. | Q-09 | D-08 | PROPOSED |
| REQ-TEST-001 | WHEN se complete un módulo, THE system SHALL disponer de caracterización, contratos, roles, errores, E2E y paridad antes de activarlo. | P0 | T | todos | Matriz escenario legacy/Next/resultado íntegra, datos sintéticos aislados. | Q-02–Q-10 | D-02 | PROPOSED |
| REQ-TEST-002 | THE system SHALL conservar las pruebas backend existentes como evidencia de contratos sin presentarlas como pruebas UI de migración. | P1 | O/T | todos | Resultados históricos separados de ejecuciones actuales y tests frontend nuevos. | Q-01,Q-08 | D-02 | PROPOSED |
| REQ-OPS-001 | IF un módulo activo presenta fallo bloqueante, THEN THE system SHALL disponer de restauración de su ruta previa con versión y mapa de proxy conocidos. | P0 | T/O | todos | Ensayo aislado de rollback sin down -v ni rollback de BBDD. | Q-10 | D-03,D-05 | PROPOSED |
| REQ-OPS-002 | WHEN se solicite activar una ruta, THE system SHALL exigir aprobaciones de infraestructura, despliegue y revisiones de seguridad aplicables. | P0 | C/T | todos | Build/health/assets/autorización/paridad PASS y aprobación registrada por módulo. | Q-10 | D-05,D-07 | PROPOSED |
| REQ-OPS-003 | WHILE no exista autenticación y entorno real aprobados, THE system SHALL limitar cualquier validación a desarrollo sintético aislado. | P0 | C | todos | Sin datos reales, piloto empresarial, producción ni transferencias sanitarias. | Q-03,Q-10 | D-01,D-07 | PROPOSED |

## 7. Seguridad y autorización

JWT HS256 validado sólo por API; `sub`, `role`, `area_id`, `clinic_ids`, `jurisdiction_ids`, `iat`, `exp`; expiración configurada por defecto 60 min. `/auth/tokens` sólo development/test, sin autenticación humana real; staging/production devuelve 404. No endpoints de logout, refresh o usuario actual. Desconexión significa borrar memoria, no revocar un token ya emitido.

Protección de navegación = UX por claims no verificados; permisos de acción = presentación conservadora; autorización definitiva = dependencias/políticas backend sobre cada petición. Layout servidor no puede validar una sesión que sólo vive en memoria cliente. No vender ese guard como control de seguridad.

CORS local admite sólo localhost/127.0.0.1:8080, métodos GET/POST/PATCH y cabeceras Authorization/Content-Type/X-Telemetry-Context. Puerto Next 3000 no está autorizado para llamadas directas. No cookies de auth verificadas; CSRF por credenciales ambientales no es el flujo vigente. Un futuro BFF con cookie HttpOnly obligaría a decidir Secure/SameSite/domain/path/expiry, comprobación Origin y defensa CSRF para escrituras. Queda fuera de esta fase y no se considera compatible por defecto.

Management interpola datos API mediante innerHTML: riesgo XSS real de construcción, sin afirmar explotación. En React usar nodos escapados y pruebas de payload sintético. Token en memoria sigue expuesto ante XSS del mismo contexto. Respuestas autenticadas private/no-store; no ISR ni caché global por URL. Proxy con destino fijo y allowlist, sin URLs arbitrarias que abran SSRF. Revisar CSP, frame-ancestors, nosniff, Referrer-Policy y TLS/HSTS en entorno aprobado; no constan como configuración productiva validada.

Auditoría de dominio sigue backend y append-only; UI no reconstruye campos redactados ni retiene datos al logout. La revisión simulada Inventory sólo avala su alcance ficticio anterior. Nuevos eventos de telemetría, exposición de auditoría, retención o tratamiento necesitan revisión de Claire Whitfield; no se declara cumplimiento HIPAA/UK GDPR.

## 8. Rendimiento

Baseline histórico `AUDIT.md` (29/10/2026): resumen escritorio LCP mediana 323.18 ms, CLS 0.03419, TBT 0; home pública móvil LCP 1952.88 ms no equivale a baseline del backoffice nuevo. `docs/CACHING_REPORT.md` respalda lazy/useMemo del historial con 2000 eventos sintéticos; no representa tamaño habitual. No se repitieron benchmarks ni pruebas backend para escribir este SDD.

D-08 exige baseline de Management, cola/detalle/forms y futuras vistas Inventory: build producción, tres navegaciones cold/warm por 393/1350px, dispositivo/red fijados, tiempos hasta datos y navegación, bytes transferidos/comprimidos por ruta, p50/p95 API, React Profiler con 20/200/2000 eventos sintéticos y tablas a 20/50/100 filas. Medir validación de formularios y solicitudes por mutación. SLO y presupuesto JS quedan por aprobar después de baseline; no prometer cifras universales ni comparar Next completo contra fuente JS sin comprimir.

Usar Server Components en shell; islas cliente donde estado requiere interacción. Mantener lazy de timeline/event-details; code splitting por módulos. React.memo/useCallback sólo si Profiler acredita rerenders costosos; useMemo para merge/sort real con dependencias correctas. No virtualizar tablas acotadas por API sin coste demostrado. Cache de catálogos backend existente no justifica caché compartida frontend; inicialmente lecturas privadas sin caché Next.

## 9. Accesibilidad y componentes

Objetivo WCAG 2.2 AA, verificación manual más automática; Lighthouse 100 no certifica cumplimiento. Matriz UI en plan.md cubre controles, semántica, foco, contraste y responsive. Conservar enlaces/anclas necesarios, botones con estados deshabilitados y avisos PHI sin presentarlos como detector.

## 10. Convivencia y equivalencia

Un propietario de ruta y una sola ejecución de escritura por acción. En transición los bookmarks hash quedan servidos por Nginx; el fragmento no llega al proxy, por lo que no se puede enrutar `#/incidents` en servidor. Sustitución por módulo mediante enlaces aprobados; redirección hash requeriría adaptador cliente posterior autorizado.

No transportar token por URL, storage compartido o postMessage sin diseño aprobado. Mantener filtros/IDs no sensibles cuando posible; formularios no enviados permanecen en página y se advierte antes de abandonarlos. Volver al legado puede perder sesión: reconexión explícita aceptada por D-01. Las escrituras confirmadas quedan en la misma API/BBDD y el rollback es de ruta/UI.

## 11. Criterios de aceptación del diseño

| ID | Criterio documental | Evidencia |
|---|---|---|
| SDD-01 | Inspeccionar árbol real, módulos y funciones sin asumir ubicaciones. | §2, §4; API y fuentes en plan. |
| SDD-02 | Requisitos EARS completos y verificables, categorías e IDs únicos. | §6; pruebas Q y tareas trazadas. |
| SDD-03 | Arquitectura modular, componentes, estado, seguridad y convivencia. | §5–10 y plan §3–9. |
| SDD-04 | Preservar contratos, permisos, reglas Inventory y distinguir NEW UI. | §4, §6, matriz API y contratos en plan. |
| SDD-05 | Fases, tareas acotadas con dependencias, pruebas y gates. | tasks.md; todo TODO/BLOCKED sin ejecución ficticia. |
| SDD-06 | Riesgos/decisiones explícitos y no implementación. | §13–15; Git sólo tres documentos nuevos. |

Aprobación del SDD no constituye por sí sola autorización de cambios protegidos, dependencias, infraestructura, despliegue o eliminación. Revisión del diseño puede PASS con decisiones futuras pendientes; implementación sigue condicionada.

## 12. Riesgos

| ID | Riesgo | Mitigación / bloqueo |
|---|---|---|
| R-01 | JWT temporal y claims no verificables en cliente; sesiones distintas. | D-01, API autoridad, memoria, reconexión; no producción. |
| R-02 | Regresión por roles/scopes mezclados e historial regional. | Matriz completa cinco roles Inventory, cinco incidentes, área/país ajeno; no herencia implícita. |
| R-03 | Proxy de hash imposible, assets Next o prefijos erróneos. | `/next` y basePath; tests de assets/deep links, mapa versionado D-03. |
| R-04 | Doble escritura por timeout/retry y falta de idempotencia. | Sin retry automático, estado incierto y verificación; D-06. |
| R-05 | XSS Management y texto libre/auditoría en logs. | React escapa, fixture malicioso sintético, logging allowlist, Claire. |
| R-06 | Documentación desfasada y OpenAPI snapshots sin Inventory. | Fuente código, snapshot vigente posterior, no cambios silenciosos. |
| R-07 | NEW UI Inventory amplía entrega previa sin aprobación. | D-04 bloquea sus tareas; reglas D-01–D-08 no cambian. |
| R-08 | Next añade JS sin baseline representativo. | D-08, budgets por módulo y comparación equivalente, sin optimización indiscriminada. |
| R-09 | Concurrencia y ausencia de total/lookup de configuración Inventory. | Lecturas explícitas, no snapshot global, gaps documentados sin inventar API. |
| R-10 | Retirada o promoción pre-MVP sin gates externos. | D-05/D-07; no autorización real ni eliminación en esta entrega. |

## 13. Decisiones y dependencias por aprobar

| ID | Clasificación | Decisión / recomendación | Responsable y efecto |
|---|---|---|---|
| D-01 | PROPOSED | JWT manual en memoria para desarrollo sintético; reconexión legacy aceptada; SSO fuera. | James Osei/desarrollador; gate auth/layout. |
| D-02 | PROPOSED | Conservar versiones verificadas de Next/React/pnpm/Node como base, aprobar TypeScript/tipos/generación y tooling de pruebas. | Desarrollador; resolver versiones y compatibilidad antes de instalar. |
| D-03 | PROPOSED | Next en uis/backoffice, basePath /next, Nginx por rutas y proxy /api-core fijo. | Tecnología; permisos expresos para infra/conexión. |
| D-04 | BLOCKED | Autorizar NEW UI Inventory por F-13–F-16 y límites de selección de clínicas/conciliación; no heredar roles. | Desarrollador + responsables; tareas Inventory bloqueadas. |
| D-05 | PROPOSED | Aprobación por módulo para activación, runtime/CI y retirada; conservar rollback. | Tecnología/desarrollador; ningún despliegue/borrado ahora. |
| D-06 | PROPOSED | Sin optimistic/retry escritura; resultado incierto con consulta manual; falta idempotency key. | Tecnología/áreas; aprobar recuperación antes de mutaciones. |
| D-07 | BLOCKED | Revisar exposición de auditoría/telemetría y garantías de entorno con Claire; no ampliar retención/tratamiento. | Cumplimiento y Gobierno del Dato; bloquea habilitación afectada/real. |
| D-08 | PROPOSED | Medir baseline primero y aprobar presupuestos de carga/JS/API/forms por módulo. | Tecnología/QA; gate rendimiento de retirada. |
| D-09 | PROPOSED | Conservar F-11 en frontend durante transición; decidir traslado opcional posterior. | Desarrollador; no mezclar ni mover home pública. |

APPROVED existente: reglas Inventory D-01–D-08 y revisión simulada HC-INV-APPROVAL-2026-11-02, sólo alcance documentado en su SDD. EXISTING: JWT, APIs y pantallas verificadas. BACKEND GAP: sin refresh/me, transiciones permitidas API, idempotencia, total Inventory, GET configuración o listado de clínicas con roles Inventory. OUT OF SCOPE: cubrir gaps mediante nuevos endpoints en esta migración; resolución requiere entrega separada.

## 14. Matriz de trazabilidad

La tabla EARS relaciona fuente → módulo → aceptación → prueba → decisión. `tasks.md` completa prueba/requisito → unidad ejecutable. Inventory añade INV-AC-001–020 y D-01–D-08 del SDD previo. Ningún requisito se considera satisfecho por esta especificación; su aceptación futura requiere evidencia ejecutada por tarea.


## 15. Registro de implementación sintética

La autorización posterior del desarrollador resuelve D-01/D-02/D-03/D-04/D-06 para desarrollo sintético y preparación local de convivencia. D-05 sólo permite preparar configuración, no activar/desplegar/retirar. D-07 sigue pendiente de Claire Whitfield para revisión de exposición y uso real; la autorización del desarrollador no se presenta como revisión de Cumplimiento. D-08 sigue sin presupuesto aprobado: se midió Management, no todas las vistas. D-09 conserva el historial React existente en `/frontend` sin traslado.

Implementación: `uis/backoffice/src/`, runtime standalone `/next`, OpenAPI vigente generado, cliente seguro, sesión efímera, Management de lectura, incidencias y NEW UI Inventory. El formulario de movimientos vive en el detalle del artículo, no en la ruta prevista `/inventory/movements/new`. DTO transportados permanecen snake_case; las etiquetas y propiedades de presentación se calculan en features sin duplicar modelos camelCase ni crear workspace raíz. Se usa CSS global encapsulado en el runtime interno y tokens locales, sin librería UI ni cambio de estilos legacy.

[execution.md](./execution.md) registra evidencias, criterios y límites; [tasks.md](./tasks.md) refleja DONE/IN_PROGRESS/BLOCKED. El baseline documental anterior permanece para distinguir situación previa de capacidad implementada. Ningún módulo legado se ha retirado y ninguna capacidad se ha autorizado para datos reales.
