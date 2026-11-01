# Lote7 revisable: salud bajo demanda y cortes de caché

Estado: aprobado e implementado para validación sintética. Rama feature/telemetryEventCapture. Contrato1.2.0 conservado, sin nuevas claves/variables ni sondeos HTTP externos.

## catalog_cache_observed

Fuente: hits/misses/bypasses de CatalogCache global existente por proceso. No leer entradas, claves o payloads ni modificar su comportamiento. Un sampler opcional en lifecycle del productor observa cada300s con reloj monotónico. Baseline inicial toma valores al arrancar, no atribuye operaciones previas a esa ventana. Cada corte emite diferencias respecto al anterior y windowSeconds=floor(elapsed monotónico), mínimo1. Cada contador debe ser entero no negativo. Si disminuye o resulta inválido, descartar corte y rebajar baseline cuando sea válida; no emitir diferencias negativas ni normalizar datos corruptos.

El baseline avanza también si la cola rechaza el corte: no acumular ventanas arbitrarias ni reintentar el mismo corte. Timer/cierre pueden perder el corte parcial; no emitirlo por cierre ni resetear contadores de caché. Si se retrasa scheduling, emitir un corte del intervalo realmente observado, sin fabricar ventanas intermedias. Un sampler por proceso, cancelado/esperado al cerrar. Partición GENERAL:cache, jurisdiction/userId/sessionId/requestId=null. Properties sólo jurisdiction/environment/hits/misses/bypasses/windowSeconds. Cero actividad puede emitir contadores0. No copiar namespaces, actor, catálogos, UUIDs ni contenidos.

Los valores representan comportamiento de contadores actuales, no una reconstrucción nueva de requests. Métrica hit ratio = hits/(hits+misses) en el corte; denominador0 significa métrica no disponible, no0%. Bypasses se informa separado. No agregar tasas por promedio simple entre workers: sumar primero contadores compatibles. No prometemos identidad worker ni agregación distribuida en el contrato actual.

## service_health_checked

Fuente de este lote: llamadas existentes a GET /health y /status bajo demanda. No crear sonda, repetir SELECT1, cambiar timeouts o invocar APIs externas. /health produce check=liveness/outcome=ok cuando su respuesta termina correctamente. /status produce check=database con outcome=ok al conectar/SELECT1, failed si engine ausente o error SQL/OSError, timeout si se captura TimeoutError. Los mismos status200/503, cuerpos y manejo de excepciones se conservan.

Las funciones dejan descriptor efímero reducido (check/outcome) mediante Request opcional; health sigue síncrona y no programa captura desde threadpool. Middleware finaliza evento sólo después de enviar el último fragmento, con duración monotónica desde entrada middleware hasta final send, excluyendo preparación posterior. No inferir éxito desde path sin descriptor ni clasificar excepciones por texto. Respuesta interrumpida/cancelada/excepción sin descriptor no emite. Un resultado fallido manejado503 sí captura su outcome observado.

Envelope: eventId UUID, timestamp final, jurisdiction/userId/sessionId=null, requestId interno ya compartido con RequestCompletionMiddleware. Properties sólo jurisdiction/environment/check/outcome/durationMs. Partición GENERAL:health, cola20/10 acotada existente. Las rutas son públicas y conservan esa condición; no derivar actor o clínica de una cabecera. Este evento no afirma sondeo periódico ni seguimiento continuo: eso queda pendiente de aprobar frecuencia/fuente si se necesita.

## Integración y archivos

Archivo protegido expresamente aprobado:
- backend/app/main.py: Request opcional y descriptores en health/status; registro del middleware y orden que no incluya preparación en duración. No modificar consulta SELECT1, permisos, respuestas, CORS, entorno ni conexiones.

Otros archivos:
- Nuevos backend/app/telemetry/health_cache_producer.py y health_completion.py.
- backend/app/telemetry/incident_producer.py: arrancar/cancelar sampler opcional y limpiar su estado junto al lifecycle existente.
- backend/app/telemetry/server.py: permitir ambos tipos sólo en sink servidor.
- Nuevo backend/tests/test_telemetry_health_cache.py; regresiones de status/caché y adaptación de sinks anteriores para contar sus tipos.
- README backend bilingües y SDD/evidencia.

Fuera de alcance: backend/app/catalogs/cache.py y router.py (sólo lectura de contadores), auth/policies, nuevas rutas/contratos, infra/.env/CI, claves, datos locales/reales, migraciones/auditoría persistente, Memory Bank/Rules, despliegue, commit/push/PR.

## Criterios de aceptación

1. Cortes300s emiten diferencias correctas, intervalo real y cero actividad; no mutan contadores ni leen contenido de caché.
2. Reinicio/disminución/valores inválidos no emiten diferencias falsas; baseline inicial/corte rechazado/cierre parcial definidos y sampler sin tareas huérfanas.
3. health200 y status200/503 conservan respuestas exactas y generan check/outcome observado; timeout tipado, sin inventar sondeo.
4. Sólo respuesta final enviada emite salud; send fallido/cancelación/excepción sin final no emite. requestId interno compartido, sin cabecera nueva.
5. Payload cerrado/null general, sin IDs/PHI/texto/secretos. Fallo captura/sampler/sink no afecta negocio, cache o status.
6. Cola20/10 y límites vigentes; pruebas con reloj controlado, ASGI fragmentado y status/caché, PostgreSQL exclusivamente sintético aislado y validate-delivery.

## Autorización y límites

El desarrollador respondió «sigue» a la solicitud concreta de aprobación del diseño y de backend/app/main.py. Se aplica ese lote, sin ampliar conexiones/consultas, permisos, configuración de entorno o datos reales. La cache existente no se modifica.

start del productor opcional es idempotente mientras siga activo, para no dejar un segundo sampler. El sampler es una tarea separada de las preparaciones clínicas de100ms: las cuotas de16 tareas y los awaits de preparación no incluyen su espera300s. stop cancela/espera esa tarea y descarta la ventana parcial.

Salud mide finalización del middleware, no latencia completa del usuario. No crea sonda ni timeout nuevo; timeout describe únicamente TimeoutError ya observado por /status. El comportamiento de producción/residencia/retención sigue pendiente. Ambos productores requieren habilitación válida del productor opcional existente y sus claves RESOURCE; no ajustes nuevos.

Dieciséis tipos tienen productor al menos parcial y23 siguen sin productor (20 sin dominio,3 técnicos). General HTTP/auditoría/otros recursos Management y políticas contextuales siguen abiertos. Sin forwarding/persistencia, despliegue, commit ni cierre global.

## Evidencia de validación

223 pruebas backend PASS;7 integraciones omitidas sin DB por guard.125 pruebas PostgreSQL16 sintético aislado/tmpfs PASS, incluidas las7 integraciones y regresiones de caché.113 pruebas de contratos/serialización/OpenAPI/entrada/Compliance/catálogos PASS en base nueva antes del ajuste final de arranque idempotente; ese ajuste sólo cambia arranque y quedó cubierto por223/125 finales, sin nuevos cambios HTTP. Recuentos solapados. Imagen final51303bf52516. git diff --check PASS, staged vacío y entorno temporal detenido.

Pruebas demuestran diferencias y ventana300/350s, cero actividad, contador disminuido/NaN y recuperación sin valores falsos, baseline después de rechazo, cierre parcial descartado, sampler300s único y arranque duplicado idempotente. health/status conservan200/503/cuerpos/SELECT1; SQL/OSError/TimeoutError reducidos y sin detalle sensible; fragmentación/send/cancel/excepción/fallo captura y requestId compartido comprobados. Integración /status usa PostgreSQL real sólo sintético.
