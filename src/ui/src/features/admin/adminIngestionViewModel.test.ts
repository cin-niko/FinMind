import { strict as assert } from "node:assert";
import type { IngestionStatus } from "../../api/client";
import {
  filterIngestionStatus,
  getVisibleIngestionSources
} from "./adminIngestionViewModel";

const v1Sources = getVisibleIngestionSources(false);
assert.deepEqual(
  v1Sources.map((source) => source.id),
  ["vn_prices_daily", "vn_prices"]
);

const allSources = getVisibleIngestionSources(true);
assert.ok(allSources.some((source) => source.id === "us_prices"));
assert.ok(allSources.some((source) => source.id === "sjc_gold_prices"));
assert.ok(allSources.some((source) => source.id === "xauusd_prices"));

const status: IngestionStatus = {
  jobs: [
    {
      job_id: "j1",
      source_id: "vn_prices_daily",
      dataset_id: "vn_prices_daily",
      period: "2026-06-25",
      trigger: "manual",
      status: "success",
      started_at: "2026-06-25T00:00:00Z",
      completed_at: "2026-06-25T00:00:01Z",
      record_count: 100,
      diagnostics: {}
    },
    {
      job_id: "j2",
      source_id: "us_prices_daily",
      dataset_id: "us_prices_daily",
      period: "2026-06-25",
      trigger: "scheduled",
      status: "success",
      started_at: "2026-06-25T00:00:00Z",
      completed_at: "2026-06-25T00:00:01Z",
      record_count: 50,
      diagnostics: {}
    },
    {
      job_id: "j3",
      source_id: "sjc_gold_prices",
      dataset_id: "sjc_gold_prices",
      period: "2026-06-25",
      trigger: "manual",
      status: "success",
      started_at: "2026-06-25T00:00:00Z",
      completed_at: null,
      record_count: 1,
      diagnostics: {}
    }
  ],
  freshness: [
    {
      dataset: "vn_prices_daily",
      status: "fresh",
      as_of: "2026-06-25",
      record_count: 100
    },
    {
      dataset: "us_prices_daily",
      status: "fresh",
      as_of: "2026-06-25",
      record_count: 50
    },
    {
      dataset: "xauusd_prices_daily",
      status: "stale",
      as_of: "2026-06-20",
      record_count: 10
    }
  ]
};

const filtered = filterIngestionStatus(status, false);
assert.ok(filtered);
assert.deepEqual(
  filtered!.jobs.map((job) => job.job_id),
  ["j1"]
);
assert.deepEqual(
  filtered!.freshness.map((row) => row.dataset),
  ["vn_prices_daily"]
);

const unfiltered = filterIngestionStatus(status, true);
assert.equal(unfiltered?.jobs.length, 3);
assert.equal(unfiltered?.freshness.length, 3);

assert.equal(filterIngestionStatus(null, false), null);
assert.equal(filterIngestionStatus(null, true), null);
