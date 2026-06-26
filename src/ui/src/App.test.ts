import { strict as assert } from "node:assert";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(resolve(here, "App.tsx"), "utf8");

assert.ok(
  source.includes('"marketInstrument"'),
  "App must define a dedicated market instrument detail view"
);
assert.ok(
  source.includes("selectedMarketInstrumentId"),
  "App must own the selected market instrument id"
);
assert.ok(
  source.includes("MarketInstrumentDetailPage"),
  "App must render the dedicated instrument detail page"
);
assert.ok(
  source.includes("onOpenInstrument"),
  "App must pass instrument navigation into MarketPage"
);
assert.ok(
  source.includes("const DATA_PLATFORM_SURFACES_ENABLED = false"),
  "App must keep the parked data platform surfaces disabled by default"
);
assert.ok(
  source.includes('nextView === "market" || nextView === "marketInstrument" || nextView === "admin"'),
  "App navigation must redirect hidden data-platform surfaces away from the parked UI"
);
assert.ok(
  source.includes("if (DATA_PLATFORM_SURFACES_ENABLED)"),
  "App must not fetch ingestion status while the data platform is parked"
);
