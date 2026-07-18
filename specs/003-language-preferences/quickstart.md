---
id: QUICKSTART-FEAT-003
feature: language-preferences
status: active
implements: []
validated_by:
  - tests/test_app.py
  - tests/test_platform_services.py
  - src/finmind_ui/src/features/settings/i18n.test.ts
adr_refs: []
---

# Quickstart: Validate Language Preferences

From the repository root:

```bash
uv run pytest
```

From `src/finmind_ui/`:

```bash
npm run test
npm run build
```

The automated acceptance boundary covers:

- default, accepted, and rejected preference API values;
- browser-order Auto-detect and English fallback;
- typed English/Vietnamese UI catalogs and missing-key fallback;
- workflow submission language capture and explicit model instruction;
- response-language validation; and
- preservation of canonical evidence across localized presentation.

Before merge, also run:

```bash
git diff --check
rg -n "language-preferences|vn-stock-workflows|gold-workflows/archive" AGENTS.md specs docs
```

Review the final search for correct ownership, then separately confirm no
deleted feature directory is referenced by canonical documentation.

## Verification record — 2026-07-18

- `.venv/bin/pytest`: 78 passed; dependency deprecation warnings remain.
- `npm run test`: passed all configured frontend tests.
- `npm run build`: passed TypeScript checking and the Vite production build.
- `git diff --cached --check`: passed before commit.
- The staged commit contains no Phase 04 or Phase 05 feature files.
