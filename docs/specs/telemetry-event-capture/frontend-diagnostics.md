# Lote10 revisable — diagnósticos frontend

Estado: lote y receptor backend aprobados expresamente mediante «apruebo» e implementados; validación sintética completada. Aplazamiento20 dominios aprobado. Contrato1.2.0 y nombres39 conservados.

## Fuente y modificación necesaria

telemetry-service.js ya tiene validación, cuotas, reintentos y contadores locales; no genera eventos diagnósticos. validation.js permite sólo browser5 y backend/app/telemetry/router.py rechaza los otros34 tipos. El canal diagnóstico backend del lote8 permite únicamente hechos internos producer=api; no reutilizarlo como entrada arbitraria del navegador.

Admitir en POST /telemetry/events únicamente los dos tipos diagnósticos con producer=frontend y jurisdiction=null bajo contexto general autenticado. Conservar validación existente de Bearer, contexto firmado, sessionId/userId HMAC/environment y actividad de clínica cuando corresponda. Un diagnóstico requiere contexto general sin clínica; rechazar producer=api/worker, contexto clínico o identidad alterada. Mantener browser5 separado en GENERAL_EVENTS y no permitir track() público para estos dos tipos. Añadir admisión diagnóstica interna explícita en frontend, sin modificar contrato/esquemas.

## Eventos y privacidad

telemetry_contract_rejected: fallo de validación de evento normal, incluida forma/tipos/NaN o tamaño2KiB, devuelve diagnóstico genérico reasonCode=schema. No copiar properties/tipo rechazado ni inferir version/privacy/timestamp sin clasificador. Sólo si contexto general ya existe y está vigente; sin identidad/contexto no emitir ni realizar una conexión nueva.

telemetry_delivery_failed: cuota normal llena → queue_full; fallo terminal de lote normal por timeout → timeout y demás errores/ACK inválido/HTTP no recuperable/contexto no renovable → unavailable. Un evento por lote terminal, no por intento ni evento. Mantener tres reintentos adicionales normales con los mismos IDs. Clasificar timeout mediante señal explícita del temporizador de transporte, no mensaje de excepción. Cancelación/disconnect/destroy/cambio de identidad no es fallo terminal.

Todos usan contexto general HMAC/session firmado ya emitido en connect(), schemaVersion vigente, requestId=null, eventId nuevo y timestamp del diagnóstico. jurisdiction=null describe diagnóstico general del productor, nunca región tomada del payload rechazado o fallback clínico. A diferencia del diagnóstico servidor anónimo, ingreso browser mantiene su identidad seudónima autenticada; no envía claves ni UUID operativos. Sin stack, URL, cuerpo, nombres de artículo, token, incidente o razón libre. No diagnóstico cuando falta el contexto general válido; pérdida local contada.

## Buffer y transporte sin recursión

Dos buffers lógicos con presupuesto reservado dentro del límite total vigente: normal máximo180 eventos/224KiB; diagnóstico máximo20 eventos/32KiB. Total incluyendo vuelo nunca supera200/256KiB; evento2KiB, cuerpo48KiB. Reducir explícitamente cuota normal para garantizar reserva sin aumentar memoria total. Lotes20 o10s desde primer evento, no debounce. Diagnóstico lleno/inválido/fallido sólo contadores, nunca genera otro evento.

Un único vuelo global. Lote normal en retry conserva exclusividad hasta terminar; luego puede enviarse diagnóstico pendiente con prioridad, sin modificar el cuerpo ni IDs del lote normal. El diagnóstico tiene un único intento5s y ningún retry, para no prolongar fallos ni autorrecursión. No garantizar que pueda entregarse mientras transporte/auth estén caídos. HTTP keepalive/visibility reutilizan scheduler y no duplican vuelo. Contexto firmado puede renovarse antes de envío; identidad/generación anterior se descarta siempre, sin enviar con nuevas credenciales. Disconnect/destroy cancela ambos buffers/timers/vuelo y libera memoria.

## Archivos propuestos

- Protegido: backend/app/telemetry/router.py, admisión específica de dos diagnósticos producer=frontend/contexto general, sin cambiar contratos, auth/policies ni admisión de hechos de servidor.
- uis/backoffice/operational-incidents/telemetry/telemetry-service.js: buffer reservado/captura interna/scheduler y contadores diagnósticos.
- validation.js: validador interno diagnóstico separado, conservando cinco tipos públicos.
- transport.js: motivo timeout tipado/acotado sin texto reflejado; mantener controles de URL y cache/redirect.
- tests/service.test.mjs y pruebas adicionales de buffer/transport; backend tests de admisión/contexto y regresiones.
- README compartido bilingüe y SDD/evidencia.

Fuera: contratos JSON, claves/env/Compose, nuevos endpoints/dependencias, auth/policies, auditoría/modelos/migraciones/datos, Memory Bank/Rules, despliegue, commit/push/PR.

## Criterios de aceptación

1. Rechazo normal produce schema reducido sin datos rechazados y sólo con contexto general válido; track() sigue permitiendo únicamente browser5.
2. Cuota/retry terminal producen un diagnóstico por hecho con motivo permitido; timeout distinguido por temporizador, cancelación no diagnosticada.
3. Memoria total200/256KiB y reserva180/224+20/32 incluyendo vuelo,20/10, un vuelo, diagnóstico sin retries. Full/failure diagnóstico no recurse.
4. Renovación/contextos/generación/disconnect preservan identidad y semántica; no caen a clínica o credenciales nuevas; respuestas y UI de negocio intactas.
5. Backend admite sólo frontend2 con contexto general/HMAC real; rechaza api/worker, clínicos, identidad/environment alterados y otros hechos servidor. Contrato publicado1.2.0 conservado.
6. Pruebas Node con reloj/fetch controlados y backend aislado, regresiones de contexto/auth/colas, PostgreSQL sintético si integración lo requiere, revisión diff y validate-delivery.

## Aprobación requerida

AGENTS.md exige aprobación expresa para cambios de seguridad/receptor. El usuario confirmó este lote y la ampliación concreta de router.py, incluida cuota normal180/224KiB y reserva diagnóstica20/32KiB, mediante «apruebo». No desplegar automáticamente. El lote amplía cobertura de dos tipos actuales, no añade nuevos tipos ni satisface dominios diferidos.


## Implementación

Buffers lógicos separados por metadata diagnostic en el almacenamiento compartido, con presupuestos reservados y contador independiente. validDiagnostic separado de validEvent/GENERAL_EVENTS; sólo captura interna construye estos eventos. Scheduler único garantiza no mezclar diagnósticos con lotes normales ni duplicar vuelo; diagnóstico pendiente puede adelantarse al normal al liberar el vuelo. TransportTimeoutError sólo desde temporizador real, no texto de excepción. Backend exige además requestId=null. Sin cambios de contratos JSON, claves, auth/policies, infraestructura o datos.


## Evidencia final

74 pruebas Node PASS;258 backend PASS con8 integraciones omitidas sólo sin DB;161 pruebas PostgreSQL16 sintético/tmpfs PASS, incluidas todas las integraciones;113 regresiones de contratos/serialización/OpenAPI/entrada/Compliance/catálogos PASS en otra base nueva. Recuentos solapados. Imagen final051867c3d096. git diff --check PASS y staged vacío.

Node comprueba reserva incluyendo vuelo, reducción de normal180, schema reducido sin campos rechazados, validación interna/public track5,20/10, fallo diagnóstico sin retry/recursión, cuatro intentos normales con body idéntico, timeout tipado, prioridad al liberar vuelo y destroy sin diagnósticos por cancelación. Se adaptaron tres expectativas previas a presencia/prioridad del diagnóstico y cuota normal aprobada; no se eliminaron las verificaciones. Backend verifica dos tipos, rechazo api/worker, identidad/requestId alterados y contexto clínico incluso con jurisdiction=null.

Los dos tipos cuentan con productores frontend/backend, con motivos genéricos y limitaciones de contexto/transporte. Los19 tipos actuales siguen teniendo cobertura al menos parcial;20 quedan DEFERRED_NO_SOURCE aprobado. Sin despliegue, Chrome de este lote, commit ni cierre integral original. La validación conjunta en servicios actualizados es el siguiente paso de activación autorizado por separado.
