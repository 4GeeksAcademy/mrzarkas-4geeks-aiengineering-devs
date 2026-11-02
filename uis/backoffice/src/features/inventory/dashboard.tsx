"use client";
import Link from "next/link";
import { useQuery } from "@/hooks/use-query";
import { useSession } from "@/lib/auth/session";
import { isInventory, canReadStock } from "@/lib/auth/presentation";
import type { Item, Stock } from "@/lib/api/types";
import {
  Alert,
  Button,
  ErrorState,
  LoadingState,
  PageHeader,
} from "@/components/ui";
import { ReceivedAt } from "./format";

export function InventoryDashboard() {
  const { session } = useSession();
  const allowed = !!session && isInventory(session.claims);
  const clinical = !!session && canReadStock(session.claims);
  const items = useQuery<Item[]>(
    allowed ? "/inventory/items?offset=0&limit=50" : null,
  );
  const stock = useQuery<Stock[]>(
    clinical ? "/inventory/stock?offset=0&limit=50" : null,
  );
  const reorder = useQuery<Stock[]>(
    clinical ? "/inventory/reorder?offset=0&limit=50" : null,
  );
  return (
    <>
      <PageHeader title="Resumen de inventario" />
      {!allowed ? (
        <Alert error>Tu perfil no dispone de Inventory.</Alert>
      ) : (
        <>
          <p className="notice">
            Primera página de cada consulta (máximo 50 filas), exclusivamente
            del ámbito autorizado. Los conteos son parciales y no un snapshot
            global. No se suman unidades de artículos diferentes. Una alerta no
            es un pedido.
          </p>
          <Button
            secondary
            onClick={() => {
              items.refresh();
              stock.refresh();
              reorder.refresh();
            }}
          >
            Actualizar resumen
          </Button>
          <div className="metrics-grid">
            {[
              {
                title: "Artículos recibidos",
                query: items,
                link: "/inventory/items",
              },
              ...(clinical
                ? [
                    {
                      title: "Posiciones recibidas",
                      query: stock,
                      link: "/inventory/stock",
                    },
                    {
                      title: "Necesidades de reposición recibidas",
                      query: reorder,
                      link: "/inventory/reorder",
                    },
                  ]
                : []),
            ].map(({ title, query, link }) => (
              <section key={title} className="panel">
                <h2>{title}</h2>
                {query.loading && <LoadingState />}
                {query.error && (
                  <>
                    <p>No disponible</p>
                    <ErrorState error={query.error} retry={query.refresh} />
                  </>
                )}
                {query.data && (
                  <>
                    <p className="metric-count">{query.data.length}</p>
                    <ReceivedAt data={query.data} />
                  </>
                )}
                <Link href={link} prefetch={false}>
                  Consultar páginas
                </Link>
              </section>
            ))}
          </div>
        </>
      )}
    </>
  );
}
