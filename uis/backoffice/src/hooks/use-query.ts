"use client";
import { useCallback, useEffect, useState } from "react";
import { ApiError, request } from "@/lib/api/client";
import { useSession } from "@/lib/auth/session";
export function useQuery<T>(path: string | null) {
  const { session, disconnect } = useSession();
  const [revision, setRevision] = useState(0);
  const [result, setResult] = useState<{
    path: string;
    id: number;
    data?: T;
    error?: ApiError;
    loading: boolean;
  } | null>(null);
  const refresh = useCallback(() => setRevision((x) => x + 1), []);
  useEffect(() => {
    if (!path || !session) {
      setResult(null);
      return;
    }
    const controller = new AbortController();
    let active = true;
    setResult({ path, id: session.id, loading: true });
    const signal = AbortSignal.any([controller.signal, session.signal]);
    void request<T>(path, session.token, { signal, onUnauthorized: disconnect })
      .then((data) => {
        if (active && !signal.aborted)
          setResult({ path, id: session.id, data, loading: false });
      })
      .catch((error) => {
        if (active && !signal.aborted)
          setResult({
            path,
            id: session.id,
            error:
              error instanceof ApiError
                ? error
                : new ApiError(0, "No se pudo consultar la API."),
            loading: false,
          });
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [path, session, disconnect, revision]);
  const current =
    result?.path === path && result.id === session?.id ? result : null;
  return {
    data: current?.data,
    error: current?.error,
    loading: !!(path && session) && (!current || current.loading),
    refresh,
  };
}
