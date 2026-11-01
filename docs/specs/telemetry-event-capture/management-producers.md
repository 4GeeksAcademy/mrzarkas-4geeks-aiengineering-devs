# Lote 3 revisable: mutaciones de clínicas en Management

Rama feature/telemetryEventCapture. management_mutation_completed aprobado e implementado para clínicas; no amplía contrato1.1.0, permisos, dominios ni aprobación de producción.

## Regla definitiva aprobada de jurisdicción del hecho

La fuente es ManagementAuditEvent persistido por la mutación, no un valor de región enviado por el frontend ni la clínica actual después de cambios posteriores.

| Acción | Fuente autoritativa | Resultado |
| --- | --- | --- |
| created | after_data.jurisdiction_id | Región de la clínica creada. |
| updated | before_data.jurisdiction_id | Región de la clínica antes de la mutación. |
| activated/deactivated | before_data.jurisdiction_id | Región previa, incluso si la clínica queda inactiva. |

Si una clínica pasa US→UK, la mutación queda en US y las siguientes operaciones de negocio pasan a UK. No emitir una copia UK del mismo cambio ni exportar pares origen/destino ni IDs originales para cruzar ambos ámbitos. Esta atribución analítica no autoriza transferencias de datos ni determina la ubicación física del backend.

Se obtiene la clave US/UK de Jurisdiction en una sesión independiente de sólo lectura, a partir del UUID de la referencia en el snapshot persistido. Jurisdicción desconocida/ausente o snapshot incompleto se descarta, sin fallback a región actual/null. Una jurisdicción histórica puede estar inactiva: se usa su clave US/UK como clasificación histórica, sin habilitar operaciones de negocio sobre referencias inactivas. No modificar resolve_clinic ni reglas del receptor/browser/lecturas de incidentes.

## Captura implementada

- Sólo create_reference_value, update_reference_value y set_reference_value_activation cuando resource=clinics. Catálogos, áreas, jurisdicciones, sistemas, coverage y compliance_review quedan sin productor hasta resolver sus ámbitos.
- add_audit_event devuelve el objeto ManagementAuditEvent generado, con UUID explícito usando el mismo uuid4 que su default. Campos/datos/correlation_id y persistencia transaccional se conservan; los callers existentes pueden ignorar el retorno. No migración ni cambio de respuesta HTTP.
- La ruta conserva audit.id antes del commit y programa captura inmediatamente después de commit satisfactorio, antes de refresh. No emitir en rollback, denegación, conflicto o fallo de commit; un refresh fallido no elimina el hecho confirmado.
- PATCH vacío, que actualmente no audita ni hace commit, no emite. Una petición de activación con el mismo estado sigue el comportamiento actual: si se audita y confirma, genera un evento; no cambiar negocio para deduplicar.
- Preparación asíncrona comparte máximo16 tareas, timeout100ms y cola20/10 de proceso existente. Lee la fila de auditoría por audit_id y actor autenticado, comprueba resource_type=clinics y acción permitida, y resuelve sólo la referencia jurisdiccional del snapshot.
- Selección HMAC regional en servidor: userId con clave de usuario; auditId con clave de recursos/propósito audit. La partición de cola usa región y binding clínico opaco derivado de resource_id. Nunca snapshots, títulos, motivos, labels ni UUID operativos en evento/log.
- Envelope confirmado: eventId UUID independiente, timestamp de captura post-commit, sessionId/requestId null. Properties cerradas: jurisdiction, environment, auditId, resource=reference, action=created/updated/activated/deactivated.
- El sink servidor admite este tipo; POST /telemetry/events browser sigue rechazando hechos de negocio. Sin transporte externo, almacenamiento adicional, claves nuevas ni datos reales.

## Archivos concretos

Archivos protegidos expresamente aprobados para esta mutación:
- backend/app/management/router.py: tres hooks post-commit sólo para clínicas; sin tocar descriptor audit_accessed del lote2 ni permisos.
- backend/app/management/service.py: retorno e ID explícito del AuditEvent generado, preservando auditoría existente.

Resto del alcance implementado:
- Nuevo backend/app/telemetry/management_producer.py, con resolución histórica separada.
- backend/app/telemetry/server.py: permitir management_mutation_completed sólo en sink interno.
- Nuevo backend/tests/test_telemetry_management.py y regresiones existentes de Management/auditoría/autorización.
- README backend bilingües y SDD.

Sin cambios de auth policies, modelos/migraciones, contrato JSON/API publicado, main/lifecycle (se reutiliza productor existente), .env/secretos, Compose/CI/despliegue, Memory Bank/Rules, commits/push/PR.

## Criterios de aceptación

1. Creación, actualización, activación y desactivación US/UK emiten una vez por commit confirmado con AuditEvent real correspondiente.
2. Cambio US→UK atribuido a US desde snapshot previo; operación posterior atribuida a UK. No dobles eventos ni referencias cruzadas exportadas.
3. Desactivación válida captura su hecho histórico; resolve_clinic/ingreso browser siguen rechazando clínica inactiva.
4. SQL/commit fallido, conflicto, denegación, PATCH vacío, recurso global y snapshot inválido no emiten. Error de preparación/sink mantiene respuesta y auditoría de negocio.
5. UUID/PHI/texto/secretos no se exportan; auditId HMAC enlazable bajo clave/propósito autorizados, payload cerrado.
6. Otros callers de add_audit_event, permisos, contratos/redacción persistente y conservación del historial permanecen correctos.
7. Cuota compartida, timeout y cierre sin tareas huérfanas; pruebas unitarias y PostgreSQL sólo aislado/sintético, seguidas de validate-delivery.

## Estado y autorización

El desarrollador respondió «continua» a la solicitud concreta de aprobación de la regla histórica y de backend/app/management/router.py y backend/app/management/service.py. La aprobación previa de HMAC por Cumplimiento conserva su alcance: claves exclusivamente servidor. No se declara autorización para datos reales, retención, exportación o producción.

## Evidencia de validación

- Suite backend sin DB: 174 PASS, cuatro integraciones omitidas por aislamiento.
- PostgreSQL16 temporal en tmpfs, base telemetry_validation sintética: 79 PASS (mutaciones reales, autorización, incidencias, auditoría, selección regional).
- PostgreSQL aislado nuevo: 113 PASS (contratos de respuesta, serialización de auditoría, OpenAPI Management, política de entrada, fixtures Compliance y catálogos).
- git diff --check PASS. Las ejecuciones se solapan y no se suman como pruebas únicas. Arnés temporal /private/tmp/telemetry-business-compose.yaml con pytest -p telemetry_validation_plugin; NullPool sólo en pruebas para evitar conexiones entre event loops.
- Integración demuestra cuatro auditorías persistidas y cuatro eventos correspondientes, cambio US→UK atribuido a US, activación/desactivación posteriores UK, clínica inactiva rechazada por resolve_clinic, rollback/conflicto/denegación/PATCH vacío sin evento y fallo del sink sin fallo de negocio.

Diez tipos tienen productor al menos parcial y29 no tienen productor. Auditoría global y recursos Management distintos de clínicas siguen abiertos. Contrato1.1.0 sin cambios; no cierre global ni exclusiones nuevas. Este lote no reconstruye el backend local ni modifica su base.
