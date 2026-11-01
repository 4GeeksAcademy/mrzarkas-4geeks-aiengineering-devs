# SPEC — Telemetry Event Capture, Fase 2

**Estado vigente — revisión final local (2026-11-01):** implementado y validado dentro del alcance reducido autorizado. Contrato1.2.0,39 tipos:19 con fuente al menos parcial y20 DEFERRED_NO_SOURCE aprobado. Un frontend/backoffice compartido y un backend; HMAC exclusivamente servidor, jurisdicción clínica autoritativa y null técnico general. Captura20/10 efímera, recepción no durable. Admisión browser5 + dos diagnósticos internos frontend restringidos; servidor admite sus hechos por canal propio. Backend/backoffice locales actualizados y Chrome sintético validado.

**La cobertura integral original NO está terminada:**9 de los20 diferidos son obligatorios; TEL-FR-018 sigue pendiente. Hay además brechas de los19 tipos actuales, detalladas en [delivery-status.md](./delivery-status.md). La aprobación de aplazamiento no equivale a requisitos satisfechos, producción ni cumplimiento normativo.

La matriz y estados vigentes están en [delivery-status.md](./delivery-status.md); la cronología que sigue conserva las propuestas y evidencias de cada revisión. Sus menciones a «actual», TODO/BLOCKED,1.1.0, cinco productores o pruebas NOT_RUN corresponden al momento histórico de esa sección y no sustituyen este estado vigente. No se han reescrito Memory Bank ni fuentes empresariales.

## Historial del diseño y de los lotes (referencia temporal)

**Fecha:** 2026-11-01. **Rama:** `feature/telemetryEventCapture`. **Estado:** DRAFT / BLOCKED para cierre de diseño e implementación.

El stub backend está implementado dentro del alcance aprobado; el frontend sigue pendiente. Este expediente registra requisitos candidatos del prompt, evidencia del checkout y preguntas de resolución. Sólo las decisiones explícitas registradas abajo están aprobadas; los restantes ADR y tareas futuras no constituyen aprobación. El gate del prompt §1.3 impide completar un diseño definitivo sin aprobación verificable de la Fase 1. Las alternativas técnicas se mantienen como hipótesis hasta resolver los bloqueos; sólo se modifica el contrato documental de telemetría autorizado; no se modifica configuración, autenticación, auditoría ni Memory Bank.

Los IDs TEL-FR/TASK-TEL se reutilizan por exigencia del prompt: son **locales a esta Fase 2**. Una referencia externa se escribe `Fase1:TEL-FR-xxx`; los enlaces locales apuntan a este expediente, evitando confundir recepción de lotes con entradas de inventario.

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


## Resumen, dominio y problema

HealthCore opera 12 clínicas (9 US, 3 UK). CONTEXT.md es el briefing empresarial; sus necesidades no acreditan capacidades. API FastAPI y backoffice de incidencias/Management existen; inventario y KPIs integrados no. Sistema pre-MVP sintético, sin piloto/producción ni certificación HIPAA/UK GDPR.

Objetivo solicitado: interfaz track(), envelope automático, cola efímera, batching, reintentos y receptor temporal sin almacenamiento, conservando futura sustitución en Fase 3. Problema: faltan aprobación y contexto regional/seudónimo; no se puede demostrar toda la cobertura empresarial desde un navegador.

## Prerrequisitos y autoridad

Orden: seguridad/Rules, AGENTS, contratos aprobados, CONTEXT, arquitectura comprobada, prompt. `empresa-BRIEFING` se interpreta como CONTEXT.md. No existe `iu/backoffice`; ruta real `uis/backoffice`. API actual `backend/app`, no recrear `services/central-api`. Se conserva la discrepancia de rutas/documentos históricos sin corregir fuentes protegidas.

Fuentes leídas: contexto obligatorio, índice Memory Bank y conventions; Rules 01/07/09 siempre activas, 05 por negocio; 02/03/04/06/08 inspeccionadas para evaluar alcance (ningún glob de código modificado). README raíz/docs/services/uis/backend/frontend y ambos backoffice; Fase 1 specs/plan/tasks/telemetry-plan/event-schemas/traceability-matrix/validation-report; SDD serialization-audit e inventario como propuestas, no aprobación. La convención de tríada existe en memory-bank/specs, pero está fuera de alcance: se usa el fallback autorizado docs/specs/telemetry-event-capture.

### Bloqueos contractuales y documentales

| ID | Evidencia / bloqueo | Resolución requerida / responsable |
|---|---|---|
| B01 | `telemetry-plan.md` cabecera declara PROPOSED; JSON se titula proposed; `validation-report.md` acredita validación documental, no aprobación contractual. Los commits f9b2d3e/c962980 demuestran versionado, no aprobación. | Responsable de Fase 1: aprobación con versión/hash y alcance, o evidencia de revisión establecida. No se consultó un servicio remoto de PR; aprobación externa UNKNOWN. |
| B02 | Fase 1 propone BATCH cada 15 min y 17 eventos STREAM; prompt Fase 2 exige todos en lotes de 20 / 10 s. El stub no proporciona alertas ni confirmación durable. | 20 eventos/10 s aprobados por el desarrollador. Pendiente: alcance STREAM y pérdidas del perfil temporal; conservar semántica de fuente. |
| B03 | `userId` y referencias de negocio son `ps_`+64 hex mediante HMAC regional; JWT contiene `sub` UUID y la UI no dispone de seudónimo autorizado. Humano autenticado exige userId no nulo en Fase 1. | Tecnología y Claire: mecanismo aprobado de contexto seudónimo regional sin entregar claves al navegador; no usar hash simple, UUID crudo ni null para eludir contrato. |
| B04 | Todas las properties requieren `jurisdiction` US/UK; JWT sólo aporta sub/role/area_id. Vistas generales y landing no tienen región fiable; Settings admite staging, contrato environment no. | Fuente clínica y null para eventos generales aprobados. Pendiente: clasificar generales, destino/ámbito HMAC sin clínica, staging y revisión Tecnología/Claire. No exportar sin contexto/destino válido. |
| B05 | API utiliza HTTPBearer; Beacon no acepta Authorization. No hay proxy autenticado de telemetría ni cookie de sesión. | Decisión de transporte resuelta: fetch keepalive con Bearer aprobado. Pendiente validar configuración/límites/CORS del entorno; no endpoint público ni tokens en URL/body. |
| B06 | No existe inventario, integraciones EHR/citas/facturación ni agregadores/scheduler. Hechos de commit, auditoría, sondas y jobs pertenecen a productores servidor. | Responsables de dominio/CTO: acotar cobertura Fase 2 y plan separado para fuentes ausentes; no sintetizar éxitos desde clics ni construir esos dominios aquí. |
| B07 | Fase 1 exige logging seguro y colector; prompt permite cantidad/event_type pero prohíbe persistir eventos. Logs de Uvicorn/runtime pueden ser retenidos externamente. | CTO/Claire: aprobar sólo resumen operacional sin envelopes y su tratamiento. No prometer ausencia de retención de logs ajenos al stub. |
| B08 | Autorizaciones de contratos públicos, configuración, privacidad y correlación son operaciones protegidas de AGENTS.md. | Obtener autorizaciones expresas del alcance futuro y revisión de Cumplimiento antes de cambios; esta ejecución sólo autoriza tres documentos. |

## Alcance, exclusiones y dependencias

La entrega inicial fue documental; el alcance actual incluye el stub backend aprobado. Memory Bank/Rules/.env/CI/infra permanecen intactos; contrato documental Fase 1 actualizado por autorización explícita. Alcance futuro candidato: receptor en API existente, servicio JavaScript compartido con adaptadores por frontend, tests aislados e instrumentación de eventos compatibles tras gate.

Excluidos persistencia de telemetría, proveedores externos, dashboards, reporting, dominios ausentes, refactors, migraciones, nuevos frameworks/dependencias, cambios de auth y auditoría. Agregar rutas públicas, contexto de identidad o configuración requiere alcance futuro expresamente aprobado. No se crea rama, commit, push ni PR.

## Requisitos funcionales EARS candidatos

Estos requisitos recogen el encargo, **no son contrato aprobado ni autorización de implementación**. Todos dependen de B01/B08; dependencias específicas y contradicciones se indican en aceptación y ADR. Cada ID de prueba representa un escenario futuro NOT_RUN. Referencias a eventos son candidatas de Fase 1; cero eventos aprobados verificables.

### TEL-FR-001 — Recepción de lotes

WHEN el backend recibe una petición POST válida en `/telemetry/events`, THE system SHALL aceptar un payload con estructura `{ "events": [...] }`.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08; ADR relacionados en plan. **Eventos:** todos los eventos compatibles; sin catálogo aprobado.
- **Aceptación:** B01 y esquema validado; aceptación de lote sintético autorizado.
- **Prueba futura:** T-B01: 1 y 20 eventos válidos.

### TEL-FR-002 — Validación estructural

WHEN se recibe un lote, THE system SHALL validar cada evento mediante un modelo Pydantic `TelemetryEvent` compatible con el envelope aprobado.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08; ADR relacionados en plan. **Eventos:** todos los eventos compatibles; sin catálogo aprobado.
- **Aceptación:** Tipos, nulabilidad, extras, fechas reales y cada properties conformes al contrato; lote atómico.
- **Prueba futura:** T-B02: positivos por evento; ausentes, nulos indebidos, formato y extras -> 422.

### TEL-FR-003 — Confirmación

WHEN el lote supera la validación, THE system SHALL responder HTTP 200 con `{ "received": N }`, siendo N el número de eventos recibidos.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08; ADR relacionados en plan. **Eventos:** todos los eventos compatibles; sin catálogo aprobado.
- **Aceptación:** 200 y received igual a longitud del lote, sin campos adicionales.
- **Prueba futura:** T-B03: N=1 y N=20; validar respuesta.

### TEL-FR-004 — Logging

WHEN se recibe un lote válido, THE system SHALL registrar su cantidad y los valores `event_type`, sin registrar PII ni propiedades sensibles.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08; ADR relacionados en plan. **Eventos:** todos los eventos compatibles; sin catálogo aprobado.
- **Aceptación:** Log contiene sólo count y tipos válidos; no payload/identificadores.
- **Prueba futura:** T-B04: caplog con marcadores sintéticos, incluso errores.

### TEL-FR-005 — Ausencia de persistencia

THE system SHALL procesar el lote sin escribir eventos en ninguna base de datos, archivo de persistencia o proveedor externo.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08; ADR relacionados en plan. **Eventos:** todos los eventos compatibles; sin catálogo aprobado.
- **Aceptación:** Cero llamadas de escritura/archivos/exportadores durante recepción válida e inválida.
- **Prueba futura:** T-B05: spies DB/files/export; sin sesión ORM en router.

### TEL-FR-006 — Configuración backend

THE system SHALL declarar y leer la configuración `TELEMETRY_ENDPOINT` mediante el mecanismo existente de configuración del backend.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08; ADR relacionados en plan. **Eventos:** todos los eventos compatibles; sin catálogo aprobado.
- **Aceptación:** Settings lee TELEMETRY_ENDPOINT; finalidad documentada separada de ruta fija.
- **Prueba futura:** T-B06: configuración ausente/presente/inválida sin cambiar URL del router.

### TEL-FR-007 — API centralizada

THE system SHALL exponer una única función pública de captura JavaScript `track(eventType, properties)` que devuelve undefined.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08; ADR relacionados en plan. **Eventos:** todos los eventos compatibles; sin catálogo aprobado.
- **Aceptación:** track(eventType, properties) síncrona devuelve undefined; componentes no conocen transporte.
- **Prueba futura:** T-F01: contrato público JS, ninguna excepción o Promise.

### TEL-FR-008 — Cola local

WHEN se ejecuta `track()`, THE system SHALL construir el envelope y añadir el evento a una cola en memoria.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08; ADR relacionados en plan. **Eventos:** todos los eventos compatibles; sin catálogo aprobado.
- **Aceptación:** Sólo evento validado entra en memoria, snapshot independiente de objeto original.
- **Prueba futura:** T-F02: mutation del objeto original no cambia evento encolado.

### TEL-FR-009 — Generación automática

WHEN se captura un evento, THE system SHALL completar automáticamente los identificadores y metadatos del envelope conforme al contrato aprobado.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08, B03, B04; ADR relacionados en plan. **Eventos:** todos los eventos compatibles; sin catálogo aprobado.
- **Aceptación:** Servicio completa ocho campos; componentes no aportan envelope; B03/B04 resueltos.
- **Prueba futura:** T-F03: UUID, contexto aprobado, null sólo donde permitido.

### TEL-FR-010 — Timestamp de captura

WHEN ocurre un evento, THE system SHALL registrar su timestamp ISO 8601 en el instante de captura, independientemente del momento en el que se envíe.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08; ADR relacionados en plan. **Eventos:** todos los eventos compatibles; sin catálogo aprobado.
- **Aceptación:** Timestamp fijado antes de encolar, no recalculado en flush/retry.
- **Prueba futura:** T-F04: reloj controlado captura t0, envío t0+10 s conserva t0.

### TEL-FR-011 — Límite de lote

WHEN la cola alcanza 20 eventos, THE system SHALL iniciar el envío de un lote sin esperar al siguiente intervalo periódico.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08; ADR relacionados en plan. **Eventos:** todos los eventos compatibles; sin catálogo aprobado.
- **Aceptación:** Con transporte libre, evento 20 dispara un lote; 19 no disparan por umbral.
- **Prueba futura:** T-F05: 19/20/21 eventos, lote máximo 20.

### TEL-FR-012 — Envío periódico

WHILE existan eventos pendientes, THE system SHALL intentar enviar los eventos acumulados respetando un intervalo de 10 segundos.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08; ADR relacionados en plan. **Eventos:** todos los eventos compatibles; sin catálogo aprobado.
- **Aceptación:** Un timer desde primer pendiente, no debounce reiniciado por track; elegible a 10000 ms.
- **Prueba futura:** T-F06: 9999/10000 ms y captura continua no pospone plazo.

### TEL-FR-013 — Transporte configurable

THE system SHALL obtener la URL de envío desde la configuración frontend.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08; ADR relacionados en plan. **Eventos:** todos los eventos compatibles; sin catálogo aprobado.
- **Aceptación:** URL viene de configuración de la aplicación real; falta/invalidez desactiva envío.
- **Prueba futura:** T-F07: dos endpoints sin cambiar instrumentación; URL inválida -> cero red.

### TEL-FR-014 — Flush de navegación

WHEN la página pasa a estado oculto mediante `visibilitychange`, THE system SHALL intentar enviar los eventos pendientes mediante fetch con keepalive y Bearer al receptor regional autorizado.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08, B05; ADR relacionados en plan. **Eventos:** todos los eventos compatibles; sin catálogo aprobado.
- **Aceptación:** Fetch keepalive usa Bearer y límite de bytes aprobado; ocultar no garantiza entrega; no enviar inFlight dos veces.
- **Prueba futura:** T-F08: hidden, unavailable, false, throw y true; no duplicar lote en vuelo.

### TEL-FR-015 — Reintentos

IF un envío HTTP falla de forma recuperable, THEN THE system SHALL reintentarlo hasta 3 veces con backoff exponencial, sin bloquear la aplicación.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08; ADR relacionados en plan. **Eventos:** todos los eventos compatibles; sin catálogo aprobado.
- **Aceptación:** Tres retries además del intento inicial; mismo payload/eventId; política de errores explícita.
- **Prueba futura:** T-F09: fallos recuperables y avance de reloj 1/2/4 s.

### TEL-FR-016 — Descarte controlado

IF se agotan los reintentos, THEN THE system SHALL descartar el lote afectado de manera controlada, sin afectar las operaciones de negocio.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08; ADR relacionados en plan. **Eventos:** todos los eventos compatibles; sin catálogo aprobado.
- **Aceptación:** Tras cuarto fallo total se descarta sólo lote en vuelo; posteriores siguen pendientes.
- **Prueba futura:** T-F10: fallo final con captura concurrente, contador local sin recursión.

### TEL-FR-017 — Correlación

THE system SHALL proporcionar mecanismos consistentes para `eventId`, `sessionId`, `userId` y `requestId`, respetando las definiciones del contrato.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08, B03, B04; ADR relacionados en plan. **Eventos:** todos los eventos compatibles; sin catálogo aprobado.
- **Aceptación:** requestId correlaciona petición de negocio si existe, null sin petición; UUID evento independiente.
- **Prueba futura:** T-F11: petición correlacionada, navegación y retry conservan identidad.

### TEL-FR-018 — Cobertura obligatoria

THE system SHALL instrumentar las métricas obligatorias de CONTEXT.md mediante los eventos del plan aprobado.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08, B06; ADR relacionados en plan. **Eventos:** catálogo obligatorio; véase inventario diagnóstico.
- **Aceptación:** Matriz de métricas aprobada sin huecos; B06 impide declarar cobertura total.
- **Prueba futura:** T-I01: comparar todas las obligaciones contra fuentes disponibles.

### TEL-FR-019 — Eventos de negocio

WHEN ocurre una acción de negocio instrumentable, THE system SHALL emitir el evento correspondiente en el punto de instrumentación definido por el plan.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08, B06; ADR relacionados en plan. **Eventos:** incident_created, incident_transitioned, incident_assigned; hechos de servidor.
- **Aceptación:** Cada hecho válido tiene productor/trigger único aprobado; no éxito emitido antes de commit.
- **Prueba futura:** T-I02: éxito y rollback; UI y servidor no duplican el mismo hecho.

### TEL-FR-020 — Errores frontend

WHEN ocurre un error frontend no capturado o una promesa rechazada sin gestión, THE system SHALL capturar un evento técnico permitido por el esquema.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08, B06; ADR relacionados en plan. **Eventos:** application_error_observed.
- **Aceptación:** Error global/rejection sólo con código, component y propiedades autorizadas.
- **Prueba futura:** T-I03: error con texto sensible sintético nunca exporta texto/stack/URL.

### TEL-FR-021 — Rendimiento

WHEN finaliza una operación frontend relevante para las métricas aprobadas, THE system SHALL capturar su duración o medida de rendimiento correspondiente.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P1.
- **Dependencias:** B01, B08, B06; ADR relacionados en plan. **Eventos:** frontend_timing_measured.
- **Aceptación:** Duración monotónica, unidad aprobada y operación concreta; ninguna medición inventada.
- **Prueba futura:** T-I04: performance.now mock y terminal de operación.

### TEL-FR-022 — Navegación

WHEN el usuario accede a una sección principal del backoffice, THE system SHALL capturar el evento de navegación establecido en el catálogo.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08, B06; ADR relacionados en plan. **Eventos:** navigation_viewed.
- **Aceptación:** Evento navigation_viewed una vez por vista normalizada permitida; no UUID/query/hash libre.
- **Prueba futura:** T-I05: hash routing y refresco; enum inválido rechazado.

### TEL-FR-023 — Autenticación

WHERE el plan aprobado incluya eventos de autenticación, THE system SHALL capturarlos en los puntos centralizados de autenticación, evitando instrumentaciones repetidas en cada página.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08, B06; ADR relacionados en plan. **Eventos:** authentication_failed, authentication_succeeded, session_started, session_ended.
- **Aceptación:** Sólo eventos auth aprobados en frontera central; conexión UI no equivale a validar JWT.
- **Prueba futura:** T-I06: 401/éxito real sin leer secretos ni repetir por página.

### TEL-FR-024 — Web Vitals

WHERE existan eventos Web Vitals aprobados o se autorice su incorporación al contrato, THE system SHALL capturarlos utilizando mecanismos compatibles con el framework actual.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P1.
- **Dependencias:** B01, B08, B06; ADR relacionados en plan. **Eventos:** frontend_timing_measured.
- **Aceptación:** Sólo métricas enum del esquema y framework existente; no nueva librería automática.
- **Prueba futura:** T-I07: métrica/unidad permitida; no URL libre.

### TEL-FR-025 — Allowlist

THE system SHALL enviar únicamente las propiedades autorizadas para cada `event_type` en `event-schemas.json`.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08; ADR relacionados en plan. **Eventos:** todos los eventos compatibles; sin catálogo aprobado.
- **Aceptación:** properties exactas por evento, campos requeridos y extras rechazados.
- **Prueba futura:** T-F12: parámetro extra, requerido ausente, enum fuera de dominio.

### TEL-FR-026 — Exclusión de PII

THE system SHALL evitar la captura de emails, nombres, contraseñas, tokens, datos sanitarios personales y otros datos sensibles no autorizados.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08, B03, B04; ADR relacionados en plan. **Eventos:** todos los eventos compatibles; sin catálogo aprobado.
- **Aceptación:** Sin nombres/email/secretos/texto clínico; seudónimos regionales sólo con B03 aprobado.
- **Prueba futura:** T-P01: corpus sintético de campos/valores prohibidos y revisión de productores.

### TEL-FR-027 — Validación del catálogo

IF se intenta capturar un evento desconocido o con propiedades no permitidas, THEN THE system SHALL aplicar una política explícita de rechazo o sanitización sin afectar el flujo de negocio.

- **Fuente:** prompt §5; contrato candidato Fase 1 para tipos/semántica. **Prioridad:** P0.
- **Dependencias:** B01, B08; ADR relacionados en plan. **Eventos:** todos los eventos compatibles; sin catálogo aprobado.
- **Aceptación:** Evento o properties inválidos rechazados íntegramente sin romper negocio.
- **Prueba futura:** T-F13: tipo desconocido/circular/BigInt/NaN, cero red, cero recursión.

## Requisitos no funcionales EARS candidatos

### TEL-NFR-001

THE system SHALL completar track sin red síncrona ni acceso a almacenamiento persistente.

- **Fuente:** prompt §6 rendimiento. **Prioridad:** P0. **Dependencias:** B01/B08 y ADR-001–008; límites numéricos candidatos requieren aprobación. **Eventos:** todos compatibles.
- **Aceptación:** 1000 capturas sintéticas de hasta 2 KiB: p95 <=2 ms en Chromium de desarrollo, registrando CPU/versión; presupuesto candidato sin medición actual.
- **Prueba futura:** T-N01; verificar cada condición descrita con mocks o revisión indicada.

### TEL-NFR-002

THE system SHALL limitar la memoria de eventos a una cuota acotada.

- **Fuente:** prompt §6 rendimiento/seguridad. **Prioridad:** P0. **Dependencias:** B01/B08 y ADR-001–008; límites numéricos candidatos requieren aprobación. **Eventos:** todos compatibles.
- **Aceptación:** Hipótesis a aprobar: <=200 eventos total pendiente+vuelo y <=256 KiB JSON UTF-8, <=2 KiB/evento, <=48 KiB/lote incluido wrapper; rechazar evento nuevo si excede; in-flight no se expulsa.
- **Prueba futura:** T-N02; verificar cada condición descrita con mocks o revisión indicada.

### TEL-NFR-003

WHILE existe un lote en vuelo o backoff, THE system SHALL mantener como máximo un transporte activo.

- **Fuente:** prompt §6 fiabilidad. **Prioridad:** P0. **Dependencias:** B01/B08 y ADR-001–008; límites numéricos candidatos requieren aprobación. **Eventos:** todos compatibles.
- **Aceptación:** Spies observan máximo 1 fetch; hidden no reenvía in-flight y entradas nuevas permanecen en pending.
- **Prueba futura:** T-N03; verificar cada condición descrita con mocks o revisión indicada.

### TEL-NFR-004

THE system SHALL enviar lotes de hasta 20 eventos sin realizar una petición por cada track.

- **Fuente:** prompt §§5.2/6. **Prioridad:** P0. **Dependencias:** B01/B08 y ADR-001–008; límites numéricos candidatos requieren aprobación. **Eventos:** todos compatibles.
- **Aceptación:** 1 evento espera timer/hidden; 20 disparan umbral; timers simultáneos no duplican IDs.
- **Prueba futura:** T-N04; verificar cada condición descrita con mocks o revisión indicada.

### TEL-NFR-005

IF falta configuración o contexto válido, THEN THE system SHALL deshabilitar exportación sin afectar el negocio.

- **Fuente:** prompt §6; B03/B04. **Prioridad:** P0. **Dependencias:** B01/B08 y ADR-001–008; límites numéricos candidatos requieren aprobación. **Eventos:** todos compatibles.
- **Aceptación:** Cero solicitudes y memoria de eventos no crece; contador local acotado; never fallback a otra región.
- **Prueba futura:** T-N05; verificar cada condición descrita con mocks o revisión indicada.

### TEL-NFR-006

IF el transporte falla, THEN THE system SHALL gestionar todo rechazo de promesa.

- **Fuente:** prompt §6 fiabilidad. **Prioridad:** P0. **Dependencias:** B01/B08 y ADR-001–008; límites numéricos candidatos requieren aprobación. **Eventos:** todos compatibles.
- **Aceptación:** Fetch/keepalive/serialización/timer fallan en mocks sin unhandledrejection ni ciclos de telemetría.
- **Prueba futura:** T-N06; verificar cada condición descrita con mocks o revisión indicada.

### TEL-NFR-007

THE system SHALL rechazar payloads fuera del tamaño aprobado antes de procesar eventos.

- **Fuente:** prompt §6 seguridad. **Prioridad:** P0. **Dependencias:** B01/B08 y ADR-001–008; límites numéricos candidatos requieren aprobación. **Eventos:** todos compatibles.
- **Aceptación:** Hipótesis <=48 KiB UTF-8, 1..20 eventos, vacío ->422 y bytes excedidos ->413; streams sin Content-Length también limitados antes de parse; no confiar sólo en header.
- **Prueba futura:** T-N07; verificar cada condición descrita con mocks o revisión indicada.

### TEL-NFR-008

THE system SHALL preservar autenticación y CORS existentes.

- **Fuente:** AGENTS; prompt §6. **Prioridad:** P0. **Dependencias:** B01/B08 y ADR-001–008; límites numéricos candidatos requieren aprobación. **Eventos:** todos compatibles.
- **Aceptación:** 401/403 conservados, origen no permitido no obtiene acceso; ningún token en URL/body/log; B05 resuelto sin hacer pública la ingestión.
- **Prueba futura:** T-N08; verificar cada condición descrita con mocks o revisión indicada.

### TEL-NFR-009

THE system SHALL validar envelope y properties usando el catálogo fuente sin mantenimiento manual duplicado.

- **Fuente:** prompt ADR-005. **Prioridad:** P0. **Dependencias:** B01/B08 y ADR-001–008; límites numéricos candidatos requieren aprobación. **Eventos:** todos compatibles.
- **Aceptación:** Generación o derivación comprobable desde JSON; prueba falla ante divergencia de nombre/required/tipo; no nueva dependencia por inferencia.
- **Prueba futura:** T-N09; verificar cada condición descrita con mocks o revisión indicada.

### TEL-NFR-010

THE system SHALL mantener independiente la interfaz track del receptor temporal.

- **Fuente:** prompt Fase 3. **Prioridad:** P0. **Dependencias:** B01/B08 y ADR-001–008; límites numéricos candidatos requieren aprobación. **Eventos:** todos compatibles.
- **Aceptación:** Mismos puntos de captura y firma funcionan al sustituir URL por receptor de prueba; ACK nunca significa commit durable.
- **Prueba futura:** T-N10; verificar cada condición descrita con mocks o revisión indicada.

### TEL-NFR-011

THE system SHALL permitir pruebas deterministas con datos sintéticos.

- **Fuente:** prompt §9. **Prioridad:** P0. **Dependencias:** B01/B08 y ADR-001–008; límites numéricos candidatos requieren aprobación. **Eventos:** todos compatibles.
- **Aceptación:** Reloj/UUID/fetch/keepalive/contexto inyectables internamente; cero red real y cero datos reales en suite unit.
- **Prueba futura:** T-N11; verificar cada condición descrita con mocks o revisión indicada.

### TEL-NFR-012

WHERE el navegador carece de una capacidad opcional, THE system SHALL degradar sin detener la aplicación.

- **Fuente:** prompt compatibilidad. **Prioridad:** P0. **Dependencias:** B01/B08 y ADR-001–008; límites numéricos candidatos requieren aprobación. **Eventos:** todos compatibles.
- **Aceptación:** keepalive, performance APIs y randomUUID ausentes: fallback aprobado o descarte local; no Math.random para identidad UUID. Matriz candidato Chromium/Firefox/WebKit actuales, soporte formal pendiente.
- **Prueba futura:** T-N12; verificar cada condición descrita con mocks o revisión indicada.

### TEL-NFR-013

THE system SHALL evitar que errores de validación y logging expongan datos del evento.

- **Fuente:** AGENTS; prompt logging. **Prioridad:** P0. **Dependencias:** B01/B08 y ADR-001–008; límites numéricos candidatos requieren aprobación. **Eventos:** todos compatibles.
- **Aceptación:** 422 redactado no refleja input/ctx/body; caplog no contiene marcadores secretos sintéticos; no envelope completo en logs.
- **Prueba futura:** T-N13; verificar cada condición descrita con mocks o revisión indicada.

### TEL-NFR-014

THE system SHALL mantener eventos personales dentro del contexto regional aprobado.

- **Fuente:** CONTEXT; Fase1 privacidad. **Prioridad:** P0. **Dependencias:** B01/B08 y ADR-001–008; límites numéricos candidatos requieren aprobación. **Eventos:** todos compatibles.
- **Aceptación:** Con clínica, endpoint regional y properties coinciden; sin clínica, null sólo en evento general clasificado y destino/ámbito HMAC autorizados; cambio de actor/contexto purga pendientes; no exportar mientras falte resolución.
- **Prueba futura:** T-N14; verificar cada condición descrita con mocks o revisión indicada.

## Contratos de eventos y API candidatos

Envelope JSON Fase 1: ocho campos requeridos y extras prohibidos. eventId UUID con patrón hex minúscula; timestamp date-time con zona y patrón del JSON (validar fecha real además de regex); sessionId UUID o null; userId ps_+64 hex o null según semántica de productor; event_type exacto del oneOf; schemaVersion constante 1.1.0; requestId UUID o null; properties propias del evento, cerradas y requeridas. Nulo no sustituye ausencia. La revisión 1.1.0 permite null sólo en los cinco eventos generales clasificados; clínica sin región resuelta se rechaza semánticamente. No se reproduce un segundo catálogo ni se alteran enums.

API implementada en el stub: POST /telemetry/events, body {"events":[...]}, respuesta 200 {"received":N}; aceptación de lote completo, sin aceptación parcial ni persistencia/dedup durable. 422 por forma/tipos/evento/semántica, 413 por exceso de bytes candidato, 401/403 conforme a política pendiente; errores sin reflejar input. Cuerpo raíz cerrado es propuesta a aprobar. Una recepción repetida válida puede volver a contar N: no prometer exactly-once. No debe emitir eventos de telemetría por procesar su propio endpoint.

TELEMETRY_ENDPOINT backend no define automáticamente el path FastAPI: finalidad candidata es referencia explícita al receptor temporal para diagnóstico/configuración y futura sustitución, sin forwarding externo ni persistencia. Su utilidad exacta y habilitación deben acordarse en ADR-006 para evitar una variable muerta. Frontend estático usa configuración pública runtime propuesta; Next.js, sólo si ese adaptador se autoriza, NEXT_PUBLIC_TELEMETRY_ENDPOINT de build. Ninguna variable ni .env se modifica ahora.

## Matriz de trazabilidad aprobada

**No disponible:** cero eventos con aprobación contractual verificable. El gate B01 impide presentar una matriz de catálogo aprobado. A continuación se registra exclusivamente un inventario diagnóstico de los 39 candidatos existentes, para localizar huecos y facilitar la revisión. Obligatorio Sí significa clasificación documental de Fase 1, no aprobación actual. Todos los productores e instrumentaciones están pendientes de aprobación; PLANNED/PROPOSED no acredita código.

| Event type candidato | Categoría | Origen | Obligatorio candidato | Properties exactas (todas required) | Trigger candidato | Instrumentation point / restricción | Requirement ID local | Task ID | Test futuro | Priority |
|---|---|---|---|---|---|---|---|---|---|---|
| `inbound_order_completed` | Inventory | MANDATORY_EXERCISE | Sí | jurisdiction, environment, operationId, movementId, itemId | Commit confirmado de movimiento de entrada asociado a operación lógica de entrada | sin módulo de inventario vigente (B06); fuente: memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2; componente PLANNED | TEL-FR-018 | TASK-TEL-030 | T-CAT-001: positivo/negativo y trigger único | P0 |
| `outbound_order_completed` | Inventory | MANDATORY_EXERCISE | Sí | jurisdiction, environment, operationId, movementId, itemId | Commit confirmado de movimiento de salida asociado a operación lógica de salida | sin módulo de inventario vigente (B06); fuente: memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2; componente PLANNED | TEL-FR-018 | TASK-TEL-030 | T-CAT-002: positivo/negativo y trigger único | P0 |
| `inventory_validation_failed` | Inventory | MANDATORY_EXERCISE | Sí | jurisdiction, environment, operationId, reasonCode | Validador rechaza una operación antes de persistir | sin módulo de inventario vigente (B06); fuente: memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2; componente PLANNED | TEL-FR-018 | TASK-TEL-030 | T-CAT-003: positivo/negativo y trigger único | P0 |
| `stock_direct_update_rejected` | Inventory | MANDATORY_EXERCISE | Sí | jurisdiction, environment, operationId, channel | Detector explícito de campo stock rechaza escritura sin movimiento; nunca inferirlo de cualquier 422 | sin módulo de inventario vigente (B06); fuente: memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2; componente PLANNED | TEL-FR-018 | TASK-TEL-030 | T-CAT-004: positivo/negativo y trigger único | P0 |
| `inventory_threshold_activated` | Inventory | MANDATORY_EXERCISE | Sí | jurisdiction, environment, itemId, scopeId, episodeId | Stock derivado cruza de >= a < umbral aprobado, después de commit | sin módulo de inventario vigente (B06); fuente: memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2; componente PLANNED | TEL-FR-018 | TASK-TEL-030 | T-CAT-005: positivo/negativo y trigger único | P0 |
| `inventory_viewed` | Inventory | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, view | Consulta autorizada de existencias finaliza | sin módulo de inventario vigente (B06); fuente: memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2; componente PLANNED | TEL-FR-018 | TASK-TEL-030 | T-CAT-006: positivo/negativo y trigger único | P1 |
| `product_selected` | Inventory | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, flowId | Selección explícita de artículo en futuro flujo UI | sin módulo de inventario vigente (B06); fuente: memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2; componente PROPOSED | TEL-FR-018 | TASK-TEL-030 | T-CAT-007: positivo/negativo y trigger único | P1 |
| `order_started` | Inventory | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, flowId, direction | Inicio explícito de flujo lógico de entrada/salida; no equivale a pedido comercial | sin módulo de inventario vigente (B06); fuente: memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2; componente PROPOSED | TEL-FR-018 | TASK-TEL-030 | T-CAT-008: positivo/negativo y trigger único | P1 |
| `order_abandoned` | Inventory | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, flowId, lastStep, durationMs | Procesador cierra flujo sin terminal tras 30 min de inactividad propuesta | sin módulo de inventario vigente (B06); fuente: memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2; componente PROPOSED | TEL-FR-018 | TASK-TEL-030 | T-CAT-009: positivo/negativo y trigger único | P1 |
| `inventory_adjustment_completed` | Inventory | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, movementId, operationId | Commit de ajuste materializado como movimiento | sin módulo de inventario vigente (B06); fuente: memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2; componente PLANNED | TEL-FR-018 | TASK-TEL-030 | T-CAT-010: positivo/negativo y trigger único | P1 |
| `inventory_threshold_cleared` | Inventory | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, episodeId, itemId, scopeId | Cruce de < a >= umbral comparable tras movimiento | sin módulo de inventario vigente (B06); fuente: memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2; componente PROPOSED | TEL-FR-018 | TASK-TEL-030 | T-CAT-011: positivo/negativo y trigger único | P1 |
| `inventory_reconciliation_failed` | DataQuality | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, checkId, check | Verificador encuentra proyección distinta a suma de movimientos comparables | sin módulo de inventario vigente (B06); fuente: memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2; componente PROPOSED | TEL-FR-018 | TASK-TEL-030 | T-CAT-012: positivo/negativo y trigger único | P1 |
| `authentication_failed` | Authentication | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, reasonCode | Dependencia rechaza credenciales; código reducido, sin error JWT literal | frontera backend auth o connect/disconnect real según evento; no confundir conexión y autenticación; fuente: backend/app/auth/dependencies.py:get_current_actor; backend/app/auth/security.py:decode_access_token; componente IMPLEMENTED | TEL-FR-023 | TASK-TEL-034 | T-CAT-013: positivo/negativo y trigger único | P1 |
| `authentication_succeeded` | Authentication | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, channel | Primera validación satisfactoria de identidad en una sesión conceptual; no login real | frontera backend auth o connect/disconnect real según evento; no confundir conexión y autenticación; fuente: backend/app/auth/dependencies.py:get_current_actor; backend/app/auth/security.py:decode_access_token; componente IMPLEMENTED | TEL-FR-023 | TASK-TEL-034 | T-CAT-014: positivo/negativo y trigger único | P1 |
| `session_started` | Authentication | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, application | UI conecta credenciales en memoria y primera lectura autorizada confirma acceso | frontera backend auth o connect/disconnect real según evento; no confundir conexión y autenticación; fuente: uis/backoffice/operational-incidents/app.js; frontend/app/internal/incident-history/workspace.js; componente PARTIAL | TEL-FR-023 | TASK-TEL-023 | T-CAT-015: positivo/negativo y trigger único | P1 |
| `session_ended` | Authentication | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, reasonCode | Desconexión explícita de UI; cierre del navegador es desconocido, no logout servidor | frontera backend auth o connect/disconnect real según evento; no confundir conexión y autenticación; fuente: frontend/app/internal/incident-history/workspace.js; README del backoffice; componente PARTIAL | TEL-FR-023 | TASK-TEL-023 | T-CAT-016: positivo/negativo y trigger único | P1 |
| `authorization_denied` | Authorization | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, reasonCode, operation | Dependencia o política devuelve denegación de capacidad/ámbito | fuente servidor/worker o futura; no emisión UI sustituta; fuente: backend/app/auth/dependencies.py; backend/app/auth/policies.py; componente IMPLEMENTED | TEL-FR-018 | TASK-TEL-032 | T-CAT-017: positivo/negativo y trigger único | P0 |
| `navigation_viewed` | Navigation | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, view | Vista lógica cambia y queda visible; excluir UUID y query string | uis/backoffice/operational-incidents/app.js: renderRoute; Management carga de sección; región/contexto pendientes; fuente: uis/backoffice/operational-incidents/app.js; uis/backoffice/management/index.html; frontend/app/page.js; componente IMPLEMENTED | TEL-FR-022 | TASK-TEL-026 | T-CAT-018: positivo/negativo y trigger único | P1 |
| `frontend_timing_measured` | Performance | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, metric, value, view | API Performance reporta métrica completa de navegación visible | adaptador performance del frontend real pendiente; fuente: frontend/app/layout.js; audit/README.md (evidencia de auditoría, no RUM); componente PROPOSED | TEL-FR-021, TEL-FR-024 | TASK-TEL-027 | T-CAT-019: positivo/negativo y trigger único | P1 |
| `api_request_completed` | Performance | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, route, statusCode, durationMs | Respuesta ASGI finaliza; middleware futuro calcula duración monotónica | fuente servidor/worker o futura; no emisión UI sustituta; fuente: backend/app/main.py; routers montados; componente IMPLEMENTED | TEL-FR-018 | TASK-TEL-032 | T-CAT-020: positivo/negativo y trigger único | P1 |
| `application_error_observed` | Errors | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, component, reasonCode | Excepción no controlada clasificada en frontera; no duplicar HTTP esperado | listeners globales futuros; lazy-error-boundary existente sólo como punto parcial; fuente: backend/app/main.py; frontend/app/internal/incident-history/lazy-error-boundary.js; componente PARTIAL | TEL-FR-020 | TASK-TEL-024 | T-CAT-021: positivo/negativo y trigger único | P1 |
| `catalog_cache_observed` | Performance | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, hits, misses, bypasses, windowSeconds | Corte agregado de contadores por worker cada 5 min | fuente servidor/worker o futura; no emisión UI sustituta; fuente: backend/app/catalogs/cache.py:CatalogCache; componente IMPLEMENTED | TEL-FR-018 | TASK-TEL-032 | T-CAT-022: positivo/negativo y trigger único | P1 |
| `service_health_checked` | Reliability | MANDATORY_BRIEFING | Sí | jurisdiction, environment, check, outcome, durationMs | Sonda futura invoca /health o /status con timeout | fuente servidor/worker o futura; no emisión UI sustituta; fuente: CONTEXT.md Tecnología; backend/app/main.py:health,status; componente PARTIAL | TEL-FR-018 | TASK-TEL-032 | T-CAT-023: positivo/negativo y trigger único | P0 |
| `alert_triggered` | Operations | MANDATORY_BRIEFING | Sí | jurisdiction, environment, episodeId, rule | Regla aprobada cruza umbral y crea episodio | fuente servidor/worker o futura; no emisión UI sustituta; fuente: CONTEXT.md Tecnología y Dirección; componente PLANNED | TEL-FR-018 | TASK-TEL-032 | T-CAT-024: positivo/negativo y trigger único | P0 |
| `notification_delivery_completed` | Operations | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, notificationId, channel, outcome | Proveedor futuro confirma entrega o fallo terminal sin destinatario | fuente servidor/worker o futura; no emisión UI sustituta; fuente: CONTEXT.md Experiencia del Paciente y Acceso; no integración en código; componente PROPOSED | TEL-FR-018 | TASK-TEL-032 | T-CAT-025: positivo/negativo y trigger único | P1 |
| `job_run_completed` | Operations | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, runId, job, outcome, durationMs | Job futuro termina con resultado o timeout | fuente servidor/worker o futura; no emisión UI sustituta; fuente: CONTEXT.md Tecnología; data/pipelines/README.md; componente PROPOSED | TEL-FR-018 | TASK-TEL-032 | T-CAT-026: positivo/negativo y trigger único | P1 |
| `data_integrity_checked` | DataQuality | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, check, outcome | Validador de referencias o futura comprobación completa un resultado | fuente servidor/worker o futura; no emisión UI sustituta; fuente: backend/app/reference_data/validation.py; backend/app/management/router.py; componente PARTIAL | TEL-FR-018 | TASK-TEL-032 | T-CAT-027: positivo/negativo y trigger único | P1 |
| `incident_created` | Operations | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, incidentId, auditId | Commit de incidencia creada | backend/app/incidents/router.py tras commit; B03/B06/B08, no inventar evidencia UI; fuente: backend/app/incidents/router.py; backend/app/incidents/history.py; componente IMPLEMENTED | TEL-FR-019 | TASK-TEL-031 | T-CAT-028: positivo/negativo y trigger único | P1 |
| `incident_transitioned` | Operations | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, incidentId, auditId | Commit de transición autorizada | backend/app/incidents/router.py tras commit; B03/B06/B08, no inventar evidencia UI; fuente: backend/app/incidents/router.py; backend/app/incidents/history.py; componente IMPLEMENTED | TEL-FR-019 | TASK-TEL-031 | T-CAT-029: positivo/negativo y trigger único | P1 |
| `incident_assigned` | Operations | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, incidentId, auditId | Commit de asignación autorizada | backend/app/incidents/router.py tras commit; B03/B06/B08, no inventar evidencia UI; fuente: backend/app/incidents/router.py; backend/app/incidents/history.py; componente IMPLEMENTED | TEL-FR-019 | TASK-TEL-031 | T-CAT-030: positivo/negativo y trigger único | P1 |
| `management_mutation_completed` | Compliance | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, auditId, resource, action | Commit de mutación con ManagementAuditEvent persistido | fuente servidor/worker o futura; no emisión UI sustituta; fuente: backend/app/management/router.py; backend/app/management/service.py; componente IMPLEMENTED | TEL-FR-018 | TASK-TEL-032 | T-CAT-031: positivo/negativo y trigger único | P1 |
| `audit_accessed` | Compliance | MANDATORY_BRIEFING | Sí | jurisdiction, environment, surface | Consulta autorizada de auditoría finaliza, sin exportar snapshots | fuente servidor/worker o futura; no emisión UI sustituta; fuente: CONTEXT.md Cumplimiento; backend/app/incidents/router.py:incident_audit; backend/app/management/router.py:list_management_audit_events; componente PARTIAL | TEL-FR-018 | TASK-TEL-032 | T-CAT-032: positivo/negativo y trigger único | P0 |
| `telemetry_contract_rejected` | DataQuality | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, reasonCode, producer | Validador futuro rechaza envelope o propiedades; diagnóstico sin payload | diagnóstico separado sin track recursivo; no nuevo canal implementado; fuente: Diseño conceptual de este hito; componente PROPOSED | TEL-FR-027 | TASK-TEL-032 | T-CAT-033: positivo/negativo y trigger único | P1 |
| `telemetry_delivery_failed` | Reliability | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, producer, reasonCode | Productor futuro agota reintentos acotados | diagnóstico separado sin track recursivo; no nuevo canal implementado; fuente: Diseño conceptual de este hito; componente PROPOSED | TEL-FR-027 | TASK-TEL-032 | T-CAT-034: positivo/negativo y trigger único | P1 |
| `appointment_period_aggregated` | BusinessAnalytics | MANDATORY_BRIEFING | Sí | jurisdiction, environment, aggregateId, periodStart, periodEnd, eligibleAppointments, noShows, attended, booked | Adaptador local aprobado cierra día con totales reconciliados | fuente servidor/worker o futura; no emisión UI sustituta; fuente: CONTEXT.md Experiencia del Paciente, Facturación, Operaciones, Personas y Dirección; sin módulos integrados; componente PLANNED | TEL-FR-018 | TASK-TEL-032 | T-CAT-035: positivo/negativo y trigger único | P1 |
| `billing_period_aggregated` | BusinessAnalytics | MANDATORY_BRIEFING | Sí | jurisdiction, environment, aggregateId, periodStart, periodEnd, adjudicatedClaims, rejectedClaims, collectedMinor, dueMinor, currency, stream | Adaptador local cierra periodo contable con cohorte reconciliada | fuente servidor/worker o futura; no emisión UI sustituta; fuente: CONTEXT.md Experiencia del Paciente, Facturación, Operaciones, Personas y Dirección; sin módulos integrados; componente PLANNED | TEL-FR-018 | TASK-TEL-032 | T-CAT-036: positivo/negativo y trigger único | P1 |
| `experience_period_aggregated` | BusinessAnalytics | MANDATORY_BRIEFING | Sí | jurisdiction, environment, aggregateId, periodStart, periodEnd, validResponses, satisfiedResponses | Encuestas locales aprobadas cierran día con agregado protegido | fuente servidor/worker o futura; no emisión UI sustituta; fuente: CONTEXT.md Experiencia del Paciente, Facturación, Operaciones, Personas y Dirección; sin módulos integrados; componente PLANNED | TEL-FR-018 | TASK-TEL-032 | T-CAT-037: positivo/negativo y trigger único | P1 |
| `workforce_period_aggregated` | BusinessAnalytics | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, aggregateId, periodStart, periodEnd, hiringDaysSum, filledRoles, departures, averageHeadcount, absenceHours, scheduledHours, expiredTraining, trainingEligible | Fuente RRHH autorizada produce cohorte semanal agregada | fuente servidor/worker o futura; no emisión UI sustituta; fuente: CONTEXT.md Experiencia del Paciente, Facturación, Operaciones, Personas y Dirección; sin módulos integrados; componente PLANNED | TEL-FR-018 | TASK-TEL-032 | T-CAT-038: positivo/negativo y trigger único | P1 |
| `clinical_workload_aggregated` | BusinessAnalytics | IDENTIFIED_OPPORTUNITY | No | jurisdiction, environment, aggregateId, periodStart, periodEnd, documentationMinutes, operatorDays | Fuente clínica autorizada produce sumas diarias sin notas ni personas | fuente servidor/worker o futura; no emisión UI sustituta; fuente: CONTEXT.md Experiencia del Paciente, Facturación, Operaciones, Personas y Dirección; sin módulos integrados; componente PLANNED | TEL-FR-018 | TASK-TEL-032 | T-CAT-039: positivo/negativo y trigger único | P1 |

### Cobertura empresarial que la Fase 2 no puede acreditar

Tecnología: service_health_checked/alert_triggered requieren sondas/reglas, no navegación. Cumplimiento: audit_accessed requiere lectura autorizada en servidor. Dirección/Acceso: appointment_period_aggregated cubre volumen/reservas/no-shows con fuente y denominador de cohorte; billing_period_aggregated cubre rechazo/cobro/ingresos separados por moneda; experience_period_aggregated cubre satisfacción con definición aprobada. Estos agregados no existen y no se producen desde visitas UI. Workforce/clinical_workload son oportunidades de Fase 1 aunque CONTEXT describe necesidades; no se cambian unilateralmente a obligatorios. Inventario es obligación del ejercicio de Fase 1, no del briefing empresarial.

Fórmulas, nulos, periodos y comparaciones permanecen en telemetry-plan.md §§Metric Definitions/KPI: no-shows/eligibleAppointments, rejectedClaims/adjudicatedClaims, collectedMinor/dueMinor, satisfiedResponses/validResponses; denominador cero -> unavailable, nunca 0; no sumar USD/GBP ni promediar ratios por clínica. Reloj monotónico para duraciones y timestamp del hecho para periodos. No se calcula reporting en esta fase.

## Privacidad, casos límite y errores

Rechazar evento entero ante campo extra/tipo inválido; no eliminar required para pasar validación. Allowlists no detectan secretos dentro de strings permitidos: usar enums/seudónimos autorizados, extracción mínima y revisión de valores por productor. No copiar mensajes de excepción, stacks, URLs dinámicas, consultas, títulos/descripciones ni respuesta API completa. Identificadores seudónimos siguen siendo personales. No usar una clave HMAC en frontend ni seudónimo estable transfronterizo.

Disconnect/cambio de identidad: cerrar contexto y descartar cola anterior sin usar credenciales nuevas; navegación full reload pierde memoria y no representa logout. Un timer no sobrevive suspensión de pestaña; deadline 10 s significa elegibilidad con event loop disponible. Offline conserva lote en backoff limitado; si caduca intento se descarta sin bloquear UI. Ningún retry modifica eventId, timestamp o properties. Eventos nuevos se guardan aparte. ACK inválido (received incorrecto/no JSON) no es éxito, política recuperable acotada propuesta. Fetch keepalive al ocultar usa Bearer; abort/error conserva pending mientras exista contexto y se aplica retry acotado. La destrucción de página puede impedir observar ACK aunque haya recepción. No reenvía lote HTTP activo.

## Especificación adicional de contexto autenticado (propuesta de revisión)

Véase [diseño concreto de contexto y claves](./plan.md#diseño-concreto-propuesto--contexto-de-servidor-y-claves). Es contrato separado propuesto POST /telemetry/context y header X-Telemetry-Context; no modifica el envelope 1.1.0 ni constituye autorización de endpoint/CORS/configuración. Contexto firmado, mínimo y en memoria; cliente no recibe UUID operativo/clave y Bearer sigue siendo obligatorio.

### TEL-FR-028 — Contexto autenticado de telemetría

WHEN un usuario autenticado solicita contexto general o de clínica autorizado, THE system SHALL proporcionar un contexto firmado ligado al actor, sesión e instalación sin entregar claves ni identificadores operativos en la respuesta.

- **Fuente:** decisiones HMAC/región del desarrollador; Actor/Clinic/Jurisdiction existentes; diseño concreto plan. **Prioridad:** P0.
- **Dependencias:** B03/B04/B08, revisión Tecnología/Claire y autorización del nuevo contrato. **Eventos:** cinco generales y eventos clínicos que se autoricen posteriormente.
- **Aceptación:** body clinicId requerido/UUID o null; respuesta cerrada contextToken/sessionId/userId/jurisdiction/schemaVersion/expiresAt con no-store; sub/clínica UUID no presentes en claims; errores seguros y ninguna escritura telemetry.
- **Prueba futura:** T-CTX-001–004/008/010; resolución con mocks sintéticos y auth vigente.

### TEL-FR-029 — Verificación de contexto por lote

WHEN el receptor recibe un lote autenticado, THE system SHALL comprobar que todos sus eventos pertenecen al contexto firmado vigente del actor y de la instalación receptora.

- **Fuente:** diseño de confianza y segregación regional; contrato 1.1.0. **Prioridad:** P0.
- **Dependencias:** TEL-FR-028 y B08. **Eventos:** lote completo, sin mezcla de contextos.
- **Aceptación:** validar Bearer/firma/issuer/audience/keyring/TTL, binding actor, sid/userId/region/env/jurisdiction y versión; rechazar lote atómicamente ante discrepancia; no autorización clínica ampliada por token ni fallback general.
- **Prueba futura:** T-CTX-003–005/010 con manipulación, actor ajeno y mezcla de contextos.

### TEL-NFR-015 — Separación y fallo seguro de claves

IF falta una clave válida o la región de instalación, THEN THE system SHALL deshabilitar la emisión de contexto y la exportación sin utilizar claves o destinos alternativos.

- **Fuente:** decisión regional/HMAC y mínimo privilegio AGENTS. **Prioridad:** P0.
- **Dependencias:** TEL-FR-028 y configuración expresamente autorizada. **Eventos:** todos los del productor autenticado.
- **Aceptación:** 503 seguro/cero export; claves >=32 bytes separadas región/entorno/finalidad; prefijos/versiones canónicas; firma/bindings/user HMAC distintos; rotación según TTL y revocación revisados; no secreto en cliente/log/config versionada.
- **Prueba futura:** T-CTX-008–010 y revisión Tecnología/Claire; vectores sólo con claves sintéticas temporales.


## Criterios de aceptación y Definition of Done

| ID | Criterio documental / futuro | Evidencia exigida |
|---|---|---|
| DOC-01 | Rutas, estado y discrepancias inspeccionados | Baseline de plan, lecturas y Git limpio inicial |
| DOC-02 | Sólo tres documentos y ninguna app/protegido cambiado | Status completo, diff tracked y lectura de untracked |
| DOC-03 | Requisitos/tareas trazables, sin afirmar aprobación o pruebas futuras | 29 FR +15 NFR; 39 candidatos exactos; tareas TODO |
| DOC-04 | Respeto del gate | B01–B08, ADR pendientes, matriz aprobada no inventada |
| FUT-01 | Gate de Fase 1 y perfil temporal aprobados | Versiones/hashes/revisores y resolución B01/B02 |
| FUT-02 | Contexto, privacidad, región, auth y transporte resueltos | Revisión Tecnología/Claire B03–B08 |
| FUT-03 | Stub probado antes de servicio | T-B01–B06, T-N07–09/13, OpenAPI, cero escrituras |
| FUT-04 | Captura, cola, transporte y errores probados | T-F01–13/T-N01–14, mocks deterministas |
| FUT-05 | Cobertura acordada y recepción real verificada | T-I01–07, matriz aprobada, DevTools sintético sin secretos |
| FUT-06 | Revisión final válida y scope autorizado | validate-delivery PASS para alcance aprobado, diff revisado |

BLOCKED no equivale a terminado ni a PASS. Esta ejecución entrega un expediente revisable bloqueado; FUT-01–06 no están satisfechos. No existe evidencia DevTools ni implementación frontend; las pruebas de implementación backend constan en la sección de cierre. Riesgos principales: pérdidas inevitables en memoria/keepalive, duplicados, cobertura empresarial imposible sin fuentes, retención de logs, suplantación de contexto del cliente, staging y regiones, y cambios protegidos fuera del alcance.

Fingerprint observado `docs/telemetry/telemetry-plan.md` SHA-256: `caa3bd9efb3aee53c512e4463a2b299a913bea03d12a909c15caebbf3aa4313b`. Esto identifica la revisión inspeccionada; no acredita aprobación.

Fingerprint observado `docs/telemetry/event-schemas.json` SHA-256: `f70ee5a208fc4c3e925b12eaed3fd5b5899c49e8277f25181bf5cea5330c9eec`. Esto identifica la revisión inspeccionada; no acredita aprobación.


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
