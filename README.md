<div align="center">
    <h1>🌱 FinMind</h1>
    <h3><em>An agentic AI platform for Financial Trading.</em></h3>
</div>

<p align="center">
  <img src="docs/assets/section-divider.svg" alt="" width="800" height="6"/>
</p>

## Overview

## Architecture

## Documentation

This repo follows Spec-Driven Development. Each artifact has a single purpose:

| Path | Purpose |
|------|---------|
| `ARCHITECTURE.md` | System architecture overview and major technical boundaries. |
| `DEPLOYMENT.md` | Runtime setup, deployment procedure, and operational commands. |
| `specs/README.md` | Spec index, cross-references, and requirement coverage. |
| `specs/system/` | Cross-feature state, contracts, runtime, security, and UI foundations. |
| `specs/NNN-slug/` | Bounded feature specs, plans, tasks, and supporting artifacts. |
| `docs/adr/` | Architecture decision records and rationale. |
| `docs/risks/` | Known risks, mitigations, and open concerns. |
| `.specify/memory/` | Stable project governance and Spec Kit memory. |
| `AGENTS.md` | Required workflow for AI coding agents in this repository. |

**Rule of thumb**: behavior and contracts live in `specs/`; decisions live in `docs/adr/`; risks live in `docs/risks/`; procedures live in the closest owning guide; everything else links there.

## Quick Start

For local development, the repository `.env` file provides the default admin
login:

```text
username: admin
password: admin
```

You can override it by exporting environment variables before starting the API:

```bash
export FINMIND_ADMIN_USERNAME=admin
export FINMIND_ADMIN_PASSWORD=admin
export FINMIND_SESSION_SECRET=session-secret-with-length
export FINMIND_GOLD_DATA_PROVIDER=twelvedata
export FINMIND_TWELVE_DATA_API_KEY=your-twelve-data-key
```

Run the PostgreSQL run store for local development (the API fails closed
without `FINMIND_DATABASE_URL`):

```bash
docker compose up postgres
```

Copy `.env.sample` to `.env` and replace the provider credentials and secrets.
The sample includes the local PostgreSQL URL and the Gemini/Twelve Data settings.

Run the backend tests:

```bash
UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run pytest
```

Start the API:

```bash
uv run uvicorn finmind_api.app:create_app --factory --reload
```

Start the UI:

```bash
cd src/finmind_ui
npm install
npm run dev
```

Or start API and UI together:

```bash
docker compose up --build
```

Open the UI at `http://127.0.0.1:5173`. The API is exposed at `http://127.0.0.1:8000`.

## Project Structure

```text
.agents/                 Repo-local agent skills
.specify/                Spec Kit scripts, templates, workflows, and governance memory
AGENTS.md                Agent workflow instructions
specs/                   Product and platform specifications
src/finmind_agents/      LangChain-backed agent runtime, finance workflows, and dataflows
src/finmind_api/         API application
src/finmind_ui/          Frontend application
tests/                   Backend test suite
```

## Development

Before changing behavior:

1. Read `AGENTS.md`.
2. Read `specs/README.md`.
3. Identify the owning system or feature spec.
4. Update the spec first when behavior or contracts change.
5. Implement the smallest scoped change.
6. Run relevant verification before completion.

Generated caches, local worktrees, runtime stores, and virtualenv artifacts should stay untracked.

### Testing

Baseline backend verification:

```bash
UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run pytest
```

Frontend verification:

```bash
cd src/finmind_ui
npm install
npm run build
```

### Code Quality

Python code should follow `.agents/skills/python-guidelines/SKILL.md`.

When a lint or spec harness command is added, prefer the repo-defined command over ad hoc checks.

## Spec-Driven Development

Behavior and contracts live in `specs/`. Decisions live in `docs/adr/`. Risks live in `docs/risks/`. Project governance lives in `.specify/memory/constitution.md`. Agent workflow lives in `AGENTS.md`.

Use this loop for feature work:

1. Start with the relevant spec.
2. Keep shared state, API contracts, runtime/security, and UI foundations in `specs/system/`.
3. Keep bounded feature behavior in `specs/NNN-slug/`.
4. Keep implementation and tests traceable to those specs.
5. Do not duplicate schemas, requirement tables, or product rules across files.

For AI coding agents, `AGENTS.md` is mandatory before acting.
