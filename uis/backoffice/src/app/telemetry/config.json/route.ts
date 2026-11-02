export const dynamic = "force-dynamic";
export function GET(request: Request) {
  const endpoint = new URL("/telemetry/events", request.url).href;
  return Response.json(
    {
      enabled:
        ["development", "test"].includes(process.env.APP_ENVIRONMENT ?? "") &&
        process.env.TELEMETRY_ENABLED === "true",
      endpoint,
      environment: process.env.APP_ENVIRONMENT ?? "development",
    },
    { headers: { "Cache-Control": "no-store" } },
  );
}
