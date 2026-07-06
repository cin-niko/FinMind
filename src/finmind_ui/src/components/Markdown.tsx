import { useMemo } from "react";

function escapeHtml(input: string): string {
  return input
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export type CitationDisplay = {
  citation_id: string;
  label: string;
};

function inlineMd(raw: string, citationsById: Map<string, CitationDisplay>): string {
  const escaped = escapeHtml(raw);
  const citationChip = (match: string, citationId: string) => {
    const citation = citationsById.get(citationId);
    if (!citation) {
      return match;
    }
    return `<button class="citationChip inline" data-citation-id="${escapeHtml(citationId)}" type="button">${escapeHtml(citation.label)}</button>`;
  };
  return escaped
    .replace(/\[cite:([A-Za-z0-9_.:-]+)\]/g, citationChip)
    .replace(/\[(citation_[A-Za-z0-9_.:-]+)\]/g, citationChip)
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*]+)\*(?!\*)/g, "$1<em>$2</em>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(
      /\[([^\]]+)\]\(([^)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
    );
}

function splitRow(line: string): string[] {
  const trimmed = line.trim().replace(/^\|/, "").replace(/\|$/, "");
  return trimmed.split("|").map((cell) => cell.trim());
}

function isSeparatorRow(line: string): boolean {
  return /^\s*\|?[\s:|-]*-[\s:|-]*\|?\s*$/.test(line) && line.includes("-");
}

function renderMarkdown(source: string, citations: CitationDisplay[] = []): string {
  const citationsById = new Map(citations.map((citation) => [citation.citation_id, citation]));
  const lines = source.replace(/\r\n/g, "\n").split("\n");
  const out: string[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // fenced code block
    if (/^```/.test(line.trim())) {
      const lang = line.trim().slice(3).trim();
      const code: string[] = [];
      i++;
      while (i < lines.length && !/^```/.test(lines[i].trim())) {
        code.push(lines[i]);
        i++;
      }
      i++; // skip closing fence
      out.push(
        `<pre class="mdCode"><code data-lang="${escapeHtml(lang)}">${escapeHtml(
          code.join("\n")
        )}</code></pre>`
      );
      continue;
    }

    // table
    if (line.includes("|") && i + 1 < lines.length && isSeparatorRow(lines[i + 1])) {
      const header = splitRow(line);
      i += 2;
      const rows: string[][] = [];
      while (i < lines.length && lines[i].includes("|") && lines[i].trim() !== "") {
        rows.push(splitRow(lines[i]));
        i++;
      }
      const head = header
        .map((cell) => `<th>${inlineMd(cell, citationsById)}</th>`)
        .join("");
      const body = rows
        .map(
          (row) =>
            `<tr>${row.map((cell) => `<td>${inlineMd(cell, citationsById)}</td>`).join("")}</tr>`
        )
        .join("");
      out.push(
        `<div class="mdTableWrap"><table class="mdTable"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`
      );
      continue;
    }

    // headings
    const heading = /^(#{1,6})\s+(.*)$/.exec(line);
    if (heading) {
      const level = heading[1].length;
      out.push(`<h${level}>${inlineMd(heading[2], citationsById)}</h${level}>`);
      i++;
      continue;
    }

    // blockquote
    if (/^>\s?/.test(line)) {
      const quote: string[] = [];
      while (i < lines.length && /^>\s?/.test(lines[i])) {
        quote.push(lines[i].replace(/^>\s?/, ""));
        i++;
      }
      out.push(`<blockquote>${inlineMd(quote.join(" "), citationsById)}</blockquote>`);
      continue;
    }

    // unordered list
    if (/^\s*[-*]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*[-*]\s+/, ""));
        i++;
      }
      out.push(
        `<ul>${items.map((item) => `<li>${inlineMd(item, citationsById)}</li>`).join("")}</ul>`
      );
      continue;
    }

    // ordered list
    if (/^\s*\d+\.\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*\d+\.\s+/, ""));
        i++;
      }
      out.push(
        `<ol>${items.map((item) => `<li>${inlineMd(item, citationsById)}</li>`).join("")}</ol>`
      );
      continue;
    }

    // blank line
    if (line.trim() === "") {
      i++;
      continue;
    }

    // paragraph: gather consecutive non-special lines
    const para: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !/^```/.test(lines[i].trim()) &&
      !/^#{1,6}\s+/.test(lines[i]) &&
      !/^>\s?/.test(lines[i]) &&
      !/^\s*[-*]\s+/.test(lines[i]) &&
      !/^\s*\d+\.\s+/.test(lines[i]) &&
      !(lines[i].includes("|") && i + 1 < lines.length && isSeparatorRow(lines[i + 1]))
    ) {
      para.push(lines[i]);
      i++;
    }
    out.push(`<p>${inlineMd(para.join(" "), citationsById)}</p>`);
  }

  return out.join("\n");
}

export function Markdown({
  content,
  citations = [],
  onCitationClick
}: {
  content: string;
  citations?: CitationDisplay[];
  onCitationClick?: (citationId: string) => void;
}) {
  const html = useMemo(() => renderMarkdown(content ?? "", citations), [content, citations]);
  return (
    <div
      className="markdown"
      dangerouslySetInnerHTML={{ __html: html }}
      onClick={(event) => {
        if (!onCitationClick) {
          return;
        }
        const target = event.target as HTMLElement;
        const citationButton = target.closest<HTMLButtonElement>("[data-citation-id]");
        if (citationButton?.dataset.citationId) {
          onCitationClick(citationButton.dataset.citationId);
        }
      }}
    />
  );
}
