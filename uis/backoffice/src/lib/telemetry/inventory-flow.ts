type Direction = "inbound" | "outbound";
type Credential = { accepted: boolean; flowId: string; flowToken: string; expiresAt: string };
type Entry = { controller: AbortController; pending: Promise<Credential | null>; started: string | null;
  flowId: string | null; lastActivity: number; lifecyclePending: boolean; expires: number; timer: ReturnType<typeof setTimeout> | null };
export type InventoryFlows = {
  select: (item: string, clinic: string) => void;
  start: (item: string, clinic: string, lot: string, direction: Direction) => void;
  confirmation: (item: string, clinic: string) => void;
  binding: (item: string, clinic: string) => string | undefined;
  reset: (item: string, clinic: string) => void;
  stop: () => void;
};
const identity = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const pseudonym = /^ps_[0-9a-f]{64}$/;
export function createInventoryFlows(
  token: string,
  signal: AbortSignal,
  fetcher: typeof fetch = fetch,
): InventoryFlows {
  const entries = new Map<string, Entry>();
  const controller = new AbortController();
  const combined = AbortSignal.any([signal, controller.signal]);
  let stopped = false;
  const enabled = (async () => {
    try {
      const response = await fetcher("/next/telemetry/config.json", {
        cache: "no-store", redirect: "error", signal: AbortSignal.any([combined, AbortSignal.timeout(5000)]),
      });
      if (!response.ok) return false;
      const value = await response.json();
      return Object.keys(value).sort().join(",") === "enabled,endpoint,environment" && value.enabled === true &&
        ["development", "test", "production"].includes(value.environment);
    } catch { return false; }
  })();
  const key = (item: string, clinic: string) => `${item}|${clinic}`;
  const reset = (item: string, clinic: string) => {
    const own = key(item, clinic);
    const entry = entries.get(own);
    entry?.controller.abort();
    if (entry?.timer) clearTimeout(entry.timer);
    entries.delete(own);
  };
  const valid = (item: string, clinic: string) => !stopped && !combined.aborted && identity.test(item) && identity.test(clinic);
  async function capture(entry: Entry, item: string, clinic: string, action: string,
    direction: Direction | null, previous: Credential | null = null): Promise<Credential | null> {
    try {
      if (!await enabled || !valid(item, clinic) || entry.controller.signal.aborted) return null;
      const response = await fetcher("/next/api-core/telemetry/inventory-flow", {
        method: "POST", cache: "no-store", redirect: "error",
        signal: AbortSignal.any([combined, entry.controller.signal, AbortSignal.timeout(5000)]),
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ action, itemId: item, clinicId: clinic, direction,
          ...(previous && Date.parse(previous.expiresAt) > Date.now() ? { flowToken: previous.flowToken } : {}) }),
      });
      if (!response.ok || combined.aborted || entry.controller.signal.aborted) return null;
      const value = await response.json();
      if (Object.keys(value).sort().join(",") !== "accepted,expiresAt,flowId,flowToken" ||
          typeof value.accepted !== "boolean" || !pseudonym.test(value.flowId) ||
          typeof value.flowToken !== "string" || value.flowToken.length > 4096 ||
          !Number.isFinite(Date.parse(value.expiresAt)) || Date.parse(value.expiresAt) <= Date.now()) return null;
      if (!value.accepted) return null;
      entry.flowId = value.flowId;
      entry.lastActivity = Date.now();
      entry.expires = Date.now() + 1800000;
      if (entry.timer) clearTimeout(entry.timer);
      entry.timer = setTimeout(() => { if (entries.get(key(item, clinic)) === entry) reset(item, clinic); }, entry.expires - Date.now());
      return value as Credential;
    } catch { return null; }
  }
  function entryFor(item: string, clinic: string) {
    if (entries.size >= 16) {
      const first = entries.keys().next().value;
      if (first) { const old = entries.get(first); old?.controller.abort(); if (old?.timer) clearTimeout(old.timer); entries.delete(first); }
    }
    const entry: Entry = { controller: new AbortController(), pending: Promise.resolve(null), started: null,
      flowId: null, lastActivity: Date.now(), lifecyclePending: false, expires: Date.now() + 1800000, timer: null };
    entries.set(key(item, clinic), entry);
    entry.timer = setTimeout(() => { if (entries.get(key(item, clinic)) === entry) reset(item, clinic); }, 1800000);
    return entry;
  }
  function activity(item: string, clinic: string, action: "activity" | "confirmation") {
    const entry = entries.get(key(item, clinic));
    if (!entry || !entry.started || !entry.flowId || entry.lifecyclePending || !valid(item, clinic)) return;
    if (action === "activity" && Date.now() - entry.lastActivity < 30000) return;
    entry.lastActivity = Date.now(); entry.lifecyclePending = true;
    void (async () => {
      try {
        if (!await enabled || !valid(item, clinic)) return;
        const response = await fetcher("/next/api-core/telemetry/inventory-flow", {
          method: "POST", cache: "no-store", redirect: "error",
          signal: AbortSignal.any([combined, entry.controller.signal, AbortSignal.timeout(5000)]),
          headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
          body: JSON.stringify({ action, itemId: item, clinicId: clinic, flowId: entry.flowId }),
        });
        if (response.ok && !entry.controller.signal.aborted && valid(item,clinic)) {
          entry.expires = Date.now() + 1800000;
          if (entry.timer) clearTimeout(entry.timer);
          entry.timer = setTimeout(() => { if (entries.get(key(item,clinic)) === entry) reset(item,clinic); },1800000);
        }
      } catch { /* Gesture capture never blocks an inventory operation. */ }
      finally { entry.lifecyclePending = false; }
    })();
  }
  const stop = () => {
    stopped = true; controller.abort();
    for (const entry of entries.values()) { entry.controller.abort(); if (entry.timer) clearTimeout(entry.timer); }
    entries.clear();
    signal.removeEventListener("abort", stop);
  };
  signal.addEventListener("abort", stop, { once: true });
  return {
    select(item, clinic) {
      if (!valid(item, clinic)) return;
      reset(item, clinic);
      const entry = entryFor(item, clinic);
      entry.pending = capture(entry, item, clinic, "product_selected", null);
    },
    start(item, clinic, lot, direction) {
      if (!valid(item, clinic)) return;
      const scope = `${lot}|${direction}`;
      let entry = entries.get(key(item, clinic));
      if (entry && entry.expires <= Date.now()) { reset(item, clinic); entry = undefined; }
      if (entry?.started === scope) { activity(item, clinic, "activity"); return; }
      if (entry?.started) { reset(item, clinic); entry = undefined; }
      entry ??= entryFor(item, clinic);
      entry.started = scope;
      const own = entry;
      own.pending = own.pending.then(previous => capture(own, item, clinic, "order_started", direction, previous));
    },
    confirmation(item,clinic) { activity(item,clinic,"confirmation"); },
    binding(item,clinic) { const entry=entries.get(key(item,clinic)); return valid(item,clinic) && entry?.started ? entry.flowId ?? undefined : undefined; },
    reset, stop,
  };
}
