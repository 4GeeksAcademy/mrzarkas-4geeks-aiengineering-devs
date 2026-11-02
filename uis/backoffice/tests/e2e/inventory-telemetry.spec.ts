import { test, expect } from "@playwright/test";
const api = process.env.BACKOFFICE_TEST_API ?? "http://127.0.0.1:18190";
test("Trusted selection and first movement interaction share a server flow without typing duplicates", async ({ page, request }) => {
  const actor = "00000000-0000-4000-8000-000000000456";
  async function issue(role: string, clinic_ids: string[] = []) {
    const response = await request.post(`${api}/auth/tokens`, { data: { actor_id: actor, role, clinic_ids } });
    expect(response.status()).toBe(201);
    return (await response.json()).access_token as string;
  }
  const admin = await issue("admin");
  const refs = await request.get(`${api}/management/reference-data/clinics?limit=100`, { headers: { Authorization: `Bearer ${admin}` } });
  expect(refs.status()).toBe(200);
  const clinic = (await refs.json()).items.find((value: { key: string }) => value.key === "dev-us-clinic-01").id as string;
  const manager = await issue("inventoryManager", [clinic]);
  const catalog = await issue("inventoryAdmin");
  const title = `Synthetic gesture ${Date.now()}`;
  const created = await request.post(`${api}/inventory/items`, { headers: { Authorization: `Bearer ${catalog}` },
    data: { title, product_code: `SYN-GESTURE-${Date.now()}`, unit: "piece" } });
  expect(created.status()).toBe(201);
  const item = (await created.json()).id as string;
  expect((await request.post(`${api}/inventory/items/${item}/clinics/${clinic}/configuration`, {
    headers: { Authorization: `Bearer ${manager}` }, data: { reorder_point: 2 },
  })).status()).toBe(200);
  const gestures: Array<{ action: string; flowId: string; accepted: boolean }> = [];
  page.on("response", async (response) => {
    if (response.url().endsWith("/telemetry/inventory-flow") && response.status() === 200) {
      const payload = response.request().postDataJSON() as { action: string };
      if (!["product_selected", "order_started"].includes(payload.action)) return;
      const value = await response.json();
      gestures.push({ action: payload.action, flowId: value.flowId, accepted: value.accepted });
    }
  });
  await page.goto("/next/inventory/stock");
  await page.getByLabel("JWT de desarrollo").fill(manager);
  await page.getByRole("button", { name: "Conectar", exact: true }).click();
  await expect(page.getByRole("link", { name: title, exact: true })).toBeVisible();
  await page.getByRole("link", { name: title, exact: true }).click();
  await expect(page.getByRole("heading", { name: "Registrar entrada o salida" })).toBeVisible();
  const quantity = page.getByLabel("Cantidad", { exact: true });
  await expect(quantity).toBeEnabled();
  await quantity.fill("123");
  await quantity.fill("124");
  await expect.poll(() => gestures.length).toBe(2);
  expect(gestures.map(value => value.action)).toEqual(["product_selected", "order_started"]);
  expect(gestures[0].flowId).toBe(gestures[1].flowId);
  expect(gestures.every(value => value.accepted)).toBe(true);
  expect(await page.evaluate(() => localStorage.length + sessionStorage.length)).toBe(0);
  await page.getByRole("button", { name: "Registrar entrada o salida", exact: true }).click();
  const movement = page.waitForResponse(response => response.url().endsWith("/inventory/movements") && response.request().method() === "POST");
  const confirmation = page.waitForRequest(request => request.url().endsWith("/telemetry/inventory-flow") && request.postDataJSON().action === "confirmation");
  await page.getByRole("button", { name: "Confirmar", exact: true }).click();
  const completed = await movement;
  expect(completed.status()).toBe(201);
  expect(completed.request().headers()["x-inventory-flow-id"]).toBe(gestures[1].flowId);
  expect((await confirmation).postDataJSON().flowId).toBe(gestures[1].flowId);
  await expect(page.getByText(/Confirmación API:/)).toBeVisible();
  await page.getByRole("button", { name: "Desconectar" }).click();
});
