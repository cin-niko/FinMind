import { X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import type { ChatArtifact, LiveCitation } from "./mockChat";
import type { Artifact, WorkflowRun } from "../../api/client";
import { MarketChart } from "../charts/MarketChart";
import { Markdown } from "../../components/Markdown";

type Props = {
  artifact: ChatArtifact | null;
  selectedCitationId?: string | null;
  citationFlashKey?: number;
  run?: WorkflowRun | null;
  citations?: LiveCitation[];
  citationOrdinals?: Map<string, number> | null;
  artifacts?: Artifact[];
  onClose: () => void;
};

const RECORD_TYPE_TITLES: Record<string, string> = {
  company_profile: "Company Profile",
  fundamental: "Fundamental Data",
  generic: "Data Record",
  indicator: "Technical Indicators",
  pattern_evidence: "Pattern Evidence",
  pattern_setup: "Pattern Setup",
  price_summary: "Price Summary"
};

function humanizeToken(value: string): string {
  return value
    .split(/[_-]+/g)
    .filter(Boolean)
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
    .join(" ");
}

function formatCitationTitle(citation: LiveCitation): string {
  const baseTitle =
    RECORD_TYPE_TITLES[citation.record_type] ??
    (citation.label && !/[_-]/.test(citation.label) ? citation.label : humanizeToken(citation.record_type));
  const date = citation.timestamp.slice(0, 10);
  return date ? `${baseTitle} (${date})` : baseTitle;
}

export function ArtifactPanel({
  artifact,
  selectedCitationId,
  citationFlashKey = 0,
  run,
  citations,
  artifacts,
  onClose
}: Props) {
  const listRef = useRef<HTMLUListElement | null>(null);
  const [expandedCitationId, setExpandedCitationId] = useState<string | null>(null);

  const resolvedCitations = citations ?? run?.output.citations ?? [];
  const resolvedArtifacts = artifacts ?? run?.output.artifacts ?? [];

  const selectedChart =
    artifact?.kind === "chart"
      ? resolvedArtifacts.find(
          (item) => item.artifact_type === "chart" && item.artifact_id === artifact.artifactId
        )
      : null;
  const selectedFile =
    artifact?.kind === "file"
      ? resolvedArtifacts.find(
          (item) => item.artifact_type === "file" && item.artifact_id === artifact.artifactId
        )
      : null;

  useEffect(() => {
    if (!selectedCitationId || !listRef.current) return;
    const target = listRef.current.querySelector<HTMLElement>(
      `#citation-${CSS.escape(selectedCitationId)}`
    );
    target?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [selectedCitationId, resolvedCitations.length]);

  const expandedCitation = useMemo(
    () =>
      expandedCitationId
        ? resolvedCitations.find((citation) => citation.citation_id === expandedCitationId) ?? null
        : null,
    [expandedCitationId, resolvedCitations]
  );

  if (!artifact && !selectedCitationId) {
    return null;
  }

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
        {selectedCitationId && resolvedCitations.length ? (
          <ul className="citationList" ref={listRef}>
            {resolvedCitations.map((citation) => {
              const title = formatCitationTitle(citation);
              const content = citation.display_content?.trim() || "";
              const isSelected = citation.citation_id === selectedCitationId;
              const flashClass = isSelected
                ? citationFlashKey % 2 === 0
                  ? " flashEven"
                  : " flashOdd"
                : "";
              return (
              <li
                aria-haspopup="dialog"
                className={`${isSelected ? "selected" : ""}${flashClass}`.trim()}
                id={`citation-${citation.citation_id}`}
                key={citation.citation_id}
                onClick={() => setExpandedCitationId(citation.citation_id)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    setExpandedCitationId(citation.citation_id);
                  }
                }}
                role="button"
                tabIndex={0}
              >
                <strong className="citationCardTitle">{title}</strong>
                {content ? (
                  <div className="citationContent">
                    <Markdown content={content} />
                  </div>
                ) : null}
              </li>
              );
            })}
          </ul>
        ) : null}
        {expandedCitation && expandedCitation.display_content ? (
          <div
            className="citationModalOverlay"
            onClick={() => setExpandedCitationId(null)}
            role="presentation"
          >
            <div
              aria-labelledby="citation-modal-title"
              aria-modal="true"
              className="citationModal"
              onClick={(event) => event.stopPropagation()}
              role="dialog"
            >
              <div className="citationModalHeader">
                <h3 id="citation-modal-title">{formatCitationTitle(expandedCitation)}</h3>
                <button
                  aria-label="Close citation"
                  className="dialogCloseButton"
                  onClick={() => setExpandedCitationId(null)}
                  type="button"
                >
                  <X size={18} />
                </button>
              </div>
              <div className="citationModalBody">
                <Markdown content={expandedCitation.display_content} />
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </aside>
  );
}
