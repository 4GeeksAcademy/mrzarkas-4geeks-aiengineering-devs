# Siguiente lote — inventory_validation_failed

Fecha2026-11-02. Estado: **DESIGN_READY**, sin implementación.
Solicitud: continuar añadiendo eventos, tras el lote de movimientos confirmados.
El tratamiento nuevo y los cambios concretos del dominio se presentan para
autorización del prototipo sintético; revisión de Cumplimiento aún pendiente.

## Fuente y disparadores propuestos

Primera cobertura limitada a validaciones de negocio en
`POST /inventory/movements`, después de permisos y validación del alcance clínico.
No capturar todo404/409/422 ni inferir reasonCode mediante comparación de textos.

| Rechazo existente | Código contractual | Status conservado |
|---|---|---|
| Falta configuración de reorden de artículo/clínica | reference |409|
| Lote requerido/inesperado, inexistente o de otro artículo | lot |422/404|
| Solicitud en packs para artículo sin presentación pack | unit |422|
| Salida que dejaría existencias negativas | insufficient_stock |409|

Los códigos quantity/scope/conflict permanecen sin productor en este lote.
Validación Pydantic, clínica/artículo ausentes, artículo inactivo, denegación403,
SQL/commit fallido y errores inesperados no se reinterpretan como estos hechos.
Sin instrumentación de lecturas, compensaciones, catálogo, seed o llamadas directas
al servicio. La clase tipada puede usarse en helpers compartidos sin que eso active
captura en sus otros llamadores.

## Implementación propuesta

1. Nuevo `backend/app/inventory/validation.py`: excepción tipada, subclase de
   HTTPException, con reasonCode de allowlist y mismos status/detail públicos.
2. `inventory/service.py`: sustituir únicamente los rechazos de la tabla por esa
   clase explícita. Sin modificar stock, transacciones, permisos ni auditoría.
3. `inventory/router.py`: en la ruta movement, capturar sólo esta excepción fuera
   del bloque session.begin(), cuando rollback ya ha terminado. El hook opcional
   recibe actor autenticado, clinic UUID interno, UUID aleatorio de la operación
   rechazada y código. Siempre relanzar la excepción original; fallo de rollback
   o cualquier otro error no emite. No leer ni enviar el cuerpo, texto del error,
   valores rechazados, cantidades, producto/lote ni razones libres.
4. Nuevo `telemetry/inventory_validation_producer.py`: revalidar permiso
   movement:write/adjust:write según kind validado, clínica y alcance desde políticas
   existentes, país activo autoritativo en sesión independiente. Actor/kind/clinica
   pasan desde payload ya validado y actor autenticado; el navegador no determina
   país ni identidad. Fallo de contexto descarta sin fallback a null.
5. Reutilizar el servicio opcional, cuota16/100ms, cola20/10 y subclave HMAC regional
   inventory_operation. operationId representa un intento rechazado, no un movimiento
   inexistente. Envelope sessionId/requestId=null. Properties exactamente
   jurisdiction/environment/operationId/reasonCode, conforme a contrato1.2.0.
6. `telemetry/server.py`: admitir inventory_validation_failed sólo en sink interno.
   Mantener rechazo browser, sin cambios del contexto público ni permisos.

Una validación observada puede emitir aunque la respuesta de error no llegue al
navegador: la fuente es el rechazo real tras rollback, no la finalización HTTP.
Entrega best effort, sin persistencia, dedup durable o garantía de captura.

Archivos: los seis indicados, nuevo
`backend/tests/test_telemetry_inventory_validation.py`, README bilingües backend/
inventario y expediente telemetry-event-capture. No .env/secretos, contratos públicos,
auth policies, modelos/migraciones, auditoría duradera, Memory Bank/Rules, dependencias,
infraestructura, commits ni despliegue.

## Criterios y pruebas previstas

- Positivos US/UK para los cuatro códigos, conservando status/detail existentes;
  evento sólo después de rollback, sin persistir movimiento rechazado.
- Negativos:403/401, errores de esquema, otras excepciones/commit, permisos o scopes
  incorrectos, clínica/país inactivos/ausentes, cuota/timeout/cancelación y disabled.
- Evento cerrado sin UUID operativos/texto/valores del request; UUID de operación
  seudonimizado por servidor y país. Browser sigue rechazándolo.
- Test hook fallido conserva excepción original y auditoría de denegaciones.
- Integración PostgreSQL sintética aislada y regresiones de dominio/telemetría.
- Pruebas **NOT_RUN**; la existencia de este diseño no incrementa cobertura.

La revisión de Cumplimiento de identificadores/contexto sigue sin evidencia;
autorizar la implementación sintética no se presenta como aprobación de Claire.


## Implementación autorizada y evidencia — 2026-11-02

Aprobación expresa del desarrollador: «Sí, autorizo este lote para el prototipo
sintético». Diseño implementado en los archivos propuestos; las secciones iniciales
DESIGN_READY/NOT_RUN corresponden a la preparación previa. Estado técnico:
**IMPLEMENTED_VALIDATED_SCOPED**, cobertura limitada a cuatro códigos y un endpoint.
No cierre completo de inventory_validation_failed ni TASK-TEL-030.

PostgreSQL16 tmpfs aislado, loopback18491, base inventory_validation_events.
DATABASE_URL e INVENTORY_TEST_DATABASE_URL se configuraron exclusivamente para
esa base. Migraciones0001–0011 aplicadas correctamente. No base compartida usada.

Desde backend, Python3.12/backend/.venv:

- `.venv/bin/pytest -q tests/test_telemetry_inventory_validation.py tests/test_telemetry_inventory.py tests/test_inventory.py tests/test_inventory_audit_policy.py tests/test_inventory_demo.py tests/test_telemetry_server.py tests/test_caching.py`: **99 passed**,1.75s, sin skips.
- `.venv/bin/pytest -q -m 'not integration' tests`: **456 passed,26 deselected**,2.32s.
- Recuentos solapados, no sumarlos como pruebas distintas.
- Integración HTTP US/UK:8 rechazos tipados,8 eventos de validación y0 movimientos
  rechazados persistidos; status/detail originales exactos. Quantity=0 genera422
  de esquema sin evento de validación. La cola también observa autenticación
  legítima; el recuento enfocado filtra por tipo, tras corregir la primera prueba
  que confundía el evento de autenticación con validaciones.
- Unitarios verifican códigos/contexto US/UK,12 contextos inválidos, orden tras
  rollback, fallo de rollback/hook, errores no tipados/403 sin captura, timeout,
  cancelación, cuotas/cierre/deshabilitación, minimizar payload y rechazo browser.

La cobertura total pasa a23 tipos al menos parcial y16 sin productor: ocho de
inventario y ocho de otros dominios. Quantity/scope/conflict y otras superficies
siguen pendientes dentro de este tipo. Contexto y HMAC siguen requiriendo revisión
de Cumplimiento; aprobación del prototipo no acredita revisión de Claire.
Sin commit, modificación de Memory Bank/Rules/.env/contratos, ni reconstrucción
de los contenedores compartidos.
