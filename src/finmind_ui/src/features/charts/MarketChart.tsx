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
        <summary>Data table ({artifact.payload.table.length} rows)</summary>
        <table className="mdTable">
          <thead>
            <tr>
              <th>Date</th>
              <th>Close</th>
              <th>Volume</th>
            </tr>
          </thead>
          <tbody>
            {artifact.payload.table.slice(0, 50).map((row, index) => (
              <tr key={`${row.date}-${index}`}>
                <td>{row.date}</td>
                <td>{row.close}</td>
                <td>{row.volume}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </section>
  );
}
