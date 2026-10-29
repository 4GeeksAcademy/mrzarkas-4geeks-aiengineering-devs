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
