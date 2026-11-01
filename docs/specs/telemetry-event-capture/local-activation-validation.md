# Actualización conjunta y validación local — 2026-11-01

Estado: PASS del paso local autorizado por «continua», después de recomendar actualización conjunta backend/backoffice y validación Chrome sintética. Rama feature/telemetryEventCapture. No autorización de producción ni cierre integral de TEL-FR-018.

## Actualización ejecutada

podman compose up --no-deps --build -d backend backoffice terminó exit0. Backend imagen a3a6b9691040, código final del lote10 y contrato1.2.0. Backend llegó a Healthy antes de iniciar backoffice. Sólo estos dos servicios reiniciados; no db-init, migraciones, seeds, recreación de DB, frontend corporativo ni cambios env/Compose. PostgreSQL conservó el contenedor (26 horas de ejecución), website conservó25 horas. Servicios sólo127.0.0.1:8000/8080.

GET /health y /status200, database=connected. Config pública backoffice: enabled=true, environment=development, endpoint=http://localhost:8000/telemetry/events, sin claves. Dentro del contenedor, check_contract() devolvióok y VERSION=1.2.0. No inspección/env/log de claves HMAC/JWT.

## Chrome real — controles UI

Nueva pestaña localhost:8080, módulos recargados. Conexión con JWT temporal de una identidad sintética technology, sin mostrar valor. UI: conectado, consulta/incidencias200 y0 resultados autorizados. No se creó ni modificó incidencia. Nueva pestaña Management: misma API/identidad sintética, carga de cuatro catálogos confirmada en UI. Sólo lecturas; no nuevas mutaciones de negocio ni datos reales.

## Chrome real — captura controlada

DevTools invocó los módulos servidos reales (/telemetry/telemetry-service.js, contrato/config), con identidad sintética emitida por /auth/tokens y contexto firmado de la API actual. Instancia experimental independiente de la UI, sin modificar global fetch ni código del repositorio. Adaptador local simuló una respuesta403 únicamente para un lote normal; los contextos y eventos aceptados fueron HTTP reales al backend. No afirmar que ese403 vino del backend ni que se provocó un fallo del servicio.

Segunda ejecución registró resultados por línea; la primera tenía el resumen truncado por la representación AX. Resultados completos:

| Envío real | Cantidad | HTTP | Versión | Jurisdicción | Productor |
|---|---|---|---|---|---|
| session_started |1|200|1.2.0|null|browser ordinario|
| navigation_viewed |20|200|1.2.0|null|browser ordinario|
| telemetry_contract_rejected |20|200|1.2.0|null|frontend|
| telemetry_contract_rejected incompleto automático |1|200|1.2.0|null|frontend|
| telemetry_delivery_failed tras403 simulado |1|200|1.2.0|null|frontend|

El lote incompleto estaba recibido al acabar la espera10502ms; no se midió su instante HTTP exacto ni se atribuye ese valor como latencia garantizada. La regla10s y los reintentos quedan además comprobados por los74 tests Node del lote10.

Contadores finales: rejected21, discarded1, received21, retries0, diagnosticRejected0, diagnosticDiscarded0, diagnosticReceived22; pending/inFlight/diagnosticPending/diagnosticInFlight0. destroy confirmó cierre vacío. El descarte normal corresponde únicamente al403 del adaptador; ese único terminal produjo un diagnóstico. No logs/artefactos con JWT, HMAC, UUID clínicos, payload rechazado o texto real; resumen sólo tipos/cantidad/estado/versión/ámbito/contadores. Advertencia Chrome observada procedía de extensión browser-integration.js, no del producto.

## Limpieza y límites

Instancias experimentales destruidas, las dos pestañas creadas para pruebas cerradas; pestañas previas del usuario conservadas. Credencial del arnés retirada de la sesión y archivo temporal sobrescrito con objeto vacío. Tokens sólo temporales de desarrollo; no revocación/política de auth modificada.

No HAR, Network headers con credenciales exportados ni alteración de preferencias/permisos del navegador. No nuevo benchmark, otros browsers, fallos reales de infraestructura ni cobertura regional nueva en este paso; últimas suites sintéticas del lote10 siguen siendo74 Node/258 backend/161 PostgreSQL/113 contratos. Recuentos solapados.

Este paso resuelve actualización conjunta y recepción diagnóstica Chrome descritas.19 tipos siguen con cobertura parcial;20 DEFERRED_NO_SOURCE aprobado; mayor cobertura HTTP/auditoría/Management, referencias/cobertura histórica, sondeo y revisión final SDD pendientes. Sin persistencia/forwarding, commit/push/PR o producción.
