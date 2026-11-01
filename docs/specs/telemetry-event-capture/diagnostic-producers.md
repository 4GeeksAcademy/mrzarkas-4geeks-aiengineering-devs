# Lote8 revisable: diagnósticos backend sin recursión

Estado: aprobado expresamente por el desarrollador («apruebo») e implementado; validación sintética completada. Rama feature/telemetryEventCapture; contrato1.2.0 conservado. No canal externo, almacenamiento persistente ni productor browser nuevo.

## Canal implementado

Una cola de diagnóstico separada por proceso del buffer de negocio, exclusiva para telemetry_contract_rejected y telemetry_delivery_failed. Puede reutilizar el mecanismo ServerQueue con allowlist explícita y callback diagnóstico desactivado: nunca reenviar un diagnóstico por la cola que falló ni diagnosticar errores del propio canal.

Límites200 eventos/256KiB incluyendo vuelo,2KiB por evento y48KiB por cuerpo, lotes20 o10s desde primero por ámbito US/UK/general, un consumidor, timeout1s de sink, sin reintentos. Saturación/validación/fallo/cierre del canal incrementa sólo sus contadores locales. Sink local independiente valida modelos diagnósticos y registra sólo cantidad/tipos permitidos; no payload/eventos/identidades/razones libres en logs. El registro en memoria es transitorio, no entrega durable ni observabilidad externa certificada.

Compartir lifecycle opcional existente: creación tras configuración válida, cierre limpia timers/tareas/buffers. Sin claves ni variables nuevas; si telemetría está deshabilitada/configuración inválida, no se capturan diagnósticos. Separación física de buffers permite intentar diagnóstico aunque la cola de negocio esté llena. Ambos canales pueden perder eventos al cerrar o fallar. No crear endpoint público para consultar buffers.

## Fuentes de telemetry_contract_rejected

1. SafeTelemetryRoute captura RequestValidationError de entrada a /telemetry/context o /events. Marcar descriptor seguro reasonCode=schema/producer=api y emitir sólo tras respuesta422 completamente enviada, sin modificar status/cuerpo/cabeceras. No inspeccionar .errors(), payload, URL, token, actor ni jurisdicción declarada. Null general/userId/sessionId=null porque no hay contexto del evento rechazado confiable. requestId interno compartido si está disponible; no cabecera pública.
2. ServerQueue normal rechaza evento no admitido o modelo/cuerpo inválido antes de enqueue: emitir schema/producer=api al canal separado. No reutilizar ningún campo del evento inválido, por lo que jurisdiction/userId/sessionId/requestId=null. No afirmar version/privacy/timestamp sin clasificador formal. No clasificar401/403 de autenticación o contexto como errores de esquema.

No cambiar el manejo actual413/401/403/503 ni reclasificarlos en este lote. El motivo enum schema es deliberadamente genérico; desglose fino y validación/rechazo frontend permanecen pendientes.

## Fuentes de telemetry_delivery_failed

- ServerQueue normal, evento ya validado que no cabe por cuota200/256KiB: reasonCode=queue_full, producer=api, usando sólo jurisdiction de modelo ya validado (US/UK/null). No cargar clínica de nuevo ni leer campos originales.
- Cola normal cerrada/no disponible: reasonCode=unavailable con null si no existe modelo validado; configuración deshabilitada no crea evento.
- Lote normal cuya entrega terminal al sink acaba en timeout: timeout. Excepción u ACK ausente/incorrecto: unavailable. El productor local no reintenta, así que este único intento constituye su fallo terminal; no inventar agotamiento de reintentos frontend.

Ámbito de lote procede de modelos validados, nunca del texto libre de partición ni de payload rechazado. Guardar metadata de jurisdicción junto al evento en buffer o usar únicamente modelos ya validados; si las regiones son incoherentes descartar diagnóstico regional, sin inventar fallback. Un diagnóstico por lote fallido, no uno por cada evento. userId/sessionId/requestId=null para fallos de cola sin correlación singular fiable. Nunca IDs de clínica, audit/incident, URL, token, excepción literal o cuerpo del lote.

Cancelación/shutdown no genera delivery_failed: es descarte de lifecycle contado localmente. Error del canal separado tampoco genera ningún evento. No alterar receipt, descartes, reintentos, respuesta o auditoría de negocio existentes.

## Archivos concretos

Archivos protegidos aprobados expresamente:
- backend/app/telemetry/router.py: descriptor genérico sólo en RequestValidationError, conservando el receptor/autenticación/errores y allowlist browser5.
- backend/app/main.py: registro de middleware de finalización diagnóstica y orden compatible con requestId; sin cambiar CORS/rutas/health/auth.

Otros archivos:
- Nuevos backend/app/telemetry/diagnostic_producer.py y diagnostic_completion.py.
- backend/app/telemetry/server.py: allowlist configurable/buffer independiente y hooks reducidos de cola normal, sin callbacks en canal diagnóstico.
- backend/app/telemetry/incident_producer.py: creación/cierre de canal separado junto al lifecycle opcional idempotente.
- Nuevo backend/tests/test_telemetry_diagnostics.py; regresiones existentes de recepción/colas/finalización/seguridad y PostgreSQL sintético.
- README backend bilingües y SDD/evidencia.

Fuera: contrato JSON/API publicado, auth/security/roles/policies, auditoría persistente, dependencias, frontend, claves/.env/Compose/CI, datos locales/reales, migraciones, Memory Bank/Rules, despliegue, commit/push/PR.

## Criterios de aceptación

1.422 de RequestValidationError produce un diagnóstico schema anónimo sólo tras final send; respuesta actual intacta y datos inválidos no reflejados.
2. Evento normal inválido no entra en cola, pero produce diagnóstico genérico sin leer identidad/jurisdicción originales. Autenticación/contexto401/403 no se reclasifica.
3. Cuota de negocio llena puede generar queue_full en canal independiente con región de modelo válido. Timeout/excepción/ACK inválido generan un evento por lote con ámbito verificado y motivo permitido.
4. Canal diagnóstico lleno/roto/validación fallida no genera recursión; cola normal nunca admite estos tipos desde browser ni los mezcla con negocio. Shutdown/cancelación no diagnostican fallo terminal.
5. Límites20/10/200/256KiB/48KiB/2KiB/1s, scope separado y cierre sin tareas huérfanas; sin PHI/UUID operativos/tokens/texto en event/log.
6. Hook opcional fallido no cambia respuesta, auditoría, recibos ni descartes de negocio. Pruebas unitarias de ambos canales y ASGI, integración sólo PostgreSQL sintético aislado, regresiones auth/contratos y validate-delivery.

## Límites y aprobación

AGENTS.md requiere aprobación expresa de seguridad/configuración de main.py y del receptor protegido router.py. La respuesta «apruebo» autoriza los cambios concretos de este lote. Los dos tipos tienen cobertura backend parcial; este resultado no certifica producción/retención; frontend y exportador permanecerán abiertos. Integridad de datos,20 eventos sin dominio y otras coberturas siguen pendientes.


## Evidencia de ejecución — lote8

Implementados DiagnosticChannel/DiagnosticCompletionMiddleware, descriptor seguro de RequestValidationError y callbacks reducidos de ServerQueue normal. El buffer guarda jurisdicción de modelo validado y separa lotes incluso si dos regiones comparten el mismo texto de scope. Canal diagnóstico sin callback; ambos canales se cierran con el lifecycle opcional. Contrato1.2.0 y allowlist browser5 conservados.

Pruebas test_telemetry_diagnostics.py: saturación independiente, payload inválido sin campos reflejados, excepción/timeout/ACK incorrecto por lote, regiones separadas, fallo/saturación del canal sin recursión, cancelación, reloj20/10, respuesta ASGI fragmentada/422/no descriptor/403/send/cancel/captura fallida, ingreso real sin reclasificar401 y logs reducidos. Integración con lifespan real: health válido con sink normal fallido y esquema inválido producen dos diagnósticos anónimos independientes, cierre limpio.

239 pruebas backend PASS;8 integraciones omitidas sólo en ejecución sin DB.142 pruebas PASS en PostgreSQL16 sintético aislado/tmpfs, incluidas las8 integraciones.113 regresiones de contratos/serialización/OpenAPI/entrada/Compliance/catálogos PASS en otra base sintética nueva. Recuentos solapados. Imagen b9d8818eea3d. La primera ejecución detectó fixture no importada; corregida y todas las ejecuciones finales pasan.

Dieciocho tipos con productor parcial y21 sin productor:20 sin dominio y data_integrity_checked. Diagnóstico frontend, mayor cobertura HTTP/auditoría/Management, políticas contextuales y exportación durable siguen abiertos. Este lote no actualiza servicios locales ni cierra el proyecto global.
