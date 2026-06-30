import { X } from "lucide-react";
import type { ChatArtifact } from "./mockChat";
import type { WorkflowRun } from "../../api/client";
import { MarketChart } from "../charts/MarketChart";

type Props = {
  artifact: ChatArtifact | null;
  run?: WorkflowRun | null;
  onClose: () => void;
};

export function ArtifactPanel({ artifact, run, onClose }: Props) {
  if (!artifact) {
    return null;
  }

  return (
    <aside className="artifactPanel" aria-label="Artifact detail">
      <header className="artifactHeader">
        <h2>{artifact.title}</h2>
        <button className="iconButton" onClick={onClose} type="button" aria-label="Close artifact">
          <X size={18} />
        </button>
      </header>
      <div className="artifactBody">
        {artifact.kind === "chart" && run?.output.artifacts.chart ? (
          <MarketChart artifact={run.output.artifacts.chart} />
        ) : null}
        {artifact.kind === "citationBundle" && run ? (
          <ul className="citationList">
            {run.output.citations.map((citation) => (
              <li key={citation.citation_id}>
                <strong>{citation.label}</strong>
                <span>{citation.dataset_id}</span>
                <span>{citation.timestamp}</span>
              </li>
            ))}
          </ul>
        ) : null}
        {artifact.kind === "evidenceList" && run ? (
          <div className="evidencePanel">
            <div className="freshness">Grounding: {run.output.grounding.grounding_status}</div>
            {run.output.grounding.blocked_claims.length ? (
              <div className="freshness">Blocked: {run.output.grounding.blocked_claims.join(", ")}</div>
            ) : null}
            <h3>Collection</h3>
            <div className="freshness">Status: {run.output.collection.status}</div>
            <div className="freshness">Groups: {run.output.collection.requested_dataset_groups.join(", ")}</div>
            {run.output.collection.warnings.length ? (
              <div className="freshness">Warnings: {run.output.collection.warnings.join(", ")}</div>
            ) : null}
            <h3>Providers</h3>
            <div className="stageList">
              {run.output.collection.provider_results.map((provider) => (
                <span className="stageChip" key={provider.provider_id}>
                  {provider.provider_id}: {provider.status}
                </span>
              ))}
            </div>
            <h3>Steps</h3>
            <div className="stageList">
              {run.output.steps.map((step) => (
                <span className="stageChip" key={step.id}>
                  {step.id}: {step.status}
                </span>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </aside>
  );
}
