"use client";
import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@/hooks/use-query";
import { useSession } from "@/lib/auth/session";
import { canReadStock } from "@/lib/auth/presentation";
import type { Stock } from "@/lib/api/types";
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
import { uuidPattern } from "./forms";
export function InventoryStock({ reorder = false }: { reorder?: boolean }) {
  const { session } = useSession();
  const allowed = !!session && canReadStock(session.claims);
  const [input, setInput] = useState("");
  const [clinic, setClinic] = useState("");
  const [offset, setOffset] = useState(0);
  const q = useQuery<Stock[]>(
    allowed
      ? `/inventory/${reorder ? "reorder" : "stock"}?offset=${offset}&limit=50${clinic ? `&clinic_id=${encodeURIComponent(clinic)}` : ""}`
      : null,
  );
  return (
    <>
      <PageHeader
        title={
          reorder ? "Artículos bajo punto de reorden" : "Stock por clínica"
        }
      />
      {!allowed ? (
        <Alert error>Tu perfil no puede leer stock clínico.</Alert>
      ) : (
        <section className="panel">
          <form
            className="filters"
            onSubmit={(e) => {
              e.preventDefault();
              setClinic(input.trim());
              setOffset(0);
              q.refresh();
            }}
          >
            <Input
              label="Clínica UUID (opcional)"
              pattern={uuidPattern}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              hint="Sin filtro, la API devuelve sólo las clínicas de tu ámbito autorizado."
            />
            <Button type="submit">Consultar</Button>
          </form>
          {q.loading && <LoadingState />}
          {q.error && <ErrorState error={q.error} retry={q.refresh} />}{" "}
          {q.data && (
            <>
              <DataTable
                rows={q.data}
                rowKey={(r) => `${r.item_id}-${r.clinic_id}`}
                label={
                  reorder ? "Alertas de reorden" : "Existencias autorizadas"
                }
                columns={[
                  {
                    label: "Artículo",
                    cell: (r) => (
                      <Link
                        href={`/inventory/items/${r.item_id}?clinic=${r.clinic_id}`}
                        prefetch={false}
                      >
                        {r.item_id}
                      </Link>
                    ),
                  },
                  { label: "Clínica", cell: (r) => r.clinic_id },
                  { label: "Cantidad", cell: (r) => `${r.quantity} ${r.unit}` },
                  {
                    label: "Presentaciones",
                    cell: (r) =>
                      r.pack_label
                        ? `${r.complete_packs} ${r.pack_label} + ${r.remaining_units} unidades`
                        : "—",
                  },
                  { label: "Punto de reorden", cell: (r) => r.reorder_point },
                  {
                    label: "Bajo reorden",
                    cell: (r) => (r.below_reorder ? "Sí" : "No"),
                  },
                ]}
              />
              <Pagination offset={offset} size={50} onChange={setOffset} />
              <p className="notice">
                Las consultas son paginadas y no un snapshot global. Una página
                corta de reorden puede deberse a cambios concurrentes; Siguiente
                permite continuar. Stock igual al umbral no activa alerta.
              </p>
            </>
          )}
        </section>
      )}
    </>
  );
}
