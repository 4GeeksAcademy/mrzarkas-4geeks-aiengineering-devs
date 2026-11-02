"use client";
import { useQuery } from "@/hooks/use-query";
import { useSession } from "@/lib/auth/session";
import { isInventory } from "@/lib/auth/presentation";
import type { Schema } from "@/lib/api/types";
import { Alert, ErrorState, LoadingState, PageHeader } from "@/components/ui";
export function Summary() {
  const { session } = useSession();
  const allowed = !!session && !isInventory(session.claims);
  const query = useQuery<Schema<"OpenIncidentsBySeverityResponse">[]>(
    allowed ? "/incidents/metrics/open-by-severity" : null,
  );
  return (
    <>
      <PageHeader title="Incidencias abiertas por severidad" />
      {!allowed ? (
        <Alert error>Tu perfil no dispone del resumen de incidencias.</Alert>
      ) : (
        <section className="panel" aria-busy={query.loading}>
          {query.loading && <LoadingState />}
          {query.error && (
            <ErrorState error={query.error} retry={query.refresh} />
          )}
          <div className="metrics-grid">
            {query.data?.map((r) => (
              <article key={r.severity_value_id} className="metric-card">
                <h2>{r.severity_label}</h2>
                <p className="metric-count">{r.open_incident_count}</p>
              </article>
            ))}
          </div>
          <p className="notice">
            La API calcula los estados abiertos y aplica el ámbito autorizado.
          </p>
        </section>
      )}
    </>
  );
}
