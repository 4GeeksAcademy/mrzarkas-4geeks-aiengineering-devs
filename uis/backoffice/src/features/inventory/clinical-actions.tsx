"use client";
import { useState } from "react";
import type { Item, Schema } from "@/lib/api/types";
import { useSession } from "@/lib/auth/session";
import { Input, Select } from "@/components/ui";
import { OperationForm, text, uuidPattern } from "./forms";
export function ClinicalActions({
  item,
  clinic,
  lot,
  refresh,
}: {
  item: Item;
  clinic: string;
  lot: string;
  refresh: () => void;
}) {
  const { session } = useSession();
  const [kind, setKind] = useState<"in" | "out">("in");
  const role = session?.claims.role;
  const valid = !!clinic && (!item.uses_lots || !!lot) && item.is_active;
  const bound = {
    item_id: item.id,
    clinic_id: clinic,
    ...(item.uses_lots ? { lot_id: lot } : {}),
  };
  return (
    <>
      {role === "inventoryManager" && (
        <OperationForm<Schema<"ClinicConfig">>
          title="Configurar punto de reorden"
          path={`/inventory/items/${item.id}/clinics/${clinic}/configuration`}
          disabled={!clinic || !item.is_active}
          refresh={refresh}
          body={(fd) => ({ reorder_point: Number(fd.get("reorder_point")) })}
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
            Esta configuración crea una posición con saldo cero, no una entrada.
            La API exige el umbral antes de cualquier movimiento.
          </p>
        </OperationForm>
      )}
      {["inventoryOperator", "inventoryManager"].includes(role ?? "") && (
        <OperationForm<Schema<"MovementCreate">>
          title="Registrar entrada o salida"
          path="/inventory/movements"
          disabled={!valid}
          refresh={refresh}
          body={(fd) => ({
            ...bound,
            kind,
            quantity: Number(fd.get("quantity")),
            unit: text(fd, "unit") as "base" | "pack",
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
            />
            <Select label="Unidad del movimiento" name="unit">
              <option value="base">Unidades base ({item.unit})</option>
              {item.pack_label && (
                <option value="pack">
                  {item.pack_label} ({item.pack_size} unidades)
                </option>
              )}
            </Select>
            <Input label="Motivo (opcional)" name="reason" maxLength={500} />
          </div>
          <p className="notice">
            La API convierte presentaciones y conserva su equivalencia
            histórica. No se admiten saldos negativos.
          </p>
        </OperationForm>
      )}
      {role === "inventoryManager" && (
        <>
          <OperationForm<Schema<"MovementCreate">>
            title="Registrar conteo físico"
            path="/inventory/movements"
            disabled={!valid}
            confirm
            refresh={refresh}
            body={(fd) => ({
              ...bound,
              kind: "adjust",
              counted_quantity: Number(fd.get("counted_quantity")),
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
            />
            <Input
              label="Motivo del conteo"
              name="reason"
              required
              maxLength={500}
              pattern=".*\S.*"
            />
            <p className="notice">
              El ajuste será un movimiento por la diferencia entre conteo y
              stock previo; no edita el saldo.
            </p>
          </OperationForm>
          <CorrectionForm refresh={refresh} />
        </>
      )}
    </>
  );
}
function CorrectionForm({ refresh }: { refresh: () => void }) {
  const [movement, setMovement] = useState("");
  return (
    <OperationForm<Schema<"ReasonRequest">>
      title="Compensar movimiento"
      path={`/inventory/movements/${encodeURIComponent(movement)}/correction`}
      confirm
      refresh={refresh}
      body={(fd) => ({ reason: text(fd, "reason") })}
    >
      <Input
        label="UUID del movimiento original"
        pattern={uuidPattern}
        required
        value={movement}
        onChange={(e) => setMovement(e.target.value)}
      />
      <Input
        label="Motivo de compensación"
        name="reason"
        required
        maxLength={500}
        pattern=".*\S.*"
      />
      <p className="notice">
        Sólo se compensa una vez el movimiento original. No se compensan
        compensaciones. Una sustitución requiere una operación separada.
      </p>
    </OperationForm>
  );
}
