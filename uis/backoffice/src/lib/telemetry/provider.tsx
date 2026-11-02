"use client";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { usePathname } from "next/navigation";
import { useSession } from "@/lib/auth/session";
import { isInventory } from "@/lib/auth/presentation";
import { createInventoryFlows, type InventoryFlows } from "./inventory-flow";
type Service = {
  connect: (api: string, token: string) => Promise<boolean>;
  activateClinic: (id: string | null) => Promise<boolean>;
  navigate: (view: string) => void;
  disconnect: () => void;
  destroy: () => void;
};
const Binding = createContext<(clinic: string | null) => void>(() => {});
const InventoryBinding = createContext<InventoryFlows | null>(null);
export function TelemetryProvider({ children }: { children: ReactNode }) {
  const { session } = useSession();
  const pathname = usePathname();
  const [clinic, setClinic] = useState<{
    path: string;
    clinic: string | null;
  } | null>(null);
  const [ready, setReady] = useState(0);
  const service = useRef<Service | null>(null);
  const [flows, setFlows] = useState<InventoryFlows | null>(null);
  useEffect(() => {
    if (!session || !isInventory(session.claims)) { setFlows(null); return; }
    const own = createInventoryFlows(session.token, session.signal);
    setFlows(own);
    return () => own.stop();
  }, [session]);
  const application = pathname.startsWith("/management/")
    ? "management"
    : "incidents";
  useEffect(() => {
    if (!session || isInventory(session.claims)) return;
    let active = true;
    let own: Service | null = null;
    const modulePath = "/next/telemetry/runtime.js";
    void import(/* webpackIgnore: true */ modulePath)
      .then(
        async (runtime: {
          bootstrapTelemetry: (app: string) => Promise<Service>;
        }) => {
          own = await runtime.bootstrapTelemetry(application);
          if (!active || session.signal.aborted) {
            own.destroy();
            return;
          }
          // The existing public module resolves config and schemas; credentials stay in its memory only.
          const connected = await own.connect(
            window.location.origin,
            session.token,
          );
          if (!active || session.signal.aborted) {
            own.destroy();
            return;
          }
          if (connected) {
            service.current = own;
            setReady((x) => x + 1);
          }
        },
      )
      .catch(() => {});
    return () => {
      active = false;
      own?.disconnect();
      own?.destroy();
      service.current = null;
    };
  }, [session, application]);
  useEffect(() => {
    const current = service.current;
    if (!current || !session) return;
    let active = true;
    const view = pathname.startsWith("/management/")
      ? "management"
      : pathname === "/incidents"
        ? "incident_queue"
        : pathname === "/incidents/new"
          ? "incident_create"
          : pathname.startsWith("/incidents/") &&
              clinic?.path === pathname &&
              clinic.clinic
            ? "incident_detail"
            : null;
    const bound = view === "incident_detail" ? (clinic?.clinic ?? null) : null;
    if (view)
      void current
        .activateClinic(bound)
        .then((ok) => {
          if (active && ok && !session.signal.aborted) current.navigate(view);
        })
        .catch(() => {});
    return () => {
      active = false;
    };
  }, [pathname, clinic, ready, session]);
  const bind = useCallback(
    (value: string | null) => setClinic({ path: pathname, clinic: value }),
    [pathname],
  );
  return <InventoryBinding.Provider value={flows}><Binding.Provider value={bind}>{children}</Binding.Provider></InventoryBinding.Provider>;
}
export function useInventoryFlows() { return useContext(InventoryBinding); }
export function useTelemetryClinic(clinic: string | null) {
  const bind = useContext(Binding);
  useEffect(() => {
    bind(clinic);
    return () => bind(null);
  }, [clinic, bind]);
}
