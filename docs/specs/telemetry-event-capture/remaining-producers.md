# Cobertura pendiente y lote 2 implementado

**Estado vigente — revisión final local (2026-11-01):** implementado y validado dentro del alcance reducido autorizado. Contrato1.2.0,39 tipos:19 con fuente al menos parcial y20 DEFERRED_NO_SOURCE aprobado. Un frontend/backoffice compartido y un backend; HMAC exclusivamente servidor, jurisdicción clínica autoritativa y null técnico general. Captura20/10 efímera, recepción no durable. Admisión browser5 + dos diagnósticos internos frontend restringidos; servidor admite sus hechos por canal propio. Backend/backoffice locales actualizados y Chrome sintético validado.

**La cobertura integral original NO está terminada:**9 de los20 diferidos son obligatorios; TEL-FR-018 sigue pendiente. Hay además brechas de los19 tipos actuales, detalladas en [delivery-status.md](./delivery-status.md). La aprobación de aplazamiento no equivale a requisitos satisfechos, producción ni cumplimiento normativo.

La matriz y estados vigentes están en [delivery-status.md](./delivery-status.md); la cronología que sigue conserva las propuestas y evidencias de cada revisión. Sus menciones a «actual», TODO/BLOCKED,1.1.0, cinco productores o pruebas NOT_RUN corresponden al momento histórico de esa sección y no sustituyen este estado vigente. No se han reescrito Memory Bank ni fuentes empresariales.

## Historial del diseño y de los lotes (referencia temporal)

Rama feature/telemetryEventCapture. Revisión del checkout después de activar configuración local. Nueve tipos con productor al menos parcial; 30 tipos siguen sin productor y la cobertura global de audit_accessed permanece pendiente. El desarrollador aprobó expresamente el lote2 mediante «aprobado». No declara fuentes inexistentes implementadas ni exclusiones aprobadas.

## Veinte tipos sin fuente actual

Inventario/pedidos/umbrales: inbound_order_completed, outbound_order_completed, inventory_validation_failed, stock_direct_update_rejected, inventory_threshold_activated, inventory_viewed, product_selected, order_started, order_abandoned, inventory_adjustment_completed, inventory_threshold_cleared, inventory_reconciliation_failed (12).

Motores ausentes: alert_triggered, notification_delivery_completed, job_run_completed (3).

Agregadores de dominios ausentes: appointment_period_aggregated, billing_period_aggregated, experience_period_aggregated, workforce_period_aggregated, clinical_workload_aggregated (5).

Propuesta: mantenerlos en backlog explícito fuera del cierre de esta entrega técnica, conservando contratos/nombres; requiere aprobación de alcance. No simular productores reales ni construir estos dominios por inferencia.

## Once tipos con fuente total/parcial

| Tipo | Situación y siguiente decisión |
| --- | --- |
| audit_accessed | Lote 2 implementado abajo: lectura de auditoría con clínica autoritativa. Auditoría global sin clínica sigue abierta. |
| management_mutation_completed | Commit/auditoría existentes. Clínicas activas permiten contexto; desactivación y cambio de jurisdicción requieren política de contexto histórico. Catálogos/áreas/sistemas globales no son una clínica. |
| authentication_succeeded | JWT verificado no es login/sesión SSO. Definir primera autenticación observada y deduplicación conceptual antes de emitir. |
| authentication_failed | No hay actor fiable ni clínica en credenciales fallidas; no tomar identidad de JWT inválido. |
| authorization_denied | Hay denegaciones de capacidad/área; clínica puede no estar disponible antes de la dependencia. |
| api_request_completed | Frontera ASGI existe; correlación requestId y región para rutas generales pendientes. |
| catalog_cache_observed | Contadores existentes, falta ventana/atribución; caché global no debe etiquetarse como clínica. |
| service_health_checked | /health y /status bajo demanda existen; no hay sondeo programado aprobado. |
| data_integrity_checked | No hay chequeo agregado del contrato equivalente al evento; validación puntual de referencias no equivale a integridad del sistema. |
| telemetry_contract_rejected | Diagnóstico técnico existente; canal separado, sin recursión y política de ámbito pendientes. |
| telemetry_delivery_failed | Igual; no enviar por la cola que acaba de fallar. |

El contrato 1.1.0 exige US/UK en estos once. No ampliar null ni alterar contratos públicos sin autorización específica. El backend compartido no convierte hechos generales en hechos US/UK.

## Lote 2 aprobado: audit_accessed

Fuentes actuales:
- GET /incidents/{incident_id}/audit: incidencia encontrada y capacidad audit:read comprobada antes de leer AuditEvent. Esta ruta no aplica comprobación de área; se conserva esa política existente, sin afirmar un control adicional.
- GET /management/audit-events sólo cuando resource_type=clinics y resource_id identifica una clínica existente autorizada; la consulta global y otros recursos quedan sin productor hasta resolver contexto.

Comportamiento implementado:
1. Las rutas dejan un descriptor interno acotado de lectura concluida: actor autenticado, clinic UUID y surface enum. Nunca snapshots, razones, filtros libres, cuerpos ni URLs. La resolución clínica posterior mantiene permisos vigentes.
2. Middleware ASGI programa captura sólo tras enviar el cuerpo final de una respuesta 2xx. Error, denegación, incidencia ausente, fallo de consulta/serialización o desconexión antes del final no generan evento. No reescribir status/cabeceras/cuerpo ni manejar errores de negocio como éxitos.
3. Productor servidor de mejor esfuerzo resuelve clínica en sesión independiente, selecciona claves US/UK, valida el modelo audit_accessed y reutiliza cola20/10 acotada. Envelope eventId/timestamp/userId HMAC, sessionId/requestId null por ahora; properties exclusivamente jurisdiction/environment/surface. Sin IDs clínicos/auditoría ni PHI exportados.
4. Ampliar sólo la allowlist del sink servidor para audit_accessed. POST /telemetry/events browser permanece limitado a cinco tipos técnicos; no aceptar afirmaciones de auditoría del navegador.
5. La lectura de auditoría persistente no se reemplaza ni modifica. No crear tablas, migraciones, logs con snapshots, claves, dependencias ni permisos nuevos. La captura fallida nunca impide la lectura.

No se incluyen history/assignment-history como auditoría genérica para evitar duplicar o reinterpretar superficies sin decisión. No emitir por cada fila devuelta, sino una vez por consulta satisfactoria. Clínica inactiva/desconocida no cae a null; esa cobertura queda explícitamente pendiente.

## Archivos aprobados e implementados

Protegidos:
- backend/app/incidents/router.py: descriptor interno tras consulta autorizada en incident_audit, sin tocar mutaciones anteriores.
- backend/app/management/router.py: descriptor sólo para filtro clinics/resource_id después de consulta satisfactoria.
- backend/app/main.py: registrar middleware ASGI de finalización, sin cambiar auth/CORS/rutas.

Dentro del alcance:
- backend/app/telemetry/server.py: política de sink servidor admite audit_accessed además del lote1.
- backend/app/telemetry/incident_producer.py: integración del ciclo de vida compartido si se necesita alojar productor de lectura, conservando hooks existentes.
- Nuevos backend/app/telemetry/audit_producer.py y backend/app/telemetry/audit_completion.py.
- Nuevos tests de productor/finalización y regresiones de auditoría/HTTP existentes.
- README backend bilingües y docs/specs/telemetry-event-capture.

Fuera: .env/secretos, Compose/CI/despliegue, Memory Bank, Rules, auth policies, contratos JSON/OpenAPI publicados, modelos/migraciones/auditoría persistente, commits/push/PR.

## Criterios de aceptación y validación

- Incidencia US/UK y Management filtrado por clínica emiten una vez sólo tras respuesta2xx completamente enviada, incluso resultado vacío autorizado.
- 401/403/404/422/500, excepción de SQL/serialización y envío interrumpido no emiten; fallo de telemetría mantiene respuesta original.
- General/otros filtros Management no emiten ni inventan jurisdicción; clínica inexistente/inactiva no genera fallback.
- Cuerpo/status/permisos y snapshots existentes idénticos; ningún UUID/secret/texto llega a event/log diagnóstico.
- Límites preparación/cola/cierre preservados; no recursión y browser business-event rejection intacto.
- Unitarios ASGI con respuestas fragmentadas/cancelación, productor regional y contrato; integración PostgreSQL sólo temporal sintética y regresiones auth/audit.
- validate-delivery revisa incremento completo. PASS del lote no equivale a cierre de audit_accessed global ni del proyecto.

## Estado y evidencia

Lote implementado tras aprobación expresa de los tres archivos protegidos y el diseño. Una consulta filtrada Management programa descriptor después de consulta/modelo satisfactorios; el productor resuelve la existencia/actividad de clínica en sesión independiente. No se añade un permiso de área que no existe en incident_audit. El productor comparte el lifecycle de incidentes y, por ello, exige su configuración válida; no requiere nuevas variables.

150 pruebas backend PASS; tres pruebas DB omitidas sin base por sus guards. PostgreSQL16 temporal en tmpfs con migraciones0001–0009/seeds sintéticos:54 PASS, incluidas las tres integraciones DB. Pruebas nuevas: respuesta fragmentada sólo emite tras final, estados2xx/no2xx, excepcionesSQL/serialización/desconexión/cancelación, sin descriptor/lifespan, captura fallida, límite16 compartido y resolución inactiva/timeout. Integración real de ambas superficies US/UK y consulta global/otros recursos/clínica inexistente/denegación404/403 sin captura; sink fallido preserva lectura200. No exporta UUID ni snapshots. No cambios de contratos JSON, políticas, migraciones, secretos, infraestructura ni datos locales.

La implementación se valida en imagen de pruebas; el backend local ya abierto requiere reconstrucción para cargar este lote. No se reinicia ni despliega automáticamente. La auditoría global/inactiva y otras30fuentes siguen abiertas; veinte tipos sin dominio no se excluyen por inferencia.

Regresión final de respuestas/redacción:58 PASS en PostgreSQL temporal recién inicializado, tests/test_response_contracts.py y tests/test_audit_serialization.py. Comandos ejecutados: podman compose --profile test run --no-deps --build --rm -e DATABASE_URL=postgresql+asyncpg://synthetic:synthetic@127.0.0.1:1/isolated test uv run --no-sync pytest tests/test_telemetry_audit.py tests/test_telemetry_shared.py tests/test_telemetry_server.py tests/test_telemetry_incident_producer.py tests/test_telemetry.py tests/test_telemetry_context.py tests/test_telemetry_identity.py tests/test_status.py tests/test_auth.py -q; integración mediante podman compose -f /private/tmp/telemetry-business-compose.yaml up --abort-on-container-exit --exit-code-from test, con plugin temporal NullPool y pytest de workflows/HTTP/productores; segunda ejecución para response_contracts/audit_serialization. Ambas usan tmpfs/seeds, no base local. git diff --check PASS. No se suman recuentos solapados como pruebas únicas.

## Lote3 aprobado: mutaciones de clínicas

Implementado management_mutation_completed sólo para clínicas, tras commit confirmado y desde jurisdicción histórica persistida: creación after_data; resto before_data. Regla y archivos protegidos aprobados expresamente por el desarrollador. Detalle y evidencia en [management-producers.md](./management-producers.md). Validación:174 PASS sin DB (4 integraciones omitidas),79 PASS con PostgreSQL sintético y113 PASS de contratos/regresiones en una base aislada nueva; recuentos solapados. Diez tipos con productor al menos parcial,29 sin productor, auditoría global/otros recursos Management pendientes. Contrato1.1.0, permisos y auditoría persistente conservados. No despliegue de este lote, producción, exclusiones nuevas ni cierre global.

## Lote4 aprobado e implementado: finalización HTTP clínica

api_request_completed cubre cuatro lecturas de incidencias autorizadas, con estado/duración monotónica y requestId exclusivamente interno. Regla y archivos protegidos aprobados mediante «apruebo». Diseño/evidencia en [api-request-producer.md](./api-request-producer.md).187 PASS sin DB (5 omitidas por aislamiento),93 PASS con PostgreSQL sintético y113 PASS de contratos/regresiones en base nueva; recuentos solapados. Once tipos con productor al menos parcial y28 sin productor; cobertura general HTTP/auditoría/otros recursos pendiente. Sin cambio de contrato1.1.0, permisos, claves, despliegue ni cierre global.

## Revisión contractual vigente1.2.0: ámbito técnico general

El desarrollador autorizó continuar con la ampliación recomendada para eventos técnicos sin clínica. Nueve tipos servidor más los cinco browser admiten null genuino; otros25 siguen exigiendo US/UK. No fallback clínico ni cambio de productores. Política de admisión browser separada de nulabilidad: sólo cinco tipos. Detalles en [general-technical-scope.md](./general-technical-scope.md). Copias frontend/backend sincronizadas; actualización coordinada necesaria,1.1.0 no se acepta silenciosamente. Once tipos al menos parcialmente instrumentados,28 aún sin productor. Sin despliegue ni cierre global.

## Lote6 aprobado: autenticación y denegación de capacidades

Implementados authentication_succeeded (primera credencial verificada por proceso), authentication_failed anónimo reducido y authorization_denied de capacidad. Jurisdicción general null/HMAC general, deduplicación1024 opaca/expiry, requestId interno compartido con finalización HTTP; /telemetry excluida. Archivos auth/dependencies.py y main.py expresamente aprobados. Detalle en [security-producers.md](./security-producers.md).209 PASS sin DB (6 integraciones omitidas),105 PASS PostgreSQL sintético,113 PASS contratos/regresiones en base nueva; recuentos solapados. Catorce tipos parcialmente instrumentados,25 sin productor. Denegaciones contextuales y otras coberturas generales pendientes. Sin cambio de contrato1.2.0, políticas, claves, despliegue ni cierre global.

## Lote7 aprobado: salud bajo demanda y caché

Implementados service_health_checked desde /health/status existentes y catalog_cache_observed como cortes de diferencias300s por proceso. Nulidad general, sin sonda externa ni mutación del cache; arranque opcional idempotente y cierre esperado. Diseño/main.py aprobados expresamente por «sigue». Detalles en [health-cache-producers.md](./health-cache-producers.md). Dieciséis tipos con productor parcial y23 sin productor; otros ámbitos pendientes, sin cambio de contrato1.2.0 ni despliegue/cierre global.


## Actualización aprobada — lote8 de diagnósticos

Implementados telemetry_contract_rejected y telemetry_delivery_failed de servidor con canal independiente sin recursión. Rechazo de esquema sólo tras422 completado o modelo normal inválido; fallo terminal/cuota usa jurisdicción validada, nunca payload rechazado ni texto de scope. Diseño/router.py/main.py aprobados por «apruebo». Detalles y validación239/142/113 en [diagnostic-producers.md](./diagnostic-producers.md). Dieciocho tipos con productor parcial y21 sin productor (20 sin dominio, data_integrity_checked). Diagnóstico browser y demás coberturas siguen abiertos; contrato1.2.0 conservado, sin despliegue ni cierre global.


## Actualización aprobada — lote9 de integridad del contrato

Implementado data_integrity_checked al arrancar un productor opcional válido, una vez por instancia, con check=event_contract y resultado anónimo/null ok/failed. Comprueba coherencia del contrato empaquetado y modelos cargados, sin acceso DB; fallo no bloquea API. main.py y lote aprobados por «apruebo». Cobertura19 tipos al menos parcial;20 sin dominio siguen sin productor. Referencias/cobertura histórica y otras coberturas permanecen abiertas. Detalles: [integrity-producer.md](./integrity-producer.md). Sin cambio de contrato1.2.0, despliegue ni cierre global.


## Alcance reducido aprobado — dominios diferidos

El desarrollador aprobó expresamente («apruebo») [deferred-domain-scope.md](./deferred-domain-scope.md). Los20 eventos sin fuente pasan a DEFERRED_NO_SOURCE para esta entrega;9 obligatorios y11 oportunidades permanecen como requisitos pendientes. No elimina ni altera el catálogo39/contrato1.2.0, ni satisface TEL-FR-018 o la cobertura integral original. Se continúa con19 tipos al menos parcialmente instrumentados y sus brechas concretas, sin crear dominios ficticios. Diagnósticos frontend y revisión conjunta siguen pendientes; no cierre global/producción.


## Lote10 aprobado — diagnósticos frontend

Implementados diagnósticos internos frontend de contrato/entrega, bajo contexto general firmado e identidad HMAC, sin datos rechazados/recursión. Backend admite sólo frontend2 general/requestId=null; público track conserva cinco tipos. Reserva normal180/224KiB y diagnóstico20/32KiB dentro de total200/256KiB; un vuelo20/10, diagnóstico un intento5s. Diseño/router.py aprobados mediante «apruebo». Evidencia74 Node/258 backend/161 PostgreSQL sintético/113 contratos en [frontend-diagnostics.md](./frontend-diagnostics.md).19 tipos con cobertura parcial y20 DEFERRED_NO_SOURCE aprobado; otras brechas y actualización conjunta local pendientes, sin cierre global ni producción.


## Activación local conjunta validada

Autorizada mediante «continua», actualización backend/backoffice sin db-init ni cambios DB/env/infra. Chrome real confirma UI incidencias y Management, contrato1.2.0 y recepción200 de navegación20, diagnósticos de esquema20+1 y entrega1 tras fallo controlado en adaptador.22 diagnósticos recibidos,0 retries diagnósticos, buffers vacíos al cerrar; backend check_contract=ok y health/status200. Detalle y límites: [local-activation-validation.md](./local-activation-validation.md). No cierre global ni producción; dominios diferidos/coberturas pendientes conservados.
