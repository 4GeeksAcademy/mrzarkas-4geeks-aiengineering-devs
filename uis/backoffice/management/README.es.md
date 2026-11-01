# Backoffice Management de HealthCore

UI estática de desarrollo para lectura de catálogos, maestros sintéticos y
registros autorizados de auditoría Management. Puede servirse con cualquier
servidor estático. Introducir la URL de la API y un JWT de desarrollo: el token
no se persiste y la autorización del backend sigue siendo la frontera de seguridad.

Es de solo lectura en M6. Las mutaciones administrativas siguen disponibles en
la API protegida, pendientes de UX final y aprobación M0.

## Arranque integrado

Desde la raíz: `podman compose up --build -d` (o `docker compose`).
Abrir http://localhost:8080/management/ y usar http://localhost:8000 como URL API.
Management comparte API, base y servidor estático con incidencias operativas.
Consultar la [configuración](../../../frontend/README.es.md). Se mantienen los controles JWT.

[English](./README.md).


## Identidad visual

La interfaz utiliza la paleta de la portada HealthCore Digital, CSS nativo,
distribución responsive y foco visible de teclado. Se conservan las consultas
a la API, las rutas y el manejo del token. Las tablas se desplazan dentro de
sus contenedores en pantallas pequeñas.

Validación: sintaxis JavaScript y comprobación del diff correctas; HTTP
confirma que ambas páginas y CSS coinciden con los archivos locales. Se
revisaron las pantallas iniciales en escritorio y Management a 393px.
Quedan pendientes las vistas con datos autenticados, el recorrido completo
por teclado y las incidencias en móvil; no se proporcionó JWT de desarrollo
para revisar las vistas con datos.


## Telemetry

Optional shared capture is disabled by default. See [documentación de telemetría](../operational-incidents/telemetry/README.es.md). Captura compartida opcional, desactivada por defecto.

## Configuración local de telemetría en Compose

Compose raíz inyecta configuración/claves telemetry sólo al backend. Backoffice recibe únicamente TELEMETRY_ENABLED, APP_ENVIRONMENT y BACKOFFICE_TELEMETRY_ENDPOINT (por defecto http://localhost:8000/telemetry/events). El entrypoint envsubst oficial de Nginx renderiza operational-incidents/nginx/default.conf.template y sirve /telemetry/config.json con sólo enabled/endpoint/environment y Cache-Control:no-store. Incidencias y Management usan esa misma configuración/API. Ninguna clave HMAC ni JWT pasa a Nginx o navegador. Actualizar la URL pública si cambia API_PORT; CORS vigente admite backoffice local8080.

Fuera de Compose se conserva telemetry/config.json desactivado por defecto. Activar sólo con datos sintéticos y claves servidor válidas; sin contexto no hay captura. Referencias a colectores externos siguen sin forwarding/persistencia. Aplicar configuración local con podman compose up --no-deps --build -d backend backoffice; reinicia sólo estos servicios, sin ejecutar db-init ni modificar registros de base de datos. No autoriza producción.
