# HealthCore backoffice — progressive Next.js migration

Internal pre-MVP prototype for isolated synthetic development. The native applications in `operational-incidents/` and `management/` remain available. This implementation does not authorize a pilot or production use.

## Runtime and routes

Next.js 16.4.3, React 19.3.1, TypeScript strict, Node 24 and pnpm 10.18.3. Run commands from this directory:

```sh
pnpm install --frozen-lockfile
APP_ENVIRONMENT=test BACKEND_URL=http://127.0.0.1:8000 pnpm dev
pnpm types:check
pnpm typecheck
pnpm test
pnpm build
APP_ENVIRONMENT=test BACKEND_URL=http://127.0.0.1:8000 pnpm start
```

Open `http://127.0.0.1:3100/next`. `pnpm start` copies generated assets to the standalone output. Set `HOSTNAME` and `PORT` if needed. Build/dev disable Next vendor telemetry. Business telemetry is separately opt-in (`TELEMETRY_ENABLED=false` by default).

| Route after `/next` | Behavior |
| --- | --- |
| `/management/catalogs`, `/management/reference-data`, `/management/audit` | Existing read-only Management queries |
| `/summary`, `/incidents`, `/incidents/new`, `/incidents/[id]` | Metrics, URL filters/paging, creation, editing, audited state/area changes and partial timeline |
| `/inventory/items`, `/inventory/items/[id]` | NEW UI: catalog, lots, clinical stock/history and authorized actions |
| `/inventory/stock`, `/inventory/reorder`, `/inventory/audit` | NEW UI: scoped stock, reorder, audit and access denials |

## Authorization and data

Paste an existing synthetic development JWT. Its input clears after connection; credentials and remote state remain in memory and clear on disconnect/401/reload. Decoded claims only control presentation; the Python API validates signatures and scopes. The proxy has a fixed server-only `BACKEND_URL`, reviewed OpenAPI allowlist, bounded bodies, no cookies and private/no-store responses. It rejects use unless `APP_ENVIRONMENT=development` or `test`. The auth-token endpoint is not exposed through this proxy.

Incident permissions remain admin/technology/responsibleArea/compliance/direction. Direction sees summaries only; responsibleArea edits title/description in its own area. Only admin reassigns areas. Inventory roles are independent: inventoryAdmin writes catalog/lots without stock; operator records in/out in its clinics; manager additionally configures reorder, counts and compensates; regional reads its jurisdictions; auditor reads stock/audit within authorized historical country scope. No UI action grants backend permission.

Inventory clinic/lot UUIDs are explicit because the current API offers no clinic lookup to those roles, no configuration GET and no list totals. Next-page remains available on short array pages. Stock is calculated by the API. Writes never retry automatically or optimistically; uncertain results require consulting authoritative data/history and explicit acknowledgement. No drafts or patient data are persisted in browser storage. Use synthetic operational text only.

## Local coexistence and rollback preparation

The default stack and legacy files are unchanged. `../../docker-compose.backoffice-next.yml` is an optional override for the existing root Compose file. It adds a private standalone service and the alternative Nginx template. Review configuration with fictional variables and `--env-file /dev/null`; the override must only be used with an isolated synthetic backend. Running or deploying a shared stack requires separate authorization.

The optional Nginx map preserves `/` and `/management/`, forwards `/next` and `/next/`, and aliases `/api-core/` to the fixed reviewed forwarding handler. Existing telemetry receiver paths remain intact. The public frontend and its React history stay in `/frontend`; the shell links to its local existing route and requires reconnection when switching applications.

Rollback is a UI-route change: restore the original Nginx template/omit the override using the same API/schema. Never delete database volumes or downgrade migrations. Inventory has no previous UI; disable its new routes rather than claiming a legacy fallback. Activation, retirement, production authentication, Compliance/Data Governance review and performance budgets remain separate gates.

## Reproducible synthetic validation

`scripts/validation-api.py` uses the backend test virtualenv, `pgserver`, a fresh temporary PostgreSQL database, synthetic seeds and a random process-only JWT key; it applies existing migrations only to that isolated database and serves port 18190. It never reads `.env`. Ctrl-C stops it. Install that test tooling in a temporary Python environment if unavailable; do not point the suite at shared data.

Build/start Next against that fixture API on a loopback port, then run with system Chrome installed:

```sh
HC_SYNTHETIC_TESTS=1 BACKOFFICE_TEST_URL=http://127.0.0.1:3100 BACKOFFICE_TEST_API=http://127.0.0.1:18190 pnpm test:e2e
node --test operational-incidents/telemetry/tests/*.test.mjs
```

The suite rejects non-loopback targets and requires the synthetic opt-in. It exercises real API permissions, scoped denials, immutable correction, memory-only connection, uncertain writes and automated accessibility at 320/393/1350 pixels. Traces, video and screenshots are disabled to avoid credential artifacts. Unit tests separately cover contract/error handling, cancellation, HTML escaping and mutation gates.

`contracts/openapi.json` is the reviewed backend-generated snapshot; `pnpm types:generate` regenerates transport types and `types:check` verifies drift against that snapshot. Refreshing the snapshot requires review against the actual backend (the check does not query a live API). No backend endpoint or schema changed here.

`scripts/validation-legacy.py` serves legacy assets read-only on loopback 8080. `HC_SYNTHETIC_TESTS=1 node scripts/measure.mjs` compares Management cold/warm in three trials at two widths against the same API, emitting only metrics. Its scope and compression limitations are explicit; it is not a complete production benchmark. Execution evidence and remaining gates live in `../../memory-bank/specs/migrationBackoffice/nextjs-migration/`.

The API fixture defaults to 127.0.0.1. For an isolated Podman machine test only, `HC_QA_API_HOST=0.0.0.0` allows the temporary container to reach it; never use this harness on a shared environment.

`python scripts/validation-regression.py` (with temporary QA Python/pgserver available) runs the existing selected auth/incident/inventory/Management tests against a second fresh database, then stops PostgreSQL. It does not replace the E2E suite.
