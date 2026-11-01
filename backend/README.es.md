# API central de HealthCore

El servicio FastAPI compartido existente contiene incidencias, Management, catálogos, Compliance, autenticación y telemetría local. Sigue siendo un prototipo pre-MVP sintético. Alcance y límites vigentes: [estado de entrega](../docs/specs/telemetry-event-capture/delivery-status.md).

## Requisitos

- Python 3.12 y `uv` para ejecución local.
- Docker o Podman con Compose para ejecución en contenedor.

## Arranque local

Desde este directorio:

```sh
uv sync --frozen
uv run --no-sync uvicorn app.main:app --reload
```

Desde la raíz del repositorio, arrancar el contenedor:

```sh
cp .env.example .env
# Completar .env según la guía integrada enlazada abajo.
docker compose up --build
# Usuarios de Podman: podman compose up --build
```

Compose inicia PostgreSQL, aplica migraciones Alembic, carga los catálogos
provisionales y los datos sintéticos de referencia, y después inicia la API y
el backoffice estático. Abrir `http://localhost:8080` para la UI y
`http://localhost:8000/health` para comprobar la API. Las credenciales de base
de datos y la clave JWT se generan localmente en el `.env` raíz;
`.env.example` contiene solo los nombres de variables. Git ignora `.env`.

Detener con `docker compose down`. Añade `-v` únicamente si quieres borrar
intencionadamente el volumen local de PostgreSQL y todos sus datos.

## PostgreSQL, SQLAlchemy y Alembic

La conexión se recibe mediante `DATABASE_URL` y no se almacena en el repositorio. La URL debe usar el dialecto asíncrono de SQLAlchemy:

```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DATABASE?ssl=require
```

Con una base disponible, ejecutar las migraciones desde esta carpeta:

```sh
uv run --no-sync alembic upgrade head
```

Consultar la revisión actual:

```sh
uv run --no-sync alembic current
```

Sin `DATABASE_URL`, la API puede arrancar y responder `/health`, pero Alembic y las operaciones de base de datos fallarán explícitamente porque necesitan una conexión.

DATABASE_URL del .env raíz debe usar el hostname del servicio `db`. No incluir credenciales reales en
`env.example` ni en Git.

Después de aplicar las migraciones, cargar los catálogos con:

```sh
uv run --no-sync seed-catalogs
```

La imagen instala la API como paquete y genera el ejecutable a partir de
`[project.scripts]`. Con Podman puede ejecutarse dentro del contenedor:

```sh
podman compose exec backend uv run --no-sync seed-catalogs
```

Documentación en inglés: [README.md](./README.md).

## Stack contenedorizado integrado

El Compose raíz inicia PostgreSQL, aplica las migraciones existentes y los
seeds sintéticos mediante `db-init`, y después inicia la API compartida,
Next.js en el puerto 3000 y el backoffice estático en 8080 (Management en
`/management/`). Todos usan el `.env` raíz y la misma base de datos. Consulta
la [guía](../frontend/README.es.md).
`GET /status` ejecuta `SELECT 1`, devolviendo HTTP 200 con
`{"status":"ok","database":"connected"}` o HTTP 503 con
`{"status":"error","database":"unavailable"}`. `/health` no cambia.
Python 3.12 conserva la restricción del paquete existente. Los requisitos
fijados se comparan con uv.lock y se instalan con uv pip; uv sync instala
el proyecto. La etapa test incluye las dependencias de desarrollo.

Pruebas de estado sin PostgreSQL: `uv run --no-sync pytest tests/test_status.py -q`.
Suite completa desde la raíz: `docker compose --profile test run --rm test`.
La suite modifica registros sintéticos: usar solo la base local de desarrollo.

Los contratos de lectura de Incident y ComplianceReview son independientes de
los esquemas de entrada y conservan los campos publicados. Las pruebas de
contrato comprueban los campos exactos, el filtrado de atributos ORM y los
esquemas de las rutas; las pruebas HTTP de Management también comprueban los
contenedores de colecciones y las respuestas de escritura.
Las comprobaciones de Management cubren las once operaciones OpenAPI,
paginación y filtros de auditoría, además del rechazo de campos gestionados
por servidor en los PATCH de valores de catálogo y clínicas.

## Política de respuesta de auditoría

La política aprobada para el entorno sintético conserva identificadores,
referencias y timestamps. Los snapshots utilizan allowlists por evento y
validación estricta de Pydantic. Los valores no nulos de title, description y
label en snapshots, y los motivos de auditoría Management e historiales de
incidencias, se devuelven como `[REDACTED]`; null sigue siendo null. Se excluyen
campos desconocidos o inválidos. `_redacted: true` dentro del snapshot señala
contenido ocultado. Eventos desconocidos o listas raíz devuelven sólo ese
marcador; se conservan listas jurisdiction_ids en eventos de cobertura. Las
referencias históricas de revisión `"None"` conservan su representación original.
La misma proyección se aplica a eventos actuales e históricos, sin reescribir
registros ni cambiar retención o permisos. Las claves técnicas siguen visibles
bajo el acceso existente; validar su sintaxis no detecta de forma general
secretos incorporados en valores de identificadores. El backoffice conserva
la presentación de motivos, ahora como el marcador de redacción.

Cierre de serialización (2026-10-31): 145 pruebas superadas con PostgreSQL sintética; 28 operaciones y rutas de documentación verificadas. Las anotaciones OpenAPI describen errores existentes (detail string o lista de validación), sin cambiar su ejecución. Véase ../docs/serialization-audit.md para redacción aprobada, mediciones, pruebas manuales Swagger y límites. No implica aprobación de producción.

## Caché TTL de catálogos (desarrollo sintético)

Catálogo activo: 60 s; páginas de valores Management: 30 s, JSON por worker.
Cada petición autentica/autoriza y consulta metadata del catálogo. Claves digest
de identidad/rol/área, catálogo, version+updated_at, namespace y página.
Create/update/activation existentes avanzan generación; entradas antiguas quedan
inaccesibles. Fechas/flags del catálogo activo se filtran en UTC en cada hit,
incluso activaciones futuras. No se almacenan sesiones ORM ni peticiones.
Límites: 256 entradas, 8 MiB de payload JSON y 256 KiB por entrada; 64 locks fijos,
espera máxima 2 s antes de bypass al origen. Errores fuente se conservan.
Escrituras externas deben avanzar metadata o usar bypass. Sin aprobación de
producción, Redis, cambios de auth/auditoría/migraciones.
Pruebas: `podman compose --profile test run --no-deps --build --rm test`.
Benchmark explícito (una línea): `podman compose --profile test run --no-deps --rm test uv run --no-sync python tests/benchmark_caching.py`.
Inserta 200 valores sintéticos sin commit, revierte y verifica conteos.
Ver docs/CACHING_REPORT.md para resultados y límites.


Validación explícita de caché entre procesos (datos sintéticos, base aislada):
`podman compose --profile test run --no-deps --build --rm test uv run --no-sync python tests/validate_caching_workers.py`.
Requiere permiso PostgreSQL CREATE/DROP DATABASE; crea y elimina únicamente una
base temporal de validación. No se ejecuta durante la colección de pytest.
Evidencia: `docs/caching-workers.json` y `docs/CACHING_REPORT.md`.

## Receptor temporal de telemetría (activación explícita)

Existen `POST /telemetry/context` y `POST /telemetry/events`, autenticados. No se
introduce almacenamiento de eventos, migraciones, exportadores externos ni
instrumentación frontend. Sólo están habilitados los cinco tipos técnicos
frontend revisados; se rechazan hechos de negocio/worker aunque validen el JSON.
Los modelos se derivan de `app/telemetry/event-contract.json`, copia empaquetada
de la fuente única `docs/telemetry/event-schemas.json` (1.1.0). Actualizar ambos
a la vez y comprobar igualdad; la copia no es una fuente editable independiente.

Está deshabilitada por defecto. Configuración mediante el mecanismo de entrega
de secretos aprobado, sin versionar claves: `TELEMETRY_ENABLED`,
`TELEMETRY_PROCESSING_REGION` (US/UK), `TELEMETRY_USER_KEY`,
`TELEMETRY_SUBJECT_KEY`, `TELEMETRY_CLINIC_KEY`, `TELEMETRY_CONTEXT_KEY`,
`TELEMETRY_KEY_VERSION` (v1 por defecto), `TELEMETRY_CONTEXT_TTL_SECONDS`
(1..300; 300 por defecto). Las cuatro claves son distintas, de al menos 32 bytes
UTF-8, y diferentes de la clave JWT de login. Separarlas por entorno y región
es responsabilidad operativa; el servicio no crea ni distribuye secretos.
`TELEMETRY_ENDPOINT` es una referencia pública opcional del receptor para
consumidores de configuración; no modifica la ruta ni habilita reenvío backend.
Settings la carga; la aplicación sólo sirve `/telemetry/events` y no exporta.
Staging no exporta hasta incluirlo en el contrato aprobado.

Solicitar contexto con Bearer existente y cuerpo requerido `{"clinicId":null}`
para eventos generales, o UUID de clínica autorizada. El contexto firmado tiene
vínculos HMAC opacos, sin UUID operativo de usuario/clínica. Enviar el token en
`X-Telemetry-Context` junto con Bearer del mismo actor. Mantener credenciales e
identificadores en memoria frontend, nunca en logs. CORS local permite ese
header en los orígenes existentes del puerto 8080. El contexto general no usa
DB. El clínico reutiliza `referenceData:read`, lee maestros y rechaza clínicas
inactivas, inexistentes o de otra región. Al recibir revalida la clínica mediante
lectura de identidades y comparación de binding sin mapa persistido; medir su
coste antes de uso compartido.

Lotes de 1..20 eventos, límite de cuerpo real 48 KiB incluso sin Content-Length.
Validación atómica, sin reflejar payload en errores. HTTP 200 `{"received":N}`
significa validación, no persistencia. Logs sólo cantidad/tipos permitidos; no
se promete deduplicación durable. Header de contexto anterior válido permite
renovar sessionId; si expira o es inválido se rechaza. Sólo se acepta versión
actual de clave: rotación invalida contextos anteriores inmediatamente; no hay
gracia de claves previas ni renovación frontend implementada.

Pruebas aisladas sin DB de negocio:
`podman compose --profile test run --no-deps --build --rm -e DATABASE_URL= test uv run --no-sync pytest tests/test_telemetry.py tests/test_telemetry_context.py tests/test_telemetry_identity.py tests/test_status.py -q`.
Decisiones y trabajo frontend pendiente en `docs/specs/telemetry-event-capture/`.

La referencia TELEMETRY_ENDPOINT, si se configura, debe ser URL absoluta sin credenciales/query/fragment y path /telemetry/events; producción exige HTTPS. Referencia inválida deshabilita contexto sin cambiar la ruta ni reenviar eventos.

## Productores servidor de incidencias (opt-in)

Implementados `incident_created`, `incident_transitioned` y `incident_assigned` después del commit y antes del refresh. No emiten en rollback/conflicto/denegación. La auditoría persistente conserva su comportamiento.

Además de la configuración telemetry vigente, requieren `TELEMETRY_RESOURCE_KEY`: secreto servidor de mínimo 32 bytes, distinto de las cuatro claves telemetry y JWT, e independiente por región/entorno. Deriva subclaves HMAC separadas para incidentId/auditId; no exporta UUID originales ni texto de incidencias. Ausencia/configuración inválida deshabilita sólo este productor opcional. No se cambia `.env`.

La clínica se resuelve en sesión independiente de sólo lectura (máximo 16 tareas, timeout 100 ms). Región extranjera, clínica desconocida/inactiva o timeout descartan captura sin afectar el negocio. sessionId/requestId son null. Cola en memoria por proceso: 200 eventos/256 KiB, lotes hasta 20 o 10 segundos desde el primero, evento 2 KiB y cuerpo 48 KiB. Un consumidor, sink con timeout 1 segundo; errores descartan el lote sin reintentos locales. Lifespan limpia tareas/timers al cerrar. El sink local valida y registra cantidades/tipos, sin persistencia ni HTTP externo. Puede perder eventos por saturación/fallo/cierre; no garantiza entrega durable.

## Telemetría con backend compartido (arquitectura vigente)

Tecnología validó un frontend y un backend. Dejar `TELEMETRY_PROCESSING_REGION` sin definir o vacío para la configuración compartida. El modo anterior US/UK por instancia conserva compatibilidad, pero ya no es necesario. Clinic/Jurisdiction validada en servidor selecciona las claves regionales; no se confía en regiones ni claves declaradas por navegador. Ambas regiones usan las mismas rutas autenticadas y contrato público. El contexto firmado vincula región, actor y clínica y el receptor revalida ese ámbito.

Configurar cuatro claves generales (`TELEMETRY_USER_KEY`, `TELEMETRY_SUBJECT_KEY`, `TELEMETRY_CLINIC_KEY`, `TELEMETRY_CONTEXT_KEY`) y `TELEMETRY_US_{USER,SUBJECT,CLINIC,CONTEXT,RESOURCE}_KEY`, más sus equivalentes `TELEMETRY_UK_*`. Generar cada una por separado con `openssl rand -hex 32`; las14 deben ser distintas entre sí y de JWT. Los generales mantienen null y claves propias. RESOURCE regional habilita productores de incidencias; `TELEMETRY_RESOURCE_KEY` anterior sólo aplica a compatibilidad de región fija.

`TELEMETRY_ENDPOINT`, `TELEMETRY_US_ENDPOINT` y `TELEMETRY_UK_ENDPOINT` son referencias opcionales, no forwarding habilitado. La selección de contexto copia internamente la referencia regional. Los lotes locales de servidor mantienen separados región/clínica y el sink sólo valida/registra cantidades. No se añade exportación ni almacenamiento externo. Ubicación del despliegue/retención pendientes de Cumplimiento. `.env.example` raíz enumera todos los ajustes; Compose ahora inyecta las variables telemetry sólo al backend. Pruebas: `tests/test_telemetry_shared.py`; las pruebas PostgreSQL requieren base sintética aislada telemetry_validation.

## Telemetría de lectura de auditoría (alcance acotado)

El servidor emite audit_accessed después del último fragmento de una respuesta2xx satisfactoria de GET /incidents/{incident_id}/audit y de GET /management/audit-events sólo con resource_type=clinics y resource_id de clínica. Se conservan permisos audit:read y proyecciones existentes. Consultas globales u otros recursos no inventan clínica. Respuestas fallidas/denegadas/incompletas no emiten.

El productor resuelve/revalida clínica por separado y elige claves US/UK. Comparte ciclo de vida opcional de incidentes, límite16 tareas, timeout y cola regional20/10. Sin configuración del productor de incidentes también se deshabilita esta captura. Properties sólo jurisdiction/environment/surface; sin snapshots, texto ni IDs operativos. sessionId/requestId siguen null. Clínica inactiva/desconocida descarta captura sin afectar lecturas. El receptor browser sigue rechazando audit_accessed; sólo el sink interno lo admite. Entrega en memoria de mejor esfuerzo. Pruebas: tests/test_telemetry_audit.py; integración DB sólo en telemetry_validation sintética aislada. No activa producción.

## Telemetría de mutaciones de clínicas

management_mutation_completed se captura tras commit y antes de refresh, sólo al crear, actualizar, activar o desactivar clínicas. La auditoría persistida determina la jurisdicción: after_data al crear, before_data en las otras acciones. US→UK emite una vez en US; acciones posteriores usan UK. Una referencia histórica inactiva sirve sólo para clasificación; resolve_clinic conserva sus controles. Snapshot inválido se descarta sin fallback.

Comparte productor opcional, cuotas y cola20/10 existentes. userId y auditId usan HMAC regional exclusivamente servidor; no exporta snapshots, texto ni UUID operativos. Rollback, conflicto, denegación y PATCH vacío no emiten; fallos de captura no afectan negocio. El browser no puede enviar este hecho. Pruebas: tests/test_telemetry_management.py, integración sólo en PostgreSQL sintético telemetry_validation. Sin persistencia/forwarding adicional ni aprobación de producción.

## Finalización HTTP de lecturas de incidencias

api_request_completed se emite tras el cuerpo final enviado de GET detalle, history, assignment-history y audit de una incidencia autorizada. Properties cerradas: jurisdicción clínica revalidada, environment, route=incidents, statusCode y duración monotónica en ms desde entrada al middleware hasta envío final, excluyendo preparación posterior. requestId UUID exclusivamente interno, sin cabecera nueva ni valor del cliente; userId HMAC regional, sessionId null. /audit conserva además audit_accessed independiente.

Respuesta incompleta, actor/clínica ausente, rutas generales y /telemetry no emiten. Un error HTTP manejado con descriptor autorizado puede emitir su estado real. Captura/sink fallidos no afectan respuesta. Reutiliza límites16/100ms y cola20/10 opcional; entrega no durable. Pruebas test_telemetry_request.py, DB sólo sintética telemetry_validation. No amplía permisos, contrato1.1.0 ni producción.

## Contrato vigente de telemetría1.2.0

El catálogo permite jurisdicción null genuina en nueve tipos técnicos generales de servidor (autenticación, autorización, finalización API, caché, salud, integridad y diagnósticos). Con los cinco tipos browser previos son14 nullable;25 siguen exigiendo US/UK. Fallo de resolución clínica nunca cae a null. Admisión de productores separada: ingreso browser conserva sólo cinco tipos. Esta revisión no añade productores. Contexto/cuerpo usan1.2.0; payload1.1.0 falla validación, por lo que API/frontend se actualizan coordinadamente. Sin claves nuevas ni despliegue local. Detalles: docs/specs/telemetry-event-capture/general-technical-scope.md.

## Telemetría de autenticación y capacidades

La dependencia marca authentication_succeeded tras verificar el JWT: una captura por credencial vigente y proceso, no por petición ni login SSO. Deduplicación sólo en memoria mediante HMAC interno de propósito propio y expiry, máximo1024 sin evicción de vigentes. Reserva al aceptar en cola; fallo posterior puede perder el hecho, reinicio/múltiples procesos pueden repetirlo. Nunca guarda el token.

authentication_failed emite missing/invalid/expired con userId=null; authorization_denied sólo para rechazo de require_capability, con operación allowlist y actor HMAC general. Todos llevan jurisdiction=null y se capturan tras respuesta final enviada, sin cambiar errores o permisos. requestId interno compartido con finalización HTTP; /telemetry excluida, sin cabecera pública. Políticas de área/jurisdicción no instrumentadas. Comparte productor/cola opcional existente y sus claves, sin nuevos ajustes ni DB para captura general. Pruebas test_telemetry_security.py; integración sólo telemetry_validation sintética. Sin aprobación de producción.

## Salud bajo demanda y contadores de caché

service_health_checked observa sólo las llamadas existentes a /health y /status tras el cuerpo final enviado, con check liveness/database y outcome ok/failed/timeout. Conserva200/503, SELECT1 y manejo de errores; no agrega sonda ni timeout. userId/sessionId/jurisdiction null, requestId interno compartido y duración monotónica de finalización middleware. Fallo de envío o captura no altera el chequeo.

catalog_cache_observed corta cada300s los contadores hits/misses/bypasses de la caché compartida por proceso, sin reiniciarlos ni leer claves/contenido. Exporta diferencias y windowSeconds del intervalo observado. Baseline inicial excluye operaciones previas; contador inválido/disminuido descarta y rebasa, cola rechazada avanza baseline, cierre pierde ventana parcial. Hit ratio=hits/(hits+misses), denominador0 no disponible; bypasses separado. Sampler opcional único, arranque idempotente y cierre cancelado/esperado. Eventos anónimos/null, cola20/10 existente sin entrega durable. Pruebas test_telemetry_health_cache.py y test_caching.py; integración DB sólo sintética telemetry_validation.

## Diagnósticos independientes de telemetría

telemetry_contract_rejected observa rechazos de esquema del receptor sólo tras completar la respuesta422, o eventos inválidos de la cola normal de servidor. Emite ámbito general/null anónimo sin leer campos rechazados. Conserva respuestas401/403/413/503 y admisión browser. requestId interno sólo para respuesta de ingreso completada.

telemetry_delivery_failed captura saturación de cola normal con jurisdicción validada, o un resultado terminal timeout/unavailable por lote validado. Cola diagnóstica opcional separada y sink validador de cantidad/tipos evitan recursión cuando cualquiera falla. Ambos conservan lotes20/10,200 eventos/256KiB incluyendo vuelo,2KiB por evento,48KiB por cuerpo y un intento de sink1s; sin reintentos, persistencia o forwarding. Fallo diagnóstico sólo afecta contabilidad local; cancelación/cierre no emite fallo. Pruebas test_telemetry_diagnostics.py; integración DB sólo telemetry_validation sintética. Sin activación de producción.

## Integridad del contrato al arrancar

data_integrity_checked se ejecuta una vez por productor opcional válido al iniciar el lifespan de la API, con check=event_contract. Lectura acotada128KiB: rechaza JSON inválido/duplicado y compara contrato empaquetado con catálogo/versión/discriminador cargados y esquemas de modelos regenerados. Acepta orden equivalente de objetos JSON. Emite jurisdiction/userId/sessionId/requestId=null y outcome=ok/failed por cola normal de servidor, sin acceso DB ni análisis de datos clínicos.

Telemetría deshabilitada/inválida omite chequeo; productor vivo no repite intento. Fallo o captura rechazada no impide arrancar API; entrega best effort. Verifica coherencia interna paquete/runtime, no firma del artefacto, sincronización frontend, referencias ni cobertura histórica. Contrato que impide importar puede bloquear API antes de observar. Pruebas test_telemetry_integrity.py y regresiones lifespan en telemetry_validation sintética. Sin nuevas claves, endpoints, despliegue o activación de producción.

## Admisión de diagnósticos browser

POST /telemetry/events admite además telemetry_contract_rejected y telemetry_delivery_failed sólo con producer=frontend, jurisdiction/requestId=null y contexto general firmado. Conserva comprobaciones Bearer/session/user-HMAC/environment. Rechaza contexto clínico y afirmaciones api/worker. Los cinco tipos browser ordinarios mantienen allowlist separada; hechos internos servidor siguen inaccesibles al navegador. Sin cambio de esquema/versión públicos. Pruebas test_telemetry_frontend_diagnostics.py; reserva y no recursión frontend en README compartido. Sin despliegue local de este lote.

## Evidencia de activación local conjunta

El2026-11-01 terminó la reconstrucción autorizada backend/backoffice sin db-init ni inicialización DB. API health/status200, contrato1.2.0 e integridadok. Chrome verificó lectura de incidencias y cuatro catálogos Management con credenciales sintéticas. Módulo browser real envió20 eventos de navegación,21 diagnósticos de esquema y uno de entrega (403 simulado sólo en adaptador experimental); envíos reales200. Buffers cerrados vacíos, sin exportar claves; pestañas de prueba cerradas. Detalles docs/specs/telemetry-event-capture/local-activation-validation.md. Sólo prototipo local, sin producción ni cobertura completa.
