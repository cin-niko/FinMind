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
      layout: { background: { color: "#FFFFFF" }, textColor: "#172033" },
      grid: {
        vertLines: { color: "#E7ECF4" },
        horzLines: { color: "#E7ECF4" }
      },
      rightPriceScale: { borderColor: "#D8DEE8" },
      timeScale: { borderColor: "#D8DEE8" }
    });
    const series = chart.addSeries(LineSeries, { color: "#138A63", lineWidth: 2 });
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
