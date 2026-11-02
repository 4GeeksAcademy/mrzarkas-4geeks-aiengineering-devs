# Clinic inventory

Synthetic development prototype in the existing central API (`backend/`). The
inventory decisions were approved in the working session on 2026-11-02. The
older inventory specifications still describe a draft and `services/central-api/`;
Memory Bank is outside the authorized edit scope and has not been rewritten.
No UI, purchases, inter-clinic transfers, expiration tracking, EHR integration,
real inventory registry or production activation is included.

## Approved behavior

- Stock belongs to an item and clinic; optional lot balances remain independent.
  Regions are countries, using the existing Clinic → Jurisdiction reference.
- Required article attributes: title, unique product code and base unit. Code,
  base unit and lot mode are immutable. Title and presentation may be edited.
- Configure a positive integer reorder point for every item/clinic before any
  movement. An unconfigured clinic/item is not stocked and reads return 409.
  Configuration creates a zero-balance inventory position, never an opening balance.
- Quantities are integer base units. Optional labeled presentations have a positive
  integer equivalence (e.g. three synthetic blisters of ten units = thirty units).
  Every movement preserves its unit and presentation equivalence.
- Initial stock is an `in` movement. `out` subtracts its converted quantity.
  `adjust` requires a nonnegative physical `counted_quantity` in base units and a
  reason. For lot-managed items, counts concern the selected lot.
- Stock is always `SUM(delta)`. No stock column, article balance input, set-stock
  endpoint, stored balance cache or independent authoritative projection exists.
- Corrections insert one compensation referencing the original movement and require
  a reason. Compensations cannot themselves be compensated; corrected originals
  cannot be compensated twice. Replacement movements are separate operations.
- Negative item/clinic/lot balances are rejected. Every write that can affect an
  item locks its stable article row before aggregation/insertion. PostgreSQL's
  default READ COMMITTED isolation is required; do not override it with REPEATABLE
  READ without redesigning the locking/snapshot strategy. This intentionally also
  serializes writes to the same item in different clinics. No movement-row lock
  is relied upon, including when the stock history is empty.
- Article deactivation requires zero total stock and retains history. Inactive
  items reject writes; historical stock and movement reads remain available for
  authorized active clinics. There is no physical deletion or reactivation API.
- Under-reorder means clinic total `< reorder_point`, including zero; equality
  does not activate it. Lot-filtered stock reports the clinic-wide reorder flag.
- Lists use `offset` (default 0) and `limit` (default 50, maximum 100). History is
  chronological with UUID tie-breaking. Reorder filters before pagination, then
  rechecks results; concurrent writes can shorten a returned page. Regional
  reads are bounded but are not a single historical snapshot across all clinics.

## Identity and permissions

Use existing Bearer authentication. New roles have inventory permissions only:

| Role | Access |
| --- | --- |
| `inventoryAdmin` | Read/manage catalog and lots; deactivate zero-stock items. No movements or clinical stock reads. |
| `inventoryOperator` | Read assigned clinics; create entries/exits; read history. |
| `inventoryManager` | Operator access plus physical counts, compensations and reorder configuration. |
| `inventoryRegional` | Read stock, reorder and histories in assigned countries. No writes. |
| `inventoryAuditor` | Regional read access plus mutation audit. No writes. |

The existing roles gain no inventory permissions. The existing development-only
`POST /auth/tokens` accepts optional `clinic_ids` and `jurisdiction_ids` UUID
arrays, included in the signed JWT. Clinical operators/managers use clinic scope;
regional supervisors/auditors use country scope. Omitted scope authorizes no
clinical data. Scopes from request bodies never authorize an operation. Token
issuance remains unavailable in staging/production, and no real actors are seeded.

This is still self-issued development identity, not a production access-assignment
system. Claire Whitfield's simulated project approval HC-INV-APPROVAL-2026-11-02
(2026-11-02) covers roles, clinic/country scope, audit data and 24-month retention.
It approves the fictitious project scenario, not real production or legal compliance.

## Routes

All paths below are under `/inventory`; OpenAPI describes exact DTOs and errors.

| Operation | Route |
| --- | --- |
| Create/list articles | `POST/GET /items` |
| Read/edit article | `GET/PATCH /items/{item_id}` |
| Deactivate (reason required) | `POST /items/{item_id}/deactivation` |
| Configure mandatory reorder point | `POST /items/{item_id}/clinics/{clinic_id}/configuration` |
| Create/list lots | `POST/GET /items/{item_id}/lots` |
| Register movement | `POST /movements` |
| Compensate original (reason required) | `POST /movements/{movement_id}/correction` |
| Read clinic stock (optional lot) | `GET /items/{item_id}/stock?clinic_id=...` |
| Read history | `GET /items/{item_id}/movements?clinic_id=...` |
| Read authorized regional/clinical stock | `GET /stock` |
| Read authorized reorder needs | `GET /reorder` |
| Read authorized access denials | `GET /access-denials` |
| Read mutation audit | `GET /items/{item_id}/audit?clinic_id=...` |

Errors: 401 missing/invalid identity, 403 denied capability/scope, 404 missing
reference, 409 state/stock/uniqueness conflict, 422 invalid inputs, and 503 when mandatory
denial evidence cannot be persisted. Unknown input
fields, including stock, are rejected. Mutations commit before returning and
rollback fully on failure. Actor and UTC timestamps originate on the server.
PostgreSQL triggers reject UPDATE/DELETE of inventory movements and audit rows.
Audit snapshots and historical reasons are redacted on read; database records
remain intact. Text must never contain PHI, secrets or actual patient identifiers.
No business telemetry producer is enabled by this module.

## Migration and tests

Revisions: `0010_inventory` creates inventory tables/triggers, followed by
`0011_inventory_audit_policy` adding historical country, accepted outcomes and an
append-only denial register. Historical rows lacking country retain null values;
the migration never guesses their original country from today's clinic. Existing
migrations, environment configuration and local operational databases are untouched.
Downgrade drops inventory history: it requires explicit authorization and a backup;
validation may only downgrade a disposable synthetic database.

From `backend/`, with an explicitly isolated PostgreSQL test connection:

```sh
uv run --no-sync alembic upgrade head
uv run --no-sync pytest tests/test_inventory.py tests/test_inventory_audit_policy.py tests/test_auth.py -q
```

Set `INVENTORY_TEST_DATABASE_URL` to a disposable database whose name starts with
`inventory_validation`; the inventory integration tests refuse other names.
`DATABASE_URL` controls the standard Alembic/API test database. Never point either
at shared, production or real-data databases. HTTP inventory tests roll back an
outer transaction; concurrency tests commit synthetic records only in the
explicitly disposable database. The concurrency test checks competing exits,
empty history, atomic rejections and append-only protection.

For regression, use the documented backend test suite with synthetic catalogs
and reference seeds. Some older telemetry tests require a dedicated database
named `telemetry_validation`, fixed-US synthetic telemetry settings, and a test
connection pool that does not reuse connections across their separate asyncio
loops. These are test-runner settings, not deployment changes.

Validation on 2026-11-02: Python 3.12 with locked backend requirements; 21 inventory/policy
tests passed on fresh PostgreSQL, then 415 tests passed without skips in the full
synthetic regression. Installation from empty schema, upgrade from 0009, repeated
upgrade, disposable downgrade/re-upgrade and inventory ORM/schema comparison passed.
The regression used a temporary NullPool adapter preserving connection codecs for
legacy tests with multiple event loops; production pooling was not modified.
The global Alembic metadata check also identified pre-existing Compliance/history
index/FK discrepancies outside inventory; those were not silently corrected.
The local Podman storage error and broken virtualenv were bypassed using a temporary
Python/PostgreSQL test environment; no operational database was migrated.

## Historical country and denial audit

New movements and clinic-specific mutation events snapshot both the server-resolved
jurisdiction UUID and its technical key. Clinic writes lock the clinic before the
item, so a concurrent country update cannot reclassify the movement during commit.
Catalog-wide events have no geographic target and retain null country/clinic.
`result=accepted` records committed business changes. `resulting_quantity` is the
output-only sum of previous quantity and delta, not a separate balance source.

Regional history/audit reads filter by the recorded country, including when a clinic
later moves countries. Current stock remains governed by its current clinic scope.
Old unclassified clinical events are excluded from regional history until a separate
approved historical-data review; they are never silently relabeled or deleted.

Authenticated inventory 403 denials are persisted after rolling back the attempted
operation, in a new transaction before returning 403. The record contains only actor,
fixed server operation, permission/scope reason code, outcome and validated resource
UUIDs/country. Missing or invalid credentials (401) do not invent a responsible actor.
Unknown references remain null; bodies, headers, tokens and free text are never saved.
If the required denial transaction fails, the operation stays denied and returns 503.

`GET /access-denials` requires inventory audit permission and filters by historical
country. Unclassified denials are visible only to an authorized auditor who is also
the recorded actor; no country-scoped auditor receives other unclassified events.
The denial register is append-only and uses the same 24-month retention policy.

## Retention and controlled disposition

Approval: HC-INV-APPROVAL-2026-11-02, simulated Claire Whitfield review. Retain movements,
adjustments, corrections, mutation audit and access-denial evidence for 24 calendar
months from each UTC event timestamp. `retention_until` is a derived output field;
February 29 clamps to February 28 in a non-leap target year. Reads remain restricted
by role and scope. No automatic deletion, expiry filter, purge worker, trigger bypass
or storage/archive dependency is enabled.

The controlled procedure after the deadline is:

1. Open an authorized retention review with the approval reference, reviewer/actor,
   UTC date, jurisdiction, proposed record identifiers and their calculated deadlines.
   Exclude records that have not reached 24 months.
2. Establish all movement, compensation and audit dependencies. Compare balances and
   historical reconstruction before any proposed disposition. Every movement still
   contributing to stock or required to reconstruct it must remain available.
3. Obtain Compliance and Technology authorization for the exact disposition plan,
   backup/restore evidence and access controls for any future archive. If preservation
   cannot be demonstrated, do not delete; return the conflict to Compliance for a
   recorded decision. Do not invent an extension or silently change the period.
4. Execute only a separately authorized and validated disposition mechanism; keep its
   actor/time, reviewed identifiers, decision, result and before/after balance and
   traceability checks in a controlled audit record. Existing append-only protection
   is not bypassed by this module.

Automatic purge and any executable archive/disposition mechanism remain deferred
for design and technical validation, as explicitly allowed by the approval. This
prototype performs retention calculations and access controls, not destructive
expiry actions. Before using it for data reaching expiry, that procedure must have
an approved executable mechanism. No independent stored opening balance may replace
the source movement history.

## Synthetic demonstration inventory

After migrations and reference-data seed, in development/test:

```bash
uv run python -m app.inventory.demo
```

Creates three SYN-INV products, one lot and six opening movements in dev-us-clinic-01/dev-uk-clinic-01. Repeated runs do not reset balances or thresholds. Conflicting reserved product definitions roll back the transaction. No real data or PHI.
