import { strict as assert } from "node:assert";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(resolve(here, "InstrumentChartPanel.tsx"), "utf8");

assert.ok(
  !source.includes("chartData && banner && !banner.blocking"),
  "Fresh charts must render even when no banner is shown"
);
assert.ok(
  source.includes("chartData && !banner?.blocking"),
  "Only blocking banners should suppress the chart canvas"
);
assert.ok(
  source.includes("CandlestickSeries"),
  "Instrument charts must support candlestick rendering"
);
assert.ok(
  source.includes('useState<ChartDisplayMode>("candle")'),
  "Instrument charts must default to candle mode"
);
assert.ok(
  source.includes('aria-label="Chart display mode"'),
  "Instrument charts must expose a line/candle display-mode control"
);
assert.ok(
  source.includes('chartMode === "line"'),
  "Instrument charts must allow switching to line mode"
);
assert.ok(
  source.includes("chartHeroHeader"),
  "Instrument chart must use the polished market chart header"
);
assert.ok(
  source.includes("chartPriceLine"),
  "Instrument chart must show a prominent latest close value"
);
assert.ok(
  source.includes("ChartModeIcon"),
  "Chart display mode buttons must use symbols instead of Candle/Line text labels"
);
assert.ok(
  source.includes('"Candlestick chart"'),
  "Candlestick mode must keep an accessible label despite icon-only UI"
);
assert.ok(
  source.includes('"Line chart"'),
  "Line mode must keep an accessible label despite icon-only UI"
);
assert.ok(
  source.includes("chartStatsGrid"),
  "Instrument chart must expose a compact latest-record stats strip"
);
