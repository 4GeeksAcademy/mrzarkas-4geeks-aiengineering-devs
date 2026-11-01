# Entrega académica — Caching

Fecha: 2026-11-01. Rama: `feature/caching-optimisation`. Referencia de implementación: `e3edee3`.

Esta revisión prepara la evaluación de 4Geeks; no representa una calificación del evaluador ni autorización de producción. Fuente de criterios: briefing inicial del usuario y [cobertura SDD](../memory-bank/specs/cachingOptimisation/spec.md), con la revisión tecnológica posterior expresamente aprobada. El backend real está en `backend/`; el backoffice conserva JavaScript nativo.

## Cobertura de criterios

| Criterio | Requisitos | Implementación / evidencia | Disposición |
| --- | --- | --- | --- |
| Dos Lazy Loading | FR-CACHE-003/004, NFR-CACHE-002 | Timeline y EventDetails mediante next/dynamic; [chunks](caching-lazy-chunks.json), [navegador](caching-browser.json) | Verificado técnicamente; sustituye los candidatos nativos iniciales tras aprobación |
| useMemo no trivial | FR-CACHE-005 | Merge/sort de historiales, dependencias statusHistory/assignmentHistory; [A/B React](caching-react-comparison.json) | Verificado: 200→0 recálculos por ronda de selección; nuevos arrays sí recalculan |
| Dos endpoints TTL | FR-CACHE-006/007/009 | Catálogo activo 60 s y páginas Management 30 s; [benchmark](caching-benchmark.json), backend/tests/test_caching.py | Verificado; actor/rol/área, catálogo, generación y página aislados |
| Invalidación | FR-CACHE-008 | Generación version+updated_at, recheck y vigencia UTC; [dos procesos](caching-workers.json) | Verificado tras alta, edición y desactivación, sin modificar auditoría |
| Datos y mediciones | NFR-CACHE-001/002/003 | 28→228→28 valores con rollback; A/B secuencial y HTTP concurrente; Node y React Profiler | Verificado dentro de escenarios sintéticos; no se implementó un seeder persistente de incidencias |
| Seguridad y regresión | SEC-CACHE-001–005, FR-CACHE-001, NFR-CACHE-004–007 | 150 tests, OpenAPI conservado, errores/aislamiento/TTL/locks; proxy privado no-store | Validación técnica sintética; revisión formal de privacidad pendiente antes de uso real |
| Informe | FR-CACHE-010 | [CACHING_REPORT](CACHING_REPORT.md): método, before/after, TTL/claves, hit ratio, exclusiones y riesgos | Cubierto; las cifras remiten a artefactos y comandos |

Los tres SDD se conservan como diseño histórico: no se reescriben sus candidatos ni se marcan todas sus tareas Pending como ejecutadas. La trazabilidad del alcance revisado vive en CACHING_REPORT. La fase inicial de “sólo tres documentos” terminó antes de la autorización de implementación.

## Paquete de evaluación

1. Leer [CACHING_REPORT](CACHING_REPORT.md) y esta matriz.
2. Seguir [la demostración](CACHING_DEMO.md), de unos seis minutos.
3. Revisar los cuatro commits: `82bfe92` diseño, `1d2260a` backend, `091c90d` frontend, `e3edee3` evidencia.
4. Usar [el borrador de PR](CACHING_PR_DRAFT.md) cuando se autorice publicación. No se ha efectuado push ni creado una PR remota.

## Límites que deben explicarse

- No hay frecuencia operacional real medida; los resultados no demuestran ahorro real de HealthCore.
- La vista React fue una alternativa mínima aprobada, no un cálculo React preexistente ni una migración del backoffice.
- La demostración visual usa fetch simulado; las pruebas API/proxy comprueban autorización aparte. No se afirma E2E autenticado de navegador.
- Profiler incluye render DOM y sobrecoste de instrumentación; las variantes no se intercalaron aleatoriamente.
- La coherencia requiere que todas las escrituras actualicen version/updated_at. No se soportan escrituras externas que omitan esa metadata.
- Claire Whitfield debe revisar privacidad antes de uso real; no se atribuye una aprobación externa a estas pruebas.

Resultado de preparación documental: criterios enlazados a evidencia verificable; calificación académica y promoción a producción fuera de esta revisión.

## Revisión de preparación documental — validate-delivery

Task: preparar cobertura, demostración y borrador local de PR. Change reference: rama feature/caching-optimisation; código evaluado hasta e3edee3; nueva preparación documental posterior. La skill se leyó explícitamente; la revisión no modifica código ni configuración.

Fuentes inspeccionadas: CONTEXT.md, AGENTS.md, los tres documentos obligatorios del Memory Bank, sus índices/conventions, Rules activas/documentales, docs/README.md, briefing original, spec.md, CACHING_REPORT, fuentes workspace/timeline/chronology, inventario de artefactos, Git y los cuatro documentos de preparación. No existe .github ni plantilla de PR local.

| AC | Estado | Método / evidencia |
| --- | --- | --- |
| AC-01 | PASS | Contexto obligatorio e índices/Rules leídos en sesión |
| AC-02 | PASS | Documentos distinguen prototipo sintético, evaluación académica y uso real |
| AC-03 | PASS | Sólo docs; conserva backend existente y backoffice nativo |
| AC-04 | PASS | Reglas de documentación, Git y datos sensibles revisadas |
| AC-05 | PASS | Usuario pide ejecutar preparación; sin modificar Memory Bank/Rules/infra/secretos |
| AC-06 | PASS | Fixture ficticio y motivo REDACTED; revisión sin credenciales/PHI reales |
| AC-07 | PASS | Tests Node, fixture en VM sin red, 32 enlaces y diff check: exit 0 |
| AC-08 | PASS | Matriz de siete criterios, demo de seis minutos y descripción de PR preparados |
| AC-09 | PASS | Tres documentos nuevos y sección de preparación/clarificación en CACHING_REPORT; sin código |
| AC-10 | PASS | Cifras y conclusiones enlazadas a resultados ya medidos; no se inventan ejecuciones |

Validación ejecutada en esta preparación: `node --experimental-default-type=module scripts/test_caching_frontend.mjs` PASS; harness `node --input-type=module` con node:vm sobre el bloque JS de CACHING_DEMO: PASS sintaxis/payload/fallback sin red; comprobador Python de enlaces locales y literales JWT/private-key: PASS (32 enlaces); `git diff --check`: PASS. Suite backend y builds no repetidos: no cambios de código, configuración ni dependencias; evidencia anterior conservada en el informe.

Riesgos: límites de medición y aprobación externa enumerados arriba. La PR está en borrador local y su destino debe decidirse antes de publicar; no hay publicación ni push en esta preparación. Recomendación: presentar el recorrido al evaluador y, cuando se autorice publicación, elegir la rama destino y publicar los commits/PR. Final status: **PASS** para preparación documental; no equivale a calificación o autorización de producción.
