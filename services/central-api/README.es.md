# API central de HealthCore

Aquí vive el servicio FastAPI compartido. El gestor de incidencias se implementará como un módulo de esta API. El esqueleto actual expone `GET /health` sin necesitar base de datos.

## Requisitos

- Python 3.12 y `uv` para ejecución local.
- Docker con Compose para ejecución en contenedor.

## Arranque local

Desde este directorio:

```sh
uv sync --frozen
uv run --no-sync uvicorn app.main:app --reload
```

Desde la raíz del repositorio, arrancar el contenedor:

```sh
docker compose up --build
```

Comprobar `http://localhost:8000/health`: debe devolver `{"status":"ok"}`. Para cambiar el puerto publicado, copiar `services/central-api/env.example` a un `.env` en la raíz y definir `API_PORT`; Git ignora `.env`.

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

Compose toma `DATABASE_URL` del `.env` de la raíz y la entrega al contenedor. No incluir credenciales reales en `env.example` ni en Git.

Documentación en inglés: [README.md](./README.md).