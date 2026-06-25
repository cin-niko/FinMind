import type { MarketInstrumentRow, MarketOverview } from "../../api/client";

export type MarketSortKey = "symbol" | "sector" | "last" | "change_percent" | "volume";
export type SortDirection = "asc" | "desc";
export type SortState = {
  key: MarketSortKey;
  direction: SortDirection;
};

export type HeatmapFilter = {
  id: string;
  label: string;
  kind: "all" | "collection" | "sector";
};

type IndexChartInput = MarketOverview["index_charts"][number];

export function toggleSort(current: SortState, nextKey: MarketSortKey): SortState {
  if (current.key !== nextKey) {
    return { key: nextKey, direction: "desc" };
  }
  return { key: nextKey, direction: current.direction === "desc" ? "asc" : "desc" };
}

export function getVisibleInstrumentRows(
  rows: MarketInstrumentRow[],
  sort: SortState,
  limit = 10
) {
  return [...rows].sort((left, right) => compareRows(left, right, sort)).slice(0, limit);
}

export function getWatchlistRows(rows: MarketInstrumentRow[], limit = 5) {
  return rows.slice(0, limit);
}

export function getGainersLosers(rows: MarketInstrumentRow[], limit = 3) {
  return {
    gainers: [...rows]
      .filter((row) => row.change_percent > 0)
      .sort((left, right) => right.change_percent - left.change_percent)
      .slice(0, limit),
    losers: [...rows]
      .filter((row) => row.change_percent < 0)
      .sort((left, right) => left.change_percent - right.change_percent)
      .slice(0, limit)
  };
}

export function buildHeatmapFilters(
  overview: Pick<MarketOverview, "collections" | "heatmap">
): HeatmapFilter[] {
  const collectionFilters = overview.collections
    .filter((collection) => collection.id !== "all")
    .map<HeatmapFilter>((collection) => ({
      id: collection.id,
      label: collection.name,
      kind: "collection"
    }));

  const sectorFilters = Array.from(
    new Set(
      overview.heatmap
        .map((row) => row.sector)
        .filter((sector): sector is string => Boolean(sector))
    )
  )
    .sort((left, right) => left.localeCompare(right))
    .map<HeatmapFilter>((sector) => ({
      id: `sector:${sector}`,
      label: sector,
      kind: "sector"
    }));

  return [{ id: "all", label: "All", kind: "all" }, ...collectionFilters, ...sectorFilters];
}

export function filterHeatmapRows(
  overview: Pick<MarketOverview, "heatmap">,
  filterId: string
) {
  if (filterId.startsWith("sector:")) {
    const sector = filterId.slice("sector:".length);
    return overview.heatmap.filter((row) => row.sector === sector);
  }
  return overview.heatmap;
}

export function getHeatmapRowsForFilter(
  overview: Pick<MarketOverview, "heatmap">,
  filterId: string,
  collectionOverview?: Pick<MarketOverview, "heatmap">
) {
  if (filterId.startsWith("sector:")) {
    return filterHeatmapRows(overview, filterId);
  }
  if (filterId !== "all" && collectionOverview) {
    return collectionOverview.heatmap;
  }
  return overview.heatmap;
}

export function getIndexCardMetrics(indexChart: IndexChartInput) {
  const lastPoint = indexChart.series.at(-1);
  const previousPoint = indexChart.series.at(-2);
  const last = lastPoint?.value ?? indexChart.last;
  const previous = previousPoint?.value ?? last;
  const changeValue = round(last - previous);
  const direction = changeValue > 0 ? "up" : changeValue < 0 ? "down" : "flat";

  return {
    changeValue,
    direction,
    linePath: buildLinePath(indexChart.series),
    areaPath: buildAreaPath(indexChart.series)
  };
}

function compareRows(left: MarketInstrumentRow, right: MarketInstrumentRow, sort: SortState) {
  const direction = sort.direction === "asc" ? 1 : -1;
  if (sort.key === "symbol" || sort.key === "sector") {
    return (
      String(left[sort.key] ?? "").localeCompare(String(right[sort.key] ?? "")) *
      direction
    );
  }
  return (Number(left[sort.key] ?? 0) - Number(right[sort.key] ?? 0)) * direction;
}

function buildLinePath(series: IndexChartInput["series"]) {
  const points = normalizeSeries(series);
  if (!points.length) {
    return "";
  }
  return points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`)
    .join(" ");
}

function buildAreaPath(series: IndexChartInput["series"]) {
  const points = normalizeSeries(series);
  if (!points.length) {
    return "";
  }
  const line = points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`)
    .join(" ");
  const first = points[0];
  const last = points[points.length - 1];
  return `${line} L ${last.x} 64 L ${first.x} 64 Z`;
}

function normalizeSeries(series: IndexChartInput["series"]) {
  const width = 240;
  const height = 64;
  const padding = 4;
  const values = series.map((point) => point.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = Math.max(max - min, 1);
  const step = series.length > 1 ? (width - padding * 2) / (series.length - 1) : 0;

  return series.map((point, index) => ({
    x: round(padding + index * step),
    y: round(height - padding - ((point.value - min) / range) * (height - padding * 2))
  }));
}

function round(value: number) {
  return Math.round(value * 100) / 100;
}
