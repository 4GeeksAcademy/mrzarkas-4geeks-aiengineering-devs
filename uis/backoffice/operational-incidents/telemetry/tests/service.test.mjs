import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createTelemetryService } from '../telemetry-service.js';
import { compileContract } from '../validation.js';
import { receiverURL, retryDelay } from '../transport.js';

const contract = JSON.parse(fs.readFileSync(new URL('../event-contract.json', import.meta.url)));
const epoch = Date.parse('2026-11-01T10:00:00Z');
const settle = async () => { for (let i = 0; i < 20; i++) await Promise.resolve(); };
class Clock {
  time = 0; seq = 0; tasks = new Map();
  set = (fn, delay) => { const id = ++this.seq; this.tasks.set(id, { fn, at: this.time + delay }); return id; };
  clear = id => this.tasks.delete(id);
  async advance(ms) {
    const target = this.time + ms;
    for (;;) {
      const entry = [...this.tasks].filter(([, value]) => value.at <= target).sort((a, b) => a[1].at - b[1].at)[0];
      if (!entry) break;
      const [id, value] = entry; this.tasks.delete(id); this.time = value.at; value.fn(); await settle();
    }
    this.time = target; await settle();
  }
}
function response(status, data, retryAfter = null) {
  return { status, ok: status >= 200 && status < 300, json: async () => data,
    headers: { get: name => name === 'Retry-After' ? retryAfter : null } };
}
async function setup(options = {}) {
  const clock = new Clock(), calls = [], document = new EventTarget(), window = new EventTarget();
  document.visibilityState = 'visible';
  let id = 1, behaviour = options.behaviour;
  const fetcher = async (url, init) => {
    calls.push({ url, ...init, at: clock.time });
    if (url.endsWith('/context')) {
      const clinic = JSON.parse(init.body).clinicId;
      return response(200, { contextToken: 'synthetic-context', sessionId: '00000000-0000-4000-8000-000000000001',
        userId: 'ps_'+'a'.repeat(64), jurisdiction: clinic === null ? null : 'US', schemaVersion: '1.2.0',
        expiresAt: new Date(epoch + clock.time + 300000).toISOString() });
    }
    if (behaviour) return behaviour(url, init);
    return response(200, { received: JSON.parse(init.body).events.length });
  };
  const service = createTelemetryService({ contract, config: { enabled: true, endpoint: 'http://localhost:8000/telemetry/events',
    environment: 'test', application: 'incidents', ...options.config }, fetcher,
    wallNow: () => epoch + clock.time, monotonicNow: () => clock.time, timers: clock,
    uuid: () => `00000000-0000-4000-8000-${String(id++).padStart(12, '0')}`, documentTarget: document, windowTarget: window });
  if (options.connect !== false) {
    assert.equal(await service.connect('http://localhost:8000', 'synthetic-bearer'), true);
    // Discard setup's session event through an ACK before selecting transport behaviour.
    behaviour = null; await service.flush(); calls.length = 0; behaviour = options.behaviour;
  }
  const track = () => service.track('navigation_viewed', { jurisdiction: null, environment: 'test', view: 'management' });
  return { service, clock, calls, document, window, track, setBehaviour: fn => behaviour = fn };
}

test('track captures immutable envelope synchronously; unknown fields, NaN, secrets and cyclic objects fail closed', async () => {
  const { service, clock, calls } = await setup();
  const props = { jurisdiction: null, environment: 'test', view: 'management' };
  assert.equal(service.track('navigation_viewed', props), undefined); props.view = 'invalid';
  service.track('unknown', {});
  service.track('navigation_viewed', { jurisdiction: NaN, environment: 'test', view: 'management' });
  service.track('navigation_viewed', { jurisdiction: null, environment: 'test', view: 'management', email: 'synthetic@example.invalid' });
  const cyclic = {}; cyclic.self = cyclic; service.track('navigation_viewed', cyclic);
  assert.equal(service.diagnostics().pending, 1); assert.equal(service.diagnostics().rejected, 4);
  assert.equal(calls.length, 0); await clock.advance(10000);
  const value = calls.flatMap(call => JSON.parse(call.body).events).find(event => event.event_type === 'navigation_viewed');
  assert.deepEqual(Object.keys(value).sort(), ['eventId','timestamp','sessionId','userId','event_type','schemaVersion','requestId','properties'].sort());
  assert.equal(value.timestamp, '2026-11-01T10:00:00.000Z'); assert.equal(value.properties.view, 'management');
  assert.equal(value.requestId, null); service.destroy();
});

test('20 events send one batch; one event waits 10 seconds; later captures do not debounce deadline', async () => {
  const { service, track, clock, calls } = await setup();
  for (let i = 0; i < 19; i++) track(); await clock.advance(0); assert.equal(calls.length, 0);
  track(); await clock.advance(0); assert.equal(calls.length, 1); assert.equal(JSON.parse(calls[0].body).events.length, 20);
  track(); await clock.advance(9000); track(); await clock.advance(999); assert.equal(calls.length, 1);
  await clock.advance(1); assert.equal(calls.length, 2); assert.equal(JSON.parse(calls[1].body).events.length, 2);
  service.destroy();
});

test('events captured during HTTP flight survive without concurrent transport', async () => {
  const { service, track, clock, calls, setBehaviour } = await setup();
  let release;
  setBehaviour(() => new Promise(resolve => release = resolve));
  for (let i = 0; i < 20; i++) track(); await clock.advance(0);
  for (let i = 0; i < 20; i++) track(); await clock.advance(1000); assert.equal(calls.length, 1);
  setBehaviour(null); release(response(200, { received: 20 })); await settle(); await clock.advance(0);
  assert.equal(calls.length, 2); assert.equal(service.diagnostics().pending, 0);
  assert.equal(service.diagnostics().received, 41); service.destroy();
});

test('recoverable failure has 3 additional retries at 1/2/4 seconds and discards only flight', async () => {
  const { service, track, clock, calls, setBehaviour } = await setup({ behaviour: () => response(503, {}) });
  track(); await clock.advance(10000); track();
  await clock.advance(1000); await clock.advance(2000); await clock.advance(4000);
  assert.deepEqual(calls.map(call => call.at), [10000,11000,13000,17000]);
  assert.equal(new Set(calls.map(call => call.body)).size, 1);
  assert.equal(service.diagnostics().retries, 3); assert.equal(service.diagnostics().discarded, 1);
  assert.equal(service.diagnostics().pending, 1);
  setBehaviour(null); await clock.advance(3000); assert.equal(calls.filter(call => JSON.parse(call.body).events[0].event_type === 'navigation_viewed').length, 5);
  assert.equal(calls.filter(call => JSON.parse(call.body).events[0].event_type === 'telemetry_delivery_failed').length, 1); service.destroy();
});

for (const status of [400,401,403,404,405,413,415,422,501,505]) test(`permanent ${status} does not retry`, async () => {
  const { service, track, clock, calls } = await setup({ behaviour: () => response(status, {}) });
  track(); await clock.advance(17000); assert.equal(calls.length, 1); assert.equal(service.diagnostics().discarded, 1); service.destroy();
});

test('network failure and malformed ACK retry with managed promises', async () => {
  const { service, track, clock, calls } = await setup({ behaviour: () => { throw new Error('synthetic-sensitive'); } });
  track(); await clock.advance(17000); assert.equal(calls.length, 4); service.destroy();
  const other = await setup({ behaviour: () => response(200, { received: 2 }) });
  other.track(); await other.clock.advance(17000); assert.equal(other.calls.length, 4); other.service.destroy();
});

test('hidden flush uses fetch keepalive with Bearer and context; no duplicate flight', async () => {
  const { service, track, clock, calls, document, setBehaviour } = await setup();
  let release; setBehaviour(() => new Promise(resolve => release = resolve));
  track(); document.visibilityState = 'hidden'; document.dispatchEvent(new Event('visibilitychange')); await settle();
  assert.equal(calls.length, 1); assert.equal(calls[0].keepalive, true);
  assert.equal(calls[0].headers.Authorization, 'Bearer synthetic-bearer'); assert.ok(calls[0].headers['X-Telemetry-Context']);
  document.dispatchEvent(new Event('visibilitychange')); await settle(); assert.equal(calls.length, 1);
  release(response(200, { received: 1 })); await settle(); service.destroy();
  document.dispatchEvent(new Event('visibilitychange')); await clock.advance(10000); assert.equal(calls.length, 1);
});

test('global queue cap includes in-flight; invalid config or mismatched API origin does not export', async () => {
  const { service, track, clock, calls, setBehaviour } = await setup();
  setBehaviour(() => new Promise(() => {}));
  for (let i = 0; i < 20; i++) track(); await clock.advance(0);
  for (let i = 0; i < 181; i++) track();
  assert.equal(service.diagnostics().pending, 160); assert.equal(service.diagnostics().rejected, 21);
  assert.equal(service.diagnostics().diagnosticPending, 20); assert.equal(service.diagnostics().diagnosticRejected, 1); service.destroy();
  const other = await setup({ connect: false, config: { enabled: false } });
  assert.equal(await other.service.connect('http://localhost:8000','synthetic'), false);
  other.track(); assert.equal(other.calls.length, 0); other.service.destroy();
  const third = await setup({ connect: false });
  assert.equal(await third.service.connect('https://untrusted.example','synthetic'), false); assert.equal(third.calls.length, 0); third.service.destroy();
});

test('clinic changes partition queued batches; general and clinic never mix', async () => {
  const { service, track, clock, calls } = await setup();
  track();
  assert.equal(await service.activateClinic('00000000-0000-4000-8000-000000000002'), true);
  service.track('navigation_viewed', { jurisdiction: 'US', environment: 'test', view: 'incident_detail' });
  await clock.advance(10000);
  const batches = calls.filter(call => call.url.endsWith('/events')).map(call => JSON.parse(call.body).events);
  assert.equal(batches.length, 2);
  assert.equal(batches[0][0].properties.jurisdiction, null); assert.equal(batches[1][0].properties.jurisdiction, 'US'); service.destroy();
});

test('disconnect clears old queue and stale HTTP callbacks cannot alter new session', async () => {
  const { service, track, clock, calls, setBehaviour } = await setup();
  let release; setBehaviour(() => new Promise(resolve => release = resolve));
  for (let i = 0; i < 20; i++) track(); await clock.advance(0);
  service.disconnect(); assert.equal(service.diagnostics().pending, 0); assert.equal(service.diagnostics().inFlight, 0);
  setBehaviour(null); await service.connect('http://localhost:8000','synthetic-new');
  release(response(200, { received: 20 })); await settle();
  assert.equal(service.diagnostics().received, 1); assert.equal(service.diagnostics().pending, 1); service.destroy();
});

test('context renews before expiry without changing event metadata', async () => {
  const { service, clock, calls, track } = await setup();
  await clock.advance(270000);
  assert.equal(calls.filter(call => call.url.endsWith('/context')).length, 1);
  track(); await clock.advance(10000);
  assert.equal(JSON.parse(calls.at(-1).body).events[0].timestamp, '2026-11-01T10:04:30.000Z'); service.destroy();
});

test('receiver config and Retry-After are explicit and bounded', () => {
  assert.equal(receiverURL('http://u:p@host/telemetry/events','test'), null);
  assert.equal(receiverURL('http://host/telemetry/events','production'), null);
  assert.equal(retryDelay(response(429, {}, '99'), 1, epoch), 30000);
  assert.equal(retryDelay(response(503, {}, 'invalid'), 2, epoch), 2000);
});

test('packaged frontend contract equals the source', () => {
  const source = JSON.parse(fs.readFileSync(new URL('../../../../../docs/telemetry/event-schemas.json', import.meta.url)));
  assert.deepEqual(contract, source);
});

const uuidValue = '00000000-0000-4000-8000-000000000001';
function sample(schema) {
  if (schema.enum) return schema.enum[0];
  if ('const' in schema) return schema.const;
  if (schema.anyOf) return sample(schema.anyOf[0]);
  if (['integer','number'].includes(schema.type)) return schema.minimum ?? 0;
  if (schema.format === 'date-time') return '2026-11-01T10:00:00Z';
  if (schema.pattern?.includes('ps_')) return 'ps_'+'a'.repeat(64);
  return uuidValue;
}
const { validate } = await import('../validation.js');
for (const [name, definition] of Object.entries(contract.definitions).filter(([name]) => name !== 'envelope')) {
  test(`schema parity: ${name} positive/required/extra/nullable/date`, () => {
    const properties = definition.allOf[1].properties.properties;
    const value = { eventId:uuidValue,timestamp:'2026-11-01T10:00:00Z',sessionId:null,userId:null,
      event_type:name,schemaVersion:'1.2.0',requestId:null,
      properties:Object.fromEntries(Object.entries(properties.properties).map(([key, child]) => [key,sample(child)])) };
    assert.equal(validate(definition,value,contract),true);
    for (const key of properties.required) {
      const invalid = structuredClone(value); delete invalid.properties[key]; assert.equal(validate(definition,invalid,contract),false);
    }
    const invalid = structuredClone(value); invalid.properties.extra = 'synthetic'; assert.equal(validate(definition,invalid,contract),false);
    invalid.properties = value.properties; invalid.timestamp = '2026-02-30T10:00:00Z'; assert.equal(validate(definition,invalid,contract),false);
    value.properties.jurisdiction = null;
    assert.equal(validate(definition,value,contract),properties.properties.jurisdiction.enum.includes(null));
  });
}

test('nullable server types do not grant browser producer admission', () => {
  const catalogue = compileContract(contract);
  assert.equal(catalogue.version, '1.2.0');
  assert.equal(catalogue.general.size, 5);
  for (const name of ['authentication_succeeded','authentication_failed','authorization_denied',
    'api_request_completed','catalog_cache_observed','service_health_checked','data_integrity_checked',
    'telemetry_contract_rejected','telemetry_delivery_failed']) {
    const definition = contract.definitions[name];
    const properties = definition.allOf[1].properties.properties;
    const value = { eventId:uuidValue,timestamp:'2026-11-01T10:00:00Z',sessionId:null,userId:null,
      event_type:name,schemaVersion:'1.2.0',requestId:null,
      properties:Object.fromEntries(Object.entries(properties.properties).map(([key,child]) => [key,sample(child)])) };
    value.properties.jurisdiction = null;
    assert.equal(validate(definition,value,contract),true);
    assert.equal(catalogue.validEvent(value),false);
    assert.equal(catalogue.general.has(name),false);
  }
});


test('diagnostic schema rejection is reduced, authenticated general and internal only', async () => {
  const {service,clock,calls}=await setup();
  service.track('unknown',{token:'synthetic-sensitive',jurisdiction:'UK'});
  service.track('telemetry_delivery_failed',{jurisdiction:null,environment:'test',producer:'frontend',reasonCode:'unavailable'});
  assert.equal(service.diagnostics().diagnosticPending,2);
  await clock.advance(9999);assert.equal(calls.length,0);
  await clock.advance(1);const events=JSON.parse(calls[0].body).events;
  assert.equal(events.length,2);
  for(const event of events){
    assert.equal(event.event_type,'telemetry_contract_rejected');
    assert.deepEqual(event.properties,{jurisdiction:null,environment:'test',producer:'frontend',reasonCode:'schema'});
    assert.equal(event.userId,'ps_'+'a'.repeat(64));assert.equal(event.requestId,null);
  }
  assert.equal(calls[0].body.includes('sensitive'),false);service.destroy();
});

test('diagnostic invalid/full/failure never recurses and has no retries',async()=>{
  const {service,clock,calls}=await setup({behaviour:()=>response(503,{})});
  for(let i=0;i<21;i++)service.track('unknown',{});
  assert.equal(service.diagnostics().diagnosticPending,20);assert.equal(service.diagnostics().diagnosticRejected,1);
  await clock.advance(0);assert.equal(calls.length,1);assert.equal(JSON.parse(calls[0].body).events.length,20);
  await clock.advance(20000);assert.equal(calls.length,1);
  assert.equal(service.diagnostics().diagnosticDiscarded,20);assert.equal(service.diagnostics().retries,0);
  service.destroy();
});

test('terminal normal failures produce one unavailable diagnostic after three retries',async()=>{
  const {service,track,clock,calls,setBehaviour}=await setup({behaviour:()=>response(200,{received:999})});
  track();await clock.advance(17000);assert.equal(calls.length,4);
  assert.equal(new Set(calls.map(call=>call.body)).size,1);
  setBehaviour(null);await clock.advance(10000);
  const event=JSON.parse(calls[4].body).events[0];
  assert.equal(event.event_type,'telemetry_delivery_failed');assert.equal(event.properties.reasonCode,'unavailable');
  assert.equal(service.diagnostics().diagnosticReceived,1);service.destroy();
});

test('typed timeout yields timeout diagnostic while explicit disconnect does not',async()=>{
  const aborting=(_,init)=>new Promise((resolve,reject)=>init.signal.addEventListener('abort',()=>reject(new Error('synthetic-sensitive')),{once:true}));
  const {service,track,clock,calls,setBehaviour}=await setup({behaviour:aborting});
  track();await clock.advance(37000);assert.equal(calls.length,4);assert.equal(service.diagnostics().discarded,1);
  setBehaviour(null);await clock.advance(10000);
  assert.equal(JSON.parse(calls[4].body).events[0].properties.reasonCode,'timeout');
  assert.equal(calls[4].body.includes('sensitive'),false);service.destroy();
  const other=await setup({behaviour:aborting});other.track();void other.service.flush();await settle();
  other.service.destroy();await other.clock.advance(30000);
  assert.equal(other.service.diagnostics().diagnosticPending,0);assert.equal(other.service.diagnostics().diagnosticReceived,0);
});

test('reserved diagnostics wait behind normal flight without concurrent send and clear on identity change',async()=>{
  const {service,clock,calls,track,setBehaviour}=await setup();let release;
  setBehaviour(()=>new Promise(resolve=>release=resolve));
  for(let i=0;i<20;i++)track();await clock.advance(0);
  for(let i=0;i<20;i++)service.track('unknown',{});
  await clock.advance(10000);assert.equal(calls.length,1);assert.equal(service.diagnostics().diagnosticPending,20);
  setBehaviour(null);release(response(200,{received:20}));await settle();await clock.advance(0);
  assert.equal(calls.length,2);assert.equal(JSON.parse(calls[1].body).events[0].event_type,'telemetry_contract_rejected');
  service.track('unknown',{});service.destroy();await clock.advance(10000);
  assert.equal(service.diagnostics().diagnosticPending,0);assert.equal(service.diagnostics().diagnosticInFlight,0);
});

test('missing general context does not send or acquire context for diagnostics',async()=>{
  const {service,calls,clock}=await setup({connect:false});service.track('unknown',{});
  await clock.advance(20000);assert.equal(calls.length,0);assert.equal(service.diagnostics().diagnosticPending,0);service.destroy();
});
