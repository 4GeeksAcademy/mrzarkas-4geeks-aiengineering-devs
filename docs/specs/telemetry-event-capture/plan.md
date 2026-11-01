# PLAN — Telemetry Event Capture, Fase 2

**Estado vigente — revisión final local (2026-11-01):** implementado y validado dentro del alcance reducido autorizado. Contrato1.2.0,39 tipos:19 con fuente al menos parcial y20 DEFERRED_NO_SOURCE aprobado. Un frontend/backoffice compartido y un backend; HMAC exclusivamente servidor, jurisdicción clínica autoritativa y null técnico general. Captura20/10 efímera, recepción no durable. Admisión browser5 + dos diagnósticos internos frontend restringidos; servidor admite sus hechos por canal propio. Backend/backoffice locales actualizados y Chrome sintético validado.

**La cobertura integral original NO está terminada:**9 de los20 diferidos son obligatorios; TEL-FR-018 sigue pendiente. Hay además brechas de los19 tipos actuales, detalladas en [delivery-status.md](./delivery-status.md). La aprobación de aplazamiento no equivale a requisitos satisfechos, producción ni cumplimiento normativo.

La matriz y estados vigentes están en [delivery-status.md](./delivery-status.md); la cronología que sigue conserva las propuestas y evidencias de cada revisión. Sus menciones a «actual», TODO/BLOCKED,1.1.0, cinco productores o pruebas NOT_RUN corresponden al momento histórico de esa sección y no sustituyen este estado vigente. No se han reescrito Memory Bank ni fuentes empresariales.

## Historial del diseño y de los lotes (referencia temporal)

**Fecha:** 2026-11-01. **Rama:** `feature/telemetryEventCapture`. **Estado:** DRAFT / BLOCKED.
Referencias: [spec](./spec.md), [tasks](./tasks.md), [contrato candidato Fase 1](../../telemetry/event-schemas.json), [plan Fase 1](../../telemetry/telemetry-plan.md).

## Implementación verificada del stub — alcance actual

Tecnología aprobó en conversación los archivos/backend, endpoints y configuración del stub enumerados. Cumplimiento aprobó el uso de HMAC porque no se entregan claves al frontend; se registra exactamente ese alcance, sin atribuir aprobación de producción, retención, transferencias o proveedor de secretos. Implementación actual: módulo backend/app/telemetry, modelos derivados del contrato 1.1.0 empaquetado, contexto firmado con bindings opacos, claves separadas, ingestión segura y no persistente. CORS sólo añade X-Telemetry-Context a los orígenes locales ya permitidos. No .env/deploy/migraciones/dependencias/auth policies modificados.

Cinco productores frontend técnicos aceptados, resto de 39 modelos validables pero emisión browser rechazada. Contexto general sin DB; contexto clínico resuelve y revalida Clinic/Jurisdiction en sólo lectura usando referenceData:read existente. No permisos nuevos; binding clínico se encuentra por lectura de IDs sin mapa persistente. Medir ese coste antes de uso compartido. Lotes de 1..20, cuerpo máximo 48 KiB incluso chunked; errores no reflejan payload, log sólo cantidad/tipos; received no es escritura ni dedup durable.

Configuración opt-in y fallos seguros: cuatro claves secretas diferentes >=32 bytes, región requerida, TTL 1..300 s, endpoint de referencia validado sin forwarding; staging no exporta. Sólo se acepta versión de clave actual, sin gracia de versión previa: rotación invalida contextos anteriores. No renovación frontend, batching/retry/keepalive frontend ni instrumentación implementados. El diseño previo de keyring/gracia se mantiene como fase futura, no capacidad actual.

Se actualizó el censo existente backend/tests/test_auth.py de 28 a 30 operaciones para incluir los endpoints nuevos; no se cambiaron permisos ni comportamiento de autenticación. Fuente documental de contrato y asset empaquetado se comparan durante validación. README backend bilingües explican límites/config/pruebas. No afirmar tests de DB de negocio, DevTools o despliegue como ejecutados.


## Revisión 1.1.0 — decisiones autorizadas y alcance de Fase 2

El desarrollador aprobó en esta sesión HMAC en servidor, clínica como fuente de jurisdicción, null para eventos generales, lotes de 20 o 10 segundos, la propuesta inicial de instalaciones regionales separadas (sustituida por backend compartido en la revisión actual) y fetch con Bearer/keepalive como sustitución de Beacon. Autorizó consolidar SDD y actualizar/validar el contrato. Es aprobación de estas decisiones y de la modificación documental; no atribuye una revisión a Claire ni autoriza datos reales, producción, configuración de despliegue o código.

**Contrato vigente de esta revisión documental:** schemaVersion 1.1.0. Es sustitución de una propuesta no desplegada; consumidores futuros deben validar esa versión. El catálogo conserva 39 nombres y sus allowlists. Se permite jurisdiction null únicamente en navigation_viewed, frontend_timing_measured, application_error_observed, session_started y session_ended. La propiedad es requerida. Los otros 34 eventos conservan US/UK obligatorio. Un evento de clínica con región desconocida se rechaza; NaN se rechaza antes de JSON.stringify, nunca se normaliza a null. Null indica ausencia genuina de clínica, no falta de configuración.

Decisión vigente, validada por Tecnología y solicitada por el desarrollador: un frontend y un backend compartidos. Sustituye la propuesta anterior de instalaciones regionales separadas. La API resuelve la clínica y selecciona en servidor las claves HMAC US/UK; firma y revalida el contexto con ese ámbito. Los eventos generales sin clínica conservan jurisdiction null y claves propias, sin atribuirles US o UK. Un contexto clínico no admite eventos de otra jurisdicción. El stub sigue local y no persistente; las referencias de destino regional no implementan forwarding ni aprueban procesamiento/almacenamiento externo. La ubicación del backend y ambos flujos requiere evaluación de Cumplimiento antes de activación real.

HMAC-SHA256 en servidor sobre UUID autenticado, con claves distintas por entorno/región/finalidad y salida ps_+64 hex. La misma identidad puede tener seudónimos distintos US/UK. No entregar claves ni UUID operativo al cliente de telemetría; no confiar en userId suministrado sin comprobarlo frente al actor autenticado/contexto. Gestión de claves, rotación y revisión de Cumplimiento siguen pendientes. Dedup futuro debe usar región de procesamiento confiable + eventId, no jurisdiction null como partición global. No dedup durable en el stub.

Perfil UI Fase 2: cola en memoria, lote máximo 20, deadline 10 s desde primer pendiente sin debounce; fetch con Bearer y keepalive al ocultar, siempre best-effort. Sustituye Beacon en requisitos de esta fase; no modifica política de autenticación ni CORS durante esta entrega. STREAM/sondas/reporting fuente siguen fuera de este transporte UI y no se declaran cubiertos.

**Cobertura inicial propuesta para revisión final:** navegación, errores frontend y Web Vitals compatibles en backoffice existente; session_started/ended sólo tras contexto autorizado. Incidencias/auditoría/auth/cache son productores servidor que requieren autorización concreta posterior; inventario/sondas/alertas/KPI/agregadores ausentes quedan aplazados, sin declarar satisfechas sus obligaciones. No crear fuentes ficticias para cerrar matriz.

Pruebas documentales: positivos US/UK en 39 eventos; null válido sólo en cinco, null inválido en 34, missing/NaN/string NaN/región inválida rechazados. Clasificación structural no comprueba clínica, autenticación o destino: esas invariantes necesitan tests de contexto del servidor al implementar. Staging sigue sin enum autorizado y no exporta hasta decisión de contrato.


## Arquitectura actual verificada

| Aspecto | Evidencia vigente | Implicación |
|---|---|---|
| API central | backend/app/main.py monta auth/catalogs/compliance/incidents/management; backend/pyproject.toml conserva healthcore-central-api | Trabajar en backend/app, no recrear services/central-api ni otra API. |
| Backend | FastAPI, Pydantic, SQLAlchemy async, Alembic, Python >=3.12,<3.13; uv y lock existentes | TelemetryEvent y router sólo en API actual; sin modelos ORM/migración. |
| Configuración | backend/app/core/config.py: BaseSettings, get_settings cache, .env, APP_ENVIRONMENT | TELEMETRY_ENDPOINT no existe; incorporación futura es protegida. No leer/imprimir secretos. |
| Autenticación | auth/dependencies.py HTTPBearer, Actor UUID, role, area_id; JWT temporal dev/test | No hay sesión servidor/seudónimo/jurisdicción en claims. No desactivar controles ni hacer pública ingestión. |
| CORS | main.py permite orígenes localhost/127.0.0.1:8080 en dev/test, GET/POST/PATCH, Authorization/Content-Type | Port 3000 directo no está autorizado; proxy de historial Next existente no es proxy telemetry. |
| Incidencias | uis/backoffice/operational-incidents/index.html + app.js ES modules, hash routing #/incidents/new/detail | JavaScript nativo, sin React/Next/TypeScript/bundler. api() centraliza fetch, connect/disconnect guarda token/claims en memoria. |
| Management | uis/backoffice/management/index.html, script inline y request() con fetch, controles de recursos | HTML/CSS/JS de lectura, no SPA router común ni sesión compartida con incidencias. No persistir JWT. |
| Next existente | frontend/package.json Next 16.4.3/React 19.3.1; app/page.js landing y app/internal/incident-history/workspace.js | Aplicación separada, JavaScript; adaptador opcional interno, no migrar backoffice a Next. |
| Historial Next | app/api/incident-history/route.js usa BACKEND_URL, Authorization y no-store | Lectura autorizada existente; no ampliar a telemetría sin alcance aprobado. Token React en memoria. |
| Errores | api/request maneja error HTTP en UI; lazy-error-boundary.js cubre chunk; backend error_contracts.py documenta errores | No gestor global de telemetría encontrado. No copiar error.message/stack/input al envelope. |
| Logging/observabilidad | Uvicorn runtime, contadores locales CatalogCache en backend/app/catalogs/cache.py | No bus ni colector; contadores/auditoría no equivalen a instrumentación. No librería analytics/OTel requerida. |
| Tests | backend/tests pytest/httpx; integration marca PostgreSQL; frontend scripts sólo dev/build/start; utilidades chronology.mjs | No runner de unit frontend configurado. Proponer Node node:test sin dependencias; DOM mediante adaptadores/mocks y navegador manual. |
| Desarrollo | README frontend/backend: API 8000, estático 8080/management, Next 3000, Compose comparte PostgreSQL sintética | Arranque Compose ejecuta seeds/migraciones; no ejecutarlo ahora sólo para documentos. |

La documentación histórica de plantilla dice que no hay apps y current-state conserva services/central-api; se contrasta con código y README vigente. El traslado no se deshace. No existe inventario en los routers/modelos vigentes; su spec en Memory Bank es propuesta.

## GAP respecto a Fase 1

Fase 1 ofrece 39 contratos documentales; revisión 1.1.0 con decisiones autorizadas, pendiente revisión completa y operativa. Falta receptor, TelemetryService, identidad HMAC regional, propagación HTTP requestId, política de productor/región y tests de captura. No hay módulos de inventario, agregadores de citas/facturación/satisfacción/RRHH ni sondas/alertas. Allowlists incluyen hechos de servidor que no se pueden generar correctamente en navegador. Batching de Fase 2 no satisface monitorización clínica ni todos los KPI en tiempo real. Véase B01–B08 en spec para resolución y propietarios.

## Arquitectura objetivo: hipótesis pendiente del gate

Este flujo sólo muestra responsabilidades candidatas. No es diseño definitivo ni selección de un mecanismo de contexto/autenticación. La interfaz pública de captura es track(eventType, properties); lifecycle/transporte/contexto son internos, no APIs de captura alternativas.

```mermaid
flowchart LR
  G[Gate: contrato y contexto aprobados] --> C[Adaptador del frontend existente]
  C --> T[track: valida y crea envelope]
  T --> Q[Cola en memoria]
  Q --> B[Un lote en vuelo]
  B --> H[Transporte autorizado]
  H --> R[API actual: telemetry/events]
  R --> V[Validación íntegra y resumen seguro]
  V --> A[200 received N; sin persistencia]
  B --> E[Retry acotado o descarte]
  F[Fuentes servidor o futuras] -. fuera del productor UI .-> G
```

## ADR-001 — Ubicación del TelemetryService

**Estado:** propuesta pendiente B01/B08. Evidencia: dos backoffice nativos independientes y Next en carpeta separada. Alternativa menos invasiva: núcleo JS sin DOM en `uis/backoffice/telemetry/telemetry-service.mjs`, transporte y adaptadores en misma carpeta; import relativo desde incidencias y Management. No crear src/services ni React. Antes de aprobar, comprobar que el servidor estático puede servir la carpeta común; el HTTP server del README que sirve sólo operational-incidents no lo permite. Si exige modificar Nginx/Compose, obtener autorización protegida y actualizar ambos README. Alternativa: empaquetar en packages tras acordar distribución, sin copiar dos servicios divergentes. Next sólo recibe un adaptador si se aprueba su inclusión; no importar assets no servidos como solución implícita.

## ADR-002 — Sesión e identidad

**Estado:** BLOCKED B03/B04/B08. Reusar conexión/desconexión real de incidencias y estado React del historial como fuente de lifecycle. SessionId candidato UUID por conexión en memoria; recarga o desconexión destruye contexto, no sessionStorage/localStorage/cookies. Management necesita delimitar conexión explícita en su flujo vigente antes de emitir session_started/ended; una carga no es login. UserId requiere seudónimo HMAC resuelto en servicio autorizado regional. No leer JWT sub como userId ni generar HMAC en cliente. Backend Actor valida autenticación, pero no dispone de endpoint de contexto telemetry: diseñarlo supondría alcance protegido adicional. Mientras falta contexto válido, deshabilitar exportación. No cerrar B03 haciendo userId null en evento autenticado. Purga de pendientes al cambiar actor/región; lote activo no se reasigna a otras credenciales. Ningún tratamiento de datos real autorizado.

## ADR-003 — Batching y concurrencia

**Estado:** umbral de 20 eventos y plazo de 10 s aprobados; algoritmo y cuotas adicionales pendientes B01/B08. Separar pending (capturas nuevas) de inFlight (snapshot inmutable) y backoff. Estados: disabled, idle, sending, retryWait. Un scheduler interno y como máximo un transporte HTTP activo.

| Estado / trigger | Acción candidata | Invariante |
|---|---|---|
| disabled / track | descartar con contador local acotado | cero red, memoria acotada |
| idle / track válido | anexar snapshot a pending, iniciar deadline sólo si no existe | timestamp e ID fijados al capturar |
| idle / >=20 o deadline | retirar prefijo <=20 y <=bytes de pending; asignar inFlight; enviar | pending recibe nuevos eventos independientemente |
| sending / track | añadir a pending | inFlight no cambia |
| sending / ACK válido | liberar inFlight; evaluar umbral/deadline de pending | ACK no acredita persistencia |
| sending / fallo recuperable | conservar lote idéntico y retry count; entrar retryWait | ningún reinserto que mezcle IDs nuevos |
| retryWait / deadline retry | reenviar inFlight con mismo payload | un transporte y contador acotado |
| sending / fallo permanente o agotado | descartar sólo inFlight; volver idle | pending intacto |
| cualquier / desconexión o contexto inválido | cancelar timer/retry, invalidar generación y purgar contexto | respuestas tardías no afectan sesión nueva |

Timer candidato: primer evento pendiente fija fecha de elegibilidad +10000 ms, nuevos track no reinician plazo. Con inFlight/backoff, marcar pendiente vencido sin arrancar otro fetch; al liberar transporte enviar prefijo vencido o de >=20 inmediatamente. Si queda remanente no vencido, conservar antigüedad del primer evento remanente, nunca reiniciar continuamente. Suspensión del event loop no garantiza envío wall-clock puntual. No debounce de 10 s. Propuesta de cuotas: 200 eventos/256 KiB totales, 2 KiB/evento, 48 KiB/lote y 20 eventos; revisar overhead/bytes UTF-8 incluyendo wrapper. Si excede cuota rechazar evento nuevo, no expulsar inFlight. Esto es decisión candidata con pérdida visible, no cumplimiento de conservación crítica Fase 1.

## ADR-004 — Visibilitychange y fetch keepalive

**Decisión del desarrollador aprobada:** sustituir Beacon por fetch con keepalive y Bearer. Mantener JSON/Content-Type y endpoint de la instalación regional; no hacer pública ingestión ni tokens en URL/body. No cambiar CORS durante el hito documental. Límites de bytes/timeout y serving deben concretarse antes de implementar.

Hidden instala un solo listener con cleanup; intenta enviar pending sin reenviar inFlight. Sólo HTTP 200 con received=N observable confirma recepción validada; cierre puede impedir observar la respuesta o completar el envío. No se promete persistencia ni entrega absoluta. Error/abort puede producir recepción desconocida y retry duplicado; mantener eventId. Aplicar cuota de payload keepalive (48 KiB candidata, no garantía del navegador) y un transporte activo. Ausencia de capacidad o error se gestiona sin afectar negocio; no fallback Beacon que pierda Bearer.

## ADR-005 — Validación y catálogo único

**Estado:** propuesta, B01/B08. JSON Schema de Fase 1 es única fuente; no lista escrita a mano en JS/Python. Evaluar derivación/generación determinista de índices de eventos y modelos/validadores desde el documento, con fingerprint y prueba de parity. Artefactos generados son outputs, nunca una segunda fuente editable. Core rechaza datos imposibles de JSON (ciclos, BigInt, NaN/Infinity), desconocidos, extras y required ausentes; copia defensiva. Python TelemetryEvent valida envelope, properties discriminadas y reglas semánticas (null según productor, región/environment); Pydantic por sí solo no reproduce todo draft-07 ni valida HMAC autorizado.

Si stdlib/generación no cubre todo vocabulario, presentar dependencia concreta para autorización antes de añadirla; no escribir validador parcial y llamarlo equivalente al contrato completo. Declarar cobertura real y ejemplos positivos/negativos de los 39 candidatos al cerrar B01. No serializar validación fallida con input/ctx en 422. T-N13 exige respuesta segura propia del receptor sin cambiar handler global de negocio.

## ADR-006 — Configuración

**Estado:** pendiente B04/B08. Ruta solicitada fija `/telemetry/events`, módulo candidato backend/app/telemetry/router.py; no concatenar TELEMETRY_ENDPOINT como prefix arbitrario. Variable backend candidata en Settings expresa la referencia de receptor temporal y futura transición, nunca URL de reenvío activa en Fase 2. Resolver finalidad operativa y conducta ausente/inválida explícitamente antes de implementarla. No modificar `.env` o deploy durante este hito.

Frontend estático: candidato config.mjs público con valor runtime telemetryEndpoint, independiente de instrumentación y sin secretos. Forma de inyección/distribución necesita aprobación si toca Nginx/Compose. Desarrollo: valor ilustrativo http://localhost:8000/telemetry/events, origen UI permitido 8080; servidor no usa localhost del navegador ni BACKEND_URL interno como URL pública. Next opcional usa NEXT_PUBLIC_TELEMETRY_ENDPOINT en build (no runtime automático); proxy sólo tras aprobación y política de auth. Entornos compartidos requieren HTTPS/destino regional revisado; ningún endpoint producción se selecciona. Staging no está en enum de JSON: sin resolución contractual no exportar ni hacer mapping silencioso.

## ADR-007 — Correlación

**Estado:** BLOCKED B03/B04/B08. eventId identifica captura; sessionId conexión; operationId identifica operación de negocio; requestId identifica petición HTTP, no lote telemetry ni evento. No generar requestId arbitrario para navegación: null. API debe validar/generar UUID en frontera y propagar contexto aprobado; main.py no contiene middleware requestId y CORS no permite header adicional actualmente. Un adaptador HTTP interno puede fijar contexto de correlación durante emisión de evento sin cambiar firma pública track(eventType, properties); no usar una variable global que mezcle promesas concurrentes. Diseñar entrega de contexto por operación/scope y test de dos peticiones concurrentes después de autorizar propagación. No colar requestId como extra en properties. Evento HTTP de negocio no toma el ID de POST telemetry; retries conservan ambos IDs originales.

## ADR-008 — Fase 3

**Estado:** propuesta. Mantener interfaz track, envelope y productores al sustituir receptor. Separar validación/ACK/transporte del almacenamiento futuro. received cuenta validación en stub, no escritura. Fase 3 debe aprobar retención, dedup, persistencia y semántica de confirmación; no prometer que cambiar URL proporciona outbox/exactly-once ni cierre de todas las pérdidas. Si contrato ACK cambia, versionarlo y adaptar transporte interno sin cambiar track; autorización requerida. Auditoría persistente operacional actual sigue siendo independiente de telemetría efímera.

## Diseño concreto propuesto — contexto de servidor y claves

**Estado:** especificación técnica para revisión, no implementación ni aprobación de Cumplimiento. Concreta las decisiones del desarrollador sin sustituir autenticación, ampliar permisos clínicos o introducir dependencias. PyJWT y HMAC/hashlib existen en el stack Python; modelos Clinic/Jurisdiction y Actor son las fuentes vigentes. No generar claves ni leer .env durante esta entrega.

### Contrato de contexto separado del envelope 1.1.0

Ruta futura propuesta: `POST /telemetry/context`, con Authorization Bearer existente, JSON cerrado `{ "clinicId": UUID | null }`. Campo requerido: null significa solicitar contexto general de la instalación. El UUID de clínica sólo sirve para resolución autorizada, no se añade a properties ni al envelope de eventos ni se escribe en logs. No incluir actorId/userId/region de cliente en la solicitud. Respuesta propuesta cerrada HTTP 200:

| Campo | Tipo / origen |
|---|---|
| contextToken | string firmado por servidor; no es token de login ni secreto de firma |
| sessionId | UUID generado por servidor para la conexión de telemetría |
| userId | ps_+64 hex HMAC del Actor autenticado |
| jurisdiction | US/UK de clínica o null de contexto general |
| schemaVersion | constante 1.1.0 |
| expiresAt | fecha UTC; caducidad de contexto, no del evento |

Cache-Control: no-store; no response clínica/nombre/UUID de actor/claves ni regionId adicional. Esta ruta no existe ahora y constituye contrato público nuevo protegido: autorización concreta antes de implementar. El contexto firmado es credencial sensible aunque no reemplace Bearer: sólo memoria, nunca URL/storage/log/HAR compartido.

El servidor verifica Bearer mediante get_current_actor existente. Con clínica: resuelve Clinic.jurisdiction_id → Jurisdiction.key y confirma US/UK, clínica/jurisdicción válidas para la operación y región igual a instalación. No asumir que un rol autoriza cualquier clínica: reutilizar autorización aplicable a la operación/incidencia; la política actual no demuestra un ámbito clínico universal. Si no puede acreditarse acceso, denegar contexto clínico en vez de ampliar permisos. Contexto general no permite acceso a datos operativos adicionales.

Respuestas propuestas: 401 Bearer ausente/inválido, 404 para clínica inexistente o inaccesible sin distinguirlas al cliente, 422 para body/UUID o referencia clínica no válida, 403 para contexto regional no permitido cuando revelarlo sea admisible, 503 si falta configuración/clave o el servicio de resolución está indisponible. Mensajes genéricos sin token/payload/identificadores. Orden y exposición final revisados con seguridad; los 404/403 no deben revelar pertenencia de clínicas prohibidas.

### Token de contexto y validación del lote

Contexto JWT propio firmado HS256, con clave exclusiva de firma de contexto (distinta de JWT de login y de HMAC de seudónimos). Verificación fija de algoritmo, issuer y audience; kid restringido al keyring local revisado, sin claves externas elegidas por el cliente. El token está firmado, no cifrado: sus claims son legibles. Por eso no incluye UUID operativo ni clínica UUID.

Claims mínimos propuestos: subjectBinding HMAC exclusivo sobre Actor.id, clinicBinding HMAC exclusivo sobre Clinic.id o null, sid UUID de sesión, processingRegion US/UK de Settings confiables, environment, jurisdiction US/UK/null, pseudonymVersion, iat/exp, iss/aud. Bindings tienen claves/prefijos distintos del userId y no se exportan en eventos. El receptor recomputa subjectBinding del Bearer autenticado; no requiere UUID original en token. Para clínica, resolución/autorización ocurre al emitir contexto y un binding no es reversible: nunca inventar lookup de HMAC o mapa persistente. La revalidación de hechos clínicos se define abajo antes de habilitarlos.

Cada envío usa Authorization Bearer + `X-Telemetry-Context` y JSON `{events:[...]}` sin cambiar envelope ni allowlists. Este header necesita revisión expresa de CORS (`main.py` hoy no lo permite): no modificar CORS por inferencia. Fetch keepalive puede enviar ambos headers; su tamaño también consume presupuesto keepalive. Receptor valida Bearer y contexto (firma/caducidad/issuer/audience/keyring), compara subjectBinding derivado del Actor, sid/sessionId de todos los eventos, jurisdiction/environment/schemaVersion y userId calculado con pseudonymVersion autorizado. Comparaciones HMAC constantes con hmac.compare_digest. Región del contexto debe coincidir con Settings confiables del receptor; ningún token de otra instalación se acepta.

Un lote pertenece a un solo contexto: no mezclar clínica A/B ni general. En contexto general, sólo los cinco eventos nullable del catálogo y jurisdiction null; en contexto clínico, jurisdiction US/UK nunca null. No deducir general de un evento clínico fallido. UserId requerido no nulo en eventos humanos de esta interfaz autenticada; null queda reservado al productor anónimo/worker aprobado de Fase 1, no se habilita un colector anónimo. El token acredita resolución y ámbito al emitirse, no acredita que una mutación ocurrió ni que sigue autorizada si datos cambian. Para hechos de negocio usar productor servidor post-commit y autorización vigente; no otorgar autoridad transaccional al navegador.

Para contexto clínico y una clínica cuyo permiso/estado cambie después de emisión, definir revalidación al usarlo: en Fase 2 inicial sólo fuentes generales frontend; no habilitar hechos clínicos hasta acordar comprobación vigente sin tabla/mapa de telemetría persistente. Esta limitación es explícita y no se resuelve sólo con TTL. Contexto general permite comenzar captura técnica sin consultas DB de clínica; emisión clínica requiere lectura de maestros existentes, pero ninguna escritura de telemetría.

### Vida de sesión, renovación y concurrencia

TTL propuesto 5 minutos, limitado por exp real del Bearer; caducidad y tolerancia de reloj deben aprobarse (propuesta 30 s). No extender token vencido ni aceptar contexto sin Bearer válido. Conexión inicial emite sid; renovación/contexto de otra clínica puede mantener sid sólo presentando contexto anterior válido del mismo Actor/instalación y sin ampliar permisos. La solicitud de renovación es contrato a definir explícitamente: header X-Telemetry-Context opcional existente, body clinicId requerido y cerrado; si no hay contexto válido, crear nuevo sid y descartar eventos de sesión anterior. No aceptar sid arbitrario en body.

Contexto expira → pausar envíos y renovar antes de flush normal; no esperar renovación bloqueante al cerrar página. Pendientes de contexto anterior sólo migran si mismo sid/Actor/región/ámbito/version HMAC y comprobación de permisos renovada; entonces no cambian payload/eventId/timestamp. Cambio de versión HMAC o identidad/sid descarta pendientes anteriores y señala contador local de pérdida sin datos. No fabricar timestamp nuevo. Token nuevo adjunto a retry no cambia envelope; retry sólo si contexto permanece equivalente y vigente. Error permanente de autenticación/contexto no dispara retries ciegos con credenciales nuevas.

Separar pending por contexto usando límites **globales** 200 eventos/256 KiB candidatos, no una cuota por clínica ilimitada. Un transporte activo global, scheduling por primer deadline elegible por partición. Contexto se captura inmutable al ocurrir la operación; cambiar selector de clínica no reasigna eventos. track conserva firma pública; adaptador de operación establece scope/contexto interno explícito y restaurable, no variable global mutable que mezcle promesas. Eventos generales utilizan contexto general propio aunque haya clínica seleccionada si el trigger realmente es general; los clínicos usan contexto resuelto de esa clínica. Scope y clasificación quedan en productor/adaptador y en tests, no propiedades extra del catálogo.

### Gestión de claves y configuración propuesta

Settings futuras: TELEMETRY_ENABLED deshabilitado si no está configurado, TELEMETRY_PROCESSING_REGION US/UK obligatorio al habilitar, TELEMETRY_ENDPOINT referencia local acordada, identificadores/keyring de versiones y referencias secretas para firma/binding/seudónimos. No reutilizar JWT_SECRET_KEY. Ninguna variable .env, Compose/secret manager o dependencia se introduce ahora.

HMAC identidad: `ps_` + hex minúscula de HMAC-SHA256(K_user, UTF-8("healthcore|telemetry-user|v1|" + UUID canónico minúscula)). Separación región/entorno garantizada por claves diferentes; mismo actor en mismo ámbito/version → salida estable de 64 hex. Binding sujeto/clínica utiliza claves diferentes y prefijos de dominio diferentes; firmas usan otra clave. Canonicalización/versiones se prueban con vectores sintéticos, no claves reales. No hashing de email, ni K en navegador, ni registro de entrada/salida HMAC en logs.

Claves aleatorias de al menos 32 bytes por entorno/región/finalidad; guardar en gestor de secretos/inyector de archivos secretos del entorno aprobado, accesibles sólo a proceso receptor/contexto autorizado. No elegir proveedor ni desplegar secret manager en esta fase. Sin clave/región válida: contexto responde 503 seguro, frontend no exporta y negocio continúa; nunca fallback a clave JWT/dev default u otra región. No persistir eventos, mappings o identificadores para que funcione el HMAC.

Rotación: versiones explícitas en contexto, nunca agregar keyVersion al envelope sin nueva aprobación contractual. Firma permite verificación de clave previa durante TTL máximo+skew aprobados; clave comprometida se revoca inmediatamente sin gracia. HMAC user rota en ventana analítica aprobada: no se afirma estabilidad entre versiones ni unión US/UK; renovar sid/purgar pendientes al cambiar pseudonymVersion. Fase 3 decidirá retención y continuidad por versión; no conservar claves indefinidamente para reconstruir identidad. Revocación/configuración nueva debe invalidar keyring cache y documentar despliegue atómico; no cambiar get_settings o CI ahora. Documentar responsable Tecnología y revisión Claire antes de usar identidad real.

### Archivos de implementación concretos para revisión

- backend/app/telemetry/context.py: resolución y servicio de contexto; sin modificar get_current_actor ni permisos existentes.
- backend/app/telemetry/identity.py: HMAC/binding/verificación de token y versiones; usa hashlib/hmac/PyJWT existentes.
- backend/app/telemetry/schemas.py y router.py: contratos context/events/receipt seguros.
- backend/app/core/config.py y main.py: Settings/montaje/header CORS sólo con autorización expresa de configuración/contratos.
- backend/tests/test_telemetry_context.py y test_telemetry_identity.py: pruebas sin claves/datos reales; resolver de clínica con mocks y pruebas HTTP autorizadas aisladas.
- uis/backoffice/telemetry/context.mjs: fetch de contexto, renovación, scopes y memoria; no lectura/escritura de browser storage.
- uis/backoffice/telemetry/telemetry-service.mjs y transport.mjs: particiones de contexto, cuotas globales, Bearer+context header y flush.

Auth/policies, auditoría, migraciones, almacenamiento y despliegue permanecen excluidos; si los permisos actuales no soportan resolución clínica, presentar una propuesta separada antes de ampliar políticas. No crear segundo servicio ni mapa persistente de seudónimos.

### Matriz de revisión previa al stub

Tecnología/Claire deben revisar estos puntos concretos: finalidad del seudónimo y vínculos, campos legibles del token, actor/región/clinic access, contexto general y destinos regionales, claves/roles/rotación/revocación, TTL/clock skew, errores/logging sin payload, ausencia de persistencia y semántica de renovación/permisos vigentes. El desarrollador aprueba alcance de archivos/headers/endpoint antes de editar código. Toda aprobación debe identificar esta sección/versión; no atribuir revisión externa a la conversación sin evidencia.

Pruebas futuras T-CTX-001–010: (1) general Bearer válido devuelve null y ps/sid sin UUID/secretos; (2) clínica US/UK resolución y receptor correcto; (3) cross-region/denied/missing/inactive no fallback a null; (4) token tampered/issuer/audience/expired/kid ajeno rechazado; (5) otro Actor/sid/userId/region/env/lote mixto rechazado; (6) renovación preserva contexto equivalente o purga al cambiar clave/actor; (7) capturas concurrentes A/B separadas y cuota global; (8) defaults sin clave/región ->503/cero export sin bloqueo negocio; (9) vectores HMAC estables/separados por propósito/región/entorno, sin fallback de clave; (10) no-store/errores/logs/no escritura y no rechazo Promise. Pruebas no ejecutadas: no existe implementación.


## Componentes, archivos previstos y autorizaciones futuras

Ninguno se modifica ahora. Lista candidata, que debe concretarse al cerrar gate:

| Componente | Archivos candidatos | Condición |
|---|---|---|
| Receptor | backend/app/telemetry/{__init__.py,router.py,schemas.py}; backend/app/main.py | Ruta pública/política/logging segura autorizadas; TelemetryEvent, TelemetryBatch, TelemetryReceipt sin ORM |
| Configuración | backend/app/core/config.py; config.mjs público propuesto | Configuración protegida B08; utilidad de TELEMETRY_ENDPOINT acordada |
| Core/transport | uis/backoffice/telemetry/{telemetry-service.mjs,transport.mjs,config.mjs} | ADR-001 distribución autorizada; no dependencia nueva |
| Catalog outputs | ubicación a resolver en TASK-TEL-004 | Mismo JSON como fuente; no escribir arbitrariamente en contrato Fase 1 |
| Adaptadores | uis/backoffice/operational-incidents/{app.js,index.html}; uis/backoffice/management/index.html | Contexto/sesión B03/B04; shared module accesible |
| Tests | backend/tests/test_telemetry.py; uis/backoffice/telemetry/tests/*.test.mjs | Unidad sin DB; runner node:test candidato |
| Next opcional | frontend/app/internal/incident-history/workspace.js y adaptador separado | Alcance opcional aprobado; pública landing sin región no exporta |
| Hechos servidor | backend/app/incidents/router.py; management/router.py; auth/dependencies.py | B06/B08 y revisión audit/auth; no reemplazar con clics UI |
| Documentación componentes | README.md/README.es.md de backend y backoffice afectados | Actualizar ambos al cambiar uso/configuración futura |

Fuentes ausentes inventario/agregadores/sondas no reciben archivos de aplicación nuevos en esta tarea. Auth, policies, auditoría, CORS/infra/.env/CI y migraciones siguen protegidos; no prometer cambios implícitos para desbloquear.

## Diseño candidato del endpoint

Secuencia prevista tras gate: autenticar productor conforme a mecanismo existente aprobado; imponer límite real de body antes de JSON incluso chunked; validar wrapper/events/TelemetryEvent/contrato íntegro y semántica; rechazar lote completo al primer error sin reflejar contenido; resumir count y nombres válidos sin identificadores ni properties; devolver 200/received. Sin session DB, persistencia, archivo de eventos ni exportador. Configurar OpenAPI request/response y alternativas específicas de ingestión sin alterar contratos existentes. Log count/types no debe registrar entradas desconocidas arbitrarias. Endpoint excluido de captura de api_request_completed y errores de entrega para evitar recursión. Rate limiting/productor/cuotas de ingress son decisión de seguridad pendiente si imprescindible, no dependencia añadida sin aprobación.

## TelemetryService y reintentos candidatos

track válido captura reloj, UUID y contexto aprobado, valida y copia properties y encola. No lanza ni devuelve Promise; rechazo local aumenta contador acotado sin enviar telemetry_contract_rejected por el mismo canal fallido. Snapshot de credenciales/contexto no se mezcla entre sesiones. No persistencia de cola en web storage/IndexedDB/service worker.

Política recuperable candidata: fallo de red/timeout, 408, 429 y 500/502/503/504. No reintentar cualquier 5xx por inferencia: 501/505 y resto requieren decisión explícita. Errores 400/401/403/404/405/413/415/422 son permanentes: descartar sin cambiar auth. Primer envío + tres retries a 1/2/4 segundos base, usando un solo timer. Retry-After válido para 429/503 aumenta espera respecto al backoff, límite candidato 30 s a aprobar; parsear delta-seconds/fecha, valores inválidos ignoran hint. Timeout candidato 5 s por intento (no prueba de no recepción). ACK 200 debe ser JSON received entero igual a N; 2xx distinto o ACK inválido es error de protocolo, propuesta recuperable acotada. Mantener payload/IDs y descartar sólo inFlight después del cuarto fallo; pending continúa. Nunca registrar el body de error. Unit tests fijan reloj sin dormir y distinguen número de retries de intentos totales.

## Estrategia de instrumentación

Aplicar exclusivamente matriz **aprobada futura**; inventario diagnóstico actual en spec no es autorización. Un propietario por hecho evita duplicar servidor/UI. Navegación hash en renderRoute, sección Management tras acceso real; enums sólo de schema, nunca hash completo ni UUID. Errores window.error/unhandledrejection en adaptador único con clasificación acotada y guard de recursión. Rendimiento monotónico con metric/unit/view permitidos; Web Vitals candidato ya aparece en frontend_timing_measured, no inventar evento web_vital. Conexión UI usa session_started/ended si aprobados, no authentication_succeeded; auth/authorization server tienen frontera propia protegida.

incident_created/transitioned/assigned requieren post-commit servidor según Fase 1. Management es lectura; no fabricar management_mutation_completed por seleccionar recurso. Inventario 5 obligatorios académicos/otras oportunidades y 6 obligatorios briefing no pueden tener cobertura completa sólo UI; B06 debe decidir un alcance explícito adicional o aplazamiento aprobado. Eventos de contrato/entrega se diagnostican por canal separado que aún no existe, evitando autorrecursión. No instrumentar datos de pacientes ni endpoints externos.

## Estrategia automatizada propuesta

Las pruebas de frontend listadas permanecen NOT_RUN; el stub, contexto/identidad, status y autenticación se han probado según sección de cierre. Usar datos sintéticos, reloj/UUID/contexto/fetch/keepalive inyectables y promesas controladas.

Backend: T-B01 lote válido 1/20; T-B02 todos los eventos/campos/nullable/enum/format y required/extras; T-B03 200/received; T-B04 caplog seguro; T-B05 spies cero escrituras, incluso invalid/401; T-B06 Settings; T-N07 body límite incluyendo chunked/ausencia Content-Length/UTF-8; T-N08 autorización/CORS; T-N09 parity catálogo; T-N13 errores seguros. OpenAPI deberá tener operación nueva y conservar baseline restante. Httpx/pytest existentes sin DB para ingestión; regresión de negocio sólo en DB temporal sintética autorizada.

Frontend: T-F01–13 de spec cubren envelope/timestamp/cola/20/10 s/config/hidden/keepalive/retry/descarte/correlación/allowlist/rechazo. Pruebas extra: primer deadline no se reinicia, capturas durante envío/retry, pending vencido se envía al finalizar, fallo/abort keepalive conserva datos mientras siga vivo el contexto, recepción desconocida no acredita ACK, guard de desconexión/respuesta tardía, máximos de memoria/bytes y no error recursivo. T-N01 presupuesto track requiere benchmark informado, no test de reloj falso. T-N02–14 verifican cuotas/no concurrencia/seguridad/compatibilidad. node:test candidato con mocks de lifecycle evita añadir jsdom/Jest; ejecución de navegador valida APIs reales y BFCache donde se apruebe soporte.

T-CAT-001–039: un ejemplo positivo por candidato + required faltante/extra/tipo/enum mal + trigger y productor/duplicados. T-I01–07 verifican cobertura, rollback, navegación, errores, perf y auth/Web Vitals condicionales. No probar contra datos reales ni interpretar ejemplos que pasan JSON como aprobación de semántica/governance.

## Integración manual reproducible futura

1. Resolver gates y usar un entorno local aislado con fixtures sintéticos y configuración ya autorizada. Consultar README para arranque. No copiar/modificar .env ni ejecutar seeds sobre DB compartida por este plan.
2. Desde raíz, `podman compose up --build -d` sólo si autorizado para ese entorno: ejecuta db-init, migraciones/seeds existentes. Alternativa API desde backend: `uv run --no-sync uvicorn app.main:app --reload`, entorno preparado y sin telemetría DB. Backoffice estático según ADR-001 distribución revisada, no asumir que servir sólo una subcarpeta resuelve imports compartidos.
3. Abrir incidencias 8080 y Management /management; Next 3000 sólo si autorizado. Introducir JWT de desarrollo local en UI sin capturarlo en evidencias. Proveer contexto regional/seudónimo aprobado; no extraer claves ni datos reales.
4. DevTools Network filtra `/telemetry/events`; ejecutar vistas/acciones aprobadas con datos sintéticos, llegar a 20 o esperar 10 s; confirmar timestamp de captura, allowlist, contenido, conteo y HTTP 200/received. Comprobar respuestas permanentes/recuperables mediante mocks o entorno aislado.
5. Ocultar pestaña y observar petición best-effort; distinguir intento keepalive de ACK HTTP observable. Prueba de falta de credenciales no se resuelve desactivando auth. Confirmar cero payloads individuales por cada track y ningún duplicado de productor.
6. Revisar OpenAPI `/docs`/`/openapi.json`, logs count/types sin properties/identidad y spies/no escrituras. Comparar schema aprobado. Capturar evidencia redactada: Authorization, cookies, tokens y UUID de negocio no se comparten; HAR completo puede contener secretos.
7. Registrar versiones, contexto sintético, comandos/resultados y limitaciones; revisión Claire y validate-delivery. Estas capturas/evidencias NO existen todavía.

## Orden, validación y riesgos

Prerrequisitos/contratos antes de cambios; stub/modelos/config/logging/tests antes de frontend; core/cola/batching/HTTP/retry/flush/contexto y tests aislados antes de instrumentación técnica; hechos obligatorios y restantes aprobados después; integración/privacidad/OpenAPI/DevTools y revisión final al terminar. Tareas detalladas en tasks.md, todas TODO. No ejecutar etapas B–G con B01–B08 abiertos.

Riesgos/mitigación: seudonimización y región faltantes -> no exportar; fetch keepalive/Bearer aprobado -> validar límites y CORS; tamaño/CORS/preflight -> límites/entorno probado; duplicados -> IDs inmutables y alcance best-effort explícito; pérdidas memoria -> contador y cobertura aprobada, no promesa durable; hechos servidor ausentes -> productor/fase separada; logs sensibles -> resumen y errores redactados; arquitectura compartida estática -> comprobar distribución antes de crear carpetas; configuración protegida -> autorización expresa; Fase 3 -> retención/persistencia fuera de esta fase.

Revisión documental actual debe comprobar sólo estos tres archivos, referencias, IDs, catálogos y scope Git; tests de aplicación no pertinentes sin código cambiado. Revisión de implementación futura exige evidencia de todas las aceptaciones FUT, sin declarar completo ante BLOCKED. No commit/push/PR/merge ni despliegue sin autorización expresa. Título futuro de PR: `feat: telemetry event capture`; cuerpo con eventos realmente instrumentados, puntos, pruebas y evidencia DevTools redactada.

## Evidencia de cierre del stub

Comando ejecutado desde raíz: `podman compose --profile test run --no-deps --build --rm -e DATABASE_URL=postgresql+asyncpg://synthetic:synthetic@127.0.0.1:1/isolated test uv run --no-sync pytest tests/test_telemetry.py tests/test_telemetry_context.py tests/test_telemetry_identity.py tests/test_status.py tests/test_auth.py -q`.
Resultado final: **103 passed in 1.64s**, Python 3.12.13, FastAPI 0.141.1, Pydantic 2.13.5, PyJWT 2.15.0. URL ficticia/inaccesible permite construir dependencias de sesión de pruebas auth existentes sin conectarse a DB; resolución de clínica probada con mocks read-only. Ningún entorno de negocio ni seed/migración ejecutado. Pruebas previas detectaron campos null requeridos de PyJWT (corregido con comprobación explícita de presencia) y un test auth existente que requería objeto DB incluso antes de 401 (preparación aislada corregida, sin cambiar política).

Contrato fuente/asset empaquetado idénticos y `git diff --check` PASS. Los 39 modelos se prueban con positivos/required ausente/extras/null/fecha inválida; sólo cinco eventos técnicos están autorizados como productor frontend del receptor. Consulta clínica de SQL real no ejecutada en DB: joins/capability/estado/región probados con mocks; medición/integración real clínica y DevTools pendientes. Suite completa PostgreSQL del repositorio NOT_RUN: no se autorizaron mutaciones de fixtures en DB de negocio para este cierre. No implementación frontend, secretos reales, despliegue o commit.


## Avance verificado del servicio frontend — 2026-11-01

Este registro actualiza el estado del hito y prevalece sobre las afirmaciones históricas de ausencia de frontend en el diseño inicial. Backend stub y núcleo frontend implementados; la captura completa sigue abierta. Ruta real: uis/backoffice/operational-incidents/telemetry/*.js, compartida con Management por ../telemetry/runtime.js; se adapta la ruta .mjs prevista al servidor estático existente, sin modificar infraestructura ni introducir dependencias.

Servicio y adaptadores técnicos implementados: track síncrono con envelope inmutable y validación estricta; lotes 20/10 segundos desde primer evento, cola acotada, contexto regional servidor y renovación, fetch Bearer/contexto/keepalive, timeout y tres reintentos adicionales. Navegación de cola/creación general y detalle con clínica resuelta, Management, errores sin texto/stack, sesión y vitals numéricos condicionales. Clínica desconocida bloquea captura. Resumen sin enum permitido se omite, sin inventar contrato. Configuración pública y backend siguen desactivados por defecto en los archivos del repositorio.

Pruebas: node --test uis/backoffice/operational-incidents/telemetry/tests/*.test.mjs: 67 PASS. Integración HTTP aislada del servicio contra stub real: 22 eventos recibidos en lotes 20, 1 tras 10 segundos y 1 mediante flush keepalive; identidad/claves sintéticas, sin DB. Los primeros intentos del arnés se corrigieron para usar HTTP 201 y application=incidents del contrato; no fallos del producto. Navegador/DevTools y benchmark en navegador NOT RUN: ningún navegador disponible. README bilingües documentan límites. Cierre C y adaptadores técnicos D/F parcial; no se marca TASK-TEL-028/035 ni entrega global DONE mientras falten evidencias del alcance completo.

Pendiente: productores de negocio/autenticación, requestId HTTP, fuentes/agregados/sondas inexistentes, vista resumen, medición de coste clínico y captura en navegador, validación visual/DevTools, configuración operativa y revisiones de activación. No se cambia Memory Bank, Rules, .env, CI, despliegue, políticas auth, ni se hace commit/push/PR. Pérdida terminal posible, sin dedup/persistencia y rotación sin gracia; cached general caducado puede omitir vitals durante selección clínica prolongada. Aprobación HMAC no equivale a aprobación de producción o tratamiento de datos reales.

## Validación en navegador — 2026-11-01

Esta evidencia actualiza el resultado previo de navegador no disponible para las comprobaciones enumeradas. Se accedió a Chrome mediante UI nativa. Conexión de Incidencias, cola vacía, navegación a creación y lectura de catálogos de Management correctas contra stub autenticado aislado, con identidad/claves sintéticas y sin DB. Al ocultar Incidencias se recibieron eventos numéricos de rendimiento; sesión/navegación de ambas aplicaciones aceptadas con seudónimo, versión 1.1.0 y jurisdicción general null. Consola Management: cero mensajes antes del benchmark (un elemento oculto no inspeccionado). Dos ejecuciones locales de 400 capturas síncronas: p95 0,30 ms y 0,10 ms; máximos 4,70 ms y 0,50 ms. Cada ejecución recibió 401 eventos incluyendo inicio de sesión, sin rechazos. No es garantía para todos los dispositivos. No se copiaron JWT ni claves HMAC a evidencias. Pendientes: detalle clínico/integración regional con DB, inspección completa Network, otros navegadores y productores restantes.

## Validación PostgreSQL y detalle — 2026-11-01

Validación ejecutada en un proyecto Compose temporal independiente, con PostgreSQL 16 en tmpfs, migraciones 0001–0009 y seeds sintéticos; no se utilizó la base de desarrollo. El arnés comprobó contexto US/UK, rechazo de región extranjera, clínica inexistente y rol sin permiso, discrepancia de jurisdicción, desactivación y revalidación de clínica, seudónimos distintos con claves regionales separadas e invalidación de credenciales US en UK. Resultado PASS; primera petición de contexto US 39,38 ms (una observación local, no benchmark de escalabilidad). Recuento de clínicas/jurisdicciones conservado; las pruebas de desactivación sólo alteraron fixtures temporales y se restauraron. Se corrigió el acceso SecretStr en el arnés antes del resultado válido, sin cambio de producto. Suite de contexto previa repetida: 11 PASS.

El servicio frontend real, ejecutado por HTTP con UUID sintéticos y API/DB reales temporales, emitió detalle US y rechazó clínica UK sin fallback general: PASS. Chrome cargó una incidencia sintética creada en ese entorno. Network mostró POST /telemetry/context y POST /telemetry/events con 200, cabeceras Bearer y X-Telemetry-Context y respuesta no-store. Payload de detalle: schemaVersion 1.1.0, seudónimo y properties={jurisdiction:US,environment:test,view:incident_detail}; sin UUID clínico ni texto de incidencia. Tokens y seudónimo se ocultaron en la evidencia de DevTools; sin HAR. La única advertencia de consola procedía de una extensión Chrome, no del código de HealthCore. CORS del arnés permite sólo localhost:18002; no modifica CORS/configuración del repositorio.

Arneses ejecutados: /private/tmp/telemetry_db_validation.py mediante /private/tmp/telemetry-db-compose.yaml; /private/tmp/telemetry_clinical_http.mjs; detalle browser mediante /private/tmp/telemetry-db-browser-compose.yaml. Es evidencia acotada a este entorno, no suite completa PostgreSQL de todos los módulos. Se cierran las verificaciones locales de detalle, contexto regional y Network descritas aquí. Siguen pendientes productores restantes, requestId HTTP, vista resumen, fuentes/agregados/sondas y configuración/revisión de activación. La fase completa no se marca terminada.


## Lote 1 de productores servidor: implementado

El lote aprobado incident_created/transitioned/assigned está implementado post-commit; detalles, límites y evidencia en [server-producers.md](./server-producers.md). Se conserva el contrato browser y la configuración desactivada por defecto. Ocho eventos tienen productores implementados y 31 quedan pendientes/diferidos. requestId HTTP, contexto de eventos generales y fuentes ausentes siguen abiertos; no se declara cierre global.

## Reajuste a backend compartido — 2026-11-01

Tecnología validó un frontend y un backend; el desarrollador pidió «reajusta teniendo en cuenta esto». Implementados juegos de claves US/UK seleccionados por Clinic/Jurisdiction validados en servidor, contextos firmados y revalidados por ámbito y productores post-commit con HMAC regional. Contrato público 1.1.0 sin cambios ni claves frontend. Generales sin clínica: null y claves generales independientes. La sesión puede renovarse al cambiar ámbito; cambia el seudónimo. Cola servidor particionada por región y binding clínico. No nuevas dependencias, auth policies, migraciones, Memory Bank, Rules, secretos, despliegue ni forwarding.

.env.example documenta TELEMETRY_PROCESSING_REGION vacío para backend compartido, cuatro claves generales y cinco por región. TELEMETRY_RESOURCE_KEY antigua no se usa en modo compartido; sus equivalentes son TELEMETRY_US_RESOURCE_KEY y TELEMETRY_UK_RESOURCE_KEY. TELEMETRY_US_ENDPOINT/UK_ENDPOINT son referencias opcionales, no transporte activo. Las configuraciones antiguas US/UK fijas se conservan sólo por compatibilidad. Producción, retención y ubicación de procesamiento/almacenamiento siguen pendientes de Cumplimiento. Los otros 31 eventos no se cierran.

## Punto 1: configuración local conectada — 2026-11-01

El desarrollador pidió «continuemos con el 1», referido a inyección Compose, configuración pública y circuito US/UK/general. Compose ahora pasa las variables telemetry sólo al backend; Nginx recibe enabled/environment/endpoint y genera /telemetry/config.json con Cache-Control:no-store mediante la plantilla operational-incidents/nginx/default.conf.template. BACKOFFICE_TELEMETRY_ENDPOINT es la URL del navegador (default http://localhost:8000/telemetry/events). Ninguna clave se entrega a backoffice/Next.js. .env.example actualizado, .env real no modificado; claves existentes verificadas sin mostrarlas:14 diferentes entre sí y de JWT.

Validación temporal derivada de Compose, PostgreSQL16 en tmpfs y secretos sintéticos: frontend real recibió lotes[1,20,1,1], el incompleto UK a los10segundos, generales null y seudónimos US/UK distintos sin UUID originales. Creación US/UK y transición/asignación se hicieron exclusivamente allí. Arneses iniciales corregidos (IPv4, EHR UK304 y view incident_queue); última ejecución PASS. Arneses /private/tmp/telemetry-wiring-compose.json y telemetry_wiring_validation.mjs; entorno detenido con compose stop.

Aplicación local: podman compose up --no-deps --build -d backend backoffice; ambos actualizados sin ejecutar db-init ni alterar registros locales. /status200, JSON público exacto tres campos/no claves, CORS8080 y envío del servicio frontend real de cuatro eventos US/UK/null:PASS. Arnes telemetry_local_readonly.mjs toma la configuración privada sólo en memoria, no guarda ni muestra JWT/claves. nginx -t y git diff --check PASS. No validación UI nativa nueva ni HAR; prueba HTTP del módulo real y preflight. Este resultado sustituye el pendiente previo de inyección Compose. No se activa exportador/almacenamiento externo ni uso con datos reales, no se cierra fase completa y no se hace commit.

## Lote2 de auditoría aprobado e implementado

El desarrollador aprobó audit_accessed en incident_audit y Management filtrado por clínica, middleware de finalización y productor regional. Detalles y límites en [remaining-producers.md](./remaining-producers.md). Nueve tipos con productor al menos parcial, treinta sin productor; auditoría global sigue abierta. Envío sólo tras cuerpo final2xx; permisos/proyecciones persistentes conservados, sin contenido libre ni claves frontend. No se declara cierre global ni nuevas exclusiones.

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
