# Entorno integrado de HealthCore

Un único proyecto Compose comparte API y PostgreSQL entre la página Next.js,
el backoffice de incidencias y Management. Prototipo local con datos sintéticos,
sin datos de pacientes; no autorizado para piloto ni producción.

## Arranque

Desde la raíz del monorepo:

```sh
podman compose up --build -d
```

Con Docker activo, usar `docker compose up --build -d`. El `.env` local ya está
preparado. En una nueva copia, copiar `.env.example` a `.env` y completar las
variables antes del arranque. No subir `.env` a Git.

El arranque aplica migraciones y seeds existentes sobre la base compartida.
Ya no es una base vacía: esta integración prima sobre el alcance mínimo del
ejercicio inicial. No se borran volúmenes ni se importan datos del stack histórico.
El volumen `mvp-postgres-data` conserva su nombre para no reemplazar la base local.

## Aplicaciones

| Aplicación | URL local |
| --- | --- |
| Página Next.js de estado y enlaces | http://localhost:3000 |
| Incidencias operativas | http://localhost:8080 |
| Management | http://localhost:8080/management/ |
| Estado API y PostgreSQL | http://localhost:8000/status |
| OpenAPI | http://localhost:8000/docs |

Next.js consulta `http://backend:8000/status` en el servidor, sin caché y con
límite de cinco segundos. El backend usa `db:5432`. Incidencias y Management
usan el mismo origen 8080 y los controles de autorización existentes.
Para utilizar sus pantallas, introducir la URL local de la API y un JWT de
desarrollo siguiendo la guía existente de la API.

| Variable | Local value / Valor local |
| --- | --- |
| POSTGRES_DB | healthcore_stack |
| POSTGRES_USER | healthcore_stack |
| POSTGRES_PASSWORD | openssl rand -hex 32 |
| DATABASE_URL | postgresql+asyncpg://USER:PASSWORD@db:5432/DATABASE |
| BACKEND_URL | http://backend:8000 |
| APP_ENVIRONMENT | development |
| JWT_SECRET_KEY | openssl rand -hex 32 |
| API_PORT | 8000 |
| FRONTEND_PORT | 3000 |
| BACKOFFICE_PORT | 8080 |
| BACKOFFICE_URL | http://localhost:8080 |

Usar en DATABASE_URL los mismos valores de usuario, contraseña y base definidos
arriba. Generar cada secreto por separado. No reutilizar credenciales de otros
entornos. BACKOFFICE_URL es una URL para el navegador; BACKEND_URL es interna.
Si se cambia 8080, hay que revisar la política CORS existente antes de usar la UI.
Node 24 y Python 3.12 se instalan en las imágenes; la primera construcción
requiere Internet. Se mantiene uv para Python y pnpm para Next.js.

## Comprobaciones y parada

```sh
podman compose ps
podman compose logs -f
curl --fail http://localhost:8000/status
curl --fail http://localhost:3000
curl --fail http://localhost:8080
curl --fail http://localhost:8080/management/
podman compose down
```

`db-init` termina correctamente después de preparar la base; los otros cuatro
servicios permanecen activos. `test` solo se ejecuta con su perfil explícito.
No usar `down -v` si se quiere conservar la base. El archivo
`docker-compose.operational-incidents.yml` queda como copia histórica de la
configuración anterior; ya no se necesita para levantar el proyecto.

[English](./README.md).
