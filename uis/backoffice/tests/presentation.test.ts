import { describe, it, expect } from "vitest";
import {
  roles,
  readClaims,
  canEditIncident,
  canReadIncident,
  canReadStock,
  canCreateIncident,
  transitionTargets,
  isInventory,
  type Claims,
} from "@/lib/auth/presentation";
const claim = (
  role: Claims["role"],
  area_id: string | null = "area",
): Claims => ({ role, area_id, clinic_ids: [], jurisdiction_ids: [] });
describe("presentation never grants additional domain capabilities", () => {
  it.each(roles)("%s stays in its own domain", (role) => {
    const c = claim(role);
    expect(isInventory(c)).toBe(role.startsWith("inventory"));
    if (isInventory(c)) {
      expect(canCreateIncident(c)).toBe(false);
      expect(canReadIncident(c)).toBe(false);
    }
  });
  it("direction has no detail or mutations", () => {
    expect(canReadIncident(claim("direction"))).toBe(false);
    expect(canEditIncident(claim("direction"), "area")).toBe(false);
  });
  it("responsibleArea can edit only own area and only close/cancel", () => {
    const c = claim("responsibleArea");
    expect(canEditIncident(c, "area")).toBe(true);
    expect(canEditIncident(c, "other")).toBe(false);
    expect(transitionTargets(c, "area", "new")).toEqual(["cancelled"]);
    expect(transitionTargets(c, "other", "new")).toEqual([]);
    expect(transitionTargets(c, "area", "resolved")).toEqual(["closed"]);
  });
  it("inventoryAdmin has no clinical stock, while operator/manager/region/auditor do", () => {
    expect(canReadStock(claim("inventoryAdmin"))).toBe(false);
    for (const r of [
      "inventoryOperator",
      "inventoryManager",
      "inventoryRegional",
      "inventoryAuditor",
    ] as const)
      expect(canReadStock(claim(r))).toBe(true);
  });
  it("rejects unknown roles and responsibleArea without area", () => {
    const token = (v: unknown) => `x.${btoa(JSON.stringify(v))}.x`;
    expect(() => readClaims(token({ role: "superuser" }))).toThrow();
    expect(() => readClaims(token({ role: "responsibleArea" }))).toThrow();
    expect(
      readClaims(
        token({
          role: "inventoryRegional",
          jurisdiction_ids: ["synthetic-country"],
        }),
      ).jurisdiction_ids,
    ).toEqual(["synthetic-country"]);
  });
});
