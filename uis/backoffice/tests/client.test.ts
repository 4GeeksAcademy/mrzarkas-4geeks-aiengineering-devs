import { describe, it, expect, vi } from "vitest";
import { request, ApiError } from "@/lib/api/client";
describe("API transport", () => {
  it("uses private same-origin transport without persisting credentials", async () => {
    const fetcher = vi.fn().mockResolvedValue(Response.json({ items: [] }));
    vi.stubGlobal("fetch", fetcher);
    await request("/inventory/items", "synthetic-only");
    expect(fetcher).toHaveBeenCalledWith(
      "/next/api-core/inventory/items",
      expect.objectContaining({
        cache: "no-store",
        redirect: "error",
        headers: { Authorization: "Bearer synthetic-only" },
      }),
    );
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
  });
  it.each([401, 403, 404, 409, 422])(
    "classifies %s as a rejected operation",
    async (status) => {
      vi.stubGlobal(
        "fetch",
        vi
          .fn()
          .mockResolvedValue(
            Response.json({ detail: "Do not log this free text" }, { status }),
          ),
      );
      const onUnauthorized = vi.fn();
      try {
        await request("/incidents", "test", {
          method: "POST",
          body: { title: "Synthetic" },
          onUnauthorized,
        });
        throw new Error("expected rejection");
      } catch (e) {
        expect(e).toBeInstanceOf(ApiError);
        expect((e as ApiError).status).toBe(status);
        expect((e as ApiError).uncertain).toBe(false);
        expect((e as Error).message).not.toContain("free text");
      }
      expect(onUnauthorized).toHaveBeenCalledTimes(status === 401 ? 1 : 0);
    },
  );
  it.each(["network", "503", "malformed-success"])(
    "does not retry uncertain writes: %s",
    async (kind) => {
      const fetcher = vi.fn();
      if (kind === "network")
        fetcher.mockRejectedValue(new TypeError("Synthetic disconnect"));
      else if (kind === "503")
        fetcher.mockResolvedValue(
          Response.json({ detail: "unavailable" }, { status: 503 }),
        );
      else
        fetcher.mockResolvedValue(
          new Response("invalid-json", { status: 201 }),
        );
      vi.stubGlobal("fetch", fetcher);
      await expect(
        request("/inventory/movements", "test", {
          method: "POST",
          body: { quantity: 1 },
        }),
      ).rejects.toMatchObject({ uncertain: true });
      expect(fetcher).toHaveBeenCalledTimes(1);
    },
  );
  it("associates validation fields without echoing rejected input", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          Response.json(
            {
              detail: [
                {
                  loc: ["body", "title"],
                  msg: "secret text",
                  input: "synthetic-sensitive",
                },
              ],
            },
            { status: 422 },
          ),
        ),
    );
    await expect(
      request("/incidents", "test", { method: "POST", body: {} }),
    ).rejects.toMatchObject({
      fields: { title: "El valor no cumple el contrato de la API." },
    });
  });
});
