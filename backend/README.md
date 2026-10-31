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
cp .env.example .env
# Fill the root .env using the integrated setup guide below.
docker compose up --build
# Podman users: podman compose up --build
```

Compose starts PostgreSQL, applies Alembic migrations, seeds the provisional
catalogs and synthetic reference data, and then starts the API and static
backoffice. Open `http://localhost:8080` for the UI and
`http://localhost:8000/health` for the API health check. The local database
credentials and JWT secret must be generated locally in the root `.env`;
`.env.example` contains variable names only. Git ignores `.env`.

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
podman compose exec backend uv run --no-sync seed-catalogs
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

The root DATABASE_URL must use the `db` service hostname. Never put real credentials in `env.example` or Git.

Spanish documentation: [README.es.md](./README.es.md).

## Integrated container stack

The root Compose starts PostgreSQL, applies existing migrations and synthetic
seeds through `db-init`, then starts the shared API, Next.js at port 3000,
and the static backoffice at port 8080 (Management at `/management/`).
All services share the root `.env` and the same database. See the
[setup guide](../frontend/README.md).
`GET /status` runs `SELECT 1`, returning HTTP 200 with
`{"status":"ok","database":"connected"}` or HTTP 503 with
`{"status":"error","database":"unavailable"}`. `/health` is unchanged.
Python 3.12 preserves the existing package constraint. Locked requirements
are verified against uv.lock and installed with uv pip; uv sync installs the
project. The test stage includes development dependencies.

Status tests without PostgreSQL: `uv run --no-sync pytest tests/test_status.py -q`.
Full synthetic integration suite from the root: `docker compose --profile test run --rm test`.
The full suite modifies synthetic test records; use only the local development database.

Incident and ComplianceReview read contracts are independent of their input
schemas and preserve the published fields. Response contract tests check exact
output fields, ORM attribute filtering and route schemas; Management HTTP tests
also check collection wrappers and write responses.
Management checks cover all eleven OpenAPI operations, pagination and audit
filters, plus rejection of server-managed fields in catalog and clinic PATCHes.

## Audit response policy

The approved synthetic-environment policy preserves audit identifiers,
references and timestamps. Audit snapshots use event-specific allowlists and
strict Pydantic validation. Non-null title, description and label values in
snapshots, and reasons in Management audit and incident histories, are returned
as `[REDACTED]`; null remains null. Unknown or invalid fields are excluded.
`_redacted: true` inside a snapshot signals content was hidden. Unknown events
or root lists return only that marker; jurisdiction_ids lists in coverage
events remain supported. Historical incident `"None"` review references retain
their original representation. Current and historical events use the same
projection, without rewriting records or changing retention or permissions.
Technical keys remain visible under the existing access policy; their syntax
validation is not a general detector of secrets embedded in identifier values.
The backoffice continues to display reasons, now as the redaction marker.

Final serialization audit (2026-10-31): 145 tests passed against synthetic PostgreSQL; all 28 operations and documentation routes verified. OpenAPI annotations describe existing errors (detail string or validation list), without changing exception handling. See ../docs/serialization-audit.md for approved redaction, measurements, manual Swagger checks and scope limitations. No production approval is implied.
