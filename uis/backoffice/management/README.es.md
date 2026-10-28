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
