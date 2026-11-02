"use client";
import { useState, type FormEvent, type ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession } from "@/lib/auth/session";
import {
  isInventory,
  canReadAudit,
  canReadStock,
} from "@/lib/auth/presentation";
import { Alert, Button, Input, PageHeader } from "./ui";
export function AppShell({ children }: { children: ReactNode }) {
  const { session, disconnect, message } = useSession();
  const pathname = usePathname();
  const links = session
    ? isInventory(session.claims)
      ? [
          ["/inventory/items", "Catálogo"],
          ...(canReadStock(session.claims)
            ? [
                ["/inventory/stock", "Stock"],
                ["/inventory/reorder", "Reorden"],
              ]
            : []),
          ...(session.claims.role === "inventoryAuditor"
            ? [["/inventory/audit", "Auditoría"]]
            : []),
        ]
      : [
          ["/summary", "Resumen"],
          ["/incidents", "Incidencias"],
          ...(session.claims.role !== "direction"
            ? [
                ["/management/catalogs", "Catálogos"],
                ["/management/reference-data", "Maestros"],
              ]
            : []),
          ...(canReadAudit(session.claims)
            ? [["/management/audit", "Auditoría"]]
            : []),
        ]
    : [];
  return (
    <>
      <a className="skip-link" href="#workspace">
        Saltar al contenido
      </a>
      <header className="topbar">
        <Link
          href="/"
          className="brand"
          prefetch={false}
          aria-label="HealthCore Digital, inicio"
        >
          <span className="brand-mark">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M10 3h4v7h7v4h-7v7h-4v-7H3v-4h7Z" />
            </svg>
          </span>
          <span>
            <span className="brand-name">HealthCore</span>
            <span className="brand-unit">DIGITAL</span>
          </span>
        </Link>
        <nav aria-label="Navegación principal">
          {links.map(([href, label]) => (
            <Link
              key={href}
              href={href}
              prefetch={false}
              aria-current={pathname === href ? "page" : undefined}
            >
              {label}
            </Link>
          ))}
        </nav>
        <span className="environment-badge">Prototipo · datos sintéticos</span>
      </header>
      <main id="workspace" tabIndex={-1} className="page-shell">
        {session ? (
          <div key={session.id}>
            <div className="actions">
              <span>Conectado como {session.claims.role}</span>
              <Button secondary onClick={disconnect}>
                Desconectar
              </Button>
            </div>
            {children}
          </div>
        ) : (
          <ConnectView message={message} />
        )}
        <footer>
          <strong>HealthCore Digital</strong> · Soluciones digitales para
          nuestros equipos
          <br />
          Entorno de desarrollo · Datos sintéticos
          <p>
            El backoffice anterior sigue disponible. Cambiar de aplicación
            requiere reconectar.
          </p>
          <a href="/#/incidents">Incidencias anteriores</a>
          {" · "}
          <a href="/management/">Management anterior</a>
          {" · "}
          <a href="http://localhost:3000/internal/incident-history">
            Historial React existente (web local)
          </a>
        </footer>
      </main>
    </>
  );
}
function ConnectView({ message }: { message: string }) {
  const { connect } = useSession();
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    setError("");
    const value = token;
    setToken("");
    try {
      await connect(value);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo conectar.");
    } finally {
      setPending(false);
    }
  }
  return (
    <>
      <PageHeader title="Conectar con HealthCore" />
      <section className="panel connection-card">
        <h2>Conectar con la API</h2>
        <p>
          Introduce un JWT de desarrollo autorizado. El backend verifica
          identidad, permisos y ámbitos.
        </p>
        <form onSubmit={submit}>
          <Input
            label="JWT de desarrollo"
            type="password"
            autoComplete="off"
            required
            value={token}
            onChange={(e) => setToken(e.target.value)}
            hint="Sólo en memoria; se pierde al desconectar o recargar."
          />
          <div className="actions">
            <Button type="submit" disabled={pending}>
              {pending ? "Conectando…" : "Conectar"}
            </Button>
          </div>
        </form>
        {error && <Alert error>{error}</Alert>}
        {message && <Alert>{message}</Alert>}
      </section>
    </>
  );
}
