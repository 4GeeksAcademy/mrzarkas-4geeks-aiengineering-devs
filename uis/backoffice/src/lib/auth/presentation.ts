export const roles = [
  "admin",
  "technology",
  "compliance",
  "direction",
  "responsibleArea",
  "inventoryAdmin",
  "inventoryOperator",
  "inventoryManager",
  "inventoryRegional",
  "inventoryAuditor",
] as const;
export type Role = (typeof roles)[number];
export type Claims = {
  role: Role;
  area_id: string | null;
  clinic_ids: string[];
  jurisdiction_ids: string[];
};
// Presentation only: the API verifies the signature, expiry and every permission.
export function readClaims(token: string): Claims {
  try {
    const part = token.split(".")[1];
    if (!part) throw new Error();
    const value: unknown = JSON.parse(
      new TextDecoder().decode(
        Uint8Array.from(atob(part.replace(/-/g, "+").replace(/_/g, "/")), (c) =>
          c.charCodeAt(0),
        ),
      ),
    );
    if (!value || typeof value !== "object") throw new Error();
    const data = value as Record<string, unknown>;
    if (!roles.includes(data.role as Role)) throw new Error();
    const area = typeof data.area_id === "string" ? data.area_id : null;
    if (data.role === "responsibleArea" && !area) throw new Error();
    const strings = (v: unknown) =>
      Array.isArray(v)
        ? v.filter((x): x is string => typeof x === "string")
        : [];
    return {
      role: data.role as Role,
      area_id: area,
      clinic_ids: strings(data.clinic_ids),
      jurisdiction_ids: strings(data.jurisdiction_ids),
    };
  } catch {
    throw new Error("El JWT no contiene un rol y ámbito legibles.");
  }
}
export const isInventory = (c: Claims) => c.role.startsWith("inventory");
export const canCreateIncident = (c: Claims) =>
  ["admin", "technology", "responsibleArea"].includes(c.role);
export const canReadIncident = (c: Claims) =>
  ["admin", "technology", "compliance", "responsibleArea"].includes(c.role);
export const canEditIncident = (c: Claims, area: string) =>
  ["admin", "technology"].includes(c.role) ||
  (c.role === "responsibleArea" && c.area_id === area);
export const canReadAudit = (c: Claims) =>
  ["admin", "compliance"].includes(c.role);
export const canReadStock = (c: Claims) =>
  [
    "inventoryOperator",
    "inventoryManager",
    "inventoryRegional",
    "inventoryAuditor",
  ].includes(c.role);
export const transitionGraph: Record<string, readonly string[]> = {
  new: ["underAnalysis", "cancelled"],
  underAnalysis: ["assigned", "inResolution", "onHold", "cancelled"],
  assigned: ["inResolution", "onHold"],
  inResolution: ["resolved", "onHold"],
  resolved: ["closed", "reopened"],
  onHold: ["underAnalysis", "assigned", "cancelled"],
  reopened: ["underAnalysis"],
  closed: [],
  cancelled: [],
};
export function transitionTargets(c: Claims, area: string, current: string) {
  const targets = transitionGraph[current] ?? [];
  if (["admin", "technology"].includes(c.role)) return targets;
  if (c.role === "responsibleArea" && c.area_id === area)
    return targets.filter((x) => ["closed", "cancelled"].includes(x));
  return [];
}
