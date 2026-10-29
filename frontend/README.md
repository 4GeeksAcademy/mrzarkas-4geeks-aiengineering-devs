# Integrated HealthCore environment

One Compose project shares the API and PostgreSQL across the Next.js page,
operational incidents and Management. Local synthetic-data prototype without
patient data, not approved for pilot or production.

## Start

From the monorepo root:

```sh
podman compose up --build -d
```

With Docker active, use `docker compose up --build -d`. The local `.env` is
configured. On a fresh checkout, copy `.env.example` to `.env` and fill every
variable before starting. Never upload `.env`.

Startup applies existing migrations and synthetic seeds to the shared database.
The database is no longer empty: integration supersedes the original minimal
exercise scope. No volumes are deleted and no historical data is imported.
The `mvp-postgres-data` name is retained to preserve the current local database.

## Applications

| Application | Local URL |
| --- | --- |
| Next.js status page and links | http://localhost:3000 |
| Operational incidents | http://localhost:8080 |
| Management | http://localhost:8080/management/ |
| API and PostgreSQL status | http://localhost:8000/status |
| OpenAPI | http://localhost:8000/docs |

Next.js fetches `http://backend:8000/status` on the server without caching, with
a five-second timeout. The backend uses `db:5432`. Incidents and Management
share origin 8080 and existing authorization controls. Their screens require
the local API URL and a development JWT; see the existing API guide.

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

Use the same user, password and database in DATABASE_URL as above. Generate
each secret separately; never reuse credentials from another environment.
BACKOFFICE_URL is browser-facing; BACKEND_URL is internal. Changing port 8080
requires reviewing the existing CORS policy before using the UI.
Node 24 and Python 3.12 are installed in images; the first build requires
Internet. Python uses uv and Next.js uses pnpm.

## Checks and stop

```sh
podman compose ps
podman compose logs -f
curl --fail http://localhost:8000/status
curl --fail http://localhost:3000
curl --fail http://localhost:8080
curl --fail http://localhost:8080/management/
podman compose down
```

`db-init` exits successfully after preparing the database; the other four
services stay running. `test` only runs through its explicit profile.
Avoid `down -v` when preserving the database. The
`docker-compose.operational-incidents.yml` file is a historical configuration
copy; it is no longer needed to start this project.

[Español](./README.es.md).


## HealthCore Digital landing

The homepage has a corporate header, welcome hero, cards for existing
Operational incidents and Management, an institutional introduction and footer.
The original tool URLs are unchanged. Inventory is not implemented and is not
shown as an available tool. A small footer indicator preserves the existing
server-side /status connectivity check.

Styles use native Next.js CSS Modules (`app/page.module.css`), system fonts,
visible keyboard focus and reduced-motion support. The hero uses the locally
provided `app/assets/imgs/AdobeStock_2207054294.jpeg` through next/image. Its
original file is unchanged; images and fonts need no external runtime services.

Validate the production build with `podman compose build frontend`. To preview
only this change, use `podman compose up -d --no-deps frontend` and open port
3000. No backend or database initialization is needed for this UI refresh.
The existing package scripts provide build/dev/start; no lint or test script
is configured. Verify desktop/mobile layouts, keyboard navigation and both
tool links in a browser.

Validation performed: production build passed; the homepage, both tool URLs
and all nine referenced resources returned HTTP 200. Desktop was visually
reviewed. Full mobile visual review, keyboard traversal and console review
remain pending because concurrent Chrome focus changes prevented completion.
Lint and tests were not run because no scripts are configured.
