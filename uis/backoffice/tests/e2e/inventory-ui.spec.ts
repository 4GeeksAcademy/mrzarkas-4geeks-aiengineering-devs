import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
const api = process.env.BACKOFFICE_TEST_API ?? "http://127.0.0.1:18190";
const actor = "00000000-0000-4000-8000-000000000123";

test("Inventory dashboard and page filters are scoped, partial and accessible at four widths", async ({
  page,
  request,
}) => {
  const r = await request.post(`${api}/auth/tokens`, {
    data: { actor_id: actor, role: "inventoryAdmin" },
  });
  expect(r.status()).toBe(201);
  const bearer = (await r.json()).access_token;
  let clinicalRequests = 0;
  page.on("request", (req) => {
    if (/api-core\/inventory\/(stock|reorder)/.test(req.url()))
      clinicalRequests++;
  });
  await page.goto("/next/inventory");
  await page.getByLabel("JWT de desarrollo").fill(bearer);
  await page.getByRole("button", { name: "Conectar", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Artículos recibidos" }),
  ).toBeVisible();
  await expect(page.getByText(/conteos son parciales/)).toBeVisible();
  await expect(page.getByText(/Recepción de la consulta/)).toBeVisible();
  for (const width of [320, 393, 768, 1350]) {
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
  expect(clinicalRequests).toBe(0);
  await page.getByRole("link", { name: "Catálogo", exact: true }).click();
  await expect(page.getByLabel("Buscar en esta página")).toHaveCSS(
    "border-top-color",
    "rgb(86, 109, 105)",
  );
  await page.setViewportSize({ width: 1350, height: 900 });
  await page.evaluate(() => {
    document.body.style.zoom = "2";
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.evaluate(() => {
    document.body.style.zoom = "1";
  });
  await page.getByLabel("Buscar en esta página").fill("SYN-NO-MATCH-FIXTURE");
  await expect(
    page.getByText("Sin resultados.", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Siguiente", exact: true }),
  ).toBeEnabled();
});

test("Lost catalog response remains blocked after navigation and needs explicit acknowledgement", async ({
  page,
  request,
}) => {
  const r = await request.post(`${api}/auth/tokens`, {
    data: { actor_id: actor, role: "inventoryAdmin" },
  });
  expect(r.status()).toBe(201);
  const bearer = (await r.json()).access_token;
  await page.goto("/next/inventory/items");
  await page.getByLabel("JWT de desarrollo").fill(bearer);
  await page.getByRole("button", { name: "Conectar", exact: true }).click();
  page.on("dialog", (d) => d.accept());
  let writes = 0;
  await page.route("**/next/api-core/inventory/items", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    writes++;
    await route.fetch();
    await route.abort("failed");
  });
  await page
    .getByLabel("Título", { exact: true })
    .fill("Synthetic uncertain catalog");
  await page
    .getByLabel("Código de producto")
    .fill(`SYN-UNCERTAIN-${Date.now()}`);
  await page.getByLabel("Unidad base", { exact: true }).fill("piece");
  await page
    .getByRole("button", { name: "Crear artículo", exact: true })
    .click();
  await expect(
    page.getByRole("region", { name: "Resultado de operación desconocido" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Inventario", exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Resultado de operación desconocido" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Catálogo", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Crear artículo", exact: true }),
  ).toBeDisabled();
  expect(writes).toBe(1);
  await page
    .getByRole("button", {
      name: "Reconozco la incertidumbre tras revisar los datos",
    })
    .click();
  await expect(
    page.getByRole("button", { name: "Crear artículo", exact: true }),
  ).toBeEnabled();
  expect(
    await page.evaluate(() => localStorage.length + sessionStorage.length),
  ).toBe(0);
});

test("Clinical detail, history, stock and audit retain responsive accessibility", async ({
  page,
  request,
}) => {
  const issue = async (role: string, scope: Record<string, unknown> = {}) => {
    const r = await request.post(`${api}/auth/tokens`, {
      data: { actor_id: actor, role, ...scope },
    });
    expect(r.status()).toBe(201);
    return (await r.json()).access_token;
  };
  const admin = await issue("admin");
  const refs = await request.get(
    `${api}/management/reference-data/clinics?limit=100`,
    { headers: { Authorization: `Bearer ${admin}` } },
  );
  expect(refs.status()).toBe(200);
  const us = (await refs.json()).items.find(
    (c: { key: string }) => c.key === "dev-us-clinic-01",
  );
  const inventoryAdmin = await issue("inventoryAdmin");
  const items = await request.get(`${api}/inventory/items?limit=50`, {
    headers: { Authorization: `Bearer ${inventoryAdmin}` },
  });
  expect(items.status()).toBe(200);
  const item = (await items.json()).find(
    (i: { product_code: string }) => i.product_code === "SYN-INV-GAUZE",
  );
  const connect = async (bearer: string, path: string) => {
    await page.goto(path);
    await page.getByLabel("JWT de desarrollo").fill(bearer);
    await page.getByRole("button", { name: "Conectar", exact: true }).click();
    await expect(
      page.getByRole("button", { name: "Desconectar" }),
    ).toBeVisible();
  };
  const check = async () => {
    for (const width of [320, 393, 768, 1350]) {
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
  };
  await connect(
    await issue("inventoryManager", { clinic_ids: [us.id] }),
    `/next/inventory/items/${item.id}?clinic=${us.id}`,
  );
  await expect(page.getByRole("table")).toBeVisible();
  await check();
  await page
    .getByRole("button", { name: "Registrar entrada o salida", exact: true })
    .focus();
  await page.keyboard.press("Enter"); // Native validity rejects empty quantity without a write.
  await page.getByLabel("Cantidad", { exact: true }).fill("3");
  await page.getByLabel("Unidad del movimiento").selectOption("pack");
  await page
    .getByRole("button", { name: "Registrar entrada o salida", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(
    page.getByRole("button", {
      name: "Registrar entrada o salida",
      exact: true,
    }),
  ).toBeFocused();
  page.on("dialog", (d) => d.accept());
  await page.getByRole("link", { name: "Stock", exact: true }).click();
  await expect(page.getByRole("table")).toBeVisible();
  await check();
  await page.getByRole("button", { name: "Desconectar" }).click();
  await page.getByLabel("JWT de desarrollo").fill(
    await issue("inventoryAuditor", {
      jurisdiction_ids: [us.jurisdiction_id],
    }),
  );
  await page.getByRole("button", { name: "Conectar", exact: true }).click();
  await page.getByRole("link", { name: "Auditoría", exact: true }).click();
  await page.getByLabel("Artículo UUID").fill(item.id);
  await page.getByLabel("Clínica UUID", { exact: true }).fill(us.id);
  await page
    .getByRole("button", { name: "Consultar eventos", exact: true })
    .click();
  await expect(page.getByText(/La API aplica la redacción/)).toBeVisible();
  await check();
});
