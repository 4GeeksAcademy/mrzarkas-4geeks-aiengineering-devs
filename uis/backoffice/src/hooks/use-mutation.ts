"use client";
import { useRef, useState } from "react";
import { ApiError, request } from "@/lib/api/client";
import { useSession } from "@/lib/auth/session";
export function useMutation() {
  const { session, disconnect } = useSession();
  const gate = useRef(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [success, setSuccess] = useState("");
  async function mutate<T>(
    path: string,
    body: unknown,
    method: "POST" | "PATCH" = "POST",
    validate?: (data: unknown) => void,
    onFailure?: (error: ApiError) => void,
    inventoryFlowId?: string,
  ): Promise<T | undefined> {
    if (!session || gate.current || error?.uncertain) return;
    gate.current = true;
    setPending(true);
    setError(null);
    setSuccess("");
    try {
      const data = await request<T>(path, session.token, {
        method,
        body,
        inventoryFlowId,
        signal: session.signal,
        onUnauthorized: disconnect,
      });
      validate?.(data);
      if (!session.signal.aborted) {
        setSuccess("La API confirmó la operación.");
        return data;
      }
    } catch (e) {
      if (!session.signal.aborted) {
        const failure =
          e instanceof ApiError
            ? e
            : new ApiError(0, "No se pudo completar la operación.", true);
        onFailure?.(failure);
        setError(failure);
      }
    } finally {
      gate.current = false;
      if (!session.signal.aborted) setPending(false);
    }
  }
  // Explicit user acknowledgement after consulting the authoritative data, never an automatic retry.
  function acknowledge() {
    setError(null);
    setSuccess(
      "Verificación reconocida. Revisa los datos antes de iniciar una nueva operación.",
    );
  }
  return { mutate, pending, error, success, acknowledge };
}
