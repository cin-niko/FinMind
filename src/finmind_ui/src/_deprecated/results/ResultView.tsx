import { EmptyState } from "../../components/layout";
import type { WorkflowRun } from "../../api/client";
import { MarketChart } from "../../features/charts/MarketChart";
import { Markdown } from "../../components/Markdown";

export function ResultView({ run }: { run: WorkflowRun | null }) {
  if (!run) {
    return <EmptyState message="No workflow run selected." />;
  }
  const chartArtifact = run.output.artifacts.find((artifact) => artifact.artifact_type === "chart");

  return (
    <div className="resultGrid">
      <section className="panel">
        <div className="panelHeader">
          <h2>Result</h2>
          <span className="badge">{run.status}</span>
        </div>
        <div className="freshness">
          Grounding: {run.output.grounding.grounding_status}
        </div>
        <div className="freshness">
          Collection: {run.output.collection.status} · {run.output.collection.requested_dataset_groups.join(", ")}
        </div>
        {run.output.collection.warnings.length ? (
          <div className="freshness">Collection warnings: {run.output.collection.warnings.join(", ")}</div>
        ) : null}
        {run.output.grounding.blocked_claims.length ? (
          <div className="freshness">Blocked claims: {run.output.grounding.blocked_claims.join(", ")}</div>
        ) : null}
        {run.output.grounding.uncited_claims.length ? (
          <div className="freshness">Uncited claims: {run.output.grounding.uncited_claims.join(", ")}</div>
        ) : null}
        {run.output.sections.map((section) => (
          <article className="sectionBlock" key={section.title}>
            <h3>{section.title}</h3>
            <div className="meta">Status: {section.status}</div>
            <Markdown content={section.content} />
            {section.warnings.length ? (
              <div className="freshness">Warnings: {section.warnings.join(", ")}</div>
            ) : null}
            {section.allowed_claims.length ? (
              <div className="freshness">Allowed: {section.allowed_claims.join(", ")}</div>
            ) : null}
            {section.blocked_claims.length ? (
              <div className="freshness">Blocked: {section.blocked_claims.join(", ")}</div>
            ) : null}
            <div className="citationRefs">Citations: {section.citations.join(", ")}</div>
          </article>
        ))}
      </section>
      <section className="panel">
        <h2>Execution</h2>
        <div className="stageList">
          {run.output.steps.map((step) => (
            <span className="stageChip" key={step.id}>
              {step.id}: {step.status}
            </span>
          ))}
        </div>
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
              <span>{citation.dataset_id}</span>
              <span>{citation.timestamp}</span>
            </li>
          ))}
        </ul>
      </section>
      {chartArtifact?.artifact_type === "chart" ? <MarketChart artifact={chartArtifact} /> : null}
    </div>
  );
}
