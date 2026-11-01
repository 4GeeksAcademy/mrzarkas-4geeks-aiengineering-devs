# Productores servidor — lote 1 implementado

Fecha: 2026-11-01. Rama: feature/telemetryEventCapture. Estado: lote 1 aprobado por el desarrollador («apruebo, continua») e implementado; activación operativa pendiente. Mantiene contrato 1.1.0 y receptor browser restringido a los cinco eventos técnicos. Fuentes contrastadas con código, no con necesidades del briefing.

## Cobertura de los 34 eventos pendientes

| Eventos | Fuente observada | Disposición |
| --- | --- | --- |
| incident_created, incident_transitioned, incident_assigned | backend/app/incidents/router.py: create_incident, transition_incident, assign_incident; AuditEvent y commit existentes | Lote 1 implementado: productor servidor post-commit |
| audit_accessed | Lecturas autorizadas de historial/auditoría de incidencias y Management | Lote posterior: sólo lectura con clínica resuelta; auditoría global carece de clínica |
| management_mutation_completed | Management y Compliance persistentes | Lote posterior: posible para mutaciones con clínica/ámbito único resuelto; catálogos, áreas y sistemas multirregión no admiten el contexto vigente |
| authentication_succeeded, authentication_failed, authorization_denied | auth/dependencies.py y policies.py | Pendiente diseño/revisión de contexto: autenticación general o fallida no proporciona clínica confiable; no usar región de instalación como jurisdicción clínica ni identificar desde JWT inválido |
| api_request_completed | Frontera HTTP existente | Fuera de lote 1; se coordina con punto 2 requestId y tratamiento de peticiones generales |
| catalog_cache_observed | catalog_cache: hits/misses/bypasses | Fuente existe, falta ventana y atribución clínica válida; no etiquetar contadores globales como una clínica |
| service_health_checked | GET /health y /status | Comprobaciones bajo demanda existentes; no hay sondeo programado. Salud de instalación sin clínica no satisface jurisdicción obligatoria |
| data_integrity_checked | Validación de referencias por operación | No hay chequeo agregado equivalente de integridad/cobertura/event_contract; no convertir una validación de formulario en chequeo de sistema |
| telemetry_contract_rejected, telemetry_delivery_failed | Contadores locales técnicos | Falta canal diagnóstico separado y contexto regional aprobado; no enviarlos por la propia cola fallida |
| inbound_order_completed, outbound_order_completed, inventory_validation_failed, stock_direct_update_rejected, inventory_threshold_activated, inventory_viewed, product_selected, order_started, order_abandoned, inventory_adjustment_completed, inventory_threshold_cleared, inventory_reconciliation_failed | Inventario, movimientos, pedidos y umbrales no existen | Diferidos por falta de fuente; no crear dominio ficticio para cerrar catálogo |
| alert_triggered, notification_delivery_completed, job_run_completed | No hay motor de alertas, entrega de notificaciones ni ejecuciones de jobs aprobados | Diferidos por falta de fuente |
| appointment_period_aggregated, billing_period_aggregated, experience_period_aggregated, workforce_period_aggregated, clinical_workload_aggregated | No existen fuentes/agregadores correspondientes | Diferidos por falta de fuente; métricas de incidencias existentes no son estos KPI |

Los cinco productores frontend actuales permanecen implementados. Ninguna disposición diferida significa DONE ni aprobación de exclusión global. Tres productores servidor implementados: ocho eventos tienen fuente implementada en total y 31 siguen pendientes/diferidos.

## Diseño del lote 1

1. Mantener referencias a los AuditEvent existentes en las tres funciones de incidencias. Inmediatamente después de que await session.commit() retorne, programar captura con actor.id, clinic_id, incident.id, audit.id y tipo fijo. Antes de refresh, para no perder el hecho confirmado si falla serialización/refresco. Un rollback, conflicto, autorización denegada o error de commit no programa evento.
2. No hacer lecturas telemétricas dentro de la transacción de negocio. Una tarea acotada resuelve Clinic/Jurisdiction en sesión de sólo lectura independiente, con timeout, y rechaza clínica inactiva/desconocida o contexto regional inválido. Sin fallback null. No modificar permisos existentes ni convertir error telemetry en error de mutación.
3. Generar seudónimo de usuario con el HMAC vigente. Añadir clave exclusiva de recursos TELEMETRY_RESOURCE_KEY en Settings (sin editar .env); mínimo32bytes y distinta de las cuatro claves telemetry y JWT. Derivar subclaves HMAC por propósito incident/audit, luego HMAC del UUID canónico con dominio/versionado. No reutilizar claves de usuario, clínica ni firma para los recursos. Nunca enviar UUID originales ni claves al frontend.
4. Envelope servidor: eventId UUID independiente; timestamp del hecho confirmado; sessionId:null (no inventar sesión); userId seudónimo del actor confirmado; requestId:null hasta punto2; schemaVersion1.1.0. Properties sólo jurisdiction, environment, incidentId y auditId, validadas por modelos derivados del contrato. No título/descripción/motivo/estado/datos sanitarios.
5. Cola servidor en memoria por proceso, sin tabla, fichero, outbox ni dependencia nueva: máximo200eventos/256KiB, lotes20 o10segundos desde primero, cuerpos48KiB/eventos2KiB. Tareas de preparación acotadas a16 y limpiadas al cerrar. Un único consumidor; errores sólo contadores saneados y sin recursión. El sink inicial comparte validación estructural/ACK del stub local, registra exclusivamente count/types y no realiza llamada HTTP con credenciales internas. No ampliar POST /telemetry/events para aceptar hechos de negocio del navegador.
6. Arrancar y cerrar productor mediante lifespan FastAPI. Sólo opt-in y clave de recurso válida; clave ausente deshabilita estos nuevos productores sin deshabilitar los cinco frontend. Captura/cola de mejor esfuerzo; puede perderse por saturación, timeout, fallo o caída tras commit. No prometer entrega durable ni exactamente una vez; se programa una vez por commit observado en el proceso. Configuración de producción/retención/transporte externo fuera de alcance.

## Archivos concretos

- Protegidos aprobados para este lote: backend/app/incidents/router.py (tres puntos post-commit, sin alterar lógica/auditoría); backend/app/core/config.py (campo SecretStr telemetry_resource_key opcional); backend/app/main.py (lifespan de productor opt-in).
- Nuevos en alcance aprobado: backend/app/telemetry/server.py (cola/ciclo de vida/sink), backend/app/telemetry/incident_producer.py (resolución y seudónimos), backend/tests/test_telemetry_server.py, backend/tests/test_telemetry_incident_producer.py.
- Pruebas existentes de incidencias/auth/status para regresión, README backend bilingües y SDD. Sin cambios a auth/policies, Management, migraciones, esquema público, endpoint browser, .env, dependencias, infraestructura, CI, Memory Bank o Rules.

## Criterios y validación antes de cerrar

- Crear/transicionar/asignar sólo tras commit: recepción del tipo correcto; auditoría persistente intacta; rollback/conflicto/denegación sin evento; refresh fallido tras commit no convierte el hecho en inexistente.
- Región desde clínica real: US/UK aceptados por el mismo backend; contexto cruzado/inactividad/ausencia/timeout descartados sin afectar operación confirmada.
- IDs opacos estables por propósito y región, sin UUID/secretos/texto; sesión/requestId null explícitos y contrato1.1.0 sin extras.
- Cola:20/10 no debounce, memoria global acotada, concurrentes conservados, cierre limpia timers/tareas; sink fallido no altera respuesta de negocio. Missing/invalid resource key fail-closed sólo en productor servidor.
- Suite unit aislada, integración PostgreSQL temporal sintética post-commit/rollback y regresiones auth/status/incidencias; revisión validate-delivery read-only. No tests contra base compartida.

## Autorización y límites

El desarrollador aprobó expresamente los tres archivos protegidos y el lote descrito mediante «apruebo, continua». Tecnología aprobó previamente el stub y Cumplimiento aprobó el seudónimo HMAC sin claves compartidas con frontend. Estas aprobaciones no constituyen autorización de producción, retención ni proveedor externo. No se modifica Memory Bank, Rules ni secretos.

## Evidencia ejecutada

- Suite backend aislada: 124 PASS (telemetry_server, telemetry_incident_producer, telemetry, telemetry_context, telemetry_identity, status y auth).
- PostgreSQL 16 temporal en tmpfs, migraciones y seeds sintéticos: creación/transición/asignación post-commit, rollback sin evento, conflictos/denegación sin evento, enlace HMAC con auditoría persistente y fallo del sink sin fallo de negocio: PASS.
- Regresiones PostgreSQL: se ejecutan workflows, HTTP authorization y productores en base recién inicializada. Un plugin temporal usa NullPool sólo en pruebas para evitar conexiones compartidas entre asyncio.run; la configuración de producción no cambia. El primer intento mezclaba fixtures del arnés previo y falló un conteo; la repetición usa base vacía.
- Prueba de integración permanente: test_real_postcommit_rollback_and_audit_links, requiere base aislada telemetry_validation y seeds sintéticos; nunca ejecutar sobre datos compartidos.

El sink valida/acepta en memoria y registra únicamente cantidad/tipos; no persiste ni reenvía a proveedor. Preparación limitada a 16 tareas con timeout 100 ms; sink limitado a 1 segundo. Las claves de cada región/entorno deben ser independientes también para recursos. La cola admite pérdidas; requestId sigue null y los otros 31 eventos permanecen abiertos.

## Reajuste vigente: API compartida

Un frontend y un backend, validado por Tecnología. IncidentProducer resuelve la clínica en la API compartida y selecciona claves de recurso/usuario US o UK antes de emitir. Los lotes mantienen región/binding separados. TELEMETRY_US_RESOURCE_KEY y TELEMETRY_UK_RESOURCE_KEY sustituyen la clave de recursos única en este modo; el resto del diseño post-commit/20/10 y límites permanece. El modo de región fija anterior se conserva sólo como compatibilidad. No se implementa transporte externo ni almacenamiento regional.

### Evidencia del reajuste compartido

133 pruebas backend PASS y dos pruebas PostgreSQL omitidas en ejecución sin DB, como corresponde a su guard de aislamiento. Integración/regresiones contra PostgreSQL16 temporal en tmpfs con seeds sintéticos:36 PASS, incluidas las dos pruebas DB. El mismo proceso API emite/revalida contextos US y UK y prepara eventos de servidor con claves diferentes; contexto cruzado/selector manipulado rechazados. Suite frontend:67 PASS sin modificar código UI. Plantilla:36 variables, cobertura de Settings/Compose y secretos vacíos; git diff --check PASS. Durante desarrollo se corrigieron validación de null interno en JWT, filtro de filas regionales y UUID UK de la prueba sintética. Ningún fallo pendiente en las comprobaciones enumeradas.

Comandos: podman compose --profile test run --no-deps --build --rm -e DATABASE_URL=postgresql+asyncpg://synthetic:synthetic@127.0.0.1:1/isolated test uv run --no-sync pytest tests/test_telemetry_shared.py tests/test_telemetry_server.py tests/test_telemetry_incident_producer.py tests/test_telemetry.py tests/test_telemetry_context.py tests/test_telemetry_identity.py tests/test_status.py tests/test_auth.py -q; node --test uis/backoffice/operational-incidents/telemetry/tests/*.test.mjs; podman compose -f /private/tmp/telemetry-business-compose.yaml up --abort-on-container-exit --exit-code-from test (arnés temporal con pytest -p telemetry_validation_plugin, NullPool sólo en pruebas aisladas). Recuentos se solapan, no se suman como tests únicos. El entorno temporal quedó detenido.

## Actualización lote2: lecturas de auditoría

Implementado audit_accessed para incident_audit y Management filtrado por clínica después de respuesta2xx finalizada, con aprobación expresa. Detalles/criterios/evidencia en [remaining-producers.md](./remaining-producers.md). Nueve tipos tienen productor al menos parcial; treinta sin productor. Auditoría global/inactiva sigue pendiente. No se amplía ingestión browser ni se cierra fase completa.

## Lote3 aprobado: mutaciones de clínicas

Implementado management_mutation_completed sólo para clínicas, tras commit confirmado y desde jurisdicción histórica persistida: creación after_data; resto before_data. Regla y archivos protegidos aprobados expresamente por el desarrollador. Detalle y evidencia en [management-producers.md](./management-producers.md). Validación:174 PASS sin DB (4 integraciones omitidas),79 PASS con PostgreSQL sintético y113 PASS de contratos/regresiones en una base aislada nueva; recuentos solapados. Diez tipos con productor al menos parcial,29 sin productor, auditoría global/otros recursos Management pendientes. Contrato1.1.0, permisos y auditoría persistente conservados. No despliegue de este lote, producción, exclusiones nuevas ni cierre global.
