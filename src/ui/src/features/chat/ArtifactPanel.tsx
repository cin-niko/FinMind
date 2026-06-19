import { X } from "lucide-react";
import type { ChatArtifact } from "./mockChat";

type Props = {
  artifact: ChatArtifact | null;
  onClose: () => void;
};

export function ArtifactPanel({ artifact, onClose }: Props) {
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
        <span className="meta">{artifact.kind}</span>
        <p>{artifact.summary}</p>
        {artifact.kind === "report" ? (
          <div className="reportPreview">
            <h3>Mock Report</h3>
            <p>
              This trusted local template represents a larger report generated inside chat. V1 does
              not execute arbitrary LLM HTML.
            </p>
            <table>
              <thead>
                <tr>
                  <th>Section</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Market context</td>
                  <td>Mock complete</td>
                </tr>
                <tr>
                  <td>Risk notes</td>
                  <td>Mock complete</td>
                </tr>
              </tbody>
            </table>
          </div>
        ) : null}
        {artifact.kind === "citationBundle" || artifact.kind === "evidenceList" ? (
          <ul className="citationList">
            <li>
              <strong>Mock Source A</strong>
              <span>Demo citation pattern</span>
              <span>2026-06-18 09:20</span>
            </li>
            <li>
              <strong>Mock Source B</strong>
              <span>Demo evidence pattern</span>
              <span>2026-06-18 08:40</span>
            </li>
          </ul>
        ) : null}
      </div>
    </aside>
  );
}
