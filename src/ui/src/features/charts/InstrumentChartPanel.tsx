import { CandlestickSeries, LineSeries, createChart, type IChartApi } from "lightweight-charts";
import { useEffect, useRef, useState } from "react";
import {
  getInstrumentChart,
  type InstrumentChart
} from "../../api/client";
import {
  DEFAULT_INSTRUMENT_TIMEFRAME,
  INSTRUMENT_TIMEFRAMES,
  selectLazyFetchBanner,
  type InstrumentTimeframe,
  type LazyFetchBanner
} from "./chartViewModel";

type Props = {
  instrumentId: string | null;
  onClose?: () => void;
};
type ChartDisplayMode = "candle" | "line";

const CHART_DISPLAY_MODES: ReadonlyArray<ChartDisplayMode> = ["candle", "line"];

export function InstrumentChartPanel({ instrumentId, onClose }: Props) {
  const [timeframe, setTimeframe] = useState<InstrumentTimeframe>(
    DEFAULT_INSTRUMENT_TIMEFRAME
  );
  const [chartMode, setChartMode] = useState<ChartDisplayMode>("candle");
  const [chartData, setChartData] = useState<InstrumentChart | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);
  const refreshScheduled = useRef(false);

  useEffect(() => {
    if (!instrumentId) {
      setChartData(null);
      return;
    }
    let cancelled = false;
    setError(null);
    getInstrumentChart(instrumentId, timeframe)
      .then((next) => {
        if (!cancelled) {
          setChartData(next);
        }
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(
            caught instanceof Error
              ? caught.message
              : "Chart data unavailable"
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, [instrumentId, timeframe, refreshTick]);

  const banner: LazyFetchBanner | null = chartData
    ? selectLazyFetchBanner(chartData.lazy_fetch, chartData.freshness)
    : null;
  const latestRecord = chartData?.records.at(-1) ?? null;
  const previousRecord = chartData?.records.at(-2) ?? null;
  const latestChange =
    latestRecord && previousRecord ? latestRecord.close - previousRecord.close : null;
  const latestChangePercent =
    latestChange !== null && previousRecord?.close
      ? (latestChange / previousRecord.close) * 100
      : null;
  const chartDirectionClass =
    latestChange === null || latestChange >= 0 ? "positive" : "negative";

  useEffect(() => {
    if (!banner || !banner.autoRefreshMs || refreshScheduled.current) {
      return;
    }
    refreshScheduled.current = true;
    const handle = setTimeout(() => {
      refreshScheduled.current = false;
      setRefreshTick((tick) => tick + 1);
    }, banner.autoRefreshMs);
    return () => {
      clearTimeout(handle);
      refreshScheduled.current = false;
    };
  }, [banner]);

  return (
    <section className="panel instrumentChartPanel marketChartPanel" aria-label="Instrument chart">
      <div className="chartHeroHeader">
        <div className="chartIdentity">
          <span className="chartTickerMark">
            {chartData?.instrument.symbol?.slice(0, 3) ?? "---"}
          </span>
          <div>
            <div className="chartTitleLine">
              <h2>{chartData?.instrument.symbol ?? "Instrument"}</h2>
              <span>{chartData?.instrument.name ?? "Select an instrument to view chart"}</span>
            </div>
            <span className="chartMeta">
              {latestRecord
                ? `At close: ${formatDateTime(latestRecord.time)} · Canonical VN daily prices`
                : "Canonical VN daily prices"}
            </span>
          </div>
        </div>
        <div className="chartPriceBlock">
          <strong className="chartPriceLine">
            {latestRecord ? formatNumber(latestRecord.close) : "--"}
          </strong>
          {latestChange !== null && latestChangePercent !== null ? (
            <span className={`chartChangeLine ${chartDirectionClass}`}>
              {formatSignedNumber(latestChange)} · {formatPercent(latestChangePercent)}
            </span>
          ) : null}
        </div>
        {onClose ? (
          <button className="textButton compactAction chartCloseButton" onClick={onClose} type="button">
            Close
          </button>
        ) : null}
      </div>
      <div className="chartToolbar">
        <div className="chartSegments timeframeTabs" role="tablist" aria-label="Timeframes">
          {INSTRUMENT_TIMEFRAMES.map((option) => {
            const active = option.id === timeframe;
            return (
              <button
                aria-selected={active}
                className={active ? "chartSegmentButton tabButton active" : "chartSegmentButton tabButton"}
                key={option.id}
                onClick={() => setTimeframe(option.id)}
                role="tab"
                title={option.hint ?? undefined}
                type="button"
              >
                {option.label}
                {option.hint ? (
                  <span className="timeframeHint" aria-label={option.hint}>
                    *
                  </span>
                ) : null}
              </button>
            );
          })}
        </div>
        <div className="chartToolbarSpacer" />
        <div className="chartSegments chartModeSegments" role="tablist" aria-label="Chart display mode">
          {CHART_DISPLAY_MODES.map((option) => {
            const active = option === chartMode;
            return (
              <button
                aria-label={option === "candle" ? "Candlestick chart" : "Line chart"}
                aria-selected={active}
                className={active ? "chartIconButton tabButton active" : "chartIconButton tabButton"}
                key={option}
                onClick={() => setChartMode(option)}
                role="tab"
                title={option === "candle" ? "Candlestick chart" : "Line chart"}
                type="button"
              >
                <ChartModeIcon mode={option} />
              </button>
            );
          })}
        </div>
      </div>
      {banner ? <BannerView banner={banner} /> : null}
      {error ? <div className="stateBox" role="alert">{error}</div> : null}
      {chartData && !banner?.blocking ? (
        <>
          <ChartCanvas data={chartData} chartMode={chartMode} />
          <ChartStatsGrid data={chartData} latestRecord={latestRecord} previousRecord={previousRecord} />
        </>
      ) : null}
    </section>
  );
}

function ChartModeIcon({ mode }: { mode: ChartDisplayMode }) {
  if (mode === "line") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M4 17l5-5 4 3 7-8" />
        <path d="M4 20h16" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M7 4v16" />
      <path d="M17 3v18" />
      <rect x="4.5" y="8" width="5" height="7" rx="1.2" />
      <rect x="14.5" y="6" width="5" height="10" rx="1.2" />
    </svg>
  );
}

function BannerView({ banner }: { banner: LazyFetchBanner }) {
  return (
    <div
      className={`chartBanner chartBanner-${banner.kind}`}
      role={banner.kind === "warning" ? "alert" : "status"}
    >
      <strong>{banner.title}</strong>
      <span>{banner.description}</span>
    </div>
  );
}

function ChartCanvas({
  chartMode,
  data
}: {
  chartMode: ChartDisplayMode;
  data: InstrumentChart;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }
    const chart: IChartApi = createChart(containerRef.current, {
      height: 390,
      layout: { background: { color: "#FFFEFB" }, textColor: "#746F65" },
      grid: {
        vertLines: { color: "#EFEAE1" },
        horzLines: { color: "#EFEAE1" }
      },
      rightPriceScale: { borderColor: "#E3DDD2" },
      timeScale: { borderColor: "#E3DDD2" }
    });
    if (chartMode === "line") {
      const series = chart.addSeries(LineSeries, {
        color: "#2F6F3E",
        lineWidth: 2
      });
      series.setData(
        data.records.map((record) => ({
          time: record.time.slice(0, 10),
          value: record.close
        }))
      );
    } else {
      const series = chart.addSeries(CandlestickSeries, {
        upColor: "#2F6F3E",
        borderUpColor: "#2F6F3E",
        wickUpColor: "#2F6F3E",
        downColor: "#9F3C45",
        borderDownColor: "#9F3C45",
        wickDownColor: "#9F3C45"
      });
      series.setData(
        data.records.map((record) => ({
          time: record.time.slice(0, 10),
          open: record.open,
          high: record.high,
          low: record.low,
          close: record.close
        }))
      );
    }
    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [chartMode, data]);

  return <div className="chartBox" ref={containerRef} />;
}

function ChartStatsGrid({
  data,
  latestRecord,
  previousRecord
}: {
  data: InstrumentChart;
  latestRecord: InstrumentChart["records"][number] | null;
  previousRecord: InstrumentChart["records"][number] | null;
}) {
  const high = data.records.length
    ? Math.max(...data.records.map((record) => record.high))
    : null;
  const low = data.records.length
    ? Math.min(...data.records.map((record) => record.low))
    : null;
  const volume = latestRecord?.volume ?? null;
  const stats = [
    ["Prev Close", previousRecord ? formatNumber(previousRecord.close) : "--"],
    ["Open", latestRecord ? formatNumber(latestRecord.open) : "--"],
    ["Volume", volume === null ? "--" : formatCompact(volume)],
    ["High", high === null ? "--" : formatNumber(high)],
    ["Low", low === null ? "--" : formatNumber(low)],
    ["Source", "Canonical"]
  ];

  return (
    <div className="chartStatsGrid" aria-label={`${data.instrument.symbol} latest values`}>
      {stats.map(([label, value]) => (
        <span className="chartStatCell" key={label}>
          <small>{label}</small>
          <strong>{value}</strong>
        </span>
      ))}
    </div>
  );
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value);
}

function formatSignedNumber(value: number) {
  return `${value >= 0 ? "+" : ""}${formatNumber(value)}`;
}

function formatPercent(value: number) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function formatCompact(value: number) {
  return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}
