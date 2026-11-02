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
  Select,
} from "@/components/ui";
import { OperationForm, text, uuidPattern } from "./forms";
import { ClinicSelector } from "./context-selector";
import { EventTime, ReceivedAt, presentation } from "./format";
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
              ...presentation(fd),
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
  const { session } = useSession();
  const clinical = ["inventoryOperator", "inventoryManager"].includes(
    session?.claims.role ?? "",
  );
  const initial =
    !clinical || session?.claims.clinic_ids.includes(initialClinic)
      ? initialClinic
      : "";
  const [input, setInput] = useState(initial);
  const [clinic, setClinic] = useState(initial);
  const [lotOffset, setLotOffset] = useState(0);
  const lots = useQuery<Schema<"LotRead">[]>(
    item.uses_lots
      ? `/inventory/items/${item.id}/lots?offset=${lotOffset}&limit=50`
      : null,
  );
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
          <ClinicSelector
            value={input}
            onChange={(value) => {
              setInput(value);
              setClinic("");
              setLot("");
              setLotInput("");
              setOffset(0);
            }}
          />
          {item.uses_lots && (
            <Select
              label="Lote (saldo y operaciones)"
              value={lotInput}
              onChange={(e) => {
                setLotInput(e.target.value);
                setLot("");
                setClinic("");
              }}
            >
              <option value="">Todos los lotes (sólo consulta)</option>
              {lots.data?.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.code} · {r.id}
                </option>
              ))}
            </Select>
          )}
          <Button type="submit">Consultar stock e historial</Button>
        </form>
        <p>
          Clínica activa: {clinic || "sin confirmar"} · Lote:{" "}
          {lot || "total clínico"}
        </p>
        {item.uses_lots && (
          <>
            <Pagination
              offset={lotOffset}
              size={50}
              onChange={(n) => {
                setLotOffset(n);
                setLotInput("");
                setLot("");
                setClinic("");
              }}
            />
            {lots.loading && <LoadingState />}
            {lots.error && (
              <ErrorState error={lots.error} retry={lots.refresh} />
            )}
          </>
        )}
        {stock.loading && <LoadingState />}
        {stock.error && (
          <>
            <ErrorState error={stock.error} retry={refresh} />
            {stock.error.status === 409 && (
              <p className="notice">
                El stock no está disponible. Puede faltar la configuración
                obligatoria o existir un conflicto de estado; no equivale a
                saldo cero. Solicita la configuración a un responsable.
              </p>
            )}
          </>
        )}{" "}
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
        <ReceivedAt data={stock.data} />
        <Button secondary onClick={refresh} disabled={!clinic}>
          Actualizar stock e historial
        </Button>
        <h3 id="historial">Movimientos de la clínica</h3>
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
                {
                  label: "Momento local / UTC",
                  cell: (r) => <EventTime value={r.occurred_at} />,
                },
                { label: "Tipo", cell: (r) => r.kind },
                { label: "Lote", cell: (r) => r.lot_id ?? "—" },
                { label: "Delta", cell: (r) => `${r.delta} ${r.unit}` },
                {
                  label: "Presentación histórica",
                  cell: (r) =>
                    r.pack_label
                      ? `${r.pack_label} × ${r.pack_size}`
                      : "Sin presentación",
                },
                {
                  label: "Compensa original",
                  cell: (r) => r.correction_of ?? "—",
                },
                {
                  label: "Retención hasta",
                  cell: (r) => <EventTime value={r.retention_until} />,
                },
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
        key={`${clinic}-${lot}-${item.pack_label}-${item.pack_size}`}
        item={item}
        clinic={clinic}
        lot={lot}
        stock={stock.data}
        history={history.data}
        refresh={refresh}
      />
    </>
  );
}
