# HealthCore central API

The shared FastAPI service lives here. Operational incidents will be implemented as a module of this API. The current scaffold exposes `GET /health` without requiring a database.

## Requirements

- Python 3.12 and `uv` for running locally.
- Docker or Podman with Compose for containerized runs.

## Run locally

From this directory:

```sh
uv sync --frozen
uv run --no-sync uvicorn app.main:app --reload
```

From the repository root, start the container:

```sh
cp services/central-api/env.example services/central-api/.env
docker compose --env-file services/central-api/.env up --build
# Podman users: podman compose --env-file services/central-api/.env up --build
```

Compose starts PostgreSQL, applies Alembic migrations, seeds the provisional
catalogs and synthetic reference data, and then starts the API and static
backoffice. Open `http://localhost:8080` for the UI and
`http://localhost:8000/health` for the API health check. The local database
credentials and JWT secret in `env.example` are development-only; change them
for any shared environment. Git ignores `services/central-api/.env`.

Stop the stack with `docker compose down`. Add `-v` only if you intentionally
want to delete the local PostgreSQL volume and all its data.

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

The API is installed as a package during the image build, so the
`seed-catalogs` executable is generated from `[project.scripts]`. With Podman,
run it inside the running service container:

```sh
podman exec 4geeks-aiengineering-api-1 uv run --no-sync seed-catalogs
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

Compose overrides the container's database URL to use the `postgres` service
hostname. Never put real credentials in `env.example` or Git.

Spanish documentation: [README.es.md](./README.es.md).