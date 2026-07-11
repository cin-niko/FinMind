---
id: SPEC-FEAT-003-QUICKSTART
feature: vn-gold-dataflows-workflows
status: draft
owner: solo
created: 2026-07-11
implements: []
validated_by: []
adr_refs: []
---

# Quickstart: VN And Gold Dataflows And Workflows Validation

## Prerequisites

- Authenticated local FinMind environment with the Phase 02 workflow foundation.
- `FINMIND_DATABASE_URL` configured for persisted run inspection.
- A documented configured gold instrument/benchmark and source connector.
- A valid VN stock symbol supported by the configured VN provider or deterministic
  fixture.

## Scenario 1: Gold Evidence Collection

1. Run collection for the configured gold instrument with its declared datasets.
2. Verify every returned record exposes source id, dataset id, market/collection
   timestamps, freshness state, rendered context, and citation eligibility.
3. Simulate a stale, missing, or undeclared dataset.
4. Verify the result is warning, unavailable, or rejected rather than
   claim-ready.

## Scenario 2: Gold Workflow

1. Open the workflow catalog and choose a supported gold workflow.
2. Confirm stock-only financial sections are absent and required gold input is
   explicit.
3. Submit the workflow and observe safe progress before final output.
4. Verify each material claim has citation provenance or an unavailable marker;
   inspect chart/artifact status and source freshness.

## Scenario 3: VN Stock Brief

1. Select the VN stock brief workflow and a supported VN stock symbol.
2. Verify collection, grounding, fundamental, and technical stages are visible.
3. Cause one evidence group to be unavailable in a deterministic fixture.
4. Verify completed sections remain visible and the affected stage is partial or
   unavailable without fabricated claims.

## Scenario 4: Scope Validation And Reinspection

1. Attempt an unsupported market or asset input.
2. Verify Phase 03 blocks or visibly marks each request before a result exists.
3. Complete one VN stock and one gold run, then reopen each from history.
4. Verify final output, status, citations, artifacts, and limitations persist.

## Verification

Run the relevant backend tests with `uv run pytest`. Build the UI using the
command in `src/finmind_ui/package.json`. Record source-specific manual
validation results before enabling a gold workflow beyond deterministic fixtures.
