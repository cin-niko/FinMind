# FinMind Deployment

Production and local deployment runbook. Environment and security rules are defined in
[`specs/system/runtime-config-security.md`](specs/system/runtime-config-security.md).

## Local development (baseline)

### Prerequisites

- Python 3.12+ with [`uv`](https://github.com/astral-sh/uv)
- Docker (for TimescaleDB/PostgreSQL via Compose)
- Node.js (for `src/ui` when working on the frontend)

### Database

Start the canonical database service:

```bash
docker compose up -d timescaledb
```

Set `FINMIND_DATABASE_URL` to the Compose-provisioned PostgreSQL URL (see
`.env.sample`).

### Backend

```bash
uv run pytest
```

Run the API using the project’s documented dev entrypoint (see repository README when
present).

### Frontend

```bash
cd src/ui
npm install
npm run build
```

## Required environment variables (V1)

| Variable | Required | Notes |
|----------|----------|-------|
| `FINMIND_ADMIN_USERNAME` | yes | Bootstrap admin |
| `FINMIND_ADMIN_PASSWORD` | yes | Bootstrap admin |
| `FINMIND_SESSION_SECRET` | yes | Cookie session signing |
| `FINMIND_DATABASE_URL` | production yes | TimescaleDB/PostgreSQL |
| `FINMIND_VN_PROVIDER` | no | `vnstock` in Compose for real Phase 002 data; `mock` only for deterministic local tests |
| `FINMIND_VNSTOCK_API_KEY` | no | Optional/reserved; server-side only |

Roadmap provider variables (`FINMIND_US_PROVIDER`, `FINMIND_XAUUSD_PROVIDER`,
`FINMIND_SJC_PROVIDER`, `FINMIND_ALPHA_VANTAGE_API_KEY`) are recognized but do not
enable V1 surfaces.

**Never** commit secrets. Use `.env` locally; inject via your host secret manager in
production.

## Operational jobs

### Scheduled ingestion

External scheduler calls the protected worker endpoint:

`POST /api/worker/ingestion/scheduled`

Use `latest` mode for current VN daily (and best-effort 1h) updates.

### Historical backfill

Long-range history runs **outside** the web API:

```bash
docker compose --profile backfill run --build --rm backfill

# local operator equivalent:
./scripts/backfill_market_history.sh --plan vn-history --from-date ... --to-date ...
```

See [`specs/002-data-operations/quickstart.md`](specs/002-data-operations/quickstart.md)
when aligned to VN-only V1.

### VN100 universe seed

After migrations, run the VN100 seed script:

```bash
./scripts/seed_vn100.sh
```

The Compose API and backfill services run this seed step automatically before
serving/backfilling.

## Production checklist (stub)

Expand this section when a production target is chosen:

- [ ] TLS termination and session cookie security
- [ ] `FINMIND_DATABASE_URL` with backups and migration strategy
- [ ] Secret rotation for admin password and provider keys
- [ ] Worker/cron for scheduled ingestion
- [ ] Log retention without provider secrets or raw reasoning
- [ ] Health checks for API and database connectivity

## Related documents

- Architecture: [`ARCHITECTURE.md`](ARCHITECTURE.md)
- Spec index: [`specs/README.md`](specs/README.md)
- Risks: [`docs/risks/`](docs/risks/)
