import { useEffect, useState } from "react";
import { Play } from "lucide-react";
import { listWorkflows, runWorkflow, type Workflow, type WorkflowRun } from "../../api/client";
import { EmptyState, ErrorAlert, LoadingState } from "../../components/layout";

type Props = {
  onRunComplete: (run: WorkflowRun) => void;
};

export function WorkflowPage({ onRunComplete }: Props) {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [market, setMarket] = useState("VN_STOCK");
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    listWorkflows()
      .then((items) => {
        setWorkflows(items);
        setSelectedId(items[0]?.id ?? "");
      })
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Failed to load workflows"))
      .finally(() => setLoading(false));
  }, []);

  const selected = workflows.find((workflow) => workflow.id === selectedId);

  async function handleRun() {
    if (!selected) {
      return;
    }
    setRunning(true);
    setError("");
    try {
      const run = await runWorkflow(selected.id, market);
      onRunComplete(run);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Workflow failed");
    } finally {
      setRunning(false);
    }
  }

  if (loading) {
    return <LoadingState />;
  }

  if (!selected) {
    return <EmptyState message="No workflows available." />;
  }

  return (
    <div className="workflowGrid">
      <section className="panel">
        <h2>Workflow</h2>
        {error ? <ErrorAlert message={error} /> : null}
        <label>
          Catalog
          <select value={selectedId} onChange={(event) => setSelectedId(event.target.value)}>
            {workflows.map((workflow) => (
              <option key={workflow.id} value={workflow.id}>
                {workflow.title}
              </option>
            ))}
          </select>
        </label>
        <label>
          Market
          <select value={market} onChange={(event) => setMarket(event.target.value)}>
            <option value="VN_STOCK">VN stocks</option>
            <option value="GOLD">Gold</option>
            <option value="US_STOCK">US stocks</option>
            <option value="BTC">BTC</option>
          </select>
        </label>
        <button className="primaryButton" disabled={running} onClick={handleRun} type="button">
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
