import type {
  InstrumentChart,
  LazyFetch,
  LazyFetchStatus
} from "../../api/client";

export type InstrumentTimeframe = InstrumentChart["timeframe"];

export const DEFAULT_INSTRUMENT_TIMEFRAME: InstrumentTimeframe = "1d";

export type TimeframeOption = {
  id: InstrumentTimeframe;
  label: string;
  hint?: string;
};

export const INSTRUMENT_TIMEFRAMES: readonly TimeframeOption[] = [
  {
    id: "1h",
    label: "1h",
    hint: "best-effort coverage"
  },
  { id: "4h", label: "4h" },
  { id: "1d", label: "1d" },
  { id: "1M", label: "1M" }
] as const;

export type LazyFetchBannerKind = "fresh" | "loading" | "warning" | "empty";

export type LazyFetchBanner = {
  kind: LazyFetchBannerKind;
  status: LazyFetchStatus | "unknown";
  title: string;
  description: string;
  /** Block rendering of the chart body when true. */
  blocking: boolean;
  /** Auto-refresh after this many milliseconds, if set. */
  autoRefreshMs?: number;
};

/** Compute the banner state for the instrument detail chart. */
export function selectLazyFetchBanner(
  lazyFetch: LazyFetch | undefined,
  freshness: InstrumentChart["freshness"] | undefined
): LazyFetchBanner {
  if (!lazyFetch) {
    return buildFreshBanner(freshness);
  }
  switch (lazyFetch.status) {
    case "success":
    case "already_present":
      return buildFreshBanner(freshness, lazyFetch.status);
    case "blocked":
      return {
        kind: "loading",
        status: "blocked",
        title: "Loading latest VN daily data\u2026",
        description:
          lazyFetch.reason ??
          "A fresh fetch is in flight. The chart will update shortly.",
        blocking: true,
        autoRefreshMs: 5000
      };
    case "failed":
      return {
        kind: "warning",
        status: "failed",
        title: "Could not refresh latest data \u2014 showing last known.",
        description:
          lazyFetch.reason ??
          "The latest fetch did not succeed. Showing the most recent rows we have.",
        blocking: false
      };
    case "out_of_scope":
      return {
        kind: "empty",
        status: "out_of_scope",
        title: "This ticker is not in the VN100 universe (V1 scope).",
        description:
          lazyFetch.reason ??
          "Only VN100 tickers are available in the V1 scope.",
        blocking: true
      };
    default:
      return buildFreshBanner(freshness);
  }
}

function buildFreshBanner(
  freshness: InstrumentChart["freshness"] | undefined,
  status: LazyFetchStatus | "unknown" = "unknown"
): LazyFetchBanner {
  const freshLabel = freshness?.status ?? "unknown";
  const asOf = freshness?.as_of;
  const title =
    freshLabel === "fresh"
      ? `Fresh as of ${asOf ?? "now"}`
      : freshLabel === "stale"
        ? `Stale as of ${asOf ?? "unknown"}`
        : `Freshness: ${freshLabel}`;
  return {
    kind: "fresh",
    status,
    title,
    description:
      freshLabel === "fresh"
        ? "Latest VN daily snapshot is up to date."
        : "Showing the latest available VN daily snapshot.",
    blocking: false
  };
}
