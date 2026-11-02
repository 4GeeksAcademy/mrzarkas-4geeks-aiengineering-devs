import test from 'node:test';
import assert from 'node:assert/strict';
import { observeVitals } from '../vitals.js';
import { createContexts } from '../context.js';
import { boundedFetch } from '../transport.js';

function vitalsFixture(count = 0) {
  const calls = [], observers = new Map(), document = new EventTarget();
  const performance = { now: () => 100, interactionCount: count };
  class Observer {
    static supportedEntryTypes = ['largest-contentful-paint', 'layout-shift', 'event'];
    constructor(callback) { this.callback = callback; }
    observe(options) { observers.set(options.type, this); }
    disconnect() { this.disconnected = true; }
    takeRecords() { return []; }
    emit(entries) { this.callback({ getEntries: () => entries }); }
  }
  const cleanup = observeVitals({ timing: (...args) => calls.push(args) }, 'incidents', { performance, Observer, document });
  const hidden = () => { document.visibilityState = 'hidden'; document.dispatchEvent(new Event('visibilitychange')); };
  return { calls, observers, document, performance, cleanup, hidden };
}

test('LCP and CLS use numeric fields only, CLS session windows exclude recent input and prior connection', () => {
  const { calls, observers, cleanup, hidden } = vitalsFixture();
  observers.get('largest-contentful-paint').emit([{ startTime: 700, url: 'synthetic-private', element: {} }]);
  observers.get('layout-shift').emit([{ startTime: 50, value: 9 }, { startTime: 200, value: 9, hadRecentInput: true },
    { startTime: 300, value: 0.1 }, { startTime: 500, value: 0.2 }, { startTime: 2000, value: 0.1 }]);
  hidden(); assert.equal(calls.length, 2); assert.deepEqual(calls[0], ['lcp_ms', 700, 'incidents']);
  assert.ok(Math.abs(calls[1][1] - 0.3) < 0.00001); assert.equal(calls[1][0], 'cls');
  assert.equal(JSON.stringify(calls).includes('private'), false);
  hidden(); assert.equal(calls.length, 2); cleanup(); assert.ok([...observers.values()].every(item => item.disconnected));
});

test('INP groups interaction entries and selects one outlier per 50 interactions', () => {
  const { calls, observers, performance, hidden } = vitalsFixture(10);
  observers.get('event').emit([{ interactionId: 1, startTime: 200, duration: 400 },
    { interactionId: 1, startTime: 250, duration: 500 }, { interactionId: 2, startTime: 300, duration: 100 },
    { interactionId: 0, startTime: 400, duration: 999 }]);
  performance.interactionCount = 60; hidden(); assert.deepEqual(calls, [['inp_ms',100,'incidents']]);
});

test('missing observers or interactionCount does not fabricate measurements', () => {
  assert.equal(typeof observeVitals({}, 'incidents', { Observer: null }), 'function');
  const fixture = vitalsFixture(undefined); fixture.performance.interactionCount = undefined;
  fixture.hidden(); assert.equal(fixture.calls.length, 0); fixture.cleanup();
});

test('invalid clinic activation never leaves a general fallback and stale context results cannot activate', async () => {
  const pending = [];
  const timers = { set: () => 1, clear() {} };
  const manager = createContexts({ fetcher: () => new Promise(resolve => pending.push(resolve)), timers,
    wallNow: () => Date.parse('2026-11-01T10:00:00Z'), endpoint:'http://localhost:8000/telemetry/events',
    environment:'test',bearer:'synthetic',version:'1.3.0' });
  const activation = manager.activate(null);
  assert.equal(await manager.activate('not-a-clinic'), null);
  pending[0]({ ok:true, json:async () => ({ contextToken:'synthetic', sessionId:'00000000-0000-4000-8000-000000000001',
    userId:'ps_'+'a'.repeat(64),jurisdiction:null,schemaVersion:'1.3.0',expiresAt:'2026-11-01T10:05:00Z' }) });
  assert.equal(await activation, null); assert.equal(manager.current(), null); manager.stop();
});

test('bounded transport links cancellation and clears timeout without leaking rejected promises', async () => {
  let cleared = false;
  const controller = new AbortController();
  const promise = boundedFetch((url, options) => new Promise((resolve, reject) => {
    options.signal.addEventListener('abort', () => reject(new Error('cancelled')), { once:true });
  }), 'http://synthetic.invalid', { signal:controller.signal }, {set:()=>1,clear:()=>cleared=true});
  controller.abort(); await assert.rejects(promise); assert.equal(cleared,true);
});
