"use client";
import { useState } from "react";
import { useQuery } from "@/hooks/use-query";
import { useSession } from "@/lib/auth/session";
import { canReadAudit, isInventory } from "@/lib/auth/presentation";
import type { Schema } from "@/lib/api/types";
import {
  Button,
  DataTable,
  ErrorState,
  Input,
  LoadingState,
  PageHeader,
  Select,
  Alert,
} from "@/components/ui";
const resources = [
  ["jurisdictions", "Jurisdicciones"],
  ["clinics", "Clínicas"],
  ["affected-systems", "Sistemas"],
  ["responsible-areas", "Áreas responsables"],
];
export function ManagementRead({
  kind,
}: {
  kind: "catalogs" | "reference-data" | "audit";
}) {
  const { session } = useSession();
  const [resource, setResource] = useState("jurisdictions");
  const [filter, setFilter] = useState("");
  const allowed =
    !!session &&
    !isInventory(session.claims) &&
    session.claims.role !== "direction" &&
    (kind !== "audit" || canReadAudit(session.claims));
  const [path, setPath] = useState<string | null>(
    kind === "catalogs" ? "/management/catalogs" : null,
  );
  const catalogs = useQuery<Schema<"CatalogListResponse">>(
    allowed && kind === "catalogs" ? path : null,
  );
  const references = useQuery<Schema<"ReferenceValueListResponse">>(
    allowed && kind === "reference-data" ? path : null,
  );
  const audit = useQuery<Schema<"ManagementAuditEventListResponse">>(
    allowed && kind === "audit" ? path : null,
  );
  const query =
    kind === "catalogs" ? catalogs : kind === "audit" ? audit : references;
  return (
    <>
      <PageHeader
        title={
          kind === "catalogs"
            ? "Catálogos"
            : kind === "audit"
              ? "Auditoría Management"
              : "Maestros"
        }
      />
      {!allowed ? (
        <Alert error>
          Tu perfil no dispone de esta consulta. La API mantiene la autoridad de
          acceso.
        </Alert>
      ) : (
        <section className="panel">
          {kind === "reference-data" && (
            <form
              className="filters"
              onSubmit={(e) => {
                e.preventDefault();
                setPath(`/management/reference-data/${resource}`);
                references.refresh();
              }}
            >
              <Select
                label="Recurso"
                value={resource}
                onChange={(e) => {
                  setResource(e.target.value);
                  setPath(null);
                }}
              >
                {resources.map(([v, l]) => (
                  <option key={v} value={v}>
                    {l}
                  </option>
                ))}
              </Select>
              <Button type="submit">Consultar</Button>
            </form>
          )}
          {kind === "audit" && (
            <form
              className="filters"
              onSubmit={(e) => {
                e.preventDefault();
                setPath(
                  `/management/audit-events?limit=50${filter ? `&resource_type=${encodeURIComponent(filter)}` : ""}`,
                );
                audit.refresh();
              }}
            >
              <Input
                label="Tipo de recurso"
                maxLength={100}
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              />
              <Button type="submit">Consultar eventos</Button>
            </form>
          )}
          {query.loading && <LoadingState />}
          {query.error && (
            <ErrorState error={query.error} retry={query.refresh} />
          )}
          {kind === "catalogs" && catalogs.data && (
            <>
              <Alert>Catálogos cargados: {catalogs.data.total}.</Alert>
              <DataTable
                rows={catalogs.data.items}
                rowKey={(r) => r.id}
                label="Resultados de catálogos"
                columns={[
                  { label: "catalog_name", cell: (r) => r.catalog_name },
                  { label: "version", cell: (r) => r.version },
                  { label: "is_active", cell: (r) => String(r.is_active) },
                ]}
              />
            </>
          )}
          {kind === "reference-data" && references.data && (
            <DataTable
              rows={references.data.items}
              rowKey={(r) => r.id}
              label="Resultados de maestros"
              columns={[
                { label: "key", cell: (r) => r.key },
                { label: "label", cell: (r) => r.label },
                {
                  label: "jurisdiction_id",
                  cell: (r) => r.jurisdiction_id ?? "",
                },
                { label: "is_active", cell: (r) => String(r.is_active) },
              ]}
            />
          )}{" "}
          {kind === "audit" && audit.data && (
            <DataTable
              rows={audit.data.items}
              rowKey={(r) => r.id}
              label="Resultados de auditoría"
              columns={[
                { label: "occurred_at", cell: (r) => r.occurred_at },
                { label: "resource_type", cell: (r) => r.resource_type },
                { label: "action", cell: (r) => r.action },
                { label: "actor_id", cell: (r) => r.actor_id },
                { label: "reason", cell: (r) => r.reason ?? "" },
              ]}
            />
          )}{" "}
          {!path && <p>Sin cargar. Selecciona los criterios y consulta.</p>}
        </section>
      )}
    </>
  );
}
