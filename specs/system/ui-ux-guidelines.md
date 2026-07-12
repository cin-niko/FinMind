---
id: SPEC-SYSTEM-UI-UX-GUIDELINES-FINMIND
status: active
last_review: 2026-07-11
implements:
  - src/finmind_ui
validated_by: []
adr_refs:
  - docs/adr/ADR-003-artifact-and-citation-inspection-contract.md
---

# UI/UX Guidelines

FinMind is an internal financial research platform, not a marketing site. The
first screen after login must be the usable application shell. Current active
surfaces are the chat-first shell, workflows entry points, and mock artifact
detail. Phase 02 supplies the fixed-workflow foundation, and Phase 03 owns the
active VN stock and gold workflow experience. Production agentic chatflow,
native market data, admin ingestion, and external plugin surfaces remain roadmap
concepts until their bounded specs make them canonical.

## Product Classification

- Product type: agentic financial research platform / fintech dashboard
- Audience: internal finance researcher/admin
- Primary tasks: ask mock chat-first finance questions, inspect trusted mock chat
  artifacts, run fixed workflows, inspect cited workflow results, and inspect
  artifacts produced by active workflows
- Stack target: React/Vite frontend consuming FastAPI JSON APIs
- Chart target: Lightweight Charts for OHLC/candlestick and market-series panels

## Design Principles

- Evidence before prose: citations, source coverage, and artifact status must be visible near generated workflow answers and chat artifacts.
- Chat-first shell: the default primary surface after login is a new chat composer, with workflows available from the left rail.
- Roadmap surfaces are not active navigation: Market, Admin ingestion, production
  chat orchestration, and plugin surfaces require new bounded specs before they
  become canonical.
- Operational clarity: ingestion status, unavailable-evidence limitations,
  failed conversations, and unsupported markets must be visible without reading
  logs.
- Dense but legible: prioritize compact navigation, tables, toolbars, split panes, and fixed-height panels.
- No raw reasoning exposure: show stages, role status, tool status, citations, and artifacts; do not show hidden model reasoning transcripts.
- Stable layout: hover, loading, validation, and chart states must not resize the shell or shift critical controls.

## Visual System

Use a light professional theme by default with a Perplexity-inspired ledger treatment: warm off-white canvas, charcoal text, quiet neutral rail, thin warm-gray dividers, restrained teal focus/selection accents, and amber/brass reserved for primary workflow actions, warnings, and coverage states. The UI must not read as generic white-card/blue-SaaS chrome. Define tokens so dark mode can be added later without rewriting component contracts.

| Role | Token | Hex | Usage |
|------|-------|-----|-------|
| Background | `bg-base` | `#FAF9F5` | App shell and page background |
| Rail | `rail-bg` | `#F5F3EE` | Left navigation rail |
| Surface | `surface-1` | `#FFFEFB` | Panels, cards, top bars, toolbars |
| Surface Raised | `surface-2` | `#FBFAF6` | Secondary panels and artifact blocks |
| Selected Row | `surface-selected` | `#EBE7DF` | Active nav row and selected history row only |
| Border | `border-subtle` | `#DDD8CE` | Panel, rail, and table dividers |
| Text Primary | `text-primary` | `#191917` | Main labels and body copy |
| Text Secondary | `text-secondary` | `#746F65` | Metadata, helper text |
| Accent Teal | `accent-teal` | `#2F6654` | Selected icons, focus rings, send button, chart highlights |
| Accent Teal Strong | `accent-teal-strong` | `#285746` | Active controls and hover states |
| Amber | `accent-amber` | `#D09A2D` | Primary workflow run CTA, warnings, and coverage status |
| Success | `success` | `#138A63` | Completed states and bullish candles |
| Danger | `danger` | `#B9433A` | Failed jobs, bearish candles, destructive states |
| Warning | `warning` | `#D09A2D` | Unavailable evidence and limitations |

Avoid gradient-orb, bokeh, decorative hero, generic white-card/blue-SaaS, heavy beige archive styling, purple-blue, and marketing-card-heavy treatments.

## Shell

Desktop shell uses a fixed left rail plus a main work area. Chat artifact detail uses a right-side split panel on desktop and a full-screen artifact view on mobile.

- Left rail width: 220-248px desktop, collapsible to icon rail on narrower screens.
- Primary nav rows use icon + text for `New Chat` and `Workflows`.
- Primary nav rows are flat text rows by default. Do not draw each row as an outlined button.
- Only the active nav row or selected history row receives `surface-selected`; avoid simultaneous white, gray, and yellow row-selection backgrounds. Active rail rows do not increase font weight.
- Yellow/amber must not be used as a rail selection color. Reserve it for run actions, warnings, and content-level coverage state.
- `History` is one rail section for persisted conversations. A workflow-created
  conversation appears here as soon as it is started; do not expose a separate
  workflow-run history or split history by relative dates in V1.
- Top context bar is compact, pinned inside the primary content pane, and aligned with the artifact detail header when the artifact panel is open. In chat, it shows only the active conversation title matching the History label, falling back to `New Chat` before a conversation exists. Other surfaces show their current surface title only; surface metadata and filters belong inside the active work area.
- Chat artifact detail headers are compact and pinned inside the right-side artifact panel. They use the same small title size as the chat header and show the artifact title plus close control only; artifact kind and metadata belong in the panel body.
- The logout control belongs in the left rail footer with the current role/session summary, not in the top context bar.
- Desktop shell scrolling is separated by panel: the left rail keeps brand/nav and logout visible while history scrolls; the primary content pane keeps its header visible; chat keeps the composer pinned to the bottom while only messages scroll; the right artifact panel keeps its header visible while only artifact body content scrolls.
- Desktop left rail may collapse to a compact icon rail. The right artifact/citation panel may fully collapse so the primary pane reclaims the width; selecting a citation or artifact opens it again. Collapse controls belong in the respective panel headers, use icon-only buttons with accessible labels, and must not destroy the active chat, artifact, or citation selection state.
- No large hero areas.

Navigation is roadmap-aware:

- Current active path: New Chat, Workflows, History
- Roadmap paths: native Market data, Admin ingestion, production chat
  orchestration, and plugin surfaces require new feature specs before appearing
  as active app-shell navigation.

## Required Screens

### Login

- Centered single-column layout with a large hero title above a soft card panel; no decorative grid or hero background.
- Login uses the same light ledger token palette as the authenticated app shell: warm off-white shell (`bg-base`), charcoal hero title in Inter, thin warm-gray borders, and no generic blue SaaS chrome.
- Primary submit control uses the neutral charcoal token (`text-primary` background, `surface-1` text). Teal and amber accents are reserved for in-app focus, run actions, and warnings, and MUST NOT be used as the login submit color.
- Username and password inputs use associated `<label htmlFor>` bindings; label text uses secondary color at normal weight (not bold) so it reads as field metadata rather than a heading.
- Password field MUST provide a show/hide toggle implemented as a `<button type="button">` inside the field with `aria-label` reflecting the current state and `aria-pressed` for assistive tech.
- Startup configuration failure state
- Submit button with loading state (label switches to a "Signing in" affordance and the control is disabled)
- Error messages use `role="alert"` and appear above the input fields

### Workflow

- Workflow catalog cards for fixed system-defined workflows
- Market/instrument inputs expose only supported VN stock and gold choices as
  enabled runnable selections for `003-vn-gold-dataflows-workflows`.
- Market identifiers in catalog summaries and selectors use human-readable
  labels rather than raw contract values; each supported market maps through a
  shared, closed UI label mapping. An unsupported market is a contract error
  and MUST render as a generic unavailable label without exposing or humanizing
  its raw identifier. Unsupported selections are disabled and cannot run.
- Roadmap market or asset choices may appear only as disabled or clearly marked
  future/out-of-scope preview options; users must not be able to select them and
  discover the limitation only after clicking Run.
- Amber run button
- Validation messages near fields
- Stage status chips
- Result panel with citations, chart artifacts, and step/grounding status
- Workflow-backed assistant responses in transcript-style views use a frameless
  editorial presentation for the assistant answer body rather than a full white
  message card.
- User prompts remain visually distinct bubbles, while assistant responses do
  not repeat `You` or `FinMind` role headers above each message.
- Workflow execution visibility inside assistant responses appears as a compact
  collapsible metadata block above the answer body. Its summary label is
  `Working` while incomplete and `Completed N steps` when complete.
- The execution-visibility block opens by default while work is still running,
  collapses by default once complete, and remains user-expandable after
  completion.
- Execution-visibility steps use lighter secondary styling, connector lines,
  step-type icons, product-facing labels, optional input subtext such as the
  active symbol, and a terminal `Done` row. They show safe stage metadata only,
  not raw reasoning transcripts.

### Conversation Detail

- Conversation list and detail view with initiating workflow metadata, first
  assistant message, its citations and artifacts, visible execution status, and
  safe failure summary
- Failed workflow-created conversations distinguishable from successful ones;
  unavailable evidence and limitations remain visible in either outcome

### Chat

- Default surface after login is a new chat composer
- Transcript area uses a simple centered conversation layout
- Composer is fixed to the bottom of the chat work area; only the message transcript scrolls.
- After a user submits any chat message, including the first message in a new chat, that latest user message must align to the top of the chat transcript viewport so the answer can unfold below it.
- `001-mvp-ui` chat responses are deterministic mock responses, not production
  orchestrator output
- User prompts may remain bubble-style, but workflow-backed assistant responses
  should read like editorial research notes in the transcript instead of
  stacked generic cards.
- Chat messages may show trusted mock inline visual blocks generated from local templates
- File and chart artifacts appear as cards after the relevant answer content.
- Clicking an artifact card opens the full artifact viewer in the right-side
  panel on desktop or equivalent full-screen artifact view on mobile.
- Inline citation chips appear at the cited answer location. Clicking a citation
  chip opens the citations view in the same right-side panel, shows the complete
  source list for the answer or conversation, and scrolls to the selected source.
- Citations are not artifact cards; they are source/evidence inspection controls.
- Chat must not render citation bundle or evidence list artifact cards when
  inline citation chips and citation-panel inspection are available.

### Artifact Detail

- Clicking an artifact card opens the artifact in a right-side detail panel on
  desktop or a full-screen artifact view on mobile.
- Artifact detail headers are compact and pinned inside the detail panel.
- The artifact panel shows the full artifact viewer, not a small preview.
- Chart artifact panels may expose view switches such as `Line` and
  `Candlestick` when the artifact declares both views.
- Artifact panels expose download actions only when the artifact is ready and a
  valid download is declared.
- Artifact detail must never execute arbitrary generated HTML.

## Accessibility

- Semantic buttons/links and `cursor: pointer`
- Keyboard tab order follows visual order
- Focus states use visible 2px blue focus rings
- Errors use `role="alert"` or `aria-live`
- Loading states use skeletons or progress indicators
- Empty states explain what happened and offer the next action
- Respect `prefers-reduced-motion`
- Charts include accessible descriptions and a non-visual data access path, such
  as a declared CSV download, without requiring a price table in the main answer
