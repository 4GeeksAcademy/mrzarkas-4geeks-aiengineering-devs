import { compileContract } from './validation.js';
import { createContexts } from './context.js';
import { boundedFetch, receiverURL, recoverable, retryDelay, TransportTimeoutError } from './transport.js';

const encoder = new TextEncoder();
const bytes = value => encoder.encode(value).length;

// Only track is a capture interface. Other methods manage lifecycle, never accept events.
export function createTelemetryService({ contract, config, fetcher = globalThis.fetch.bind(globalThis),
  uuid = () => globalThis.crypto.randomUUID(), wallNow = () => Date.now(),
  monotonicNow = () => globalThis.performance.now(),
  timers = { set: (fn, ms) => setTimeout(fn, ms), clear: id => clearTimeout(id) },
  documentTarget = globalThis.document, windowTarget = globalThis.window } = {}) {
  const catalogue = compileContract(contract);
  const endpoint = config?.enabled === true ? receiverURL(config.endpoint, config.environment) : null;
  let manager = null, pending = [], flight = null, timer = null, generation = 0, destroyed = false;
  let lastView = null, observersCleanup = () => {}, captureContext = null;
  const counters = { rejected: 0, discarded: 0, received: 0, retries: 0, diagnosticRejected: 0, diagnosticDiscarded: 0, diagnosticReceived: 0 };
  const increment = (name, count = 1) => { counters[name] = Math.min(Number.MAX_SAFE_INTEGER, counters[name] + count); };
  const clearTimer = () => { if (timer !== null) timers.clear(timer); timer = null; };
  const identity = entry => entry.context.key;
  const schedule = () => {
    clearTimer();
    if (!pending.length || flight || destroyed) return;
    const due = [false, true].some(kind => pending.filter(entry => Boolean(entry.diagnostic) === kind).length >= 20) ? 0 : Math.max(0, pending[0].at + 10000 - monotonicNow());
    timer = timers.set(() => { timer = null; void flush(); }, due);
  };
  const finish = (batch, accepted, reason = 'unavailable') => {
    if (flight !== batch) return;
    increment(batch.diagnostic ? (accepted ? 'diagnosticReceived' : 'diagnosticDiscarded') : (accepted ? 'received' : 'discarded'), batch.entries.length);
    if (!accepted && !batch.diagnostic) diagnose('telemetry_delivery_failed', reason);
    flight = null; schedule();
  };
  async function attempt(batch, keepalive) {
    if (batch.generation !== generation || destroyed) return;
    let context = batch.context;
    if (context.expires - wallNow() <= 30000) {
      context = await manager?.renew(context);
      if (batch.generation !== generation || destroyed) return;
      if (!context) { finish(batch, false); return; }
      batch.context = context;
    }
    let response, canRetry = true, reason = 'unavailable';
    try {
      response = await boundedFetch(fetcher, endpoint, { method: 'POST', keepalive, signal: batch.controller.signal,
        headers: { Authorization: `Bearer ${context.bearer}`, 'X-Telemetry-Context': context.contextToken,
          'Content-Type': 'application/json' }, body: batch.body }, timers);
      if (batch.generation !== generation || destroyed) return;
      if (response.status === 200) {
        const receipt = await response.json();
        if (receipt && Object.keys(receipt).length === 1 && receipt.received === batch.entries.length && Number.isInteger(receipt.received)) {
          finish(batch, true); return;
        }
      } else canRetry = recoverable(response.status);
    } catch (error) { if (error instanceof TransportTimeoutError) reason = 'timeout'; }
    if (batch.generation !== generation || destroyed) return;
    if (batch.diagnostic || !canRetry || batch.retry >= 3) { finish(batch, false, reason); return; }
    increment('retries'); batch.retry++;
    batch.retryTimer = timers.set(() => { batch.retryTimer = null; void attempt(batch, false); },
      retryDelay(response, batch.retry, wallNow()));
  }
  async function flush(keepalive = false) {
    if (flight || !pending.length || destroyed || !manager) return;
    clearTimer();
    const first = pending.find(entry => entry.diagnostic) ?? pending[0], entries = [];
    let remaining = [], batchBytes = bytes('{"events":[]}');
    for (const entry of pending) {
      if (Boolean(entry.diagnostic) === Boolean(first.diagnostic) && identity(entry) === identity(first) && entries.length < 20 && batchBytes + entry.size + 1 <= 48 * 1024) {
        entries.push(entry); batchBytes += entry.size + 1;
      } else remaining.push(entry);
    }
    pending = remaining;
    const batch = { entries, context: first.context, body: JSON.stringify({ events: entries.map(entry => entry.event) }),
      generation, diagnostic: Boolean(first.diagnostic), retry: 0, retryTimer: null, controller: new AbortController() };
    flight = batch;
    await attempt(batch, keepalive);
  }
  function budget(diagnostic) {
    return [...pending, ...(flight?.entries ?? [])].filter(entry => Boolean(entry.diagnostic) === diagnostic);
  }
  function diagnose(eventType, reasonCode) {
    try {
      const context = manager?.general();
      if (!endpoint || destroyed || !context) { increment('diagnosticRejected'); return; }
      const event = { eventId: uuid(), timestamp: new Date(wallNow()).toISOString(),
        sessionId: context.sessionId, userId: context.userId, event_type: eventType,
        schemaVersion: catalogue.version, requestId: null,
        properties: { jurisdiction: null, environment: config.environment, producer: 'frontend', reasonCode } };
      const body = JSON.stringify(event), size = bytes(body), entries = budget(true);
      if (!catalogue.validDiagnostic(event) || size > 2048 || entries.length >= 20
        || entries.reduce((sum, entry) => sum + entry.size, 0) + size > 32 * 1024) {
        increment('diagnosticRejected'); return;
      }
      pending.push({ event: JSON.parse(body), context, at: monotonicNow(), size, diagnostic: true });
      schedule();
    } catch { increment('diagnosticRejected'); }
  }
  const reject = (reason = 'schema') => {
    increment('rejected');
    diagnose(reason === 'queue_full' ? 'telemetry_delivery_failed' : 'telemetry_contract_rejected', reason);
  };
  function track(eventType, properties) {
    try {
      const context = captureContext ?? manager?.current();
      if (!endpoint || !context || context.expires <= wallNow() || destroyed) { increment('rejected'); return; }
      // Reject NaN/non-JSON values before serialization can turn them into null.
      const value = { eventId: uuid(), timestamp: new Date(wallNow()).toISOString(),
        sessionId: context.sessionId, userId: context.userId, event_type: eventType,
        schemaVersion: catalogue.version, requestId: null, properties };
      if (!catalogue.validEvent(value)) { reject(); return; }
      const serialized = JSON.stringify(value), size = bytes(serialized);
      if (size > 2048) { reject(); return; }
      const entries = budget(false);
      if (entries.length >= 180 || entries.reduce((sum, entry) => sum + entry.size, 0) + size > 224 * 1024) {
        reject('queue_full'); return;
      }
      pending.push({ event: JSON.parse(serialized), context, at: monotonicNow(), size });
      schedule();
    } catch { reject(); }
  }
  const onVisibility = () => { if (documentTarget?.visibilityState === 'hidden') queueMicrotask(() => { void flush(true); }); };
  const onPageHide = () => { void flush(true); };
  documentTarget?.addEventListener('visibilitychange', onVisibility);
  windowTarget?.addEventListener('pagehide', onPageHide);
  function disconnect() {
    generation++; clearTimer(); flight?.controller.abort();
    if (flight?.retryTimer !== null && flight?.retryTimer !== undefined) timers.clear(flight.retryTimer);
    increment('discarded', budget(false).length);
    increment('diagnosticDiscarded', budget(true).length);
    pending = []; flight = null; manager?.stop(); manager = null; lastView = null; observersCleanup();
  }
  return {
    track,
    async connect(apiUrl, bearer) {
      disconnect();
      if (!endpoint || destroyed || typeof bearer !== 'string' || !bearer || bearer.length > 8192
        || !['development', 'test', 'production'].includes(config.environment)) return false;
      try { if (new URL(apiUrl).origin !== new URL(endpoint).origin) return false; } catch { return false; }
      const ownGeneration = generation;
      const ownManager = createContexts({ fetcher, timers, wallNow, endpoint, bearer,
        environment: config.environment, version: catalogue.version });
      manager = ownManager;
      const context = await ownManager.activate(null);
      if (ownGeneration !== generation || manager !== ownManager) return false;
      if (!context) { ownManager.stop(); manager = null; return false; }
      track('session_started', { jurisdiction: null, environment: config.environment, application: config.application });
      return true;
    },
    async activateClinic(clinicId) {
      const ownManager = manager;
      if (!ownManager) return false;
      const context = await ownManager.activate(clinicId);
      if (ownManager !== manager) return false;
      return Boolean(context);
    },
    navigate(view) {
      const context = manager?.current();
      if (!context) return;
      const key = `${context.key}|${view}`;
      if (key === lastView) return;
      const rejected = counters.rejected;
      track('navigation_viewed', { jurisdiction: context.jurisdiction, environment: config.environment, view });
      if (counters.rejected === rejected) lastView = key;
    },
    error(reasonCode = 'unexpected') {
      const context = manager?.current();
      if (context) track('application_error_observed', { jurisdiction: context.jurisdiction,
        environment: config.environment, component: 'backoffice', reasonCode });
    },
    timing(metric, value, view) {
      const context = manager?.general();
      if (context) {
        captureContext = context;
        try { track('frontend_timing_measured', { jurisdiction: null, environment: config.environment, metric, value, view }); }
        finally { captureContext = null; }
      }
    },
    setObserversCleanup(fn) { observersCleanup(); observersCleanup = fn; },
    disconnect() {
      const context = manager?.current();
      if (context) track('session_ended', { jurisdiction: context.jurisdiction, environment: config.environment, reasonCode: 'disconnect' });
      void flush(true);
      disconnect();
    },
    flush,
    destroy() {
      disconnect(); destroyed = true;
      documentTarget?.removeEventListener('visibilitychange', onVisibility);
      windowTarget?.removeEventListener('pagehide', onPageHide);
    },
    diagnostics: () => ({ ...counters, pending: pending.filter(entry => !entry.diagnostic).length, inFlight: flight?.diagnostic ? 0 : (flight?.entries.length ?? 0),
      diagnosticPending: pending.filter(entry => entry.diagnostic).length, diagnosticInFlight: flight?.diagnostic ? flight.entries.length : 0 })
  };
}
