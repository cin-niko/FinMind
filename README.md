# FinMind

FinMind is an internal finance research workbench. Phase 1 implements an authenticated workflow platform for VN stocks and gold with cited outputs, freshness metadata, chart artifacts, and result inspection.

## Backend

Set required admin environment variables before starting the API:

```bash
export FINMIND_ADMIN_USERNAME=analyst
export FINMIND_ADMIN_PASSWORD=secret-pass
export FINMIND_SESSION_SECRET=session-secret-with-length
```

Run tests:

```bash
UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run pytest
```

Start the API:

```bash
uv run uvicorn api.app:create_app --factory --reload
```

## Docker Compose

Create a local environment file:

```bash
cp .env.sample .env
```

Start the API and UI together:

```bash
docker compose up --build
```

The Compose stack builds package-specific images from `src/api/Dockerfile` and
`src/ui/Dockerfile`. It reads `.env` automatically. The sample starts in deterministic
demo provider mode and uses these admin credentials:

```bash
FINMIND_ADMIN_USERNAME=analyst
FINMIND_ADMIN_PASSWORD=secret-pass
FINMIND_SESSION_SECRET=session-secret-with-length
```

Phase 002 data operations use TimescaleDB/PostgreSQL from Compose. The sample starts
with deterministic mock providers:

```bash
FINMIND_VN_PROVIDER=mock
FINMIND_XAUUSD_PROVIDER=mock
FINMIND_SJC_PROVIDER=mock
```

To use the implemented free real providers, edit `.env`:

```bash
FINMIND_VN_PROVIDER=vnstock
FINMIND_XAUUSD_PROVIDER=yfinance
FINMIND_XAUUSD_DAILY_FALLBACK=alpha_vantage
FINMIND_SJC_PROVIDER=sjc_official
FINMIND_VNSTOCK_API_KEY=your-vnstock-key
FINMIND_ALPHA_VANTAGE_API_KEY=optional-alpha-vantage-key
```

Provider credentials are not shared across adapters. `FINMIND_VNSTOCK_API_KEY` is
required when `FINMIND_VN_PROVIDER=vnstock`; `FINMIND_ALPHA_VANTAGE_API_KEY` is used
only by the Alpha Vantage XAUUSD daily fallback.

Open the UI at `http://127.0.0.1:5173`. The API is exposed at `http://127.0.0.1:8000`.

## Frontend

```bash
cd src/ui
npm install
npm run dev
```

The Vite development server proxies `/api` requests to `http://127.0.0.1:8000` locally, or to `http://api:8000` inside Docker Compose.

## Phase 1 Validation

1. Attempt to open protected workflow or result surfaces without a session.
2. Log in with the configured admin credentials.
3. Run a VN stock or gold workflow.
4. Confirm the result includes citations, freshness metadata, visible execution status, and a chart artifact with table fallback.
5. Log out and confirm protected content is blocked again.
