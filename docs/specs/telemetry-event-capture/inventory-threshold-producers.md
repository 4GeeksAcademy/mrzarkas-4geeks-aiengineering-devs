# Siguiente lote — episodios de reorden

Fecha2026-11-02. Estado DESIGN_READY; sin implementación ni pruebas nuevas.
Eventos: inventory_threshold_activated e inventory_threshold_cleared.
Reentrada después de product_selected/order_started, por solicitud «continua».

## Semántica contractual

El stock de la posición es la suma de todos los movimientos de artículo/clínica,
incluidos lotes y compensaciones, en unidades base. El umbral es reorder_point.
La comparación es estricta: quantity < reorder_point significa bajo umbral;
igualdad significa despejado. No contar cada lote como episodio separado.

- Activar sólo si un movimiento confirmado cambia stock de >= a < umbral.
- Cerrar sólo si cambia de < a >= el mismo umbral comparable y hay un episodio
  conocido abierto; reutilizar su episodeId. Una caída posterior abre otro UUID.
- Movimientos dentro del mismo lado, ajustes delta=0 y consultas no crean eventos.
- Observar in/out/adjust/correction HTTP, después de commit, con permisos originales.
  No reinterpretar correction como inventory_adjustment_completed.
- Configuración nueva/modificada no emite estos eventos: el contrato cleared
  especifica cruce tras movimiento. Si cambia el valor del umbral, el episodio
  anterior deja de ser comparable y se descarta su seguimiento al siguiente
  movimiento, sin inventar cleared. Se evalúa el cruce real bajo el nuevo umbral.
- Posiciones preexistentes bajo umbral no reciben activaciones retroactivas.
  En la primera operación se usa stock previo real calculado desde movimientos.
  Si no hay episodio conocido, una recuperación no inventa un cierre pareado.

## Seguimiento propuesto y aislamiento de fallos

Para preservar identidad entre procesos/reinicios se proponen dos tablas nuevas,
sin cambiar modelos/migraciones existentes ni reescribir datos sintéticos actuales:

1. InventoryThresholdState: clave item_id/clinic_id, umbral comparable y episode_id
   abierto nullable. Seguimiento sólo de estado conocido, no stock alternativo.
2. InventoryThresholdTransition: UUID, episode_id, movement_id, tipo activated/
   cleared y umbral/country históricos. Restricción única por movimiento y
   referencias a movimientos/artículos/clínicas; transiciones append-only.
   Esta evidencia interna no reemplaza la auditoría existente, no guarda razones,
   snapshots, tokens ni datos de pacientes. Sin endpoint público para estas tablas.

Nueva migración0012, exclusivamente creación de tablas/constraints/triggers e
índices; downgrade sólo elimina esas tablas en una base de prueba desechable.
No backfill de episodios ni revisión de migraciones0010/0011.

El observador se ejecuta dentro de un savepoint después de crear/flush del movimiento
pero antes del commit exterior. Reutiliza los locks clínicos/artículo ya adquiridos
por el dominio y bloquea su fila de seguimiento para serializar cada posición.
Obtiene stock posterior agregado y calcula stock previo restando delta del movimiento;
decide el cruce y actualiza estado/evidencia juntos. Un fallo ordinario del observador
revierte sólo el savepoint y omite captura; el movimiento conserva su transacción.
Un fallo de conexión/commit de la base de negocio sigue siendo fallo de negocio;
no prometer éxito cuando PostgreSQL no puede confirmar el movimiento.

Una brecha del observador puede perder una transición. En la operación siguiente
se revalida coherencia del episodio con stock previo y umbral; estado obsoleto no
inventa cierres ni bloquea movimientos. Seguimiento durable no garantiza entrega
durable del evento: caída después de commit/antes del hook o pérdida de cola se
declaran best effort. No outbox/replay/retries en este lote.

## Implementación concreta pendiente de autorización

- Nuevos inventory/threshold_models.py y inventory/thresholds.py; importar metadata
  en app/db/models/__init__.py o el punto real de registro equivalente tras revisión.
  Nueva alembic/versions/0012_inventory_thresholds.py.
- inventory/router.py: observador en movimientos y correction dentro de transacción;
  hook opcional con UUID de transición únicamente después de commit exterior.
  Retornos/modelos/status/permisos/auditoría y stock derivados se conservan.
- Nuevo telemetry/inventory_threshold_producer.py: consultar transición persistida
  en sesión independiente, validar movimiento aceptado/actor/permiso/alcance y
  país histórico coincidente con clínica/país activos. Fallo de contexto descarta
  sin fallback general. Reutilizar servicio/cuota16/100ms/cola20/10/cierre.
- Ampliar resource_id con propósitos inventory_episode e inventory_scope, separados
  de inventory_item/operation/flow. itemId y scopeId (clínica) HMAC regional;
  episodeId derivado del UUID persistido; no UUID/cantidades/umbrales en eventos.
  Ambos eventos usan exactamente jurisdiction/environment/itemId/scopeId/episodeId,
  contrato1.2.0; sessionId/requestId=null. Sin nuevas claves.
- telemetry/server.py: admitir los dos tipos sólo por sink interno; mantener rechazo
  browser, sin modificar nueva ruta UI-flow ni sus credenciales.
- Pruebas nuevas test_telemetry_inventory_thresholds.py, ajustes necesarios de
  metadata/migraciones de pruebas, README bilingües y expediente de telemetría.
  No UI, contratos públicos, dependencias, .env, infraestructura, auth policies,
  Memory Bank/Rules, commit/push o actualización de contenedores compartidos.

## Criterios y pruebas previstas

- US/UK, igualdad, activación/cierre con mismo UUID y nuevo episodio en nueva caída;
  entradas/salidas/conteos/compensaciones y suma entre lotes.
- Consulta repetida, delta=0, movimientos sin cruce y posición legacy no inventan
  eventos. Cambio de umbral invalida comparabilidad sin cleared ficticio.
- Concurrencia serializada por posición; unique movement impide transición duplicada.
  Reinicio conserva episodio; no se afirma deduplicación durable de la entrega.
- Savepoint fallido conserva movimiento/stock/auditoría; rollback/commit exterior
  fallido no captura ni deja transición persistida.
- Permisos/scope, país histórico/clínica inactiva/incoherente, timeout/cuotas/disabled
  y cancelación omiten captura; no cambian denegaciones ni respuestas existentes.
- Payload cerrado/minimizado, HMAC separado y rechazo browser.
- Alembic fresh/upgrade/downgrade exclusivamente PostgreSQL sintético desechable;
  integración real de transacciones/concurrencia y regresión de lotes anteriores.
  Tests NOT_RUN hasta implementar. validate-delivery del alcance concreto.

Pendientes explícitos: revisión de Cumplimiento del almacenamiento/contexto/identidad,
retención/disposición de la nueva evidencia, correlación con claves después de
rotación y fuentes por cambios de configuración. No nueva garantía de retención
ni autorización de datos reales. La aprobación de prototipo no equivale a revisión
de Claire ni cierre de entrega/producción.


## Implementación autorizada y evidencia — 2026-11-02

Aprobación expresa del desarrollador: «Sí, autorizo este lote para el prototipo
sintético». Estado **IMPLEMENTED_VALIDATED_SCOPED**; el diseño y NOT_RUN de arriba
corresponden a la preparación previa. Implementados dos modelos nuevos, observer
con savepoint, registro metadata, migración0012, hooks post-commit movimiento/
correction y productor con HMAC inventory_episode/inventory_scope. No modificación
de migraciones anteriores, stock, políticas, contratos públicos o UI en este lote.

### Validaciones ejecutadas

Python3.12/backend/.venv, APP_ENVIRONMENT=test. DATABASE_URL e
INVENTORY_TEST_DATABASE_URL exclusivamente contra PostgreSQL16 efímero tmpfs,
loopback18491, base inventory_validation_thresholds.

- Alembic fresh0001–0012: **PASS**.
- `.venv/bin/pytest -q tests/test_telemetry_inventory_thresholds.py tests/test_telemetry_inventory_flow.py tests/test_telemetry_inventory_view.py tests/test_telemetry_inventory_validation.py tests/test_telemetry_inventory.py tests/test_inventory.py tests/test_inventory_audit_policy.py tests/test_inventory_demo.py tests/test_telemetry_server.py tests/test_caching.py`: **204 passed**,2.71s, sin skips.
- `.venv/bin/pytest -q -m 'not integration' tests`: **556 passed,31 deselected**,2.66s. Recuentos solapados, no sumarlos.
- Roundtrip0012→0011→0012 en base desechable: **PASS**; mismos recuentos de
  inventory_item/movement/audit/access_denial; tablas nuevas vacías sin backfill.
- US/UK con dos lotes: cruce agregado, igualdad, compensaciones y episodio pareado,
  nueva caída/UUID, cambio de umbral sin cierre inventado; cuatro transiciones
  por caso y cuatro eventos. Trigger rechaza UPDATE de transición append-only.
- Dos salidas concurrentes6→5→4: exactamente una transición. Conteo delta0 no
  añade transición. Rollback exterior conserva stock4 y episodio previo.
- Error SQL SELECT1/0 en savepoint del observer: movimiento posterior persiste,
  stock correcto y sin nueva transición. No intervención en auditoría de negocio.
- Resolver:13 negativos de actor/permiso/scope/movimiento/país; hooks sólo tras
  commit en ambos endpoints; cancelación/timeout/lookup, cuotas/closed/disabled
  y rechazo browser. Payload reducido y episodio HMAC pareado.

Estado durable verificado desde sesiones independientes; no se hizo una prueba
de despliegue/reinicio del servicio compartido. No se repitieron pruebas UI: este
lote sólo afecta backend y nuevas tablas; evidencia frontend del lote previo
permanece histórica. Integraciones de otros dominios no seleccionadas.

Cobertura actual28 tipos al menos parcial y11 sin productor: tres de inventario
(stock_direct_update_rejected, order_abandoned, inventory_reconciliation_failed)
y ocho de otros dominios. Los tipos instrumentados conservan sus brechas.
Revisión Cumplimiento/retención de nueva evidencia y rotación de claves pendiente.
Sin actualización del entorno compartido, datos reales, commit/push o producción.
