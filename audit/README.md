# Frontend audit evidence

Local synthetic-data environment, 29 October 2026. This tests production builds,
not approval to deploy HealthCore to real users. No development server is used.

The website is `frontend/` at http://localhost:3000/. Its Dockerfile runs
`pnpm build` and starts the standalone production output with `node server.js`.
The dependency-free backoffice is served directly by production Nginx at
http://localhost:8080/. There is no compilation step for its native HTML/CSS/JS.

## Reproduce

```sh
podman compose build frontend
podman compose up -d --no-deps frontend
npm exec --yes --package=lighthouse@12.8.2 -- lighthouse --version
# Set this to the node_modules directory containing the temporary Lighthouse install:
export AUDIT_TOOLS_DIR=/absolute/path/to/temporary/node_modules
node scripts/frontend-audit.mjs audit/before website desktop
node scripts/frontend-audit.mjs audit/before website mobile
node scripts/frontend-audit.mjs audit/before backoffice desktop
node scripts/frontend-audit.mjs audit/before summary desktop
```

Run the same commands with `audit/after` after corrections. Do not overwrite
`before`. `summary` obtains a short-lived development token for `direction`,
which can read metrics only. It navigates, submits the connection form and waits
for actual API metrics within the Lighthouse navigation. It does not seed or
modify operational data and does not persist credentials. The four configured
severity cards contain real API counts from the local synthetic database.

Lighthouse 12.8.2, installed temporarily outside application dependencies; local
Chrome, actual version recorded in every JSON `environment.hostUserAgent`.
Default Lighthouse simulated mobile throttling and desktop preset; explicit
`disableStorageReset: false`; a fresh Chrome process for each run. Exact CPU,
network and viewport settings are in each JSON `configSettings`. Three runs per
profile; compare medians and ranges, not best scores.

`.report.json` and `.report.html` are full reports; `.report.png` is an actual
Chrome screenshot of the report with all four scores and performance metrics.
`.page.png` records the audited screen; `.trace.json` preserves the first run's
Chrome performance trace. The initial CLI reports without numeric suffix are
exploratory runs, separate from the three-run comparison series.
Evaluated script arguments in traces are scrubbed of the development JWT before
writing; the redaction does not change timing or score data.

There is no CrUX/RUM dataset for this private localhost environment. INP and FID
are unavailable as field metrics. TBT is a lab diagnostic, not measured INP.
TTFB from Lighthouse is a local server response measurement, not Internet TTFB.
The authenticated journey includes connection-related layout changes; compare
it only with the same journey after changes, not with an already connected tab.

See `skill-review.md`, `../AUDIT.md` and `../REPORT.md` for interpretation.
