"use client";
import { useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@/hooks/use-query";
import { useSession } from "@/lib/auth/session";
import { isInventory, canReadStock } from "@/lib/auth/presentation";
import type { Item, Schema, Stock } from "@/lib/api/types";
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
import { OperationForm, text, uuidPattern } from "./forms";
import { ClinicalActions } from "./clinical-actions";
export function InventoryDetail({ id }: { id: string }) {
  const { session } = useSession();
  const allowed = !!session && isInventory(session.claims);
  const path = `/inventory/items/${encodeURIComponent(id)}`;
  const q = useQuery<Item>(allowed ? path : null);
  return (
    <>
      <PageHeader title="Artículo de inventario" />
      <Link href="/inventory/items" prefetch={false}>
        Volver al catálogo
      </Link>
      {!allowed ? (
        <Alert error>Tu perfil no dispone de Inventory.</Alert>
      ) : (
        <>
          {q.loading && <LoadingState />}
          {q.error && <ErrorState error={q.error} retry={q.refresh} />}{" "}
          {q.data && <ItemDetail key={id} item={q.data} refresh={q.refresh} />}
        </>
      )}
    </>
  );
}
function ItemDetail({ item, refresh }: { item: Item; refresh: () => void }) {
  const { session } = useSession();
  const search = useSearchParams();
  const admin = session?.claims.role === "inventoryAdmin";
  return (
    <>
      <section className="panel">
        <h2>{item.title}</h2>
        <dl className="facts">
          {Object.entries({
            Código: item.product_code,
            "Unidad base": item.unit,
            Lotes: item.uses_lots ? "Sí" : "No",
            Activo: item.is_active ? "Sí" : "No",
            Presentación: item.pack_label ?? "Sin presentación",
            Equivalencia: item.pack_size,
          }).map(([k, v]) => (
            <div key={k}>
              <dt>{k}</dt>
              <dd>{v}</dd>
            </div>
          ))}
        </dl>
        <p className="notice">
          El stock pertenece a artículo y clínica y se calcula desde
          movimientos. No hay saldo editable.
        </p>
      </section>
      {admin && item.is_active && (
        <>
          <OperationForm<Schema<"ItemUpdate">>
            title="Actualizar título y presentación"
            path={`/inventory/items/${item.id}`}
            method="PATCH"
            refresh={refresh}
            body={(fd) => ({
              title: text(fd, "title"),
              pack_label: text(fd, "pack_label") || null,
              pack_size: Number(fd.get("pack_size")),
            })}
          >
            <div className="form-grid">
              <Input
                label="Título"
                name="title"
                defaultValue={item.title}
                required
                maxLength={200}
                pattern=".*\S.*"
              />
              <Input
                label="Nombre de presentación"
                name="pack_label"
                defaultValue={item.pack_label ?? ""}
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
                defaultValue={item.pack_size}
              />
            </div>
          </OperationForm>
          <OperationForm<Schema<"ReasonRequest">>
            title="Dar de baja artículo"
            path={`/inventory/items/${item.id}/deactivation`}
            confirm
            refresh={refresh}
            body={(fd) => ({ reason: text(fd, "reason") })}
          >
            <Input
              label="Motivo de baja"
              name="reason"
              required
              maxLength={500}
              pattern=".*\S.*"
            />
            <p className="notice">
              La API sólo permite la baja con stock total cero. Conserva el
              historial y no ofrece reactivación.
            </p>
          </OperationForm>
        </>
      )}
      {item.uses_lots && <Lots item={item} admin={admin} />}{" "}
      {session && canReadStock(session.claims) && (
        <ClinicalDetail
          key={`${item.id}-${item.is_active}`}
          item={item}
          initialClinic={search.get("clinic") ?? ""}
        />
      )}
    </>
  );
}
function Lots({ item, admin }: { item: Item; admin: boolean }) {
  const [offset, setOffset] = useState(0);
  const q = useQuery<Schema<"LotRead">[]>(
    `/inventory/items/${item.id}/lots?offset=${offset}&limit=50`,
  );
  return (
    <section className="panel">
      <h2>Lotes</h2>
      {q.loading && <LoadingState />}
      {q.error && <ErrorState error={q.error} retry={q.refresh} />}{" "}
      {q.data && (
        <>
          <DataTable
            rows={q.data}
            label="Lotes del artículo"
            rowKey={(r) => r.id}
            columns={[
              { label: "UUID", cell: (r) => r.id },
              { label: "Código", cell: (r) => r.code },
            ]}
          />
          <Pagination offset={offset} size={50} onChange={setOffset} />
        </>
      )}
      {admin && item.is_active && (
        <OperationForm<Schema<"LotCreate">>
          title="Crear lote"
          path={`/inventory/items/${item.id}/lots`}
          refresh={q.refresh}
          body={(fd) => ({ code: text(fd, "code") })}
        >
          <Input
            label="Código de lote"
            name="code"
            required
            maxLength={100}
            pattern="[A-Za-z0-9][A-Za-z0-9_.-]*"
          />
        </OperationForm>
      )}
    </section>
  );
}
function ClinicalDetail({
  item,
  initialClinic,
}: {
  item: Item;
  initialClinic: string;
}) {
  const [input, setInput] = useState(initialClinic);
  const [clinic, setClinic] = useState(initialClinic);
  const [lotInput, setLotInput] = useState("");
  const [lot, setLot] = useState("");
  const [offset, setOffset] = useState(0);
  const stock = useQuery<Stock>(
    clinic
      ? `/inventory/items/${item.id}/stock?clinic_id=${encodeURIComponent(clinic)}${lot ? `&lot_id=${encodeURIComponent(lot)}` : ""}`
      : null,
  );
  const history = useQuery<Schema<"MovementRead">[]>(
    clinic
      ? `/inventory/items/${item.id}/movements?clinic_id=${encodeURIComponent(clinic)}&offset=${offset}&limit=50`
      : null,
  );
  const refresh = () => {
    stock.refresh();
    history.refresh();
  };
  return (
    <>
      <section className="panel">
        <h2>Stock e historial clínico</h2>
        <form
          className="filters"
          onSubmit={(e) => {
            e.preventDefault();
            setClinic(input.trim());
            setLot(lotInput.trim());
            setOffset(0);
            refresh();
          }}
        >
          <Input
            label="Clínica UUID"
            required
            pattern={uuidPattern}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            hint="La API valida la clínica y su ámbito. No se utiliza el catálogo de Management con roles Inventory."
          />
          {item.uses_lots && (
            <Input
              label="Lote UUID (opcional para lectura, obligatorio para movimientos)"
              pattern={uuidPattern}
              value={lotInput}
              onChange={(e) => setLotInput(e.target.value)}
            />
          )}
          <Button type="submit">Consultar stock e historial</Button>
        </form>
        {stock.loading && <LoadingState />}
        {stock.error && <ErrorState error={stock.error} retry={refresh} />}{" "}
        {stock.data && (
          <>
            <p>
              Cantidad:{" "}
              <strong>
                {stock.data.quantity} {stock.data.unit}
              </strong>
              {stock.data.pack_label
                ? ` · ${stock.data.complete_packs} ${stock.data.pack_label} y ${stock.data.remaining_units} unidades`
                : ""}
            </p>
            <p>
              Punto de reorden clínico: {stock.data.reorder_point} · Bajo
              reorden: {stock.data.below_reorder ? "Sí" : "No"}
            </p>
          </>
        )}
        <h3>Movimientos de la clínica</h3>
        {history.loading && <LoadingState />}
        {history.error && (
          <ErrorState error={history.error} retry={refresh} />
        )}{" "}
        {history.data && (
          <>
            <DataTable
              rows={history.data}
              label="Historial de movimientos"
              rowKey={(r) => r.id}
              columns={[
                { label: "UUID", cell: (r) => r.id },
                { label: "Momento UTC", cell: (r) => r.occurred_at },
                { label: "Tipo", cell: (r) => r.kind },
                { label: "Lote", cell: (r) => r.lot_id ?? "—" },
                { label: "Delta", cell: (r) => r.delta },
                { label: "Saldo previo", cell: (r) => r.previous_quantity },
                {
                  label: "Saldo resultante",
                  cell: (r) => r.resulting_quantity,
                },
                { label: "Actor", cell: (r) => r.actor_id },
                { label: "Motivo", cell: (r) => r.reason ?? "—" },
                {
                  label: "País histórico",
                  cell: (r) => r.jurisdiction_key ?? "Desconocido",
                },
              ]}
            />
            <Pagination offset={offset} size={50} onChange={setOffset} />
          </>
        )}{" "}
        {!clinic && <p>Introduce una clínica autorizada para consultar.</p>}
      </section>
      <ClinicalActions
        key={`${clinic}-${lot}`}
        item={item}
        clinic={clinic}
        lot={lot}
        refresh={refresh}
      />
    </>
  );
}
