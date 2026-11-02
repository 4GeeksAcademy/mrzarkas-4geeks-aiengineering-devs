import { forward } from "@/lib/api/forward";
export const dynamic = "force-dynamic";
async function handle(
  request: Request,
  { params }: { params: Promise<{ path: string[] }> },
) {
  return forward(request, (await params).path);
}
export { handle as GET, handle as POST, handle as PATCH };
