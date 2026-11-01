# Estado final de entrega — Telemetry Event Capture

Fecha2026-11-01. Rama feature/telemetryEventCapture. Revisión/documentación autorizada mediante «hazlo». Alcance local reducido implementado y revisado; **la cobertura integral original no está cerrada**. No commit/push/PR, aprobación de producción ni certificación HIPAA/UK GDPR.

## Contrato y arquitectura vigentes

Contrato1.2.0;39 tipos,14 nullable y25 US/UK-only; tres copias JSON byte-identical. SHA256 del artefacto revisado: a7fccbdc278b83472eb039183fb87e9c6882aa238fa71b8fd6192f4b0d2db2bf. Este hash registra el estado inspeccionado, no inventa una aprobación externa del hash.

API real backend/app, backoffice uis/backoffice/operational-incidents y Management; no servicios duplicados. Tecnología validó un front/back compartido; HMAC servidor y no entrega de claves al front aprobados por Cumplimiento en conversación. Clínica determina US/UK; null general no sustituye fallo clínico. Keyrings separados general/US/UK y14 claves activas; contexto firmado y revalidación clínica, sin cambiar auth/policies.

track público permite cinco tipos. Diagnósticos frontend2 sólo internos, producer=frontend/contexto general/session/userHMAC/requestId=null; backend rechaza afirmaciones api/worker/clínicas desde navegador. Fuentes servidor se entregan por cola interna, sin aceptar hechos de negocio browser.

Memoria frontend total200/256KiB incluyendo vuelo, normal180/224 y diagnóstico20/32; lotes20 o10s, un vuelo, timeout5s,3 retries normales/0 diagnósticos. Servidor: cola normal y canal diagnóstico separados200/256KiB cada uno, evento2KiB/body48KiB,20/10/un vuelo por canal/timeout1s/sin retry local.16 preparaciones/100ms; cache sampler300s. No persistencia, forwarding ni dedup durable; referencias endpoint no son colectores activos.

## Matriz de cobertura vigente

COVERED_IN_SCOPE significa productor verificado en el alcance de su nota, **no** cobertura universal del evento/requisito.

| Tipo | Fuente | Estado | Cobertura y límite |
|---|---|---|---|
| api_request_completed | backend | COVERED_IN_SCOPE | Cuatro GET clínicos tras final send; otras rutas pendientes |
| application_error_observed | frontend | COVERED_IN_SCOPE | Enums reducidos, sin stack/URL; no clasificación exhaustiva |
| audit_accessed | backend | COVERED_IN_SCOPE | Incidencia y Management filtrado por clínica; global/inactiva pendiente |
| authentication_failed | backend | COVERED_IN_SCOPE | Missing/invalid/expired reducidos; /telemetry excluida |
| authentication_succeeded | backend | COVERED_IN_SCOPE | Primera credencial vigente por proceso; no deduplicación SSO/global |
| authorization_denied | backend | COVERED_IN_SCOPE | require_capability; denegaciones contextuales pendientes |
| catalog_cache_observed | backend | COVERED_IN_SCOPE | Delta300s por proceso; no agregación entre réplicas |
| data_integrity_checked | backend | COVERED_IN_SCOPE | event_contract al arranque; references/historical_coverage pendientes |
| frontend_timing_measured | frontend | COVERED_IN_SCOPE | LCP/CLS/INP condicionales; contexto general vigente requerido |
| incident_assigned | backend | COVERED_IN_SCOPE | Tras commit; capture best effort |
| incident_created | backend | COVERED_IN_SCOPE | Tras commit; fuente clínica activa revalidada |
| incident_transitioned | backend | COVERED_IN_SCOPE | Tras commit; audit persistente conservado |
| management_mutation_completed | backend | COVERED_IN_SCOPE | Sólo clínicas, jurisdicción histórica; otros maestros/Compliance pendientes |
| navigation_viewed | frontend | COVERED_IN_SCOPE | Vistas allowlist; summary omitida sin valor contractual |
| service_health_checked | backend | COVERED_IN_SCOPE | /health/status bajo demanda; sonda programada no implementada |
| session_ended | frontend | COVERED_IN_SCOPE | Desconexión explícita best effort; cierre navegador no garantiza logout |
| session_started | frontend | COVERED_IN_SCOPE | Conexión UI con contexto autorizado; no login SSO |
| telemetry_contract_rejected | backend/frontend | COVERED_IN_SCOPE | Schema genérico, canales sin recursión; desglose fino pendiente |
| telemetry_delivery_failed | backend/frontend | COVERED_IN_SCOPE | Terminal/cuota reducidos; recepción y diagnóstico best effort |

Los20 restantes conservan DEFERRED_NO_SOURCE aprobado en [deferred-domain-scope.md](./deferred-domain-scope.md):12 inventario,3 motores y5 agregadores.9 obligatorios (5 ejercicio+4 briefing) y11 oportunidades. Ninguno pasa a DONE ni satisface TEL-FR-018. Reentrada requiere fuente real aprobada, reglas/cohortes/contexto y pruebas, no clics o datos ficticios presentados como negocio real.

## Resolución actual de gates originales

| Gate | Disposición local | Pendiente que no se da por aprobado |
|---|---|---|
| B01 | Contrato1.2.0 y lotes concretos autorizados en conversación, modelos sincronizados | No se certifica aprobación global de toda Fase1 ni de todas las fuentes |
| B02 |20/10 y pérdidas best effort documentados/aprobados | STREAM/alertas/durabilidad no implementados |
| B03 | UUID autenticado→HMAC servidor/contexto firmado aprobados | Gestor/rotación operativa y SSO de producción |
| B04 | Clínica/USUK y generalesnull; backend compartido validado Tecnología | Tratamiento real transfronterizo, ubicación/retención/procesadores; staging no exporta |
| B05 | fetch Bearer/keepalive implementado y probado local | Entornos productivos/otras topologías no autorizados |
| B06 |20 fuentes ausentes explícitamente aplazadas | Obligaciones empresariales/ejercicio permanecen pendientes |
| B07 | Stub no persiste envelopes; logging reducido y límites revisados | Retención de Uvicorn/infra externa y política productiva no certificadas |
| B08 | Archivos/configuración/lotes protegidos y actualización local autorizados expresamente | No autorización general para datos reales, infra futura, commit/push/PR/producción |

## Estados actuales de tareas (no modificar Estado inicial histórico)

| Tareas | Estado de entrega | Evidencia/límite |
|---|---|---|
|001–003|RESOLVED_FOR_LOCAL_SCOPE|Decisiones y gates anteriores; no aprobación total Fase1/producción|
|004–005|REVIEWED_SCOPED|Contrato/modelos sincronizados y matriz39;20 sin productor|
|006–021|IMPLEMENTED_SCOPED|Receptor, config local, validación, cola,20/10/ACK/retries/cleanup/keepalive; límites vigentes arriba|
|022|PARTIAL|RequestId sólo cuatro lecturas clínicas y eventos técnicos asociados; no correlación integral|
|023–025|IMPLEMENTED_SCOPED|Lifecycle UI y errores reducidos; no SSO/logout universal|
|026–027|IMPLEMENTED_SCOPED|Vistas allowlist y métricas frontend compatibles; summary/API incompatible se omite|
|028|VALIDATED_SCOPED|Suites Node/ASGI, región/credenciales/cierre/fallos|
|029|REVIEWED_WITH_GAPS|19 fuentes y20 aplazados, cobertura obligatoria no cumplida|
|030|DEFERRED_NO_SOURCE|12 tipos inventario; no código de inventario vigente|
|031|IMPLEMENTED_SCOPED|Tres hechos de incidencias tras commit/auditoría real|
|032|PARTIAL|Productores internos implementados; otros dominios/ámbitos y sondeos pendientes|
|033|IMPLEMENTED_CONDITIONAL|LCP/CLS/INP cuando APIs/contexto lo permiten|
|034|PARTIAL|Autenticación observada/capacidades; contexto/SSO/global dedup no universal|
|035|VALIDATED_SCOPED|74 Node/258 backend/161 PostgreSQL/113 contratos y Chrome local; no todos los navegadores/escenarios|
|036|REVIEWED_DOCUMENTATION_ONLY|Expediente final y texto de entrega preparado; no PR creado|
|037|PARTIAL|Separación de claves/contexto local; gestión/rotación productiva pendiente|

## Requisitos vigentes del alcance reducido (EARS)

- WHEN un frontend conectado captura uno de sus cinco tipos públicos, THE system SHALL construir y validar un envelope1.2.0 cerrado con contexto firmado e identidad seudónima, sin copiar datos sanitarios o texto libre.
- WHEN un buffer alcanza20 eventos o el primero permanece10s pendiente con event loop disponible, THE system SHALL programar envío por ámbito dentro de los límites vigentes, evitando vuelos duplicados.
- IF un evento normal falla validación o su lote falla de forma terminal, THE system SHALL intentar un diagnóstico reducido por su canal interno, sin recursión y sólo con contexto válido cuando es browser.
- WHEN una operación de incidencias aprobada confirma commit, THE system SHALL intentar su evento post-commit sin modificar respuesta/auditoría si telemetría falla.
- WHILE la telemetría está deshabilitada o su configuración no es válida, THE system SHALL mantener los productores opcionales inactivos sin habilitar caminos alternativos de acceso.
- WHEN una clínica no puede validarse, THE system SHALL descartar la captura clínica sin atribuirla a null u otra región.
- WHEN se cierra una generación de identidad, THE system SHALL cancelar y descartar su memoria/timers sin usar las credenciales posteriores.
- WHERE no existe dominio fuente, THE system SHALL conservar el productor como DEFERRED_NO_SOURCE y declarar el requisito pendiente, sin simular cobertura.

## Evidencia final y límites

Último código:74 Node PASS,258 backend PASS (8 integraciones omitidas sólo sinDB),161 PostgreSQL16 sintético/tmpfs PASS (todas las integraciones),113 contratos/serialización/OpenAPI/entrada/Compliance/catálogos PASS. Recuentos solapados, no sumarlos como pruebas únicas. Imagen test051867c3d096; backend local a3a6b9691040.

Chrome real: conexión incidencias, Management4 catálogos, recepción200 de navigation20/schema20+1/delivery1;22 diagnósticos, buffers0.403 simulado exclusivamente en adaptador experimental, no fallo real backend. Espera10502ms no es medición del instante exacto ni benchmark. Backend contrato1.2.0/check_contractok, health/status200. Actualización conjunta sin db-init/DB mutation. Evidencia [frontend-diagnostics.md](./frontend-diagnostics.md) y [local-activation-validation.md](./local-activation-validation.md).

Revisión final es documental: no nuevos cambios de código desde pruebas/activación; no repetir suites sin motivo. Copias/version/censo39/19+20/enlaces y diff comprobados. Archivos empresariales, Memory Bank/Rules, .env real, migraciones/authpolicies no modificados en esta revisión. Historial conservado e identificado para evitar confundir propuestas1.1.0/TODO con estado actual.

## Texto de entrega preparado (sin crear PR)

Título: Telemetry Event Capture — captura local segura y diagnósticos en backoffice compartido

El backoffice de incidencias y Management disponen de captura efímera20/10 con contexto firmado, identidad HMAC servidor y jurisdicción clínica US/UK. El receptor FastAPI valida lotes sin persistir ni reenviar; productores internos observan hechos confirmados y diagnósticos separados evitan recursión. API y UI locales están coordinadas en contrato1.2.0.

Validación:74 Node,258 backend,161 PostgreSQL sintético y113 contratos pasan; Chrome confirma recepción real y limpieza. Alcance reducido:19 tipos con cobertura acotada y20 explícitamente aplazados por falta de fuente. Nueve aplazados son obligatorios, por lo que no se declara cumplimiento integral del prompt. Sin garantía durable, producción, transferencia sanitaria aprobada ni cambio a SSO.

## Disposición final

La revisión del alcance local y su documentación queda preparada para entrega con brechas declaradas. **No presentar el proyecto completo ni TEL-FR-018 como terminado.** Completar cobertura clínica/global/otros maestros requiere nuevas decisiones y autorizaciones; las fuentes aplazadas requieren proyectos propios. Commit/push/PR y promoción siguen sujetos a autorización expresa.
