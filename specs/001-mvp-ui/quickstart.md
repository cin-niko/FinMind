---
id: SPEC-FEAT-001-QUICKSTART
feature: mvp-ui
status: active
owner: solo
created: 2026-06-26
implements:
  - src/finmind_ui
  - src/finmind_api
validated_by:
  - tests/test_app.py
adr_refs: []
---

# Quickstart: MVP UI Validation

## Commands

```bash
UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest tests/test_app.py
```

```bash
cd src/finmind_ui
npm run build
```

## Scenario 1: Login And Shell

1. Configure admin environment variables.
2. Open the app without a session and confirm login is required.
3. Log in and confirm the default surface is `New Chat`.
4. Navigate to `Workflows` and grouped `History`.
5. Log out and confirm protected content is blocked.

## Scenario 2: Mock Artifact Detail

1. Submit a chat prompt.
2. Confirm a deterministic mock response appears.
3. Open an artifact card.
4. Confirm the detail surface renders without arbitrary generated HTML.
