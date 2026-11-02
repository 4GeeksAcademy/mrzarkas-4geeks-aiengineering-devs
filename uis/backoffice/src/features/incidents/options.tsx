"use client";
import { useQuery } from "@/hooks/use-query";
import { useSession } from "@/lib/auth/session";
import { isInventory } from "@/lib/auth/presentation";
import type { Catalog, Schema, Reference } from "@/lib/api/types";
export type Option = {
  id: string;
  label: string;
  key: string;
  jurisdiction_id?: string | null;
};
export function useIncidentOptions() {
  const { session } = useSession();
  const enabled =
    !!session &&
    !isInventory(session.claims) &&
    session.claims.role !== "direction";
  const status = useQuery<Catalog>(enabled ? "/catalogs/incidentStatus" : null);
  const severity = useQuery<Catalog>(enabled ? "/catalogs/severity" : null);
  const channel = useQuery<Catalog>(enabled ? "/catalogs/entryChannel" : null);
  const type = useQuery<Catalog>(enabled ? "/catalogs/incidentType" : null);
  const clinics = useQuery<Schema<"ReferenceValueListResponse">>(
    enabled ? "/management/reference-data/clinics?offset=0&limit=100" : null,
  );
  const jurisdictions = useQuery<Schema<"ReferenceValueListResponse">>(
    enabled
      ? "/management/reference-data/jurisdictions?offset=0&limit=100"
      : null,
  );
  const systems = useQuery<Schema<"ReferenceValueListResponse">>(
    enabled
      ? "/management/reference-data/affected-systems?offset=0&limit=100"
      : null,
  );
  const areas = useQuery<Schema<"ReferenceValueListResponse">>(
    enabled
      ? "/management/reference-data/responsible-areas?offset=0&limit=100"
      : null,
  );
  const queries = [
    status,
    severity,
    channel,
    type,
    clinics,
    jurisdictions,
    systems,
    areas,
  ];
  const refs = (v: Reference[] | undefined) => v ?? [];
  const data = {
    status: status.data?.values ?? [],
    severity: severity.data?.values ?? [],
    channel: channel.data?.values ?? [],
    type: type.data?.values ?? [],
    clinics: refs(clinics.data?.items),
    jurisdictions: refs(jurisdictions.data?.items),
    systems: refs(systems.data?.items),
    areas: refs(areas.data?.items),
  };
  function label(kind: keyof typeof data, id: string | null | undefined) {
    return data[kind].find((r) => r.id === id)?.label ?? id ?? "—";
  }
  return {
    data,
    label,
    loading: queries.some((q) => q.loading),
    error: queries.find((q) => q.error)?.error,
    refresh: () => queries.forEach((q) => q.refresh()),
  };
}
