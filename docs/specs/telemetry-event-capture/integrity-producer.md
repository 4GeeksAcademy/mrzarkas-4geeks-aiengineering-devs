# Lote9 revisable — integridad del contrato de eventos

Estado: aprobado expresamente («apruebo») e implementado; validación sintética completada. Rama feature/telemetryEventCapture. Contrato1.2.0 conservado.

## Evidencia y alcance

backend/app/reference_data/validation.py valida referencias de operaciones individuales. No existe un chequeo agregado ni una tarea de integridad; no presentar esas validaciones como integridad global. El catálogo permite check=references/historical_coverage/event_contract y outcome=ok/failed. Este lote cubre exclusivamente event_contract, no referencias históricas ni integridad de datos sanitarios.

## Comprobación implementada

Una ejecución por arranque del productor opcional de telemetría, después de crearlo con configuración válida. Sin cron, endpoint nuevo ni sondeo de base de datos. Leer exclusivamente backend/app/telemetry/event-contract.json con límite128KiB (actual85161 bytes); JSON duplicado o estructura inválida se considera fallo. Comparar el documento semánticamente con el contrato cargado por schemas.py; comprobar versión y conjunto de tipos, correspondencia de discriminator/event_type con cada modelo, campos requeridos y propiedades cerradas con las definiciones. Comparar estructuras, no depender del orden/formato del archivo ni añadir otra copia del catálogo.

Resultado ok sólo si todas esas comprobaciones terminan correctamente. Archivo ausente, excesivo, JSON inválido o discrepancia devuelve failed. No reportar causas, rutas, versiones libres, contenido, excepciones, hash o nombres de eventos defectuosos. La comparación verifica coherencia interna del paquete cargado, no firma del artefacto ni equivalencia con un frontend remoto. Una corrupción que impide importar schemas.py puede impedir arrancar FastAPI antes del chequeo: no prometer que emitirá diagnóstico en ese caso.

## Evento y entrega

Tras resultado completo, intentar exactamente una captura data_integrity_checked: properties={jurisdiction:null,environment:<entorno>,check:event_contract,outcome:ok|failed}; userId/sessionId/requestId=null; envelope normal UUID/timestamp/schemaVersion. No identidad ni HMAC de actor, acceso DB, PHI, clínica, referencias operativas o tokens.

Admitir el tipo sólo en ServerQueue interna y sink de negocio, manteniendo browser5 y canal diagnóstico2 separados. Usar cola20/10 existente y cuotas200/256KiB/2KiB/48KiB/timeout1s; sin reintentos nuevos. Fallos de cola pueden emitir diagnóstico reducido por el canal separado del lote8. El resultado failed no modifica configuración, permisos, contratos o disponibilidad de la API: este productor es observación opcional. Captura fallida no reejecuta el chequeo ni lanza excepción al lifespan.

Telemetría deshabilitada/configuración inválida: no ejecutar ni emitir. Evitar duplicación si start() reutiliza productor vivo; nuevo proceso/productor puede emitir un resultado nuevo. Registrar el intento por instancia antes de ejecutar/capturar para impedir reentrada; cierre no ejecuta otro chequeo ni crea tareas huérfanas. No añadir variables/keys, dependencias, persistencia, forwarding ni despliegue.

## Archivos revisables

- backend/app/main.py (protegido): integrar el chequeo una vez tras start(), dentro del lifecycle existente, sin alterar routers, auth, CORS, health o respuestas.
- Nuevo backend/app/telemetry/integrity_producer.py: comprobación acotada y captura opcional con bandera por instancia.
- backend/app/telemetry/server.py: añadir sólo data_integrity_checked a admisión servidor/sink.
- Nuevo backend/tests/test_telemetry_integrity.py y ajustes de expectativas de arranque en integraciones existentes: distinguir evento de integridad de eventos del caso probado, conservando sus aserciones.
- README backend bilingües y documentación SDD/evidencia.

Fuera: schemas.py/contrato público, auth/auditoría, datos/modelos/migraciones, DB/conexiones, frontend, env/claves/Compose/CI, Memory Bank/Rules, despliegue, commit/push/PR.

## Criterios de aceptación y validación

1. Archivo real del paquete y modelos coherentes producen ok; probar reordenación equivalente, tamaño excesivo, JSON inválido/duplicado, archivo ausente y discrepancias de catálogo/version/discriminator/campos → failed.
2. Evento cerrado y anónimo con check=event_contract, sin contenido/excepción/ruta o identificadores operativos en evento/log. No afirmar cobertura de references/historical_coverage.
3. Una ejecución por productor válido, arranque repetido sin duplicado, nuevo productor puede repetir; deshabilitado/invalidado no ejecuta; fallo chequeo/captura no bloquea API. Cierre limpio.
4. Browser rechaza este tipo; sink interno lo acepta; canal diagnóstico no lo admite. Cuota/sink normal roto conserva API y diagnóstico independiente sin recursión.
5. Pruebas unitarias y lifespan real en PostgreSQL sintético aislado (únicamente para regresión de la aplicación; comprobación no usa DB); suites de telemetría/auth/health, contratos y auditoría pasan. Revisar diff y validate-delivery.

## Aprobación requerida

AGENTS.md protege seguridad/configuración de entornos; main.py configura el lifecycle de la aplicación. El usuario respondió «apruebo» a la solicitud expresa del cambio de arranque y del lote completo; autorización registrada en la sesión.

Con esta implementación hay19 tipos con cobertura al menos parcial y20 sin productor. No constituye cierre global: referencias/cobertura histórica, diagnósticos browser, demás ámbitos y dominios inexistentes permanecen pendientes.


## Evidencia del lote9

255 pruebas backend PASS;8 integraciones omitidas sólo sin DB.158 pruebas PASS en PostgreSQL16 sintético aislado/tmpfs, incluidas todas las integraciones y los16 casos nuevos.113 regresiones de contratos/serialización/OpenAPI/entrada/Compliance/catálogos PASS en otra base sintética nueva. Recuentos solapados; imagen final7ad72aca4a57. git diff --check PASS; staged vacío.

Se corrigieron durante validación dos casos: generación de campos dependiente del orden de objetos JSON, y prueba de salud que vaciaba sólo un lote antes de verificar sus eventos. Suites finales repetidas con éxito. Las integraciones de negocio filtran únicamente el nuevo evento de arranque; el test específico verifica su admisión y contenido, sin debilitar aserciones de negocio.

No se cambiaron main routers/health/auth, contrato JSON, datos, env, infraestructura ni servicios locales. Sin persistencia/exportación, despliegue, commit o cierre global.
