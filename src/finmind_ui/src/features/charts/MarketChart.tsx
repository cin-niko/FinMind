import { CandlestickSeries, LineSeries, createChart, type IChartApi } from "lightweight-charts";
import { ChartNoAxesCombined, SlidersVertical } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ChartArtifact } from "../../api/client";
import { useI18n } from "../settings/i18n";

const ARTIFACT_REASON_KEYS = {
  missing_price_series: "missingPriceSeries",
  unsupported_chart_requirement: "unsupportedChartRequirement"
} as const;

type ChartPoint = { date: string; value: number; change_percent?: number };

export function MarketChart({
  artifact,
  showDownloads = true
}: {
  artifact: ChartArtifact;
  showDownloads?: boolean;
}) {
  const { t } = useI18n();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const supportedViews = artifact.spec.supported_views;
  const [view, setView] = useState(() => artifact.spec.default_view);
  const firstSeries = getRenderableSeries(artifact);
  const candles = artifact.spec.candles;
  const canShowCandles = supportedViews.includes("candlestick") && candles.length > 0;
  const activeView = view === "candlestick" && canShowCandles ? "candlestick" : "line";
  const isReady = (artifact.status ?? "ready") === "ready" && (firstSeries.length > 0 || canShowCandles);
  const reasonKey = artifact.reason
    ? ARTIFACT_REASON_KEYS[artifact.reason as keyof typeof ARTIFACT_REASON_KEYS]
    : undefined;

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }
    if (!isReady) {
      return;
    }
    const chart: IChartApi = createChart(containerRef.current, {
      height: 260,
      layout: { background: { color: "#FFFFFF" }, textColor: "#172033" },
      grid: {
        vertLines: { color: "#E7ECF4" },
        horzLines: { color: "#E7ECF4" }
      },
      rightPriceScale: { borderColor: "#D8DEE8" },
      timeScale: { borderColor: "#D8DEE8" }
    });
    if (activeView === "candlestick") {
      const candleSeries = chart.addSeries(CandlestickSeries, {
        upColor: "#138A63",
        downColor: "#B84A3A",
        borderVisible: false,
        wickUpColor: "#138A63",
        wickDownColor: "#B84A3A"
      });
      candleSeries.setData(
        candles.map((point) => ({
          time: point.date.slice(0, 10),
          open: point.open,
          high: point.high,
          low: point.low,
          close: point.close
        }))
      );
    } else {
      const series = chart.addSeries(LineSeries, { color: "#138A63", lineWidth: 2 });
      series.setData(
        firstSeries.map((point) => ({
          time: point.date.slice(0, 10),
          value: point.value
        }))
      );
    }
    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [activeView, artifact, candles, firstSeries, isReady]);

  return (
    <section className="panel">
      <h2>{artifact.title}</h2>
      <div className="chartToolbar" aria-label={t("chartControls")}>
        {supportedViews.includes("line") ? (
          <button
            className={activeView === "line" ? "chartToggle active" : "chartToggle"}
            onClick={() => setView("line")}
            type="button"
            aria-label={t("lineChart")}
            title={t("lineChart")}
          >
            <ChartNoAxesCombined size={16} />
          </button>
        ) : null}
        {canShowCandles ? (
          <button
            className={activeView === "candlestick" ? "chartToggle active" : "chartToggle"}
            onClick={() => setView("candlestick")}
            type="button"
            aria-label={t("candleChart")}
            title={t("candleChart")}
          >
            <SlidersVertical size={16} />
          </button>
        ) : null}
      </div>
      {isReady ? (
        <div className="chartBox" ref={containerRef} />
      ) : (
        <div className="freshness">{t("chartUnavailable")}: {reasonKey ? t(reasonKey) : t("missingData")}</div>
      )}
      {showDownloads && artifact.downloads.length ? (
        <div className="downloadRow">
          {artifact.downloads.map((download) => (
            <a className="downloadChip" href={download.url} key={download.url}>
              {t("download")} {download.format?.toUpperCase() ?? download.filename}
            </a>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function getRenderableSeries(artifact: ChartArtifact): ChartPoint[] {
  const series = artifact.spec.series.find((item) => item.type === "line") ?? artifact.spec.series[0];
  if (!series) {
    return [];
  }
  return series.data;
}
