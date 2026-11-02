"use client";
import { Input, Select } from "@/components/ui";
import { useSession } from "@/lib/auth/session";
import { uuidPattern } from "./forms";

export function ClinicSelector({
  value,
  onChange,
  optional = false,
}: {
  value: string;
  onChange: (value: string) => void;
  optional?: boolean;
}) {
  const { session } = useSession();
  const role = session?.claims.role;
  const clinical = role === "inventoryOperator" || role === "inventoryManager";
  return clinical ? (
    <Select
      label={optional ? "Clínica UUID (opcional)" : "Clínica UUID"}
      value={value}
      required={!optional}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="">
        {optional
          ? "Todas las clínicas de mi ámbito"
          : "Selecciona una clínica asignada"}
      </option>
      {session?.claims.clinic_ids.map((id) => (
        <option key={id} value={id}>
          {id}
        </option>
      ))}
    </Select>
  ) : (
    <Input
      label={optional ? "Clínica UUID (opcional)" : "Clínica UUID"}
      value={value}
      required={!optional}
      pattern={uuidPattern}
      onChange={(e) => onChange(e.target.value)}
      hint="UUID validado por la API. No existe un catálogo nominal de clínicas para Inventory; el historial conserva el ámbito histórico."
    />
  );
}
