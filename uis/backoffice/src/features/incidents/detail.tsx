"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@/hooks/use-query";
import { useMutation } from "@/hooks/use-mutation";
import { useSession } from "@/lib/auth/session";
import {
  canEditIncident,
  canReadIncident,
  transitionTargets,
} from "@/lib/auth/presentation";
import type { Incident, Schema } from "@/lib/api/types";
import {
  Alert,
  Button,
  ErrorState,
  Input,
  LoadingState,
  MutationState,
  PageHeader,
  Select,
  Textarea,
} from "@/components/ui";
import { useTelemetryClinic } from "@/lib/telemetry/provider";
import { useIncidentOptions } from "./options";
import { useUnsavedChanges } from "@/hooks/use-unsaved-changes";
const Timeline = dynamic(() => import("./timeline"), {
  loading: () => <LoadingState />,
  ssr: false,
});
export function IncidentDetail({ id }: { id: string }) {
  const { session } = useSession();
  const search = useSearchParams();
  const allowed = !!session && canReadIncident(session.claims);
  const base = `/incidents/${encodeURIComponent(id)}`;
  const query = useQuery<Incident>(allowed ? base : null);
  const status = useQuery<Schema<"StatusHistoryResponse">[]>(
    allowed ? `${base}/history` : null,
  );
  const assignments = useQuery<Schema<"AssignmentHistoryResponse">[]>(
    allowed ? `${base}/assignment-history` : null,
  );
  const options = useIncidentOptions();
  useTelemetryClinic(query.data?.clinic_id ?? null);
  const refresh = () => {
    query.refresh();
    status.refresh();
    assignments.refresh();
  };
  return (
    <>
      <PageHeader title="Detalle de incidencia" />
      <Link
        href={`/incidents${search.get("queue") ? `?${search.get("queue")}` : ""}`}
        prefetch={false}
      >
        Volver a incidencias
      </Link>
      {!allowed ? (
        <Alert error>Tu perfil no puede leer el detalle.</Alert>
      ) : (
        <>
          {query.loading && <LoadingState />}
          {query.error && (
            <ErrorState error={query.error} retry={refresh} />
          )}{" "}
          {query.data && (
            <>
              <section className="panel">
                <h2>{query.data.title}</h2>
                <p>{query.data.incident_identifier}</p>
                {search.get("created") === "1" && (
                  <Alert>
                    Incidencia creada. La API confirmó el resultado.
                  </Alert>
                )}
                <dl className="facts">
                  {(
                    [
                      ["Estado", "status", query.data.status_value_id],
                      ["Severidad", "severity", query.data.severity_value_id],
                      ["Clínica", "clinics", query.data.clinic_id],
                      [
                        "Jurisdicción",
                        "jurisdictions",
                        query.data.jurisdiction_id,
                      ],
                      ["Sistema", "systems", query.data.affected_system_id],
                      ["Área", "areas", query.data.responsible_area_id],
                      ["Canal", "channel", query.data.entry_channel_value_id],
                      ["Tipo", "type", query.data.incident_type_value_id],
                    ] as const
                  ).map(([name, kind, value]) => (
                    <div key={name}>
                      <dt>{name}</dt>
                      <dd>{options.label(kind, value)}</dd>
                    </div>
                  ))}
                </dl>
                <p>
                  Última actualización:{" "}
                  {new Date(query.data.updated_at).toLocaleString("es-ES")}
                </p>
              </section>
              {options.error && (
                <ErrorState error={options.error} retry={options.refresh} />
              )}
              <IncidentEditor incident={query.data} refresh={refresh} />
              <IncidentActions
                incident={query.data}
                options={options}
                refresh={refresh}
              />
              <section className="panel">
                <h2>Cronología</h2>
                {(status.loading || assignments.loading) && <LoadingState />}
                {status.error && (
                  <ErrorState error={status.error} retry={status.refresh} />
                )}{" "}
                {assignments.error && (
                  <ErrorState
                    error={assignments.error}
                    retry={assignments.refresh}
                  />
                )}{" "}
                {!status.loading && !assignments.loading && (
                  <Timeline
                    status={status.data ?? []}
                    assignments={assignments.data ?? []}
                    label={(kind, value) => options.label(kind, value)}
                  />
                )}
              </section>
            </>
          )}
        </>
      )}
    </>
  );
}
function IncidentEditor({
  incident,
  refresh,
}: {
  incident: Incident;
  refresh: () => void;
}) {
  const { session } = useSession();
  const m = useMutation();
  const draft = useUnsavedChanges();
  const [title, setTitle] = useState(incident.title);
  const [description, setDescription] = useState(incident.description);
  useEffect(() => {
    setTitle(incident.title);
    setDescription(incident.description);
  }, [incident]);
  if (
    !session ||
    !canEditIncident(session.claims, incident.responsible_area_id)
  )
    return (
      <section className="panel">
        <h2>Descripción</h2>
        <p>{incident.description}</p>
      </section>
    );
  return (
    <section className="panel">
      <h2>Editar incidencia</h2>
      <form
        onChange={draft.markDirty}
        onSubmit={async (e) => {
          e.preventDefault();
          if (!title.trim() || !description.trim()) return;
          const result = await m.mutate<Incident>(
            `/incidents/${incident.id}`,
            { title: title.trim(), description: description.trim() },
            "PATCH",
          );
          if (result) {
            draft.markClean();
            refresh();
          }
        }}
      >
        <fieldset disabled={m.pending || !!m.error?.uncertain}>
          <legend className="sr-only">Edición de título y descripción</legend>
          <Input
            label="Título"
            required
            maxLength={200}
            pattern=".*\S.*"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            error={m.error?.fields.title}
          />
          <Textarea
            label="Descripción"
            required
            maxLength={10000}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            error={m.error?.fields.description}
          />
          <p className="privacy-notice">
            Describe el impacto operativo. No incluyas datos de pacientes.
          </p>
          <Button type="submit" disabled={m.pending}>
            Guardar cambios
          </Button>
        </fieldset>
      </form>
      <MutationState mutation={m} verify={refresh} />
    </section>
  );
}
function IncidentActions({
  incident,
  options,
  refresh,
}: {
  incident: Incident;
  options: ReturnType<typeof useIncidentOptions>;
  refresh: () => void;
}) {
  const { session } = useSession();
  const transition = useMutation();
  const assignment = useMutation();
  const [target, setTarget] = useState("");
  const [reason, setReason] = useState("");
  const current =
    options.data.status.find((r) => r.id === incident.status_value_id)?.key ??
    "";
  const targets = session
    ? transitionTargets(session.claims, incident.responsible_area_id, current)
    : [];
  const selected = options.data.status.find((r) => r.id === target)?.key ?? "";
  const values = options.data.status.filter((r) => targets.includes(r.key));
  useEffect(() => {
    setTarget("");
    setReason("");
  }, [incident.status_value_id]);
  return (
    <section className="panel">
      <h2>Acciones operativas</h2>
      {values.length > 0 && (
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            if (
              ["cancelled", "onHold", "reopened"].includes(selected) &&
              !reason.trim()
            )
              return;
            const result = await transition.mutate<Incident>(
              `/incidents/${incident.id}/transitions`,
              { status_value_id: target, reason: reason.trim() || null },
            );
            if (result) refresh();
          }}
        >
          <fieldset
            disabled={transition.pending || !!transition.error?.uncertain}
          >
            <legend>Cambiar estado</legend>
            <Select
              label="Estado destino"
              required
              value={target}
              onChange={(e) => setTarget(e.target.value)}
            >
              <option value="">Selecciona un estado</option>
              {values.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.label}
                </option>
              ))}
            </Select>
            <Textarea
              label="Motivo de transición"
              required={["cancelled", "onHold", "reopened"].includes(selected)}
              maxLength={2000}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              hint="Obligatorio al cancelar, pausar o reabrir."
            />
            <Button type="submit" disabled={transition.pending}>
              Aplicar transición
            </Button>
          </fieldset>
        </form>
      )}
      <MutationState mutation={transition} verify={refresh} />
      {session?.claims.role === "admin" && (
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            const fd = new FormData(e.currentTarget);
            const result = await assignment.mutate<Incident>(
              `/incidents/${incident.id}/assignments`,
              {
                responsible_area_id: String(fd.get("area")),
                reason: String(fd.get("reason")).trim(),
              },
            );
            if (result) refresh();
          }}
        >
          <fieldset
            disabled={assignment.pending || !!assignment.error?.uncertain}
          >
            <legend>Reasignar área responsable</legend>
            <Select label="Nueva área responsable" name="area" required>
              <option value="">Selecciona un área</option>
              {options.data.areas
                .filter(
                  (r) => r.is_active && r.id !== incident.responsible_area_id,
                )
                .map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.label}
                  </option>
                ))}
            </Select>
            <Textarea
              label="Motivo de reasignación"
              name="reason"
              required
              maxLength={2000}
            />
            <Button type="submit" disabled={assignment.pending}>
              Reasignar incidencia
            </Button>
          </fieldset>
        </form>
      )}
      <MutationState mutation={assignment} verify={refresh} />
      {!values.length && session?.claims.role !== "admin" && (
        <p>
          No hay acciones de estado o asignación para tu perfil, ámbito y estado
          actual.
        </p>
      )}
    </section>
  );
}
