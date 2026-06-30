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
import { summarizeWorkflow } from "./workflowCatalog";

type Props = {
  onRunStart: (workflowId: string, symbol: string, market: string) => void;
  onSessionExpired: () => void;
};

export function WorkflowPage({ onRunStart, onSessionExpired }: Props) {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [market, setMarket] = useState("VN_STOCK");
  const [symbol, setSymbol] = useState("");
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
  const symbolInput = selected?.required_inputs.find((input) => input.name === "symbol");
  const symbolValue = symbol.trim().toUpperCase();
  const requiresSymbol = Boolean(symbolInput?.required);

  function handleRun() {
    if (!selected || !selectedMarket || (requiresSymbol && !symbolValue)) {
      return;
    }
    onRunStart(selected.id, symbolValue, selectedMarket);
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
          <WorkflowCard
            key={workflow.id}
            workflow={workflow}
            onSelect={() => {
              setSelectedId(workflow.id);
              setMarket(workflow.market_scope[0] ?? "VN_STOCK");
              setSymbol("");
            }}
          />
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
                {scope === "VN_STOCK" ? "VN stocks" : "US stocks"}
              </option>
            ))}
            <option disabled value="BTC">
              BTC (future)
            </option>
          </select>
        </label>
        {symbolInput ? (
          <label>
            Symbol
            <input
              autoCapitalize="characters"
              value={symbol}
              onChange={(event) => setSymbol(event.target.value)}
              placeholder="VCB"
            />
          </label>
        ) : null}
        <button
          className="primaryButton"
          disabled={!selectedMarket || (requiresSymbol && !symbolValue)}
          onClick={handleRun}
          type="button"
        >
          <Play size={16} /> Run
        </button>
      </section>
      <section className="panel">
        <h2>{selected.title}</h2>
        <p>{selected.description}</p>
        <div className="meta">Markets: {selected.market_scope.join(", ")}</div>
        <div className="meta">Sections: {selected.output_sections.join(", ")}</div>
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

function WorkflowCard({
  workflow,
  onSelect,
}: {
  workflow: Workflow;
  onSelect: () => void;
}) {
  const summary = summarizeWorkflow(workflow);
  return (
    <button className="workflowCard" onClick={onSelect} type="button">
      <span className="meta">{summary.metadata}</span>
      <h2>{summary.title}</h2>
      <p>{summary.description}</p>
      <div className="workflowMeta">Sections: {summary.sections}</div>
      <div className="stageList">
        {summary.stages.slice(0, 4).map((stage) => (
          <span className="stageChip" key={stage}>
            {stage}
          </span>
        ))}
      </div>
    </button>
  );
}
