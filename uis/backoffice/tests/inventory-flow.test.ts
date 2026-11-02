import { afterEach, describe, expect, it, vi } from "vitest";
import { createInventoryFlows } from "../src/lib/telemetry/inventory-flow";
const item = "00000000-0000-4000-8000-000000000001";
const clinic = "00000000-0000-4000-8000-000000000002";
const credential = () => ({ accepted: true, flowId: `ps_${"a".repeat(64)}`,
  flowToken: "synthetic-flow-credential", expiresAt: new Date(Date.now() + 60000).toISOString() });
const instances: ReturnType<typeof createInventoryFlows>[] = [];
afterEach(() => { instances.forEach(instance => instance.stop()); instances.length = 0; vi.useRealTimers(); });
function setup(enabled = true) {
  const requests: Array<Record<string, unknown>> = [];
  const fetcher = vi.fn(async (url: RequestInfo | URL, options?: RequestInit) => {
    if (String(url).endsWith("config.json")) return new Response(JSON.stringify({ enabled, endpoint: "http://localhost/telemetry/events", environment: "test" }));
    requests.push(JSON.parse(options!.body as string));
    return new Response(JSON.stringify(credential()));
  });
  const controller = new AbortController();
  const flows = createInventoryFlows("synthetic-bearer", controller.signal, fetcher as typeof fetch);
  instances.push(flows);
  return { requests, fetcher, controller, flows };
}
describe("inventory flow memory", () => {
  it("bounds memory to sixteen flows and aborts the evicted selection", async () => {
    const { requests, flows } = setup();
    for (let index = 1; index <= 17; index++)
      flows.select(`00000000-0000-4000-8000-${String(index).padStart(12, "0")}`, clinic);
    await vi.waitFor(() => expect(requests).toHaveLength(16));
    expect(requests.some(value => value.itemId === item)).toBe(false);
  });
  it("keeps lifecycle after credential expiry and coalesces activity", async () => {
    vi.useFakeTimers();
    const { requests, flows } = setup();
    flows.start(item, clinic, "", "inbound");
    await vi.advanceTimersByTimeAsync(1);
    expect(requests).toHaveLength(1);
    await vi.advanceTimersByTimeAsync(61000);
    flows.start(item, clinic, "", "inbound");
    await vi.advanceTimersByTimeAsync(1);
    expect(requests).toHaveLength(2);
    expect(requests[1]).not.toHaveProperty("flowToken");
    expect(requests[1].action).toBe("activity");
  });
  it("shares a selection credential with one start despite rapid typing", async () => {
    const { requests, flows } = setup();
    flows.select(item, clinic);
    flows.start(item, clinic, "", "inbound");
    flows.start(item, clinic, "", "inbound");
    await vi.waitFor(() => expect(requests).toHaveLength(2));
    expect(requests[0]).toEqual({ action: "product_selected", itemId: item, clinicId: clinic, direction: null });
    expect(requests[1]).toEqual({ action: "order_started", itemId: item, clinicId: clinic, direction: "inbound", flowToken: "synthetic-flow-credential" });
  });
  it("starts directly and creates a new flow on direction or lot changes", async () => {
    const { requests, flows } = setup();
    flows.start(item, clinic, "", "inbound");
    await vi.waitFor(() => expect(requests).toHaveLength(1));
    flows.start(item, clinic, "", "outbound");
    await vi.waitFor(() => expect(requests).toHaveLength(2));
    flows.start(item, clinic, "another-lot", "outbound");
    await vi.waitFor(() => expect(requests).toHaveLength(3));
    expect(requests.every(value => value.action === "order_started" && !("flowToken" in value))).toBe(true);
    expect(JSON.stringify(requests)).not.toContain("another-lot");
  });
  it("does not send when disabled, stopped or scoped IDs are invalid", async () => {
    const disabled = setup(false);
    disabled.flows.select(item, clinic);
    disabled.flows.start(item, clinic, "", "inbound");
    const active = setup();
    active.flows.select("invalid", clinic);
    active.controller.abort();
    active.flows.start(item, clinic, "", "inbound");
    await new Promise(resolve => setTimeout(resolve, 10));
    expect(disabled.requests).toHaveLength(0);
    expect(active.requests).toHaveLength(0);
  });
  it("ignores a late selection after reset and does not leak its token", async () => {
    let release!: (value: Response) => void;
    const requests: Array<Record<string, unknown>> = [];
    const fetcher = vi.fn(async (url: RequestInfo | URL, options?: RequestInit) => {
      if (String(url).endsWith("config.json")) return new Response(JSON.stringify({ enabled: true, endpoint: "http://localhost/telemetry/events", environment: "test" }));
      requests.push(JSON.parse(options!.body as string));
      if (requests.length === 1) return await new Promise<Response>(resolve => { release = resolve; });
      return new Response(JSON.stringify(credential()));
    });
    const flows = createInventoryFlows("synthetic", new AbortController().signal, fetcher as typeof fetch);
    instances.push(flows);
    flows.select(item, clinic);
    await vi.waitFor(() => expect(requests).toHaveLength(1));
    flows.reset(item, clinic);
    flows.start(item, clinic, "", "outbound");
    release(new Response(JSON.stringify(credential())));
    await vi.waitFor(() => expect(requests).toHaveLength(2));
    expect(requests[1]).not.toHaveProperty("flowToken");
  });
  it("contains telemetry failures without retries or business errors", async () => {
    const calls: string[] = [];
    const fetcher = vi.fn(async (url: RequestInfo | URL) => {
      calls.push(String(url));
      if (String(url).endsWith("config.json")) return new Response(JSON.stringify({ enabled: true, endpoint: "http://localhost/telemetry/events", environment: "test" }));
      throw new Error("Synthetic unavailable");
    });
    const flows = createInventoryFlows("synthetic", new AbortController().signal, fetcher as typeof fetch);
    instances.push(flows);
    expect(() => flows.start(item, clinic, "", "inbound")).not.toThrow();
    await vi.waitFor(() => expect(calls).toHaveLength(2));
    flows.start(item, clinic, "", "inbound");
    expect(calls).toHaveLength(2);
  });
});

it("binds confirmed operations to the tracked flow and sends no form data", async () => {
  const { requests, flows } = setup();
  flows.start(item, clinic, "", "inbound");
  await vi.waitFor(() => expect(requests).toHaveLength(1));
  expect(flows.binding(item,clinic)).toBe(`ps_${"a".repeat(64)}`);
  flows.confirmation(item,clinic);
  flows.confirmation(item,clinic);
  await vi.waitFor(() => expect(requests).toHaveLength(2));
  expect(requests[1]).toEqual({ action: "confirmation", itemId: item, clinicId: clinic, flowId: `ps_${"a".repeat(64)}` });
  flows.reset(item,clinic);
  expect(flows.binding(item,clinic)).toBeUndefined();
});
