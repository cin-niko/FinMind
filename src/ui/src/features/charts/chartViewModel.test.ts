import { strict as assert } from "node:assert";
import type { LazyFetch } from "../../api/client";
import {
  DEFAULT_INSTRUMENT_TIMEFRAME,
  INSTRUMENT_TIMEFRAMES,
  selectLazyFetchBanner
} from "./chartViewModel";

assert.equal(DEFAULT_INSTRUMENT_TIMEFRAME, "1d");

assert.deepEqual(
  INSTRUMENT_TIMEFRAMES.map((tf) => tf.id),
  ["1h", "4h", "1d", "1M"]
);

const hourly = INSTRUMENT_TIMEFRAMES.find((tf) => tf.id === "1h");
assert.ok(hourly?.hint && hourly.hint.length > 0);
assert.equal(
  INSTRUMENT_TIMEFRAMES.filter((tf) => tf.hint).length,
  1,
  "only the 1h option has a coverage hint"
);

function lazy(status: LazyFetch["status"], reason: string | null = null): LazyFetch {
  return {
    status,
    dataset_id: "vn_prices_daily",
    instrument_id: "vn_stock:VCB",
    reason,
    jobs: []
  };
}

const freshFreshness = { status: "fresh", as_of: "2026-06-25" };

const successBanner = selectLazyFetchBanner(lazy("success"), freshFreshness);
assert.equal(successBanner.kind, "fresh");
assert.equal(successBanner.blocking, false);
assert.ok(successBanner.title.includes("Fresh"));

const alreadyBanner = selectLazyFetchBanner(
  lazy("already_present"),
  { status: "stale", as_of: "2026-06-20" }
);
assert.equal(alreadyBanner.kind, "fresh");
assert.ok(alreadyBanner.title.includes("Stale"));

const blockedBanner = selectLazyFetchBanner(
  lazy("blocked", "Fetch in progress"),
  undefined
);
assert.equal(blockedBanner.kind, "loading");
assert.equal(blockedBanner.blocking, true);
assert.equal(blockedBanner.autoRefreshMs, 5000);
assert.ok(blockedBanner.description.includes("Fetch in progress"));

const failedBanner = selectLazyFetchBanner(lazy("failed"), freshFreshness);
assert.equal(failedBanner.kind, "warning");
assert.equal(failedBanner.blocking, false);
assert.ok(failedBanner.title.toLowerCase().includes("could not"));

const oosBanner = selectLazyFetchBanner(lazy("out_of_scope"), undefined);
assert.equal(oosBanner.kind, "empty");
assert.equal(oosBanner.blocking, true);
assert.ok(oosBanner.title.includes("VN100"));

const noLazyBanner = selectLazyFetchBanner(undefined, freshFreshness);
assert.equal(noLazyBanner.kind, "fresh");
assert.equal(noLazyBanner.blocking, false);
