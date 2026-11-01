# Lote4 revisable: api_request_completed para lecturas de incidencias

Estado: aprobado e implementado para validación sintética. Rama feature/telemetryEventCapture. Contrato1.1.0 existente, sin ampliar null ni publicar cabeceras nuevas.

## Alcance

GET /incidents/{incident_id}, /history, /assignment-history y /audit. Sólo solicitudes con actor autenticado y clínica obtenida de la incidencia encontrada después de los controles existentes. /audit conserva audit:read y su política vigente; las otras tres conservan incident:read y control de área. No instrumentar listado, métricas, mutaciones, Management, auth, health/status, catálogos ni /telemetry en este lote.

## Captura implementada

1. Middleware ASGI genera UUID requestId exclusivamente interno y mide duración mediante reloj monotónico desde entrada HTTP hasta envío satisfactorio del último fragmento del cuerpo. No confiar en IDs/cabeceras/URLs del cliente ni devolver cabecera nueva.
2. Cada ruta deja descriptor interno (actor, clinic UUID) después de consulta y controles satisfactorios. No guardar cuerpo, parámetros, texto, JWT ni URL en descriptor/evento. Si SQL falla antes del descriptor, no emitir.
3. Un único api_request_completed al completarse el cuerpo, incluido un4xx/5xx manejado si ya existe descriptor autorizado; no emitir si falta actor, clínica o una respuesta final enviada. Excepción sin respuesta final, cancelación o desconexión descartan. No inventar éxito ni modificar mensajes/status.
4. Properties: jurisdiction=US/UK, environment, route=incidents, statusCode real y durationMs no negativo. Envelope: eventId UUID nuevo, timestamp final, sessionId=null, userId HMAC regional servidor, requestId UUID interno. No IDs operativos ni métodos/rutas libres.
5. Resolver/revalidar clínica en sesión independiente con controles actuales. Inactiva/desconocida/timeout descarta sin fallback; el coste de preparación posterior no forma parte de durationMs.
6. Reutilizar productor opcional, máximo16 tareas/timeout100ms y cola por región/binding clínico20/10 existente. Sink interno permite este tipo; browser lo sigue rechazando. Sin claves/dependencias/tablas nuevas, persistencia ni forwarding.
7. /audit puede emitir audit_accessed y api_request_completed: son hechos distintos, uno de lectura de auditoría y otro de finalización HTTP. No ampliar correlación del productor audit_accessed ni otros eventos en este lote; sus requestId actuales permanecen null.

## Archivos aprobados

Protegidos:
- backend/app/incidents/router.py: Request opcional y descriptor sólo en las cuatro lecturas señaladas; consultas, permisos y respuesta conservados.
- backend/app/main.py: registrar middleware nuevo, conservando CORS, autenticación y lifecycle.

Otros archivos del lote:
- Nuevos backend/app/telemetry/request_completion.py y request_producer.py.
- backend/app/telemetry/server.py: allowlist interna.
- Nuevo backend/tests/test_telemetry_request.py.
- README backend bilingües y documentación SDD de cobertura/evidencia.

Fuera de alcance: auth/dependencies/policies, auditoría persistente, contratos públicos JSON/OpenAPI, infraestructura/.env/CI, Memory Bank/Rules, datos locales/reales, despliegue y commit.

## Criterios de aceptación

1. Cuatro lecturas US/UK con respuesta completa emiten exactamente un evento HTTP con clave regional correcta.
2. statusCode y duración monotónica observados, incluyendo respuesta fragmentada y un error manejado posterior a descriptor; requestId independiente de datos externos.
3.401/403/404/422 sin descriptor, SQL previo, cancelación y send fallido no emiten. Rutas generales/telemetry ignoradas, sin recursión.
4. Permisos, cuerpos/cabeceras y auditoría persistente se conservan. /audit mantiene su evento previo independiente.
5. Payload cerrado, HMAC sin UUID operativos/texto/secretos y no fallback clínico inválido.
6. Saturación/timeout/fallo sink/cierre no alteran respuesta ni dejan tareas huérfanas.
7. Unitarias ASGI, integración sólo PostgreSQL sintético aislado, regresiones HTTP/serialización y validate-delivery.

## Limitaciones

Cobertura HTTP parcial explícita. No certifica producción ni cierra los tipos o superficies que siguen pendientes. No hay emisión para autenticación fallida o denegaciones anteriores a contexto; esas decisiones siguen abiertas. La aprobación de HMAC exclusivamente servidor conserva su alcance y no autoriza almacenamiento/transferencia real.

## Autorización y evidencia

El desarrollador respondió «apruebo» a la solicitud expresa del lote4 y de backend/app/incidents/router.py y backend/app/main.py. Pruebas test_telemetry_request.py: medición monotónica125ms, fragmentación, errores manejados400/500 con descriptor, query/serialización/send/cancel sin respuesta completa, fallo captura, cuota16/17, resolución UK/HMAC, clínica inválida/timeout y cierre. Integración real valida las cuatro rutas US/UK, requestId único sin cabecera pública ni IDs externos, coexistencia independiente de audit_accessed,401/403/404/422 y rutas generales sin captura, sink fallido sin fallo HTTP.

Se adaptó el sink de la integración test_telemetry_audit.py para contar sólo sus tipos de evento; la nueva integración confirma explícitamente ambos productores. No se rebajaron sus assertions de auditoría.

Validaciones:187 PASS sin DB y5 integraciones omitidas por guard;93 PASS con PostgreSQL16 temporal tmpfs telemetry_validation;113 PASS de contratos/serialización/OpenAPI/entrada/Compliance/catálogos en base aislada nueva. Recuentos solapados, no sumar como únicos. git diff --check PASS. Imagen de pruebas a3119fba302c; arnés /private/tmp/telemetry-business-compose.yaml, plugin NullPool sólo temporal/sintético. Entorno detenido. No se reconstruyó backend local ni se modificó su base.

Once tipos con productor al menos parcial,28 sin productor; cobertura global HTTP, auditoría y otros recursos Management sigue pendiente. Contrato1.1.0 y claves existentes conservados. Duración excluye la preparación posterior de telemetría y mide la finalización observada por este middleware, sin garantizar latencia de red del usuario.
