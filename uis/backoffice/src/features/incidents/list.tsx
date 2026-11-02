"use client";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@/hooks/use-query";
import { useSession } from "@/lib/auth/session";
import {
  canCreateIncident,
  canReadIncident,
  isInventory,
} from "@/lib/auth/presentation";
import type { Schema } from "@/lib/api/types";
import {
  Alert,
  Button,
  DataTable,
  ErrorState,
  LoadingState,
  PageHeader,
  Pagination,
  Select,
} from "@/components/ui";
import { useIncidentOptions } from "./options";
export function IncidentList() {
  const { session } = useSession();
  const router = useRouter();
  const search = useSearchParams();
  const options = useIncidentOptions();
  const allowed = !!session && !isInventory(session.claims);
  const offset = Math.max(0, Number(search.get("offset")) || 0);
  const params = new URLSearchParams({
    offset: String(offset),
    limit: "20",
    sort_by: search.get("sort_by") ?? "created_at",
    sort_direction: search.get("sort_direction") ?? "desc",
  });
  for (const key of [
    "status_value_id",
    "severity_value_id",
    "responsible_area_id",
  ]) {
    const value = search.get(key);
    if (
      value &&
      !(
        key === "responsible_area_id" &&
        session?.claims.role === "responsibleArea"
      )
    )
      params.set(key, value);
  }
  const query = useQuery<Schema<"IncidentListResponse">>(
    allowed ? `/incidents?${params}` : null,
  );
  function navigate(values: URLSearchParams) {
    router.push(`/incidents?${values}`);
  }
  return (
    <>
      <PageHeader title="Incidencias" />
      {!allowed ? (
        <Alert error>Tu perfil no dispone de incidencias.</Alert>
      ) : (
        <section className="panel">
          {session && canCreateIncident(session.claims) && (
            <Link href="/incidents/new" prefetch={false}>
              Nueva incidencia
            </Link>
          )}
          {session?.claims.role !== "direction" && (
            <form
              className="filters"
              key={search.toString()}
              onSubmit={(e) => {
                e.preventDefault();
                const fd = new FormData(e.currentTarget);
                const next = new URLSearchParams();
                for (const [key, value] of fd)
                  if (typeof value === "string" && value) next.set(key, value);
                navigate(next);
              }}
            >
              <Select
                label="Estado"
                name="status_value_id"
                defaultValue={params.get("status_value_id") ?? ""}
              >
                <option value="">Todos</option>
                {options.data.status.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.label}
                  </option>
                ))}
              </Select>
              <Select
                label="Severidad"
                name="severity_value_id"
                defaultValue={params.get("severity_value_id") ?? ""}
              >
                <option value="">Todas</option>
                {options.data.severity.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.label}
                  </option>
                ))}
              </Select>
              {session?.claims.role !== "responsibleArea" && (
                <Select
                  label="Área"
                  name="responsible_area_id"
                  defaultValue={params.get("responsible_area_id") ?? ""}
                >
                  <option value="">Todas</option>
                  {options.data.areas.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.label}
                    </option>
                  ))}
                </Select>
              )}
              <Select
                label="Ordenar por"
                name="sort_by"
                defaultValue={params.get("sort_by") ?? "created_at"}
              >
                {[
                  ["created_at", "Creación"],
                  ["updated_at", "Actualización"],
                  ["title", "Título"],
                  ["incident_identifier", "Identificador"],
                ].map(([v, l]) => (
                  <option key={v} value={v}>
                    {l}
                  </option>
                ))}
              </Select>
              <Select
                label="Dirección"
                name="sort_direction"
                defaultValue={params.get("sort_direction") ?? "desc"}
              >
                <option value="desc">Descendente</option>
                <option value="asc">Ascendente</option>
              </Select>
              <Button type="submit">Aplicar filtros</Button>
            </form>
          )}
          {options.error && (
            <ErrorState error={options.error} retry={options.refresh} />
          )}{" "}
          {query.loading && <LoadingState />}
          {query.error && (
            <ErrorState error={query.error} retry={query.refresh} />
          )}{" "}
          {query.data && (
            <>
              <Alert>{query.data.total} incidencias encontradas.</Alert>
              <DataTable
                rows={query.data.items}
                rowKey={(r) => r.id}
                label="Cola de incidencias"
                columns={[
                  {
                    label: "Identificador",
                    cell: (r) =>
                      session && canReadIncident(session.claims) ? (
                        <Link
                          href={`/incidents/${r.id}?queue=${encodeURIComponent(search.toString())}`}
                          prefetch={false}
                        >
                          {r.incident_identifier}
                        </Link>
                      ) : (
                        r.incident_identifier
                      ),
                  },
                  { label: "Título", cell: (r) => r.title },
                  {
                    label: "Estado",
                    cell: (r) => (
                      <span className="badge">
                        {options.label("status", r.status_value_id)}
                      </span>
                    ),
                  },
                  {
                    label: "Severidad",
                    cell: (r) => options.label("severity", r.severity_value_id),
                  },
                  {
                    label: "Clínica",
                    cell: (r) => options.label("clinics", r.clinic_id),
                  },
                  {
                    label: "Área",
                    cell: (r) => options.label("areas", r.responsible_area_id),
                  },
                ]}
              />
              <Pagination
                offset={offset}
                size={20}
                total={query.data.total}
                onChange={(n) => {
                  const next = new URLSearchParams(search);
                  next.set("offset", String(n));
                  navigate(next);
                }}
              />
            </>
          )}
        </section>
      )}
    </>
  );
}
