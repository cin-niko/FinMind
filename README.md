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

Start the API and UI together:

```bash
docker compose up --build
```

The Compose stack builds package-specific images from `src/api/Dockerfile` and
`src/ui/Dockerfile`. It uses these default admin credentials unless overridden in
the shell:

```bash
FINMIND_ADMIN_USERNAME=analyst
FINMIND_ADMIN_PASSWORD=secret-pass
FINMIND_SESSION_SECRET=session-secret-with-length
```

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
