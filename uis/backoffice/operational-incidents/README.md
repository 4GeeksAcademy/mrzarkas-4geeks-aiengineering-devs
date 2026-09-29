# Operational incidents backoffice

Static, dependency-free development UI for the `OperationalIncident` API.
It provides a paginated incident queue and a detail page with the scoped
title/description editor. It uses the API as the authorization boundary and
is intended for synthetic development/test data only; it is not approved for
shared write access, real data, pilot, or production.

## Run locally

Recommended: start PostgreSQL, the API, and this backoffice together from the
repository root using Docker Compose:

```sh
cp services/central-api/env.example services/central-api/.env
docker compose --env-file services/central-api/.env up --build
# Podman: podman compose --env-file services/central-api/.env up --build
```

Open `http://localhost:8080` and use `http://localhost:8000` as the API base
URL. Compose applies migrations and loads synthetic development catalogs and
reference data before starting the API. The values in `env.example` are for
local development only.

To run only the static UI without Compose, serve this directory with a static
HTTP server (opening `index.html` directly may prevent browser module loading):

For example, from the repository root:

```sh
python -m http.server 8080 --directory uis/backoffice/operational-incidents
```

Open `http://localhost:8080`, enter the API base URL and a development JWT.
The JWT remains in JavaScript memory only; it is not written to browser
storage or the URL and is discarded on disconnect or reload. Use HTTPS outside
local development. If the UI and API use different origins, configure the API
to allow only the UI origin and the required `Authorization` and
`Content-Type` headers; do not use wildcard CORS for this authenticated client.

## Pages and behavior

- `#/incidents`: paginated queue with status and severity filters. Broader
  roles can also request an area filter; `responsibleArea` stays scoped to its
  JWT area and does not receive that filter. The list shows explicit loading,
  recoverable error, and empty-result states. The create button is available
  only to `admin`, `technology`, and `responsibleArea`.
- `#/incidents/new`: create an incident using active catalogs and reference
  data from the API. Clinic options follow the selected jurisdiction, while
  the API validates the affected system's jurisdiction. The reporter's
  identity is derived by the API from the JWT and is never sent by the form.
- `#/incidents/{uuid}`: incident detail. `responsibleArea` can edit only title
  and description when the incident's `responsible_area_id` matches its JWT
  `area_id`. `admin` and `technology` use their existing general update
  capability; read-only roles receive no editor. API authorization remains
  authoritative even if a request bypasses this UI.

Incident creation is shown for `admin`, `technology`, and `responsibleArea`;
the latter can only submit incidents for the area in its JWT. A successful
create opens the new incident detail and displays a confirmation.

The UI decodes JWT claims only to present appropriate controls. It does not
verify signatures or grant access. Catalog labels and reference-data labels
are loaded from API endpoints rather than hardcoded. API-provided values are
inserted as text nodes, not interpreted as HTML.

Current API contract limits shown in the editor are 200 characters for title
and 10,000 for description. The PHI warning is a user reminder, not a PHI
detector. These values remain subject to M0 approval; do not treat this
prototype as a compliance control.