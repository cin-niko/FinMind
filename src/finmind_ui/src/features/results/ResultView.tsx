import { EmptyState } from "../../components/layout";
import type { WorkflowRun } from "../../api/client";
import { MarketChart } from "../charts/MarketChart";

export function ResultView({ run }: { run: WorkflowRun | null }) {
  if (!run) {
    return <EmptyState message="No workflow run selected." />;
  }

  return (
    <div className="resultGrid">
      <section className="panel">
        <div className="panelHeader">
          <h2>Result</h2>
          <span className="badge">{run.status}</span>
        </div>
        <div className="freshness">
          Data quality: {run.output.quality.quality_status} · {run.output.quality.freshness_summary}
        </div>
        <div className="freshness">
          Collection: {run.output.collection.status} · {run.output.collection.requested_dataset_groups.join(", ")}
        </div>
        {run.output.collection.warnings.length ? (
          <div className="freshness">Collection warnings: {run.output.collection.warnings.join(", ")}</div>
        ) : null}
        {run.output.freshness.map((freshness) => (
          <div className="freshness" key={`${freshness.dataset}-${freshness.as_of}`}>
            {freshness.dataset}: {freshness.status} as of {freshness.as_of}
          </div>
        ))}
        {run.output.sections.map((section) => (
          <article className="sectionBlock" key={section.title}>
            <h3>{section.title}</h3>
            <div className="meta">Status: {section.status}</div>
            <p>{section.content}</p>
            {section.warnings.length ? (
              <div className="freshness">Warnings: {section.warnings.join(", ")}</div>
            ) : null}
            <div className="citationRefs">Citations: {section.citations.join(", ")}</div>
          </article>
        ))}
      </section>
      <section className="panel">
        <h2>Execution</h2>
        <div className="stageList">
          {run.output.visible_execution.stages.map((stage) => (
            <span className="stageChip" key={stage.id}>
              {stage.id}: {stage.status}
            </span>
          ))}
        </div>
        <div className="meta">Tool status: {run.output.visible_execution.tool_status}</div>
        <div className="stageList">
          {run.output.collection.provider_results.map((provider) => (
            <span className="stageChip" key={`${provider.provider_id}-${provider.dataset_groups.join("-")}`}>
              {provider.provider_id}: {provider.status}
            </span>
          ))}
        </div>
      </section>
      <section className="panel">
        <h2>Citations</h2>
        <ul className="citationList">
          {run.output.citations.map((citation) => (
            <li key={citation.citation_id}>
              <strong>{citation.label}</strong>
              <span>{citation.source_type}</span>
              <span>{citation.timestamp}</span>
            </li>
          ))}
        </ul>
      </section>
      {run.output.artifacts.chart ? <MarketChart artifact={run.output.artifacts.chart} /> : null}
    </div>
  );
}
