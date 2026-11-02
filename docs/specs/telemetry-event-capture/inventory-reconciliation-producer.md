# Lote propuesto — inventory_reconciliation_failed

2026-11-03. DESIGN_READY. Implementación/pruebas NOT_RUN.

## Fuente real y semántica
No existe conciliador ni saldo/proyección persistida independiente. service.stock calcula una proyección de consulta con SUM(delta), lotes, presentación y reorden. El lote añade un verificador real de esa proyección frente a reconstrucción independiente en Python desde deltas persistidos; no crea un segundo balance ni compara dos llamadas idénticas a SUM.

El contrato1.2.0 sólo permite check=stock_projection y properties jurisdiction/environment/checkId/check. Emitir únicamente tras una comprobación completa que encuentra cantidad proyectada distinta de la suma del historial comparable. Un error SQL, timeout, stock negativo de una operación rechazada, fila no comparable o límite de lectura no son reconciliación fallida: resultado inconclusive, sin evento.

## Alcance concreto pendiente de autorización
1. Nuevo inventory/reconciliation.py: conexión independiente, transacción PostgreSQL REPEATABLE READ READ ONLY (sin locks de escritura), deadline1s y statement_timeout local; permisos audit:read y stock:read existentes, clínica/item/país activos US/UK y scope de inventoryAuditor. Consultar service.stock una vez y leer columnas delta/lot_id/jurisdiction_id/key del mismo item/clínica, máximo10001 filas (cap10000), sin motivos ni actores del historial. Mismo snapshot para todas las lecturas y config/lotes: movimientos concurrentes no crean diferencias temporales.
2. Suma Python del ámbito correcto: lot_id especificado sólo lote; sin lot_id agrega todos. Lotes, ajustes, compensaciones, ceros y posición sin movimientos siguen fórmulas existentes. Si cualquier fila clínica que entra en comparación no tiene país histórico conocido coincidente con la clínica/país del snapshot, devolver inconclusive; no comparar subconjuntos con la proyección completa ni reinterpretar legado como país actual. Proyección negativa no es suficiente: el trigger requiere desigualdad con suma comparable. Comparación exclusivamente quantity, no ampliar check a integridad histórica, auditoría o packs/reorder.
3. Nueva ruta POST /inventory/items/{item_id}/clinics/{clinic_id}/reconciliation, query lot_id UUID opcional, sin body ni cantidades del cliente. Usa InventoryRoute/actor/session habituales para conservar auditoría de denegaciones; el verificador usa su propia sesión sólo lectura. Response cerrada result=matched/mismatched/inconclusive y telemetryAccepted bool. Sin cantidades, deltas ni identificadores históricos. Auth401/403, referencia404 y denegación-audit503 conservan controles; contexto no comparable/límite/timeout ->inconclusive, no evento. Sin escribir inventario ni reparar discrepancias.
4. Nuevo telemetry/inventory_reconciliation_producer.py: sólo mismatch de verificador completo con UUID check generado por servidor. Revalidar permiso/scope y item/clínica/país activo en sesión independiente antes de emitir; país debe coincidir con snapshot. checkId HMAC con propósito separado inventory_check; userId HMAC regional, sessionId/requestId null. Cola interna y cuota16/100ms/cierre existentes; fallo/disabled descarta sin afectar comprobación. Sin persistencia de resultado, outbox/retries ni dedup entre ejecuciones manuales distintas.
5. inventory/router.py y telemetry/server.py admiten nueva operación y evento sólo interno; /telemetry/events continúa rechazándolo. resource_id añade únicamente inventory_check. OpenAPI Next/tipos y censo de operaciones se sincronizan; proxy continúa basándose en contrato, sin UI nueva. README bilingües y expediente/tests. No worker automático, migraciones, tablas, nuevas dependencias, .env, Rules/Memory Bank, modificaciones de roles/permisos, commits o despliegue compartido.

## Criterios y validaciones
- US/UK matched reales para apertura/entrada/salida/conteo/compensación/múltiples lotes/cero; matched no emite.
- Discrepancia real detectada por checker independiente; prueba positiva con proyección alterada sólo mediante seam de test sintético (sin escribir saldo ficticio), un evento mínimo con HMAC/región correctos. Fuente positiva no habilita fallo artificial en runtime.
- Snapshot consistente bajo movimiento concurrente, incluyendo cambios de config/lote; sin falso mismatch por distintas transacciones.
- Límite10000/10001, timeout/error de DB, historial legado/country incoherente ->inconclusive y cero eventos; no resultados parciales presentados como matched.
- Sin identidad/rol/scope, clínica/item/país/lote inexistente/inactivo ->rechazo original o descarte contextual del productor; auditoría403 durable conservada. Payload cerrado y browser403.
- Zero writes del verificador: transacción READ ONLY comprobada y recuentos stock/movimientos/auditoría/episodios/flow intactos; sólo auditoría de denegaciones esperada ante403.
- PostgreSQL sintético temporal, regresión de productores/inventario y general; tipos/contrato/forwarding. No E2E UI nueva porque no se añade interfaz; smoke HTTP real de ruta.

## Riesgos y límites
Revisión de Claire del tratamiento/contexto/identidad pendiente. La ruta nueva y la conexión/aislamiento requieren aprobación expresa conforme AGENTS.md; las anteriores no cubren este verificador. Este contraste comprueba implementación de la proyección, no acredita exactitud de inventario físico ni detecta alteraciones coherentes en ambos lados del historial. Los historiales>10000 y país legado quedan sin diagnóstico de discrepancia en este lote. Sin reparaciones ni fuente de EHR/facturación/pacientes, datos sólo sintéticos. Captura best effort y sin cierre global de telemetría.


## Implementación autorizada y evidencia — 2026-11-03

Aprobación «Sí, autorizo este lote para el prototipo sintético». Implementados reconciliation.py, nuevo productor, ruta/esquema/censo48operaciones, allowlist interna y HMAC inventory_check; OpenAPI Next/tipos/proxy sincronizados. DESIGN_READY/NOT_RUN anteriores históricos. No nueva UI, workers, tablas, migraciones, dependencias, .env, Rules/Memory Bank ni despliegue/commit.

### Pruebas ejecutadas
Python3.12/.venv, APP_ENVIRONMENT=test; PostgreSQL16 tmpfs loopback18491/inventory_validation_reconciliation, ambas URLs de tests allí. Migraciones existentes fresh0001–0013 PASS.

- `.venv/bin/pytest -q tests/test_telemetry_inventory_reconciliation.py tests/test_telemetry_inventory_abandonment.py tests/test_telemetry_inventory_direct_stock.py tests/test_telemetry_inventory_thresholds.py tests/test_telemetry_inventory_flow.py tests/test_telemetry_inventory_view.py tests/test_telemetry_inventory_validation.py tests/test_telemetry_inventory.py tests/test_inventory.py tests/test_inventory_audit_policy.py tests/test_inventory_demo.py tests/test_telemetry_server.py tests/test_caching.py tests/test_auth.py`: **297 passed**,5.00s.
- `.venv/bin/pytest -q -m 'not integration' tests`: **627 passed,36 deselected**,3.85s; solapados.
- Fichero nuevo tras ampliar aserciones de aislamiento: **22 passed**,1.94s (20 unitarios/2 integraciones). US/UK lotes/entradas/salidas/conteo/corrección; matched sin evento, seam test que altera sólo proyección produce1 evento mínimo con HMAC/región.
- WRITE SQL rechazado en checker: inconclusive, pack_size=1 y recuentos movimientos/auditoría intactos. SHOW transaction_isolation=repeatable read y transaction_read_only=on. Escritura concurrente después de lectura proyectada no produce mismatch: suma usa mismo snapshot.
- Límite controlado, legado/país incoherente, cero/lote y timeout; negativos producer rol/scope/item/clínica/país; disabled/cuota/closed/lookup. Browser403, auth401, permiso403 auditado, body rechazado422.
- Node24 Alpine, dependencias existentes: Vitest **66 passed**,2.92s, TypeScript noEmit PASS, openapi-typescript7.13.0 genera nuevo contrato. Prueba adicional proxy: **13 passed**,1.08s, sólo POST admitido; no nuevo E2E/build porque no hay UI ni cambio de componentes, contrato/tipos verificados.
- Fallo transitorio de integración: lectura de stream vacío impedía record_denial, devolviendo503 en vez de403; cache vacío preservado antes del checker y pruebas repetidas PASS.
- HTTP smoke real por ASGITransport contra DB efímera, no servicio compartido. No repetir migración rollback: este lote no añade ni modifica migraciones. No comprobación explícita de recuentos de episodios/flow: módulo sólo consulta proyección y deltas con transacción READ ONLY.

Cobertura31 tipos parcialmente instrumentados y8 sin productor, todos de otros dominios. Los12 tipos de inventario tienen alguna instrumentación, no cobertura completa de sus requisitos. Conciliación compara proyección de consulta y ledger, no dos saldos persistidos ni stock físico; historial>10000/legado sigue inconclusive. TELEMETRY best effort, sin resultados persistidos, reparaciones o revisión externa de Claire.
