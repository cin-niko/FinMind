import { LineSeries, createChart, type IChartApi } from "lightweight-charts";
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
};

export function InstrumentChartPanel({ instrumentId }: Props) {
  const [timeframe, setTimeframe] = useState<InstrumentTimeframe>(
    DEFAULT_INSTRUMENT_TIMEFRAME
  );
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
    <section className="panel instrumentChartPanel" aria-label="Instrument chart">
      <div className="panelHeader compactHeader">
        <div>
          <h2>{chartData?.instrument.symbol ?? "Instrument"}</h2>
          <span className="meta">
            {chartData?.instrument.name ?? "Select an instrument to view chart"}
          </span>
        </div>
        <div className="timeframeTabs" role="tablist" aria-label="Timeframes">
          {INSTRUMENT_TIMEFRAMES.map((option) => {
            const active = option.id === timeframe;
            return (
              <button
                aria-selected={active}
                className={active ? "tabButton active" : "tabButton"}
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
      </div>
      {banner ? <BannerView banner={banner} /> : null}
      {error ? <div className="stateBox" role="alert">{error}</div> : null}
      {chartData && banner && !banner.blocking ? (
        <ChartCanvas data={chartData} />
      ) : null}
    </section>
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

function ChartCanvas({ data }: { data: InstrumentChart }) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }
    const chart: IChartApi = createChart(containerRef.current, {
      height: 280,
      layout: { background: { color: "#FFFFFF" }, textColor: "#172033" },
      grid: {
        vertLines: { color: "#E7ECF4" },
        horzLines: { color: "#E7ECF4" }
      },
      rightPriceScale: { borderColor: "#D8DEE8" },
      timeScale: { borderColor: "#D8DEE8" }
    });
    const series = chart.addSeries(LineSeries, {
      color: "#138A63",
      lineWidth: 2
    });
    series.setData(
      data.records.map((record) => ({
        time: record.time.slice(0, 10),
        value: record.close
      }))
    );
    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [data]);

  return <div className="chartBox" ref={containerRef} />;
}
