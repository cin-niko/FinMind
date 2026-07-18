---
id: CONTRACT-FEAT-003-LANGUAGE
feature: language-preferences
status: active
implements:
  - src/finmind_api/routes/preferences.py
  - src/finmind_ui/src/api/client.ts
validated_by:
  - tests/test_app.py
adr_refs: []
---

# Language Preference Contract

## Read preference

`GET /api/preferences/language`

- Requires an authenticated session.
- Returns `{ "selection": "auto" | "vi" | "en" }`.
- If no value exists for the user, persists and returns `auto`.

## Update preference

`PUT /api/preferences/language`

- Requires an authenticated session.
- Accepts `{ "selection": "auto" | "vi" | "en" }` only.
- Updates only the authenticated user's preference.
- Rejects unsupported values without changing the saved value.

## Browser resolution

- An explicit `vi` or `en` selection resolves to itself.
- `auto` examines `navigator.languages` in order.
- Regional values normalize by primary language (`vi-*` to `vi`, `en-*` to
  `en`).
- No supported entry resolves to `en`.

## Workflow boundary

- Workflow submission accepts an effective `language` of `vi` or `en`, never
  `auto` or a localized label.
- The accepted value is captured as the conversation output language and added
  to the model-facing language instruction.
- Generated output that fails captured-language validation fails safely.
- A preference update does not mutate saved conversation output.

## Evidence boundary

Language affects FinMind-owned presentation and generated narrative only. It
does not translate or mutate canonical records, source text, citation snapshots,
publisher names, URLs, identifiers, timestamps, numeric values, or symbols.
