/**
 * Structural sanity tests for `MarketPage.tsx`.
 *
 * The UI codebase does not include a React DOM test harness, so we treat the
 * source file as a string fixture and assert that scope-down rules from T046
 * are visible in the component definition.
 */
import { strict as assert } from "node:assert";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(resolve(here, "MarketPage.tsx"), "utf8");

assert.ok(
  !source.includes("US Markets"),
  "Market page must not expose the US market option"
);
assert.ok(
  !source.includes("Commodity</option>"),
  "Market page must not expose the Commodity market option"
);
assert.ok(
  !/<select[\s\S]*value=\{market\}/.test(source),
  "Market page must not render a <select> bound to a market state value"
);
assert.ok(
  !source.includes("marketToolbar"),
  "Market toolbar shell (which previously hosted the selector) must be gone"
);
assert.ok(
  source.includes("InstrumentChartPanel"),
  "Market page must mount the instrument detail chart panel"
);
assert.ok(
  source.includes("filterRoadmapInstruments"),
  "Market page must apply roadmap filtering to instrument rows"
);
