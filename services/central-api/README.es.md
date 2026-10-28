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
cp .env.example .env
# Completar .env según la guía integrada enlazada abajo.
docker compose up --build
# Usuarios de Podman: podman compose up --build
```

Compose inicia PostgreSQL, aplica migraciones Alembic, carga los catálogos
provisionales y los datos sintéticos de referencia, y después inicia la API y
el backoffice estático. Abrir `http://localhost:8080` para la UI y
`http://localhost:8000/health` para comprobar la API. Las credenciales de base
de datos y la clave JWT se generan localmente en el `.env` raíz;
`.env.example` contiene solo los nombres de variables. Git ignora `.env`.

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

DATABASE_URL del .env raíz debe usar el hostname del servicio `db`. No incluir credenciales reales en
`env.example` ni en Git.

Después de aplicar las migraciones, cargar los catálogos con:

```sh
uv run --no-sync seed-catalogs
```

La imagen instala la API como paquete y genera el ejecutable a partir de
`[project.scripts]`. Con Podman puede ejecutarse dentro del contenedor:

```sh
podman compose exec backend uv run --no-sync seed-catalogs
```

Documentación en inglés: [README.md](./README.md).

## Stack contenedorizado integrado

El Compose raíz inicia PostgreSQL, aplica las migraciones existentes y los
seeds sintéticos mediante `db-init`, y después inicia la API compartida,
Next.js en el puerto 3000 y el backoffice estático en 8080 (Management en
`/management/`). Todos usan el `.env` raíz y la misma base de datos. Consulta
la [guía](../../uis/backoffice/stack-status/README.es.md).
`GET /status` ejecuta `SELECT 1`, devolviendo HTTP 200 con
`{"status":"ok","database":"connected"}` o HTTP 503 con
`{"status":"error","database":"unavailable"}`. `/health` no cambia.
Python 3.12 conserva la restricción del paquete existente. Los requisitos
fijados se comparan con uv.lock y se instalan con uv pip; uv sync instala
el proyecto. La etapa test incluye las dependencias de desarrollo.

Pruebas de estado sin PostgreSQL: `uv run --no-sync pytest tests/test_status.py -q`.
Suite completa desde la raíz: `docker compose --profile test run --rm test`.
La suite modifica registros sintéticos: usar solo la base local de desarrollo.
