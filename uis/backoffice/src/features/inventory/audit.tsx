"use client";
import { useState } from "react";
import { useQuery } from "@/hooks/use-query";
import { useSession } from "@/lib/auth/session";
import type { Schema } from "@/lib/api/types";
import {
  Alert,
  Button,
  DataTable,
  ErrorState,
  Input,
  LoadingState,
  PageHeader,
  Pagination,
} from "@/components/ui";
import { EventTime, ReceivedAt } from "./format";
import { text, uuidPattern } from "./forms";
export function InventoryAudit() {
  const { session } = useSession();
  const allowed = session?.claims.role === "inventoryAuditor";
  const [item, setItem] = useState("");
  const [clinic, setClinic] = useState("");
  const [offset, setOffset] = useState(0);
  const [denialClinic, setDenialClinic] = useState("");
  const [denialOffset, setDenialOffset] = useState(0);
  const audit = useQuery<Schema<"AuditRead">[]>(
    allowed && item && clinic
      ? `/inventory/items/${encodeURIComponent(item)}/audit?clinic_id=${encodeURIComponent(clinic)}&offset=${offset}&limit=50`
      : null,
  );
  const denials = useQuery<Schema<"AccessDenialRead">[]>(
    allowed
      ? `/inventory/access-denials?offset=${denialOffset}&limit=50${denialClinic ? `&clinic_id=${encodeURIComponent(denialClinic)}` : ""}`
      : null,
  );
  return (
    <>
      <PageHeader title="Auditoría de inventario" />
      {!allowed ? (
        <Alert error>
          Esta consulta está reservada a Inventory Auditor y su ámbito
          autorizado.
        </Alert>
      ) : (
        <>
          <section className="panel">
            <h2>Eventos del artículo</h2>
            <form
              className="filters"
              onSubmit={(e) => {
                e.preventDefault();
                const fd = new FormData(e.currentTarget);
                setItem(text(fd, "item"));
                setClinic(text(fd, "clinic"));
                setOffset(0);
                audit.refresh();
              }}
            >
              <Input
                label="Artículo UUID"
                name="item"
                required
                pattern={uuidPattern}
              />
              <Input
                label="Clínica UUID"
                name="clinic"
                required
                pattern={uuidPattern}
              />
              <Button type="submit">Consultar eventos</Button>
            </form>
            {audit.loading && <LoadingState />}
            {audit.error && (
              <ErrorState error={audit.error} retry={audit.refresh} />
            )}{" "}
            {audit.data && (
              <>
                <DataTable
                  rows={audit.data}
                  label="Eventos de auditoría"
                  rowKey={(r) => r.id}
                  columns={[
                    {
                      label: "UTC",
                      cell: (r) => <EventTime value={r.occurred_at} />,
                    },
                    { label: "Acción", cell: (r) => r.action },
                    { label: "Actor", cell: (r) => r.actor_id },
                    {
                      label: "País histórico",
                      cell: (r) => r.jurisdiction_key ?? "Desconocido",
                    },
                    { label: "Resultado", cell: (r) => r.result },
                    { label: "Motivo", cell: (r) => r.reason ?? "—" },
                    {
                      label: "Retención hasta",
                      cell: (r) => <EventTime value={r.retention_until} />,
                    },
                  ]}
                />
                <ReceivedAt data={audit.data} />
                <Button secondary onClick={audit.refresh}>
                  Actualizar eventos
                </Button>
                <Pagination offset={offset} size={50} onChange={setOffset} />
              </>
            )}
            <p className="notice">
              La API aplica la redacción. La fecha de retención es informativa y
              no habilita borrado.
            </p>
          </section>
          <section className="panel">
            <h2>Denegaciones de acceso</h2>
            <form
              className="filters"
              onSubmit={(e) => {
                e.preventDefault();
                setDenialClinic(text(new FormData(e.currentTarget), "clinic"));
                setDenialOffset(0);
                denials.refresh();
              }}
            >
              <Input
                label="Clínica UUID (opcional)"
                name="clinic"
                pattern={uuidPattern}
              />
              <Button type="submit">Consultar denegaciones</Button>
            </form>
            {denials.loading && <LoadingState />}
            {denials.error && (
              <ErrorState error={denials.error} retry={denials.refresh} />
            )}{" "}
            {denials.data && (
              <>
                <DataTable
                  rows={denials.data}
                  label="Denegaciones autorizadas"
                  rowKey={(r) => r.id}
                  columns={[
                    {
                      label: "UTC",
                      cell: (r) => <EventTime value={r.occurred_at} />,
                    },
                    { label: "Operación", cell: (r) => r.operation },
                    { label: "Actor", cell: (r) => r.actor_id },
                    { label: "Razón", cell: (r) => r.reason_code },
                    {
                      label: "País histórico",
                      cell: (r) => r.jurisdiction_key ?? "Desconocido",
                    },
                    { label: "Resultado", cell: (r) => r.result },
                    {
                      label: "Retención hasta",
                      cell: (r) => <EventTime value={r.retention_until} />,
                    },
                  ]}
                />
                <ReceivedAt data={denials.data} />
                <Button secondary onClick={denials.refresh}>
                  Actualizar denegaciones
                </Button>
                <Pagination
                  offset={denialOffset}
                  size={50}
                  onChange={setDenialOffset}
                />
              </>
            )}
          </section>
        </>
      )}
    </>
  );
}
