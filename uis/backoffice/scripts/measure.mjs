import { chromium } from "@playwright/test";
import { gzipSync } from "node:zlib";
import { writeFileSync } from "node:fs";
if (process.env.HC_SYNTHETIC_TESTS !== "1")
  throw new Error("Synthetic isolated servers required");
const api = process.env.BACKOFFICE_TEST_API ?? "http://127.0.0.1:18190";
const next = process.env.BACKOFFICE_TEST_URL ?? "http://127.0.0.1:13100";
const legacy = "http://127.0.0.1:8080";
if (
  ![api, next, legacy].every((url) =>
    ["localhost", "127.0.0.1"].includes(new URL(url).hostname),
  )
)
  throw new Error("Loopback only");
const browser = await chromium.launch({ channel: "chrome", headless: true });
const tokenResponse = await fetch(`${api}/auth/tokens`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    actor_id: "00000000-0000-4000-8000-000000000123",
    role: "admin",
  }),
});
if (tokenResponse.status !== 201)
  throw new Error("Synthetic token unavailable");
const { access_token: token } = await tokenResponse.json();
const rows = [];
try {
  for (const width of [1350, 393])
    for (const app of ["legacy", "next"])
      for (let trial = 1; trial <= 3; trial++) {
        const context = await browser.newContext({
          viewport: { width, height: 900 },
        });
        const page = await context.newPage();
        await page.addInitScript(() => {
          window.__metrics = { lcp: 0, cls: 0 };
          new PerformanceObserver((list) => {
            for (const e of list.getEntries())
              window.__metrics.lcp = e.startTime;
          }).observe({ type: "largest-contentful-paint", buffered: true });
          new PerformanceObserver((list) => {
            for (const e of list.getEntries())
              if (!e.hadRecentInput) window.__metrics.cls += e.value;
          }).observe({ type: "layout-shift", buffered: true });
        });
        for (const cache of ["cold", "warm"]) {
          await page.goto(
            app === "legacy"
              ? `${legacy}/management/`
              : `${next}/next/management/catalogs`,
          );
          if (app === "legacy") {
            await page.locator("#apiUrl").fill(api);
            await page.locator("#token").fill(token);
          } else await page.getByLabel("JWT de desarrollo").fill(token);
          const started = Date.now();
          await (
            app === "legacy"
              ? page.locator("#load")
              : page.getByRole("button", { name: "Conectar", exact: true })
          ).click();
          await (
            app === "legacy"
              ? page.locator("#catalogs table")
              : page.getByRole("table")
          ).waitFor();
          const ready = Date.now() - started;
          await page.waitForTimeout(150);
          const metrics = await page.evaluate(() => {
            const n = performance.getEntriesByType("navigation")[0];
            return {
              ttfb_ms: n.responseStart - n.requestStart,
              lcp_ms: window.__metrics.lcp,
              cls: window.__metrics.cls,
              overflow: document.documentElement.scrollWidth > innerWidth,
              api_ms: performance
                .getEntriesByType("resource")
                .filter((r) => r.name.includes("/management/catalogs"))
                .map((r) => r.duration),
              scripts: performance
                .getEntriesByType("resource")
                .filter((r) => r.initiatorType === "script")
                .map((r) => r.name),
            };
          });
          let gzipBytes = 0;
          for (const url of new Set(metrics.scripts)) {
            const r = await fetch(url);
            gzipBytes += gzipSync(Buffer.from(await r.arrayBuffer())).length;
          }
          delete metrics.scripts;
          rows.push({
            app,
            width,
            trial,
            cache,
            data_ready_ms: ready,
            js_gzip_bytes: gzipBytes,
            ...metrics,
          });
        }
        await context.close();
      }
  const report = {
    environment: {
      node: process.version,
      browser: "system Chrome headless",
      network: "loopback; no CPU/network throttling",
      api: "fresh isolated PostgreSQL; synthetic catalogs",
      next: "production standalone 16.4.3",
      trials: 3,
    },
    scope:
      "Management catalogs only; synthetic connection included; no approved retirement budget. JS gzip is recompressed unique script responses, not measured network gzip. CLS here is cumulative observed shifts, not production session windows.",
    rows,
  };
  if (process.argv[2])
    writeFileSync(process.argv[2], JSON.stringify(report, null, 2) + "\n");
  else process.stdout.write(JSON.stringify(report, null, 2) + "\n");
} finally {
  await browser.close();
}
