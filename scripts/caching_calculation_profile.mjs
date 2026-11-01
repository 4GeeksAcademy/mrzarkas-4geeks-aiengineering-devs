// Pure synthetic in-memory calculation profile; no DOM, DB, credentials or patient data.
// From repo root: node scripts/caching_calculation_profile.mjs
import { performance } from 'node:perf_hooks';
import os from 'node:os';

function chronology(statusHistory, assignmentHistory) {
  return [
    ...statusHistory.map(item => ({ kind: 'status', at: item.changed_at, actor: item.changed_by, reason: item.reason, from: item.from_status_value_id, to: item.to_status_value_id })),
    ...assignmentHistory.map(item => ({ kind: 'assignment', at: item.changed_at, actor: item.changed_by, reason: item.reason, from: item.from_responsible_area_id, to: item.to_responsible_area_id })),
  ].sort((a, b) => new Date(a.at) - new Date(b.at));
}
const results = [];
for (const count of [20, 200, 2000]) {
  const status = Array.from({ length: count / 2 }, (_, i) => ({ changed_at: new Date(Date.UTC(2026, 0, 1) + ((i * 17) % count) * 1000).toISOString() }));
  const assignment = Array.from({ length: count / 2 }, (_, i) => ({ changed_at: new Date(Date.UTC(2026, 0, 1) + ((i * 31) % count) * 1000).toISOString() }));
  const samples = [];
  for (let i = 0; i < 220; i++) {
    const start = performance.now();
    const result = chronology(status, assignment);
    const duration = performance.now() - start;
    if (result.length !== count) throw new Error('Incorrect event count');
    if (i >= 20) samples.push(duration);
  }
  samples.sort((a, b) => a - b);
  results.push({ synthetic_events: count, p50_ms: samples[Math.ceil(samples.length * .5) - 1], p95_ms: samples[Math.ceil(samples.length * .95) - 1] });
}
console.log(JSON.stringify({ method: 'Extracted map+sort from native renderDetail; Node calculation only, not browser/React profiling. Synthetic input, 20 warmup and 200 measured samples; nearest-rank percentiles. Counts are scenarios, not observed production volumes.', runtime: process.version, platform: process.platform, cpu: os.cpus()[0]?.model, results }, null, 2));
