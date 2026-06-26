import { useEffect, useMemo, useState } from "react";
import {
  getMarketOverview,
  type MarketOverview
} from "../../api/client";
import {
  buildHeatmapFilters,
  filterRoadmapIndexCharts,
  filterRoadmapInstruments,
  getGainersLosers,
  getHeatmapRowsForFilter,
  getIndexCardMetrics,
  getVisibleInstrumentRows,
  getWatchlistRows,
  readRoadmapMarketsEnabled,
  toggleSort,
  type HeatmapFilter,
  type MarketSortKey,
  type SortState
} from "./marketViewModel";

const MARKET_SCOPE: "VN" = "VN";
type MoverTab = "gainers" | "losers";
type CollectionHeatmapOverview = {
  filterId: string;
  overview: MarketOverview;
};
type SelectedIndexChart = MarketOverview["index_charts"][number];

type MarketPageProps = {
  onOpenInstrument: (instrumentId: string) => void;
};

export function MarketPage({ onOpenInstrument }: MarketPageProps) {
  const [heatmapFilterId, setHeatmapFilterId] = useState("all");
  const [sortState, setSortState] = useState<SortState>({ key: "change_percent", direction: "desc" });
  const [overview, setOverview] = useState<MarketOverview | null>(null);
  const [collectionHeatmapOverview, setCollectionHeatmapOverview] = useState<CollectionHeatmapOverview | null>(null);
  const [overviewError, setOverviewError] = useState<string | null>(null);
  const [selectedIndexChart, setSelectedIndexChart] = useState<SelectedIndexChart | null>(null);
  const [moverTab, setMoverTab] = useState<MoverTab>("gainers");

  useEffect(() => {
    let cancelled = false;
    setOverviewError(null);
    getMarketOverview(MARKET_SCOPE, "all")
      .then((nextOverview) => {
        if (cancelled) {
          return;
        }
        setOverview(nextOverview);
        setCollectionHeatmapOverview(null);
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setOverviewError(error instanceof Error ? error.message : "Market data unavailable");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const roadmapMarketsEnabled = useMemo(
    () => readRoadmapMarketsEnabled(overview),
    [overview]
  );

  const visibleInstrumentRows = useMemo(
    () =>
      filterRoadmapInstruments(
        overview?.instrument_rows ?? [],
        roadmapMarketsEnabled
      ),
    [overview, roadmapMarketsEnabled]
  );

  const visibleIndexCharts = useMemo(
    () =>
      filterRoadmapIndexCharts(
        overview?.index_charts ?? [],
        roadmapMarketsEnabled
      ),
    [overview, roadmapMarketsEnabled]
  );

  const visibleHeatmapRows = useMemo(
    () =>
      filterRoadmapInstruments(
        overview?.heatmap ?? [],
        roadmapMarketsEnabled
      ),
    [overview, roadmapMarketsEnabled]
  );

  const sortedRows = useMemo(
    () => getVisibleInstrumentRows(visibleInstrumentRows, sortState),
    [visibleInstrumentRows, sortState]
  );

  const heatmapFilters = useMemo(() => {
    if (!overview) {
      return [];
    }
    return buildHeatmapFilters({
      collections: overview.collections,
      heatmap: visibleHeatmapRows
    });
  }, [overview, visibleHeatmapRows]);

  const activeHeatmapFilter = useMemo(() => {
    return heatmapFilters.find((filter) => filter.id === heatmapFilterId);
  }, [heatmapFilterId, heatmapFilters]);

  useEffect(() => {
    if (!activeHeatmapFilter || activeHeatmapFilter.kind !== "collection") {
      setCollectionHeatmapOverview(null);
      return;
    }

    let cancelled = false;
    setCollectionHeatmapOverview(null);
    getMarketOverview(MARKET_SCOPE, activeHeatmapFilter.id)
      .then((nextOverview) => {
        if (!cancelled) {
          setCollectionHeatmapOverview({
            filterId: activeHeatmapFilter.id,
            overview: nextOverview
          });
        }
      })
      .catch(() => {
        if (!cancelled) {
          setCollectionHeatmapOverview(null);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [activeHeatmapFilter]);

  const filteredHeatmapRows = useMemo(() => {
    if (!overview) {
      return [];
    }
    const scopedHeatmap =
      collectionHeatmapOverview?.filterId === heatmapFilterId
        ? filterRoadmapInstruments(
            collectionHeatmapOverview.overview.heatmap,
            roadmapMarketsEnabled
          )
        : undefined;
    return getHeatmapRowsForFilter(
      { heatmap: visibleHeatmapRows },
      heatmapFilterId,
      scopedHeatmap ? { heatmap: scopedHeatmap } : undefined
    );
  }, [
    collectionHeatmapOverview,
    heatmapFilterId,
    overview,
    roadmapMarketsEnabled,
    visibleHeatmapRows
  ]);
  const watchlistRows = useMemo(
    () => getWatchlistRows(visibleInstrumentRows),
    [visibleInstrumentRows]
  );
  const movers = useMemo(
    () => getGainersLosers(visibleInstrumentRows),
    [visibleInstrumentRows]
  );
  const activeMoverRows = moverTab === "gainers" ? movers.gainers : movers.losers;

  if (overviewError) {
    return <div className="stateBox" role="alert">{overviewError}</div>;
  }

  if (!overview) {
    return <div className="stateBox">Loading market data...</div>;
  }

  return (
    <section className="marketPage marketWorkbench">
      <div className="marketLayout">
        <main className="marketMainColumn">
          <section className="indexStrip" aria-label="Top indexes">
            {visibleIndexCharts.map((indexChart) => (
              <IndexMiniCard
                indexChart={indexChart}
                isSelected={selectedIndexChart?.symbol === indexChart.symbol}
                key={indexChart.symbol}
                onSelect={() => {
                  setSelectedIndexChart(indexChart);
                }}
              />
            ))}
          </section>

          {selectedIndexChart ? (
            <IndexChartDetailPanel
              indexChart={selectedIndexChart}
              onClose={() => setSelectedIndexChart(null)}
            />
          ) : null}

          <div className="marketDashboardGrid">
            <section className="panel instrumentListPanel" aria-label="Instrument list">
              <div className="panelHeader compactHeader">
                <div>
                  <h2>Instruments</h2>
                  <span className="meta">Showing top 10 rows by the active sort</span>
                </div>
              </div>
              <div className="marketDataTable">
                <table>
                  <thead>
                    <tr>
                      <SortableHeader
                        label="Symbol"
                        sortKey="symbol"
                        sortState={sortState}
                        onSort={setSortState}
                      />
                      <SortableHeader
                        label="Sector"
                        sortKey="sector"
                        sortState={sortState}
                        onSort={setSortState}
                      />
                      <SortableHeader
                        label="Price"
                        sortKey="last"
                        sortState={sortState}
                        onSort={setSortState}
                      />
                      <SortableHeader
                        label="Change"
                        sortKey="change_percent"
                        sortState={sortState}
                        onSort={setSortState}
                      />
                      <SortableHeader
                        label="Volume"
                        sortKey="volume"
                        sortState={sortState}
                        onSort={setSortState}
                      />
                    </tr>
                  </thead>
                  <tbody>
                    {sortedRows.map((row) => (
                      <tr
                        key={row.id}
                        onClick={() => {
                          setSelectedIndexChart(null);
                          onOpenInstrument(row.id);
                        }}
                      >
                        <td>
                          <button className="symbolButton" type="button">{row.symbol}</button>
                        </td>
                        <td>{row.sector ?? "-"}</td>
                        <td>{formatNumber(row.last)}</td>
                        <td className={row.change_percent >= 0 ? "up" : "down"}>
                          {formatPercent(row.change_percent)}
                        </td>
                        <td>{formatCompact(row.volume)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="panel marketHeatmap" aria-label="Market heatmap">
              <div className="panelHeader compactHeader">
                <div>
                  <h2>Market Heatmap</h2>
                  <span className="meta">Filter by collection or sector</span>
                </div>
              </div>
              <div className="collectionTabs" role="list" aria-label="Market heatmap filters">
                {heatmapFilters.map((filter) => (
                  <button
                    className={filter.id === heatmapFilterId ? "tabButton active" : "tabButton"}
                    key={filter.id}
                    onClick={() => handleHeatmapFilter(filter)}
                    type="button"
                  >
                    {filter.label}
                  </button>
                ))}
              </div>
              <div className="heatmapGrid">
                {filteredHeatmapRows.map((cell) => (
                  <button
                    className={cell.change_percent >= 0 ? "heatCell positive" : "heatCell negative"}
                    key={cell.id}
                    onClick={() => {
                      setSelectedIndexChart(null);
                      onOpenInstrument(cell.id);
                    }}
                    style={{ minHeight: `${Math.max(72, Math.min(142, cell.value / 130000000))}px` }}
                    type="button"
                  >
                    <strong>{cell.symbol}</strong>
                    <span>{formatPercent(cell.change_percent)}</span>
                    <small>{cell.sector ?? "Unclassified"}</small>
                  </button>
                ))}
              </div>
            </section>
          </div>
        </main>

        <aside className="marketRightRail" aria-label="Market side panel">
          <section className="railPanel" aria-label="Watchlist">
            <div className="railHeader">
              <h2>Watchlist</h2>
            </div>
            <div className="railList">
              {watchlistRows.map((row) => (
                <MarketRailRow
                  key={row.id}
                  onSelect={() => {
                    setSelectedIndexChart(null);
                    onOpenInstrument(row.id);
                  }}
                  row={row}
                />
              ))}
            </div>
          </section>

          <section className="railPanel moverPanel" aria-label="Gainers and losers">
            <div className="moverTabs" role="tablist" aria-label="Mover groups">
              <button
                aria-selected={moverTab === "gainers"}
                className={moverTab === "gainers" ? "moverTab active" : "moverTab"}
                onClick={() => setMoverTab("gainers")}
                role="tab"
                type="button"
              >
                Gainers
              </button>
              <button
                aria-selected={moverTab === "losers"}
                className={moverTab === "losers" ? "moverTab active" : "moverTab"}
                onClick={() => setMoverTab("losers")}
                role="tab"
                type="button"
              >
                Losers
              </button>
            </div>
            <div className="railList compact" role="tabpanel">
              {activeMoverRows.length ? (
                activeMoverRows.map((row) => (
                  <MarketRailRow
                    key={row.id}
                    onSelect={() => {
                      setSelectedIndexChart(null);
                      onOpenInstrument(row.id);
                    }}
                    row={row}
                  />
                ))
              ) : (
                <span className="railEmpty">No {moverTab} in this view</span>
              )}
            </div>
          </section>
        </aside>
      </div>

    </section>
  );

  function handleHeatmapFilter(filter: HeatmapFilter) {
    setHeatmapFilterId(filter.id);
  }
}

function IndexMiniCard({
  indexChart,
  isSelected,
  onSelect
}: {
  indexChart: MarketOverview["index_charts"][number];
  isSelected: boolean;
  onSelect: () => void;
}) {
  const metrics = getIndexCardMetrics(indexChart);
  const directionClass = indexChart.change_percent >= 0 ? "up" : "down";

  return (
    <button
      className={
        isSelected
          ? "marketChartCard indexMiniChart indexMiniChartButton selected"
          : "marketChartCard indexMiniChart indexMiniChartButton"
      }
      onClick={onSelect}
      type="button"
    >
      <div className="indexCardHeader">
        <div>
          <span className="indexName">{indexChart.name}</span>
          <strong>{formatNumber(indexChart.last)}</strong>
        </div>
        <div className="indexChangeStack">
          <span className={directionClass}>{formatPercent(indexChart.change_percent)}</span>
          <small>{formatSignedNumber(metrics.changeValue)}</small>
        </div>
      </div>
      <svg className="indexLineChart" viewBox="0 0 240 64" role="img" aria-label={`${indexChart.name} mini chart`}>
        <path className="indexBaseline" d="M 0 32 L 240 32" />
        <path className={directionClass === "up" ? "indexArea positive" : "indexArea negative"} d={metrics.areaPath} />
        <path className={directionClass === "up" ? "indexLine positive" : "indexLine negative"} d={metrics.linePath} />
      </svg>
    </button>
  );
}

function IndexChartDetailPanel({
  indexChart,
  onClose
}: {
  indexChart: SelectedIndexChart;
  onClose: () => void;
}) {
  const metrics = getIndexCardMetrics(indexChart);
  const directionClass = indexChart.change_percent >= 0 ? "up" : "down";
  const latestPoint = indexChart.series.at(-1);
  const previousPoint = indexChart.series.at(-2);
  const high = indexChart.series.length
    ? Math.max(...indexChart.series.map((point) => point.value))
    : null;
  const low = indexChart.series.length
    ? Math.min(...indexChart.series.map((point) => point.value))
    : null;
  const metricCells = [
    ["Prev Close", previousPoint ? formatNumber(previousPoint.value) : "--"],
    ["Latest", latestPoint ? formatNumber(latestPoint.value) : "--"],
    ["High", high === null ? "--" : formatNumber(high)],
    ["Low", low === null ? "--" : formatNumber(low)]
  ];
  return (
    <section className="panel marketChartPanel indexChartDetailPanel" aria-label={`${indexChart.name} full chart`}>
      <div className="chartHeroHeader indexChartHeroHeader">
        <div className="chartIdentity">
          <span className="chartTickerMark">{indexChart.symbol.slice(0, 3)}</span>
          <div>
            <div className="chartTitleLine">
              <h2>{indexChart.name}</h2>
              <span>{indexChart.symbol}</span>
            </div>
            <span className="chartMeta">Market index · canonical overview series</span>
          </div>
        </div>
        <div className="chartPriceBlock">
          <strong className="chartPriceLine">{formatNumber(indexChart.last)}</strong>
          <span className={`chartChangeLine ${directionClass === "up" ? "positive" : "negative"}`}>
            {formatSignedNumber(metrics.changeValue)} · {formatPercent(indexChart.change_percent)}
          </span>
        </div>
        <button className="textButton compactAction chartCloseButton" onClick={onClose} type="button">
          Close
        </button>
      </div>
      <svg className="marketChartSurface indexDetailChart" viewBox="0 0 240 64" role="img" aria-label={`${indexChart.name} chart`}>
        <path className="indexBaseline" d="M 0 32 L 240 32" />
        <path className={directionClass === "up" ? "indexArea positive" : "indexArea negative"} d={metrics.areaPath} />
        <path className={directionClass === "up" ? "indexLine positive" : "indexLine negative"} d={metrics.linePath} />
      </svg>
      <div className="indexMetricStrip chartStatsGrid" aria-label={`${indexChart.name} latest values`}>
        {metricCells.map(([label, value]) => (
          <span className="chartStatCell" key={label}>
            <small>{label}</small>
            <strong>{value}</strong>
          </span>
        ))}
      </div>
    </section>
  );
}

function SortableHeader({
  label,
  sortKey,
  sortState,
  onSort
}: {
  label: string;
  sortKey: MarketSortKey;
  sortState: SortState;
  onSort: (nextState: SortState) => void;
}) {
  const active = sortState.key === sortKey;
  return (
    <th aria-sort={active ? (sortState.direction === "asc" ? "ascending" : "descending") : "none"}>
      <button
        className={active ? "sortableHeader active" : "sortableHeader"}
        onClick={() => onSort(toggleSort(sortState, sortKey))}
        type="button"
      >
        {label}
        <span aria-hidden="true">{active ? (sortState.direction === "asc" ? "▲" : "▼") : "↕"}</span>
      </button>
    </th>
  );
}

function MarketRailRow({
  onSelect,
  row
}: {
  onSelect: () => void;
  row: MarketOverview["instrument_rows"][number];
}) {
  return (
    <button className="railInstrumentRow" onClick={onSelect} type="button">
      <span className="railSymbolMark">{row.symbol.slice(0, 2)}</span>
      <span className="railInstrumentMeta">
        <strong>{row.symbol}</strong>
        <small>{row.sector ?? row.exchange ?? "Market"}</small>
      </span>
      <span className="railPriceBlock">
        <strong>{formatNumber(row.last)}</strong>
        <small className={row.change_percent >= 0 ? "up" : "down"}>{formatPercent(row.change_percent)}</small>
      </span>
    </button>
  );
}

function formatPercent(value: number) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function formatSignedNumber(value: number) {
  return `${value >= 0 ? "+" : ""}${formatNumber(value)}`;
}

function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value);
}

function formatCompact(value: number) {
  return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}
