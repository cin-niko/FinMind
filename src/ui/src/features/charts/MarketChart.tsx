import { LineSeries, createChart, type IChartApi } from "lightweight-charts";
import { useEffect, useRef } from "react";
import type { WorkflowRun } from "../../api/client";

type ChartArtifact = NonNullable<WorkflowRun["output"]["artifacts"]["chart"]>;

export function MarketChart({ artifact }: { artifact: ChartArtifact }) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }
    const chart: IChartApi = createChart(containerRef.current, {
      height: 260,
      layout: { background: { color: "#111827" }, textColor: "#E5E7EB" },
      grid: {
        vertLines: { color: "#293548" },
        horzLines: { color: "#293548" }
      },
      rightPriceScale: { borderColor: "#293548" },
      timeScale: { borderColor: "#293548" }
    });
    const series = chart.addSeries(LineSeries, { color: "#26A69A", lineWidth: 2 });
    series.setData(
      artifact.payload.series.map((point) => ({
        time: point.time.slice(0, 10),
        value: point.value
      }))
    );
    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [artifact]);

  return (
    <section className="panel">
      <h2>{artifact.title}</h2>
      <div className="chartBox" ref={containerRef} />
      <details>
        <summary>Table</summary>
        <table>
          <thead>
            <tr>
              <th>Record</th>
              <th>Market time</th>
              <th>Close</th>
            </tr>
          </thead>
          <tbody>
            {artifact.payload.table.map((row) => (
              <tr key={row.record_key}>
                <td>{row.record_key}</td>
                <td>{row.market_time}</td>
                <td>{row.close}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </section>
  );
}
