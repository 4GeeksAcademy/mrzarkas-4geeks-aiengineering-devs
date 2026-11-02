# Lote propuesto — stock_direct_update_rejected

Estado DESIGN_READY, 2026-11-02. Implementación y pruebas NOT_RUN.

## Fuente y alcance
El stock real es SUM(delta); no existe operación set-stock. Schema.extra=forbid ya rechaza campos desconocidos, pero cualquier 422 no acredita una escritura directa. Este lote instrumenta únicamente el intento explícito del campo JSON superior `stock`, incluso null, rechazado con error extra_forbidden en dos rutas existentes:

- POST /inventory/items/{item_id}/clinics/{clinic_id}/configuration
- POST /inventory/movements

Sólo capturar si RequestValidationError contiene loc=(body,stock), type=extra_forbidden, el body es objeto y contiene stock. Nunca leer ni conservar su valor. La ruta y el campo, no texto de error ni payload enviado al sink, determinan el detector. Otros campos, stock anidado, JSON malformado y 422 ajenos no capturan. quantity/counted_quantity son entradas legítimas de movimientos y no se clasifican como stock directo. No añadir rutas de escritura ni cambiar esquema, respuesta/status o contrato público.

CRUD global de artículos sin clínica queda pendiente: no inferir jurisdicción desde rol, primer scope, query adicional o clave de entorno. Tampoco detectar SQL externo, rutas inexistentes (404/405) ni stock aliases no definidos. Cobertura parcial explícita.

## Cambios concretos pendientes de autorización
1. Nuevo app/inventory/direct_stock.py: detector cerrado de RequestValidationError y rutas exactas; extraer sólo UUID item_id/clinic_id y kind permitido para movimientos. Sin parseo adicional del body ni conservación de stock/errores.
2. app/inventory/access_audit.py: rama específica de RequestValidationError antes de relanzar la misma excepción; usar actor autenticado de request.state. Fallo ordinario de captura no altera error. Rama 403/auditoría duradera sin cambios. Validación fallida nunca entra en mutación de negocio.
3. Nuevo app/telemetry/inventory_direct_stock_producer.py: sesión independiente, validación de item/clínica/país activos, scopes y permiso config:write o movement:write/adjust:write según ruta/kind. País US/UK confirmado por referencias persistidas. Contexto inválido descarta sin fallback. UUID aleatorio por rechazo sólo en memoria; operationId HMAC inventory_operation, userId regional, channel=api; properties cerradas jurisdiction/environment/operationId/channel, sessionId/requestId null, contrato1.2.0 intacto.
4. app/telemetry/server.py admite tipo únicamente en sink interno; ingreso browser continúa rechazándolo. Reutilizar cuota16/preparación100ms y cola/cierre/disabled existentes, sin retries ni outbox.
5. Nuevo tests/test_telemetry_inventory_direct_stock.py y README bilingües backend/inventory; expediente de telemetría. Sin migraciones, tablas, dependencias, UI, Memory Bank/Rules, .env, despliegue o commits.

## Criterios de aceptación y validación
- Positivos US/UK en ambas rutas: mismo HTTP422 y contenido de respuesta que antes; un intento de captura por rechazo, sin doble inventory_validation_failed.
- stock ausente, anidado, campo extra diferente, quantity legítima, JSON inválido, rutas ajenas y CRUD global: cero eventos.
- Identidad ausente/expirada, rol incorrecto, scope ajeno, item/clínica/país inexistente/inactivo, UUID o kind inválidos: cero eventos, denegación original intacta.
- Payload mínimo, sin stock ni body/errors/tokens/identificadores originales; HMAC regional; rechazo del tipo por ingreso browser.
- Fallos de lookup, timeout, cuota, cierre, disabled y cancelación: ninguna mutación ni modificación de respuesta.
- PostgreSQL efímero sintético: comprobar stock/movimientos/configuración/auditoría intactos después de rechazos; regresión de lotes anteriores y suite general, git diff --check.

## Límites y aprobación
Nueva instrumentación de rechazo/contexto/identificadores requiere aprobación expresa conforme a AGENTS.md. Aprobaciones anteriores no cubren este detector. Revisión de Cumplimiento y Gobierno del Dato pendiente; autorización sintética no equivale a revisión de Claire ni a producción. Entrega de telemetría sigue best effort. No instrumentado hasta aprobación.


## Implementación autorizada — 2026-11-03

Aprobación expresa: «Sí, autorizo este lote para el prototipo sintético». Implementados detector direct_stock.py, rama RequestValidationError en InventoryRoute que relanza la excepción original, productor independiente y admisión interna. Sin cambios de esquemas/contratos, migraciones, UI, permisos o auditoría 403. El estado DESIGN_READY/NOT_RUN anterior es histórico.

Validación en backend/.venv Python3.12, APP_ENVIRONMENT=test, PostgreSQL16 efímero tmpfs loopback18491/inventory_validation_direct_stock:
- `.venv/bin/alembic upgrade head`: PASS fresh0001–0012, migraciones existentes sin modificación.
- `.venv/bin/pytest -q tests/test_telemetry_inventory_direct_stock.py tests/test_telemetry_inventory_thresholds.py tests/test_telemetry_inventory_flow.py tests/test_telemetry_inventory_view.py tests/test_telemetry_inventory_validation.py tests/test_telemetry_inventory.py tests/test_inventory.py tests/test_inventory_audit_policy.py tests/test_inventory_demo.py tests/test_telemetry_server.py tests/test_caching.py`: **241 passed**,3.05s.
- `.venv/bin/pytest -q -m 'not integration' tests`: **592 passed,32 deselected**,2.83s. Recuentos solapados.
- Test nuevo:36 unitarias y1 integración. US/UK ambas rutas, respuesta idéntica con productor activo/desactivado;4 eventos específicos, ninguno inventory_validation_failed; cero movimientos y umbrales sin cambios. Auth puede emitir su propio evento independiente.
- Resolver: negativos item/clínica/país/rol/scope/kind/DB; detector stock null/presente y negativos anidado/ausente/ruta/método/UUID/error; timeout/cancelación/lookup, cuota/closed/disabled; payload mínimo y browser403.
- Prueba adicional final del fichero nuevo: **37 passed**,0.85s; incluye fallo síncrono del hook con respuesta422 intacta y recuentos de InventoryAudit/InventoryAccessDenial del artículo intactos. No se ha realizado prueba UI ni revisión de Cumplimiento. La rama403 queda intacta y pasa su regresión existente.

Cobertura actual29 tipos parcialmente instrumentados y10 sin productor. Restan order_abandoned e inventory_reconciliation_failed en inventario y8 de otros dominios. CRUD global de artículos sin clínica y aliases de stock siguen pendientes. Sin commits ni despliegue compartido. La revisión de Cumplimiento del nuevo contexto/identificadores sigue pendiente.
