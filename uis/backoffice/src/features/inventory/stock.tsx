"use client";
import { useState } from "react";
import Link from "next/link";
import { useInventoryFlows } from "@/lib/telemetry/provider";
import { useQuery } from "@/hooks/use-query";
import { useSession } from "@/lib/auth/session";
import { canReadStock } from "@/lib/auth/presentation";
import type { Item, Stock } from "@/lib/api/types";
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
import { ClinicSelector } from "./context-selector";
import { ReceivedAt } from "./format";
export function InventoryStock({ reorder = false }: { reorder?: boolean }) {
  const { session } = useSession();
  const flows = useInventoryFlows();
  const allowed = !!session && canReadStock(session.claims);
  const [search, setSearch] = useState("");
  const [priority, setPriority] = useState(false);
  const [input, setInput] = useState("");
  const [clinic, setClinic] = useState("");
  const [offset, setOffset] = useState(0);
  const q = useQuery<Stock[]>(
    allowed
      ? `/inventory/${reorder ? "reorder" : "stock"}?offset=${offset}&limit=50${clinic ? `&clinic_id=${encodeURIComponent(clinic)}` : ""}`
      : null,
  );
  const catalog = useQuery<Item[]>(
    allowed ? "/inventory/items?offset=0&limit=50" : null,
  );
  const rows = q.data ?? [];
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
            <ClinicSelector
              optional
              value={input}
              onChange={(value) => {
                setInput(value);
                setClinic(value);
                setOffset(0);
                setSearch("");
              }}
            />
            <Button type="submit">Consultar</Button>
          </form>
          <p className="notice">
            Los nombres de artículos se resuelven sólo desde la primera página
            del catálogo; se conserva UUID si no está disponible.
          </p>
          <p className="notice">
            Clínica: {clinic || "todas las posiciones del ámbito autorizado"}.
            Página parcial; sin total global. Una alerta no es un pedido.
          </p>
          <div className="filters">
            <Input
              label="Filtrar artículo o clínica en esta página"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <label>
              <input
                type="checkbox"
                checked={priority}
                onChange={(e) => setPriority(e.target.checked)}
              />{" "}
              Priorizar por déficit de cada posición (sólo página)
            </label>
            <Button secondary onClick={q.refresh}>
              Actualizar existencias
            </Button>
          </div>
          {q.loading && <LoadingState />}
          {q.error && <ErrorState error={q.error} retry={q.refresh} />}{" "}
          {q.data && (
            <>
              {[
                ...new Set(
                  rows
                    .filter((r) =>
                      `${r.item_id} ${r.clinic_id}`
                        .toLowerCase()
                        .includes(search.toLowerCase()),
                    )
                    .map((r) => r.clinic_id),
                ),
              ]
                .sort()
                .map((group) => (
                  <section key={group} aria-label={`Clínica ${group}`}>
                    <h2>Clínica {group} · grupo parcial de la página</h2>
                    <DataTable
                      rows={rows
                        .filter(
                          (r) =>
                            r.clinic_id === group &&
                            `${r.item_id} ${r.clinic_id}`
                              .toLowerCase()
                              .includes(search.toLowerCase()),
                        )
                        .sort((a, b) =>
                          priority
                            ? Math.max(0, b.reorder_point - b.quantity) -
                                Math.max(0, a.reorder_point - a.quantity) ||
                              a.item_id.localeCompare(b.item_id)
                            : 0,
                        )}
                      rowKey={(r) => `${r.item_id}-${r.clinic_id}`}
                      label={
                        reorder
                          ? "Alertas de reorden"
                          : "Existencias autorizadas"
                      }
                      columns={[
                        {
                          label: "Artículo",
                          cell: (r) => (
                            <Link
                              href={`/inventory/items/${r.item_id}?clinic=${r.clinic_id}`}
                              prefetch={false}
                              onClick={(event) => {
                                if (event.nativeEvent.isTrusted && event.button === 0 && !event.metaKey &&
                                    !event.ctrlKey && !event.shiftKey && !event.altKey)
                                  flows?.select(r.item_id, r.clinic_id);
                              }}
                            >
                              {catalog.data?.find(
                                (item) => item.id === r.item_id,
                              )?.title ?? r.item_id}
                            </Link>
                          ),
                        },
                        { label: "Clínica", cell: (r) => r.clinic_id },
                        {
                          label: "Cantidad",
                          cell: (r) => `${r.quantity} ${r.unit}`,
                        },
                        {
                          label: "Presentaciones",
                          cell: (r) =>
                            r.pack_label
                              ? `${r.complete_packs} ${r.pack_label} + ${r.remaining_units} unidades`
                              : "—",
                        },
                        {
                          label: "Punto de reorden",
                          cell: (r) => r.reorder_point,
                        },
                        {
                          label: "Bajo reorden",
                          cell: (r) => (r.below_reorder ? "Sí" : "No"),
                        },
                      ]}
                    />
                  </section>
                ))}
              {rows.filter((r) =>
                `${r.item_id} ${r.clinic_id}`
                  .toLowerCase()
                  .includes(search.toLowerCase()),
              ).length === 0 && (
                <p role="status">Sin resultados en esta página y filtros.</p>
              )}
              <ReceivedAt data={q.data} />
              <Pagination
                offset={offset}
                size={50}
                onChange={(n) => {
                  setOffset(n);
                  setSearch("");
                }}
              />
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
