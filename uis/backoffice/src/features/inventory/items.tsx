"use client";
import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@/hooks/use-query";
import { useSession } from "@/lib/auth/session";
import { isInventory } from "@/lib/auth/presentation";
import type { Item, Schema } from "@/lib/api/types";
import {
  Alert,
  DataTable,
  ErrorState,
  Input,
  LoadingState,
  PageHeader,
  Pagination,
} from "@/components/ui";
import { OperationForm, text } from "./forms";
export function InventoryItems() {
  const { session } = useSession();
  const allowed = !!session && isInventory(session.claims);
  const [offset, setOffset] = useState(0);
  const query = useQuery<Item[]>(
    allowed ? `/inventory/items?offset=${offset}&limit=50` : null,
  );
  return (
    <>
      <PageHeader title="Catálogo de inventario" />
      {!allowed ? (
        <Alert error>Tu perfil no dispone de Inventory.</Alert>
      ) : (
        <>
          <section className="panel">
            {query.loading && <LoadingState />}
            {query.error && (
              <ErrorState error={query.error} retry={query.refresh} />
            )}{" "}
            {query.data && (
              <>
                <DataTable
                  rows={query.data}
                  rowKey={(r) => r.id}
                  label="Artículos de inventario"
                  columns={[
                    {
                      label: "Código",
                      cell: (r) => (
                        <Link
                          href={`/inventory/items/${r.id}`}
                          prefetch={false}
                        >
                          {r.product_code}
                        </Link>
                      ),
                    },
                    { label: "Título", cell: (r) => r.title },
                    { label: "Unidad base", cell: (r) => r.unit },
                    {
                      label: "Presentación",
                      cell: (r) =>
                        r.pack_label
                          ? `${r.pack_label} (${r.pack_size})`
                          : "Sin presentación",
                    },
                    {
                      label: "Lotes",
                      cell: (r) => (r.uses_lots ? "Sí" : "No"),
                    },
                    {
                      label: "Activo",
                      cell: (r) => (r.is_active ? "Sí" : "No"),
                    },
                  ]}
                />
                <Pagination offset={offset} size={50} onChange={setOffset} />
              </>
            )}
          </section>
          {session?.claims.role === "inventoryAdmin" && (
            <OperationForm<Schema<"ItemCreate">>
              title="Crear artículo"
              path="/inventory/items"
              refresh={query.refresh}
              body={(fd) => ({
                title: text(fd, "title"),
                product_code: text(fd, "product_code"),
                unit: text(fd, "unit"),
                uses_lots: fd.get("uses_lots") === "on",
                pack_label: text(fd, "pack_label") || null,
                pack_size: Number(fd.get("pack_size")),
              })}
            >
              <div className="form-grid">
                <Input
                  label="Título"
                  name="title"
                  required
                  maxLength={200}
                  pattern=".*\S.*"
                />
                <Input
                  label="Código de producto"
                  name="product_code"
                  required
                  maxLength={100}
                  pattern="[A-Za-z0-9][A-Za-z0-9_.-]*"
                />
                <Input
                  label="Unidad base"
                  name="unit"
                  required
                  maxLength={80}
                  pattern=".*\S.*"
                />
                <Input
                  label="Nombre de presentación (opcional)"
                  name="pack_label"
                  maxLength={80}
                />
                <Input
                  label="Unidades por presentación"
                  name="pack_size"
                  type="number"
                  min={1}
                  max={1000000000}
                  step={1}
                  required
                  defaultValue={1}
                />
                <label>
                  <input name="uses_lots" type="checkbox" /> Gestionar lotes
                  (inmutable después del alta)
                </label>
              </div>
              <p className="notice">
                El código, unidad y modo de lotes no podrán modificarse. Sin
                presentación, la equivalencia debe ser 1.
              </p>
            </OperationForm>
          )}
        </>
      )}
    </>
  );
}
