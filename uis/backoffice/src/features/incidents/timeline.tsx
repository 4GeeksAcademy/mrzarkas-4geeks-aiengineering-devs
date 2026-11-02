"use client";
import { useMemo } from "react";
import type { Schema } from "@/lib/api/types";
export default function Timeline({
  status,
  assignments,
  label,
}: {
  status: Schema<"StatusHistoryResponse">[];
  assignments: Schema<"AssignmentHistoryResponse">[];
  label: (kind: "status" | "areas", id: string | null) => string;
}) {
  const events = useMemo(
    () =>
      [
        ...status.map((r) => ({
          id: r.id,
          at: r.changed_at,
          actor: r.changed_by,
          reason: r.reason,
          kind: "status" as const,
          from: r.from_status_value_id,
          to: r.to_status_value_id,
        })),
        ...assignments.map((r) => ({
          id: r.id,
          at: r.changed_at,
          actor: r.changed_by,
          reason: r.reason,
          kind: "areas" as const,
          from: r.from_responsible_area_id,
          to: r.to_responsible_area_id,
        })),
      ].sort((a, b) => Date.parse(a.at) - Date.parse(b.at)),
    [status, assignments],
  );
  if (!events.length) return <p>Sin eventos en el historial.</p>;
  return (
    <ol className="history-list">
      {events.map((r) => (
        <li key={`${r.kind}-${r.id}`}>
          <h3>
            {r.kind === "status" ? "Estado" : "Área"}: {label(r.kind, r.from)} →{" "}
            {label(r.kind, r.to)}
          </h3>
          <p>
            <time dateTime={r.at}>
              {new Date(r.at).toLocaleString("es-ES")}
            </time>{" "}
            · Autor: {r.actor}
          </p>
          {r.reason && <p>Motivo: {r.reason}</p>}
        </li>
      ))}
    </ol>
  );
}
