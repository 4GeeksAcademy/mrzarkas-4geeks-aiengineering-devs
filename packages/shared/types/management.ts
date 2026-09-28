/** Public Management API contracts. Generated behaviour is documented by
 * FastAPI's /openapi.json; these types give the backoffice a stable source
 * for the currently published snake_case payloads. */

export type UUID = string;

export interface ManagementCatalog {
  id: UUID;
  catalog_name: string;
  version: number;
  is_active: boolean;
}

export interface ManagementCatalogValue {
  id: UUID;
  key: string;
  label: string;
  description: string | null;
  is_active: boolean;
  is_open: boolean | null;
  sort_order: number;
  effective_from: string;
  effective_to: string | null;
}

export interface ReferenceValue {
  id: UUID;
  key: string;
  label: string;
  is_active: boolean;
  jurisdiction_id: UUID | null;
}

export interface ManagementAuditEvent {
  id: UUID;
  resource_type: string;
  resource_id: UUID;
  action: string;
  actor_id: UUID;
  before_data: Record<string, unknown> | null;
  after_data: Record<string, unknown> | null;
  reason: string | null;
  correlation_id: UUID | null;
  occurred_at: string;
}

export interface Paginated<T> {
  items: T[];
  total: number;
}
