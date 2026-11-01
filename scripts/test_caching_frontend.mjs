import assert from 'node:assert/strict';
import { chronology } from '../frontend/app/internal/incident-history/chronology.mjs';
import { POST } from '../frontend/app/api/incident-history/route.js';
const first = Object.freeze([{ id: 'a', changed_at: '2026-01-02T00:00:00Z' }]);
const second = Object.freeze([{ id: 'b', changed_at: '2026-01-01T00:00:00Z' }]);
assert.deepEqual(chronology(first, second).map(x => x.id), ['b', 'a']);
assert.equal(first[0].id, 'a');
assert.deepEqual(chronology([], []), []);
const call = (body, authorization) => POST(new Request('http://local/api/incident-history', { method: 'POST', headers: { 'Content-Type': 'application/json', ...(authorization ? { Authorization: authorization } : {}) }, body: JSON.stringify(body) }));
assert.equal((await call({})).status, 401);
assert.equal((await call({ incident: 'not-a-uuid' }, 'Bearer synthetic')).status, 422);
const original = globalThis.fetch;
try {
  let calls = 0;
  globalThis.fetch = async (url, options) => { calls++; assert.equal(options.cache, 'no-store'); assert.equal(options.headers.Authorization, 'Bearer synthetic'); return Response.json([], { status: calls === 2 ? 403 : 200 }); };
  const result = await call({ incident: '00000000-0000-0000-0000-000000000001' }, 'Bearer synthetic');
  assert.equal(result.status, 403); assert.equal(calls, 2);
  calls = 0;
  globalThis.fetch = async () => { calls++; return Response.json([]); };
  const ok = await call({ incident: '00000000-0000-0000-0000-000000000001' }, 'Bearer synthetic');
  assert.equal(ok.headers.get('cache-control'), 'private, no-store');
  assert.deepEqual(await ok.json(), { statusHistory: [], assignmentHistory: [] });
  globalThis.fetch = async () => { throw new Error('synthetic outage'); };
  assert.equal((await call({ incident: '00000000-0000-0000-0000-000000000001' }, 'Bearer synthetic')).status, 503);
} finally { globalThis.fetch = original; }
console.log('PASS chronology order/immutability/empty; private forwarding: 401, 422, 403, 200, 503 and no-store');
