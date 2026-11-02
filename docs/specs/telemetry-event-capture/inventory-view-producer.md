# Siguiente lote — inventory_viewed

Fecha2026-11-02. Estado: DESIGN_READY, sin implementación ni pruebas nuevas.
Solicitud del desarrollador: continuar después de validaciones de inventario.

## Fuente y alcance propuestos

El contrato1.2.0 describe una consulta autorizada de existencias finalizada;
properties obligatorias: jurisdiction US/UK, environment y view con enum
items/stock/reorder/movements. No requiere identificadores de artículo ni operación.

| Consulta | view | Condición del primer lote |
|---|---|---|
| GET /inventory/items/{item_id}/stock | stock | Clínica explícita autorizada, lectura completada |
| GET /inventory/items/{item_id}/movements | movements | Clínica explícita autorizada, lectura completada |
| GET /inventory/stock?clinic_id=... | stock | Sólo variante filtrada por clínica |
| GET /inventory/reorder?clinic_id=... | reorder | Sólo variante filtrada por clínica |

Una consulta satisfactoria emite una vez, incluso resultado vacío autorizado,
no por fila. Lecturas sin clinic_id quedan pendientes: pueden cubrir varias
clínicas/países o devolver vacío y no tienen un único contexto clínico probado.
Catálogo global items no se atribuye a una clínica ficticia. No modificar consultas,
paginación ni permisos para generar telemetría; no afirmar cobertura universal.

## Diseño concreto pendiente de autorización

1. `inventory/router.py`: Request opcional en las cuatro rutas y marcador interno
   tras consulta/modelos satisfactorios, actor autenticado, clinic UUID y view
   cerrado; sin contenido, filtros libres, URL, cantidades ni IDs de artículos.
2. Nuevo `telemetry/inventory_view_completion.py`: middleware ASGI de finalización,
   siguiendo audit_completion.py. Emitir sólo después de enviar completamente una
   respuesta2xx. Fallo de SQL/modelo/serialización, respuesta401/403/404/409/422/500,
   desconexión/cancelación o send fallido no capturan. Limpiar descriptor incluso
   si no se emite. Errores opcionales no alteran cabeceras/body/status.
3. `app/main.py`: registrar ese middleware sin modificar los existentes.
4. Nuevo `telemetry/inventory_view_producer.py`: revalidar stock:read para stock/
   reorder o history:read para movements, usando políticas existentes. Resolver
   clínica/país activos y scope del actor en sesión independiente; país proviene
   de maestros y no de petición/JWT. Inactivo/desconocido/fallo no cae a null.
   Las lecturas de historia autorizadas sobre clínica inactiva conservan su
   respuesta, pero no emiten en este primer alcance.
5. Reutilizar servicio opcional y cuota16/100ms/cola20/10. Envelope userId HMAC
   regional existente, sessionId/requestId=null. Properties únicamente
   jurisdiction/environment/view. Clinic UUID sólo determina ámbito interno de
   cola mediante HMAC de clínica; no sale como campo nuevo ni aparece en logs.
6. `telemetry/server.py`: admitir inventory_viewed sólo en sink interno; browser
   sigue rechazándolo. Sin cambiar contrato1.2.0 ni autorizaciones.

Archivos: los cinco indicados, nuevo
`backend/tests/test_telemetry_inventory_view.py`, README bilingües de backend/
inventario y expediente telemetry-event-capture. No nuevos permisos, cambios de
auth/auditoría persistente, modelos/migraciones, .env/secretos, dependencias,
Memory Bank/Rules, infraestructura, commits ni despliegue.

## Criterios y validación prevista

- US/UK, stock/movements/reorder, consulta vacía filtrada: un evento tras final send.
- Mensajes HTTP fragmentados/cancelación/error en send, estado no2xx o ausencia
  de descriptor: cero captura; preservar byte a byte respuesta original.
- Permisos operator/manager/regional/auditor y scope clínico/jurisdiccional vigentes;
  inventoryAdmin y roles ajenos no adquieren lecturas; scope inválido no emite.
- Clínica/país inactivos/ausentes, country noUSUK, timeout/cuotas/closed/disabled
  descartan; errores no alteran respuesta ni auditoría de denegaciones existente.
- Sin contenido de filas/UUID operativos/texto libre; browser403 para evento.
- Integración HTTP PostgreSQL exclusivamente sintética aislada y regresiones de
  los dos lotes anteriores. Pruebas NOT_RUN hasta implementación autorizada.

La autorización anterior de validaciones no se registra como autorización de
este middleware/consulta nueva. AGENTS.md exige aprobación expresa del tratamiento
de contexto/identificadores. Revisión de Cumplimiento sigue pendiente; aprobación
del prototipo no se presenta como revisión de Claire ni cierre de entrega global.


## Implementación autorizada y evidencia — 2026-11-02

Aprobación expresa: «Sí, autorizo este lote para el prototipo sintético».
Estado técnico: **IMPLEMENTED_VALIDATED_SCOPED** para cuatro rutas con clínica
explícita; las secciones DESIGN_READY/NOT_RUN anteriores son históricas.
Marcadores, middleware de finalización y productor registrados en archivos previstos.
Contrato/permisos/contexto browser/auditoría persistente sin modificar.

Pruebas Python3.12 desde backend/.venv, APP_ENVIRONMENT=test, DATABASE_URL e
INVENTORY_TEST_DATABASE_URL exclusivamente contra PostgreSQL16 efímero tmpfs
en loopback18491, base inventory_validation_views, migraciones0001–0011:

- `.venv/bin/pytest -q tests/test_telemetry_inventory_view.py tests/test_telemetry_inventory_validation.py tests/test_telemetry_inventory.py tests/test_inventory.py tests/test_inventory_audit_policy.py tests/test_inventory_demo.py tests/test_telemetry_server.py tests/test_caching.py`: **147 passed**,2.03s, sin skips.
- `.venv/bin/pytest -q -m 'not integration' tests`: **503 passed,27 deselected**,2.48s.
- Recuentos solapados: no sumarlos como pruebas únicas.
- Integración HTTP:10 lecturas capturadas, stock/movements/reorder US/UK y vacíos
  autorizados; consultas globales/items y respuestas401/403 no añaden eventos.
- ASGI:16 combinaciones de marcador/status, fragmentos byte-preservados, emisión
  tras final send, eliminación de estado obsoleto; app/send failure, cancelación
  y respuesta incompleta no emiten; captura fallida conserva respuesta enviada.
- Contexto: cuatro roles de lectura aceptados con su alcance y11 casos negativos;
  payload reducido, cuotas/cierre, timeout/cancelación y rechazo browser.

Cobertura actual24 tipos con productor al menos parcial y15 sin productor, siete
de inventario y ocho de otros dominios. inventory_viewed no cubre todavía items
ni consultas sin clínica explícita. Captura efímera best effort; sin producción,
commit o reconstrucción de contenedores compartidos. Revisión de Cumplimiento
de contexto e identidad seudónima sigue pendiente; autorización sintética no
equivale a revisión de Claire ni cierre completo de entrega.
