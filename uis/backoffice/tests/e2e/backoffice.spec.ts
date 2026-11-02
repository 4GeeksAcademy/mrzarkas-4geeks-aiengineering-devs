import {
  test,
  expect,
  type APIRequestContext,
  type Page,
} from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import type {
  Schema,
  Item,
  Incident,
  Reference,
} from "../../src/lib/api/types";
const api = process.env.BACKOFFICE_TEST_API ?? "http://127.0.0.1:18190";
const actor = "00000000-0000-4000-8000-000000000123";
const code = () => `SYN-QA-${Date.now()}-${Math.floor(Math.random() * 100000)}`;
async function token(
  request: APIRequestContext,
  role: string,
  scope: Record<string, unknown> = {},
) {
  const r = await request.post(`${api}/auth/tokens`, {
    data: { actor_id: actor, role, ...scope },
  });
  expect(r.status()).toBe(201);
  return ((await r.json()) as { access_token: string }).access_token;
}
async function get<T>(
  request: APIRequestContext,
  path: string,
  bearer: string,
) {
  const r = await request.get(`${api}${path}`, {
    headers: { Authorization: `Bearer ${bearer}` },
  });
  expect(r.status()).toBe(200);
  return (await r.json()) as T;
}
async function connect(page: Page, bearer: string, path = "/next") {
  await page.goto(path);
  await page.getByLabel("JWT de desarrollo").fill(bearer);
  await page.getByRole("button", { name: "Conectar", exact: true }).click();
  await expect(page.getByRole("button", { name: "Desconectar" })).toBeVisible();
}
async function seed(request: APIRequestContext) {
  const admin = await token(request, "admin");
  const refs = await get<Schema<"ReferenceValueListResponse">>(
    request,
    "/management/reference-data/clinics?limit=100",
    admin,
  );
  const us = refs.items.find((r) => r.key === "dev-us-clinic-01")!;
  const uk = refs.items.find((r) => r.key === "dev-uk-clinic-01")!;
  const areas = (
    await get<Schema<"ReferenceValueListResponse">>(
      request,
      "/management/reference-data/responsible-areas",
      admin,
    )
  ).items;
  const systems = (
    await get<Schema<"ReferenceValueListResponse">>(
      request,
      "/management/reference-data/affected-systems",
      admin,
    )
  ).items;
  const catalog = async (name: string) =>
    (await get<Schema<"CatalogResponse">>(request, `/catalogs/${name}`, admin))
      .values;
  return {
    admin,
    us,
    uk,
    areas,
    systems,
    status: await catalog("incidentStatus"),
    severity: await catalog("severity"),
    channel: await catalog("entryChannel"),
    type: await catalog("incidentType"),
  };
}
async function createIncident(
  request: APIRequestContext,
  s: Awaited<ReturnType<typeof seed>>,
  area: Reference,
) {
  const r = await request.post(`${api}/incidents`, {
    headers: { Authorization: `Bearer ${s.admin}` },
    data: {
      title: "Synthetic API fixture",
      description: "Synthetic operational issue without patient data",
      clinic_id: s.us.id,
      jurisdiction_id: s.us.jurisdiction_id,
      affected_system_id: s.systems.find((r) => r.key.includes("us"))!.id,
      responsible_area_id: area.id,
      severity_value_id: s.severity[0].id,
      entry_channel_value_id: s.channel[0].id,
      incident_type_value_id: s.type[0].id,
    },
  });
  expect(r.status()).toBe(201);
  return (await r.json()) as Incident;
}
async function createItem(
  request: APIRequestContext,
  options: Partial<Schema<"ItemCreate">> = {},
) {
  const bearer = await token(request, "inventoryAdmin");
  const r = await request.post(`${api}/inventory/items`, {
    headers: { Authorization: `Bearer ${bearer}` },
    data: {
      title: "Synthetic QA article",
      product_code: code(),
      unit: "piece",
      ...options,
    },
  });
  expect(r.status()).toBe(201);
  return (await r.json()) as Item;
}

test("Management read parity, safe table text and responsive accessibility", async ({
  page,
  request,
}) => {
  const s = await seed(request);
  await connect(page, s.admin, "/next/management/catalogs");
  await expect(page.getByRole("table")).toBeVisible();
  await expect(
    page.getByRole("columnheader", { name: "catalog_name" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Maestros", exact: true }).click();
  for (const resource of [
    "jurisdictions",
    "clinics",
    "affected-systems",
    "responsible-areas",
  ]) {
    await page.getByLabel("Recurso").selectOption(resource);
    await page.getByRole("button", { name: "Consultar", exact: true }).click();
    await expect(page.getByRole("table")).toBeVisible();
  }
  await page.getByRole("link", { name: "Auditoría", exact: true }).click();
  await page.getByRole("button", { name: "Consultar eventos" }).click();
  await expect(
    page
      .getByRole("table")
      .or(page.getByText(/Sin resultados/))
      .first(),
  ).toBeVisible();
  for (const width of [1350, 393, 320]) {
    await page.setViewportSize({ width, height: 900 });
    const result = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
      .analyze();
    expect(
      result.violations.map((v) => ({ id: v.id, impact: v.impact })),
    ).toEqual([]);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
  }
  await page.keyboard.press("Tab");
  expect(await page.evaluate(() => document.activeElement?.tagName)).not.toBe(
    "BODY",
  );
  await expect(
    page.getByRole("link", { name: "Incidencias anteriores" }),
  ).toHaveAttribute("href", "/#/incidents");
});

test("JWT input is cleared, reload disconnects, and invalid token cannot connect", async ({
  page,
  request,
}) => {
  await page.goto("/next");
  await page.getByLabel("JWT de desarrollo").fill("invalid.synthetic.jwt");
  await page.getByRole("button", { name: "Conectar", exact: true }).click();
  await expect(page.locator("main").getByRole("alert")).toBeVisible();
  await expect(page.getByLabel("JWT de desarrollo")).toHaveValue("");
  const bearer = await token(request, "direction");
  await connect(page, bearer);
  expect(
    await page.evaluate(() => ({
      local: localStorage.length,
      session: sessionStorage.length,
      cookies: document.cookie,
    })),
  ).toEqual({ local: 0, session: 0, cookies: "" });
  await page.reload();
  await expect(page.getByLabel("JWT de desarrollo")).toBeVisible();
});

test("Direction has only summaries and never fetches detail or catalogs", async ({
  page,
  request,
}) => {
  const s = await seed(request);
  const incident = await createIncident(request, s, s.areas[0]);
  const calls: string[] = [];
  page.on("request", (r) => {
    if (r.url().includes("/api-core")) calls.push(r.url());
  });
  await connect(page, await token(request, "direction"), "/next/incidents");
  await expect(page.getByRole("table")).toBeVisible();
  expect(
    await page.getByRole("link", { name: "Nueva incidencia" }).count(),
  ).toBe(0);
  await page.goto(`/next/incidents/${incident.id}`);
  await connect(
    page,
    await token(request, "direction"),
    `/next/incidents/${incident.id}`,
  );
  await expect(page.locator("main").getByRole("alert")).toContainText(
    "no puede leer",
  );
  expect(
    calls.filter(
      (p) => p.includes("/catalogs") || p.includes(`/incidents/${incident.id}`),
    ),
  ).toEqual([]);
});

test("Incident creation, edition, transitions and admin assignment preserve API history", async ({
  page,
  request,
}) => {
  const s = await seed(request);
  await connect(page, s.admin, "/next/incidents/new");
  await page
    .getByLabel("Jurisdicción", { exact: true })
    .selectOption(s.us.jurisdiction_id!);
  await page.getByLabel("Clínica", { exact: true }).selectOption(s.us.id);
  await page
    .getByLabel("Sistema afectado", { exact: true })
    .selectOption(s.systems.find((r) => r.key.includes("us"))!.id);
  await page
    .getByLabel("Área responsable", { exact: true })
    .selectOption(s.areas[0].id);
  await page
    .getByLabel("Canal de entrada", { exact: true })
    .selectOption(s.channel[0].id);
  await page.getByLabel("Tipo", { exact: true }).selectOption(s.type[0].id);
  await page
    .getByLabel("Severidad", { exact: true })
    .selectOption(s.severity[0].id);
  await page
    .getByLabel("Título", { exact: true })
    .fill("Synthetic browser incident");
  await page
    .getByLabel("Descripción", { exact: true })
    .fill("Synthetic outage without patient information");
  await page.getByRole("button", { name: "Crear incidencia" }).click();
  await expect(page).toHaveURL(/\/incidents\/[0-9a-f-]+\?created=1/);
  await expect(
    page.getByRole("heading", { name: "Editar incidencia" }),
  ).toBeVisible();
  const id = page.url().match(/incidents\/([0-9a-f-]+)/)![1];
  await page
    .getByLabel("Título", { exact: true })
    .fill("Synthetic browser edited");
  await page.getByRole("button", { name: "Guardar cambios" }).click();
  await expect(
    page.getByRole("heading", { name: "Synthetic browser edited" }),
  ).toBeVisible();
  await page
    .getByLabel("Estado destino")
    .selectOption(s.status.find((r) => r.key === "underAnalysis")!.id);
  await page.getByRole("button", { name: "Aplicar transición" }).click();
  await expect(page.getByLabel("Estado destino")).toHaveValue("");
  await page.getByLabel("Nueva área responsable").selectOption(s.areas[1].id);
  await page
    .getByLabel("Motivo de reasignación")
    .fill("Synthetic responsibility transfer");
  await page.getByRole("button", { name: "Reasignar incidencia" }).click();
  await expect(
    page.getByText(s.areas[1].label, { exact: true }).first(),
  ).toBeVisible();
  const history = await get<Schema<"StatusHistoryResponse">[]>(
    request,
    `/incidents/${id}/history`,
    s.admin,
  );
  expect(
    history.some(
      (r) =>
        r.to_status_value_id ===
        s.status.find((r) => r.key === "underAnalysis")!.id,
    ),
  ).toBe(true);
  const assignments = await get<Schema<"AssignmentHistoryResponse">[]>(
    request,
    `/incidents/${id}/assignment-history`,
    s.admin,
  );
  expect(
    assignments.some((r) => r.to_responsible_area_id === s.areas[1].id),
  ).toBe(true);
});

test("ResponsibleArea own and foreign areas are restricted in UI and real API", async ({
  page,
  request,
}) => {
  const s = await seed(request);
  const own = await createIncident(request, s, s.areas[0]);
  const foreign = await createIncident(request, s, s.areas[1]);
  const bearer = await token(request, "responsibleArea", {
    area_id: s.areas[0].id,
  });
  await connect(page, bearer, `/next/incidents/${own.id}`);
  await expect(
    page.getByRole("heading", { name: "Editar incidencia" }),
  ).toBeVisible();
  expect(await page.getByLabel("Nueva área responsable").count()).toBe(0);
  await page
    .getByLabel("Título", { exact: true })
    .fill("Synthetic area edited");
  await page.getByRole("button", { name: "Guardar cambios" }).click();
  await expect(
    page.getByRole("heading", { name: "Synthetic area edited" }),
  ).toBeVisible();
  const denied = await request.patch(`${api}/incidents/${own.id}`, {
    headers: { Authorization: `Bearer ${bearer}` },
    data: { severity_value_id: s.severity[0].id },
  });
  expect(denied.status()).toBe(403);
  await page.goto(`/next/incidents/${foreign.id}`);
  await connect(page, bearer, `/next/incidents/${foreign.id}`);
  await expect(page.locator("main").getByRole("alert").first()).toContainText(
    "denegado",
  );
});

test("InventoryAdmin manages catalog and lots without stock access", async ({
  page,
  request,
}) => {
  const bearer = await token(request, "inventoryAdmin");
  await connect(page, bearer, "/next/inventory/items");
  const product = code();
  await page
    .getByLabel("Título", { exact: true })
    .fill("Synthetic lot article");
  await page.getByLabel("Código de producto").fill(product);
  await page.getByLabel("Unidad base", { exact: true }).fill("piece");
  await page.getByLabel("Gestionar lotes").check();
  await page
    .getByRole("button", { name: "Crear artículo", exact: true })
    .click();
  await expect(
    page.getByRole("link", { name: product, exact: true }),
  ).toBeVisible();
  await page.getByRole("link", { name: product, exact: true }).click();
  await page.getByLabel("Código de lote").fill("SYN-LOT-QA");
  await page.getByRole("button", { name: "Crear lote", exact: true }).click();
  await expect(
    page.getByRole("cell", { name: "SYN-LOT-QA", exact: true }),
  ).toBeVisible();
  expect(
    await page.getByRole("link", { name: "Stock", exact: true }).count(),
  ).toBe(0);
  expect(await page.getByLabel("Clínica UUID", { exact: true }).count()).toBe(
    0,
  );
  await page
    .getByLabel("Motivo de baja")
    .fill("Synthetic zero-balance retirement");
  await page
    .getByRole("button", { name: "Dar de baja artículo", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirmar", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Dar de baja artículo", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("cell", { name: "SYN-LOT-QA", exact: true }),
  ).toBeVisible();
});

test("Manager configuration, pack movements, count and unique compensation preserve stock", async ({
  page,
  request,
}) => {
  const s = await seed(request);
  const item = await createItem(request, { pack_label: "pack", pack_size: 10 });
  const bearer = await token(request, "inventoryManager", {
    clinic_ids: [s.us.id],
  });
  await connect(
    page,
    bearer,
    `/next/inventory/items/${item.id}?clinic=${s.us.id}`,
  );
  await page.getByLabel("Punto de reorden obligatorio").fill("20");
  await page
    .getByRole("button", { name: "Configurar punto de reorden", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirmar", exact: true })
    .click();
  await expect(
    page.getByText("Punto de reorden clínico: 20 · Bajo reorden: Sí"),
  ).toBeVisible();
  await page.getByLabel("Cantidad", { exact: true }).fill("2");
  await page.getByLabel("Unidad del movimiento").selectOption("pack");
  await page
    .getByRole("button", { name: "Registrar entrada o salida", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirmar", exact: true })
    .click();
  await expect(
    page.getByText("Punto de reorden clínico: 20 · Bajo reorden: No"),
  ).toBeVisible();
  await page.getByLabel("Cantidad contada en unidades base").fill("19");
  await page.getByLabel("Motivo del conteo").fill("Synthetic physical count");
  await page
    .getByRole("button", { name: "Registrar conteo físico", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirmar", exact: true })
    .click();
  await expect(
    page.getByText("Punto de reorden clínico: 20 · Bajo reorden: Sí"),
  ).toBeVisible();
  const history = await get<Schema<"MovementRead">[]>(
    request,
    `/inventory/items/${item.id}/movements?clinic_id=${s.us.id}`,
    bearer,
  );
  const count = history.find((r) => r.kind === "adjust")!;
  expect(count.delta).toBe(-1);
  await page.getByLabel("UUID del movimiento original").selectOption(count.id);
  await page.getByLabel("Motivo de compensación").fill("Synthetic correction");
  await page
    .getByRole("button", { name: "Compensar movimiento", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirmar", exact: true })
    .click();
  await expect(
    page.getByText("Punto de reorden clínico: 20 · Bajo reorden: No"),
  ).toBeVisible();
  const stock = await get<Schema<"StockRead">>(
    request,
    `/inventory/items/${item.id}/stock?clinic_id=${s.us.id}`,
    bearer,
  );
  expect(stock.quantity).toBe(20);
  const twice = await request.post(
    `${api}/inventory/movements/${count.id}/correction`,
    {
      headers: { Authorization: `Bearer ${bearer}` },
      data: { reason: "Synthetic repeated correction" },
    },
  );
  expect(twice.status()).toBe(409);
});

test("Operator, regional and auditor retain scopes and durable denials", async ({
  page,
  request,
}) => {
  const s = await seed(request);
  const region = await token(request, "inventoryRegional", {
    jurisdiction_ids: [s.us.jurisdiction_id],
  });
  await connect(page, region, "/next/inventory/stock");
  await expect(
    page
      .getByRole("table")
      .or(page.getByText(/Sin resultados/))
      .first(),
  ).toBeVisible();
  expect(
    await page.getByRole("cell", { name: s.uk.id, exact: true }).count(),
  ).toBe(0);
  await page.getByLabel("Clínica UUID (opcional)").fill(s.uk.id);
  await page.getByRole("button", { name: "Consultar", exact: true }).click();
  await expect(page.locator("main").getByRole("alert")).toContainText(
    "denegado",
  );
  const auditor = await token(request, "inventoryAuditor", {
    jurisdiction_ids: [s.uk.jurisdiction_id],
  });
  const denials = await get<Schema<"AccessDenialRead">[]>(
    request,
    "/inventory/access-denials",
    auditor,
  );
  expect(
    denials.some((r) => r.actor_id === actor && r.clinic_id === s.uk.id),
  ).toBe(true);
  const operator = await token(request, "inventoryOperator", {
    clinic_ids: [s.us.id],
  });
  await page.getByRole("button", { name: "Desconectar" }).click();
  await page.getByLabel("JWT de desarrollo").fill(operator);
  await page.getByRole("button", { name: "Conectar", exact: true }).click();
  await page.getByRole("link", { name: "Stock", exact: true }).click();
  await expect(
    page
      .getByRole("table")
      .or(page.getByText(/Sin resultados/))
      .first(),
  ).toBeVisible();
  const first = (await get<Item[]>(request, "/inventory/items", operator))[0];
  const adjust = await request.post(`${api}/inventory/movements`, {
    headers: { Authorization: `Bearer ${operator}` },
    data: {
      item_id: first.id,
      clinic_id: s.us.id,
      kind: "adjust",
      counted_quantity: 0,
      reason: "Synthetic operator denial",
    },
  });
  expect(adjust.status()).toBe(403);
});

test("Lost response after accepted write never creates an automatic duplicate", async ({
  page,
  request,
}) => {
  const bearer = await token(request, "inventoryAdmin");
  await connect(page, bearer, "/next/inventory/items");
  let writes = 0;
  await page.route("**/next/api-core/inventory/items", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    writes++;
    const response = await route.fetch();
    expect(response.status()).toBe(201);
    await route.abort("failed");
  });
  const product = code();
  await page
    .getByLabel("Título", { exact: true })
    .fill("Synthetic uncertain response");
  await page.getByLabel("Código de producto").fill(product);
  await page.getByLabel("Unidad base", { exact: true }).fill("piece");
  await page
    .getByRole("button", { name: "Crear artículo", exact: true })
    .click();
  await expect(page.locator("main").getByRole("alert").first()).toContainText(
    "Resultado incierto",
  );
  await expect(
    page.getByRole("button", { name: "Crear artículo", exact: true }),
  ).toBeDisabled();
  await page.waitForTimeout(500);
  expect(writes).toBe(1);
  const items = await get<Item[]>(
    request,
    "/inventory/items?limit=100",
    bearer,
  );
  expect(items.filter((r) => r.product_code === product)).toHaveLength(1);
  await page
    .getByRole("button", { name: "Consultar datos e historial" })
    .click();
  await expect(
    page.getByRole("link", { name: product, exact: true }),
  ).toBeVisible();
});

test("Forwarding fails closed and private responses remain uncached", async ({
  request,
}) => {
  const base = process.env.BACKOFFICE_TEST_URL ?? "http://127.0.0.1:13100";
  const missing = await request.get(`${base}/next/api-core/inventory/items`);
  expect(missing.status()).toBe(401);
  expect(missing.headers()["cache-control"]).toBe("private, no-store");
  const excluded = await request.post(`${base}/next/api-core/auth/tokens`, {
    data: { role: "admin" },
  });
  expect(excluded.status()).toBe(404);
  const config = await request.get(`${base}/next/telemetry/config.json`);
  expect(await config.json()).toMatchObject({
    enabled: false,
    environment: "test",
  });
  expect(Object.keys(await config.json()).sort()).toEqual([
    "enabled",
    "endpoint",
    "environment",
  ]);
});

test("Compliance is read-only; Technology cannot assign; backend rejects a tampered signature", async ({
  page,
  request,
}) => {
  const s = await seed(request);
  const incident = await createIncident(request, s, s.areas[0]);
  for (const role of ["compliance", "technology"]) {
    const bearer = await token(request, role);
    await connect(page, bearer, `/next/incidents/${incident.id}`);
    await expect(
      page.getByRole("heading", {
        name: role === "compliance" ? "Descripción" : "Editar incidencia",
        exact: true,
      }),
    ).toBeVisible();
    await expect(page.getByLabel("Nueva área responsable")).toHaveCount(0);
    const denied = await request.post(
      `${api}/incidents/${incident.id}/assignments`,
      {
        headers: { Authorization: `Bearer ${bearer}` },
        data: {
          responsible_area_id: s.areas[1].id,
          reason: "Synthetic forbidden assignment",
        },
      },
    );
    expect(denied.status()).toBe(403);
  }
  const parts = s.admin.split(".");
  parts[2] = (parts[2][0] === "A" ? "B" : "A") + parts[2].slice(1);
  await page.goto("/next");
  await page.getByLabel("JWT de desarrollo").fill(parts.join("."));
  await page.getByRole("button", { name: "Conectar", exact: true }).click();
  await expect(page.locator("main").getByRole("alert")).toContainText(
    "JWT es inválido",
  );
  await expect(page.getByLabel("JWT de desarrollo")).toHaveValue("");
});

test("Inventory forms preserve keyboard access, errors and unsaved navigation at small widths", async ({
  page,
  request,
}) => {
  await connect(
    page,
    await token(request, "inventoryAdmin"),
    "/next/inventory/items",
  );
  for (const width of [393, 320]) {
    await page.setViewportSize({ width, height: 900 });
    expect(
      (
        await new AxeBuilder({ page })
          .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
          .analyze()
      ).violations.map((v) => v.id),
    ).toEqual([]);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  }
  await page
    .getByLabel("Título", { exact: true })
    .fill("Synthetic unsaved article");
  const dialog = page.waitForEvent("dialog");
  const navigation = page
    .getByRole("link", { name: "Incidencias anteriores" })
    .click();
  const warning = await dialog;
  expect(warning.message()).toContain("sin guardar");
  await warning.dismiss();
  await navigation;
  await expect(page).toHaveURL(/\/next\/inventory\/items$/);
  await page.getByLabel("Código de producto").fill(code());
  await page.getByLabel("Unidad base", { exact: true }).fill("piece");
  await page.getByLabel("Unidades por presentación").fill("2");
  await page
    .getByRole("button", { name: "Crear artículo", exact: true })
    .click();
  await expect(page.locator("main").getByRole("alert").first()).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Crear artículo", exact: true }),
  ).toBeEnabled();
});

test("Queue filters survive detail return and browser history", async ({
  page,
  request,
}) => {
  const s = await seed(request);
  await createIncident(request, s, s.areas[0]);
  await connect(page, s.admin, "/next/incidents");
  await page
    .getByLabel("Estado", { exact: true })
    .selectOption(s.status.find((r) => r.key === "new")!.id);
  await page.getByLabel("Ordenar por").selectOption("title");
  await page.getByRole("button", { name: "Aplicar filtros" }).click();
  await expect(page).toHaveURL(/sort_by=title/);
  const filtered = page.url();
  await page.getByRole("table").getByRole("link").first().click();
  await page
    .getByRole("link", { name: "Volver a incidencias", exact: true })
    .click();
  await expect(page).toHaveURL(filtered);
  await page.goBack();
  await expect(page).toHaveURL(/incidents\/[0-9a-f-]+/);
  await page.goBack();
  await expect(page).toHaveURL(filtered);
});

test("Partial history failure preserves detail and available status history", async ({
  page,
  request,
}) => {
  const s = await seed(request);
  const incident = await createIncident(request, s, s.areas[0]);
  await page.route(
    `**/next/api-core/incidents/${incident.id}/assignment-history`,
    (route) => route.abort("failed"),
  );
  await connect(page, s.admin, `/next/incidents/${incident.id}`);
  await expect(
    page.getByRole("heading", { name: incident.title, exact: true }),
  ).toBeVisible();
  await expect(page.locator("main").getByRole("alert")).toContainText(
    "No se pudo consultar",
  );
  await expect(
    page.getByRole("heading", { name: /Estado:/ }).first(),
  ).toBeVisible();
});

test("Inventory auditor reads historical US events and sees denial for foreign clinic", async ({
  page,
  request,
}) => {
  const s = await seed(request);
  const item = await createItem(request);
  const manager = await token(request, "inventoryManager", {
    clinic_ids: [s.us.id],
  });
  const r = await request.post(
    `${api}/inventory/items/${item.id}/clinics/${s.us.id}/configuration`,
    {
      headers: { Authorization: `Bearer ${manager}` },
      data: { reorder_point: 2 },
    },
  );
  expect(r.status()).toBe(200);
  await connect(
    page,
    await token(request, "inventoryAuditor", {
      jurisdiction_ids: [s.us.jurisdiction_id],
    }),
    "/next/inventory/audit",
  );
  await page.getByLabel("Artículo UUID").fill(item.id);
  await page.getByLabel("Clínica UUID", { exact: true }).fill(s.us.id);
  await page
    .getByRole("button", { name: "Consultar eventos", exact: true })
    .click();
  await expect(
    page.getByRole("region", { name: "Eventos de auditoría", exact: true }),
  ).toBeVisible();
  await page.getByLabel("Clínica UUID", { exact: true }).fill(s.uk.id);
  await page
    .getByRole("button", { name: "Consultar eventos", exact: true })
    .click();
  await expect(page.locator("main").getByRole("alert")).toContainText(
    "denegado",
  );
});
