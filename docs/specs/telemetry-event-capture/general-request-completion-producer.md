# Lote propuesto — api_request_completed en health/status

2026-11-03. DESIGN_READY, implementación/pruebas NOT_RUN.

## Evidencia y elección
RequestCompletionMiddleware genera UUID interno, mide tiempo monotónico y captura después de final send exitoso. request_producer sólo acepta marcas clínicas y publica route=incidents; cuatro GET tienen mark_request. El contrato1.2.0 ya permite route=health/status y jurisdiction=null. main.py tiene ambas rutas generales sin autenticación, con healthResponse/statusResponse explícitos. Existe service_health_checked bajo demanda, pero no api_request_completed para ellas: hechos distintos, no reemplazar ni duplicar el mismo tipo.

No ampliar inventario usando route=unknown: falta inventory en enum contractual y resolver_clinic usa permisos de incidencias, incompatibles con roles de inventario. Esa ampliación requiere lote propio con contrato y resolución correctos. Management/audit global tampoco admite null actualmente; conservar pendiente.

## Cambios concretos pendientes de autorización
- request_producer.py: marca general explícita para health/status con clave state separada; captura general anónima con userId/sessionId=null, requestId UUID interno existente, propiedades cerradas jurisdiction=null/environment/route/statusCode/durationMs. No actor, country/IP/URL/body/query/headers ni mensajes de error. Allowlist exactamente dos rutas. Mismo servicio opcional/cola/sink interno, captura best effort sin retries ni persistencia.
- request_completion.py: observar marca general sólo tras final response.body enviado correctamente. Mantener descriptor clínico/captura existentes y precedencia única para no duplicar tipo. Limpiar ambas marcas/UUID al finalizar; websocket, final send fallido, respuesta incompleta, cancelación o excepción sin final send no capturan. Duración monotónica desde entrada ASGI, incluye espera de DB/red de envío; no mide sólo SQL ni latencia frontend.
- main.py: marcar health y status, incluyendo status503 por engine ausente/fallo de conexión. Conservar health/status schemas, códigos, mark_health y productores de salud existentes. No hook en auth/telemetry/unknown/404 ni captura automática de todos los endpoints.
- Tests nuevos o extensión test_telemetry_requests.py (localizar nombre real), README bilingües backend y expediente. Sin nuevos contratos/campos/allowlists browser, permisos, .env, infraestructura, dependencias, DB o UI. No commits ni despliegue compartido.

## Criterios de aceptación
1. health200, status200 y status503 completos generan uno api_request_completed con ruta/status/duración correctos y contexto genuinamente general; health-check existente sigue independiente.
2. RequestId único generado por servidor, nunca copiar X-Request-Id del cliente. Payload mínimo, sin datos de respuesta/token/actor/URL ni PHI.
3. Marca clínica vigente sigue produciendo exactamente uno route=incidents regional con lógica previa; ausencia de marca no captura, incluso auth/telemetry/404.
4. ASGI streaming/final send fallido/cancelación/respuesta incompleta no capturan; estado eliminado, sin repetir por final body duplicado.
5. Disabled/closed/cola saturada/sink fallido/medición inválida no alteran respuesta de servicio ni provocan recursión.
6. Unitarios ASGI/contrato/browser y smoke HTTP para health/status, regresión productores/general; git diff --check y validate-delivery. No probar fallo de DB contra servicio compartido; engine simulado o PostgreSQL desechable.

## Límites y revisión
Cobertura sigue parcial: otras rutas, mutaciones, inventario/management/compliance y correlación integral pendientes. Este lote no cambia31tipos/8sin productor: amplía un tipo existente. Solicitar aprobación expresa para nueva captura/correlación de requests y hooks de entorno conforme AGENTS.md; revisión de Cumplimiento pendiente. Sin afirmación de cumplimiento HIPAA/UK GDPR ni producción.


## Implementación autorizada y evidencia — 2026-11-03

Aprobación «Sí, autorizo este lote para el prototipo sintético». Implementadas marcas generales separadas, captura anónima, final send/limpieza en middleware y marcas health/status. Descriptor clínico conserva precedencia y firma previa. No nuevos contratos, tipos, IDs de usuario, auth policies, UI, dependencias, tablas, .env, Memory Bank/Rules ni despliegue/commit. DESIGN_READY/NOT_RUN anteriores son históricos.

- `.venv/bin/pytest -q -m 'not integration' tests/test_telemetry_general_request.py tests/test_telemetry_request.py tests/test_telemetry_health_cache.py tests/test_telemetry_server.py tests/test_telemetry_incident_producer.py`: **67 passed,3 deselected**,0.83s.
- `.venv/bin/pytest -q -m 'not integration' tests`: **646 passed,36 deselected**,4.02s; recuentos solapados. APP_ENVIRONMENT=test, DATABASE_URL contra PostgreSQL16 sintético tmpfs loopback18491/inventory_validation_requests para pruebas generales de caché. Fresh migraciones existentes0001–0013 PASS; sin migración nueva.
- Nuevo fichero19 pruebas: streaming/finalsend, cancelación, envío fallido, body repetido/incompleto, fallo captura, sinmarca y precedencia clínica; HTTP ASGI health200/status200/status503 con engine simulado, IDs internos correlacionados y contenido/códigos intactos; disabled/closed/saturación/sink/medición inválida y browser403. Duración125ms comprobada con reloj monotónico controlado.
- Tests de salud actualizados para exigir ambos tipos independientes y drenar sus ámbitos separados GENERAL y GENERAL:health; no eliminación de aserciones de salud. Expectativa de la integración regional existente ajustada por dos nuevas lecturas generales; esa integración no se ejecutó (requiere DB telemetry_validation y fixtures específicas). Lógica regional sí pasa sus pruebas unitarias previas. No UI/build/E2E: no cambios frontend/contrato.
- git diff --check PASS. Fuentes revisadas: request_producer/completion, main, nuevo test y ajustes de health/request; cambios previos preservados.

Cobertura31 tipos parcial/8 sin productor sin cambio: se amplía un tipo existente. api_request_completed sigue pendiente en otras rutas, mutaciones y correlación integral. Contexto clínico inválido no cae a null; las nuevas rutas son generales por definición. Sin entrega durable ni aprobación global de Cumplimiento/producción.
