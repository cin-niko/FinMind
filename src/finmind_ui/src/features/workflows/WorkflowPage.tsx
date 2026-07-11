import { useEffect, useState } from "react";
import { Play, X } from "lucide-react";
import {
  isUnauthorizedError,
  listWorkflows,
  type Workflow,
} from "../../api/client";
import { EmptyState, ErrorAlert, LoadingState } from "../../components/layout";
import { marketLabel, summarizeWorkflow } from "./workflowCatalog";

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

  return (
    <>
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
      {selected ? (
        <div className="workflowDialogOverlay" onClick={() => setSelectedId(null)}>
          <section
            className="workflowDialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="workflow-dialog-title"
            onClick={(event) => event.stopPropagation()}
          >
            <button
              className="dialogCloseButton"
              onClick={() => setSelectedId(null)}
              type="button"
              aria-label="Close workflow details"
            >
              <X size={16} />
            </button>
            <div className="workflowDialogBody">
              <WorkflowSummary workflow={selected} titleId="workflow-dialog-title" />
            </div>
            {error ? <ErrorAlert message={error} /> : null}
            <div className="workflowRunOptions">
              <label>
                Market
                <select value={selectedMarket} onChange={(event) => setMarket(event.target.value)}>
                  {selected.market_scope.map((scope) => (
                    <option key={scope} value={scope}>
                      {marketLabel(scope)}
                    </option>
                  ))}
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
            </div>
            <button
              className="primaryButton"
              disabled={!selectedMarket || (requiresSymbol && !symbolValue)}
              onClick={handleRun}
              type="button"
            >
              <Play size={16} /> Run
            </button>
          </section>
        </div>
      ) : null}
    </>
  );
}

function WorkflowCard({
  workflow,
  onSelect,
}: {
  workflow: Workflow;
  onSelect: () => void;
}) {
  return (
    <button className="workflowCard" onClick={onSelect} type="button">
      <WorkflowSummary workflow={workflow} />
    </button>
  );
}

function WorkflowSummary({
  workflow,
  titleId,
}: {
  workflow: Workflow;
  titleId?: string;
}) {
  const summary = summarizeWorkflow(workflow);
  return (
    <>
      <h2 id={titleId}>{summary.title}</h2>
      <p>{summary.description}</p>
      <dl className="workflowMeta">
        <div>
          <dt>Markets</dt>
          <dd>{summary.markets.join(", ")}</dd>
        </div>
        <div>
          <dt>Inputs</dt>
          <dd>{summary.requiredInputs.join(", ")}</dd>
        </div>
        <div>
          <dt>Stages</dt>
          <dd>{summary.stages.join(" -> ")}</dd>
        </div>
        <div>
          <dt>Sections</dt>
          <dd>{summary.sections.join(", ")}</dd>
        </div>
        <div>
          <dt>Evidence</dt>
          <dd>
            {summary.citationLabel}; {summary.chartLabel}
          </dd>
        </div>
      </dl>
    </>
  );
}
