# Backoffice telemetry

**Current local status:** contract1.2.0, public track5 plus two internal diagnostics, coordinated backend/backoffice and Chrome validated.19 types scoped/20 deferred; full original coverage remains incomplete. [Delivery status](../../../../docs/specs/telemetry-event-capture/delivery-status.md). Evidence paragraphs below record their historical execution;1.1.0 and earlier unavailable-browser/pending states are not current operation.

Shared dependency-free ES modules used by incidents and Management. The module lives under the existing incidents static root so `/telemetry/` works with the current server mounts; Management imports `../telemetry/runtime.js`. Serving Management alone without this sibling directory leaves telemetry disabled.

`config.json` is disabled by default. Activation requires an approved shared local setup with separate regional server keyrings with the backend telemetry settings and secret injection configured, an absolute `/telemetry/events` endpoint on the API origin, and environment `development`, `test` or `production` (HTTPS required in production). This public file contains only enabled, endpoint and environment; never place keys or tokens here. No deployment or environment configuration was changed.

Capture uses `track(eventType, properties)` and contract 1.2.0. Only five technical producers are enabled: navigation, sanitized error reason codes, session lifecycle and supported numeric LCP/CLS/INP. Batches contain up to 20 events or send after 10 seconds from the first event, partitioned by immutable server context. Fetch uses Bearer and X-Telemetry-Context, a five-second timeout, three additional recoverable retries and keepalive on hiding. Queue limits: 200 events/256 KiB; event limit 2 KiB; body limit 48 KiB. No persistence, raw paths, error messages, DOM nodes, patient identifiers or browser secrets are exported.

Context comes from the server; HMAC keys remain there. General events use null jurisdiction. Detail navigation uses the incident clinic UUID only to resolve server context, never in an event. Unknown/pending clinic disables capture rather than using a general context. Context refresh preserves session only while the prior signed context remains valid; rotation has no grace period. Cached general context expiry can suppress document vitals during prolonged clinic selection. Hidden/unload/disconnect delivery is best effort; pending/in-flight events may be lost. Receipt is not durable storage or deduplication.

Summary navigation has no allowed view in this contract and is deliberately omitted. Business/authentication facts are server-only with scoped producers; broader HTTP correlation, inventory, clinical aggregates and scheduled probes remain pending. Unsupported performance APIs produce no fabricated metrics. This prototype is not approved for real data or production.

Run from repository root:

```sh
node --test uis/backoffice/operational-incidents/telemetry/tests/*.test.mjs
```

Evidence on 2026-11-01: 67 Node tests pass, including schema parity, queue/concurrency/deadlines, refresh, retries, privacy and observer calculations. An isolated HTTP test against the actual stub received 20, 1 and 1 events (timeout and explicit keepalive), using synthetic identity/keys and no database. Browser/DevTools and browser capture-overhead measurements remain NOT RUN because no browser is available in this session. Existing backend scoped suite: 103 tests passed; business PostgreSQL integration is not covered by this evidence.

## Browser validation — 2026-11-01

This evidence supersedes the earlier unavailable-browser result for the checks listed here. Chrome was accessible through native UI. Actual incidents connection, empty queue and create navigation, and Management catalogue read succeeded against the isolated authenticated stub with synthetic identity/keys and no database. Hiding incidents emitted accepted numeric timing events; session/navigation events from both applications were accepted with pseudonyms, schema 1.1.0 and null general jurisdiction. Management console showed zero messages before the benchmark (one hidden item, not inspected). Two local runs of 400 synchronous captures produced p95 0.30 ms and 0.10 ms, maximum 4.70 ms and 0.50 ms respectively; each run received 401 events including session start, with zero rejected captures. These are local observations, not guarantees for all devices. No raw JWT/HMAC keys were copied into evidence. Clinical detail/regional real-DB integration, complete Network inspection, other browsers and remaining producers are still pending.

## PostgreSQL and detail validation — 2026-11-01

PASS against a separate temporary Compose project with PostgreSQL 16 in tmpfs, migrations 0001–0009 and synthetic seeds; the development database was not used. Checks cover US/UK context, foreign/missing/unauthorized clinic rejection, jurisdiction mismatch, inactive clinic revalidation, distinct pseudonyms with separate regional keys and rejection of US credentials in UK. First US context took 39.38 ms (one local observation, not a scaling benchmark). Reference counts unchanged; only temporary fixtures were deactivated and restored. The harness SecretStr access was corrected before the passing run; no product change. Existing context suite rerun: 11 PASS.

The actual frontend service emitted US detail against the real temporary API/DB and rejected UK clinic without general fallback: PASS. Chrome loaded the synthetic incident. Network confirmed context/events POST 200, Bearer and X-Telemetry-Context headers and no-store response. Detail payload uses schema1.1.0, pseudonym and jurisdiction/environment/view properties, without clinic UUID or incident text. Tokens and pseudonym were redacted in DevTools evidence; no HAR exported. The only console warning came from a Chrome extension. Test-only CORS allows localhost:18002; repository configuration unchanged.

Executed harnesses: /private/tmp/telemetry_db_validation.py with /private/tmp/telemetry-db-compose.yaml, /private/tmp/telemetry_clinical_http.mjs and browser detail via /private/tmp/telemetry-db-browser-compose.yaml. This closes the described local clinic/regional/Network checks, not the entire PostgreSQL business suite. Remaining producers, HTTP requestId, summary view, absent aggregates/probes and operational activation reviews remain open; full phase2 is not complete.

## Local Compose telemetry configuration

The root Compose injects server telemetry settings/keys only into the backend. Backoffice receives only TELEMETRY_ENABLED, APP_ENVIRONMENT and BACKOFFICE_TELEMETRY_ENDPOINT (default http://localhost:8000/telemetry/events). The official Nginx envsubst entrypoint renders nginx/default.conf.template and serves /telemetry/config.json with exactly enabled/endpoint/environment and Cache-Control:no-store. Incidents and Management use that same configuration/API. No HMAC or JWT key is passed to Nginx or the browser. Update the public URL if API_PORT changes; the existing CORS policy supports local backoffice port8080.

Static serving outside Compose retains telemetry/config.json disabled by default. Enable only with synthetic data and valid server keyrings; a missing context keeps capture inactive. Endpoint references for external collection still do not forward or persist. Apply local configuration with podman compose up --no-deps --build -d backend backoffice; this restarts these two services without rerunning db-init or changing database records. No production approval.

Current contract1.2.0 adds nullable general server models without enabling their browser producers. API and frontend must update together; previous payload versions are rejected. This change adds no producer or deployment.

## Internal frontend diagnostics

The public track interface still admits only five types. Internal telemetry_contract_rejected and telemetry_delivery_failed use producer=frontend, a valid cached general server context, null jurisdiction/requestId, and authenticated pseudonym/session. No rejected fields, raw errors, URLs or tokens are copied. Missing general context suppresses diagnostics without acquiring another identity. Generic schema rejection, normal quota and one terminal delivery outcome generate reduced reasons; timer-triggered timeout is typed explicitly. Lifecycle cancellation is counted locally.

Buffers share a200-event/256KiB total including flight: normal180/224KiB and reserved diagnostics20/32KiB. One global flight,20/10 batches; diagnostic priority after normal flight/retries finish. Normal retains three additional retries; diagnostics have one5s attempt, no retries and no recursive events. Diagnostic accounting is separate in diagnostics(). Disconnect/destroy clears both channels and preserves credential generation. Backend accepts only these two frontend diagnostics with a signed general context and matching identity; api/worker/clinical/requestId assertions remain rejected. Contract1.2.0 unchanged. Tests:74 Node checks, including diagnostic deadlines, quota during flight, retries, timeout, sanitized body and disposal. Local services must update together; this lot does not deploy them.

## Joint local activation evidence

On2026-11-01 the authorized backend/backoffice rebuild completed without db-init or database initialization. API health/status200 and contract1.2.0 integrity=ok. Chrome verified incident reads and four Management catalogues using synthetic credentials. Real browser module sent20 navigation events,21 schema diagnostics and one delivery diagnostic (a403 simulated only in the experiment adapter); all real sends200. Buffers closed empty; no keys exported, test tabs closed. Details: docs/specs/telemetry-event-capture/local-activation-validation.md. Local prototype only, no production approval or complete coverage claim.


## Inventory follow-up — 2026-11-02

Next inventory now has a dedicated authenticated gesture channel for product_selected/order_started; the shared five-type browser module described below is unchanged. Server-issued flow credentials stay in bounded session memory. The inventory backend also captures committed movements, typed validation and completed explicit-clinic reads. Current scope:26 types at least partially covered,13 without producers; see the UI-flow lot.


## Bounded telemetry closure — 2026-11-03

The current contract is 1.3.0 (39 types, 14 nullable). Clinic-explicit inventory audit reads now emit server-only `audit_accessed` with `surface=inventory` after a completed 2xx response. Active clinic/country, auditor scope and comparable historical country are independently revalidated; unknown/mixed history is discarded without changing the business response. API and consumers must use 1.3.0 together; 1.2.0 is rejected. The approved synthetic scope is technically validated, with 31 types partially instrumented and 8 without producers. Full coverage, durable delivery/retention and Compliance review remain pending. See `docs/specs/telemetry-event-capture/inventory-audit-and-close.md`; earlier version/coverage notes are historical.
