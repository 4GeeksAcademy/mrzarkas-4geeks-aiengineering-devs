# HealthCore Management backoffice

Static development UI for reading catalogues, synthetic master data and
authorized Management audit events. Serve the `uis/backoffice/management`
directory with any static server, then enter the API URL and a JWT issued for
development. It never persists the token and backend authorization remains the
security boundary.

This is intentionally read-only in M6. Administrative mutations remain
available through the protected API while the final UX and M0 approvals are
pending.


## Integrated startup

From the monorepo root: `podman compose up --build -d` (or `docker compose`).
Open http://localhost:8080/management/ and use http://localhost:8000 as the API URL.
Management shares the API, database and static server with operational incidents.
See [configuration](../../../frontend/README.md). Existing JWT controls remain required.


## Visual identity

The UI uses the HealthCore Digital landing palette, native CSS, responsive
layouts and visible keyboard focus. Existing API requests, routes and token
handling are unchanged. Tables scroll within their containers on small screens.

Validation: JavaScript syntax checks and diff whitespace checks passed;
HTTP checks confirmed both pages and CSS match local files. Both initial
screens were reviewed on desktop, and Management at 393px. Authenticated
data views, full keyboard traversal and mobile incidents review remain
pending; no development JWT was supplied for the data views.


## Telemetry

Optional shared capture is disabled by default. See [telemetry documentation](../operational-incidents/telemetry/README.md).

## Local Compose telemetry configuration

The root Compose injects server telemetry settings/keys only into the backend. Backoffice receives only TELEMETRY_ENABLED, APP_ENVIRONMENT and BACKOFFICE_TELEMETRY_ENDPOINT (default http://localhost:8000/telemetry/events). The official Nginx envsubst entrypoint renders operational-incidents/nginx/default.conf.template and serves /telemetry/config.json with exactly enabled/endpoint/environment and Cache-Control:no-store. Incidents and Management use that same configuration/API. No HMAC or JWT key is passed to Nginx or the browser. Update the public URL if API_PORT changes; the existing CORS policy supports local backoffice port8080.

Static serving outside Compose retains telemetry/config.json disabled by default. Enable only with synthetic data and valid server keyrings; a missing context keeps capture inactive. Endpoint references for external collection still do not forward or persist. Apply local configuration with podman compose up --no-deps --build -d backend backoffice; this restarts these two services without rerunning db-init or changing database records. No production approval.
