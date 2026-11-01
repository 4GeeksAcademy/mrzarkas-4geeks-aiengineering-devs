# Plan — Optimización de rendimiento: Caching

Estado: diseño futuro, pendiente de revisión. Sólo los tres documentos SDD están autorizados ahora en esta carpeta. Fuente de requisitos: [spec.md](./spec.md); tareas: [tasks.md](./tasks.md). Backend actual `backend/`, excepción documentada en README raíz. No reubicar API ni duplicar frontend.

## Secuencia y gates

P0 → P1 → P2 → P3; P4 y P5 pueden abordarse independientemente sólo tras sus gates, sin delegación implícita. P6 requiere cambios aprobados; P7 requiere resultados de P6. La rama feature/caching-optimisation ya existe: primera tarea verifica y reutiliza. Todos los comandos siguientes son futuros; ninguno se ha ejecutado como validación de rendimiento en esta fase.

## P0. Contexto, Git y baseline

- Dependencia: revisión del usuario.
- Requisitos: FR-CACHE-001/002. Tareas TASK-CACHE-001/002.
- Rutas: Repositorio y documentación.
- Enfoque: Contexto obligatorio, Rules y README; verificar rama existente y diff; congelar contratos y entorno sin arrancar Compose que ejecuta seeds.
- Alternativas, riesgos y autorización: No crear rama por rutina; reutilizar si coincide. Riesgo de cambios locales: detener parte dependiente sin sobrescribir.
- Validaciones y criterio de salida: Scope de ejecución aprobado y Git/contratos registrados.

## P1. Inventario y observabilidad

- Dependencia: fase precedente y gates aplicables; ver tareas 003/004.
- Requisitos: FR-CACHE-002; NFR-CACHE-001/002; SEC-CACHE-003. Tareas TASK-CACHE-003/004.
- Rutas: backend/app/main.py y routers; app.js; frontend/app/page.js.
- Enfoque: Inventario AST contrastado con OpenAPI en entorno aislado; instrumentar timing futuro con monotonic, métricas por método/ruta plantilla, nunca URL concreta o query.
- Alternativas, riesgos y autorización: Middleware puede tocar auditoría/config protegida: aprobar antes. Alternativa harness externo sin modificar request flow.
- Validaciones y criterio de salida: 28 operaciones y rutas relevantes, contadores sin datos sensibles y perfiles baseline guardados.

## P2. Datos y benchmarks controlados

- Dependencia: fase precedente y gates aplicables; ver tareas 005/006.
- Requisitos: NFR-CACHE-001/003. Tareas TASK-CACHE-005/006.
- Rutas: Seeds backend como referencia; scripts/README.md; docs/serialization-measurement.py.
- Enfoque: Diseñar seeder escalonado y harness de frío/caliente, concurrencia y muestras comparables según spec.
- Alternativas, riesgos y autorización: Aprobación de datos/almacenamiento y limpieza; alternativa fixtures transaccionales. Nunca suite contra DB compartida.
- Validaciones y criterio de salida: Idempotencia, conteos reales, aislamiento demostrado y baseline reproducible.

## P3. Priorización y aprobaciones

- Dependencia: fase precedente y gates aplicables; ver tareas 007/011.
- Requisitos: FR-CACHE-003–009; SEC-CACHE-001–005. Tareas TASK-CACHE-007/011.
- Rutas: Inventarios de spec; backend/app/auth/dependencies.py y policies.py.
- Enfoque: Ratificar L1/L2 nativos, resolver useMemo, clasificar C1/C2 y medir frecuencia; acordar TTL/umbral antes de implementar.
- Alternativas, riesgos y autorización: Si ejercicio exige React, B1/B2 impiden ejecución frontend. Si coste insuficiente, rechazar caché; alternativa C3/métricas sólo con nueva revisión.
- Validaciones y criterio de salida: Decisión escrita de evaluador/usuario y Claire según impacto; ningún gate implícito.

## P4. Lazy Loading y memoización

- Dependencia: fase precedente y gates aplicables; ver tareas 008/009/010.
- Requisitos: FR-CACHE-003/004/005; NFR-CACHE-002. Tareas TASK-CACHE-008/009/010.
- Rutas: uis/backoffice/operational-incidents/app.js; frontend sólo si scope React independiente aprobado.
- Enfoque: Separar renderDetail y renderMetrics en módulos propuestos (aún no existentes) junto a app.js; import() en dispatcher; conservar API/helper/session, sin exportar credencial global nueva. Cronología: medir antes de elegir memoización.
- Alternativas, riesgos y autorización: No ssr:false ni next/dynamic para HTML nativo. Si candidato React aparece, usar boundary cliente mínimo, Suspense/fallback y comparar SSR/chunks; no diferir hero ni anclas.
- Validaciones y criterio de salida: Dos chunks separados medidos, navegación/foco/errores probados; useMemo sólo sobre candidato React real y coste demostrado, o B2 permanece.

## P5. Cache-aside para dos lecturas

- Dependencia: fase precedente y gates aplicables; ver tareas 012–016/022.
- Requisitos: FR-CACHE-006–009; NFR-CACHE-004–006; SEC-CACHE-001–004. Tareas TASK-CACHE-012–016/022.
- Rutas: backend/app/catalogs/router.py; backend/app/management/router.py; tests/.
- Enfoque: Implementar utilitario TTL futuro junto a módulo catálogo sin dependencia nueva; autorización antes de lookup; leer generación DB y validar before publish. C1/C2 JSON inmutable; integración independiente en TASK-CACHE-013 y TASK-CACHE-022.
- Alternativas, riesgos y autorización: Aprobación almacenamiento y puntos de invalidación/auditoría; no caché de auth ni sesión ORM. Invalidation por version existente evita Redis; fecha de vigencia exige frontera futura.
- Validaciones y criterio de salida: Hit/miss, TTL/fronteras, tres mutaciones, rollback, race, límites y dos workers superados.

## P6. Seguridad, regresión y comparación

- Dependencia: fase precedente y gates aplicables; ver tareas 017/018/019.
- Requisitos: FR-CACHE-001; NFR-CACHE-001/002/007; SEC-CACHE-001–005. Tareas TASK-CACHE-017/018/019.
- Rutas: backend/tests/; frontend/README.md; backoffice README.
- Enfoque: Ejecutar matriz negativa y comparación A/B acordada; auth y generación SQL separadas de consultas eliminadas.
- Alternativas, riesgos y autorización: No declarar mejora con p95 fuera de variabilidad; alternativa revertir optimización autorizadamente y documentar sin borrar archivos por inferencia.
- Validaciones y criterio de salida: Contratos y seguridad equivalentes; resultado observado frente a umbral acordado; bloqueos reportados.

## P7. Informe y revisión final

- Dependencia: fase precedente y gates aplicables; ver tareas 020/021.
- Requisitos: FR-CACHE-010; NFR-CACHE-007. Tareas TASK-CACHE-020/021.
- Rutas: Propuesto docs/CACHING_REPORT.md; README locales si comportamiento cambia.
- Enfoque: Crear informe futuro con referencias reproducibles y revisión read-only validate-delivery; no commit automático.
- Alternativas, riesgos y autorización: README bilingües en ejecución autorizada; Memory Bank adicional excluido. Informe usa métricas reales, nunca fixtures/IDs sensibles.
- Validaciones y criterio de salida: Todos criterios trazados; PASS sólo si no hay gates/validaciones pendientes para ejecución.

## Matriz de decisiones técnicas

| Decisión | Ventaja | Coste/riesgo | Propuesta y condición |
| --- | --- | --- | --- |
| In-process | Sin dependencia, simple en prototipo | Copias por worker, frío al reiniciar, locks sólo locales | Preferido para experimento; consulta Catalog.version por hit y doble validación refill |
| Redis | Datos compartidos, herramientas TTL | Dependencia, red, operación, auth/retención/infra, failover | No presente; no introducir sin aprobación y beneficio demostrado; no necesario para ejercicio local |
| Sólo TTL | Implementación limitada | Hasta TTL de obsolescencia; no cubre cambios inmediatos | Rechazado como única frescura; C1 frontera temporal adicional |
| Version + TTL + invalidación | Commit visible por generación DB, TTL limita memoria | Consulta por hit y coordinación refill; seeders externos pueden no versionar | Verificar todos writers; fuera de protocolo bypass/reset aprobado |
| useMemo React | Evita recalcular un valor con dependencias iguales | No reduce por sí solo commits; mantenimiento/dependencias | B2: no componente cliente costoso existente |
| Refactor de estado/índices nativos | Evita sort/find repetidos sin cambiar framework | Invalidation de datos en memoria y pruebas UX | Alternativa medida; no equivale a useMemo para 4Geeks |
| React.memo | Evita renders con props estables | Ineficaz si props/callbacks cambian; ningún consumidor candidato | Sólo si profiling de una futura UI React justifica |
| import() nativo | Separa dos rutas existentes | Requests adicionales, overhead de módulos y helpers | L1/L2, gate B1; no migración a React |
| next/dynamic/React.lazy | Integración React/Suspense | No aplica a backoffice nativo; Server Component pequeño no aporta chunk cliente | Sólo candidato React real aprobado; nunca crear complejidad para cumplir conteo |

## Contratos y diseño de pruebas

Baseline OpenAPI debe fijar versión/commit y 28 operaciones, incluidos PUT de cobertura, HTTP 200/201 y errores actuales. Comparar JSON schemas sin retirar metadata ni redacción; comparar items/total, paging, sort, nullability y permisos mediante tests existentes. No cachear Headers/Response de contexto ni devolver objetos mutables compartidos.

Cache unit tests futuros: reloj inyectado, hit/miss, expiry, frontera inclusiva, invalidación tras create/update/activation, rollback, deep-copy/inmutabilidad, eviction, oversize, exceptions y cancelación. Integration: actores sintéticos distintos, warmup admin y luego 401/403, scope por área, generación después del commit en segundo worker; relectura version impide refill viejo. JWT sin jurisdicción: registrar limitación, no introducir claims sin autorización. No cachear referencias privadas como fallback automático.

Frontend: entrar inicialmente a cola, confirmar ausencia de L1/L2 en waterfall; navegar detalle/métricas/repetir/volver/desconectar mientras carga/import fail; fallback aria-busy y foco, sin listeners duplicados y sin respuesta de sesión anterior al reconectar. Chunks contienen código, nunca JWT ni datos. Comparar payload/tiempos en navegador real y revisar desktop/mobile/teclado. useMemo requiere datos inmutables de historial/locale/opciones como dependencias completas si se autoriza componente real; sort no muta arrays fuente. Invalidar identidad al desconectar; no almacenar cálculo privado global.

Comandos futuros verificados en README/scripts: `git status --short`, `git branch --list feature/caching-optimisation`, `git diff --check`; desde backend `uv run --no-sync pytest tests/test_status.py -q`; suite root `podman compose --profile test run --rm test` sólo con entorno sintético aislado aprobado (modifica datos); build `podman compose build frontend` o desde frontend `pnpm build` si dependencias presentes. `node --check uis/backoffice/operational-incidents/app.js` para sintaxis; script inline Management requiere extraer sólo a /tmp antes de comprobarlo. Ningún comando de startup/migraciones/seed corre por inferencia. No hay test/lint frontend configurado. Nuevos tests/harness y sus comandos se concretan al implementar sin introducir dependencias por rutina.

## Informe futuro

TASK-CACHE-020 propone `docs/CACHING_REPORT.md`, ubicación nueva a autorizar junto al alcance de ejecución. Contendrá entorno y método medidos; filas/distribución antes/después; tabla por caso p50/p95/SQL/bytes/hits/misses/llamadas; componentes/chunks y cálculo memoizado; TTL/clave/partición/invalidación por endpoint; decisión de frescura versus coste; lo excluido; fallos y riesgos; enlaces a scripts/perfiles/resultados reales. Si B1/B2/B3 siguen abiertos, explicarlo y no declarar reto completado. No actualizar Memory Bank ni Rules adicionalmente sin permiso específico; no ejecutar commit/push/PR/despliegue.
