"use client";
import { ErrorState } from "@/components/ui";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <ErrorState
      error={
        new Error("No se pudo mostrar la página. Puedes volver a cargarla.")
      }
      retry={reset}
    />
  );
}
