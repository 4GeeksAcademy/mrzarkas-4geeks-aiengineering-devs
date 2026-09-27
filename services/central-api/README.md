# HealthCore central API

The shared FastAPI service lives here. Operational incidents will be implemented as a module of this API. The current scaffold exposes `GET /health` without requiring a database.

## Requirements

- Python 3.12 and `uv` for running locally.
- Docker with Compose for containerized runs.

## Run locally

From this directory:

```sh
uv sync --frozen
uv run --no-sync uvicorn app.main:app --reload
```

From the repository root, start the container:

```sh
docker compose up --build
```

Check `http://localhost:8000/health` for `{"status":"ok"}`. For a different published port, copy `services/central-api/env.example` to a root `.env` and set `API_PORT`; Git ignores `.env`.

## PostgreSQL, SQLAlchemy, and Alembic

The connection is read from `DATABASE_URL` and is never stored in the repository. Use SQLAlchemy's asyncpg dialect:

```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DATABASE?ssl=require
```

With an available database, run migrations from this directory:

```sh
uv run --no-sync alembic upgrade head
```

Check the current revision:

```sh
uv run --no-sync alembic current
```

Without `DATABASE_URL`, the API can still start and answer `/health`, but Alembic and database operations fail explicitly because they require a connection.

Seed the provisional catalogs after applying migrations:

```sh
uv run --no-sync seed-catalogs
```

The seed is idempotent, uses the stable catalog keys, and does not create clinics,
users, systems, or other master data owned by an external domain. It does not
reactivate a value that has been deliberately disabled.

Read an active catalog through the API:

```sh
curl http://localhost:8000/catalogs/severity
```

The endpoint returns only active values currently within their effective date
range, ordered by `sort_order` and then by technical key.

Compose reads `DATABASE_URL` from the root `.env` file and passes it to the container. Never put real credentials in `env.example` or Git.

Spanish documentation: [README.es.md](./README.es.md).