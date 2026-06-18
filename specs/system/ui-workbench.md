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

FinMind is an internal analyst workbench, not a marketing site. The first screen after login must be the usable application shell. Surfaces are introduced by feature phase: workflow/results in `001-mvp-workflow-platform`, admin ingestion and market data in `002-data-operations`, chat in `003-evidence-backed-chat`.

## Product Classification

- Product type: fintech research dashboard / analyst workbench
- Audience: internal finance researcher/admin
- Primary tasks: run fixed workflows, inspect cited results, monitor ingestion, inspect freshness and artifacts, ask evidence-backed chat questions once chat ships
- Stack target: React/Vite frontend consuming FastAPI JSON APIs
- Chart target: Lightweight Charts for OHLC/candlestick and market-series panels

## Design Principles

- Evidence before prose: citations, freshness, source coverage, and artifact status must be visible near generated answers.
- Workflow-first: the workflow tab is the default primary surface after login in Phase 1.
- Operational clarity: ingestion status, stale data warnings, failed runs, and unsupported markets must be visible without reading logs.
- Dense but legible: prioritize compact navigation, tables, toolbars, split panes, and fixed-height panels.
- No raw reasoning exposure: show stages, role status, tool status, citations, and artifacts; do not show hidden model reasoning transcripts.
- Stable layout: hover, loading, validation, and chart states must not resize the shell or shift critical controls.

## Visual System

Use a restrained dark analyst theme with blue data accents and amber action highlights.

| Role | Token | Hex | Usage |
|------|-------|-----|-------|
| Background | `bg-base` | `#0B1020` | App shell and page background |
| Surface | `surface-1` | `#111827` | Panels, sidebars, toolbars |
| Surface Raised | `surface-2` | `#172033` | Active panels, popovers, selected rows |
| Border | `border-subtle` | `#293548` | Panel and table dividers |
| Text Primary | `text-primary` | `#E5E7EB` | Main labels and body copy |
| Text Secondary | `text-secondary` | `#94A3B8` | Metadata, helper text |
| Data Blue | `accent-blue` | `#3B82F6` | Links, focus rings, selected nav |
| Deep Blue | `accent-blue-strong` | `#1E40AF` | Primary controls and chart highlights |
| Amber | `accent-amber` | `#F59E0B` | Primary workflow run CTA, warnings |
| Success | `success` | `#26A69A` | Fresh data, bullish candles, success states |
| Danger | `danger` | `#EF5350` | Failed jobs, bearish candles, destructive states |
| Warning | `warning` | `#F59E0B` | Stale data, partial results |

Avoid gradient-orb, bokeh, decorative hero, beige, purple-blue, and marketing-card-heavy treatments.

## Shell

Desktop shell uses a fixed left rail plus a main work area.

- Left rail width: 220-248px desktop, collapsible to icon rail on narrower screens.
- Top context bar shows current surface title, active market scope, global freshness summary, session/admin identity, and logout.
- No large hero areas.

Navigation is phase-aware:

- Phase 1: Workflow, Results
- Phase 2: Market Data, Admin
- Phase 3: Chat

## Required Screens

### Login

- Compact centered login panel
- Username and password inputs with labels
- Startup configuration failure state
- Submit button with loading state
- Error messages use `role="alert"`

### Workflow

- Workflow picker
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

- Dataset selector
- Freshness summary
- Chart panel
- Data table fallback

### Admin Ingestion

- Freshness cards
- Job history table
- Manual fetch form
- Diagnostics panel

### Chat

- Transcript area
- Composer fixed to bottom of chat work area
- Artifact panel for inline charts, tables, and computed outputs
- Role/stage status visible for current run

## Accessibility

- Semantic buttons/links and `cursor: pointer`
- Keyboard tab order follows visual order
- Focus states use visible 2px blue focus rings
- Errors use `role="alert"` or `aria-live`
- Loading states use skeletons or progress indicators
- Empty states explain what happened and offer the next action
- Respect `prefers-reduced-motion`
- Charts include accessible table fallbacks
