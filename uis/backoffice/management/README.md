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
