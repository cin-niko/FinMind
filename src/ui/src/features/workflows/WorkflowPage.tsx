import { useEffect, useState } from "react";
import { ArrowLeft, Play } from "lucide-react";
import {
  isUnauthorizedError,
  listWorkflows,
  runWorkflow,
  type Workflow,
  type WorkflowRun
} from "../../api/client";
import { EmptyState, ErrorAlert, LoadingState } from "../../components/layout";

type Props = {
  onRunComplete: (run: WorkflowRun) => void;
  onSessionExpired: () => void;
};

export function WorkflowPage({ onRunComplete, onSessionExpired }: Props) {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [market, setMarket] = useState("VN_STOCK");
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    listWorkflows()
      .then((items) => {
        setWorkflows(items);
      })
      .catch((caught) => {
        if (isUnauthorizedError(caught)) {
          onSessionExpired();
          return;
        }
        setError(caught instanceof Error ? caught.message : "Failed to load workflows");
      })
      .finally(() => setLoading(false));
  }, [onSessionExpired]);

  const selected = workflows.find((workflow) => workflow.id === selectedId);
  const selectedMarket =
    selected?.market_scope.includes(market) ? market : selected?.market_scope[0] ?? "";

  async function handleRun() {
    if (!selected || !selectedMarket) {
      return;
    }
    setRunning(true);
    setError("");
    try {
      const run = await runWorkflow(selected.id, selectedMarket);
      onRunComplete(run);
    } catch (caught) {
      if (isUnauthorizedError(caught)) {
        onSessionExpired();
        return;
      }
      setError(caught instanceof Error ? caught.message : "Workflow failed");
    } finally {
      setRunning(false);
    }
  }

  if (loading) {
    return <LoadingState />;
  }

  if (!workflows.length) {
    return <EmptyState message="No workflows available." />;
  }

  if (!selected) {
    return (
      <div className="workflowCatalog">
        {error ? <ErrorAlert message={error} /> : null}
        {workflows.map((workflow) => (
          <button
            className="workflowCard"
            key={workflow.id}
            onClick={() => {
              setSelectedId(workflow.id);
              setMarket(workflow.market_scope[0] ?? "VN_STOCK");
            }}
            type="button"
          >
            <span className="meta">{workflow.market_scope.join(", ")}</span>
            <h2>{workflow.title}</h2>
            <p>Fixed system-defined workflow with cited output, freshness metadata, and chart artifacts.</p>
            <div className="stageList">
              {workflow.stages.slice(0, 4).map((stage) => (
                <span className="stageChip" key={stage}>
                  {stage}
                </span>
              ))}
            </div>
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className="workflowGrid">
      <section className="panel">
        <button className="textButton" onClick={() => setSelectedId(null)} type="button">
          <ArrowLeft size={16} /> Catalog
        </button>
        <h2>Run Workflow</h2>
        {error ? <ErrorAlert message={error} /> : null}
        <div className="selectedWorkflowName">{selected.title}</div>
        <label>
          Market
          <select value={selectedMarket} onChange={(event) => setMarket(event.target.value)}>
            {selected.market_scope.map((scope) => (
              <option key={scope} value={scope}>
                {scope === "VN_STOCK" ? "VN stocks" : "Gold"}
              </option>
            ))}
            <option disabled value="US_STOCK">
              US stocks (future)
            </option>
            <option disabled value="BTC">
              BTC (future)
            </option>
          </select>
        </label>
        <button
          className="primaryButton"
          disabled={running || !selectedMarket}
          onClick={handleRun}
          type="button"
        >
          <Play size={16} /> {running ? "Running" : "Run"}
        </button>
      </section>
      <section className="panel">
        <h2>{selected.title}</h2>
        <div className="meta">Markets: {selected.market_scope.join(", ")}</div>
        <div className="stageList">
          {selected.stages.map((stage) => (
            <span className="stageChip" key={stage}>
              {stage}
            </span>
          ))}
        </div>
        <div className="meta">Charts: {selected.chart_requirements.join(", ")}</div>
      </section>
    </div>
  );
}
