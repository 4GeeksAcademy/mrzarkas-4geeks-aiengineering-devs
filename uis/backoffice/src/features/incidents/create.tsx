"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useSession } from "@/lib/auth/session";
import { canCreateIncident } from "@/lib/auth/presentation";
import type { Incident, Schema } from "@/lib/api/types";
import { useMutation } from "@/hooks/use-mutation";
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
import { useIncidentOptions } from "./options";
import { useUnsavedChanges } from "@/hooks/use-unsaved-changes";
export function IncidentCreate() {
  const { session } = useSession();
  const router = useRouter();
  const options = useIncidentOptions();
  const m = useMutation();
  const draft = useUnsavedChanges();
  const [jurisdiction, setJurisdiction] = useState("");
  if (!session || !canCreateIncident(session.claims))
    return <Alert error>Tu perfil no puede crear incidencias.</Alert>;
  const own =
    session.claims.role === "responsibleArea" ? session.claims.area_id : null;
  return (
    <>
      <PageHeader title="Nueva incidencia" />
      <Link href="/incidents" prefetch={false}>
        Volver a incidencias
      </Link>
      <section className="panel">
        {options.loading ? (
          <LoadingState />
        ) : options.error ? (
          <ErrorState error={options.error} retry={options.refresh} />
        ) : (
          <form
            onChange={draft.markDirty}
            onSubmit={async (e) => {
              e.preventDefault();
              const fd = new FormData(e.currentTarget);
              const text = (key: string) => String(fd.get(key) ?? "").trim();
              if (!text("title") || !text("description")) return;
              const body: Schema<"IncidentCreate"> = {
                title: text("title"),
                description: text("description"),
                jurisdiction_id: jurisdiction,
                clinic_id: text("clinic_id"),
                affected_system_id: text("affected_system_id"),
                responsible_area_id: own ?? text("responsible_area_id"),
                entry_channel_value_id: text("entry_channel_value_id"),
                incident_type_value_id: text("incident_type_value_id"),
                severity_value_id: text("severity_value_id"),
              };
              const result = await m.mutate<Incident>("/incidents", body);
              if (result) {
                draft.markClean();
                router.push(`/incidents/${result.id}?created=1`);
              }
            }}
          >
            <fieldset disabled={m.pending || !!m.error?.uncertain}>
              <legend className="sr-only">Datos de incidencia</legend>
              <div className="form-grid">
                <Select
                  label="Jurisdicción"
                  required
                  value={jurisdiction}
                  onChange={(e) => setJurisdiction(e.target.value)}
                >
                  <option value="">Selecciona una jurisdicción</option>
                  {options.data.jurisdictions
                    .filter((r) => r.is_active)
                    .map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.label}
                      </option>
                    ))}
                </Select>
                <Select
                  key={jurisdiction}
                  label="Clínica"
                  name="clinic_id"
                  required
                >
                  <option value="">Selecciona una clínica</option>
                  {options.data.clinics
                    .filter(
                      (r) => r.is_active && r.jurisdiction_id === jurisdiction,
                    )
                    .map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.label}
                      </option>
                    ))}
                </Select>
                <Select
                  label="Sistema afectado"
                  name="affected_system_id"
                  required
                >
                  <option value="">Selecciona un sistema</option>
                  {options.data.systems
                    .filter((r) => r.is_active)
                    .map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.label}
                      </option>
                    ))}
                </Select>
                <Select
                  label="Área responsable"
                  name="responsible_area_id"
                  required
                  defaultValue={own ?? ""}
                >
                  <option value="">Selecciona un área</option>
                  {options.data.areas
                    .filter((r) => r.is_active && (!own || r.id === own))
                    .map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.label}
                      </option>
                    ))}
                </Select>
                {(
                  [
                    ["channel", "entry_channel_value_id", "Canal de entrada"],
                    ["type", "incident_type_value_id", "Tipo"],
                    ["severity", "severity_value_id", "Severidad"],
                  ] as const
                ).map(([kind, name, label]) => (
                  <Select key={name} {...{ name, label }} required>
                    <option value="">Selecciona una opción</option>
                    {options.data[kind].map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.label}
                      </option>
                    ))}
                  </Select>
                ))}
              </div>
              <Input
                label="Título"
                name="title"
                required
                maxLength={200}
                pattern=".*\S.*"
                error={m.error?.fields.title}
              />
              <Textarea
                label="Descripción"
                name="description"
                required
                maxLength={10000}
                error={m.error?.fields.description}
              />
              <p className="privacy-notice">
                No incluyas nombres, identificadores, diagnósticos, notas
                clínicas ni datos de pacientes.
              </p>
              <div className="actions">
                <Link href="/incidents" prefetch={false}>
                  Cancelar
                </Link>
                <Button type="submit" disabled={m.pending}>
                  {m.pending ? "Creando…" : "Crear incidencia"}
                </Button>
              </div>
            </fieldset>
          </form>
        )}
        <MutationState mutation={m} verify={() => router.push("/incidents")} />
      </section>
    </>
  );
}
