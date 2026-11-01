# TASKS — Telemetry Event Capture, Fase 2

**Estado vigente — revisión final local (2026-11-01):** implementado y validado dentro del alcance reducido autorizado. Contrato1.2.0,39 tipos:19 con fuente al menos parcial y20 DEFERRED_NO_SOURCE aprobado. Un frontend/backoffice compartido y un backend; HMAC exclusivamente servidor, jurisdicción clínica autoritativa y null técnico general. Captura20/10 efímera, recepción no durable. Admisión browser5 + dos diagnósticos internos frontend restringidos; servidor admite sus hechos por canal propio. Backend/backoffice locales actualizados y Chrome sintético validado.

**La cobertura integral original NO está terminada:**9 de los20 diferidos son obligatorios; TEL-FR-018 sigue pendiente. Hay además brechas de los19 tipos actuales, detalladas en [delivery-status.md](./delivery-status.md). La aprobación de aplazamiento no equivale a requisitos satisfechos, producción ni cumplimiento normativo.

La matriz y estados vigentes están en [delivery-status.md](./delivery-status.md); la cronología que sigue conserva las propuestas y evidencias de cada revisión. Sus menciones a «actual», TODO/BLOCKED,1.1.0, cinco productores o pruebas NOT_RUN corresponden al momento histórico de esa sección y no sustituyen este estado vigente. No se han reescrito Memory Bank ni fuentes empresariales.

## Historial del diseño y de los lotes (referencia temporal)

**Fecha:** 2026-11-01. **Rama:** `feature/telemetryEventCapture`. **Estado:** DRAFT / BLOCKED.
Referencias: [spec](./spec.md), [plan](./plan.md). IDs locales de Fase 2; no confundir con TASK-TEL de Fase 1.

Todas las tareas tienen estado inicial **TODO**: no se implementa ni se ejecuta ninguna en este hito documental. A01–05 son acciones para resolver gates; B–G permanecen no ejecutables hasta aprobar contrato, cobertura, ADR y alcance protegido. TODO no significa permiso ni gate superado. Los tests y evidencias son futuros, NOT_RUN. Cuando una fuente no existe, la tarea resuelve su disposición, nunca construye el dominio fuera de alcance.

Orden requerido: A → B (stub probado) → C (servicio probado) → D → E → F condicional → G. TASK-TEL-028 cierra pruebas C después de integrar adaptadores D; core/transport se prueban incrementalmente antes de instrumentar. No habilitar productores sin su unit suite previa; la prueba completa añade integración de los adaptadores. No crear nueva rama, dependencias, commit, push, PR ni merge. Archivos abreviados se resuelven dentro del componente declarado en plan; al cerrar gate debe fijarse su ruta exacta antes de editar.

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


## TASK-TEL-001 — Verificar aprobación de Fase 1

- **Grupo:** A. **Estado inicial:** TODO.
- **Objetivo:** verificar aprobación de fase 1 con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Obtener estado/revisor/alcance/hash; contrastar revisión aprobada y no confundir commit con aprobación. Aceptar sólo registro verificable que identifica ambas fuentes.
- **Requisitos EARS:** TEL-FR-002, TEL-FR-018 (Fase 2).
- **Dependencias:** lectura de contexto y evidencia de aprobación; B01 abierto; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** docs/telemetry/telemetry-plan.md y event-schemas.json (sólo lectura); expediente Fase 2; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** Revisión B01; fingerprints comparados (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Aprobación externa ausente; no ejecutar etapas posteriores.

## TASK-TEL-002 — Resolver perfil temporal y cobertura

- **Grupo:** A. **Estado inicial:** TODO.
- **Objetivo:** resolver perfil temporal y cobertura con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Registrar 20/10 s aprobados y resolver garantías STREAM frente al perfil temporal; enumerar fuentes de los 11 candidatos obligatorios. Obtener decisión escrita de perfil temporal y cobertura aplazada; no afirmar monitorización completa.
- **Requisitos EARS:** TEL-FR-011, TEL-FR-012, TEL-FR-018 (Fase 2).
- **Dependencias:** TASK-TEL-001; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** expediente Fase 2; contrato Fase 1 sólo mediante tarea separada autorizada; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** B02/B06; matriz de fuentes y métricas (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Reducir cobertura sin aprobación o alterar contrato unilateralmente.

## TASK-TEL-003 — Resolver contexto regional, identidad y transporte

- **Grupo:** A. **Estado inicial:** TODO.
- **Objetivo:** resolver contexto regional, identidad y transporte con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Conservar decisiones HMAC/clinica/null/20 eventos/10 s aprobadas; revisar con Tecnología y Claire gestión de claves, clasificación/destino/ámbito HMAC de generales, staging, configuración de fetch keepalive con Bearer y summary logs. Aceptar mecanismo seguro documentado y autorizaciones B03–B08; nunca clave en cliente ni endpoint público por inferencia.
- **Requisitos EARS:** TEL-FR-009, TEL-FR-014, TEL-FR-017, TEL-FR-026 (Fase 2).
- **Dependencias:** TASK-TEL-001; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** expediente Fase 2; auth/config/infra sólo lectura hasta autorización separada; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** Revisión de diseño y matriz 401/403/CORS/regiones (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Bloqueo real: esta tarea no autoriza construir endpoint de contexto ni cambiar auth.

## TASK-TEL-004 — Concretar validación derivada y distribución

- **Grupo:** A. **Estado inicial:** TODO.
- **Objetivo:** concretar validación derivada y distribución con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Revalidar rutas reales y servidor estático; especificar generación desde JSON y parity completa. Aceptar ruta servible y cobertura de vocabulario, sin segunda fuente manual ni dependencia no autorizada.
- **Requisitos EARS:** TEL-FR-002, TEL-FR-025, TEL-NFR-009 (Fase 2).
- **Dependencias:** TASK-TEL-001, TASK-TEL-002, TASK-TEL-003; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** expediente Fase 2; posibles artefactos derivados y shared service sólo futuros; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-N09 y prueba de alcance del servidor/import relativo (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Diseño incompleto de serving/validador.

## TASK-TEL-005 — Cerrar matriz de catálogo aprobado

- **Grupo:** A. **Estado inicial:** TODO.
- **Objetivo:** cerrar matriz de catálogo aprobado con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Sustituir inventario diagnóstico por matriz aprobada tras gates; mantener cada nombre/allowlist/trigger y productor, separar fuentes ausentes. Aceptar cero huecos no explicados y aprobación expresa de exclusiones.
- **Requisitos EARS:** TEL-FR-018, TEL-FR-019 (Fase 2).
- **Dependencias:** TASK-TEL-001, TASK-TEL-002, TASK-TEL-003, TASK-TEL-004; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** spec.md / plan.md / tasks.md de este expediente; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-I01 y T-CAT-001–039 (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** No crear payload/evento para cubrir fuente ausente.

## TASK-TEL-006 — Definir TelemetryEvent y wrapper/receipt

- **Grupo:** B. **Estado inicial:** TODO. **Estado actual:** implementado; pruebas de cierre en sección stub y revisión final.
- **Objetivo:** definir telemetryevent y wrapper/receipt con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Derivar modelos del contrato según ADR-005; validar tipos, required/nullable, extras y propiedades discriminadas. Aceptar lote cerrado atómico y recibo exacto recibido N.
- **Requisitos EARS:** TEL-FR-001, TEL-FR-002, TEL-FR-003 (Fase 2).
- **Dependencias:** TASK-TEL-005; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** backend/app/telemetry/schemas.py y __init__.py; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-B02/03; positivos/negativos por contrato (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Contrato público nuevo requiere autorización futura B08.

## TASK-TEL-007 — Montar router POST temporal

- **Grupo:** B. **Estado inicial:** TODO. **Estado actual:** implementado; pruebas de cierre en sección stub y revisión final.
- **Objetivo:** montar router post temporal con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Montar ruta fija aprobada con auth acordada, validación y receipt; no depender de ORM ni exportador. Aceptar 200/received con ninguna escritura.
- **Requisitos EARS:** TEL-FR-001, TEL-FR-003, TEL-FR-005 (Fase 2).
- **Dependencias:** TASK-TEL-006; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** backend/app/telemetry/router.py; backend/app/main.py; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-B01/03/05; inspección dependencias (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** No hacer pública ingestión; montaje autorizado.

## TASK-TEL-008 — Leer TELEMETRY_ENDPOINT en Settings

- **Grupo:** B. **Estado inicial:** TODO. **Estado actual:** implementado; pruebas de cierre en sección stub y revisión final.
- **Objetivo:** leer telemetry_endpoint en settings con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Implementar finalidad acordada ADR-006, validar valor/ausencia, separar referencia de ruta; no reenvío. Aceptar lectura real probada y sin configuración muerta.
- **Requisitos EARS:** TEL-FR-006 (Fase 2).
- **Dependencias:** TASK-TEL-005; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** backend/app/core/config.py; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-B06 (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Configuración protegida requiere autorización; no .env automático.

## TASK-TEL-009 — Aplicar resumen seguro y límite de body

- **Grupo:** B. **Estado inicial:** TODO. **Estado actual:** implementado; pruebas de cierre en sección stub y revisión final.
- **Objetivo:** aplicar resumen seguro y límite de body con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Imponer cuota real antes de parse, contar tipos válidos y evitar input/ctx en errores. Aceptar 413 seguro, 422 sin reflejo y logs sólo resumen aprobado.
- **Requisitos EARS:** TEL-FR-004, TEL-NFR-007, TEL-NFR-013 (Fase 2).
- **Dependencias:** TASK-TEL-007; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** backend/app/telemetry/router.py; middleware local sólo si acordado; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-B04; T-N07/13 chunked/UTF-8 (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Logger externo/retención B07; no cambiar errores globales.

## TASK-TEL-010 — Validar stub y OpenAPI antes de frontend

- **Grupo:** B. **Estado inicial:** TODO. **Estado actual:** implementado; pruebas de cierre en sección stub y revisión final.
- **Objetivo:** validar stub y openapi antes de frontend con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Ejecutar pytest/httpx aislado sin DB; validar lote válido/inválido, auth, payload size, recibo, logging, no escritura y OpenAPI nuevo con baseline restante. Aceptar todas las pruebas pertinentes PASS.
- **Requisitos EARS:** TEL-FR-001–006, TEL-NFR-007–009, TEL-NFR-013 (Fase 2).
- **Dependencias:** TASK-TEL-007, TASK-TEL-008, TASK-TEL-009; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** backend/tests/test_telemetry.py; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-B01–06 y T-N07–09/13 (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Bloquea frontend si test/gate falla.

## TASK-TEL-011 — Configurar URL pública del backoffice

- **Grupo:** C. **Estado inicial:** TODO.
- **Objetivo:** configurar url pública del backoffice con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Usar mecanismo runtime aprobado en ADR-001/006; validar URL y región antes de habilitar exportación. Aceptar dos URLs configurables sin cambiar productores y ausencia/invalidez -> cero red.
- **Requisitos EARS:** TEL-FR-013, TEL-NFR-005 (Fase 2).
- **Dependencias:** TASK-TEL-010; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** uis/backoffice/telemetry/config.mjs; README.md/es.md afectados; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-F07; T-N05 (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Serving/config protegida; no tocar Compose/.env por inferencia.

## TASK-TEL-012 — Construir envelope en track JavaScript

- **Grupo:** C. **Estado inicial:** TODO.
- **Objetivo:** construir envelope en track javascript con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Implementar captura síncrona con UUID/timestamp/contexto autorizado interno y retorno undefined; dependencias inyectables sin API de captura alternativa. Aceptar ocho campos y mismo timestamp al enviar.
- **Requisitos EARS:** TEL-FR-007, TEL-FR-009, TEL-FR-010 (Fase 2).
- **Dependencias:** TASK-TEL-011; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** uis/backoffice/telemetry/telemetry-service.mjs; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-F01/03/04; T-N01 (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** No JWT sub crudo ni HMAC de cliente.

## TASK-TEL-013 — Validar y copiar properties desde contrato

- **Grupo:** C. **Estado inicial:** TODO.
- **Objetivo:** validar y copiar properties desde contrato con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Comprobar catálogo/required/types/extras y valores no JSON antes de copia defensiva; rechazar evento íntegro sin throw/red. Aceptar parity del JSON y cero mutación posterior.
- **Requisitos EARS:** TEL-FR-025, TEL-FR-026, TEL-FR-027 (Fase 2).
- **Dependencias:** TASK-TEL-012, TASK-TEL-004; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** telemetry-service.mjs y outputs derivados en ubicación aprobada; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-F02/12/13, T-N09, T-P01 (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Allowlists por sí solas no detectan secretos en strings.

## TASK-TEL-014 — Implementar cola acotada en memoria

- **Grupo:** C. **Estado inicial:** TODO.
- **Objetivo:** implementar cola acotada en memoria con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Separar pending/inFlight, contar bytes UTF-8, rechazar evento nuevo al exceder cuotas aprobadas; no storage. Aceptar límites incluso durante retry y preservar inFlight.
- **Requisitos EARS:** TEL-FR-008, TEL-NFR-002 (Fase 2).
- **Dependencias:** TASK-TEL-013; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** uis/backoffice/telemetry/telemetry-service.mjs; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-F02; T-N02 (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Pérdida acotada exige perfil temporal aprobado.

## TASK-TEL-015 — Implementar extracción de lotes y exclusión

- **Grupo:** C. **Estado inicial:** TODO.
- **Objetivo:** implementar extracción de lotes y exclusión con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Extraer prefijo hasta 20 y límite bytes; serializar snapshot único; guardar capturas nuevas en pending. Aceptar 19/20/21 y máximo un transporte; no pérdida de nuevos.
- **Requisitos EARS:** TEL-FR-011, TEL-NFR-003, TEL-NFR-004 (Fase 2).
- **Dependencias:** TASK-TEL-014; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** telemetry-service.mjs; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-F05; T-N03/04 (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Duplicados por timers/hidden concurrentes.

## TASK-TEL-016 — Implementar deadline periódico no debounce

- **Grupo:** C. **Estado inicial:** TODO.
- **Objetivo:** implementar deadline periódico no debounce con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Primer pendiente fija deadline 10 s; track posteriores no reinician; marcar vencido durante vuelo/backoff y enviar al liberar. Aceptar 9999/10000 ms y captura continua.
- **Requisitos EARS:** TEL-FR-012 (Fase 2).
- **Dependencias:** TASK-TEL-015; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** telemetry-service.mjs; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-F06 y envío de remanente vencido (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Event loop suspendido impide garantía wall-clock.

## TASK-TEL-017 — Implementar transporte HTTP y validar ACK

- **Grupo:** C. **Estado inicial:** TODO.
- **Objetivo:** implementar transporte http y validar ack con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Enviar JSON con mecanismo auth aprobado, timeout y ACK received=N; gestionar excepciones internamente. Aceptar 200 correcto, ACK incorrecto/2xx alternativo/red fallida conforme a política.
- **Requisitos EARS:** TEL-FR-003, TEL-FR-013, TEL-NFR-006 (Fase 2).
- **Dependencias:** TASK-TEL-016; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** uis/backoffice/telemetry/transport.mjs; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-F07/09; T-N06/08 (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** No interpretar HTTP válido como persistencia durable.

## TASK-TEL-018 — Implementar tres reintentos adicionales

- **Grupo:** C. **Estado inicial:** TODO.
- **Objetivo:** implementar tres reintentos adicionales con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Clasificar errores según política aprobada; primer intento más retries 1/2/4 s; Retry-After según límite; conservar bytes/IDs. Aceptar máximo cuatro intentos y uno en vuelo.
- **Requisitos EARS:** TEL-FR-015 (Fase 2).
- **Dependencias:** TASK-TEL-017; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** transport.mjs y telemetry-service.mjs; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-F09; temporizadores y estados HTTP (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Timeout puede duplicar recepción; no exactly-once.

## TASK-TEL-019 — Implementar descarte terminal aislado

- **Grupo:** C. **Estado inicial:** TODO.
- **Objetivo:** implementar descarte terminal aislado con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Tras error permanente o cuarto fallo liberar sólo inFlight y procesar pending; contador diagnóstico local sin track recursivo. Aceptar nuevos eventos conservados y sin rejected Promise.
- **Requisitos EARS:** TEL-FR-016, TEL-NFR-006 (Fase 2).
- **Dependencias:** TASK-TEL-018; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** telemetry-service.mjs; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-F10, T-N06 (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** No eliminar cola nueva junto al lote fallido.

## TASK-TEL-020 — Implementar lifecycle hidden y cleanup

- **Grupo:** C. **Estado inicial:** TODO.
- **Objetivo:** implementar lifecycle hidden y cleanup con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Instalar visibilitychange/cleanup una vez; BFCache/pagehide sólo perfil aprobado; no reenvío de inFlight. Aceptar hidden produce un intento y cambios de instalación no duplican listeners.
- **Requisitos EARS:** TEL-FR-014, TEL-NFR-012 (Fase 2).
- **Dependencias:** TASK-TEL-019; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** adaptador lifecycle en uis/backoffice/telemetry/; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-F08; browser lifecycle manual (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Hidden no prueba logout ni entrega.

## TASK-TEL-021 — Implementar fetch keepalive autorizado

- **Grupo:** C. **Estado inicial:** TODO.
- **Objetivo:** implementar beacon/fallback autorizado con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Sólo tras B05 resuelto: verificar Bearer/CORS/content-type/bytes y gestionar ACK/fallo/abort sin duplicar inFlight. Aceptar ausencia de tokens URL/body y sin promesa de entrega al destruir página.
- **Requisitos EARS:** TEL-FR-014, TEL-NFR-008, TEL-NFR-012 (Fase 2).
- **Dependencias:** TASK-TEL-020, TASK-TEL-003; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** transport.mjs; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-F08 y T-N08/12 (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Beacon sustituido expresamente por decisión aprobada; límites/configuración requieren revisión.

## TASK-TEL-022 — Propagar correlación interna por operación

- **Grupo:** C. **Estado inicial:** TODO.
- **Objetivo:** propagar correlación interna por operación con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Usar contexto requestId auténtico de operación, null sin request; aislar dos operaciones concurrentes sin extra properties ni cambio track. Aceptar IDs distintos por evento y correlación exacta.
- **Requisitos EARS:** TEL-FR-017 (Fase 2).
- **Dependencias:** TASK-TEL-019, TASK-TEL-003; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** adaptadores HTTP aprobados; core context; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-F11 con promesas concurrentes (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Header/middleware/context API requieren autorización B08.

## TASK-TEL-023 — Integrar lifecycle de sesión sin almacenamiento

- **Grupo:** C. **Estado inicial:** TODO.
- **Objetivo:** integrar lifecycle de sesión sin almacenamiento con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Reusar conexión válida/descarga de contexto aprobado, session UUID por conexión; purge al disconnect/cambio actor/región e invalidar callbacks tardíos. Aceptar token en memoria y ningún evento anterior con credenciales nuevas.
- **Requisitos EARS:** TEL-FR-009, TEL-FR-017, TEL-FR-023 (Fase 2).
- **Dependencias:** TASK-TEL-021, TASK-TEL-022; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** incidencias app.js; Management index.html; contexto interno aprobado; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-F03/11; T-N14; lifecycle sintético (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Toca puntos auth protegidos: aprobación expresa primero.

## TASK-TEL-024 — Capturar errores globales permitidos

- **Grupo:** D. **Estado inicial:** TODO.
- **Objetivo:** capturar errores globales permitidos con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Instalar window.error una vez, clasificar sólo código/component permitidos; no messages/stacks/URLs/input; ignorar fallos del canal. Aceptar evento válido o rechazo seguro sin recursión.
- **Requisitos EARS:** TEL-FR-020, TEL-FR-026 (Fase 2).
- **Dependencias:** TASK-TEL-023; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** adaptador errores del frontend existente; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-I03, T-P01 (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Datos sensibles embebidos en error.

## TASK-TEL-025 — Capturar unhandledrejection sin contenido

- **Grupo:** D. **Estado inicial:** TODO.
- **Objetivo:** capturar unhandledrejection sin contenido con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Escuchar unhandledrejection con guard; no convertir reason arbitrario en properties. Aceptar payload cerrado y Promise interna siempre gestionada.
- **Requisitos EARS:** TEL-FR-020, TEL-NFR-006 (Fase 2).
- **Dependencias:** TASK-TEL-024; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** mismo adaptador errores; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-I03 con Error/string/objeto sintético (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** La instrumentación no oculta ni sustituye manejo de negocio.

## TASK-TEL-026 — Capturar navegación normalizada

- **Grupo:** D. **Estado inicial:** TODO.
- **Objetivo:** capturar navegación normalizada con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Mapear vista a enum exacto de schema; capturar acceso una vez con política aprobada, sin query/UUID/hash completo. Aceptar ruta permitida y dedup acordado sin fusionar mutaciones.
- **Requisitos EARS:** TEL-FR-022 (Fase 2).
- **Dependencias:** TASK-TEL-023; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** incidencias app.js renderRoute; Management sección autorizada; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-I05, T-CAT-018 (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Landing anónima sin jurisdicción no exporta.

## TASK-TEL-027 — Capturar duración frontend

- **Grupo:** D. **Estado inicial:** TODO.
- **Objetivo:** capturar duración frontend con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Medir operación relevante aprobada con performance.now y metric/unit permitidos; emitir al terminal. Aceptar duración >=0 y sin duplicado de api_request_completed.
- **Requisitos EARS:** TEL-FR-021 (Fase 2).
- **Dependencias:** TASK-TEL-023; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** adaptador performance del frontend real; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-I04, T-CAT-019 (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** No fabricar métricas ni añadir librería.

## TASK-TEL-028 — Validar servicio completo aislado

- **Grupo:** C. **Estado inicial:** TODO.
- **Objetivo:** validar servicio completo aislado con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Ejecutar node:test candidato con timer/UUID/context/fetch/keepalive controlados y sin red/DB; covering race, cuota, retry, sesión y fallos. Aceptar suite PASS y budget track medido por separado.
- **Requisitos EARS:** TEL-FR-007–017, TEL-FR-025–027, TEL-NFR-001–014 (Fase 2).
- **Dependencias:** TASK-TEL-024, TASK-TEL-025, TASK-TEL-026, TASK-TEL-027; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** uis/backoffice/telemetry/tests/*.test.mjs; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-F01–13, T-N01–14 y T-P01 (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Runner de DOM no existente; dependencias requieren aprobación.

## TASK-TEL-029 — Confirmar obligaciones por productor

- **Grupo:** E. **Estado inicial:** TODO.
- **Objetivo:** confirmar obligaciones por productor con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Reconciliar 5 ejercicio+6 briefing con alcance aprobado y estado real; adjuntar owner de cada hecho. Aceptar ninguna obligación atribuida falsamente al navegador y disposición aprobada de fuentes ausentes.
- **Requisitos EARS:** TEL-FR-018 (Fase 2).
- **Dependencias:** TASK-TEL-028, TASK-TEL-005; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** matriz aprobada de expediente Fase 2; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-I01 (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Sin B06 resuelto no hay cobertura completa.

## TASK-TEL-030 — Resolver instrumentación de inventario pendiente

- **Grupo:** E. **Estado inicial:** TODO.
- **Objetivo:** resolver instrumentación de inventario pendiente con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Para los 12 candidatos inventory/data reconciliation, registrar dependencia de módulo futuro y propietario; no crear fuente falsa ni payload distinto. Aceptar aplazamiento aprobado o tarea separada explícita tras existir fuente.
- **Requisitos EARS:** TEL-FR-018, TEL-FR-019 (Fase 2).
- **Dependencias:** TASK-TEL-029; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** sólo expediente y spec inventario en lectura; ningún módulo nuevo dentro de esta fase; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-CAT-001–012 cuando haya implementación autorizada (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Inventario inexistente: tarea de disposición, no implementación de dominio.

## TASK-TEL-031 — Instrumentar hechos de incidencias aprobados

- **Grupo:** E. **Estado inicial:** TODO.
- **Objetivo:** instrumentar hechos de incidencias aprobados con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Emitir incident_created/transitioned/assigned en productor post-commit aprobado, sin sustituir auditoría; si scope UI exclusivo, aplazar con aprobación en vez de emitir clic. Aceptar rollback sin evento y hecho único por commit.
- **Requisitos EARS:** TEL-FR-019 (Fase 2).
- **Dependencias:** TASK-TEL-029, TASK-TEL-003; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** backend/app/incidents/router.py y tests correspondientes sólo con autorización; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-I02, T-CAT-028–030 (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Post-commit real/seudónimos/auth/auditoría fuera del scope documental.

## TASK-TEL-032 — Resolver restantes eventos por fuente aprobada

- **Grupo:** E. **Estado inicial:** TODO.
- **Objetivo:** resolver restantes eventos por fuente aprobada con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Para cache/sondas/alertas/jobs/calidad/Management/audit/KPI/diagnóstico, documentar productor y dependencia; instrumentar sólo fuente existente aprobada y no diagnósticos por canal recursivo. Aceptar disposición por cada fila T-CAT restante sin eventos inventados.
- **Requisitos EARS:** TEL-FR-018, TEL-FR-019, TEL-FR-027 (Fase 2).
- **Dependencias:** TASK-TEL-029; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** expediente; módulos backend presentes sólo si autorizados; fuentes futuras no se crean aquí; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-CAT-017,020,022–027,031–039 y T-I01 (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** No construir scheduler/EHR/agregadores ni cambiar auditoría por inferencia.

## TASK-TEL-033 — Capturar Web Vitals condicionales

- **Grupo:** F. **Estado inicial:** TODO.
- **Objetivo:** capturar web vitals condicionales con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Activar sólo si perfil/evento aprobado y APIs compatibles; metric/unit/view exactos, sin librería nueva. Aceptar medición sintética permitida o exclusión expresa cuando API ausente.
- **Requisitos EARS:** TEL-FR-024 (Fase 2).
- **Dependencias:** TASK-TEL-027, TASK-TEL-028; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** adaptador frontend_timing_measured del frontend autorizado; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-I07, T-CAT-019 (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** No convertir auditoría Lighthouse en RUM emitido.

## TASK-TEL-034 — Capturar autenticación en frontera autorizada

- **Grupo:** F. **Estado inicial:** TODO.
- **Objetivo:** capturar autenticación en frontera autorizada con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Distinguir validación JWT de conexión y session events; instrumentar authentication_failed/succeeded sólo en frontera aprobada sin cambiar permisos ni repetición por página. Aceptar 401/éxito real, sin secretos.
- **Requisitos EARS:** TEL-FR-023 (Fase 2).
- **Dependencias:** TASK-TEL-023, TASK-TEL-028, TASK-TEL-003; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** backend/app/auth/dependencies.py sólo con autorización y revisión; session adapter existente; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-I06, T-CAT-013–016 (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Cambio de auth protegido; no presentarlo como permiso implícito.

## TASK-TEL-035 — Validar integración, privacidad y DevTools

- **Grupo:** G. **Estado inicial:** TODO.
- **Objetivo:** validar integración, privacidad y devtools con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Ejecutar estrategia plan en entorno aislado; test backend/frontend y catálogo; revisar OpenAPI/no escrituras/PII/región; observar batches 20/10 s/hidden. Aceptar cada FUT con resultado y evidencia real, sin HAR con Authorization.
- **Requisitos EARS:** TEL-FR-001–027, TEL-NFR-001–014 (Fase 2).
- **Dependencias:** TASK-TEL-030, TASK-TEL-031, TASK-TEL-032, TASK-TEL-033, TASK-TEL-034; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** tests/evidencias sintéticas redactadas en ubicación autorizada; README bilingües afectados; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** T-B/F/I/N/P/CAT; DevTools manual (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** Datos reales/DB compartida no autorizados; no declarar NOT_RUN como PASS.

## TASK-TEL-036 — Revisión de entrega y preparar texto de PR

- **Grupo:** G. **Estado inicial:** TODO.
- **Objetivo:** revisión de entrega y preparar texto de pr con aceptación verificable antes de habilitar dependientes.
- **Descripción y pasos:** Revisar diff completo/estado y ejecutar validate-delivery read-only; preparar título feat: telemetry event capture y descripción con matriz/pruebas/evidencias. Aceptar PASS real sin bloqueos y autorización aparte para commit/push/PR.
- **Requisitos EARS:** TEL-NFR-010 (Fase 2).
- **Dependencias:** TASK-TEL-035; B01–B08 y autorización de archivos protegidos cuando corresponda.
- **Archivos previstos:** expediente y borrador local de PR en ubicación autorizada; sin crear PR; nada modificado ahora.
- **Criterios de aceptación:** condiciones “Aceptar” de los pasos verificadas con los tests/revisión indicados; sin cambios fuera del alcance expresamente autorizado. Ningún campo/contrato inventado ni gate abierto ocultado.
- **Pruebas necesarias:** DOC/FUT y AC-01–10; git diff --check (futuras, NOT_RUN).
- **Evidencia esperada:** diff limitado, resultado de pruebas/revisión con fecha y versión, y aprobación correspondiente a esta tarea. No marcar DONE sin artefacto verificable.
- **Riesgos:** BLOCKED no es listo; no commit/push/PR/merge automático.

## TASK-TEL-037 — Revisar contexto y gestión de claves concretos

- **Grupo:** A. **Estado inicial:** TODO; precede implementación de grupos B/C.
- **Objetivo:** obtener revisión verificable del contrato contexto/header, bindings, permisos/región y gestión de claves antes de editar archivos protegidos.
- **Descripción y pasos:** revisar la sección de diseño concreto en plan con Tecnología y Claire; fijar TTL/rotación/secret injection, alcance de clínicas y revalidación; aprobar archivos/endpoint/header CORS. Registrar decisiones, sin cambiar auth/config ni crear claves ahora.
- **Requisitos EARS:** TEL-FR-028, TEL-FR-029, TEL-NFR-015.
- **Dependencias:** TASK-TEL-003 y TASK-TEL-005; B03/B04/B08; revisión externa evidenciada, no supuesta.
- **Archivos previstos:** tres SDD actuales; futuros context.py/identity.py/schemas.py/router.py/config.py/main.py/context.mjs/tests enumerados en plan, sólo tras autorización.
- **Criterios de aceptación:** contrato request/response/claims mínimo, permisos vigentes y destino regional definidos; gestión de claves y autorización concreta registradas; fuentes clínicas pendientes no presentadas como implementadas.
- **Pruebas necesarias:** T-CTX-001–010 como escenarios de revisión, NOT_RUN hasta implementación; comprobar no UUID/secretos en claims y no dependencia nueva.
- **Evidencia esperada:** revisión de sección y versión aprobada por responsables, alcance de archivos; resultados reales posteriores de pruebas.
- **Riesgos:** aprobación ausente, header requiere CORS protegido, token firmado no cifrado, falta de permiso clínico o rotación incompatible con cola; no convertir TODO en DONE por documentación.

## Cierre de tareas

Preparación del PR significa texto local revisable; creación remota, commit, push y merge a main requieren autorización expresa adicional y aprobaciones del repositorio. Si cambia contrato, productor o alcance, actualizar los tres documentos tras aprobación antes de ejecutar; no modificar Fase 1, Memory Bank o Rules unilateralmente. Exclusiones condicionales necesitan disposición aprobada, no DONE por falta de fuente. El estado final de implementación sólo puede cerrarse con evidencias y validate-delivery PASS.

## Evidencia de tareas B del stub

TASK-TEL-006–010 tienen implementación y pruebas de cierre referenciadas en plan: 103 pruebas de stub/contexto/identity/status/auth pasadas en entorno aislado. Los modelos de negocio del catálogo son validables pero su productor browser no está habilitado. Contexto/key rotation con gracia, frontend y todas las tareas C–G siguen pendientes según alcance; no marcar la captura completa terminada. Aprobación Tecnología de archivos y Cumplimiento del uso HMAC registrada en conversación, sin atribuir autorización de producción.


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

### Evidencia del reajuste compartido

133 pruebas backend PASS y dos pruebas PostgreSQL omitidas en ejecución sin DB, como corresponde a su guard de aislamiento. Integración/regresiones contra PostgreSQL16 temporal en tmpfs con seeds sintéticos:36 PASS, incluidas las dos pruebas DB. El mismo proceso API emite/revalida contextos US y UK y prepara eventos de servidor con claves diferentes; contexto cruzado/selector manipulado rechazados. Suite frontend:67 PASS sin modificar código UI. Plantilla:36 variables, cobertura de Settings/Compose y secretos vacíos; git diff --check PASS. Durante desarrollo se corrigieron validación de null interno en JWT, filtro de filas regionales y UUID UK de la prueba sintética. Ningún fallo pendiente en las comprobaciones enumeradas.

Comandos: podman compose --profile test run --no-deps --build --rm -e DATABASE_URL=postgresql+asyncpg://synthetic:synthetic@127.0.0.1:1/isolated test uv run --no-sync pytest tests/test_telemetry_shared.py tests/test_telemetry_server.py tests/test_telemetry_incident_producer.py tests/test_telemetry.py tests/test_telemetry_context.py tests/test_telemetry_identity.py tests/test_status.py tests/test_auth.py -q; node --test uis/backoffice/operational-incidents/telemetry/tests/*.test.mjs; podman compose -f /private/tmp/telemetry-business-compose.yaml up --abort-on-container-exit --exit-code-from test (arnés temporal con pytest -p telemetry_validation_plugin, NullPool sólo en pruebas aisladas). Recuentos se solapan, no se suman como tests únicos. El entorno temporal quedó detenido.

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
