import { X } from "lucide-react";
import type { ChatArtifact } from "./mockChat";
import type { WorkflowRun } from "../../api/client";
import { MarketChart } from "../charts/MarketChart";

type Props = {
  artifact: ChatArtifact | null;
  selectedCitationId?: string | null;
  run?: WorkflowRun | null;
  onClose: () => void;
};

export function ArtifactPanel({ artifact, selectedCitationId, run, onClose }: Props) {
  if (!artifact && !selectedCitationId) {
    return null;
  }
  const selectedChart =
    artifact?.kind === "chart"
      ? run?.output.artifacts.find(
          (item) => item.artifact_type === "chart" && item.artifact_id === artifact.artifactId
        )
      : null;
  const selectedFile =
    artifact?.kind === "file"
      ? run?.output.artifacts.find(
          (item) => item.artifact_type === "file" && item.artifact_id === artifact.artifactId
        )
      : null;

  return (
    <aside className="artifactPanel" aria-label="Artifact detail">
      <header className="artifactHeader">
        <h2>{selectedCitationId ? "Citations" : artifact?.title}</h2>
        <button className="iconButton" onClick={onClose} type="button" aria-label="Close artifact">
          <X size={18} />
        </button>
      </header>
      <div className="artifactBody">
        {artifact?.kind === "chart" && selectedChart?.artifact_type === "chart" ? (
          <MarketChart artifact={selectedChart} />
        ) : null}
        {artifact?.kind === "file" && selectedFile?.artifact_type === "file" ? (
          <div className="fileViewer">
            <div className="freshness">
              {selectedFile.file.filename} · {selectedFile.file.mime_type}
              {selectedFile.file.size_bytes ? ` · ${Math.round(selectedFile.file.size_bytes / 1024)} KB` : ""}
            </div>
            {selectedFile.file.mime_type === "application/pdf" || selectedFile.file.mime_type.startsWith("image/") ? (
              <iframe className="fileFrame" src={selectedFile.file.url} title={selectedFile.title} />
            ) : (
              <a className="downloadChip" href={selectedFile.file.url}>
                Open file
              </a>
            )}
            {selectedFile.downloads.length ? (
              <div className="downloadRow">
                {selectedFile.downloads.map((download) => (
                  <a className="downloadChip" href={download.url} key={download.url}>
                    Download {download.filename}
                  </a>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}
        {selectedCitationId && run ? (
          <ul className="citationList">
            {run.output.citations.map((citation) => (
              <li
                className={citation.citation_id === selectedCitationId ? "selected" : ""}
                id={`citation-${citation.citation_id}`}
                key={citation.citation_id}
              >
                <strong>{citation.label}</strong>
                <span>{citation.source_id}</span>
                <span>{citation.dataset_id}</span>
                <span>{citation.timestamp}</span>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </aside>
  );
}
