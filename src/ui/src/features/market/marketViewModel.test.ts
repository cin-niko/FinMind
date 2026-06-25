import { strict as assert } from "node:assert";
import type { MarketInstrumentRow, MarketOverview } from "../../api/client";
import {
  buildHeatmapFilters,
  filterHeatmapRows,
  getHeatmapRowsForFilter,
  getGainersLosers,
  getIndexCardMetrics,
  getVisibleInstrumentRows,
  getWatchlistRows,
  toggleSort
} from "./marketViewModel";

function row(
  symbol: string,
  sector: string | null,
  price: number,
  change: number,
  volume: number
): MarketInstrumentRow {
  return {
    id: `vn_stock:${symbol}`,
    symbol,
    name: symbol,
    market: "VN_STOCK",
    asset_class: "stock",
    exchange: "HOSE",
    currency: "VND",
    sector,
    industry: null,
    sub_industry: null,
    last: price,
    change_percent: change,
    volume,
    value: volume * price,
    freshness: "fresh"
  };
}

const rows = [
  row("AAA", "Energy", 11, -0.3, 200),
  row("BBB", "Banking", 13, 1.2, 900),
  row("CCC", "Banking", 12, 0.6, 500),
  row("DDD", "Real Estate", 10, -1.8, 300),
  row("EEE", "Technology", 18, 2.1, 800),
  row("FFF", "Materials", 9, 0.2, 700),
  row("GGG", "Energy", 14, 0.1, 100),
  row("HHH", "Consumer", 16, -0.1, 450),
  row("III", "Banking", 15, 0.7, 600),
  row("JJJ", "Utilities", 17, -0.4, 250),
  row("KKK", "Energy", 19, 1.9, 750)
];

const overview = {
  collections: [
    { id: "vn30", name: "VN30", type: "index" },
    { id: "vn100", name: "VN100", type: "index" }
  ],
  heatmap: rows
} as MarketOverview;

const visible = getVisibleInstrumentRows(rows, {
  key: "change_percent",
  direction: "desc"
});
assert.equal(visible.length, 10);
assert.equal(visible[0].symbol, "EEE");
assert.equal(visible[9].symbol, "JJJ");

const priceAscending = getVisibleInstrumentRows(rows, {
  key: "last",
  direction: "asc"
});
assert.equal(priceAscending[0].symbol, "FFF");
assert.equal(priceAscending[1].symbol, "DDD");

assert.deepEqual(toggleSort({ key: "last", direction: "desc" }, "last"), {
  key: "last",
  direction: "asc"
});
assert.deepEqual(toggleSort({ key: "last", direction: "asc" }, "volume"), {
  key: "volume",
  direction: "desc"
});

const filters = buildHeatmapFilters(overview);
assert.deepEqual(
  filters.map((filter) => filter.label),
  ["All", "VN30", "VN100", "Banking", "Consumer", "Energy", "Materials", "Real Estate", "Technology", "Utilities"]
);
assert.equal(filterHeatmapRows(overview, "sector:Energy").length, 3);
assert.equal(filterHeatmapRows(overview, "vn30").length, rows.length);

const vn30HeatmapOverview = {
  ...overview,
  heatmap: rows.slice(1, 4)
} as MarketOverview;
assert.deepEqual(
  getHeatmapRowsForFilter(overview, "vn30", vn30HeatmapOverview).map((item) => item.symbol),
  ["BBB", "CCC", "DDD"]
);
assert.deepEqual(
  getHeatmapRowsForFilter(overview, "sector:Energy", vn30HeatmapOverview).map((item) => item.symbol),
  ["AAA", "GGG", "KKK"]
);

const watchlistRows = getWatchlistRows(rows);
assert.deepEqual(
  watchlistRows.map((item) => item.symbol),
  ["AAA", "BBB", "CCC", "DDD", "EEE"]
);

const movers = getGainersLosers(rows, 3);
assert.deepEqual(
  movers.gainers.map((item) => item.symbol),
  ["EEE", "KKK", "BBB"]
);
assert.deepEqual(
  movers.losers.map((item) => item.symbol),
  ["DDD", "JJJ", "AAA"]
);

const indexMetrics = getIndexCardMetrics({
  symbol: "VNINDEX",
  name: "VNINDEX",
  last: 1288,
  change_percent: 0.31,
  series: [
    { time: "2026-06-18T02:00:00+00:00", value: 1280 },
    { time: "2026-06-18T03:00:00+00:00", value: 1284 },
    { time: "2026-06-18T04:00:00+00:00", value: 1288 }
  ]
});
assert.equal(indexMetrics.changeValue, 4);
assert.equal(indexMetrics.direction, "up");
assert.ok(indexMetrics.linePath.startsWith("M "));
