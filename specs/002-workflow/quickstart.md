---
id: SPEC-FEAT-002-QUICKSTART
feature: workflow
status: draft
owner: solo
created: 2026-06-26
implements: []
validated_by: []
adr_refs: []
---

# Quickstart: Workflow Validation

## Commands

No runnable phase 02 validation command is canonical until `/speckit-plan` and
implementation tasks are completed.

## Scenario 1: VN Stock Workflow

1. Log in through the MVP UI shell.
2. Open `Workflows`.
3. Run a supported VN stock workflow.
4. Confirm output sections, citations, freshness metadata, chart artifacts, and
   execution status.

## Scenario 2: US Stock Workflow

1. Log in through the MVP UI shell.
2. Open `Workflows`.
3. Run a supported US stock workflow.
4. Confirm output sections, citations, freshness metadata, chart artifacts, and
   execution status.

## Scenario 3: Unsupported Asset

1. Attempt to run gold, BTC, or another unsupported asset.
2. Confirm execution is blocked or clearly marked unavailable.

Expected result: unsupported assets do not produce fabricated workflow results.
