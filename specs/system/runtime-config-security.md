---
id: SPEC-SYSTEM-RUNTIME-SECURITY-FINMIND
status: active
last_review: 2026-06-18
implements:
  - src/agent_core/settings
  - src/api/settings.py
  - src/api/auth.py
  - src/api/dependencies.py
validated_by:
  - tests/test_app.py
adr_refs:
  - docs/adr/0001-vn-only-v1-market-scope.md
  - docs/adr/0004-dormant-roadmap-market-connectors.md
---

# Runtime, Config, And Security

## Authentication

All user-facing app and API surfaces require successful login before protected content is displayed. V1 uses one internal admin account bootstrapped from environment variables:

- `FINMIND_ADMIN_USERNAME`
- `FINMIND_ADMIN_PASSWORD`
- `FINMIND_SESSION_SECRET`

The application must fail closed when any required value is missing or invalid. Fail closed means protected content is not available to unauthenticated visitors.

Phase 002 V1 data operations add production-only provider and database configuration. V1 is **VN-only**:

- `FINMIND_DATABASE_URL`
- `FINMIND_VN_PROVIDER=mock|vnstock`
- `FINMIND_VNSTOCK_API_KEY` (optional/reserved; server-side only)
- `FINMIND_PROVIDER_TIMEOUT_SECONDS`

The following provider variables remain recognized config names for roadmap
re-enablement, but they are **not part of V1**. Setting them MUST NOT enable
ingestion, scheduling, freshness output, or UI surfaces in V1:

- `FINMIND_US_PROVIDER` (roadmap)
- `FINMIND_XAUUSD_PROVIDER` (roadmap)
- `FINMIND_XAUUSD_DAILY_FALLBACK` (roadmap)
- `FINMIND_SJC_PROVIDER` (roadmap)
- `FINMIND_ALPHA_VANTAGE_API_KEY` (roadmap)

Provider credentials are server-side runtime configuration and are scoped to their
provider-specific variables. API responses, UI diagnostics, logs, tests, and fixture
data must not expose API keys, bearer tokens, authorization headers, or raw
secret-bearing request details.

The V1 real-source set uses `vnstock` for VN stock daily history (canonical) and
1h history (best-effort over the rolling free-provider window); `mock` remains the
default for local deterministic tests. Docker Compose defaults VN ingestion to
`vnstock` for Phase 002 real-data operation. Free-source limitations such as rate limits,
recent-only 1h history, and unavailable backfill ranges must be surfaced as
non-secret capability diagnostics rather than hidden or replaced with synthetic
data. VN stock historical backfill, scheduled latest fetches, and lazy
on-first-access fetches all share the same canonical idempotent ingestion path.
Incomplete `vn_prices` 1h coverage does not block V1 launch when missing ranges
are recorded as diagnostics; `vn_prices_daily` is the freshness/launch-critical
timeframe.

## Sessions

V1 uses cookie-backed web sessions for authenticated browser access. Session cookie values must be signed or otherwise verified using `FINMIND_SESSION_SECRET`; unsigned, malformed, or tampered session cookies must be treated as unauthenticated. Logout and expiration must block protected content again.

## Scope Gates

V1 user-facing market coverage is **VN stocks only**, scoped to the pre-seeded
VN100 universe. Gold (XAUUSD and SJC), US stocks, and BTC are roadmap markets
and must return clear out-of-scope behavior in V1 surfaces.

Mock/demo surfaces are still user-facing scope surfaces. Workflow, Market, and
chat controls must not present roadmap markets as enabled runnable V1 choices.
If roadmap markets are shown for product preview, they must be disabled or
clearly marked future/out-of-scope before execution rather than allowing the
user to submit and discover the limitation only through a backend validation
error.

V1 excludes:

- Trade execution
- Broker connectivity
- Portfolio order management
- Self-service registration
- External identity providers
- US stocks and BTC as user-facing supported markets
- Gold (XAUUSD and SJC) as user-facing supported markets in V1
- Open on-demand instrument creation outside the pre-seeded VN100 universe

## Data Safety

Ingestion reruns must be idempotent for the same dataset and period. Unsafe overlap must be blocked with visible status. Failure diagnostics must never expose secrets.

## Evidence Safety

Generated material claims must show citations and freshness metadata, or be omitted, qualified, or marked unsupported/unavailable. Stale data must be visible as stale rather than silently presented as current.

## Reasoning Safety

The UI may show evidence, citations, workflow stages, role status, tool status, artifact status, and final grounded rationale. It must not expose raw agent reasoning.
