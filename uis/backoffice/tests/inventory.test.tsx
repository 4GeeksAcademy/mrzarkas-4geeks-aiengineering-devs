import {
  render,
  screen,
  fireEvent,
  waitFor,
  within,
} from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import { integer, presentation } from "@/features/inventory/format";
import { ClinicalActions } from "@/features/inventory/clinical-actions";
import { ClinicSelector } from "@/features/inventory/context-selector";
import { InventoryOperations } from "@/features/inventory/operation-state";
import { OperationForm } from "@/features/inventory/forms";
import { InventoryDashboard } from "@/features/inventory/dashboard";
import type { Item, Stock, Schema } from "@/lib/api/types";

const clinic = "10000000-0000-4000-8000-000000000001";
const other = "10000000-0000-4000-8000-000000000002";
const itemId = "20000000-0000-4000-8000-000000000001";
const moveId = "30000000-0000-4000-8000-000000000001";
const sessionMock = vi.hoisted(() => ({
  role: "inventoryManager",
  clinics: [] as string[],
  signal: new AbortController().signal,
}));
vi.mock("@/lib/auth/session", () => {
  const session = {
    id: 1,
    token: "synthetic-only",
    signal: sessionMock.signal,
    claims: {
      get role() {
        return sessionMock.role;
      },
      get clinic_ids() {
        return sessionMock.clinics;
      },
      jurisdiction_ids: [],
    },
  };
  const disconnect = vi.fn();
  return { useSession: () => ({ session, disconnect }) };
});
const item: Item = {
  id: itemId,
  title: "Synthetic gauze",
  product_code: "SYN-QA",
  unit: "piece",
  uses_lots: false,
  pack_label: "pack",
  pack_size: 10,
  is_active: true,
  created_by: clinic,
  created_at: "2026-11-02T10:00:00Z",
};
const stock: Stock = {
  item_id: itemId,
  clinic_id: clinic,
  lot_id: null,
  quantity: 20,
  unit: "piece",
  pack_label: "pack",
  pack_size: 10,
  complete_packs: 2,
  remaining_units: 0,
  reorder_point: 20,
  below_reorder: false,
};
const movement: Schema<"MovementRead"> = {
  id: moveId,
  item_id: itemId,
  clinic_id: clinic,
  lot_id: null,
  kind: "adjust",
  delta: -1,
  unit: "piece",
  pack_label: "pack",
  pack_size: 10,
  previous_quantity: 20,
  counted_quantity: 19,
  resulting_quantity: 19,
  correction_of: null,
  reason: "[REDACTED]",
  jurisdiction_id: clinic,
  jurisdiction_key: "US",
  result: "accepted",
  actor_id: clinic,
  occurred_at: "2026-11-02T10:00:00Z",
  retention_until: "2028-11-02T10:00:00Z",
};
function actions(props: Partial<Parameters<typeof ClinicalActions>[0]> = {}) {
  return (
    <InventoryOperations>
      <ClinicalActions
        item={item}
        clinic={clinic}
        lot=""
        stock={stock}
        history={[movement]}
        refresh={vi.fn()}
        {...props}
      />
    </InventoryOperations>
  );
}
function confirm(name: string) {
  fireEvent.click(screen.getByRole("button", { name }));
  fireEvent.click(
    within(screen.getByRole("dialog")).getByRole("button", {
      name: "Confirmar",
    }),
  );
}
beforeEach(() => {
  sessionMock.role = "inventoryManager";
  sessionMock.clinics = [clinic];
  Object.defineProperty(HTMLDialogElement.prototype, "showModal", {
    configurable: true,
    value() {
      this.setAttribute("open", "");
    },
  });
  Object.defineProperty(HTMLDialogElement.prototype, "close", {
    configurable: true,
    value() {
      this.removeAttribute("open");
    },
  });
});
it.each(["", " ", "0", "-1", "1.5", "1000000001"])(
  "rejects invalid movement amount %s without truncation",
  (value) => {
    expect(() => integer(value)).toThrow();
  },
);
it("allows zero only for physical counts and validates presentation removal", () => {
  expect(integer("0", 0)).toBe(0);
  expect(integer("3")).toBe(3);
  const data = new FormData();
  data.set("pack_size", "10");
  expect(() => presentation(data)).toThrow();
  data.set("pack_label", " pack ");
  expect(presentation(data)).toEqual({ pack_label: "pack", pack_size: 10 });
  data.set("pack_label", "");
  data.set("pack_size", "1");
  expect(presentation(data).pack_label).toBeNull();
});
it("limits clinical options to assigned clinics including empty scope", () => {
  const { rerender } = render(<ClinicSelector value="" onChange={vi.fn()} />);
  expect(screen.getByRole("option", { name: clinic })).toBeVisible();
  expect(screen.queryByRole("option", { name: other })).toBeNull();
  sessionMock.clinics = [];
  rerender(<ClinicSelector value="" onChange={vi.fn()} />);
  expect(screen.getAllByRole("option")).toHaveLength(1);
});
it("confirms pack conversion and clinic, then submits one exact payload", async () => {
  const fetcher = vi.fn().mockResolvedValue(
    Response.json({
      ...movement,
      kind: "in",
      delta: 30,
      previous_quantity: 20,
      resulting_quantity: 50,
    }),
  );
  vi.stubGlobal("fetch", fetcher);
  render(actions());
  fireEvent.change(screen.getByLabelText("Cantidad", { exact: true }), {
    target: { value: "3" },
  });
  fireEvent.change(screen.getByLabelText("Unidad del movimiento"), {
    target: { value: "pack" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Registrar entrada o salida" }),
  );
  const dialog = screen.getByRole("dialog");
  expect(within(dialog).getByText(/3 × 10 = 30 piece/)).toBeVisible();
  expect(within(dialog).getByText(new RegExp(clinic))).toBeVisible();
  const button = within(dialog).getByRole("button", { name: "Confirmar" });
  fireEvent.click(button);
  fireEvent.click(button);
  await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(1));
  expect(JSON.parse(fetcher.mock.calls[0][1].body)).toEqual({
    item_id: itemId,
    clinic_id: clinic,
    kind: "in",
    quantity: 3,
    unit: "pack",
    reason: null,
  });
  await screen.findByText(/Saldo resultante 50/);
});
it("shows count delta preview but authoritative concurrent result wins", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      Response.json({
        ...movement,
        previous_quantity: 25,
        counted_quantity: 0,
        delta: -25,
        resulting_quantity: 0,
      }),
    ),
  );
  render(actions());
  fireEvent.change(screen.getByLabelText("Cantidad contada en unidades base"), {
    target: { value: "0" },
  });
  fireEvent.change(screen.getByLabelText("Motivo del conteo"), {
    target: { value: "Synthetic recount" },
  });
  expect(screen.getAllByText(/Diferencia prevista: -20/)[0]).toBeVisible();
  confirm("Registrar conteo físico");
  await screen.findByText(
    /Saldo previo 25 · Diferencia -25 · Saldo resultante 0/,
  );
});
it("requires loaded original and links its compensation response", async () => {
  const fetcher = vi.fn().mockResolvedValue(
    Response.json({
      ...movement,
      id: other,
      kind: "correction",
      correction_of: moveId,
      delta: 1,
      resulting_quantity: 21,
    }),
  );
  vi.stubGlobal("fetch", fetcher);
  render(actions());
  expect(
    screen.getByRole("button", { name: "Compensar movimiento" }),
  ).toBeDisabled();
  fireEvent.change(screen.getByLabelText("UUID del movimiento original"), {
    target: { value: moveId },
  });
  fireEvent.change(screen.getByLabelText("Motivo de compensación"), {
    target: { value: "Synthetic correction" },
  });
  confirm("Compensar movimiento");
  await screen.findByText(new RegExp(`Compensa ${moveId}`));
  expect(fetcher.mock.calls[0][0]).toContain(`/movements/${moveId}/correction`);
});
it("blocks writes without stock, lot or assigned clinic", () => {
  const { rerender } = render(actions({ stock: undefined }));
  expect(
    screen.getByRole("button", { name: "Registrar entrada o salida" }),
  ).toBeDisabled();
  rerender(actions({ item: { ...item, uses_lots: true }, lot: "" }));
  expect(
    screen.getByRole("button", { name: "Registrar conteo físico" }),
  ).toBeDisabled();
  rerender(actions({ clinic: other }));
  expect(
    screen.getByRole("button", { name: "Configurar punto de reorden" }),
  ).toBeDisabled();
});
it.each(["lost", "invalid", "5xx"])(
  "keeps uncertain %s operation across feature navigation and blocks another form",
  async (scenario) => {
    const fetcher = vi
      .fn()
      .mockImplementation(() =>
        scenario === "lost"
          ? Promise.reject(new TypeError("Synthetic lost response"))
          : Promise.resolve(
              Response.json(
                scenario === "invalid" ? {} : { detail: "Synthetic failure" },
                { status: scenario === "5xx" ? 503 : 201 },
              ),
            ),
      );
    vi.stubGlobal("fetch", fetcher);
    const view = (name: string) => (
      <InventoryOperations>
        <OperationForm
          title={name}
          path="/inventory/items"
          body={() => ({ title: "Synthetic" })}
          refresh={vi.fn()}
        >
          {null}
        </OperationForm>
      </InventoryOperations>
    );
    const { rerender } = render(view("First"));
    fireEvent.click(screen.getByRole("button", { name: "First" }));
    await screen
      .findByRole("region", { name: "Resultado de operación desconocido" })
      .catch(() =>
        screen.findByLabelText("Resultado de operación desconocido"),
      );
    rerender(view("Second"));
    expect(screen.getByRole("button", { name: "Second" })).toBeDisabled();
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(localStorage.length).toBe(0);
  },
);
it("dashboard has page counts, partial failure and no clinical request for admin", async () => {
  sessionMock.role = "inventoryAdmin";
  const fetcher = vi.fn().mockResolvedValue(Response.json([item]));
  vi.stubGlobal("fetch", fetcher);
  const { unmount } = render(<InventoryDashboard />);
  await screen.findByText("1");
  expect(fetcher.mock.calls.every(([url]) => url.includes("/items"))).toBe(
    true,
  );
  unmount();
  sessionMock.role = "inventoryManager";
  fetcher.mockImplementation((url: string) =>
    url.includes("/reorder")
      ? Promise.resolve(Response.json({}, { status: 503 }))
      : Promise.resolve(
          Response.json(url.includes("/stock") ? [stock] : [item]),
        ),
  );
  render(<InventoryDashboard />);
  await screen.findByText("No disponible");
  expect(screen.getAllByText("1")).toHaveLength(2);
  expect(screen.getByText(/conteos son parciales/)).toBeVisible();
});

it("retains a lost response when the originating form unmounts while pending", async () => {
  let reject: (e: Error) => void = () => {};
  const fetcher = vi.fn().mockImplementation(
    () =>
      new Promise((_resolve, r) => {
        reject = r;
      }),
  );
  vi.stubGlobal("fetch", fetcher);
  const view = (old: boolean) => (
    <InventoryOperations>
      {old ? (
        <OperationForm
          key="old"
          title="Old"
          path="/inventory/items"
          body={() => ({ title: "Synthetic" })}
          refresh={vi.fn()}
        >
          {null}
        </OperationForm>
      ) : (
        <OperationForm
          key="new"
          title="New"
          path="/inventory/items"
          body={() => ({ title: "Synthetic" })}
          refresh={vi.fn()}
        >
          {null}
        </OperationForm>
      )}
    </InventoryOperations>
  );
  const { rerender } = render(view(true));
  fireEvent.click(screen.getByRole("button", { name: "Old" }));
  rerender(view(false));
  reject(new TypeError("Synthetic delayed response loss"));
  await screen.findByRole("region", {
    name: "Resultado de operación desconocido",
  });
  expect(screen.getByRole("button", { name: "New" })).toBeDisabled();
  expect(fetcher).toHaveBeenCalledTimes(1);
});
