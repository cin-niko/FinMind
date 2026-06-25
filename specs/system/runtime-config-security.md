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
adr_refs: []
---

# Runtime, Config, And Security

## Authentication

All user-facing app and API surfaces require successful login before protected content is displayed. V1 uses one internal admin account bootstrapped from environment variables:

- `FINMIND_ADMIN_USERNAME`
- `FINMIND_ADMIN_PASSWORD`
- `FINMIND_SESSION_SECRET`

The application must fail closed when any required value is missing or invalid. Fail closed means protected content is not available to unauthenticated visitors.

Phase 002 data operations add production-only provider and database configuration:

- `FINMIND_DATABASE_URL`
- `FINMIND_VN_PROVIDER`
- `FINMIND_XAUUSD_PROVIDER`
- `FINMIND_XAUUSD_DAILY_FALLBACK`
- `FINMIND_SJC_PROVIDER`
- `FINMIND_VNSTOCK_API_KEY`
- `FINMIND_ALPHA_VANTAGE_API_KEY`
- `FINMIND_PROVIDER_TIMEOUT_SECONDS`

Provider credentials are server-side runtime configuration and are scoped to their
provider-specific variables. API responses, UI diagnostics, logs, tests, and fixture
data must not expose API keys, bearer tokens, authorization headers, or raw
secret-bearing request details.

The initial real-source set uses `vnstock` for VN stock history, yfinance/Yahoo
Finance for recent XAUUSD intraday history, Alpha Vantage free gold history as XAUUSD
daily fallback, and official SJC website/chart surfaces for SJC daily quotes. Real
provider values are selected per dataset with `FINMIND_VN_PROVIDER`,
`FINMIND_XAUUSD_PROVIDER`, and `FINMIND_SJC_PROVIDER`; `mock` remains the default for
local deterministic data. Free-source limitations such as rate limits, recent-only
intraday history, unavailable backfill ranges, and scraper parse failures must be
surfaced as non-secret capability diagnostics rather than hidden or replaced with
synthetic data. VN stock pre-production historical backfill and post-launch latest
fetches use the same 1h ingestion path. Phase 002 starts with a 1-month operational
US and Gold baseline backfill while VNStock historical backfill is paused; incomplete longer free-provider coverage does not
block launch when missing ranges are recorded as diagnostics.

## Sessions

V1 uses cookie-backed web sessions for authenticated browser access. Session cookie values must be signed or otherwise verified using `FINMIND_SESSION_SECRET`; unsigned, malformed, or tampered session cookies must be treated as unauthenticated. Logout and expiration must block protected content again.

## Scope Gates

V1 user-facing market coverage is VN stocks and gold only. US stocks and BTC are roadmap markets and must return clear out-of-scope behavior in V1 surfaces.

Mock/demo surfaces are still user-facing scope surfaces. Workflow, Market, and chat controls must not present US stocks or BTC as enabled runnable V1 choices. If roadmap markets are shown for product preview, they must be disabled or clearly marked future/out-of-scope before execution rather than allowing the user to submit and discover the limitation only through a backend validation error.

V1 excludes:

- Trade execution
- Broker connectivity
- Portfolio order management
- Self-service registration
- External identity providers
- US stocks and BTC as user-facing supported markets

## Data Safety

Ingestion reruns must be idempotent for the same dataset and period. Unsafe overlap must be blocked with visible status. Failure diagnostics must never expose secrets.

## Evidence Safety

Generated material claims must show citations and freshness metadata, or be omitted, qualified, or marked unsupported/unavailable. Stale data must be visible as stale rather than silently presented as current.

## Reasoning Safety

The UI may show evidence, citations, workflow stages, role status, tool status, artifact status, and final grounded rationale. It must not expose raw agent reasoning.
