---
id: SPEC-SYSTEM-UI-WORKBENCH-FINMIND
status: active
last_review: 2026-06-18
implements:
  - src/ui
validated_by: []
adr_refs: []
---

# UI Workbench

FinMind is an internal analyst workbench, not a marketing site. The first screen after login must be the usable application shell. Surfaces are introduced by feature phase: chat-first shell, Market, workflow/results in `001-mvp-workflow-platform`, admin ingestion in `002-data-operations`, and production evidence-backed chat in `003-evidence-backed-chat`.

## Product Classification

- Product type: fintech research dashboard / analyst workbench
- Audience: internal finance researcher/admin
- Primary tasks: ask chat-first finance questions, inspect generated chat artifacts, monitor real market data in Market, run fixed workflows, inspect cited workflow results, monitor ingestion, inspect freshness and artifacts
- Stack target: React/Vite frontend consuming FastAPI JSON APIs
- Chart target: Lightweight Charts for OHLC/candlestick and market-series panels

## Design Principles

- Evidence before prose: citations, freshness, source coverage, and artifact status must be visible near generated workflow answers and chat artifacts.
- Chat-first shell: the default primary surface after login in Phase 1 is a new chat composer, with workflows and Market available from the left rail.
- Market is real data only: market snapshots, charts, tables, source/news feeds, and freshness states must not include LLM summaries, recommendations, or generated prose.
- Operational clarity: ingestion status, stale data warnings, failed runs, and unsupported markets must be visible without reading logs.
- Dense but legible: prioritize compact navigation, tables, toolbars, split panes, and fixed-height panels.
- No raw reasoning exposure: show stages, role status, tool status, citations, and artifacts; do not show hidden model reasoning transcripts.
- Stable layout: hover, loading, validation, and chart states must not resize the shell or shift critical controls.

## Visual System

Use a light professional theme by default with a Perplexity-inspired ledger treatment: warm off-white canvas, charcoal text, quiet neutral rail, thin warm-gray dividers, restrained teal focus/selection accents, and amber/brass reserved for primary workflow actions, warnings, freshness, and coverage states. The UI must not read as generic white-card/blue-SaaS chrome. Define tokens so dark mode can be added later without rewriting component contracts.

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
| Amber | `accent-amber` | `#D09A2D` | Primary workflow run CTA, warnings, freshness and coverage status |
| Success | `success` | `#138A63` | Fresh data, bullish candles, success states |
| Danger | `danger` | `#B9433A` | Failed jobs, bearish candles, destructive states |
| Warning | `warning` | `#D09A2D` | Stale data, partial results |

Avoid gradient-orb, bokeh, decorative hero, generic white-card/blue-SaaS, heavy beige archive styling, purple-blue, and marketing-card-heavy treatments.

## Shell

Desktop shell uses a fixed left rail plus a main work area. Chat artifact detail uses a right-side split panel on desktop and a full-screen artifact view on mobile.

- Left rail width: 220-248px desktop, collapsible to icon rail on narrower screens.
- Primary nav rows use icon + text for `New Chat`, `Market`, and `Workflows`.
- Primary nav rows are flat text rows by default. Do not draw each row as an outlined button.
- Only the active nav row or selected history row receives `surface-selected`; avoid simultaneous white, gray, and yellow row-selection backgrounds. Active rail rows do not increase font weight.
- Yellow/amber must not be used as a rail selection color. Reserve it for run actions, warnings, stale/freshness attention, and content-level coverage state.
- `History` is one rail section with two subsections: `Chat` and `Workflow Runs`. Do not split history by relative dates such as Today or Yesterday in V1.
- Top context bar is compact, pinned inside the primary content pane, and aligned with the artifact detail header when the artifact panel is open. In chat, it shows only the active conversation title matching the History label, falling back to `New Chat` before a conversation exists. Other surfaces show their current surface title only; surface metadata, freshness, and filters belong inside the active work area.
- Chat artifact detail headers are compact and pinned inside the right-side artifact panel. They use the same small title size as the chat header and show the artifact title plus close control only; artifact kind and metadata belong in the panel body.
- The logout control belongs in the left rail footer with the current role/session summary, not in the top context bar.
- Desktop shell scrolling is separated by panel: the left rail keeps brand/nav and logout visible while history scrolls; the primary content pane keeps its header visible; chat keeps the composer pinned to the bottom while only messages scroll; the right artifact panel keeps its header visible while only artifact body content scrolls.
- No large hero areas.

Navigation is phase-aware:

- Phase 1: New Chat, Market, Workflows, History
- Phase 2: Admin ingestion
- Phase 3: Production evidence-backed chat and orchestrator-backed artifacts

## Required Screens

### Login

- Compact centered login panel
- Username and password inputs with labels
- Startup configuration failure state
- Submit button with loading state
- Error messages use `role="alert"`

### Workflow

- Workflow catalog cards for fixed system-defined workflows
- Market/instrument inputs
- Amber run button
- Validation messages near fields
- Stage status chips
- Result panel with citations, freshness, chart artifacts, visible execution status

### Results

- Run list with filters
- Detail view with output, citations, artifacts, visible execution status, and logs summary
- Partial and failed runs distinguishable from successful runs

### Market Data

- Market uses a hybrid watchlist layout for VN stocks and gold only
- System-predefined watchlist in V1, user-editable watchlists later
- Freshness summary
- Chart panel
- News/source feed
- Market snapshot cards
- Data table fallback

### Admin Ingestion

- Freshness cards
- Job history table
- Manual fetch form
- Diagnostics panel

### Chat

- Default surface after login is a new chat composer
- Transcript area uses a simple centered conversation layout
- Composer is fixed to the bottom of the chat work area; only the message transcript scrolls.
- After a user submits any chat message, including the first message in a new chat, that latest user message must align to the top of the chat transcript viewport so the answer can unfold below it.
- V1 chat responses are deterministic mock responses, not production orchestrator output
- Chat messages may show trusted mock inline visual blocks generated from local templates
- Report, chart, table, evidence list, and citation bundle artifacts appear as cards inside messages
- Clicking an artifact card opens the artifact in the right-side detail panel on desktop or full-screen artifact view on mobile
- Chat V1 citation/evidence cards are mock UI patterns only

## Accessibility

- Semantic buttons/links and `cursor: pointer`
- Keyboard tab order follows visual order
- Focus states use visible 2px blue focus rings
- Errors use `role="alert"` or `aria-live`
- Loading states use skeletons or progress indicators
- Empty states explain what happened and offer the next action
- Respect `prefers-reduced-motion`
- Charts include accessible table fallbacks
