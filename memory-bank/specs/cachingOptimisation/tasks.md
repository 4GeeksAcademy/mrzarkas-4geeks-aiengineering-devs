# Tareas — Optimización de rendimiento: Caching

Todas son futuras y comienzan `[ ] Pending`; no reflejan ejecución por haber redactado el diseño. Requisitos completos en [spec.md](./spec.md), fases y decisiones en [plan.md](./plan.md). Paths abreviados `app.js` corresponden a `uis/backoffice/operational-incidents/app.js`. `backend/` es la ubicación real. Módulos/harness/tests nuevos son propuestas explícitas, nombres se concretarán al ejecutar. Para requisitos abreviados con slash/rangos usar prefijo completo del primer ID. La fase actual termina tras validar estos tres archivos.

## TASK-CACHE-001 — Rama y autorización de ejecución

- Estado: [ ] Pending.
- Objetivo: Verificar/reutilizar feature/caching-optimisation, crear sólo si ausente y expresamente aprobado.
- SPEC: FR-CACHE-001.
- Evidencia/archivos: Git y documentos SDD.
- Dependencias TASK-CACHE: —.
- Instrucciones: Leer contexto y obtener revisión de este diseño; inspeccionar branch/status/staged/unstaged/untracked; conservar locales.
- Aceptación: Rama correcta sin sobrescritura; autorización alcance registrada.
- Pruebas/comandos o comprobaciones: git branch --list feature/caching-optimisation; git status --short.
- Riesgo y aprobación necesaria: Crear rama/commit nunca implícito; no ejecución ahora.

## TASK-CACHE-002 — Congelar baseline contractual

- Estado: [ ] Pending.
- Objetivo: Registrar contratos y entorno de referencia.
- SPEC: FR-CACHE-001; NFR-CACHE-007.
- Evidencia/archivos: backend/app/main.py y routers; backend/tests/.
- Dependencias TASK-CACHE: 001.
- Instrucciones: Comparar rutas estáticas con OpenAPI en harness aislado; conservar HTTP/orden/campos y metadata.
- Aceptación: 28 operaciones sin endpoint inventado; artifact versionado autorizado.
- Pruebas/comandos o comprobaciones: Comparación OpenAPI y tests de contracts existentes.
- Riesgo y aprobación necesaria: No arrancar Compose ni datos sin aislamiento aprobado.

## TASK-CACHE-003 — Inventario y timing backend

- Estado: [ ] Pending.
- Objetivo: Medir frecuencia y coste por plantilla de ruta.
- SPEC: FR-CACHE-002; NFR-CACHE-001; SEC-CACHE-003.
- Evidencia/archivos: backend/app/main.py; routers; docs/serialization-measurement.py.
- Dependencias TASK-CACHE: 002.
- Instrucciones: Preferir harness externo; middleware futuro sólo si necesario y aprobado; contadores SQL sin parámetros.
- Aceptación: p50/p95, llamadas/bytes/SQL separados; cardinalidad acotada y ausencia de query/PHI.
- Pruebas/comandos o comprobaciones: Revisión de logs sintéticos; benchmark con rutas dinámicas.
- Riesgo y aprobación necesaria: Auditoría/observabilidad protegida requiere aprobación si afectada.

## TASK-CACHE-004 — Profiling frontend

- Estado: [ ] Pending.
- Objetivo: Establecer costes de rutas/chunks/cálculos reales.
- SPEC: NFR-CACHE-002; FR-CACHE-002.
- Evidencia/archivos: frontend/app/page.js; app.js; management/index.html; audit/.
- Dependencias TASK-CACHE: 002.
- Instrucciones: Medir producción/estático, waterfall inicial y rutas, cronología sort/find; usar Profiler sólo en React cliente existente.
- Aceptación: Artefactos sin contenido sensible; coste y limitación React documentados.
- Pruebas/comandos o comprobaciones: Browser desktop/mobile fijo; performance marks; React DevTools si aplica.
- Riesgo y aprobación necesaria: No migrar framework; capturas sin tokens ni datos reales.

## TASK-CACHE-005 — Seeder sintético aislado

- Estado: [ ] Pending.
- Objetivo: Preparar escalado idempotente autorizado.
- SPEC: NFR-CACHE-003; SEC-CACHE-005.
- Evidencia/archivos: backend/app/reference_data/seed.py y catalogs/seed.py como referencias; scripts/README.md.
- Dependencias TASK-CACHE: 003.
- Instrucciones: Aprobar DB temporal y límites; crear generador futuro no reescribir seeds; namespace/manifiesto/relaciones válidas; dry-run.
- Aceptación: Conteos antes/después; segunda ejecución estable; rollback seguro probado.
- Pruebas/comandos o comprobaciones: Verificar conteos/FK/idempotencia en DB aislada.
- Riesgo y aprobación necesaria: Almacenamiento, datos y limpieza requieren autorización; no ejecutar ahora.

## TASK-CACHE-006 — Harness baseline backend

- Estado: [ ] Pending.
- Objetivo: Reproducir muestras comparables sin caché.
- SPEC: NFR-CACHE-001/003.
- Evidencia/archivos: Referencia docs/serialization-measurement.py; scripts/.
- Dependencias TASK-CACHE: 003/005.
- Instrucciones: Tres rondas 200 tras 20 warmup, concurrencia 1/10; fijar SQL/auth/generación y transporte; no inventar tráfico.
- Aceptación: Resultados y variabilidad por C1/C2, dataset/entorno/percentiles definidos.
- Pruebas/comandos o comprobaciones: Harness futuro ASGI y HTTP, contadores SQL.
- Riesgo y aprobación necesaria: Sin deps nuevas ni DB compartida; umbral se acuerda tras resultados.

## TASK-CACHE-007 — Resolver candidatos frontend

- Estado: [ ] Pending.
- Objetivo: Cerrar B1 y B2 con usuario/evaluador.
- SPEC: FR-CACHE-003/004/005.
- Evidencia/archivos: spec.md inventario; app.js; frontend/.
- Dependencias TASK-CACHE: 004.
- Instrucciones: Presentar dos rutas import() nativas y ausencia de cálculo React; acordar adaptación o scope React independiente.
- Aceptación: Decisión explícita; candidato React real antes de useMemo o bloqueo permanece.
- Pruebas/comandos o comprobaciones: Revisión de perfil y aceptación 4Geeks.
- Riesgo y aprobación necesaria: Migrar apps no autorizado; adaptación nativa no cumple useMemo literal.

## TASK-CACHE-008 — Lazy Loading de detalle L1

- Estado: [ ] Pending.
- Objetivo: Diferir renderDetail preservando comportamiento.
- SPEC: FR-CACHE-003; NFR-CACHE-002.
- Evidencia/archivos: app.js renderRoute/renderDetail; módulo futuro local.
- Dependencias TASK-CACHE: 007.
- Instrucciones: Extraer sólo detalle; import() en dispatcher, helpers/contexto mínimo; loading/error/retry; cancelar vista obsoleta.
- Aceptación: Chunk ausente en cola; navegación/editor/historial y permisos iguales.
- Pruebas/comandos o comprobaciones: Waterfall frío/caliente; node --check; browser teclado/import fail.
- Riesgo y aprobación necesaria: Requiere ejecución aprobada y B1 resuelto; no JSX nativo.

## TASK-CACHE-009 — Lazy Loading de métricas L2

- Estado: [ ] Pending.
- Objetivo: Diferir renderMetrics independientemente.
- SPEC: FR-CACHE-004; NFR-CACHE-002.
- Evidencia/archivos: app.js renderRoute/renderMetrics; módulo futuro local.
- Dependencias TASK-CACHE: 007/008.
- Instrucciones: Separar tarjetas/renderer; carga bajo demanda, fallback y reintento; no precargar en primera vista sin medir.
- Aceptación: Segundo chunk real ausente inicialmente; sesión/foco/permisos preservados.
- Pruebas/comandos o comprobaciones: Waterfall; navegación repetida/reconexión; node --check.
- Riesgo y aprobación necesaria: Mismo gate; overhead puede superar ahorro, medir y decidir.

## TASK-CACHE-010 — useMemo condicionado a evidencia

- Estado: [ ] Pending.
- Objetivo: Memoizar cálculo costoso en React real aprobado.
- SPEC: FR-CACHE-005; NFR-CACHE-002.
- Evidencia/archivos: Sin archivo React cliente candidato actual; cronología app.js alternativa.
- Dependencias TASK-CACHE: 007.
- Instrucciones: No ejecutar mientras B2; localizar componente real tras aprobación independiente, perfilar cálculo y dependencias completas estables; no mutar arrays.
- Aceptación: Resultado igual con inputs/cambios; duración comparada; sin prometer menos renders; bloqueo si no candidato.
- Pruebas/comandos o comprobaciones: React Profiler/calculation marks; cambio de todas dependencias.
- Riesgo y aprobación necesaria: Bloqueada por B2; índices/memo nativo no se etiquetan useMemo.

## TASK-CACHE-011 — Diseño y permisos de caché

- Estado: [ ] Pending.
- Objetivo: Cerrar C1/C2, TTL/partición/privacidad.
- SPEC: FR-CACHE-006/007/008/009; SEC-CACHE-001–005.
- Evidencia/archivos: backend/app/catalogs/router.py; management/router.py; auth/.
- Dependencias TASK-CACHE: 006.
- Instrucciones: Medir coste/frecuencia, clasificar fields/actors; ratificar 60/30 s, límites, generación y fronteras; documentar review Claire.
- Aceptación: Dos candidatos justificados o B3; aprobación almacenamiento/invalidation; permisos sin cachear.
- Pruebas/comandos o comprobaciones: Revisión de matriz de claves/datos/writers/consumers.
- Riesgo y aprobación necesaria: B3/B4; Redis, auth, audit, infra requieren autorización separada.

## TASK-CACHE-012 — Capa TTL acotada

- Estado: [ ] Pending.
- Objetivo: Implementar cache-aside reutilizable sin deps.
- SPEC: NFR-CACHE-004/005/006; SEC-CACHE-003.
- Evidencia/archivos: Módulo futuro junto a backend/app/catalogs/; tests futuros.
- Dependencias TASK-CACHE: 011.
- Instrucciones: JSON validado inmutable, reloj monotonic, eviction/bytes, single-flight por generación, finally/cancelación y bypass.
- Aceptación: Límites y fallos probados, no ORM/session/request global, sin lru_cache sin TTL.
- Pruebas/comandos o comprobaciones: Tests unitarios reloj/fallos/oversize/concurrencia.
- Riesgo y aprobación necesaria: Almacenamiento autorizado; nuevos módulos son propuesta, no existentes.

## TASK-CACHE-013 — Integración C1: catálogo activo

- Estado: [ ] Pending.
- Objetivo: Añadir lookup/fill al catálogo activo.
- SPEC: FR-CACHE-006/007; SEC-CACHE-001/002/004.
- Evidencia/archivos: get_catalog; tests futuros.
- Dependencias TASK-CACHE: 012.
- Instrucciones: Auth y validación antes de lookup; consultar generación DB; clave por partición/catalog/página; response_models íntegros.
- Aceptación: Hit/miss equivalentes en catálogo activo; errores no cacheados; auth ejecutada en hits.
- Pruebas/comandos o comprobaciones: Tests de API catálogo activo/nombre/roles.
- Riesgo y aprobación necesaria: Sólo catálogo activo y valores Management aprobados, sin fallback privado automático.

## TASK-CACHE-022 — Integración C2: valores Management

- Estado: [ ] Pending.
- Objetivo: Añadir cache-aside exclusivamente a list_catalog_values.
- SPEC: FR-CACHE-007; SEC-CACHE-001/002/004.
- Evidencia/archivos: backend/app/management/router.py: list_catalog_values; tests futuros.
- Dependencias TASK-CACHE: 012/013.
- Instrucciones: Autorizar y validar página antes del lookup; consultar Catalog.version; clave particionada por actor/rol/área/catalog_name/offset/limit/contrato; conservar CatalogValueListResponse completo.
- Aceptación: Hit/miss equivalentes, items/total/orden sin cambios, páginas aisladas, errores no almacenados, autorización siempre ejecutada.
- Pruebas/comandos o comprobaciones: Tests HTTP por catálogo/página/rol y count+consulta/generación; comparar SQL frío/caliente.
- Riesgo y aprobación necesaria: Metadata actor privada y almacenamiento requieren aprobación B4; coste/frecuencia B3; no retirar campos.

## TASK-CACHE-014 — Invalidación de escrituras

- Estado: [ ] Pending.
- Objetivo: Conservar frescura tras create/update/activation.
- SPEC: FR-CACHE-008; NFR-CACHE-005.
- Evidencia/archivos: management/router.py tres mutaciones; Catalog.version.
- Dependencias TASK-CACHE: 013/022.
- Instrucciones: Usar version existente; comprobar commit/rollback y recheck antes de publish; no tocar audit transaction.
- Aceptación: Ambos caches no sirven generación antigua tras commit; rollback mantiene anterior; race descartada.
- Pruebas/comandos o comprobaciones: Tests writer-reader concurrente y rollback.
- Riesgo y aprobación necesaria: Puntos de almacenamiento/auditoría protegidos; seeds externos bypass/reset explícito.

## TASK-CACHE-015 — TTL y vigencia temporal

- Estado: [ ] Pending.
- Objetivo: Cubrir vencimientos sin escritura.
- SPEC: FR-CACHE-009; NFR-CACHE-006.
- Evidencia/archivos: CatalogValue fechas; get_catalog; capa TTL.
- Dependencias TASK-CACHE: 013/022.
- Instrucciones: Calcular frontera de futuros effective_from/existing effective_to, inclusive semántica; límites de TTL y reloj UTC/monotonic.
- Aceptación: Pruebas antes/igual/después, catálogo inactivo y valores futuros/expirados; C2 30 s propuesto ratificado.
- Pruebas/comandos o comprobaciones: Tests reloj controlado sin sleep largo.
- Riesgo y aprobación necesaria: No convertir >= en > ni cambiar contratos; incertidumbre reloj = bypass.

## TASK-CACHE-016 — Concurrencia, workers y resiliencia

- Estado: [ ] Pending.
- Objetivo: Evitar fills antiguos y controlar fallos.
- SPEC: NFR-CACHE-004/005/006; FR-CACHE-008.
- Evidencia/archivos: Capa TTL; endpoints; tests futuros.
- Dependencias TASK-CACHE: 014/015.
- Instrucciones: Dos instancias de caché/worker contra DB aislada, commit intercalado, reinicio frío, timeout/exception/cancel y techo locks.
- Aceptación: Nuevo worker ve generación actual; fail-cache consulta DB; fail-DB conserva error; sin locks huérfanos.
- Pruebas/comandos o comprobaciones: Tests dos workers y stampede; resultados contados.
- Riesgo y aprobación necesaria: No introducir Redis ni configurar despliegue por inferencia.

## TASK-CACHE-017 — Seguridad y separación

- Estado: [ ] Pending.
- Objetivo: Probar autorización en hits y ausencia de exposición.
- SPEC: SEC-CACHE-001–005.
- Evidencia/archivos: auth/dependencies.py y policies.py como referencia; tests HTTP.
- Dependencias TASK-CACHE: 016.
- Instrucciones: Calentar válido y solicitar inválido/expirado/rol denegado; usuarios/áreas distintas; revisar digest/logs y no caché pública.
- Aceptación: Sin fuga; limitación JWT jurisdicción explícita; bypass si dimensión futura sin soporte.
- Pruebas/comandos o comprobaciones: Tests HTTP de matriz identidades; inspección headers/logs.
- Riesgo y aprobación necesaria: Cambiar auth/headers/contrato requiere aprobación; Claire si privacidad/audit/retención.

## TASK-CACHE-018 — Mediciones comparativas

- Estado: [ ] Pending.
- Objetivo: Evaluar beneficio real y variación.
- SPEC: NFR-CACHE-001/002; FR-CACHE-003–007.
- Evidencia/archivos: Harness/perfiles futuros; audit/ como referencia.
- Dependencias TASK-CACHE: 008/009/010/016.
- Instrucciones: Repetir protocolo baseline con mismos inputs; frío/caliente/TTL/invalidación; separar pendientes B2 sin saltarlo.
- Aceptación: Before/after p50/p95/SQL/bytes/hit ratio/llamadas y frontend; umbral acordado evaluado.
- Pruebas/comandos o comprobaciones: Harness futuro A/B tres rondas, browser mismo entorno.
- Riesgo y aprobación necesaria: Si B2 bloquea, parcial documentado; nunca declarar ejecución completa.

## TASK-CACHE-019 — Regresión contractual y UX

- Estado: [ ] Pending.
- Objetivo: Verificar ningún cambio observable no autorizado.
- SPEC: FR-CACHE-001; NFR-CACHE-007.
- Evidencia/archivos: backend/tests/; frontend/; backoffice README.
- Dependencias TASK-CACHE: 017/018.
- Instrucciones: Suite aislada existente y nuevos tests; comparación OpenAPI; builds/sintaxis; navegación y teclado, no seeds implícitos.
- Aceptación: 28 operaciones/HTTP/shape/orden/paging/redacción igual; builds y UX sin errores.
- Pruebas/comandos o comprobaciones: Suite Compose sólo DB aislada aprobada; pnpm build; node --check; git diff --check.
- Riesgo y aprobación necesaria: Suite modifica datos; sin frontend test/lint configurado.

## TASK-CACHE-020 — CACHING_REPORT.md futuro

- Estado: [ ] Pending.
- Objetivo: Redactar evidencia medida y exclusiones.
- SPEC: FR-CACHE-010; NFR-CACHE-001/002/007.
- Evidencia/archivos: Propuesto docs/CACHING_REPORT.md; README bilingües si aplica.
- Dependencias TASK-CACHE: 019.
- Instrucciones: Seguir índice de plan: método/dataset/SQL/latencia/frontend/TTL/claves/frescura/exclusiones/links; marcar pendientes.
- Aceptación: Cifras trazables; sin tokens/PHI; bloqueos no ocultados; no creado en fase SDD.
- Pruebas/comandos o comprobaciones: Revisión tablas contra artifacts y comandos.
- Riesgo y aprobación necesaria: Nuevo alcance documental/README debe autorizarse; Memory Bank adicional excluido.

## TASK-CACHE-021 — Validación de entrega

- Estado: [ ] Pending.
- Objetivo: Evaluar criterios uno a uno con validate-delivery.
- SPEC: Todos FR-CACHE/NFR-CACHE/SEC-CACHE.
- Evidencia/archivos: Diff total, tres documentos y futuras modificaciones autorizadas.
- Dependencias TASK-CACHE: 020.
- Instrucciones: Leer skill y matriz AC-01–10; revisar untracked, scope/autorizaciones, secret/PHI, test evidence; reportar en respuesta.
- Aceptación: PASS sólo si obligatorios cumplen; BLOCKED no terminado; no commit automático.
- Pruebas/comandos o comprobaciones: git status --short; git diff --check; revisión skill read-only.
- Riesgo y aprobación necesaria: No escribir informe adicional sin permiso, commits/push/PR/despliegue excluidos.

## Regla de cierre y evaluación

001–007 corresponden a P0–P3; 008–010 a P4; 011–016 y 022 a P3/P5; 017–019 a P6; 020–021 a P7. TASK-CACHE-010 sigue bloqueada por B2; 008/009 dependen de aceptación B1; 011–016 requieren B3/B4. Mantener Pending hasta ejecución verificada, nunca marcar completas por plantear alternativa. Las tareas 013 y 022 implementan C1 y C2 independientemente; ambas preceden a invalidación y pruebas TTL. No interpretar un plan como permiso para almacenamiento, datos, auth, audit, dependencias, infraestructura o contratos.
