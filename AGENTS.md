# AGENTS.md - AI Agent Workflow for FinMind

This file orients any AI coding agent working in this repository. Read it before acting.

## 1. What This Repo Is

FinMind is an internal finance research workbench. The current product direction is an authenticated, workflow-first platform for VN stocks and gold, with evidence-backed outputs, canonical data contracts, chart artifacts, admin data operations, and later chat/plugin extension surfaces.

The reusable agent substrate lives under `src/agent_core`. Finance product APIs, UI, data workflows, and orchestration are specified under `specs/` before implementation.

## 2. Single Source Of Truth

Every piece of information should have one canonical location. Link to it instead of duplicating it.

| I need the... | Look here |
|---------------|-----------|
| Project rules and governance | [`.specify/memory/constitution.md`](.specify/memory/constitution.md) |
| Spec index and cross-references | [`specs/README.md`](specs/README.md) |
| Platform-wide state, contracts, runtime, security, UI rules | [`specs/system/`](specs/system/) |
| Per-feature specs | [`specs/NNN-slug/`](specs/README.md) |
| Local agent skills | [`.agents/skills/`](.agents/skills/) |
| Existing agent substrate code | [`src/agent_core/`](src/agent_core/) |
| Existing tests | [`tests/`](tests/) |
| Product source ideas | [`ideas/`](ideas/) |

## 3. Hard Rules

1. **Specs before code.** When adding or changing behavior, update the relevant `specs/system/*` or `specs/NNN-slug/*` file first, then implementation and tests.
2. **Do not collapse bounded features into one phase.** Use append-only feature folders such as `001-mvp-workflow-platform/`, `002-data-operations/`, `003-evidence-backed-chat/`, and `004-extension-hardening/`.
3. **System contracts live in `specs/system/`.** If a feature changes shared state, API contracts, runtime behavior, security, or UI foundations, update `specs/system/*` and cross-reference the feature.
4. **Use YAML frontmatter on spec files.** Include `id`, `status` or feature lifecycle status, `implements`, `validated_by`, and `adr_refs`. Only reference paths that exist; draft specs may use `implements: []` until code lands.
5. **Keep VN stocks and gold as V1 user-facing scope.** US stocks and BTC are roadmap-only unless a later spec explicitly changes scope.
6. **No raw agent reasoning in user-facing surfaces.** Show evidence, citations, stages, tool/artifact status, and grounded outputs only.
7. **Provider details stay abstract at product-contract level.** Implementation may validate providers, licensing, credentials, and schemas behind source connector contracts.
8. **Do not duplicate schemas or tables.** Pick the canonical spec and link to it.
9. **Do not hand-edit generated/cache files.** Local agent skills live under `.agents/skills/`; generated runtime caches and virtualenv artifacts should be ignored.
10. **Run relevant verification before completion.** For Python work, use `uv run pytest`; for frontend work, use the commands defined by `src/ui/package.json` once that app exists.

## 4. Standard Loops

### 4.1 Feature Change

1. Read [`specs/README.md`](specs/README.md) to identify the owning spec.
2. Read relevant `specs/system/*` specs for shared contracts.
3. Read the feature folder under `specs/NNN-slug/`.
4. If behavior or contracts change, update specs first.
5. Implement the smallest scoped change matching the spec.
6. Add or update tests proportional to risk.
7. Run relevant verification.
8. Summarize changed specs, code, and verification results.

### 4.2 New Feature

Use Spec Kit for a new bounded capability:

1. `/speckit-specify <description>` creates `specs/NNN-slug/spec.md`.
2. `/speckit-clarify` resolves major ambiguity when needed.
3. `/speckit-plan <tech choices>` creates `plan.md` and design artifacts.
4. `/speckit-tasks` creates ordered implementation tasks.
5. `/speckit-implement` executes tasks in order.

If the feature adds or changes a shared contract, also update `specs/system/*` and the cross-reference table in `specs/README.md`.

### 4.3 Continuing A Feature In A Fresh Session

1. Check `.specify/feature.json`.
2. If it points to the wrong feature, set:

   ```bash
   export SPECIFY_FEATURE_DIRECTORY=specs/NNN-slug
   ```

3. Confirm the active feature by reading its `spec.md`, `plan.md`, and `tasks.md`.

### 4.4 Spec Migration Or Refactor

When moving or splitting specs:

1. Inventory every source artifact before editing.
2. Preserve every FR/SC and acceptance scenario, either in `specs/system/` or a feature folder.
3. Update all relative links and stale folder references.
4. Update `specs/README.md` with the new cross-reference map.
5. Run `rg` checks for old paths and requirement IDs.

## 5. Local Verification

Baseline commands:

```bash
uv run pytest
```

When UI exists:

```bash
cd src/ui
npm install
npm run build
```

When a spec harness or Makefile is added, prefer the repo-defined commands such as `make check-specs`, `make lint`, and `make test`.

## 6. Local Agent Skills

Use `.agents/skills/` for repo-local guidance:

| Skill | When |
|-------|------|
| `python-guidelines` | Writing, reviewing, or refactoring Python |
| `speckit-specify` | Creating or updating a feature specification |
| `speckit-plan` | Planning implementation artifacts |
| `speckit-tasks` | Generating ordered task plans |
| `speckit-implement` | Executing task plans |
| `speckit-analyze` | Checking consistency across spec, plan, and tasks |
| `speckit-converge` | Comparing implementation to spec/plan/tasks |
| `ui-ux-pro-max` | UI/UX design work |

Skills are procedural guidance. Normative product behavior belongs in specs.

## 7. Anti-Patterns

- Do not recreate a monolithic V1 spec folder as the long-term source of truth.
- Do not add chat, ingestion admin, plugin hardening, US stocks, or BTC into the Phase 1 MVP unless the owning spec is explicitly changed.
- Do not expose provider secrets, environment secrets, or raw model reasoning in docs, logs, UI, or tests.
- Do not invent new market scope terminology outside `specs/system/runtime-config-security.md`.
- Do not let feature specs redefine shared entities that belong in `specs/system/state-model.md`.

## 8. Quick Reference

```text
specs/README.md          spec index and FR/SC coverage
specs/system/            shared state, contracts, runtime, security, UI
specs/NNN-slug/          bounded feature specs
.agents/skills/          local agent workflows and guidance
.specify/                Spec Kit scripts, templates, and memory
src/agent_core/          reusable agent substrate
tests/                   current test suite
```

## 9. Current Feature Order

1. `001-mvp-workflow-platform`: auth, app shell, fixed workflow, citations, freshness, chart artifacts, result inspection.
2. `002-data-operations`: ingestion jobs, freshness, idempotent reruns, market data inspector, admin diagnostics.
3. `003-evidence-backed-chat`: chat over shared evidence, citations, artifacts, freshness, and execution records.
4. `004-extension-hardening`: plugin-ready execution artifacts and evidence contracts without shipping an adapter.
