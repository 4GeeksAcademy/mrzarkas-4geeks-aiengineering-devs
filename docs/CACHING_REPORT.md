# CACHING_REPORT — HealthCore

Fecha: 2026-11-01. Referencia: feature/caching-optimisation. Implementación y validación técnica completadas para desarrollo sintético; commits locales autorizados tras PASS. No autorización de piloto/producción ni certificación HIPAA/UK GDPR.

## Alcance revisado y autorizado

El usuario autorizó caché in-process con TTL de dos catálogos, invalidación, aislamiento y pruebas sintéticas; excluyó modificar autenticación, auditoría, infraestructura o dependencias. Tras la revisión tecnológica aprobó implementar la alternativa React interna. Backend continúa en backend/ y backoffice en JavaScript nativo, sin modificación. Portada Next.js conservada.

La ruta nueva `/internal/incident-history` es una vista operativa interna separada de la portada. No se presenta como integración EHR. El usuario pidió documentar en este informe. Memory Bank adicional y Rules no se modifican; los tres documentos SDD originales siguen como diseño histórico, con los cambios de candidatos trazados aquí. No se presume autorización para editar otros archivos protegidos ni efectuar commit/push/PR/despliegue.

## Backend implementado

| Lectura | TTL | Contenido y clave | Invalidación |
| --- | --- | --- | --- |
| GET /catalogs/{catalog_name} | 60 s | Snapshot JSON de valores, flags y fechas; namespace active, identidad/rol/área, catálogo, version+updated_at, contract-v1, todo en digest SHA-256 | Generation consultada en DB antes de hit; recheck antes de publicar miss; vigencia se filtra en UTC en cada lectura |
| GET /management/catalogs/{catalog_name}/values | 30 s | Página JSON íntegra, items/total y metadata; namespace managed-values, mismos ámbitos, offset/limit | Misma generación tras las tres mutaciones existentes |

Catálogos activos se cargan con flags y fechas incluso futuras; el filtro temporal se vuelve a aplicar en cada hit, conservando effective_from <= now y effective_to >= now. Así no se oculta una activación o expiración por el TTL. Valores inactivos no se devuelven en la vista activa; Management conserva su contrato. No hay sesión/objeto ORM/request en memoria global.

Las escrituras existentes de alta, edición y activación actualizan version y updated_at; no se cambió su código, auditoría ni transacción. La clave incluye ambos campos para reducir riesgo de colisión de incrementos concurrentes. Entradas antiguas quedan inaccesibles para peticiones con generación nueva; recheck evita publicar refill de generación anterior. Lecturas ya iniciadas conservan semántica de aislamiento DB. Actualizaciones externas sin metadata NO están cubiertas y requieren bypass/reset aprobado.

Límites: 256 entradas, 8 MiB de payload JSON, 256 KiB por entrada; overhead de claves/objetos adicional acotado por entradas. LRU, limpieza de expiradas al escribir y expiración monotonic. 64 stripes de locks, espera máxima 2 s; timeout/fallo de caché => lectura origen autorizada. Fallos fuente no se convierten en éxito. Reinicio frío y caché independiente por worker; metadata de DB se consulta siempre. No Redis ni dependencia nueva.

Cada endpoint conserva require_capability y JWT vigente en hits. La partición usa identidad/rol/área sin IDs legibles, JWT, cookies, PHI ni query strings en claves/logs. Clínica/jurisdicción/tenant no son claims actuales: no se finge soporte. Si pasan a influir en la respuesta, el diseño debe incorporar esa dimensión antes de compartir datos. Catálogos Management incluyen actor metadata: sólo ámbito privado autorizado sintético; revisión formal de privacidad sigue pendiente para uso real.

## Frontend implementado

| Componente real añadido tras aprobación | Lazy Loading | Activación |
| --- | --- | --- |
| frontend/app/internal/incident-history/timeline.js | next/dynamic, boundary cliente, ssr:false | Tras una consulta autorizada de historial; ausente del árbol inicial |
| frontend/app/internal/incident-history/event-details.js | next/dynamic, boundary cliente, ssr:false | Sólo al seleccionar evento |

Ambos tienen fallback role=status y recuperación ante error mediante LazyErrorBoundary con recarga explícita. La recarga pierde credenciales deliberadamente. La vista interna es noindex; la portada, hero/LCP, SSR institucional, anclas y enlaces no se difieren.

workspace.js almacena JWT sólo en estado de memoria, sin URL/storage; consulta explícita, cancelación/epoch frente a datos obsoletos al cambiar incidencia/token/desconectar. El handler Next `/api/incident-history` reenvía las dos lecturas existentes (history/assignment-history), autorización en API para cada una, redirect:error, timeout 5 s y private/no-store. No hay nuevo verificador JWT, política de permisos, cambio de CORS o almacenamiento de token. UUID se valida y sólo se envían datos si ambas lecturas se autorizan. React escapa los campos y la política audit-output-v1 continúa en backend.

useMemo está en Timeline: combinación y sort de statusHistory/assignmentHistory mediante chronology.mjs, O(n log n), con dependencias completas `[statusHistory, assignmentHistory]`. Arrays se reemplazan tras nueva consulta y no se mutan. Cambiar evento seleccionado re-renderiza Timeline sin recomputar esos historiales. No se promete reducir commits React por memoizar un valor. La cronología dejó de ser una alternativa hipotética tras la aprobación; no se introdujo un cálculo artificial ni se migró el backoffice.

Chunks inspeccionados en build de producción, bytes JS sin compresión (no waterfall de navegador):

| Módulo | Chunk | Bytes |
| --- | --- | ---: |
| event-details | 05lvmxfxifxgz.js | 633 |
| timeline | 3c521zfh0xrol.js | 1258 |

## Método, datos y resultados backend

Artefacto reproducible: [caching-benchmark.json](./caching-benchmark.json), ejecutado con `podman compose --profile test run --no-deps --rm test uv run --no-sync python tests/benchmark_caching.py`. Código en backend/tests/benchmark_caching.py. FastAPI ASGI y PostgreSQL local de Podman, sesión/transacción reutilizada, sin coste HTTP externo, concurrencia 1. Actor admin sintético. Tres rondas, cada una 20 warmup + 200 muestras por modo/ruta; before es código final con caché deshabilitada, after es caché caliente: NO checkout antiguo ni cold-start.

Dataset: 200 valores creados temporalmente en un catálogo sintético, orden/fechas válidos, página Management limit=100. Escenario de escala, no tamaño/frecuencia real de catálogo ni datos de pacientes. No se inflan catálogos persistentes ni se anuncia necesidad operativa a partir del escenario. Valores totales 28 → 228 → 28 tras rollback; no commit del benchmark. Idempotencia por transacción reversible y conteo posterior. No se añadieron incidencias/clínicas ni se transfirieron datos entre US/UK.

p50/p95 nearest-rank, ms; todas las respuestas fueron 200. SELECT por request medido incluye metadata de generación; no parámetros SQL ni datos privados en resultados. Bytes son respuesta HTTP ASGI sin compresión.

| Endpoint | Ronda | Modo | p50 ms | p95 ms | SELECT/request | Bytes |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| active-catalog | 1 | cache off | 3.096 | 3.652 | 2 | 41560 |
| active-catalog | 1 | warm cache | 1.282 | 1.377 | 1 | 41560 |
| active-catalog | 2 | cache off | 3.049 | 3.387 | 2 | 41560 |
| active-catalog | 2 | warm cache | 1.306 | 1.656 | 1 | 41560 |
| active-catalog | 3 | cache off | 3.163 | 5.381 | 2 | 41560 |
| active-catalog | 3 | warm cache | 1.287 | 1.393 | 1 | 41560 |
| managed-values | 1 | cache off | 2.461 | 2.630 | 3 | 41293 |
| managed-values | 1 | warm cache | 1.161 | 1.538 | 1 | 41293 |
| managed-values | 2 | cache off | 2.455 | 2.651 | 3 | 41293 |
| managed-values | 2 | warm cache | 1.143 | 1.289 | 1 | 41293 |
| managed-values | 3 | cache off | 2.463 | 2.655 | 3 | 41293 |
| managed-values | 3 | warm cache | 1.144 | 1.217 | 1 | 41293 |

Las tres rondas reducen p95 y SELECT: activo 2→1, Management 3→1. Coste de cold miss final: una consulta adicional de recheck; no se presenta como mejora de cold start. Por ronda caliente: 220 llamadas, 219 hits/1 miss incluyendo warmup (99,55%); las 200 muestras medidas son hits. Las rondas off son bypass, excluidas del hit ratio. No hay tráfico real observado: este artefacto secuencial sólo respalda el escenario sintético repetido por identidad; la comparación HTTP concurrente se documenta por separado abajo.

## Cálculo React y baseline frontend

`node scripts/profile_react_chronology.mjs` mide chronology.mjs real en Node v18.20.3, 20 warmup + 200 muestras, entradas sintéticas, percentiles nearest-rank. Artefacto [caching-react-calculation.json](./caching-react-calculation.json). No es React Profiler ni medición del hook/commits/render DOM. El resultado fundamenta coste escalable; no demuestra volúmenes habituales.

| Eventos sintéticos | p50 ms | p95 ms |
| ---: | ---: | ---: |
| 20 | 0.037 | 0.047 |
| 200 | 0.555 | 0.804 |
| 2000 | 5.265 | 6.208 |

El baseline estático anterior, [caching-baseline.json](./caching-baseline.json), inventaría 28 operaciones y fuentes (app.js nativo 39763 bytes, select-field 422, page.js 7379). [caching-after.json](./caching-after.json) confirma fuentes iniciales conservadas. La vista React es nueva: no se inventa un before de una ruta que no existía. Perfil anterior de cronología nativa es histórico: caching-calculation-profile.json. Lighthouse del 2026-10-29 y medición de serialización anterior no son evidencia de mejora de caching.

## Cierre de comparativas (2026-11-01)

A/B React real: [caching-react-comparison.json](./caching-react-comparison.json). Dos builds temporales con `next build --profile`; variante direct elimina únicamente useMemo del mismo cálculo chronology.mjs mediante `CACHING_PROFILE_MODE=direct` en scripts/caching_profile_setup.cjs. No cambios de aplicación entregada ni dependencias. Chrome, mismo dataset de 1000 eventos de estado + 1000 de asignación, tres rondas por variante, 20 selecciones warmup + 200 medidas. Dos requestAnimationFrame entre selecciones; suma de actualDuration de commits por selección, percentiles nearest-rank. Incluye render DOM y sobrecoste de Profiler; no intercalación aleatoria ni volumen real demostrado.

| Ronda | Direct p50/p95 ms | useMemo p50/p95 ms | Recálculos direct/memo |
| --- | --- | --- | --- |
| 1 | 4,600 / 5,400 | 3,600 / 4,500 | 200 / 0 |
| 2 | 4,600 / 5,200 | 3,500 / 4,200 | 200 / 0 |
| 3 | 4,600 / 5,300 | 3,500 / 4,300 | 200 / 0 |

El resultado demuestra menor trabajo al conservar referencias y seleccionar eventos; nueva consulta sí vuelve a calcular, comprobado anteriormente. No reduce el número de renders.

A/B backend concurrente: [caching-workers.json](./caching-workers.json), campo concurrent_benchmark. Loopback HTTP real con Uvicorn, PostgreSQL aislado y sesión independiente por request, concurrencia 10, tres rondas, 20 warmup + 200 muestras por modo/ruta. Dataset distinto al benchmark secuencial de escala: dos valores sintéticos, uno desactivado tras la prueba de mutaciones. No comparar cifras absolutas entre ambos datasets/transportes. Todas las respuestas 200; bytes iguales por modo. Media SELECT medida sobre las 200 llamadas concurrentes, sin parámetros SQL.

| Ruta | Ronda | Off p50/p95 ms | Warm p50/p95 ms | SELECT off/warm |
| --- | --- | --- | --- | --- |
| active | 1 | 45,008 / 108,506 | 43,956 / 59,363 | 2 / 1 |
| active | 2 | 44,255 / 77,970 | 43,024 / 51,014 | 2 / 1 |
| active | 3 | 43,993 / 66,383 | 43,952 / 51,522 | 2 / 1 |
| managed | 1 | 44,980 / 71,605 | 43,963 / 62,196 | 3 / 1 |
| managed | 2 | 44,045 / 67,102 | 43,165 / 62,303 | 3 / 1 |
| managed | 3 | 44,034 / 72,471 | 43,671 / 56,692 | 3 / 1 |

p95 mejora en las tres rondas; p50 cambia poco con catálogos pequeños y coste de transporte. No se atribuye una mejora operacional global. Cada modo warm medido tiene 200 hits/0 misses. La misma ejecución verificó coherencia entre procesos y eliminó la base temporal al finalizar.

Revisión móvil cerrada con viewport Responsive 393×852 y zoom de Chrome restablecido con Cmd+0 desde la barra de direcciones (fuera de DevTools). El zoom previo de Chrome explicaba recortes del emulador. Contenido, formulario, cronología y detalle revisados visualmente; main/body.scrollWidth=393, cero descendientes fuera de 393, storage vacío. Los clics AX sobre campos emulados se desviaban a la consola: el fixture se cargó con setter/input events y requestSubmit en DevTools, sin cambiar fuentes; teclado e interacción desktop comprobados aparte. Cuatro selecciones adicionales no descargaron scripts nuevos. No se certifica comportamiento de un dispositivo físico ni E2E con token real.

## Pruebas ejecutadas y regresión

- `podman compose --profile test run --no-deps --build --rm test`: 150 passed in 1.77s, imagen test 94ac2152201c. Nuevos tests: TTL exacto, serialización independiente, LRU/oversize, diez fills concurrentes/single-flight, rechazo de generación obsoleta, fallo caché/origen y locks liberados; HTTP hit/miss/401/403/422, aislamiento actor/rol/área por claves, fronteras UTC deterministas; tres mutaciones reales PostgreSQL en savepoint bajo rollback exterior, catálogo temporal eliminado por rollback.
- Hubo un fallo inicial de pool compartido entre event loops al añadir la prueba DB. Se corrigió creando motor NullPool exclusivo de la prueba. La suite final pasa; no se modificó configuración de conexión de la aplicación.
- `podman compose build frontend`: PASS, Next.js 16.4.3, imagen a866a9b25c23; rutas /, /api/incident-history y /internal/incident-history compiladas. No test/lint frontend configurado; no se anuncia ejecución inexistente.
- `node --experimental-default-type=module scripts/test_caching_frontend.mjs`: PASS orden/inmutabilidad/vacío, reenvío privado y 401/422/403/200/503/no-store.
- OpenAPI final [caching-openapi.json](./caching-openapi.json): paths y components idénticos a docs/serialization-openapi.json, 28 operaciones backend. El nuevo handler Next no es operación FastAPI ni cambia sus contratos.
- Vista previa local temporal en puerto 3001: HTTP 200 en landing y cronología, 401 anónimo y private,no-store comprobados en [caching-preview-http.json](./caching-preview-http.json). El artefacto HTTP corresponde al preview anterior; las pruebas Chrome posteriores usaron la imagen final a866a9b25c23 con error boundary. No se sustituyeron servicios existentes.
- Inventario y `git diff --check`: PASS. El primer comando Compose de suite ejecutó db-init existente (migración/seed sintético local); las siguientes ejecuciones usaron --no-deps. No se alteraron archivos de migración, infraestructura, secretos ni dependencias.

## Exclusiones, frescura y límites

No cachear health/status, JWT, decisiones de permisos, mutaciones, incidencias privadas, historial o auditoría. /status mantiene SELECT 1/no-store. La cronología recibe historiales sólo mediante petición privada sin caché; no CDN/browser/proxy compartido. Version+updated_at y filtro temporal priman sobre evitar la consulta de generación; hay una consulta por hit.

Validación adicional 2026-11-01: Chrome nativo disponible aunque el inventario de proveedores de navegador estaba vacío. [caching-browser.json](./caching-browser.json) registra ResourceTiming: cero chunks diferidos inicialmente; Timeline descargado tras consultar (1038 bytes transferidos, 10,6 ms), EventDetails tras seleccionar (933 bytes, 12 ms). Se observaron ambos loading, selección por teclado y detalle redactado. La respuesta de historiales se sustituyó exclusivamente por un fixture sintético en DevTools; autorización y errores del proxy se verificaron por tests separados, no se afirma E2E con credenciales reales. Los tiempos incluyen pausas manuales y no son métricas LCP ni comparación de velocidad de carga.

React Profiler real en compilación temporal `next build --profile`, con instrumentación sólo dentro de contenedor descartable mediante scripts/caching_profile_setup.cjs: cinco commits actualDuration 0,6 / 8,2 / 1,3 / 1,3 / 0,9 ms, una ejecución del cálculo y una consulta al seleccionar dos eventos; nueva consulta con nuevos arrays: dos ejecuciones/dos consultas acumuladas. Esto confirma reutilización e invalidación del hook; no mide ahorro de render frente a una versión sin useMemo. El coste puro escalable sigue documentado por Node. Sin dependencias ni instrumentación añadidas a la aplicación entregada.

Se forzó un error del script Timeline interceptando temporalmente document.head.appendChild en DevTools: apareció el mensaje de recuperación; Recargar vista volvió al formulario con token y UUID vacíos. localStorage/sessionStorage vacíos. Se rechazaron las propuestas de guardar el texto sintético de Chrome/LastPass. Errores de extensiones LastPass/Passbolt no se atribuyen a la aplicación. Revisión desktop visual y emulación iPhone 16 393×852 realizadas: main.scrollWidth=393, viewport inicial=393; al reabrir DevTools innerWidth cambió a 800 con main aún 393. Se conserva esta anomalía de zoom y no se certifica responsive completo.

[validate_caching_workers.py](../backend/tests/validate_caching_workers.py) ejecutado con `podman compose --profile test run --no-deps --build --rm test uv run --no-sync python tests/validate_caching_workers.py`: exit 0. [caching-workers.json](./caching-workers.json) confirma dos procesos PID 8/9, ambos calientes antes de escrituras, invalidación update/create/activation visible en el otro proceso, 20 lecturas concurrencia 10 coherentes (14 hits/6 misses). Base PostgreSQL temporal independiente creada y eliminada, base de aplicación intacta. La ejecución posterior incorpora el A/B HTTP concurrente descrito en el cierre de comparativas.

Comparativas A/B concurrentes y React y revisión móvil cerradas con evidencia arriba. La ausencia de frecuencia operacional real sigue siendo una limitación de extrapolación, no una afirmación de ahorro real. No se añadió un seeder de incidencias ajeno al dominio de los catálogos.

Cumplimiento/Gobierno del Dato (Claire Whitfield) debe revisar impactos de privacidad/metadata/retención antes de uso real; no se atribuye su aprobación a la del usuario. No datos reales ni producción. Los SDD siguen sin marcar tareas pendientes como completas; el informe conserva trazabilidad del alcance revisado.

## Trazabilidad y revisión de entrega

| Requisitos | Implementación/evidencia | Resultado |
| --- | --- | --- |
| FR-CACHE-001/002 | Inventarios + OpenAPI idéntico + tests | PASS |
| FR-CACHE-003/004 | Candidatos nativos sustituidos por Timeline/EventDetails Next tras revisión usuario; next/dynamic y chunks | PASS técnico; chunks y UX sintética observados |
| FR-CACHE-005 | Timeline useMemo, chronology.mjs, perfil y dependencias | PASS sintético; Profiler real y comparación A/B |
| FR-CACHE-006/007/008/009 | cache.py y dos routers; TTL/fechas/generación, writes PostgreSQL | PASS sintético |
| FR-CACHE-010 | Este informe, scripts y JSON enlazados | PASS con limitaciones explícitas |
| NFR-CACHE-001/002/003 | Benchmark reversible, conteos, perfiles Node/chunks | PASS sintético; A/B React y HTTP concurrente |
| NFR-CACHE-004/005/006/007 | Fallos, límites, fills, regresión | PASS técnico sintético; multiworker/recuperación comprobados |
| SEC-CACHE-001/002/003/004/005 | Autorización intacta, particiones digest/no-store/sintético | Validación técnica; revisión formal de Gobierno del Dato pendiente |

Skill validate-delivery aplicada por lectura explícita, revisión read-only del diff y archivos nuevos; task: caching, rama feature/caching-optimisation. Fuentes inspeccionadas: contexto obligatorio, índices/Rules/conventions, README raíz/backend/frontend/backoffices/scripts/docs, SDD, routers/cache, fuentes React, scripts/tests y todos los artefactos aquí enlazados.

| AC | Estado | Método y evidencia |
| --- | --- | --- |
| AC-01 | PASS | Contexto obligatorio/Rules consultados en sesión |
| AC-02 | PASS | Terminología operativa, sintético, no EHR/producción afirmados |
| AC-03 | PASS | backend existente, frontend interno aprobado, backoffice nativo intacto |
| AC-04 | PASS | Rules revisadas; README bilingües; sin cambios de Rules |
| AC-05 | PASS | Autorizaciones usuario de caché/alcance React y reporte; protegidos excluidos |
| AC-06 | PASS | Revisión diff/nuevos archivos: datos sintéticos, no JWT real/PHI/secretos |
| AC-07 | PASS | Suite/build/Node/HTTP/Chrome/Profiler/multiworker y A/B concurrente/React pasan; evidencia enlazada |
| AC-08 | PASS | Requisitos revisados del reto: dos next/dynamic, useMemo con A/B real, dos TTL aislados, invalidación, métricas y regresión |
| AC-09 | PASS | Diff de alcance y artefactos; SDD preexistentes preservados; commits locales autorizados |
| AC-10 | PASS | Conclusiones trazadas a código, comandos y JSON; límites señalados |

Cierre de esta validación: contenedores temporales healthcore-caching-preview y healthcore-caching-profiler detenidos; pestañas de prueba cerradas, sin guardar credenciales. `node --check scripts/caching_profile_setup.cjs`, parseo de los nuevos JSON y `git diff --check`: exit 0. No cambios de código de aplicación en esta continuación ni modificaciones de SDD/Rules. Los contenedores A/B healthcore-caching-memo y healthcore-caching-direct y sus tres pestañas se cerraron al finalizar.

Recomendaciones: medir frecuencia operacional y obtener revisión formal de privacidad antes de promover el prototipo. La entrega evaluada se limita al código y validación con datos sintéticos aprobados; no modifica políticas de privacidad, auditoría, retención ni procesa PHI real. No autoriza piloto/producción. Estado de validación técnica de este alcance: **PASS**; no quedan comprobaciones técnicas obligatorias pendientes. Los SDD originales se conservan como diseño histórico sin reescribir rutas/candidatos o estados protegidos; este informe documenta la revisión expresamente aprobada del alcance.

Revisión final antes de commits: 40 archivos de texto changed/untracked inspeccionados, todos los JSON parseados, sin literales de clave privada/JWT en el escaneo acotado; revisión manual de alcance y fixtures sintéticos. `git diff --check`: exit 0. No detector automático de PHI general ni certificación de privacidad. Autorización de commits: usuario solicita generar commits; ratifica completar validación antes de crearlos. No push autorizado.
