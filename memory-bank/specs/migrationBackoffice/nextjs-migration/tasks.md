# Tareas — Migración progresiva HealthCore Backoffice

**Fecha:** 2026-11-02 · **Estado de implementación:** ejecutada en desarrollo sintético; cierre integral pendiente.
[Requisitos y decisiones](./spec.md) · [Arquitectura, contratos y pruebas Q](./plan.md).

El diseño inicial era TODO/BLOCKED. La autorización posterior expresa y su alcance constan en spec §15. DONE sólo acepta el criterio verificado indicado; IN_PROGRESS identifica código entregado con evidencia adicional pendiente; BLOCKED conserva gates de revisión/activación. No crear commits, desplegar ni retirar legado.

Registro de evidencia requerido tras cada ejecución: comando exacto, versiones/entorno/dataset sintético, exit status, artefacto autorizado, comparación esperada/obtenida, diff y permiso aplicable. Estado documental de esta entrega no equivale a estado de tareas.

## Fase 0 — Discovery y baseline

### T-00 — Confirmar decisiones del SDD

| Campo | Detalle |
|---|---|
| Estado | DONE |
| Objetivo | Registrar alcance y aprobaciones sin ejecutar cambios protegidos. |
| Requisitos EARS | REQ-ARCH-001, REQ-MIG-004, REQ-OPS-002 |
| Dependencias | Revisión del desarrollador; D-01–09 |
| Archivos afectados o previstos | Estos SDD; registro de decisiones autorizado |
| Pasos técnicos | Revisar D-01–09; distinguir aprobación diseño y permiso de operación; acordar owners y exclusiones. |
| Pruebas necesarias | Revisión documental |
| Criterio de aceptación | Decisiones aprobadas/rechazadas/pendientes con fuente explícita. |
| Evidencia de ejecución | Autorización sintética expresa; decisiones reales pendientes enumeradas en spec §15. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Aprobación genérica interpretada como despliegue. |

### T-01 — Caracterizar Management de lectura

| Campo | Detalle |
|---|---|
| Estado | IN_PROGRESS |
| Objetivo | Fijar comportamiento actual de F-01–04 antes del piloto. |
| Requisitos EARS | REQ-MIG-001, REQ-TEST-001, REQ-TEST-002, REQ-UI-002 |
| Dependencias | T-00 |
| Archivos afectados o previstos | uis/backoffice/management/index.html (lectura); tests/fixtures y matriz futura autorizada |
| Pasos técnicos | Observar catálogos, cuatro maestros, auditoría type/limit50; capturar fixture sintético redactado; registrar columnas/errores y token DOM. |
| Pruebas necesarias | Q-02,Q-03 |
| Criterio de aceptación | Cada acción/código y rol tiene expected y evidencia actual, sin inventar paginador. |
| Evidencia de ejecución | Implementación presente; falta caracterización completa y matriz por rol, ver execution.md. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | XSS/credenciales en capturas. |

### T-02 — Caracterizar incidentes y matriz de roles

| Campo | Detalle |
|---|---|
| Estado | IN_PROGRESS |
| Objetivo | Fijar cola/resumen/detalle/alta/edición/estado/asignación/historia reales. |
| Requisitos EARS | REQ-MIG-001, REQ-RBAC-002, REQ-RBAC-003, REQ-API-004, REQ-TEST-001 |
| Dependencias | T-00 |
| Archivos afectados o previstos | app.js, backend/app/incidents y auth (lectura); fixtures futuras |
| Pasos técnicos | Inventariar grafo app/history; cinco roles, área propia/ajena; filtros/orden/página20; motivos y errores parciales; registrar discrepancias sin cambiar API. |
| Pruebas necesarias | Q-03,Q-04 |
| Criterio de aceptación | F-05–10 cuentan con escenarios positivos/negativos y baseline de permisos. |
| Evidencia de ejecución | Implementación presente; falta caracterización completa y matriz por rol, ver execution.md. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Desfase SDD histórico/API. |

### T-03 — Congelar contratos vigentes y cobertura tipos

| Campo | Detalle |
|---|---|
| Estado | DONE |
| Objetivo | Contrastar firmas estáticas con OpenAPI actual sin datos reales. |
| Requisitos EARS | REQ-API-001, REQ-API-002, REQ-TEST-002 |
| Dependencias | T-00; tooling lectura API aislada |
| Archivos afectados o previstos | backend/app/*/router.py y schemas.py, packages/shared/types (lectura); snapshot futuro autorizado |
| Pasos técnicos | Generar OpenAPI app aislada sin credenciales reales; comparar snapshots históricos; verificar DTO/responses/errores y cobertura Inventory; diseñar adapters snake/camel. |
| Pruebas necesarias | Q-01 |
| Criterio de aceptación | Endpoints y schemas consumidos completos; gaps identificados, sin modificar contratos. |
| Evidencia de ejecución | Snapshot igual a OpenAPI actual y generación reproducible; E-01/E-02. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Snapshot sin Inventory usado como vigente. |

### T-04 — Capturar baseline visual y rendimiento por módulo

| Campo | Detalle |
|---|---|
| Estado | IN_PROGRESS |
| Objetivo | Medir pantallas reales antes de presupuestos nuevos. |
| Requisitos EARS | REQ-UI-001, REQ-ACC-003, REQ-PERF-001, REQ-PERF-002, REQ-PERF-003 |
| Dependencias | T-01,T-02; D-08 |
| Archivos afectados o previstos | styles.css, frontend CSS, audit y docs/CACHING_REPORT (lectura); artefactos futuros |
| Pasos técnicos | Capturar desktop/mobile/keyboard; medir producción cold/warm tres rondas, JS gzip/API p50-p95/tiempo a datos; acordar budgets con QA; no aplicar memo preventiva. |
| Pruebas necesarias | Q-05,Q-09 |
| Criterio de aceptación | Dataset/entorno/métrica/budget aprobado por módulo, no extrapolar home. |
| Evidencia de ejecución | Sólo baseline Management tres cold/warm y dos anchuras; falta resto de módulos, Profiler y presupuesto D-08. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Baseline no representativo o ausencia de presupuesto. |

## Fase 1 — Arquitectura Next.js

### T-05 — Aprobar arquitectura de autenticación/conexión

| Campo | Detalle |
|---|---|
| Estado | DONE |
| Objetivo | Resolver D-01/03 sin sustituir JWT existente. |
| Requisitos EARS | REQ-AUTH-001, REQ-AUTH-003, REQ-ARCH-002, REQ-SEC-001, REQ-OPS-003 |
| Dependencias | D-01,D-03; autorización expresa protegida |
| Archivos afectados o previstos | Diseño auth, mapa de proxy previsto |
| Pasos técnicos | Acordar memoria/reconexión, backend autoridad, no cookie/refresh; aprobar cambios necesarios de auth/conexión separados del SDD. |
| Pruebas necesarias | Q-03,Q-07 documental |
| Criterio de aceptación | Permisos expresos y modelo coherente antes de implementar. |
| Evidencia de ejecución | Modelo memoria y proxy fijo autorizado expresamente; E-00. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Cambiar controles por inferencia. |

### T-06 — Crear estructura Next estricta dentro del backoffice

| Campo | Detalle |
|---|---|
| Estado | DONE |
| Objetivo | Preparar runtime interno sin tocar aplicaciones existentes. |
| Requisitos EARS | REQ-ARCH-001, REQ-API-002 |
| Dependencias | T-00,T-03,T-05; D-02,D-03 y dependencias aprobadas |
| Archivos afectados o previstos | uis/backoffice/package.json, lock, tsconfig, next.config, src/app/layout.tsx; README bilingües futuros |
| Pasos técnicos | Resolver versiones compatibles Next16.4.3/React19.3.1/Node24/pnpm10.18.3 y TS; configurar strict/basePath; aislar legacy; no crear workspace raíz implícito. |
| Pruebas necesarias | Q-01 |
| Criterio de aceptación | Build/typecheck PASS; rutas legacy y frontend público intactos. |
| Evidencia de ejecución | Build, tipos estrictos y Docker PASS; árboles anteriores sin diff. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Dependencias o Docker copy incompatibles. |

### T-07 — Generar DTO y adaptadores de lectura

| Campo | Detalle |
|---|---|
| Estado | DONE |
| Objetivo | Evitar drift de contrato y campos null/optional incorrectos. |
| Requisitos EARS | REQ-API-001, REQ-API-002 |
| Dependencias | T-03,T-06 |
| Archivos afectados o previstos | packages/shared/types o types generados aprobados; lib/api/types y adapters |
| Pasos técnicos | Integrar generador dev-only aprobado; separar transporte snake_case y vista camelCase; comprobar arrays/envelopes/UUID y redaction. |
| Pruebas necesarias | Q-01 |
| Criterio de aceptación | Drift check detecta cambio real de schema y generación repetible sin diff inesperado. |
| Evidencia de ejecución | types:generate/types:check y comparación OpenAPI PASS; sin workspace nuevo. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Tipos parciales/generación no determinista. |

### T-08 — Implementar cliente API y errores seguros

| Campo | Detalle |
|---|---|
| Estado | DONE |
| Objetivo | Centralizar fetch/AbortSignal/status sin nuevos endpoints. |
| Requisitos EARS | REQ-API-001, REQ-UI-002, REQ-DATA-001, REQ-DATA-002, REQ-SEC-001, REQ-SEC-003 |
| Dependencias | T-07,T-05 |
| Archivos afectados o previstos | src/lib/api/client.ts, errors.ts; tests/unit/integration |
| Pasos técnicos | Destino fijo; Authorization en memoria; timeout lecturas; sin retry write; clasificar 401/403/404/409/422/503 y resultado incierto; private/no-store; abort+epoch. |
| Pruebas necesarias | Q-03,Q-06 |
| Criterio de aceptación | Respuesta tardía no mezcla identidad; POST perdido no se repite; sin logs sensibles. |
| Evidencia de ejecución | 40 unitarias y E2E de respuesta perdida y firma inválida; E-02/E-03. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Doble write/cache compartida. |

### T-09 — Implementar conexión efímera y guard de navegación

| Campo | Detalle |
|---|---|
| Estado | DONE |
| Objetivo | Mantener JWT manual y limpieza de sesión sólo en Next. |
| Requisitos EARS | REQ-AUTH-001, REQ-AUTH-002, REQ-AUTH-003, REQ-RBAC-001, REQ-RBAC-003, REQ-DATA-002, REQ-OPS-003 |
| Dependencias | T-05,T-08; permiso auth expreso |
| Archivos afectados o previstos | src/lib/auth, app/connect, workspace/layout; tests |
| Pasos técnicos | Provider client; decode sólo UX; limpiar input/token/datos/context al logout/401; no prefetch privado; reconectar legacy; direction sin fetch de catálogo. |
| Pruebas necesarias | Q-03,Q-06,Q-07 |
| Criterio de aceptación | No storage/cookie/URL token; invalid/expired rechaza API; reconexión comprobada. |
| Evidencia de ejecución | JWT input borrado, storage vacío, reload, abort/epoch verificados. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Claims sin firma confundidos con autoridad. |

### T-10 — Adaptar shell y componentes mínimos HealthCore

| Campo | Detalle |
|---|---|
| Estado | IN_PROGRESS |
| Objetivo | Reusar identidad y semántica sin rediseño. |
| Requisitos EARS | REQ-UI-001, REQ-UI-002, REQ-ACC-001, REQ-ACC-002, REQ-ACC-003, REQ-SEC-002 |
| Dependencias | T-04,T-06 |
| Archivos afectados o previstos | src/components/ui,layout,forms,tables; styles/tokens.css |
| Pasos técnicos | Brand/header/nav/breadcrumb/pageheader/button/input/select/table/alert/badge/states/footer; dialog sólo necesario; escapar API; conservar breakpoints y foco. |
| Pruebas necesarias | Q-02,Q-05,Q-03 |
| Criterio de aceptación | Matriz componentes con visual/keyboard/contrast PASS, sin sidebar obligatoria inventada. |
| Evidencia de ejecución | Axe/320/393/1350 y inspección móvil realizadas; revisión manual completa teclado/zoom/contraste pendiente. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | XSS/foco/estilo distinto por overrides. |

### T-11 — Preparar proxy y runtime aislados

| Campo | Detalle |
|---|---|
| Estado | DONE |
| Objetivo | Probar convivencia /next, assets y API sin ampliar CORS. |
| Requisitos EARS | REQ-MIG-002, REQ-SEC-003, REQ-OPS-001, REQ-OPS-002 |
| Dependencias | T-06,T-08; D-03,D-05 infraestructura/conexiones aprobadas |
| Archivos afectados o previstos | Dockerfile Next futuro, Nginx template y Compose futuros autorizados |
| Pasos técnicos | Configurar basePath y rewrite /api-core destino fijo; preservar rutas hash/management; copiar src/TS correctamente; probar assets/deep links/headers/health. |
| Pruebas necesarias | Q-07,Q-10 |
| Criterio de aceptación | Old/new accesibles; auth upstream intacta; no cambio de volúmenes/BBDD. |
| Evidencia de ejecución | Imagen no root, Nginx/deep links, alias y Compose config verificados. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Mapa Nginx erróneo y exposición de auth. |

## Fase 2 — Piloto Management

### T-12 — Migrar consulta de catálogos piloto

| Campo | Detalle |
|---|---|
| Estado | DONE |
| Objetivo | Trasladar F-02 sin ampliar funcionalidad. |
| Requisitos EARS | REQ-MIG-001, REQ-UI-002, REQ-API-001, REQ-SEC-002, REQ-TEST-001 |
| Dependencias | T-01,T-08,T-09,T-10,T-11 |
| Archivos afectados o previstos | features/management/catalogs y app/management/catalogs; tests |
| Pasos técnicos | Leer /management/catalogs primera página; columnas/total mensaje existentes; loading/empty/403; texto React escapado; no escrituras ni paginador nuevo. |
| Pruebas necesarias | Q-02,Q-03,Q-05 |
| Criterio de aceptación | Paridad F-02 PASS con fixture normal/malicioso y rol permitido/denegado. |
| Evidencia de ejecución | Catálogos y estados; E2E Management y test XSS de DataTable. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | API HTML ejecutado o alcance aumentado. |

### T-13 — Migrar consultas de cuatro maestros

| Campo | Detalle |
|---|---|
| Estado | DONE |
| Objetivo | Trasladar selección y lectura F-03. |
| Requisitos EARS | REQ-MIG-001, REQ-API-001, REQ-UI-002, REQ-RBAC-001 |
| Dependencias | T-12 |
| Archivos afectados o previstos | features/management/reference-data; app correspondiente; tests |
| Pasos técnicos | Seleccionar cuatro recursos existentes; columnas actuales; error por rol; cancelar al cambiar recurso; no altas/edición ni catálogo nuevo. |
| Pruebas necesarias | Q-02,Q-03,Q-06 |
| Criterio de aceptación | Cuatro recursos y carreras/empty/errores equivalentes. |
| Evidencia de ejecución | Cuatro maestros consultados; cancelación de cambios por useQuery. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Respuesta anterior reemplaza recurso actual. |

### T-14 — Migrar auditoría Management autorizada

| Campo | Detalle |
|---|---|
| Estado | BLOCKED |
| Objetivo | Trasladar F-04 sin ampliar exposición. |
| Requisitos EARS | REQ-MIG-001, REQ-RBAC-001, REQ-SEC-001, REQ-SEC-003 |
| Dependencias | T-12; D-07 revisión exposición Claire |
| Archivos afectados o previstos | features/management/audit y app/audit; tests |
| Pasos técnicos | Mantener type/limit50/columnas; admin/compliance; no recuperar datos redactados; no logs/body persistidos. |
| Pruebas necesarias | Q-02,Q-03,Q-05 |
| Criterio de aceptación | Paridad/roles/redacción PASS y revisión necesaria registrada. |
| Evidencia de ejecución | UI sintética implementada; D-07 Claire sigue pendiente, no aprobación real de exposición. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Exposición de auditoría mayor que alcance aprobado. |

### T-15 — Validar piloto y navegación entre apps

| Campo | Detalle |
|---|---|
| Estado | BLOCKED |
| Objetivo | Demostrar arquitectura sin retirar código. |
| Requisitos EARS | REQ-MIG-002, REQ-AUTH-003, REQ-TEST-001, REQ-PERF-002, REQ-OPS-002 |
| Dependencias | T-12,T-13,T-14; D-08,D-05 |
| Archivos afectados o previstos | tests/e2e pilot; matriz y artefactos autorizados |
| Pasos técnicos | Rutas/hash/back/forward; reconexión esperada; errores y AA; comparar baseline; ensayo rollback links/map; solicitar activación sólo con evidencia concreta. |
| Pruebas necesarias | Q-03,Q-05,Q-07,Q-09,Q-10 |
| Criterio de aceptación | Piloto PASS y aprobación por separado; legacy intacto. |
| Evidencia de ejecución | Convivencia local probada; piloto empresarial y presupuestos/activación no autorizados. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Creer PASS de diseño autoriza despliegue. |

## Fase 3 — Migración modular e Inventory NEW UI

### T-16 — Migrar resumen de incidencias

| Campo | Detalle |
|---|---|
| Estado | IN_PROGRESS |
| Objetivo | Trasladar F-05 sin dashboard empresarial nuevo. |
| Requisitos EARS | REQ-MIG-001, REQ-RBAC-003, REQ-UI-002 |
| Dependencias | T-02,T-15 |
| Archivos afectados o previstos | features/incidents/summary; app/summary; tests |
| Pasos técnicos | Consumir metrics/open-by-severity, area scope/direction; labels existentes y estados; no detalles/prefetch. |
| Pruebas necesarias | Q-03,Q-04,Q-05 |
| Criterio de aceptación | Métricas por rol/área equivalentes; no exposición de descripción. |
| Evidencia de ejecución | Implementación presente; falta caracterización completa y matriz por rol, ver execution.md. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | API resumen confundida con acceso completo. |

### T-17 — Migrar cola y estado URL

| Campo | Detalle |
|---|---|
| Estado | DONE |
| Objetivo | Trasladar F-06 con filtros/orden/page20. |
| Requisitos EARS | REQ-MIG-001, REQ-UI-003, REQ-RBAC-002, REQ-RBAC-003, REQ-API-001 |
| Dependencias | T-16 |
| Archivos afectados o previstos | features/incidents/list; app/incidents; tests |
| Pasos técnicos | Mantener query/offset y sort; total servidor; area propia; direction summary; enlaces/volver; no filtros nuevos. |
| Pruebas necesarias | Q-03,Q-04,Q-07 |
| Criterio de aceptación | Back/forward y filtros no pierden contexto; permisos idénticos. |
| Evidencia de ejecución | Filtros/orden/retorno detalle/atrás/adelante verificados por E2E. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Filtro cliente presentado como servidor. |

### T-18 — Migrar detalle lectura y cronología

| Campo | Detalle |
|---|---|
| Estado | IN_PROGRESS |
| Objetivo | Trasladar F-08 lectura y F-10, sin mezclar contratos del handler React. |
| Requisitos EARS | REQ-MIG-001, REQ-UI-002, REQ-RBAC-002, REQ-RBAC-003, REQ-DATA-002, REQ-PERF-003 |
| Dependencias | T-17 |
| Archivos afectados o previstos | features/incidents/detail,history; app/incidents/[id]; tests |
| Pasos técnicos | GET detalle + ambos historiales; mantener error parcial nativo; escapar/redactar; merge orden temporal; lazy sólo medido; dirección denegada. |
| Pruebas necesarias | Q-03,Q-04,Q-05,Q-06,Q-09 |
| Criterio de aceptación | Historia/partial error/detalle y autoría equivalentes, respuesta tardía cancelada. |
| Evidencia de ejecución | Detalle e historia parcial verificados; justificación Profiler/lazy/memo pendiente. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Handler all-or-nothing usado sin paridad. |

### T-19 — Migrar formulario de alta

| Campo | Detalle |
|---|---|
| Estado | DONE |
| Objetivo | Trasladar F-07 sobre contrato vigente. |
| Requisitos EARS | REQ-MIG-001, REQ-API-004, REQ-RBAC-002, REQ-DATA-001, REQ-DATA-003, REQ-ACC-002 |
| Dependencias | T-18; D-06 recovery aprobado |
| Archivos afectados o previstos | features/incidents/create; app/incidents/new; tests |
| Pasos técnicos | Catálogos activos y clínica-jurisdicción; límites200/10000; trim; reporter omitido; create201 y detalle confirmed; incierto sin resend. |
| Pruebas necesarias | Q-03,Q-04,Q-06 |
| Criterio de aceptación | Validación/permisos/errores y una sola creación comprobados. |
| Evidencia de ejecución | Alta sintética real y reporter omitido; límites y permisos API vigentes. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Sin idempotencia, doble alta. |

### T-20 — Migrar editor título y descripción

| Campo | Detalle |
|---|---|
| Estado | DONE |
| Objetivo | Trasladar editor F-08 sin ampliar PATCH UI. |
| Requisitos EARS | REQ-MIG-001, REQ-RBAC-002, REQ-DATA-001, REQ-DATA-003, REQ-ACC-002 |
| Dependencias | T-18; D-06 aprobado |
| Archivos afectados o previstos | features/incidents/editor; tests |
| Pasos técnicos | Editor admin/technology/área propia; PATCH sólo title/description; conservar mensajes; releer autoritativo; recuperar conflicto/red. |
| Pruebas necesarias | Q-03,Q-04,Q-06 |
| Criterio de aceptación | Área ajena/compliance/direction no escriben; unknown fields no inventan rechazo nuevo. |
| Evidencia de ejecución | Edición title/description admin y área propia; ajena/compliance denegadas. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Ampliar capacidades por API general. |

### T-21 — Migrar transición de estado

| Campo | Detalle |
|---|---|
| Estado | IN_PROGRESS |
| Objetivo | Trasladar parte F-09 con grafo y motivos actuales. |
| Requisitos EARS | REQ-MIG-001, REQ-RBAC-001, REQ-DATA-001, REQ-DATA-003, REQ-ACC-002 |
| Dependencias | T-18,T-20; D-06 |
| Archivos afectados o previstos | features/incidents/transitions; tests |
| Pasos técnicos | Mapear grafo real; motivos UI cancel/onHold/reopened ≤2000; roles/área; post único; releer detail/history/summary; no arreglar gap motivo API. |
| Pruebas necesarias | Q-03,Q-04,Q-06 |
| Criterio de aceptación | Escenarios destino permitido/denegado/motivo/409 PASS y audit backend conservado. |
| Evidencia de ejecución | Transición underAnalysis real y grafo unitario; ampliar E2E motivos/destinos/conflictos. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Grafo histórico usado como contrato real. |

### T-22 — Migrar reasignación de área

| Campo | Detalle |
|---|---|
| Estado | DONE |
| Objetivo | Trasladar parte F-09 admin-only. |
| Requisitos EARS | REQ-MIG-001, REQ-RBAC-001, REQ-DATA-001, REQ-DATA-003 |
| Dependencias | T-21 |
| Archivos afectados o previstos | features/incidents/assignments; tests |
| Pasos técnicos | Área activa diferente y motivo obligatorio; sólo admin; POST assignments; actualizar historia/lista/ámbito; sin PATCH bypass. |
| Pruebas necesarias | Q-03,Q-04,Q-06 |
| Criterio de aceptación | API deniega technology/área/compliance/direction; auditoría backend intacta. |
| Evidencia de ejecución | Asignación admin persistente; technology/compliance 403 reales y otros roles sin control. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Permisos propuestos antiguos mezclados. |

### T-23 — Resolver conservación del historial React existente

| Campo | Detalle |
|---|---|
| Estado | DONE |
| Objetivo | Decidir F-11 sin duplicar ni mover web pública. |
| Requisitos EARS | REQ-ARCH-001, REQ-MIG-001, REQ-PERF-003, REQ-SEC-003 |
| Dependencias | D-09; T-18 |
| Archivos afectados o previstos | frontend/app/internal/incident-history y handler (lectura); traslado sólo autorizado |
| Pasos técnicos | Comparar all-or-nothing vs cronología parcial; mantener ruta como alternativa recomendada; si se autoriza traslado, preservar lazy/memo/private/timeout y registrar redirects. |
| Pruebas necesarias | Q-01,Q-03,Q-07,Q-09 |
| Criterio de aceptación | Decisión documentada; no módulo declarado migrado sólo por ruta. |
| Evidencia de ejecución | Historial existente conservado en frontend, enlace local y decisión explícita. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Mezcla sitio público y backoffice. |

### T-24 — Aprobar alcance NEW UI Inventory y selector clínica

| Campo | Detalle |
|---|---|
| Estado | IN_PROGRESS |
| Objetivo | Resolver dependencias frontend sin inventar APIs. |
| Requisitos EARS | REQ-MIG-004, REQ-RBAC-004, REQ-API-003, REQ-DATA-004 |
| Dependencias | D-04,D-06,D-07 |
| Archivos afectados o previstos | Diseño Inventory y matriz de contratos existentes |
| Pasos técnicos | Acordar F-13–16, UUID clínica vs entrega backend separada; sin GET config/total/lookup clínico; revisar exposición y recuperación. |
| Pruebas necesarias | Q-08 revisión documental |
| Criterio de aceptación | Autorización explícita NEW UI y UX viable con contratos existentes, límites aceptados. |
| Evidencia de ejecución | NEW UI y UUID expresamente autorizados; revisión externa D-07 pendiente. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Ampliación no autorizada de alcance previo. |

### T-25 — Crear UI catálogo y lotes Inventory

| Campo | Detalle |
|---|---|
| Estado | DONE |
| Objetivo | Exponer catálogo aprobado, no saldos editables. |
| Requisitos EARS | REQ-MIG-004, REQ-API-001, REQ-RBAC-004, REQ-DATA-004 |
| Dependencias | T-07,T-10,T-24 |
| Archivos afectados o previstos | features/inventory/items,lots; app/inventory/items; tests |
| Pasos técnicos | Lista/detalle/alta/edición title/presentation; código/unit/lot mode immutable; lotes opcionales; baja motivo y stock total cero; sólo admin escribe; arrays paginados. |
| Pruebas necesarias | Q-08,Q-03,Q-05 |
| Criterio de aceptación | Invariantes catálogo/pack/lotes/baja y roles PASS; sin reactivar/eliminar. |
| Evidencia de ejecución | Alta/lotes/baja historial en E2E; invariantes y edición cubiertas por regresión backend y código UI. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | InventoryAdmin recibe stock implícito. |

### T-26 — Crear UI stock, reorden e historial Inventory

| Campo | Detalle |
|---|---|
| Estado | DONE |
| Objetivo | Lecturas con scope real, sin snapshot global inventado. |
| Requisitos EARS | REQ-MIG-004, REQ-RBAC-004, REQ-API-003, REQ-DATA-004, REQ-UI-002 |
| Dependencias | T-25 |
| Archivos afectados o previstos | features/inventory/stock,reorder,history; app correspondientes; tests |
| Pasos técnicos | Clínica UUID aprobada, lot_id opcional; stock backend/base/pack; reorden clínico; offset/limit sin total; Siguiente explícito; país histórico. |
| Pruebas necesarias | Q-08,Q-03,Q-06 |
| Criterio de aceptación | US/UK aislados; igualdad no alerta; página corta no se considera fin; 409 config visible. |
| Evidencia de ejecución | Stock/reorden/historia scoped, igualdad20, UI sin total; pruebas reales US/UK y paginador unitario. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Listado clínico no soportado o fuga país. |

### T-27 — Crear configuración de reorden y entradas/salidas

| Campo | Detalle |
|---|---|
| Estado | DONE |
| Objetivo | Registrar sólo operaciones backend aprobadas. |
| Requisitos EARS | REQ-MIG-004, REQ-RBAC-004, REQ-DATA-001, REQ-DATA-003, REQ-DATA-004, REQ-ACC-002 |
| Dependencias | T-26; D-06 |
| Archivos afectados o previstos | features/inventory/configuration,movements; tests |
| Pasos técnicos | Manager configura positive reorder; operator/manager in/out quantity entera base/pack y lote si aplica; post confirmado relee stock/reorder/history; sin retry. |
| Pruebas necesarias | Q-08,Q-06,Q-05 |
| Criterio de aceptación | Umbral previo obligatorio; negativos rechazados; conversión/snapshot preservados. |
| Evidencia de ejecución | Configuración200 e in-pack201 reales, reread sin optimismo; reglas backend64. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Doble movimiento o umbral implícito. |

### T-28 — Crear conteos físicos y compensaciones

| Campo | Detalle |
|---|---|
| Estado | DONE |
| Objetivo | Preservar ajuste/compensación única manager-only. |
| Requisitos EARS | REQ-MIG-004, REQ-RBAC-004, REQ-DATA-001, REQ-DATA-003, REQ-DATA-004 |
| Dependencias | T-27 |
| Archivos afectados o previstos | features/inventory/counts,corrections; tests |
| Pasos técnicos | Adjust counted_quantity no negativo en base y motivo; correction original con motivo, no compensation of compensation; resultado incierto y verificación. |
| Pruebas necesarias | Q-08,Q-06 |
| Criterio de aceptación | Saldo/lote independiente y rechazo negativo/doble corrección; sin editar history. |
| Evidencia de ejecución | Count19 produce delta-1, corrección restaura20 y segunda409; inmutabilidad backend. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Conciliación ambigua y concurrencia. |

### T-29 — Crear auditoría/denegaciones Inventory

| Campo | Detalle |
|---|---|
| Estado | BLOCKED |
| Objetivo | Mostrar evidencia autorizada sin ampliar retención. |
| Requisitos EARS | REQ-MIG-004, REQ-RBAC-004, REQ-SEC-001, REQ-SEC-003 |
| Dependencias | T-26; D-07 Claire |
| Archivos afectados o previstos | features/inventory/audit,denials; app/audit; tests |
| Pasos técnicos | Auditor país histórico; unknown país sólo denegación propia según API; redactado, retention_until informativo; sin purge/export/restore texto. |
| Pruebas necesarias | Q-08,Q-03,Q-05 |
| Criterio de aceptación | Scopes/redacción/24meses coherentes y review exposición registrada. |
| Evidencia de ejecución | Auditor US y clínica UK denegada en E2E; revisión exposición Claire pendiente. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Retención interpretada como borrado permitido. |

## Fase 4 — Validación integral

### T-30 — Adaptar telemetría opt-in al shell Next

| Campo | Detalle |
|---|---|
| Estado | BLOCKED |
| Objetivo | Mantener captura existente sin ampliar eventos por inferencia. |
| Requisitos EARS | REQ-SEC-004, REQ-AUTH-002, REQ-SEC-001 |
| Dependencias | D-07,D-03 permisos; T-09,T-10 |
| Archivos afectados o previstos | src/lib/telemetry adaptador, contrato/runtime existente lectura; tests |
| Pasos técnicos | Integrar connect/activateClinic/navigate/disconnect con efectos cleanup; deshabilitada default; config pública tres campos; no HMAC/JWT key client; fallos no negocio. |
| Pruebas necesarias | Q-03,Q-09 |
| Criterio de aceptación | Evento/ámbito aprobado, desconexión/StrictMode no duplica capture; sin secretos. |
| Evidencia de ejecución | Adaptador deshabilitado default y 74 tests nativos PASS; ensayo opt-in/StrictMode nuevo y D-07 pendientes. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Telemetría cruza país o amplía tratamiento. |

### T-31 — Ejecutar regresión integral por roles y módulos

| Campo | Detalle |
|---|---|
| Estado | IN_PROGRESS |
| Objetivo | Cerrar matriz funcional/error/AA/perf por F. |
| Requisitos EARS | REQ-TEST-001, REQ-TEST-002, REQ-MIG-001, REQ-ACC-001, REQ-ACC-002, REQ-ACC-003, REQ-PERF-001, REQ-PERF-002 |
| Dependencias | T-15–22; T-25–30 sólo alcance habilitado |
| Archivos afectados o previstos | tests/e2e/integration y matrices de aceptación autorizadas |
| Pasos técnicos | Ejecutar Q completos contra datos sintéticos aislados; backend suite sólo aislamiento demostrado; comparar expected/actual; confirmar no secrets; bloquear módulos con evidencia ausente. |
| Pruebas necesarias | Q-01–Q-10 |
| Criterio de aceptación | Matriz F habilitados PASS, skips no aceptación, limitaciones explícitas. |
| Evidencia de ejecución | 40 unitarias +15 E2E +64 backend +74 telemetría; falta matriz completa Q/performance/manualAA. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Pruebas históricas usadas como actuales. |

## Fase 5 — Activación y retirada progresiva

### T-32 — Preparar activación y ensayo rollback por módulo

| Campo | Detalle |
|---|---|
| Estado | BLOCKED |
| Objetivo | Resultado concreto antes de aprobación de despliegue. |
| Requisitos EARS | REQ-MIG-002, REQ-OPS-001, REQ-OPS-002, REQ-OPS-003 |
| Dependencias | T-31; D-05 autorización infra y entorno |
| Archivos afectados o previstos | Mapa proxy/version/build/runbook futuros autorizados |
| Pasos técnicos | Build/runtime/health/assets/deeplinks; guardar mapa anterior; ensayo restauración rutas en aislado; documentar Inventory sin UI antigua; solicitar deploy sólo al cerrar evidence. |
| Pruebas necesarias | Q-07,Q-10 |
| Criterio de aceptación | Rollback probado sin datos perdidos/downgrade DB; aprobación expresa antes activación. |
| Evidencia de ejecución | Configuración/health/rollback de rutas preparados localmente; activación no autorizada. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Desplegar o alterar infra sin permiso. |

### T-33 — Retirar legado autorizado por módulo

| Campo | Detalle |
|---|---|
| Estado | BLOCKED |
| Objetivo | Eliminar únicamente tras todas las condiciones de salida. |
| Requisitos EARS | REQ-MIG-003, REQ-OPS-001, REQ-OPS-002 |
| Dependencias | T-32; eliminación/deploy expresamente aprobados |
| Archivos afectados o previstos | Archivos legacy concretos aprobados; README bilingües futuros |
| Pasos técnicos | Revisar ownership/tráfico/paridad/roles/AA/budget; validar dependencias telemetry/assets; retirar sólo lista autorizada; conservar rollback disponible. |
| Pruebas necesarias | Q-07,Q-10 y review validate-delivery |
| Criterio de aceptación | Cero módulos retirados sin PASS y autorización; no borrar evidencia/volúmenes. |
| Evidencia de ejecución | Fuera de alcance autorizado: cero eliminaciones, ningún despliegue. Evidencia y comandos: [execution.md](./execution.md). |
| Riesgos | Retirada irreversible de dependencia compartida. |

## Primer bloque después de aprobar el SDD

T-00–04: registrar decisiones, caracterizar Management/incidentes, congelar contratos y medir baseline. T-05 desbloquea diseño auth/conexión antes de implementación; T-06 sólo con aprobación de dependencias/estructura. Después T-07/08/10 pueden preparar tipos, cliente y componentes dentro del alcance aprobado. Proxy/session y NEW UI tienen gates independientes; no inferir permisos de una tarea TODO.

## Cobertura y cierre

Cada requisito EARS aparece en al menos una tarea; todos los F habilitados requieren prueba Q y matriz de paridad o aceptación NEW UI. D-04 bloquea T-24–29 y D-07 los bloques de exposición afectados. Los gaps backend no se resuelven creando endpoints aquí. El cierre de implementación exige evidencias por tarea, revisión final y autorizaciones expresas; este archivo no solicita ni ejecuta commit.


## Cierre de esta ejecución

Implementación sintética disponible en migration/backofficeMigration. DONE no autoriza producción, piloto, activación, commit ni retirada. El cierre global del SDD sigue pendiente; se detallan los bloqueos y validaciones restantes en execution.md.
