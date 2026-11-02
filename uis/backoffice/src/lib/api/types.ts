import type { components } from "./generated";
export type Schema<K extends keyof components["schemas"]> =
  components["schemas"][K];
export type Incident = Schema<"IncidentResponse">;
export type IncidentSummary = Schema<"IncidentListItem">;
export type Reference = Schema<"ReferenceValueListItem">;
export type Catalog = Schema<"CatalogResponse">;
export type Item = Schema<"ItemRead">;
export type Stock = Schema<"StockRead">;
