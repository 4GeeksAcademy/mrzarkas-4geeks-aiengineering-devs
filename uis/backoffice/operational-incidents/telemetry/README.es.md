# Telemetría del backoffice

**Estado local vigente:** contrato1.2.0, track público5 más dos diagnósticos internos, backend/backoffice coordinados y Chrome validado.19 tipos acotados/20 aplazados; cobertura original incompleta. [Estado de entrega](../../../../docs/specs/telemetry-event-capture/delivery-status.md). Los párrafos de evidencia conservan su ejecución histórica;1.1.0 y estados anteriores de navegador no disponible/pendientes no describen la operación actual.

Módulos ES compartidos, sin dependencias nuevas. Incidencias carga `./telemetry/runtime.js`; Management carga `../telemetry/runtime.js`. Se conserva la raíz estática existente y no se modifica Compose. Management servido de forma aislada sin el directorio vecino mantiene la captura desactivada.

`config.json` queda desactivado por defecto. Su activación requiere configuración local compartida aprobada con keyrings regionales separados en backend e inyección de secretos en servidor. El archivo público sólo admite enabled, endpoint y environment; nunca claves ni tokens. El endpoint debe terminar en `/telemetry/events` y compartir origen con la API; producción exige HTTPS. No se configura ni despliega ningún entorno en esta entrega.

Interfaz de captura: `track(eventType, properties)`, contrato 1.2.0. Cinco productores técnicos: navegación, códigos de error saneados, sesión y LCP/CLS/INP numéricos cuando existen APIs compatibles. Lotes de hasta 20 o a los 10 segundos desde el primer evento; separación por contexto inmutable. Fetch con Bearer, X-Telemetry-Context, timeout de 5 segundos, tres reintentos adicionales recuperables y keepalive al ocultarse. Máximos: 200 eventos/256 KiB en memoria, 2 KiB por evento y 48 KiB por cuerpo. Sin persistencia ni exportación de rutas, mensajes de error, nodos DOM o identificadores de pacientes.

El servidor proporciona el seudónimo HMAC y la jurisdicción de la clínica. Los eventos generales usan null. La clínica desconocida o pendiente bloquea la captura; su UUID sólo se usa al pedir contexto y no se incluye en eventos. Se renueva el contexto antes de caducar; no existe gracia entre versiones de clave. Un contexto general caducado puede omitir vitals durante una selección clínica prolongada. El envío al ocultar, cerrar o desconectar es de mejor esfuerzo y puede perder eventos. received no implica almacenamiento ni deduplicación durables.

Resumen no tiene view permitido y se omite expresamente. Hechos de negocio/autenticación sólo servidor con productores acotados; correlación HTTP más amplia, inventario, agregados clínicos y sondas programadas pendientes. No se inventan métricas si faltan APIs. Prototipo sin aprobación para datos reales ni producción.

Pruebas desde la raíz:

```sh
node --test uis/backoffice/operational-incidents/telemetry/tests/*.test.mjs
```

Evidencia 2026-11-01: 67 pruebas Node superadas; recepción HTTP aislada contra el stub real de lotes 20, 1 y 1 con identidad y claves sintéticas, sin base de datos. Navegador, DevTools y medida de coste de captura en navegador: NOT RUN, navegador no disponible. Suite backend acotada previa: 103 pruebas; no cubre integración PostgreSQL de negocio.

## Validación en navegador — 2026-11-01

Esta evidencia actualiza el resultado previo de navegador no disponible para las comprobaciones enumeradas. Se accedió a Chrome mediante UI nativa. Conexión de Incidencias, cola vacía, navegación a creación y lectura de catálogos de Management correctas contra stub autenticado aislado, con identidad/claves sintéticas y sin DB. Al ocultar Incidencias se recibieron eventos numéricos de rendimiento; sesión/navegación de ambas aplicaciones aceptadas con seudónimo, versión 1.1.0 y jurisdicción general null. Consola Management: cero mensajes antes del benchmark (un elemento oculto no inspeccionado). Dos ejecuciones locales de 400 capturas síncronas: p95 0,30 ms y 0,10 ms; máximos 4,70 ms y 0,50 ms. Cada ejecución recibió 401 eventos incluyendo inicio de sesión, sin rechazos. No es garantía para todos los dispositivos. No se copiaron JWT ni claves HMAC a evidencias. Pendientes: detalle clínico/integración regional con DB, inspección completa Network, otros navegadores y productores restantes.

## Validación PostgreSQL y detalle — 2026-11-01

Validación ejecutada en un proyecto Compose temporal independiente, con PostgreSQL 16 en tmpfs, migraciones 0001–0009 y seeds sintéticos; no se utilizó la base de desarrollo. El arnés comprobó contexto US/UK, rechazo de región extranjera, clínica inexistente y rol sin permiso, discrepancia de jurisdicción, desactivación y revalidación de clínica, seudónimos distintos con claves regionales separadas e invalidación de credenciales US en UK. Resultado PASS; primera petición de contexto US 39,38 ms (una observación local, no benchmark de escalabilidad). Recuento de clínicas/jurisdicciones conservado; las pruebas de desactivación sólo alteraron fixtures temporales y se restauraron. Se corrigió el acceso SecretStr en el arnés antes del resultado válido, sin cambio de producto. Suite de contexto previa repetida: 11 PASS.

El servicio frontend real, ejecutado por HTTP con UUID sintéticos y API/DB reales temporales, emitió detalle US y rechazó clínica UK sin fallback general: PASS. Chrome cargó una incidencia sintética creada en ese entorno. Network mostró POST /telemetry/context y POST /telemetry/events con 200, cabeceras Bearer y X-Telemetry-Context y respuesta no-store. Payload de detalle: schemaVersion 1.1.0, seudónimo y properties={jurisdiction:US,environment:test,view:incident_detail}; sin UUID clínico ni texto de incidencia. Tokens y seudónimo se ocultaron en la evidencia de DevTools; sin HAR. La única advertencia de consola procedía de una extensión Chrome, no del código de HealthCore. CORS del arnés permite sólo localhost:18002; no modifica CORS/configuración del repositorio.

Arneses ejecutados: /private/tmp/telemetry_db_validation.py mediante /private/tmp/telemetry-db-compose.yaml; /private/tmp/telemetry_clinical_http.mjs; detalle browser mediante /private/tmp/telemetry-db-browser-compose.yaml. Es evidencia acotada a este entorno, no suite completa PostgreSQL de todos los módulos. Se cierran las verificaciones locales de detalle, contexto regional y Network descritas aquí. Siguen pendientes productores restantes, requestId HTTP, vista resumen, fuentes/agregados/sondas y configuración/revisión de activación. La fase completa no se marca terminada.

## Configuración local de telemetría en Compose

Compose raíz inyecta configuración/claves telemetry sólo al backend. Backoffice recibe únicamente TELEMETRY_ENABLED, APP_ENVIRONMENT y BACKOFFICE_TELEMETRY_ENDPOINT (por defecto http://localhost:8000/telemetry/events). El entrypoint envsubst oficial de Nginx renderiza nginx/default.conf.template y sirve /telemetry/config.json con sólo enabled/endpoint/environment y Cache-Control:no-store. Incidencias y Management usan esa misma configuración/API. Ninguna clave HMAC ni JWT pasa a Nginx o navegador. Actualizar la URL pública si cambia API_PORT; CORS vigente admite backoffice local8080.

Fuera de Compose se conserva telemetry/config.json desactivado por defecto. Activar sólo con datos sintéticos y claves servidor válidas; sin contexto no hay captura. Referencias a colectores externos siguen sin forwarding/persistencia. Aplicar configuración local con podman compose up --no-deps --build -d backend backoffice; reinicia sólo estos servicios, sin ejecutar db-init ni modificar registros de base de datos. No autoriza producción.

Contrato vigente1.2.0: añade modelos generales servidor nullable sin habilitar productores browser. API y frontend deben actualizarse juntos; versiones anteriores del payload se rechazan. Sin productores nuevos ni despliegue.

## Diagnósticos internos frontend

track público conserva sólo cinco tipos. telemetry_contract_rejected y telemetry_delivery_failed internos usan producer=frontend, contexto general válido ya almacenado, jurisdicción/requestId null e identidad/sesión seudónimas autenticadas. No copian campos rechazados, errores literales, URLs o tokens. Sin contexto general omiten diagnóstico, sin adquirir otra identidad. Rechazo genérico de esquema, cuota normal y resultado terminal único generan motivos reducidos; timeout activado por temporizador tiene tipo explícito. Cancelación de lifecycle sólo contabilidad local.

Buffers comparten total200 eventos/256KiB incluyendo vuelo: normal180/224KiB y reserva diagnóstica20/32KiB. Un vuelo global, lotes20/10; diagnóstico prioritario tras terminar vuelo/retries normales. Normal conserva tres reintentos adicionales; diagnóstico un intento5s sin retries ni eventos recursivos. diagnostics() separa contadores. Disconnect/destroy limpia ambos canales y mantiene generación de credenciales. Backend admite sólo estos dos diagnósticos frontend con contexto general firmado e identidad concordante; rechaza api/worker/clínica/requestId. Contrato1.2.0 conservado.74 pruebas Node cubren plazos, cuota incluyendo vuelo, retries, timeout, body reducido y cierre. Servicios locales requieren actualización coordinada; este lote no los despliega.

## Evidencia de activación local conjunta

El2026-11-01 terminó la reconstrucción autorizada backend/backoffice sin db-init ni inicialización DB. API health/status200, contrato1.2.0 e integridadok. Chrome verificó lectura de incidencias y cuatro catálogos Management con credenciales sintéticas. Módulo browser real envió20 eventos de navegación,21 diagnósticos de esquema y uno de entrega (403 simulado sólo en adaptador experimental); envíos reales200. Buffers cerrados vacíos, sin exportar claves; pestañas de prueba cerradas. Detalles docs/specs/telemetry-event-capture/local-activation-validation.md. Sólo prototipo local, sin producción ni cobertura completa.
