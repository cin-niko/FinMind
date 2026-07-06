---
id: ADR-003
status: accepted
date: 2026-07-06
deciders:
  - solo
related_specs:
  - specs/system/contracts.md
  - specs/system/state-model.md
  - specs/system/ui-ux-guidelines.md
  - specs/002-workflow/spec.md
  - specs/002-workflow/contracts/api-contract.md
related_risks: []
---

# ADR-003: Artifact And Citation Inspection Contract

## Status

Accepted

## Context

Phase 02 workflow answers need two inspectable support surfaces:

- Generated outputs such as files and charts that users can open and download.
- Citations/sources that ground answer claims and let users inspect internal
  fetched data or outbound source links.

Earlier contracts treated chart/table/computed/inline visualization outputs as
separate artifact types and considered citation bundles as artifact-like UI
cards. This made the artifact taxonomy broader than the actual product need and
blurred the boundary between generated outputs and evidence sources.

## Decision

FinMind MUST model production artifacts as a parent `Artifact` with
`artifact_type` as the top-level discriminator. Phase 02 supports:

- `file`: a physical asset with `file_type`, `mime_type`, filename, file URL,
  status, download behavior, and source refs when applicable.
- `chart`: a structured chart artifact with chart intent, supported chart views,
  default view, renderable chart spec, status, download options, and source refs.

Citations MUST remain evidence/source references, not artifacts. Inline citation
chips open the shared right panel in citation-list mode, show all sources for
the answer/run, and jump to the clicked source. Artifact cards open the same
right panel in artifact-viewer mode and show the full artifact, not a small
preview.

Chart artifacts SHOULD support line/candlestick switching when both data shapes
are available. Chart artifacts SHOULD avoid rendering a separate price table in
the main answer; raw chart data access should use declared downloads or a future
file artifact.

## Alternatives Considered

| Alternative | Reason Not Chosen |
|-------------|-------------------|
| `document`, `spreadsheet`, `image`, `chart` as top-level artifact types | Too many physical-file categories at the domain level; most are better represented as `artifact_type=file` plus `file_type` and `mime_type`. |
| Single `file` artifact type only | Does not represent the current interactive chart behavior, where the primary artifact is structured chart data rather than a physical file. |
| Generic `visualization` artifact type | Too abstract for Phase 02 because the only required visualization is charting. `chart` is clearer and easier to test. |
| Citation bundle artifact | Blurs generated outputs with evidence sources and makes inline citation inspection harder to reason about. |

## Consequences

- UI can switch on `artifact_type` only at the top level: `file` or `chart`.
- File viewer selection is derived from `file_type`; transport/download behavior
  still uses `mime_type`.
- Chart viewer behavior is derived from chart spec and supported views.
- Citation inspection becomes a right-panel mode rather than an artifact card
  subtype.
- Existing chart contract and UI must migrate away from required table fallback
  rendering in the main answer.

## Validation

- Workflow run responses include only supported artifact types.
- File artifacts preserve `file_type`, `mime_type`, filename, status, and download
  metadata.
- Chart artifacts can render supported views and expose declared downloads.
- Clicking an artifact card opens the right-panel artifact viewer.
- Clicking an inline citation chip opens the right-panel citation list and jumps
  to the selected source.
- No raw agent reasoning, generated HTML, or unsafe embedded external content is
  exposed through artifact or citation inspection.

## References

- `specs/system/contracts.md`
- `specs/system/state-model.md`
- `specs/system/ui-ux-guidelines.md`
- `specs/002-workflow/spec.md`
- `specs/002-workflow/contracts/api-contract.md`
