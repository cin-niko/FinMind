---
id: SPEC-FEAT-003-IMPLEMENTATION-NOTES
feature: vn-gold-dataflows-workflows
status: active
owner: solo
created: 2026-07-12
implements: []
validated_by: []
adr_refs: []
---

# Phase 03 Implementation Notes

## Started

- 2026-07-12: Implementation started after user approved proceeding with the
  incomplete specification-quality checklist. The unresolved checklist items are
  spec-quality follow-up, not a decision to relax implementation safety or tests.
- UI guidance used: `ui-ux-pro-max` accessibility guidance for labelled controls,
  error announcements, visible focus, and contrast. FinMind's shared
  `specs/system/ui-ux-guidelines.md` remains the visual source of truth; no
  generated vibrant/marketing visual style is adopted.

## Deviations

- The Gold provider retains an injected connector seam for deterministic tests,
  while the production registry now selects the approved Twelve Data daily
  XAUUSD connector. Missing credentials and permanent request errors fail
  closed; only transient transport/provider failures are retried.
- VN news, valuation, and stock-brief workflow definitions are now present and
  deterministic fixture-covered. Publisher-provider configuration, normalized
  persistence child tables, and full lifecycle/browser UI coverage remain in
  the unchecked tasks.

## Multilingual Presentation Boundary

- Phase 03 localizes FinMind-owned UI chrome, workflow catalog copy, progress
  labels/statuses, deterministic messages, and generated narrative through
  stable typed keys with English fallback.
- Canonical record field names/content and citation evidence are deliberately
  not translated. Citation panel controls may be localized, but titles,
  excerpts, publisher/source metadata, URLs, and payload snapshots remain
  canonical.
- Workflow/API stage identifiers and status codes remain language-neutral. The
  frontend resolves their display labels; it does not consume a server-supplied
  English label as the contract.

## Validation Log

- 2026-07-13 Gold completion pass: production runtime selects Twelve Data with
  `FINMIND_GOLD_DATA_PROVIDER=twelvedata` and
  `FINMIND_TWELVE_DATA_API_KEY`; contract tests mock the HTTP boundary and
  verify daily XAUUSD parameters, numeric-string normalization, transient-only
  retries, permanent failure behavior, and unsupported-interval rejection.
- `UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest -q`
  — 17 passed.
- `npm run test && npm run build` in `src/finmind_ui` — passed; the fixed Gold
  catalog card opens the shared confirmation dialog, then starts fixed XAUUSD
  without exposing market, symbol, or interval inputs.
- Targeted Ruff validation for the changed production Gold/configuration modules
  — passed. Repository-wide checking of `tests/test_platform_services.py` still
  reports seven pre-existing long lines in the mixed Phase 03 test file.
- `npm run test` in `src/finmind_ui` — passed; covers browser-language
  resolution, locale interpolation, English fallback for unknown workflow
  stages, Vietnamese workflow catalog labels, and deterministic chat behavior.
- `npm run build` in `src/finmind_ui` — passed after the typed locale catalog and
  stable progress-code refactor.
- `UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest tests/test_platform_services.py tests/test_app.py` — 13 passed, including the model-language/evidence-preservation prompt boundary.
- `UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest tests/test_app.py tests/test_platform_services.py` — 13 passed.
- `npm run build` in `src/finmind_ui` — passed.
- `npm run test` in `src/finmind_ui` — passed; covers ordered browser-language resolution, unsupported-language fallback, and explicit selection precedence.
- `ruff check src tests` was run. It reports pre-existing repository-wide
  formatting/import findings as well as style cleanup still needed in the new
  persistence module; it is not a passing validation gate yet.
