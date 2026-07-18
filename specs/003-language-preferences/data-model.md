---
id: DATA-MODEL-FEAT-003
feature: language-preferences
status: active
implements:
  - src/finmind_agents/models.py
validated_by:
  - tests/test_platform_services.py
adr_refs: []
---

# Data Model: Language Preferences

Phase 03 uses shared entities from `../system/state-model.md`; it does not define
a separate persistence model.

## UserLanguagePreference

- Owner: authenticated username.
- Persisted value: `selection = auto | vi | en`.
- Default: `auto`, created when no preference exists.
- Update: an accepted save replaces only that user's value.

## EffectiveUiLanguage

- Ephemeral value: `vi | en`.
- Explicit selection resolves to itself.
- Auto-detect resolves the first supported normalized browser language, else
  `en`.
- It is presentation state, not canonical evidence state.

## Conversation output language

- Persisted value: `output_language = vi | en` captured at workflow submission.
- It is immutable for the saved output and does not follow later preference
  changes.
- It controls generated narrative language, not source evidence representation.

## Invariants

1. Stored preference selections are limited to `auto`, `vi`, and `en`.
2. Submitted effective languages are limited to `vi` and `en`.
3. Language labels are presentation values, never API or workflow identifiers.
4. Changing language does not mutate canonical records or citation snapshots.
