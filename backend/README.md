# HealthCore central API

The existing shared FastAPI service contains operational incidents, Management, catalogues, Compliance, authentication and local telemetry. It remains a synthetic pre-MVP prototype. Current telemetry scope and delivery limits: [delivery status](../docs/specs/telemetry-event-capture/delivery-status.md).

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

## Catalog TTL caching (synthetic development)

Active catalog reads use a 60-second per-worker JSON TTL; managed value pages use
30 seconds. Every request authenticates/authorizes and reads catalog metadata.
Keys digest identity/role/area, catalog, version+updated_at, namespace and page.
Existing create/update/activation advance the generation; old entries are no
longer addressable. All effective dates/active flags are cached for the active
catalog and projected at current UTC on each hit, including future activation.
No ORM session/request is stored. Limits: 256 entries, 8 MiB JSON payload total,
256 KiB per entry; fixed 64 lock stripes and 2-second wait before source bypass.
Source errors remain errors. External writes must advance metadata or bypass;
this is not production approval. No Redis, auth, audit or migration change.
Test: `podman compose --profile test run --no-deps --build --rm test`.
Explicit transactional benchmark: `podman compose --profile test run --no-deps --rm test uv run --no-sync python tests/benchmark_caching.py` (one shell line).
It inserts 200 synthetic values, never commits, rolls back and verifies counts.
See docs/CACHING_REPORT.md for measurements and limitations.


Explicit multi-process caching validation (synthetic, isolated database):
`podman compose --profile test run --no-deps --build --rm test uv run --no-sync python tests/validate_caching_workers.py`.
This requires PostgreSQL CREATE/DROP DATABASE permission and creates/drops only
an ephemeral validation database. It does not run during pytest collection.
Evidence: `docs/caching-workers.json` and `docs/CACHING_REPORT.md`.

## Temporary telemetry receiver (opt-in)

The backend now provides authenticated `POST /telemetry/context` and
`POST /telemetry/events`. No event storage, migration, external exporter or
frontend instrumentation is introduced. Only the five reviewed frontend
technical event types are enabled as producers; business/worker events are
rejected even if structurally valid. Typed models derive from the packaged
`app/telemetry/event-contract.json`, copied from the single source
`docs/telemetry/event-schemas.json` (1.1.0). Update both together and verify parity.

Telemetry is disabled by default. Before enabling it, supply configuration
through the approved secret delivery mechanism (do not commit keys):
`TELEMETRY_ENABLED`, `TELEMETRY_PROCESSING_REGION` (US or UK),
`TELEMETRY_USER_KEY`, `TELEMETRY_SUBJECT_KEY`, `TELEMETRY_CLINIC_KEY`,
`TELEMETRY_CONTEXT_KEY`, `TELEMETRY_KEY_VERSION` (default v1), and
`TELEMETRY_CONTEXT_TTL_SECONDS` (1..300, default 300).
The four independent keys must each contain at least 32 UTF-8 bytes and must
not equal the login JWT key. Environment/regional key separation is an
operator requirement; the service does not invent or distribute secrets.
`TELEMETRY_ENDPOINT` is an optional public receiver reference for deployment
configuration, not a router prefix or forwarding destination; the application
only serves `/telemetry/events` and never sends events elsewhere. It is loaded
by Settings for configuration consumers; no backend forwarding is enabled.
Staging does not export until included in the approved event contract.

Obtain context with the existing Bearer and required body `{"clinicId":null}`
for general events, or a clinic UUID for an authorized regional context.
Context tokens contain opaque HMAC bindings, not operational actor/clinic UUIDs.
Send the returned token as `X-Telemetry-Context` alongside the same actor's
Bearer. Tokens and identifiers stay in frontend memory and must not be logged.
The local CORS policy permits this header on the existing port-8080 origins.
General contexts need no database. Clinic contexts reuse existing
`referenceData:read`, read clinic/jurisdiction and reject inactive, missing or
foreign-region clinics. Clinical contexts are revalidated on receipt; the
receiver scans clinic identities to match the binding without keeping a
persistent mapping. This read cost should be measured before shared use.

Batches contain 1..20 events, with a 48-KiB raw-body limit enforced even without
Content-Length. Validation is atomic and errors never reflect the submitted
payload. HTTP 200 `{"received":N}` means validation, not persistence. Only
count and approved event types are logged. Retries may be received twice; no
durable deduplication is claimed. A valid previous context header can renew the
session ID; invalid/expired previous tokens fail, not silently renew. Only the
current key version is accepted: changing keys/version invalidates old contexts
immediately; previous-key grace and frontend renewal are not implemented.

Isolated tests without business database access:
`podman compose --profile test run --no-deps --build --rm -e DATABASE_URL= test uv run --no-sync pytest tests/test_telemetry.py tests/test_telemetry_context.py tests/test_telemetry_identity.py tests/test_status.py -q`.
See `docs/specs/telemetry-event-capture/` for decisions and pending frontend work.

When supplied, TELEMETRY_ENDPOINT must be an absolute URL without credentials/query/fragment and with path /telemetry/events; production requires HTTPS. Invalid references fail context issuance closed without changing the route or forwarding events.

## Incident server producers (opt-in)

`incident_created`, `incident_transitioned` and `incident_assigned` are captured after commit, before refresh. Rollback/conflict/denial emit no event; persistent audit behavior is preserved.

In addition to existing telemetry settings, these producers require `TELEMETRY_RESOURCE_KEY`: a server secret of at least 32 bytes, distinct from all four telemetry keys and JWT, independently configured per region/environment. Separate HMAC subkeys pseudonymize incidentId/auditId; raw UUIDs and incident text are never exported. Missing/invalid settings disable this optional producer only. `.env` is unchanged.

Clinic resolution uses a separate read-only session (16 preparation tasks maximum, 100 ms timeout). Unknown/inactive/foreign clinics or timeout discard capture without affecting business operations. sessionId/requestId remain null. Process-local memory queue: 200 events/256 KiB, batches up to 20 or 10 seconds from the first event, 2 KiB per event/48 KiB per body. One consumer, 1-second sink timeout; failures discard the batch without local retries. Lifespan cleans up tasks/timers. The local sink validates and logs counts/types only, without persistence or external HTTP. Saturation/failure/shutdown may lose events; delivery is not durable.

## Shared backend telemetry (current architecture)

Technology validated one frontend and one backend. Leave `TELEMETRY_PROCESSING_REGION` unset/empty to enable shared-region configuration. The previous US/UK fixed-instance mode remains compatible but is not required. Server-validated Clinic/Jurisdiction selects the regional keyring; browser-supplied regions/keys are never trusted. Both US and UK use the same authenticated API routes and unchanged public contract. Signed contexts bind region, actor and clinic; ingress revalidates clinical scope.

Provide four general keys (`TELEMETRY_USER_KEY`, `SUBJECT_KEY`, `CLINIC_KEY`, `CONTEXT_KEY`, each with the TELEMETRY_ prefix), plus `TELEMETRY_US_{USER,SUBJECT,CLINIC,CONTEXT,RESOURCE}_KEY` and the equivalent `TELEMETRY_UK_*` keys. Generate each independently with `openssl rand -hex 32`; all14 must differ from each other and JWT. General events retain null jurisdiction and their own keys. Regional RESOURCE keys enable incident producers; old `TELEMETRY_RESOURCE_KEY` applies only to fixed-region compatibility.

`TELEMETRY_ENDPOINT`, `TELEMETRY_US_ENDPOINT` and `TELEMETRY_UK_ENDPOINT` are optional references, not enabled forwarding. Context selection copies the corresponding regional reference internally. Local server batches stay partitioned by region/clinic; the sink validates/logs counts only. No external export or storage is added. Deployment location/retention still need Compliance review. The root `.env.example` lists all settings; Compose now injects telemetry variables only into the backend. Tests: `tests/test_telemetry_shared.py` (isolated PostgreSQL tests require synthetic telemetry_validation database).

## Audit-read telemetry (bounded scope)

The server emits audit_accessed after the final body of a successful 2xx response for GET /incidents/{incident_id}/audit, and GET /management/audit-events only with resource_type=clinics plus a clinic resource_id. Existing audit:read permissions and response projections remain unchanged. Global/other-resource audit queries do not invent a clinic. Failed/denied/incomplete responses emit no event.

The producer resolves/revalidates the clinic separately and selects US/UK keys. It shares the optional incident producer lifespan, 16 preparation-task limit, timeout and regional20/10 queue. Missing incident-producer configuration also disables this producer. Properties contain only jurisdiction/environment/surface; no snapshots, text or operational IDs. sessionId/requestId remain null. Inactive/unknown clinics discard capture without affecting reads. Browser ingestion still rejects audit_accessed; only the internal sink permits it. Delivery remains non-persistent best effort. Tests: tests/test_telemetry_audit.py; database integration requires isolated synthetic telemetry_validation. No production activation.

## Clinic mutation telemetry

management_mutation_completed is captured after commit and before refresh, only for clinic creation, updates, activation and deactivation. Persisted audit snapshots determine jurisdiction: after_data for creation, before_data otherwise. US→UK emits once in US; later actions use UK. An inactive historical reference is used only for classification; resolve_clinic retains its checks. Invalid snapshots are discarded without fallback.

Capture shares the existing optional producer, quotas and20/10 queue. userId and auditId use server-only regional HMAC; snapshots, text and operational UUIDs are never exported. Rollback, conflicts, denied requests and empty PATCH do not emit; capture failures do not affect business operations. Browser ingestion rejects this business fact. Tests: tests/test_telemetry_management.py; integration requires isolated synthetic PostgreSQL telemetry_validation. No additional persistence/forwarding or production approval.

## HTTP completion for incident reads

api_request_completed is emitted after the final body is sent for authorized incident detail, history, assignment-history and audit GET requests. Closed properties include revalidated clinic jurisdiction, environment, route=incidents, actual statusCode and monotonic duration in ms from middleware entry to final send, excluding later preparation. requestId is a server-generated internal UUID, with no new response header or client-supplied value; userId is regional HMAC and sessionId is null. /audit also retains its independent audit_accessed event.

Incomplete responses, missing actor/clinic, general routes and /telemetry do not emit. A handled HTTP error with an authorized descriptor may emit its actual status. Capture/sink failures do not affect responses. Existing optional16/100ms limits and20/10 queue are reused; delivery is not durable. Tests: test_telemetry_request.py; DB integration only against synthetic telemetry_validation. No permission, contract1.1.0 or production approval expansion.

## Current telemetry contract1.2.0

The catalogue permits genuine null jurisdiction for nine additional general server technical types (authentication, authorization, API completion, cache, health, integrity and telemetry diagnostics). Together with the previous five browser types,14 are nullable;25 remain US/UK-only. Clinical resolution failures never fall back to null. Producer admission is separate: browser ingestion still allows only five types. This revision adds no producers. Context/body use1.2.0;1.1.0 payloads fail validation, so update API/frontend together. No new keys or local deployment. Details: docs/specs/telemetry-event-capture/general-technical-scope.md.

## Authentication and capability telemetry

The dependency marks authentication_succeeded after JWT verification: one capture per live credential and process, not per request or SSO login. Deduplication stores only a purpose-separated internal HMAC and expiry, up to1024 live entries without eviction. Reservation follows queue acceptance; later delivery failure can lose the fact, and restart/multiple processes can repeat it. Tokens are never stored.

authentication_failed emits missing/invalid/expired with userId=null; authorization_denied covers only require_capability rejection, with an allowlisted operation and general actor HMAC. All use jurisdiction=null and capture after final response send, preserving errors and permissions. Internal requestId is shared with HTTP completion; /telemetry is excluded, with no public header. Area/jurisdiction policies are not instrumented. Capture shares the existing optional producer/queue and keys, without new settings or general-capture DB access. Tests: test_telemetry_security.py; integration only against synthetic telemetry_validation. No production approval.

## On-demand health and cache counters

service_health_checked observes only existing /health and /status calls after the final body is sent, with liveness/database check and ok/failed/timeout outcome.200/503 responses, SELECT1 and error handling remain unchanged; no probe or timeout is added. userId/sessionId/jurisdiction are null; requestId is internally shared and duration measures monotonic middleware completion. Send/capture failures do not alter the check.

catalog_cache_observed samples process-local shared cache hits/misses/bypasses every300s, without resetting counters or reading keys/content. Events carry deltas and observed windowSeconds. Startup baseline excludes earlier activity; invalid/decreasing counters discard and rebase, queue rejection advances the baseline, shutdown loses the partial window. Hit ratio=hits/(hits+misses), unavailable for a zero denominator; bypasses are separate. One optional sampler, idempotent startup and cancellation awaited on shutdown. Anonymous/null events use the existing20/10 queue without durable delivery. Tests: test_telemetry_health_cache.py and test_caching.py; DB integration only against synthetic telemetry_validation.

## Independent telemetry diagnostics

telemetry_contract_rejected observes schema rejection at the telemetry ingress only after the complete422 response, or an invalid normal-server event. It emits anonymous general/null scope without reading rejected fields. Existing401/403/413/503 responses and browser admission remain unchanged. An internal requestId is used only for the completed ingress response.

telemetry_delivery_failed captures normal queue saturation from validated jurisdiction, or one terminal timeout/unavailable outcome per validated batch. A separate optional diagnostic queue and count/type-only validating sink prevent recursion when either channel fails. Both retain20/10 batching,200 events/256KiB including flight,2KiB per event,48KiB per body and one1s sink attempt; no retries, persistence or forwarding. Diagnostic failures affect only local accounting; cancellation/shutdown emits no failure event. Tests: test_telemetry_diagnostics.py; database integration only against synthetic telemetry_validation. No production activation.

## Startup event-contract integrity

data_integrity_checked runs once per valid optional telemetry producer at API lifespan startup, with check=event_contract. A bounded128KiB read rejects duplicate/invalid JSON and compares the packaged contract to the loaded catalogue/version/discriminator and regenerated model schemas. Equivalent JSON object ordering is accepted. It emits anonymous jurisdiction/userId/sessionId/requestId=null with outcome=ok/failed through the normal server queue; no database access or clinical-data scan.

Disabled/invalid telemetry skips the check; an existing producer does not repeat its attempt. Failure or rejected capture does not prevent API startup, and delivery remains best effort. This verifies internal package/runtime coherence, not an artifact signature, frontend synchronization, reference integrity or historical coverage. An import-breaking contract can prevent API startup before observation. Tests: test_telemetry_integrity.py plus lifespan regressions on synthetic telemetry_validation. No new keys, endpoints, deployment or production activation.

## Browser diagnostic admission

POST /telemetry/events now additionally admits telemetry_contract_rejected and telemetry_delivery_failed only with producer=frontend, jurisdiction/requestId=null and a signed general context. Existing Bearer/session/user-HMAC/environment checks remain mandatory. Clinical contexts and api/worker claims are rejected. The five ordinary browser types retain their separate allowlist; internal server facts remain unavailable to browsers. No public schema/version change. Tests: test_telemetry_frontend_diagnostics.py; frontend reserve and no-recursion behavior documented in its shared README. No local deployment in this lot.

## Joint local activation evidence

On2026-11-01 the authorized backend/backoffice rebuild completed without db-init or database initialization. API health/status200 and contract1.2.0 integrity=ok. Chrome verified incident reads and four Management catalogues using synthetic credentials. Real browser module sent20 navigation events,21 schema diagnostics and one delivery diagnostic (a403 simulated only in the experiment adapter); all real sends200. Buffers closed empty; no keys exported, test tabs closed. Details: docs/specs/telemetry-event-capture/local-activation-validation.md. Local prototype only, no production approval or complete coverage claim.

## Clinic inventory

The approved synthetic inventory module provides per-clinic stock and country-scoped
regional reads, integer presentations, lot-aware movements, physical counts,
compensations and mandatory reorder thresholds. Stock is derived exclusively from
movements. See [inventory](app/inventory/README.md) for permissions, API contracts,
migration safety and isolated tests. No UI or production activation is included.


## Inventory telemetry / Telemetría de inventario — 2026-11-02

Optional server capture observes committed HTTP in/out/adjust movements. It revalidates persisted actor, inventory permissions, clinic scope and historical country independently. Regional purpose-separated HMAC identifiers exclude operational UUIDs, quantities, reasons and snapshots. Rollback emits nothing; capture failure preserves the response. Corrections and direct service/demo calls are excluded. Browser ingestion cannot assert these facts. Delivery remains ephemeral best effort. No production activation. See [scope and validation](../docs/specs/telemetry-event-capture/inventory-producers.md).


## Inventory validation telemetry — 2026-11-02

The optional inventory_validation_failed producer captures typed movement rejections for missing reorder configuration (reference), incompatible/missing lots (lot), unavailable pack presentation (unit), and insufficient stock. Capture is attempted only after rollback. It independently revalidates actor permissions, clinic scope and active country; failed context never falls back to general scope. Payload contains only regional HMAC operationId and allowlisted reasonCode plus jurisdiction/environment. Schema errors and unrelated HTTP errors do not emit. Status/detail, denial audit and browser rejection remain unchanged. See [validation lot](../docs/specs/telemetry-event-capture/inventory-validation-producer.md).


## Inventory view telemetry — 2026-11-02

The optional inventory_viewed producer observes completed stock, movement-history and reorder reads with an explicit clinic. It emits once after the final successful HTTP response send, including authorized empty results. It revalidates existing read permissions, clinic scope and active country independently; properties contain only jurisdiction/environment/view and user identity uses regional HMAC. Failed/incomplete responses do not capture. Global/unfiltered reads and items catalogue remain excluded; inactive history still returns according to existing policy but does not capture. Browser cannot assert these facts. See [view scope](../docs/specs/telemetry-event-capture/inventory-view-producer.md).


## Inventory UI-flow telemetry — 2026-11-02

Synthetic UI-flow telemetry adds POST /telemetry/inventory-flow with a closed request (action, clinicId, itemId, optional direction/flowToken). Selection requires stock:read; start requires movement:write and clinic-item configuration. Both revalidate active resources and actor scope. The server issues a regional HMAC flowId and signed credential bound to actor/clinic/item/direction, expiring within 300s and Bearer lifetime without extension. Declared UI gestures use the internal queue; POST /telemetry/events still rejects these types. The credential is not a stock operation or evidence that a human clicked. No persistence or durable dedup. Next captures trusted stock-link clicks and first movement-field interaction using bounded session memory, without delaying business actions. See [UI-flow lot](../docs/specs/telemetry-event-capture/inventory-ui-flow-producers.md).


## Comparable threshold episodes — 2026-11-02

Comparable threshold episodes now follow HTTP movements and compensations over aggregate article/clinic stock. Activation is >=→< reorder point; clearance is <→>= with the same known episode and unchanged threshold. Equality is clear; per-lot reads, zero-delta counts and configuration changes do not emit crossings. New migration0012 creates internal state and append-only transition tables without backfill. Tracking uses a savepoint under existing domain locks; an ordinary tracking failure omits capture while preserving the business movement. Post-commit regional HMAC events export no quantities or operational UUIDs. Persistent state does not guarantee event delivery. Legacy lows and changed thresholds do not receive fictitious paired closes; retention/disposition and Compliance review remain pending. See [threshold lot](../docs/specs/telemetry-event-capture/inventory-threshold-producers.md).


## Rejected direct stock writes — 2026-11-03

Optional stock_direct_update_rejected telemetry recognizes only a top-level JSON stock field rejected as extra_forbidden on movement and item/clinic configuration POSTs. The original HTTP422 response is preserved. Active item/clinic/country, permission and scope are revalidated before queueing channel=api and regional HMAC operationId; stock, body and errors are never exported. Legitimate movement quantity/count inputs are excluded. Global CRUD without clinic context, aliases and external SQL remain uninstrumented. Capture is best effort, with no new tables or policy changes. See docs/specs/telemetry-event-capture/inventory-direct-stock-producer.md; Compliance review remains pending.


## Inventory flow abandonment — 2026-11-03

order_abandoned follows persisted UI selection/start flows. Authenticated activity and confirmation update stages without extending the300s credential; an internal processor scans up to100 rows every60s and closes open flows with≥30min of server-observed inactivity. An in/out movement may supply X-Inventory-Flow-Id: only the exact actor/item/clinic/direction/country binding becomes completed; other matching open flows become uncertain and emit no abandonment. Savepoints and a conservative fallback isolate ordinary tracking failures from business writes. No quantities, reasons, tokens or form contents in the table/events. Migration0013 creates only inventory_telemetry_flow. Retention/disposition and Compliance review remain pending; durable state does not imply durable delivery. See docs/specs/telemetry-event-capture/inventory-abandonment-producer.md for limits and evidence.


## Projection reconciliation — 2026-11-03

POST /inventory/items/{item_id}/clinics/{clinic_id}/reconciliation (optional lot_id, no body) requires existing audit:read and stock:read permissions. The auditor compares service.stock with an independent delta sum in the same REPEATABLE READ READ ONLY transaction, bounded to10000 movements/1s. Result is matched/mismatched/inconclusive, without quantities. Legacy/non-comparable country history, limit or timeout does not emit failure. Only a completed mismatch attempts inventory_reconciliation_failed with regional HMAC checkId and check=stock_projection; the producer revalidates context and may discard. telemetryAccepted acknowledges preparation admission, not delivery. No repair, new table or UI. This does not establish physical inventory accuracy. Evidence/limits: docs/specs/telemetry-event-capture/inventory-reconciliation-producer.md; Compliance review pending.


## Completed general requests — 2026-11-03

api_request_completed observes /health and /status only after the final body is successfully sent, including status503. Genuinely general context: jurisdiction/userId/sessionId null; internal server requestId shared with the independent service_health_checked event. Duration is monotonic from ASGI entry; no body/URL/token/identity/IP or caller correlation header. Capture remains best effort, without HTTP changes or new probes. Other routes remain outside this increment; see docs/specs/telemetry-event-capture/general-request-completion-producer.md.


## Completed catalogue reads — 2026-11-03

api_request_completed observes active catalogue GETs authorized with catalog:read, on both cache hits and misses, only after the response is fully sent. route=catalogs and jurisdiction=null; userId uses independent general HMAC, sessionId=null and requestId is an internal UUID. No catalogue names/values/UUIDs, URL, query or tokens. Single-region configuration without an established independent general keyring discards this capture without changing the read.401/403/404 remain outside this lot. Contracts, cache and permissions are preserved; capture is best effort. Evidence: docs/specs/telemetry-event-capture/catalog-request-completion-producer.md.


## Bounded telemetry closure — 2026-11-03

The current contract is 1.3.0 (39 types, 14 nullable). Clinic-explicit inventory audit reads now emit server-only `audit_accessed` with `surface=inventory` after a completed 2xx response. Active clinic/country, auditor scope and comparable historical country are independently revalidated; unknown/mixed history is discarded without changing the business response. API and consumers must use 1.3.0 together; 1.2.0 is rejected. The approved synthetic scope is technically validated, with 31 types partially instrumented and 8 without producers. Full coverage, durable delivery/retention and Compliance review remain pending. See `docs/specs/telemetry-event-capture/inventory-audit-and-close.md`; earlier version/coverage notes are historical.
