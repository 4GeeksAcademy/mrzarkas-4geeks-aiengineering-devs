"use client";
import {
  createContext,
  useContext,
  useRef,
  useState,
  type ReactNode,
} from "react";
import Link from "next/link";
import { Alert, Button } from "@/components/ui";
import { useSession } from "@/lib/auth/session";

type State = {
  acknowledged: number;
  blocked: boolean;
  begin: () => boolean;
  finish: () => void;
  unknown: (summary: string) => void;
};
const Context = createContext<State | null>(null);
export const useOperationState = () => useContext(Context);

function Operations({ children }: { children: ReactNode }) {
  const gate = useRef(false);
  const [acknowledged, setAcknowledged] = useState(0);
  const [pending, setPending] = useState(false);
  const [uncertain, setUncertain] = useState("");
  const state: State = {
    acknowledged,
    blocked: pending || !!uncertain,
    begin: () => {
      if (gate.current) return false;
      gate.current = true;
      setPending(true);
      return true;
    },
    finish: () => {
      gate.current = false;
      setPending(false);
    },
    unknown: (summary) => {
      gate.current = true;
      setPending(false);
      setUncertain(summary);
    },
  };
  return (
    <Context.Provider value={state}>
      {uncertain && (
        <section
          className="panel"
          aria-label="Resultado de operación desconocido"
        >
          <Alert error>
            Resultado incierto: {uncertain}. Las escrituras de Inventory quedan
            bloqueadas en esta sesión hasta revisar la operación.
          </Alert>
          <p>
            No existe idempotencia ni conciliación exacta. Una coincidencia en
            el historial no prueba la identidad de la solicitud. Recargar o
            desconectar no revierte la operación.
          </p>
          <Link href="/inventory/items" prefetch={false}>
            Consultar catálogo, datos e historial
          </Link>
          <div className="actions">
            <Button
              secondary
              onClick={() => {
                gate.current = false;
                setUncertain("");
                setAcknowledged((n) => n + 1);
              }}
            >
              Reconozco la incertidumbre tras revisar los datos
            </Button>
          </div>
        </section>
      )}
      {children}
    </Context.Provider>
  );
}
export function InventoryOperations({ children }: { children: ReactNode }) {
  const { session } = useSession();
  return (
    <Operations key={session?.id ?? "disconnected"}>{children}</Operations>
  );
}
