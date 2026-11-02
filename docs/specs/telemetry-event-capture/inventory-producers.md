# TASK-TEL-030 — Reentrada de inventario

Fecha: 2026-11-02. Rama inspeccionada: `feature/telemetryEventCapture`.
Estado: **REOPENED_SOURCE_AVAILABLE**; diseño del primer lote preparado para revisión.
El desarrollador solicitó continuar en el orden propuesto: fuentes, contexto/permisos,
movimientos confirmados, validaciones/interfaz y reglas adicionales. Esta instrucción
no se registra como aprobación de cambios concretos de seguridad todavía no revisados.
No hay productores de inventario implementados ni pruebas nuevas de captura ejecutadas.

## Fuentes verificadas y alcance

`backend/app/inventory/{router,service,models,schemas,policies}.py` implementa
movimientos `in`, `out`, `adjust` y compensaciones `correction`, stock derivado,
consultas autorizadas y validaciones de dominio. La afirmación histórica de que
no existía inventario queda superada para esta tarea. No se cambia el aplazamiento
histórico aprobado ni se considera satisfecha la cobertura integral TEL-FR-018.

| Evento | Fuente actual | Disposición siguiente |
|---|---|---|
| inbound_order_completed | POST /inventory/movements, kind=in | Primer lote, sólo tras commit |
| outbound_order_completed | POST /inventory/movements, kind=out | Primer lote, sólo tras commit |
| inventory_adjustment_completed | POST /inventory/movements, kind=adjust | Primer lote, conteo confirmado incluso delta=0 |
| inventory_validation_failed | Esquemas y validaciones de service.py | Lote posterior: códigos y fronteras explícitos |
| inventory_viewed | Lecturas autorizadas de stock | Lote posterior: disparador y contexto clínico |
| product_selected | Selección de producto en UI | Lote posterior: admisión browser y seudónimo de recurso |
| order_started | Formularios de entrada/salida | Lote posterior: inicio lógico y flowId |
| order_abandoned | No hay política de abandono | Definir cierre/inactividad y correlación antes de emitir |
| inventory_threshold_activated | Stock/reorden calculados | Falta ciclo de episodios y deduplicación |
| inventory_threshold_cleared | Stock/reorden calculados | Falta cierre del mismo episodio |
| stock_direct_update_rejected | extra=forbid no acredita detector específico | Definir detector explícito; no usar cualquier 422 |
| inventory_reconciliation_failed | No hay chequeo de reconciliación | Implementación independiente pendiente |

Los tres motores y cinco agregadores de otros dominios siguen sin fuente.
Las compensaciones no se reinterpretan como ajustes físicos en este primer lote.
El seed/demo, llamadas directas a service.py y operaciones fuera del endpoint
no se instrumentan en este alcance.

## Revisión de contexto y permisos

Los roles de inventario están reconocidos por autenticación, pero no reciben
`referenceData:read` en `app/auth/roles.py`. El resolver clínico común de telemetría
exige esa capacidad. El proveedor Next además omite sesiones de inventario.
Conectar el productor existente sin otra resolución descartaría estos hechos.

Propuesta del primer lote: resolver el movimiento persistido en una sesión
independiente, con el actor autenticado y su identificador de movimiento. Verificar
actor_id, result=accepted, kind permitido, clínica y país histórico del movimiento;
revalidar permisos `movement:write` o `adjust:write` y alcance usando las políticas
existentes de inventario. La clínica y jurisdicción deben estar activas y el país
histórico debe coincidir con la clasificación clínica actual; incoherencia,
desactivación, cambio de país o fallo de consulta descartan sin fallback a null.

No conceder capacidades de Management/incidencias a roles de inventario. No cambiar
`auth/roles.py`, `auth/dependencies.py`, `inventory/policies.py`, contexto público,
emisión de JWT ni admisión browser en este lote. Un operador sólo emite entradas y
salidas propias dentro de sus clínicas; un manager también emite conteos propios.
Admin, regional y auditor no obtienen permisos de movimiento por telemetría.

## Diseño concreto del primer lote, pendiente de aprobación

1. En `inventory/router.py`, obtener el movimiento dentro de `session.begin()`;
   salir correctamente del bloque de transacción antes de invocar un hook opcional.
   Retornar el mismo modelo/respuesta. Un rollback o commit fallido no invoca el hook.
2. Nuevo `telemetry/inventory_producer.py`: preparación asíncrona con la resolución
   anterior y el servicio opcional compartido, máximo 16 preparaciones y 100 ms.
   El hook sólo recibe actor y movement UUID internos; nunca cuerpo, razones,
   cantidades, nombres, tokens, snapshots ni datos de pacientes.
3. Mantener contrato 1.2.0. Para in/out, properties exactamente jurisdiction,
   environment, operationId, movementId, itemId; para adjust, jurisdiction,
   environment, operationId, movementId. Envelope sessionId/requestId=null.
4. Proponer una operación lógica por movimiento confirmado: operationId y
   movementId derivan del mismo UUID persistido con propósitos HMAC distintos.
   Esto no acredita idempotencia HTTP ni correlación con flowId de la UI.
   itemId usa el UUID del artículo. Todos son `ps_` + SHA256 HMAC regional,
   con subclaves por propósito `inventory_operation`, `inventory_movement`,
   `inventory_item`, separadas de incident/audit/user/clinic; reutilizar la clave
   regional de recurso validada sin nuevas claves ni cambios de .env.
5. Ampliar únicamente la allowlist interna `SERVER_EVENTS` en `telemetry/server.py`
   con estos tres tipos. Reutilizar cola 20/10, límites y diagnóstico existentes.
   El navegador continúa sin poder afirmar estos hechos.
6. Telemetría deshabilitada, configuración inválida, saturación, timeout, excepción
   o cierre no alteran la respuesta ni la evidencia append-only de inventario.
   No introducir reintentos, almacenamiento, migraciones ni colectores externos.

Archivos propuestos: `backend/app/inventory/router.py`, nuevo
`backend/app/telemetry/inventory_producer.py`, `backend/app/telemetry/server.py`,
nuevo `backend/tests/test_telemetry_inventory.py`, README bilingües de backend e
inventario y este expediente. Sin dependencias, contratos públicos nuevos,
Memory Bank/Rules, infraestructura, despliegue o commits.

El nuevo tratamiento de identificadores seudónimos y el resolver de contexto
requieren aprobación expresa del diseño concreto y revisión de Cumplimiento y
Gobierno del Dato conforme a AGENTS.md. La aprobación simulada de inventario
HC-INV-APPROVAL-2026-11-02 no se extiende automáticamente a telemetría.
No hay evidencia de revisión de Claire de este incremento al preparar este diseño.

## Criterios de aceptación y validación prevista

- In/out/adjust US y UK generan el tipo y properties correctos después del commit;
  país procede de la fuente persistida validada, no de un campo del navegador.
- Commit fallido/rollback, movimiento ausente, actor distinto, kind correction,
  result inválido, país incoherente, clínica/país inactivos y scopes incorrectos
  no generan un evento. Denegaciones y errores mantienen su comportamiento actual.
- HMAC estable por versión/país/propósito, separación entre propósitos y países;
  ningún UUID operativo, razón, token, cantidad o texto libre sale en el evento.
- Un hook que falla no altera status/body/commit; límites, deshabilitación,
  timeout, saturación y cancelación conservan las garantías existentes.
- Browser rechaza estos tres hechos incluso cuando validan contra el contrato.
- Integración PostgreSQL en una base exclusivamente sintética y aislada comprueba
  lectura posterior al commit, persistencia del movimiento y regresiones de
  autorización/auditoría; no usar la base compartida para pruebas destructivas.
- Suites enfocadas de productor/cola/contrato y regresiones inventario/telemetría;
  resultados se registrarán tras ejecución, sin reutilizar recuentos históricos
  como evidencia de este incremento. Revisión validate-delivery antes de entrega.

Revisión documental realizada: fuentes y campos contrastados con código,
contrato y políticas; fuentes pendientes separadas de productores implementados.
Pruebas de implementación: **NOT_RUN**, todavía no existe el incremento.


## Implementación y evidencia — 2026-11-02

El desarrollador autorizó expresamente «Sí, autorizo este lote para el prototipo
sintético». Implementado el diseño anterior en router.py, inventory_producer.py
y server.py; sin modificación de permisos, contratos, claves o contexto browser.
Estado técnico del lote: **IMPLEMENTED_VALIDATED_SCOPED**. Las secciones iniciales
registran el diseño antes de la autorización; no describen el estado final.
TASK-TEL-030 sigue PARTIAL: tres tipos con productor nuevo, nueve tipos restantes
de inventario pendientes; catálogo39 con22 tipos cubiertos al menos parcialmente
y17 todavía sin productor. No cierre integral TEL-FR-018.

Pruebas ejecutadas con Python3.12 en backend/.venv:

- `pytest -q -m 'not integration' tests`: **426 passed,25 deselected**,2.23s.
- `pytest -q tests/test_telemetry_inventory.py tests/test_inventory.py tests/test_inventory_audit_policy.py tests/test_inventory_demo.py tests/test_telemetry_server.py tests/test_caching.py`: **68 passed**,1.41s, sin skips.
- PostgreSQL16 efímero en tmpfs, base inventory_validation_telemetry_v2 en loopback18491; DATABASE_URL e INVENTORY_TEST_DATABASE_URL apuntaron exclusivamente a esa base. Alembic0001–0011 aplicado correctamente. No usar credenciales sintéticas de prueba como configuración operativa.
- Prueba nueva de integración observa seis movimientos confirmados in/out/adjust
  US/UK desde sesiones independientes y seis eventos válidos; salida rechazada
  por stock insuficiente no captura. Las suites existentes verifican permisos,
  denegaciones duraderas, histórico, compensaciones y demo.
- Pruebas nuevas: actor/rol/alcance, clínica/país inactivos o incoherentes, movimiento
  ausente/correction/denegado, timeout/cancelación, separación HMAC país/propósito/
  versión, rollback/commit fallido y fallo de hook; browser rechaza los tres hechos.
- Recuentos solapados: no sumar426 y68 como pruebas distintas.

Incidencias resueltas de validación: regresión inicial tomó DATABASE_URL local
con host postgres; se repitió contra PostgreSQL efímero. La primera integración
creó claves US/UK con UUID aleatorios e interfería con el seed canónico de demo;
se corrigió el fixture para reutilizar países canónicos y se repitió en base vacía.
Ninguna incidencia implicó cambios en la base compartida o en código de dominio.

La revisión de Cumplimiento/Gobierno del Dato de este tratamiento sigue pendiente;
la autorización del prototipo no se presenta como revisión de Claire ni autorización
de datos reales. No reconstrucción del entorno compartido, commit/push ni producción.
