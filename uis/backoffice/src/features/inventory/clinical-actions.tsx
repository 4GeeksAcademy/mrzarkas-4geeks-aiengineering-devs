"use client";
import { useState } from "react";
import type { Item, Schema, Stock } from "@/lib/api/types";
import { useSession } from "@/lib/auth/session";
import { Input, Select } from "@/components/ui";
import { OperationForm, text } from "./forms";
import { integer } from "./format";

type Movement = Schema<"MovementRead">;
export function ClinicalActions({
  item,
  clinic,
  lot,
  stock,
  history = [],
  refresh,
}: {
  item: Item;
  clinic: string;
  lot: string;
  stock?: Stock;
  history?: Movement[];
  refresh: () => void;
}) {
  const { session } = useSession();
  const [kind, setKind] = useState<"in" | "out">("in");
  const [quantity, setQuantity] = useState("");
  const [unit, setUnit] = useState<"base" | "pack">("base");
  const [counted, setCounted] = useState("");
  const role = session?.claims.role;
  const inScope = !!clinic && !!session?.claims.clinic_ids.includes(clinic);
  const valid =
    inScope && (!item.uses_lots || !!lot) && item.is_active && !!stock;
  const bound = {
    item_id: item.id,
    clinic_id: clinic,
    ...(item.uses_lots ? { lot_id: lot } : {}),
  };
  const context = `Artículo ${item.product_code} · Clínica ${clinic || "sin seleccionar"} · Lote ${lot || "sin lote"}`;
  const factor = unit === "pack" ? item.pack_size : 1;
  const amount = Number(quantity);
  const conversionValid =
    !!quantity.trim() &&
    Number.isInteger(amount) &&
    amount > 0 &&
    amount <= 1000000000;
  const count = Number(counted);
  const countValid =
    !!counted.trim() &&
    Number.isInteger(count) &&
    count >= 0 &&
    count <= 1000000000;
  const movementSummary = (
    <p>
      {kind === "in" ? "Entrada" : "Salida"}:{" "}
      {conversionValid
        ? `${amount} × ${factor} = ${amount * factor} ${item.unit}`
        : "Introduce una cantidad entera válida"}
      . Saldo disponible orientativo:{" "}
      {stock ? `${stock.quantity} ${stock.unit}` : "no consultado"}. La API
      valida el saldo final.
    </p>
  );
  const countSummary = (
    <p>
      Saldo previo orientativo: {stock?.quantity ?? "no consultado"}. Cantidad
      física: {countValid ? count : "sin validar"}. Diferencia prevista:{" "}
      {countValid && stock ? count - stock.quantity : "no disponible"}. Se
      generará un movimiento de ajuste; la diferencia final depende de la API.
    </p>
  );
  return (
    <>
      <p className="notice">
        Clínica activa: {clinic || "sin seleccionar"} · Lote activo:{" "}
        {lot || "sin seleccionar"}
      </p>
      {role === "inventoryManager" && (
        <OperationForm<Schema<"ClinicConfig">>
          title="Configurar punto de reorden"
          path={`/inventory/items/${item.id}/clinics/${clinic}/configuration`}
          disabled={!inScope || !item.is_active}
          refresh={refresh}
          confirm
          context={context}
          summary={
            <p>
              Esta configuración no crea una entrada. La posición nueva comienza
              en cero.
            </p>
          }
          body={(fd) => ({ reorder_point: integer(fd.get("reorder_point")) })}
        >
          <Input
            label="Punto de reorden obligatorio"
            name="reorder_point"
            type="number"
            min={1}
            max={1000000000}
            step={1}
            required
          />
          <p className="notice">
            Umbral actual:{" "}
            {stock?.reorder_point ??
              "no disponible; consulta el stock o configura la posición"}
            . La API exige un umbral antes de cualquier movimiento.
          </p>
        </OperationForm>
      )}
      {["inventoryOperator", "inventoryManager"].includes(role ?? "") && (
        <div id="movimientos">
          <OperationForm<Schema<"MovementCreate">>
            title="Registrar entrada o salida"
            path="/inventory/movements"
            disabled={!valid}
            refresh={refresh}
            confirm
            context={`${context} · ${kind} · ${quantity || "sin cantidad"} ${unit}`}
            summary={movementSummary}
            body={(fd) => ({
              ...bound,
              kind,
              quantity: integer(fd.get("quantity")),
              unit,
              reason: text(fd, "reason") || null,
            })}
          >
            <div className="form-grid">
              <Select
                label="Movimiento"
                value={kind}
                onChange={(e) => setKind(e.target.value as "in" | "out")}
              >
                <option value="in">Entrada</option>
                <option value="out">Salida</option>
              </Select>
              <Input
                label="Cantidad"
                name="quantity"
                type="number"
                min={1}
                max={1000000000}
                step={1}
                required
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
              />
              <Select
                label="Unidad del movimiento"
                name="unit"
                value={unit}
                onChange={(e) => setUnit(e.target.value as "base" | "pack")}
              >
                <option value="base">Unidades base ({item.unit})</option>
                {item.pack_label && (
                  <option value="pack">
                    {item.pack_label} ({item.pack_size} unidades)
                  </option>
                )}
              </Select>
              <Input label="Motivo (opcional)" name="reason" maxLength={500} />
            </div>
            {movementSummary}
          </OperationForm>
        </div>
      )}
      {role === "inventoryManager" && (
        <>
          <div id="conteo">
            <OperationForm<Schema<"MovementCreate">>
              title="Registrar conteo físico"
              path="/inventory/movements"
              disabled={!valid}
              confirm
              context={`${context} · Contado ${counted || "sin cantidad"} ${item.unit}`}
              summary={countSummary}
              refresh={refresh}
              body={(fd) => ({
                ...bound,
                kind: "adjust",
                counted_quantity: integer(fd.get("counted_quantity"), 0),
                unit: "base",
                reason: text(fd, "reason"),
              })}
            >
              <Input
                label="Cantidad contada en unidades base"
                name="counted_quantity"
                type="number"
                min={0}
                max={1000000000}
                step={1}
                required
                value={counted}
                onChange={(e) => setCounted(e.target.value)}
              />
              <Input
                label="Motivo del conteo"
                name="reason"
                required
                maxLength={500}
                pattern=".*\S.*"
              />
              {countSummary}
            </OperationForm>
          </div>
          <CorrectionForm
            history={history}
            clinic={clinic}
            context={context}
            refresh={refresh}
            disabled={!inScope || !item.is_active}
          />
        </>
      )}
    </>
  );
}
function CorrectionForm({
  history,
  clinic,
  context,
  refresh,
  disabled,
}: {
  history: Movement[];
  clinic: string;
  context: string;
  refresh: () => void;
  disabled: boolean;
}) {
  const [movement, setMovement] = useState("");
  const original = history.find(
    (r) =>
      r.id === movement && r.clinic_id === clinic && r.kind !== "correction",
  );
  const corrected = history.some((r) => r.correction_of === movement);
  return (
    <OperationForm<Schema<"ReasonRequest">>
      title="Compensar movimiento"
      path={`/inventory/movements/${encodeURIComponent(movement)}/correction`}
      disabled={disabled}
      canSubmit={!!original && !corrected}
      confirm
      context={context}
      refresh={refresh}
      summary={
        <p>
          Original: {original?.id ?? "sin seleccionar"} · Clínica del original:{" "}
          {original?.clinic_id ?? "—"} · Delta histórico:{" "}
          {original?.delta ?? "—"}. La API rechazará compensaciones previas o
          saldo negativo.
        </p>
      }
      body={(fd) => ({ reason: text(fd, "reason") })}
    >
      <Select
        label="UUID del movimiento original"
        required
        value={movement}
        onChange={(e) => setMovement(e.target.value)}
      >
        <option value="">
          Selecciona un original de la página de historial
        </option>
        {history
          .filter((r) => r.kind !== "correction")
          .map((r) => (
            <option key={r.id} value={r.id}>
              {r.id} · {r.kind} · delta {r.delta}
            </option>
          ))}
      </Select>
      <Input
        label="Motivo de compensación"
        name="reason"
        required
        maxLength={500}
        pattern=".*\S.*"
      />
      <p className="notice">
        {corrected
          ? "Existe una compensación de este original en la página consultada."
          : "La API comprueba compensaciones anteriores, incluso fuera de esta página."}{" "}
        Una sustitución requiere una operación separada. No se editan
        movimientos.
      </p>
    </OperationForm>
  );
}
