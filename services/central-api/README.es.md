# API central de HealthCore

Aquí vive el servicio FastAPI compartido. El gestor de incidencias se implementará como un módulo de esta API. El esqueleto actual expone `GET /health` sin necesitar base de datos.

## Requisitos

- Python 3.12 y `uv` para ejecución local.
- Docker o Podman con Compose para ejecución en contenedor.

## Arranque local

Desde este directorio:

```sh
uv sync --frozen
uv run --no-sync uvicorn app.main:app --reload
```

Desde la raíz del repositorio, arrancar el contenedor:

```sh
cp services/central-api/env.example services/central-api/.env
docker compose --env-file services/central-api/.env up --build
# Usuarios de Podman: podman compose --env-file services/central-api/.env up --build
```

Compose inicia PostgreSQL, aplica migraciones Alembic, carga los catálogos
provisionales y los datos sintéticos de referencia, y después inicia la API y
el backoffice estático. Abrir `http://localhost:8080` para la UI y
`http://localhost:8000/health` para comprobar la API. Las credenciales de base
de datos y la clave JWT de `env.example` son sólo para desarrollo; cámbialas
en cualquier entorno compartido. Git ignora `services/central-api/.env`.

Detener con `docker compose down`. Añade `-v` únicamente si quieres borrar
intencionadamente el volumen local de PostgreSQL y todos sus datos.

## PostgreSQL, SQLAlchemy y Alembic

La conexión se recibe mediante `DATABASE_URL` y no se almacena en el repositorio. La URL debe usar el dialecto asíncrono de SQLAlchemy:

```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DATABASE?ssl=require
```

Con una base disponible, ejecutar las migraciones desde esta carpeta:

```sh
uv run --no-sync alembic upgrade head
```

Consultar la revisión actual:

```sh
uv run --no-sync alembic current
```

Sin `DATABASE_URL`, la API puede arrancar y responder `/health`, pero Alembic y las operaciones de base de datos fallarán explícitamente porque necesitan una conexión.

Compose configura la URL de base de datos dentro de los contenedores usando el
hostname del servicio `postgres`. No incluir credenciales reales en
`env.example` ni en Git.

Después de aplicar las migraciones, cargar los catálogos con:

```sh
uv run --no-sync seed-catalogs
```

La imagen instala la API como paquete y genera el ejecutable a partir de
`[project.scripts]`. Con Podman puede ejecutarse dentro del contenedor:

```sh
podman exec 4geeks-aiengineering-api-1 uv run --no-sync seed-catalogs
```

Documentación en inglés: [README.md](./README.md).