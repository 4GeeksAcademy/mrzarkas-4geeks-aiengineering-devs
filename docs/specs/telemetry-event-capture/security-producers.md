# Lote6 revisable: autenticación y denegación de capacidades

Estado: aprobado e implementado para desarrollo sintético. Rama feature/telemetryEventCapture; contrato1.2.0 sin cambios.

## Fuentes y semántica

- authentication_succeeded: primera validación JWT satisfactoria observada de una credencial por proceso mientras sigue vigente. No emisión por cada solicitud ni afirmación de login SSO. La sesión conceptual es esa credencial verificada; sessionId=null porque no existe sesión browser autoritativa en la dependencia. channel=api.
- authentication_failed: dependencia get_current_actor rechaza credencial ausente/inválida/expirada. reasonCode missing/invalid/expired, reducido por tipo de excepción; nunca mensaje JWT literal. Sin actor fiable: userId=null.
- authorization_denied: require_capability rechaza capacidad para actor ya verificado. reasonCode=capability; operation de allowlist según mapa explícito de capacidades. No clasificar403 por texto libre ni afirmar cobertura de area_scope/jurisdiction_scope. Denegaciones de políticas contextuales quedan pendientes de otro lote.

El ámbito de la verificación/denegación de capacidad precede a cargar clínica: jurisdiction=null, con claves generales exclusivamente servidor. No consultar clínica sólo para enriquecer una denegación ni reutilizar un contexto browser no validado. El endpoint /auth/tokens no es login y no genera authentication_succeeded por emitir tokens.

## Captura implementada

1. get_current_actor admite Request opcional para llamadas directas/tests; deja descriptor seguro después de construir Actor verificado, o descriptor anónimo reducido antes de su401 actual. No cambia validación JWT, claims, respuesta o excepción existente. Excluir /telemetry/context y /events para evitar que transportar telemetría genere nuevos eventos.
2. require_capability deja descriptor de denegación antes de403. Mapa explícito desde capacidades actuales a read/create/update/transition/assign/manage; capacidad sin mapeo no inventa operation.
3. authentication_succeeded deduplica por HMAC interno de credencial íntegra ya verificada, derivado con propósito propio de clave general CONTEXT. El HMAC nunca se exporta. Sólo digest y expiry verificado persisten en memoria; sin token, claims/UUID/rol/área persistidos. Capacidad1024 entradas, limpieza de expirados, sin evicción de entradas vigentes: saturación descarta nuevos hechos en vez de provocar duplicados por evicción. Sin exp válido no capturar éxito; no modificar la autenticación existente. Reserva sólo cuando la cola acepta el evento. Cierre elimina estado. Deduplicación local de mejor esfuerzo: reinicio/múltiples procesos pueden repetir el evento; no prometer sesiones únicas globales.
4. Middleware ASGI captura al enviarse el cuerpo final. Éxito de autenticación no exige éxito de negocio: actor verificado puede terminar403/404/500 manejado.401 requiere descriptor authentication_failed;403 requiere descriptor explícito capability. Excepción/desconexión sin respuesta final no emite. Un403 de capacidad puede generar primera autenticación y denegación como hechos distintos.
5. requestId UUID interno compartido con RequestCompletionMiddleware mediante estado efímero de solicitud; nunca aceptar cabecera de cliente ni publicar cabecera nueva. Los tres eventos usan ese UUID y eventId independiente. Sin propagación a otros productores anteriores. Estado/descriptores se limpian al finalizar.
6. userId HMAC general sólo para Actor verificado; nunca derivado de JWT inválido. Properties exclusivamente jurisdiction/environment más channel o reasonCode/operation según tipo. sessionId=null. Nada de tokens/URLs/cuerpos/PHI/IDs operativos/mensajes de error.
7. Reutilizar lifecycle opcional y ServerQueue existente, con partición GENERAL:security, lotes20/10 y límites200/256KiB. Captura general sin consultas DB. Configuración inválida o cola saturada descarta sin afectar seguridad/negocio. No usar logs o telemetría recursiva para sus fallos; los contadores existentes son sólo locales. Reutiliza claves actuales; no habilitar exporter o almacenamiento.
8. Cambiar sólo allowlist del sink servidor para estos tres tipos; ingreso browser conserva cinco tipos. Políticas de permisos, firma/expiración JWT, rutas públicas y auditoría persistente permanecen intactas.

## Archivos concretos

Archivos protegidos expresamente aprobados:
- backend/app/auth/dependencies.py: Request opcional/descriptores en get_current_actor y require_capability; controles y errores existentes conservados.
- backend/app/main.py: registro de middleware de seguridad y orden compatible con correlación/finalización; sin cambiar CORS/auth/lifecycle.

Otros archivos del lote:
- Nuevo backend/app/telemetry/security_producer.py: captura general, mapa de operaciones y deduplicación HMAC acotada.
- Nuevo backend/app/telemetry/security_completion.py: observación final ASGI.
- backend/app/telemetry/request_completion.py: requestId interno compartido/limpieza, sin cambiar medición ni respuesta.
- backend/app/telemetry/incident_producer.py: alojar/limpiar estado de deduplicación del lifecycle opcional si corresponde.
- backend/app/telemetry/server.py: permitir tres tipos nuevos exclusivamente servidor.
- Nuevo backend/tests/test_telemetry_security.py y adaptación/regresiones existentes de auth/HTTP/productores para contar tipos correspondientes.
- README backend bilingües y documentación SDD/evidencia.

Fuera: auth/security.py, roles.py, policies.py, emisión de tokens, secretos/.env/Compose/CI, contratos JSON/API, modelos/migraciones/auditoría persistente, Memory Bank/Rules, datos locales/reales, despliegue y commit.

## Criterios de aceptación

1. Credencial válida usada varias veces produce un éxito por proceso/credencial vigente, conservando acceso; credencial distinta puede producir otro. No contar /auth/tokens como login ni /telemetry como uso autenticado.
2. Missing/invalid/expired producen401 y evento anónimo reducido; payload/token adulterado nunca aporta actor/región. Sin errores JWT literales en eventos/logs.
3. Denegación de capacidad devuelve403 idéntico y genera capability con operación permitida/actor HMAC general; políticas contextuales sin descriptor no se reinterpretan.
4. Respuesta fragmentada captura sólo al final; desconexión/excepción/cancelación no emite. requestId interno común y cabeceras/cuerpos intactos.
5. Deduplicación1024/expiry/saturación y cierre acotados, sin tokens almacenados ni nuevo I/O de base. Fallo de captura no bloquea autenticación/autorización.
6. Contratos/browser/colas/HMAC regional existentes correctos. Pruebas unitarias con credenciales sintéticas y ASGI, regresiones permisos/HTTP y PostgreSQL sólo aislado; validate-delivery.

## Límites y autorización

El desarrollador respondió «sí, apruebo» a la solicitud concreta del diseño y de backend/app/auth/dependencies.py y backend/app/main.py. Esa autorización sólo cubre este lote; no modifica políticas, validación JWT ni aprobación de producción. La aprobación previa de Cumplimiento sobre HMAC exclusivamente servidor conserva su alcance.

## Evidencia y límites observados

209 pruebas backend PASS,6 integraciones omitidas sin DB por sus guards.105 pruebas PostgreSQL16 en tmpfs telemetry_validation sintética PASS, incluidas las6 integraciones.113 pruebas de respuesta/serialización/OpenAPI/entrada/Compliance/catálogos PASS en base aislada nueva. git diff --check PASS; recuentos solapados. Imagen final5b4feece8767. Arnés temporal /private/tmp/telemetry-business-compose.yaml y plugin NullPool sólo pruebas; entorno detenido, base local y backend local intactos.

Unitarias verifican tres usos de token→un éxito, token distinto→otro, missing/invalid/expired anónimos,403 de capacidad y operación manage, exclusión /telemetry,204/401/403/404/500 fragmentados, query/send/cancel/fallo captura,1024 entradas sin evicción, limpieza expiry, reserva sólo si enqueue acepta y close vacío. Integración API real confirma mismo requestId en authentication_succeeded general y api_request_completed US, con seudónimos diferentes por clave general/regional, denegación de capacidad y401 anónimo. /telemetry/context no genera éxito nuevo.

Orden: RequestCompletionMiddleware observa final send antes de captura síncrona de seguridad; no incluye esa preparación en durationMs. requestId está en estado efímero y se elimina al finalizar. Se adaptaron sinks de integraciones previas para contar sólo sus tipos y drenar todas las particiones; la integración nueva valida explícitamente coexistencia, sin debilitar permisos o auditoría.

Deduplicación local, sólo de capturas aceptadas en cola: fallo posterior de entrega no reemite ese éxito. Reinicio o más procesos pueden repetirlo; no sirve como recuento global durable de sesiones. El productor de seguridad comparte la habilitación opcional existente (incluidas claves RESOURCE del productor de incidencias); no nuevas variables. Telemetría de denegaciones contextuales permanece pendiente y no se deduce de mensajes403.

Catorce tipos con productor al menos parcial y25 sin productor (20 sin dominio,5 técnicos). Permanecen cobertura general HTTP/auditoría/otros recursos Management y políticas contextuales. Sin forwarding, persistencia adicional, claves nuevas, despliegue, commit ni producción.
