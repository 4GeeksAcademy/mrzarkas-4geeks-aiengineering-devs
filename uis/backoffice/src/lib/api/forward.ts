import contract from "../../../contracts/openapi.json";
const privateHeaders = {
  "Cache-Control": "private, no-store",
  "Content-Type": "application/json",
  "X-Content-Type-Options": "nosniff",
};
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const modules = [
  "incidents",
  "catalogs",
  "management",
  "inventory",
  "telemetry",
];
const managementReads = [
  "/management/catalogs",
  "/management/reference-data/{resource}",
  "/management/audit-events",
];
export function allowedRoute(
  segments: string[],
  method: string,
): string | null {
  if (
    !modules.includes(segments[0]) ||
    !["GET", "POST", "PATCH"].includes(method)
  )
    return null;
  for (const [template, operation] of Object.entries(contract.paths)) {
    if (!(method.toLowerCase() in operation)) continue;
    if (
      segments[0] === "management" &&
      (method !== "GET" || !managementReads.includes(template))
    )
      continue;
    const parts = template.slice(1).split("/");
    if (parts.length !== segments.length) continue;
    if (
      parts.every((p, i) =>
        p.startsWith("{")
          ? p === "{catalog_name}"
            ? [
                "incidentStatus",
                "severity",
                "entryChannel",
                "incidentType",
              ].includes(segments[i])
            : p === "{resource}"
              ? [
                  "jurisdictions",
                  "clinics",
                  "affected-systems",
                  "responsible-areas",
                ].includes(segments[i])
              : uuid.test(segments[i])
          : p === segments[i],
      )
    )
      return template;
  }
  return null;
}
async function boundedBody(request: Request): Promise<Uint8Array | undefined> {
  if (request.method === "GET") return undefined;
  const reader = request.body?.getReader();
  if (!reader) return new Uint8Array();
  let size = 0;
  const chunks: Uint8Array[] = [];
  while (true) {
    const part = await reader.read();
    if (part.done) break;
    size += part.value.byteLength;
    if (size > 64 * 1024) {
      await reader.cancel();
      throw new RangeError();
    }
    chunks.push(part.value);
  }
  const data = new Uint8Array(size);
  let at = 0;
  for (const chunk of chunks) {
    data.set(chunk, at);
    at += chunk.length;
  }
  return data;
}
export async function forward(
  request: Request,
  segments: string[],
  fetcher: typeof fetch = fetch,
): Promise<Response> {
  const json = (status: number, detail: string) =>
    Response.json({ detail }, { status, headers: privateHeaders });
  if (!["development", "test"].includes(process.env.APP_ENVIRONMENT ?? ""))
    return json(503, "Synthetic development environment required");
  const template = allowedRoute(segments, request.method);
  if (!template) return json(404, "Not found");
  const bearer = request.headers.get("authorization");
  if (!bearer?.startsWith("Bearer "))
    return json(401, "Authentication required");
  let upstream: URL;
  try {
    upstream = new URL(process.env.BACKEND_URL ?? "http://127.0.0.1:8000");
    if (
      !["http:", "https:"].includes(upstream.protocol) ||
      upstream.username ||
      upstream.password ||
      upstream.search ||
      upstream.hash ||
      upstream.pathname !== "/"
    )
      throw new Error();
  } catch {
    return json(503, "API unavailable");
  }
  upstream.pathname = "/" + segments.map(encodeURIComponent).join("/");
  upstream.search = new URL(request.url).search;
  try {
    const body = await boundedBody(request);
    const response = await fetcher(upstream, {
      method: request.method,
      headers: {
        Authorization: bearer,
        ...(body ? { "Content-Type": "application/json" } : {}),
        ...(request.headers.has("x-telemetry-context")
          ? {
              "X-Telemetry-Context": request.headers.get(
                "x-telemetry-context",
              )!,
            }
          : {}),
      },
      body: body as BodyInit | undefined,
      redirect: "error",
      cache: "no-store",
      signal: AbortSignal.any([request.signal, AbortSignal.timeout(10000)]),
    });
    // Only the reviewed JSON API is forwarded. Never pass cookies or arbitrary upstream headers.
    if (!response.headers.get("content-type")?.includes("application/json"))
      return json(503, "API unavailable");
    return new Response(await response.arrayBuffer(), {
      status: response.status,
      headers: privateHeaders,
    });
  } catch (e) {
    return e instanceof RangeError
      ? json(413, "Payload too large")
      : json(503, "API unavailable");
  }
}
