export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public uncertain = false,
    public fields: Record<string, string> = {},
  ) {
    super(message);
  }
}
const messages: Record<number, string> = {
  401: "La conexión ha caducado o el JWT es inválido. Vuelve a conectar.",
  403: "La API ha denegado el acceso por permisos o ámbito.",
  404: "El recurso no existe o no está disponible.",
  409: "La operación entra en conflicto con el estado actual. Consulta los datos antes de continuar.",
  422: "La API rechazó los datos. Revisa los campos indicados.",
  503: "La API no está disponible.",
};
export async function request<T>(
  path: string,
  token: string,
  options: {
    method?: "GET" | "POST" | "PATCH";
    body?: unknown;
    inventoryFlowId?: string;
    signal?: AbortSignal;
    onUnauthorized?: () => void;
  } = {},
): Promise<T> {
  const method = options.method ?? "GET";
  const write = method !== "GET";
  let response: Response;
  try {
    response = await fetch(`/next/api-core${path}`, {
      method,
      cache: "no-store",
      redirect: "error",
      headers: {
        Authorization: `Bearer ${token}`,
        ...(path === "/inventory/movements" && method === "POST" && /^ps_[0-9a-f]{64}$/.test(options.inventoryFlowId ?? "")
          ? { "X-Inventory-Flow-Id": options.inventoryFlowId! } : {}),
        ...(options.body !== undefined
          ? { "Content-Type": "application/json" }
          : {}),
      },
      body:
        options.body !== undefined ? JSON.stringify(options.body) : undefined,
      signal: options.signal
        ? AbortSignal.any([options.signal, AbortSignal.timeout(15000)])
        : AbortSignal.timeout(15000),
    });
  } catch (error) {
    if (!write && options.signal?.aborted) throw error;
    throw new ApiError(
      0,
      write
        ? "Resultado incierto. La solicitud pudo aplicarse. Consulta el historial antes de volver a enviar."
        : "No se pudo consultar la API. Puedes reintentar la lectura.",
      write,
    );
  }
  if (!response.ok) {
    if (response.status === 401) options.onUnauthorized?.();
    const fields: Record<string, string> = {};
    if (response.status === 422) {
      try {
        const value = (await response.json()) as { detail?: unknown };
        if (Array.isArray(value.detail))
          for (const issue of value.detail) {
            if (issue && Array.isArray(issue.loc)) {
              const field = issue.loc.at(-1);
              if (typeof field === "string")
                fields[field] = "El valor no cumple el contrato de la API.";
            }
          }
      } catch {
        /* Never include response bodies in logs. */
      }
    }
    const uncertain = write && response.status >= 500;
    throw new ApiError(
      response.status,
      uncertain
        ? "Resultado incierto. Verifica el historial y los datos antes de repetir la operación."
        : (messages[response.status] ??
            `La API respondió con error ${response.status}.`),
      uncertain,
      fields,
    );
  }
  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError(
      0,
      write
        ? "Resultado incierto: la respuesta no pudo leerse. Verifica los datos antes de repetir."
        : "La API devolvió una respuesta inválida.",
      write,
    );
  }
}
