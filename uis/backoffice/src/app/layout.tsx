import type { Metadata } from "next";
import type { ReactNode } from "react";
import "@/styles/tokens.css";
import { SessionProvider } from "@/lib/auth/session";
import { TelemetryProvider } from "@/lib/telemetry/provider";
import { AppShell } from "@/components/app-shell";
export const metadata: Metadata = {
  title: "HealthCore · Backoffice",
  icons: { icon: "/next/favicon.svg" },
  robots: { index: false, follow: false },
};
export default function Layout({ children }: { children: ReactNode }) {
  return (
    <html lang="es">
      <body>
        <SessionProvider>
          <TelemetryProvider>
            <AppShell>{children}</AppShell>
          </TelemetryProvider>
        </SessionProvider>
      </body>
    </html>
  );
}
