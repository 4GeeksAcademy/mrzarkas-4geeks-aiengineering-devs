// Profiles the actual React calculation function, not React commits or useMemo overhead.
import { performance } from 'node:perf_hooks';
import { chronology } from '../frontend/app/internal/incident-history/chronology.mjs';
const results = [];
for (const count of [20, 200, 2000]) {
  const status = Array.from({ length: count / 2 }, (_, i) => ({ id: `synthetic-${i}`, changed_at: new Date(Date.UTC(2026, 0, 1) + ((i * 17) % count) * 1000).toISOString() }));
  const assignment = Array.from({ length: count / 2 }, (_, i) => ({ id: `synthetic-${i}`, changed_at: new Date(Date.UTC(2026, 0, 1) + ((i * 31) % count) * 1000).toISOString() }));
  const samples = [];
  for (let i = 0; i < 220; i++) {
    const start = performance.now(); const value = chronology(status, assignment); const elapsed = performance.now() - start;
    if (value.length !== count) throw new Error('Count mismatch');
    if (i >= 20) samples.push(elapsed);
  }
  samples.sort((a, b) => a - b);
  results.push({ synthetic_events: count, p50_ms: samples[99], p95_ms: samples[189] });
}
console.log(JSON.stringify({ method: 'Actual chronology.mjs map/merge/sort, Node only, 20 warmup/200 samples, nearest rank. Synthetic scenarios, not observed history volumes; no React commit measurements.', runtime: process.version, results }, null, 2));
