# AGENTS.md - AI Agent Workflow for FinMind

This file orients any AI coding agent working in this repository. Read it before acting.

## 1. What This Repo Is

FinMind is an agentic AI platform for Financial Trading. The current short-term product direction is an authenticated, workflow-first finance advice workbench for VN stocks and US stocks, with evidence-backed outputs, citations, canonical contracts, chart artifacts, and deterministic mock chat artifacts. The product principle is advice, not decision; data driven; claims with citations and source provenance, not hallucination.

The target repo split is `src/finmind_agents` for the shared agentic and
finance orchestration layer, `src/finmind_api` for the backend API layer, and
`src/finmind_ui` for the frontend layer. Phase 02 planning uses the LangChain
ecosystem with `langchain-litellm` as the default model adapter and defers
LangGraph until graph state or multi-agent branching is required. Finance
product APIs, UI, data workflows, and orchestration are specified under
`specs/` before implementation.

## 2. Single Source Of Truth

Every piece of information should have one canonical location. Link to it instead of duplicating it.

| I need the... | Look here |
|---------------|-----------|
| Project rules and governance | [`.specify/memory/constitution.md`](.specify/memory/constitution.md) |
| Spec index and cross-references | [`specs/README.md`](specs/README.md) |
| Platform-wide state, contracts, runtime, security, UI rules | [`specs/system/`](specs/system/) |
| Per-feature specs | [`specs/NNN-slug/`](specs/README.md) |
| Local agent skills | [`.agents/skills/`](.agents/skills/) |
| Planned shared agent runtime | [`specs/002-workflow/plan.md`](specs/002-workflow/plan.md) |
| Existing tests | [`tests/`](tests/) |
| Product source ideas | [`ideas/`](ideas/) |

## 3. Hard Rules

1. **Specs before code.** When adding or changing behavior, update the relevant `specs/system/*` or `specs/NNN-slug/*` file first, then implementation and tests.
2. **Do not collapse bounded features into one phase.** Current bounded feature folders are active `001-mvp-ui/`, draft `002-workflow/`, and draft `003-agentic-chatflow/`. Create future `NNN-slug/` folders only when the next bounded capability is ready to become canonical.
3. **System contracts live in `specs/system/`.** If a feature changes shared state, API contracts, runtime behavior, security, or UI foundations, update `specs/system/*` and cross-reference the feature.
4. **Use YAML frontmatter on spec files.** Include `id`, `status` or feature lifecycle status, `implements`, `validated_by`, and `adr_refs`. Only reference paths that exist; draft specs may use `implements: []` until code lands.
5. **Keep VN stocks and US stocks as current user-facing market scope.** Gold, BTC, and other assets are roadmap-only unless a later spec explicitly changes scope.
6. **No raw agent reasoning in user-facing surfaces.** Show evidence, citations, stages, tool/artifact status, and grounded outputs only.
7. **Keep humans in control.** Do not implement autonomous trades, orders, or irreversible financial actions; unsupported, stale, missing, failed, or unsafe outputs must be blocked or clearly marked before user reliance.
8. **Provider details stay abstract at product-contract level.** Implementation may validate providers, licensing, credentials, and schemas behind source connector contracts.
9. **Do not duplicate schemas or tables.** Pick the canonical spec and link to it.
10. **Do not hand-edit generated/cache files.** Local agent skills live under `.agents/skills/`; generated runtime caches and virtualenv artifacts should be ignored.
11. **Run relevant verification before completion.** For Python work, use `uv run pytest`; for frontend work, use the commands defined by `src/finmind_ui/package.json` once that app exists.
12. **Use semantic commit messages.** Commits must follow the Conventional Commits format, such as `feat(ui): add workflow picker`, `fix(api): block unsupported markets`, or `docs(agents): document commit rules`.

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
cd src/finmind_ui
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
| `ui-ux-pro-max` | UI/UX design, review, or frontend implementation work |

Skills are procedural guidance. Normative product behavior belongs in specs.
For UI work, use `ui-ux-pro-max` for design-system/search guidance and implementation heuristics, then encode durable product decisions in [`specs/system/ui-ux-guidelines.md`](specs/system/ui-ux-guidelines.md) or the owning feature spec before changing code.

## 7. Anti-Patterns

- Do not recreate a monolithic V1 spec folder as the long-term source of truth.
- Do not add ingestion admin, plugin hardening, gold, BTC, or other assets into the current MVP unless the owning spec is explicitly changed.
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
src/finmind_agents/       planned shared agentic runtime, skills, and dataflows
src/finmind_api/          planned backend API layer
src/finmind_ui/           planned frontend layer
tests/                   current test suite
```

## 9. Current Feature State

1. `001-mvp-ui`: active implemented feature covering auth, app shell, deterministic mock chat UI, artifact detail, navigation, grouped history layout, and UI foundations.
2. `002-workflow`: draft phase 02 feature for a guarded workflow runtime, retrieval-first `dataflows` module, YAML workflow definitions, Markdown agent skills, VN stock and US stock scope, citations, chart artifacts, execution status, and workflow run inspection.
3. `003-agentic-chatflow`: draft phase 03 feature for future evidence-backed flexible Q&A chatflow over trusted sources.

Deleted roadmap folders such as data operations and extension hardening are not canonical. Recreate future capabilities through a fresh Spec Kit cycle only when scope, data access, safety, and contracts are ready.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at specs/002-workflow/plan.md
<!-- SPECKIT END -->
