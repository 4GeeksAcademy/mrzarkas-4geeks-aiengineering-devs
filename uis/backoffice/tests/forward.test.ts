import { beforeEach, describe, it, expect, vi } from "vitest";
import { allowedRoute, forward } from "@/lib/api/forward";
const id = "00000000-0000-4000-8000-000000000001";
beforeEach(() => {
  vi.stubEnv("APP_ENVIRONMENT", "test");
  vi.stubEnv("BACKEND_URL", "http://api.internal:8000");
});
const req = (path: string, method = "GET", body?: string) =>
  new Request(`http://localhost:3100/next/api-core${path}`, {
    method,
    headers: { Authorization: "Bearer synthetic-only" },
    body,
  });
describe("bounded forwarding", () => {
  it.each([
    ["auth", "tokens"],
    ["inventory", "..", "items"],
    ["incidents", "bad-uuid"],
    ["management", "arbitrary"],
    ["http:", "evil"],
  ])("rejects unknown or unsafe path %j", async (...parts) => {
    const fetcher = vi.fn();
    expect(
      (await forward(req("/bad"), parts as string[], fetcher)).status,
    ).toBe(404);
    expect(fetcher).not.toHaveBeenCalled();
  });
  it("allows exactly the reviewed operations", () => {
    expect(allowedRoute(["telemetry", "inventory-flow"], "POST")).toBe("/telemetry/inventory-flow");
    expect(allowedRoute(["telemetry", "inventory-flow"], "GET")).toBeNull();
    expect(allowedRoute(["inventory", "items", id, "stock"], "GET")).toBe(
      "/inventory/items/{item_id}/stock",
    );
    expect(
      allowedRoute(["management", "reference-data", "clinics"], "POST"),
    ).toBeNull();
    expect(
      allowedRoute(["incidents", id, "assignments"], "POST"),
    ).not.toBeNull();
  });
  it("fails closed outside synthetic dev/test", async () => {
    vi.stubEnv("APP_ENVIRONMENT", "production");
    expect(
      (await forward(req("/inventory/items"), ["inventory", "items"], vi.fn()))
        .status,
    ).toBe(503);
  });
  it("requires Bearer before calling upstream", async () => {
    const fetcher = vi.fn();
    expect(
      (
        await forward(
          new Request("http://localhost/"),
          ["inventory", "items"],
          fetcher,
        )
      ).status,
    ).toBe(401);
    expect(fetcher).not.toHaveBeenCalled();
  });
  it("forwards method/body/filter but not cookies, and returns only private JSON headers", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValue(
        Response.json(
          { items: [] },
          { headers: { "Set-Cookie": "synthetic=1" } },
        ),
      );
    const response = await forward(
      req(`/inventory/items?offset=50&limit=50`),
      ["inventory", "items"],
      fetcher,
    );
    const [url, options] = fetcher.mock.calls[0];
    expect(url.href).toBe(
      "http://api.internal:8000/inventory/items?offset=50&limit=50",
    );
    expect(options.redirect).toBe("error");
    expect(options.headers).not.toHaveProperty("Cookie");
    expect(response.headers.get("cache-control")).toBe("private, no-store");
    expect(response.headers.get("set-cookie")).toBeNull();
  });
  it("rejects excessive request bodies before upstream", async () => {
    const fetcher = vi.fn();
    expect(
      (
        await forward(
          req("/inventory/items", "POST", "x".repeat(65537)),
          ["inventory", "items"],
          fetcher,
        )
      ).status,
    ).toBe(413);
    expect(fetcher).not.toHaveBeenCalled();
  });
  it("does not follow redirects or expose upstream failure text", async () => {
    const fetcher = vi
      .fn()
      .mockRejectedValue(new Error("synthetic backend address details"));
    const response = await forward(
      req("/inventory/items"),
      ["inventory", "items"],
      fetcher,
    );
    expect(response.status).toBe(503);
    expect(await response.text()).not.toContain("address");
  });
});

it("forwards only a bounded flow binding on the movement POST", async () => {
  for (const [path, flow, expected] of [
    ["/inventory/movements", `ps_${"a".repeat(64)}`, true],
    ["/inventory/movements", "invalid", false],
    ["/inventory/items", `ps_${"a".repeat(64)}`, false],
  ] as const) {
    const fetcher = vi.fn(async () => Response.json({ result: "accepted" }));
    const request = req(path, "POST", "{}");
    request.headers.set("X-Inventory-Flow-Id", flow);
    await forward(request, path.slice(1).split("/"), fetcher);
    const options = fetcher.mock.calls[0] as unknown as [URL, RequestInit];
    expect(new Headers(options[1].headers).has("X-Inventory-Flow-Id")).toBe(expected);
  }
});

it("allows only POST for the reviewed reconciliation route", () => {
  const parts = ["inventory", "items", id, "clinics", id, "reconciliation"];
  expect(allowedRoute(parts, "POST")).toBe("/inventory/items/{item_id}/clinics/{clinic_id}/reconciliation");
  expect(allowedRoute(parts, "GET")).toBeNull();
  expect(allowedRoute(parts, "PATCH")).toBeNull();
});
