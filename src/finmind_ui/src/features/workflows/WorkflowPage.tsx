import { useEffect, useState } from "react";
import { Play, X } from "lucide-react";
import {
  isUnauthorizedError,
  listWorkflows,
  type Workflow,
} from "../../api/client";
import { EmptyState, ErrorAlert, LoadingState } from "../../components/layout";
import {
  formatWorkflowMarket,
  isSupportedWorkflowMarket,
  summarizeWorkflow,
} from "./workflowCatalog";
import { useI18n } from "../settings/i18n";

type Props = {
  onRunStart: (workflowId: string, symbol: string, market: string) => void;
  onSessionExpired: () => void;
};

export function WorkflowPage({ onRunStart, onSessionExpired }: Props) {
  const { language, t } = useI18n();
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
        setError(t("workflowLoadFailed"));
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
    if (
      !selected ||
      !isSupportedWorkflowMarket(selectedMarket) ||
      (requiresSymbol && !symbolValue)
    ) {
      return;
    }
    onRunStart(selected.id, symbolValue, selectedMarket);
  }

  if (loading) {
    return <LoadingState />;
  }

  if (!workflows.length) {
    return <EmptyState message={t("noWorkflows")} />;
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
              aria-label={t("closeWorkflowDetails")}
            >
              <X size={16} />
            </button>
            <div className="workflowDialogBody">
              <WorkflowSummary workflow={selected} titleId="workflow-dialog-title" />
            </div>
            {error ? <ErrorAlert message={error} /> : null}
            {selected.id !== "gold-technical-analysis" ? (
              <div className="workflowRunOptions">
                <label>
                  {t("market")}
                  <select value={selectedMarket} onChange={(event) => setMarket(event.target.value)}>
                    {selected.market_scope.map((scope) => (
                      <option
                        key={scope}
                        value={scope}
                        disabled={!isSupportedWorkflowMarket(scope)}
                      >
                        {formatWorkflowMarket(scope, language)}
                      </option>
                    ))}
                  </select>
                </label>
                {symbolInput ? (
                  <label>
                    {t("symbol")}
                    <input
                      autoCapitalize="characters"
                      value={symbol}
                      onChange={(event) => setSymbol(event.target.value)}
                      placeholder="VCB"
                    />
                  </label>
                ) : null}
              </div>
            ) : null}
            <button
              className="primaryButton"
              disabled={
                !isSupportedWorkflowMarket(selectedMarket) ||
                (requiresSymbol && !symbolValue)
              }
              onClick={handleRun}
              type="button"
            >
              <Play size={16} /> {t("run")}
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
  const { language, t } = useI18n();
  const summary = summarizeWorkflow(workflow, language);
  return (
    <>
      <h2 id={titleId}>{summary.title}</h2>
      <p>{summary.description}</p>
      <dl className="workflowMeta">
        <div>
          <dt>{t("markets")}</dt>
          <dd>{summary.markets.join(", ")}</dd>
        </div>
        <div>
          <dt>{t("inputs")}</dt>
          <dd>{summary.requiredInputs.join(", ")}</dd>
        </div>
        <div>
          <dt>{t("stages")}</dt>
          <dd>{summary.stages.join(" -> ")}</dd>
        </div>
        <div>
          <dt>{t("sections")}</dt>
          <dd>{summary.sections.join(", ")}</dd>
        </div>
        <div>
          <dt>{t("evidence")}</dt>
          <dd>
            {summary.citationLabel}; {summary.chartLabel}
          </dd>
        </div>
      </dl>
    </>
  );
}
