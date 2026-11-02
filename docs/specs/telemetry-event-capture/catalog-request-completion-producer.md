# Lote propuesto — api_request_completed en catálogos

2026-11-03. DESIGN_READY, implementación/pruebas NOT_RUN.

## Fuente y significado
GET /catalogs/{catalog_name} comprueba catalog:read mediante require_capability, consulta catálogo activo y construye CatalogResponse, con caché consciente de versión/actor. Catálogos de incidencias globales, sin clínica. Contrato1.2.0 ya admite route=catalogs, jurisdiction=null y userId seudónimo. No usar nombre/UUID de catálogo, keys/valores, URL o query en telemetría.

## Cambios concretos pendientes de autorización
1. catalogs/router.py: Request opcional, construir respuesta existente y marcar lectura sólo después de autorización/carga/construcción correctas. Mismo contrato HTTP y caché. Marca tanto hit como miss. No emitir tras401/403/404, error de DB/cache/serialización/envío o respuesta incompleta. No añadir captura de operaciones Management de escritura.
2. request_producer.py: nueva marca autenticada general con statekey separado, actor y route cerrado exclusivamente catalogs. Revalidar has_capability(actor.role,catalog:read) y UUIDactor/requestId al capturar; HMAC userId con keyring general. Sólo configuración compartida telemetry_processing_region=None, keys/settings válidos y claves generales independientes existentes. Configuración regional única descarta este incremento si no acredita keyring general independiente; no usar clave US/UK para etiquetar identidad null. Sin nuevas claves/.env. sessionId=null, requestId UUID interno existente; properties jurisdiction=null/environment/route=catalogs/statusCode/durationMs, sin otros campos.
3. request_completion.py: atender marca nueva sólo tras final send exitoso; precedencia clínica > autenticada general > anónima health/status, exactamente una captura del tipo por request. Limpiar todas las marcas y UUID en errores/cancelación/finalización. Capturas clínicas y health/status previas intactas. Cola/sink internos, captura síncrona pequeña de mejor esfuerzo, sin retries/persistencia/nuevos timers.
4. Pruebas de productor/ASGI y HTTP con catálogo sintético y caché hit/miss, README bilingües backend y expediente. Si fuera necesario modificar expectativas antiguas, conservar aserciones del evento original y distinguir tipos nuevos; no retirar cobertura de caché/autenticación.

Sin cambios de modelos/contratos/versiones, política browser, auth roles/capabilities, auditoría, almacenamiento, dependencias, infraestructura, UI, .env, Memory Bank/Rules, commits o despliegue compartido. Sí nuevo tratamiento de identidad/correlación y hook autorizado por lote propio.

## Criterios de aceptación
- GET autorizado con catálogo activo, hit/miss, genera una captura sólo tras respuesta completa; payload route=catalogs, jurisdicciónnull, HMACgeneral, status y duraciónmonotónica reales.
- Actor/session/request anteriores no se reutilizan; UUIDrequest propio, no X-Request-Id; sin texto libre, URL/catálogo/valores/tokens/identificadores originales en evento.
- Permiso ausente, UUIDinválido, keyring inválido/regionalúnico, disabled/closed/cuota de cola/sink/medición inválida ->descarte; respuesta/caché existentes intactos.
- 401/403/404, serialización/carga fallida, streaming incompleto, finalsend fallido/cancelado ->sin evento; estado limpio. Browser no puede afirmar api_request_completed.
- Precedencia única y regresión de capturas clínicas y health/status. Cache hits no omiten ni duplican petición.
- PostgreSQL efímero sintético para HTTP/catalog/caché y regresión general; unitarios de límites ASGI/contexto, diffcheck y validate-delivery. Sin nueva UI/build/E2E porque no cambia frontend ni contrato.

## Límites y aprobación
Extiende un tipo existente:31 tipos parcialmente instrumentados/8 sin productor no cambian. Quedan otras rutas/mutaciones/inventario/Management y correlación integral. Catálogos globales genuinos no deben convertirse en fallback de fallos clínicos. AGENTS.md exige aprobación expresa del nuevo tratamiento de contexto/identidad; revisión externa de Claire y aprobación global siguen pendientes.


## Implementación autorizada y evidencia — 2026-11-03

Aprobación «Sí, autorizo este lote para el prototipo sintético». Implementados hook en catalogs/router.py, marca/captura autenticada general y precedencia/limpieza en request_completion.py. HMAC general sólo en configuración compartida independiente; revalidación UUID/capability y keyring. Capturas clínicas y health/status mantienen firmas y campos. DESIGN_READY/NOT_RUN anteriores son históricos. Sin cambios de contratos, políticas, caché, claves/.env, datos reales, Memory Bank/Rules, migraciones o UI.

- `.venv/bin/pytest -q -m 'not integration' tests/test_telemetry_catalog_request.py tests/test_telemetry_general_request.py tests/test_telemetry_request.py`: **50 passed,2 deselected**,0.81s; incluye regresión clínica.
- `.venv/bin/pytest -q tests/test_telemetry_catalog_request.py tests/test_telemetry_general_request.py tests/test_auth.py`: **55 passed**,0.90s. Nuevo fichero19 casos,18 unitarios/1 integración PostgreSQL real; cache misses1/hits1, respuestas idénticas, dos requestIds internos y ningún evento API en401/403/404. Sin nombres/valores/IDs/token en payload.
- `.venv/bin/pytest -q -m 'not integration' tests`: **664 passed,37 deselected**,4.24s; recuentos solapados.
- Fresh Alembic0001–0013 existentes PASS. Python3.12/.venv, APP_ENVIRONMENT=test; PostgreSQL16 efímero tmpfs loopback18491/inventory_validation_catalog_requests, ambas URLs de integración allí.
- Unitarios: identidad HMAC general distinta de US/UK; permiso, UUID/keyring/región inválidos, disabled/closed/saturación/NaN; streaming, send/cancel/incompleto/duplicado, fallo captura, precedencia clínica/autenticada/anónima y estado limpio.
- git diff --check PASS. Sin frontend/contrato: no build/E2E nuevos ni sincronización de tipos necesaria. Integraciones de dominios ajenos no seleccionadas. No prueba específica de fallo SQL/serialización de catálogo: hook se coloca tras construir respuesta y finally/finalsend se verifican en unitarios.

Cobertura31 tipos parcialmente instrumentados/8 sin productor sin cambio. api_request_completed ahora cubre cuatro lecturas clínicas, health/status generales y catálogos autorizados; otras rutas/mutaciones/ámbitos siguen pendientes. Nueva correlación/identidad continúa sin revisión externa de Claire; entrega best effort, no cumplimiento normativo o producción. Sin commits ni despliegue compartido.
