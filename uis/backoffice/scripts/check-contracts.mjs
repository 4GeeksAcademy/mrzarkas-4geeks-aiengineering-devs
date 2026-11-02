import { execFileSync } from "node:child_process";
import { readFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
const destination = join(
  mkdtempSync(join(tmpdir(), "hc-contracts-")),
  "generated.ts",
);
execFileSync(
  "pnpm",
  ["exec", "openapi-typescript", "contracts/openapi.json", "-o", destination],
  { stdio: "pipe" },
);
if (
  readFileSync(destination, "utf8") !==
  readFileSync("src/lib/api/generated.ts", "utf8")
) {
  process.stderr.write(
    "API types differ from the reviewed OpenAPI snapshot. Run types:generate.\n",
  );
  process.exitCode = 1;
}
