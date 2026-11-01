import { boundedFetch } from './transport.js';
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const pseudonym = /^ps_[0-9a-f]{64}$/;

export function createContexts({ fetcher, timers, wallNow, endpoint, environment, bearer, version }) {
  const contexts = new Map(), controller = new AbortController();
  let generation = 0, active = null, stopped = false, refreshTimer = null;
  const cancelRefresh = () => { if (refreshTimer !== null) timers.clear(refreshTimer); refreshTimer = null; };
  const scheduleRefresh = (context, retry = false) => {
    cancelRefresh();
    refreshTimer = timers.set(async () => {
      refreshTimer = null;
      const candidate = await request(context.clinicId, context.expires > wallNow() ? context : undefined);
      if (stopped || active?.key !== context.key) return;
      if (candidate) { contexts.set(context.clinicId, candidate); active = candidate; scheduleRefresh(candidate); }
      else if (context.expires > wallNow()) scheduleRefresh(context, true);
      else active = null;
    }, retry ? 10000 : Math.max(1000, context.expires - wallNow() - 30000));
  };
  const decode = (value, clinicId) => {
    if (!value || Object.keys(value).sort().join(',') !== 'contextToken,expiresAt,jurisdiction,schemaVersion,sessionId,userId'
      || typeof value.contextToken !== 'string' || value.contextToken.length > 4096
      || !uuid.test(value.sessionId) || !pseudonym.test(value.userId) || value.schemaVersion !== version
      || ![null, 'US', 'UK'].includes(value.jurisdiction) || (clinicId === null) !== (value.jurisdiction === null)
      || !Number.isFinite(Date.parse(value.expiresAt)) || Date.parse(value.expiresAt) <= wallNow()) return null;
    return Object.freeze({ ...value, clinicId, environment, bearer, endpoint,
      expires: Date.parse(value.expiresAt), key: `${value.sessionId}|${clinicId ?? 'general'}|${value.userId}` });
  };
  async function request(clinicId, previous) {
    try {
      const response = await boundedFetch(fetcher, endpoint.replace(/\/events$/, '/context'), {
        method: 'POST', signal: controller.signal, headers: { Authorization: `Bearer ${bearer}`, 'Content-Type': 'application/json',
          ...(previous ? { 'X-Telemetry-Context': previous.contextToken } : {}) }, body: JSON.stringify({ clinicId })
      }, timers);
      if (!response.ok) return null;
      return decode(await response.json(), clinicId);
    } catch { return null; }
  }
  return {
    current: () => active,
    general: () => { const context = contexts.get(null); return context?.expires > wallNow() ? context : null; },
    async activate(clinicId = null) {
      const ownGeneration = ++generation;
      cancelRefresh();
      active = null; // failed clinic resolution must never leave a general fallback active
      if (stopped || (clinicId !== null && !uuid.test(clinicId))) return null;
      let candidate = contexts.get(clinicId);
      if (!candidate || candidate.expires - wallNow() <= 30000) {
        candidate = await request(clinicId, candidate?.expires > wallNow() ? candidate : undefined);
      }
      if (stopped || generation !== ownGeneration || !candidate) return null;
      if (!contexts.has(clinicId) && contexts.size >= 16) contexts.delete(contexts.keys().next().value);
      contexts.set(clinicId, candidate); active = candidate; scheduleRefresh(candidate); return candidate;
    },
    async renew(context) {
      if (stopped || context.expires <= wallNow()) return null;
      const candidate = await request(context.clinicId, context);
      if (!candidate || stopped || candidate.key !== context.key) return null;
      contexts.set(context.clinicId, candidate);
      if (active?.key === context.key) { active = candidate; scheduleRefresh(candidate); }
      return candidate;
    },
    stop() { cancelRefresh(); controller.abort(); stopped = true; generation++; active = null; contexts.clear(); }
  };
}
