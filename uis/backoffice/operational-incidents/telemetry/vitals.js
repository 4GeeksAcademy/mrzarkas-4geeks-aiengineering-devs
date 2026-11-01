// Standards-based document LCP/CLS and INP where Event Timing + interactionCount exist.
// Raw entries (including DOM nodes/URLs) never leave the observer callback.
export function observeVitals(service, view, { performance = globalThis.performance,
  Observer = globalThis.PerformanceObserver, document = globalThis.document } = {}) {
  if (!Observer || !document || !performance) return () => {};
  const observers = [];
  let lcp = null, cls = 0, windowSum = 0, windowStart = 0, lastShift = -Infinity;
  let observedLcp = false, observedCls = false, lastLcpSent = null, lastClsSent = null, lastInpSent = null;
  const interactions = new Map();
  const start = performance.now();
  const initialInteractions = performance.interactionCount;
  const observe = (type, handler, options = {}) => {
    if (!Observer.supportedEntryTypes?.includes(type)) return;
    try {
      const observer = new Observer(list => handler(list.getEntries()));
      observer.observe({ type, buffered: true, ...options }); observers.push({ observer, handler });
    } catch { /* Browser support is optional; no new library or fabricated metric. */ }
  };
  observe('largest-contentful-paint', entries => {
    for (const entry of entries) { lcp = entry.startTime; observedLcp = true; }
  });
  observe('layout-shift', entries => {
    for (const entry of entries) {
      if (entry.startTime < start || entry.hadRecentInput) continue;
      observedCls = true;
      if (entry.startTime - lastShift < 1000 && entry.startTime - windowStart < 5000) windowSum += entry.value;
      else { windowStart = entry.startTime; windowSum = entry.value; }
      lastShift = entry.startTime; cls = Math.max(cls, windowSum);
    }
  });
  if (Number.isFinite(initialInteractions)) observe('event', entries => {
    for (const entry of entries) {
      if (!entry.interactionId || entry.startTime < start) continue;
      interactions.set(entry.interactionId, Math.max(interactions.get(entry.interactionId) ?? 0, entry.duration));
      if (interactions.size > 200) {
        const smallest = [...interactions].reduce((a, b) => a[1] < b[1] ? a : b);
        interactions.delete(smallest[0]);
      }
    }
  }, { durationThreshold: 16 });
  const publish = () => {
    for (const { observer, handler } of observers) {
      try { const entries = observer.takeRecords?.() ?? []; if (entries.length) handler(entries); } catch {}
    }
    if (observedLcp && lcp !== lastLcpSent) { service.timing('lcp_ms', lcp, view); lastLcpSent = lcp; }
    if (observedCls && cls !== lastClsSent) { service.timing('cls', cls, view); lastClsSent = cls; }
    const count = performance.interactionCount - initialInteractions;
    if (interactions.size && Number.isFinite(count) && count > 0 && Math.floor(count / 50) < 200) {
      const largest = [...interactions.values()].sort((a, b) => b - a);
      const inp = largest[Math.min(largest.length - 1, Math.floor(count / 50))];
      if (inp !== lastInpSent) { service.timing('inp_ms', inp, view); lastInpSent = inp; }
    }
  };
  const onHidden = () => { if (document.visibilityState === 'hidden') publish(); };
  document.addEventListener('visibilitychange', onHidden);
  return () => { document.removeEventListener('visibilitychange', onHidden); observers.forEach(({ observer }) => observer.disconnect()); };
}
