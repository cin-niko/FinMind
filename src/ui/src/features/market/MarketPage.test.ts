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
  source.includes("onOpenInstrument"),
  "Market page must delegate instrument detail navigation to its parent"
);
assert.ok(
  !source.includes("selectedInstrumentId"),
  "Market page must not own selected instrument state in the overview"
);
assert.ok(
  !source.includes("selectedRow"),
  "Instrument table clicks must not leave selected-row state in the Market overview"
);
assert.ok(
  !source.includes("railInstrumentRow selected"),
  "Watchlist and mover rows must not receive selected state from instrument clicks"
);
assert.ok(
  !source.includes("InstrumentChartPanel"),
  "Market page must not render the full instrument chart directly"
);
assert.ok(
  source.includes("selectedIndexChart ?"),
  "Market page must open a full index chart only after a mini chart selection"
);
assert.ok(
  source.includes("filterRoadmapInstruments"),
  "Market page must apply roadmap filtering to instrument rows"
);
assert.ok(
  source.includes("marketChartCard"),
  "Index mini charts must share the polished market chart card style"
);
assert.ok(
  source.includes("marketChartSurface"),
  "Index detail charts must share the soft chart surface treatment"
);
assert.ok(
  source.includes("indexMetricStrip"),
  "Index detail charts must expose compact metric cells below the chart"
);
