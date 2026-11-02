# Lote final propuesto — auditoría de inventario y cierre técnico acotado

## Aprobación y cierre del alcance — 2026-11-03

**Estado del alcance sintético entregado: PASS / cerrado.** El desarrollador autorizó posteriormente los commits con «haz los commits»: el cierre queda versionado por responsabilidades (almacenamiento, backend/contrato, interfaz y documentación). No push ni despliegue. Las notas anteriores de «sin commits» describen el estado previo a esta autorización. El desarrollador comunica en esta conversación: «autorizado por Claire el 3 de noviembre 2026». Se registra como aprobación de Claire Whitfield, Cumplimiento y Gobierno del Dato, comunicada por el desarrollador para el incremento de telemetría y su cierre acotado. Fuente: mensaje del desarrollador; no se ha consultado un acta o sistema externo ni se atribuye aprobación de datos reales, piloto, producción, nuevas fuentes o despliegue.

Esta evidencia resuelve el bloqueo de Cumplimiento del cierre acotado indicado anteriormente. Se conservan los resultados de pruebas ya ejecutadas; esta actualización sólo modifica documentación. Los ocho tipos sin productor, la cobertura integral TEL-FR-018 y las mejoras de durabilidad/retención/rotación/correlación permanecen como backlog fuera del alcance cerrado. No se han creado commits ni desplegado servicios. Las menciones posteriores a Cumplimiento pendiente/BLOCKED son históricas y quedan sustituidas únicamente para este incremento.

2026-11-03. DESIGN_READY. Implementación/pruebas NOT_RUN.

## Alcance de cierre
El usuario pide «continua, a ver si terminamos». Proponer un último incremento de captura con fuente existente y después revisión consolidada de entrega, sin encadenar ampliaciones indefinidas.31 tipos con alguna instrumentación y8 sin productor permanecen; no afirmar cobertura universal. Los8 tipos sin fuente y brechas restantes se conservan explícitamente como backlog. Cumplimiento real sigue pendiente; no aprobar producción por terminar código/pruebas.

## Auditoría y contrato
Actual audit_accessed sólo admite surface incident/management y US/UK. No existe surface inventory ni resolución compatible con roles inventory; no etiquetar inventario como management. Añadir surface=inventory en tres copias del contrato y schemaVersion1.3.0 para transición explícita, conservando39 tipos/14nullable/25clínicos, propiedades y política browser. No aceptar/normalizar silenciosamente1.2.0 en backend/frontend nuevos; actualizar fixtures positivas, conservar tests de versión antigua, sincronizar consumidores/modelos/OpenAPI y activos de telemetría. Sólo entorno aislado de validación; no despliegue compartido.

## Consultas cubiertas
- GET /inventory/items/{item_id}/audit: clínica obligatoria, actor inventoryAuditor autorizado; marcar después de consulta y construcción redacted existentes.
- GET /inventory/access-denials: sólo cuando clinic_id explícito; query/resultados/permisos existentes intactos. Sin clínica, no capturar ni inventar región de actor/primer scope.
- Captura después de último body2xx enviado correctamente, incluidos resultados vacíos con contexto válido.
- Descriptor interno conserva actor/clínica y conjunto acotado de países históricos de las filas clínicas devueltas (paginación≤100). Filas globales de catálogo sin clínica no se reinterpretan como clínicas. No contenidos/snapshots/reasons/tokens/UUIDs de filas en evento.
- Productor revalida audit:read, clínica activa, scope y país US/UK activo en sesión independiente; cada país histórico de fila clínica debe ser conocido y coincidir con la clínica. Filas legadas/desconocidas/mixtas o actor que sólo tenga país antiguo ->descarte, nunca fallback null. Resultados/semántica histórica existentes no cambian por descarte de telemetría.

## Archivos y cambios autorizados e implementados
1. Nuevos telemetry/inventory_audit_producer.py y tests/test_telemetry_inventory_audit.py; marcador con statekey distinto al auditor anterior. HMAC regionaluserId, sessionId/requestId null, properties jurisdiction/environment/surface=inventory. Reutilizar cola/cuota16/100ms/closed/disabled y admitir tipo por sink existente; browser continúa rechazándolo.
2. inventory/router.py añade Request/marcas en ambas lecturas; ninguna mutación o política nueva. audit_completion.py atiende nueva marca con precedencia definida para no duplicar tipo y limpieza en finally; marca incident/management previa conserva comportamiento.
3. docs/telemetry/event-schemas.json y copias backend/telemetry y backoffice/telemetry: surface inventory +VERSION1.3.0; fixtures runtime/test positivas y OpenAPI/tipos del backoffice sincronizados, activos mediante script existente. No nuevas dependencias ni claves. No modificar contratos de negocio, auth/capabilities, auditoría durable, stock o migraciones.
4. README bilingües backend/inventory/backoffice/telemetry y expediente. Consolidar estado actual en docs/specs/telemetry-event-capture/delivery-status.md, tasks.md y remaining-producers.md, preservando historia y declarando pendientes. No Memory Bank/Rules ni CONTEXT.
5. Revisión validate-delivery de este alcance final y resumen de límites/fuentes pendientes. Informe fuera del repositorio. Sin commits/push/PR/despliegue: requieren aprobación independiente y cumplimiento de sus gates.

## Criterios de aceptación y validación final
- US/UK positivas audit/denials con clínica explícita, resultados vacíos, payload mínimo surfaceinventory/HMAC; sin contenido/identificadores originales.
- Read/redaction/status/permisos intactos; 401/403/404/422, scope ajeno/inactiva/país inválido, filas legadas/mixtas y denials sinclinic ->cero eventos nuevos. Permisos/denegaciones durables originales conservados.
- ASGI finalsend/streaming/incompleto/cancelación/fallo/capturefault y limpieza/precedencia; cuota/lookup/timeout/closed/disabled sin cambiar respuesta.
- Contratos1.3.0 byteidénticos,39tipos/14nullable, inventory válido sólo audit_accessed; browser no afirma auditoría,1.2.0 rechazado sin normalización. Incidencias/Management existentes siguen válidos con nuevo envelope.
- PostgreSQL sintético aislado: integración real de auditoría histórica y regresión inventario/telemetría; suite general y checks existentes de contrato. Node telemetry tests/Vitest/typecheck/build y smoke E2E pertinente contra servicios temporales1.3.0. Ninguna prueba sobre servicio compartido.
- Diff sólo dentro del lote/aprobaciones anteriores, sin secretos/PHI; documentación consolidada coherente con código/evidencia. Expresar pass técnico acotado separado del gate global de Cumplimiento pendiente.

## Pendientes tras este cierre acotado
8 tipos sin productores (alert/job/notification y5agregados); cobertura universal de rutas API/mutaciones/autorización contextual; audit global/legado mixto; entrega durable/retención/rotación/correlación de señales tardías. No desaparecen por revisar el último lote ni se presentan como implementados. Decisión de continuar esos proyectos requiere alcance nuevo.


## Resultado técnico verificado — 2026-11-03

Autorización expresa: «Sí, autorizo este lote y el cierre técnico acotado». Implementado el productor, las dos marcas, observación ASGI y contrato/consumidores 1.3.0. Se conservan redacción, consultas y permisos; las pruebas históricas existentes de inventario también pasan. Se corrigió el fixture Node de `crypto` mediante descriptor restaurable para compatibilidad con Node24, sin cambiar el runtime.

Validaciones finales: 372 enfocadas /1 skip (otra DB dedicada), 700 generales /38 integración excluidas; 38 específicas de auditoría (solapadas con las anteriores salvo el caso final de límites/precedencia). Node75/75; Vitest67/67; tsc/build aprobados; Chrome1/1 flujo real de selección/inicio/confirmación. PostgreSQL aislado fresco 0001–0013. Contratos byteidénticos; SHA256 7065d4703487f7478ffbc144421c728dcd883a8c9608339854cc4271f0aa248e. `git diff --check` aprobado. No pruebas en la base compartida.

La revisión técnica queda acotada a lo autorizado. La revisión global de entrega conserva BLOCKED por Cumplimiento/Gobierno del Dato pendientes, según AGENTS.md y validate-delivery; no hay un fallo técnico conocido en las comprobaciones ejecutadas. La captura y cola siguen best effort; `accepted` no acredita entrega durable. No se inicia un nuevo lote. Informe final externo al repositorio: `/private/tmp/healthcore-telemetry-final-review.md`.
