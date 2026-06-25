import type {
  DatasetFreshness,
  IngestionJob,
  IngestionStatus
} from "../../api/client";

export type IngestionSource = {
  id: string;
  label: string;
};

export const V1_INGESTION_SOURCES: readonly IngestionSource[] = [
  { id: "vn_prices_daily", label: "VN Stocks Daily" },
  { id: "vn_prices", label: "VN Stocks 1h" }
] as const;

export const ROADMAP_INGESTION_SOURCES: readonly IngestionSource[] = [
  { id: "us_prices", label: "US Stocks 1h" },
  { id: "us_prices_daily", label: "US Stocks Daily" },
  { id: "xauusd_prices", label: "XAUUSD 1h" },
  { id: "xauusd_prices_daily", label: "XAUUSD Daily Fallback" },
  { id: "sjc_gold_prices", label: "SJC Gold Daily" }
] as const;

const ROADMAP_SOURCE_IDS: ReadonlySet<string> = new Set(
  ROADMAP_INGESTION_SOURCES.map((source) => source.id)
);

const ROADMAP_DATASET_IDS: ReadonlySet<string> = new Set([
  "us_prices",
  "us_prices_daily",
  "xauusd_prices",
  "xauusd_prices_daily",
  "sjc_gold_prices"
]);

/** Sources visible in the manual fetch dropdown for the current scope. */
export function getVisibleIngestionSources(
  roadmapEnabled: boolean
): IngestionSource[] {
  if (roadmapEnabled) {
    return [...V1_INGESTION_SOURCES, ...ROADMAP_INGESTION_SOURCES];
  }
  return [...V1_INGESTION_SOURCES];
}

function isV1Job(job: IngestionJob): boolean {
  return (
    !ROADMAP_SOURCE_IDS.has(job.source_id) &&
    !ROADMAP_DATASET_IDS.has(job.dataset_id)
  );
}

function isV1Freshness(item: DatasetFreshness): boolean {
  return !ROADMAP_DATASET_IDS.has(item.dataset);
}

/** Strip roadmap rows from an ingestion status payload for V1 scope. */
export function filterIngestionStatus(
  status: IngestionStatus | null,
  roadmapEnabled: boolean
): IngestionStatus | null {
  if (!status || roadmapEnabled) {
    return status;
  }
  return {
    jobs: status.jobs.filter(isV1Job),
    freshness: status.freshness.filter(isV1Freshness)
  };
}
