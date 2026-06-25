import { useState, type FormEvent } from "react";
import type { IngestionFetchRequest, IngestionStatus } from "../../api/client";

const sources = [
  { id: "us_prices", label: "US Stocks 1h" },
  { id: "us_prices_daily", label: "US Stocks Daily" },
  { id: "vn_prices", label: "VN Stocks 1h" },
  { id: "xauusd_prices", label: "XAUUSD 1h" },
  { id: "xauusd_prices_daily", label: "XAUUSD Daily Fallback" },
  { id: "sjc_gold_prices", label: "SJC Gold Daily" }
];

const modes = [
  { id: "latest", label: "Latest daily" },
  { id: "period", label: "Single period" }
] as const;

type Props = {
  status: IngestionStatus | null;
  onRefresh: () => Promise<unknown>;
  onRunFetch: (payload: IngestionFetchRequest) => Promise<void>;
};

export function AdminIngestionPage({ status, onRefresh, onRunFetch }: Props) {
  const [sourceId, setSourceId] = useState("vn_prices");
  const [mode, setMode] = useState<IngestionFetchRequest["mode"]>("latest");
  const [period, setPeriod] = useState("2026-06-18");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await onRunFetch(buildFetchRequest(sourceId, mode, period));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Manual fetch failed");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="adminPage" aria-label="Admin ingestion">
      {error ? <div className="stateBox" role="alert">{error}</div> : null}
      <div className="freshnessCards">
        {(status?.freshness ?? []).map((item) => (
          <article className="metricCard" key={item.dataset}>
            <span>{item.dataset}</span>
            <strong className={item.status === "fresh" ? "up" : "warn"}>{item.status}</strong>
            <small>{item.record_count} records · {item.as_of ?? "no data"}</small>
          </article>
        ))}
        {!status ? <div className="stateBox">Loading ingestion status...</div> : null}
      </div>

      <div className="adminGrid">
        <section className="panel">
          <div className="panelHeader compactHeader">
            <div>
              <h2>Manual Fetch</h2>
              <span className="meta">Latest and single-period fetches only. Historical backfill runs outside the app.</span>
            </div>
          </div>
          <form className="fetchForm" onSubmit={handleSubmit}>
            <label>
              Source
              <select value={sourceId} onChange={(event) => setSourceId(event.target.value)}>
                {sources.map((source) => (
                  <option key={source.id} value={source.id}>{source.label}</option>
                ))}
              </select>
            </label>
            <label>
              Mode
              <select
                value={mode}
                onChange={(event) => setMode(event.target.value as IngestionFetchRequest["mode"])}
              >
                {modes.map((item) => (
                  <option key={item.id} value={item.id}>{item.label}</option>
                ))}
              </select>
            </label>
            {mode === "period" ? (
              <label>
                Period
                <input value={period} onChange={(event) => setPeriod(event.target.value)} />
              </label>
            ) : null}
            <div className="formActions">
              <button className="primaryButton" disabled={isSubmitting} type="submit">
                {isSubmitting ? "Running" : "Run fetch"}
              </button>
              <button className="textButton" onClick={() => void onRefresh()} type="button">
                Refresh
              </button>
            </div>
          </form>
        </section>

        <section className="panel">
          <div className="panelHeader compactHeader">
            <div>
              <h2>Diagnostics</h2>
              <span className="meta">Latest non-secret job context.</span>
            </div>
          </div>
          <div className="diagnosticsBox">
            {status?.jobs[0] ? JSON.stringify(status.jobs[0].diagnostics, null, 2) : "No jobs yet"}
          </div>
        </section>
      </div>

      <section className="panel">
        <div className="panelHeader compactHeader">
          <div>
            <h2>Job History</h2>
            <span className="meta">Scheduled and manual ingestion outcomes.</span>
          </div>
        </div>
        <div className="marketDataTable">
          <table>
            <thead>
              <tr>
                <th>Job</th>
                <th>Source</th>
                <th>Trigger</th>
                <th>Status</th>
                <th>Period</th>
                <th>Records</th>
              </tr>
            </thead>
            <tbody>
              {(status?.jobs ?? []).map((job) => (
                <tr key={job.job_id}>
                  <td>{job.job_id}</td>
                  <td>{job.source_id}</td>
                  <td>{job.trigger}</td>
                  <td className={job.status === "success" ? "up" : "warn"}>{job.status}</td>
                  <td>{job.period}</td>
                  <td>{job.record_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </section>
  );
}

function buildFetchRequest(
  sourceId: string,
  mode: IngestionFetchRequest["mode"],
  period: string
): IngestionFetchRequest {
  if (mode === "period") {
    return { source_id: sourceId, mode, period };
  }
  return { source_id: sourceId, mode };
}
