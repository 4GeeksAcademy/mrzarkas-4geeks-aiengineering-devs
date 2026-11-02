import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { it, expect, vi } from "vitest";
import { SessionProvider, useSession } from "@/lib/auth/session";
import { useQuery } from "@/hooks/use-query";
import { useMutation } from "@/hooks/use-mutation";
const token = `x.${btoa(JSON.stringify({ role: "direction" }))}.x`;
function View() {
  const { session, connect, disconnect } = useSession();
  const q = useQuery<{ secret: string }>(session ? "/incidents" : null);
  const m = useMutation();
  return (
    <>
      <button onClick={() => void connect(token)}>connect</button>
      <button onClick={disconnect}>disconnect</button>
      <button
        disabled={m.pending || m.error?.uncertain}
        onClick={() => void m.mutate("/incidents", { title: "Synthetic" })}
      >
        write
      </button>
      <span>{session ? "connected" : "offline"}</span>
      <span>{q.data?.secret}</span>
      {m.error && <p>{m.error.message}</p>}
    </>
  );
}
it("does not resurrect data from a late response after logout", async () => {
  let resolve: (r: Response) => void = () => {};
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation((url: string) =>
      url.includes("/metrics/")
        ? Promise.resolve(Response.json([]))
        : new Promise<Response>((r) => {
            resolve = r;
          }),
    ),
  );
  render(
    <SessionProvider>
      <View />
    </SessionProvider>,
  );
  fireEvent.click(screen.getByText("connect"));
  await screen.findByText("connected");
  fireEvent.click(screen.getByText("disconnect"));
  resolve(Response.json({ secret: "synthetic-old-identity" }));
  await waitFor(() => expect(screen.getByText("offline")).toBeVisible());
  expect(screen.queryByText("synthetic-old-identity")).toBeNull();
  expect(localStorage.length).toBe(0);
});
it("blocks repeated submission after an uncertain write", async () => {
  const fetcher = vi
    .fn()
    .mockImplementation((_: string, options: RequestInit) =>
      options.method === "POST"
        ? Promise.reject(new TypeError("Synthetic lost response"))
        : Promise.resolve(Response.json([])),
    );
  vi.stubGlobal("fetch", fetcher);
  render(
    <SessionProvider>
      <View />
    </SessionProvider>,
  );
  fireEvent.click(screen.getByText("connect"));
  await screen.findByText("connected");
  fireEvent.click(screen.getByText("write"));
  await screen.findByText(/Resultado incierto/);
  expect(screen.getByText("write")).toBeDisabled();
  expect(
    fetcher.mock.calls.filter(([, o]) => o.method === "POST"),
  ).toHaveLength(1);
});
