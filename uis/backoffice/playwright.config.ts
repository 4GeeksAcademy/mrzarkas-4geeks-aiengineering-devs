import { defineConfig } from "@playwright/test";
const base = process.env.BACKOFFICE_TEST_URL ?? "http://127.0.0.1:13100";
const api = process.env.BACKOFFICE_TEST_API ?? "http://127.0.0.1:18190";
if (
  process.env.HC_SYNTHETIC_TESTS !== "1" ||
  ![base, api].every((value) =>
    ["localhost", "127.0.0.1"].includes(new URL(value).hostname),
  )
)
  throw new Error(
    "E2E requires HC_SYNTHETIC_TESTS=1 and explicit loopback synthetic test servers.",
  );
export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: "list",
  timeout: 45000,
  use: {
    baseURL: base,
    channel: "chrome",
    headless: true,
    viewport: { width: 1350, height: 900 },
    trace: "off",
    video: "off",
    screenshot: "off",
  },
});
