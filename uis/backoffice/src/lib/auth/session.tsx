"use client";
import {
  createContext,
  useEffect,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { request } from "@/lib/api/client";
import { readClaims, isInventory, type Claims } from "./presentation";
type Session = {
  token: string;
  claims: Claims;
  signal: AbortSignal;
  id: number;
};
type Context = {
  session: Session | null;
  connect: (token: string) => Promise<void>;
  disconnect: () => void;
  message: string;
};
const Context = createContext<Context | null>(null);
export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [message, setMessage] = useState("");
  const generation = useRef(0);
  const pending = useRef<AbortController | null>(null);
  useEffect(
    () => () => {
      generation.current++;
      pending.current?.abort();
      pending.current = null;
    },
    [],
  );
  const disconnect = useCallback(() => {
    generation.current++;
    pending.current?.abort();
    pending.current = null;
    setSession(null);
    setMessage("Desconectado. Vuelve a introducir un JWT autorizado.");
  }, []);
  const connect = useCallback(async (input: string) => {
    const id = ++generation.current;
    pending.current?.abort();
    setSession(null);
    setMessage("");
    const controller = new AbortController();
    pending.current = controller;
    const token = input.trim();
    const claims = readClaims(token);
    const path = isInventory(claims)
      ? "/inventory/items?limit=1"
      : claims.role === "direction"
        ? "/incidents/metrics/open-by-severity"
        : "/management/catalogs?limit=1";
    await request(path, token, { signal: controller.signal });
    if (generation.current !== id || controller.signal.aborted) return;
    setSession({ token, claims, signal: controller.signal, id });
  }, []);
  const value = useMemo(
    () => ({ session, connect, disconnect, message }),
    [session, connect, disconnect, message],
  );
  return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function useSession() {
  const context = useContext(Context);
  if (!context) throw new Error("SessionProvider required");
  return context;
}
