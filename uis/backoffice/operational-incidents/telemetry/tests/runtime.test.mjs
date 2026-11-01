import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { bootstrapTelemetry } from '../runtime.js';
const contract = JSON.parse(fs.readFileSync(new URL('../event-contract.json', import.meta.url)));
const uuid = '00000000-0000-4000-8000-000000000001';

test('bootstrap failure returns a no-op and global errors never export message/stack/URL', async () => {
  const originals = {fetch:globalThis.fetch,document:globalThis.document,window:globalThis.window,crypto:globalThis.crypto};
  const calls = [];
  globalThis.document = new EventTarget(); globalThis.window = new EventTarget();
  globalThis.crypto = {randomUUID:()=>uuid};
  globalThis.fetch = async () => { throw new Error('synthetic'); };
  const disabled = await bootstrapTelemetry('incidents'); assert.equal(await disabled.connect('x','y'),false);
  globalThis.fetch = async (url, init) => {
    const address = String(url);
    const json = data => ({ok:true,status:200,json:async()=>data});
    if (address.endsWith('/config.json')) return json({enabled:true,endpoint:'http://localhost:8000/telemetry/events',environment:'test'});
    if (address.endsWith('/event-contract.json')) return json(contract);
    if (address.endsWith('/context')) return json({contextToken:'synthetic',sessionId:uuid,userId:'ps_'+'a'.repeat(64),
      jurisdiction:null,schemaVersion:'1.2.0',expiresAt:new Date(Date.now()+300000).toISOString()});
    calls.push(JSON.parse(init.body)); return json({received:calls.at(-1).events.length});
  };
  const service = await bootstrapTelemetry('incidents');
  assert.equal(await service.connect('http://localhost:8000','synthetic'),true);
  const error = new Event('error'); error.message = 'synthetic-private-message'; error.stack = 'synthetic-private-stack';
  globalThis.window.dispatchEvent(error);
  const rejection = new Event('unhandledrejection'); rejection.reason = {secret:'synthetic-private'};
  globalThis.window.dispatchEvent(rejection);
  await service.flush();
  assert.equal(calls[0].events.filter(event=>event.event_type==='application_error_observed').length,2);
  assert.equal(JSON.stringify(calls).includes('private'),false);
  service.destroy();
  for (const [key,value] of Object.entries(originals)) { if(value===undefined) delete globalThis[key]; else globalThis[key]=value; }
});
