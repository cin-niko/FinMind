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
        {run.output.freshness.map((freshness) => (
          <div className="freshness" key={`${freshness.dataset}-${freshness.as_of}`}>
            {freshness.dataset}: {freshness.status} as of {freshness.as_of}
          </div>
        ))}
        {run.output.sections.map((section) => (
          <article className="sectionBlock" key={section.title}>
            <h3>{section.title}</h3>
            <p>{section.content}</p>
            <div className="citationRefs">Citations: {section.citations.join(", ")}</div>
          </article>
        ))}
      </section>
      <section className="panel">
        <h2>Execution</h2>
        <div className="stageList">
          {run.output.visible_execution.stages.map((stage) => (
            <span className="stageChip" key={stage}>
              {stage}
            </span>
          ))}
        </div>
        <div className="meta">Tool status: {run.output.visible_execution.tool_status}</div>
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
