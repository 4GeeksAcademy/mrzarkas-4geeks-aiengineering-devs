import { mkdirSync, copyFileSync } from "node:fs";
const target = "public/telemetry";
mkdirSync(target, { recursive: true });
for (const file of [
  "runtime.js",
  "telemetry-service.js",
  "context.js",
  "transport.js",
  "validation.js",
  "vitals.js",
  "event-contract.json",
])
  copyFileSync(`operational-incidents/telemetry/${file}`, `${target}/${file}`);
copyFileSync("operational-incidents/favicon.svg", "public/favicon.svg");
