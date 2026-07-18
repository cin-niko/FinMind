---
id: SPEC-FEAT-003
feature: language-preferences
status: active
owner: solo
created: 2026-07-11
last_review: 2026-07-18
implements:
  - src/finmind_api/routes/preferences.py
  - src/finmind_ui/src/features/settings
  - src/finmind_ui/src/App.tsx
  - src/finmind_agents/runtime/service.py
validated_by:
  - tests/test_app.py
  - tests/test_platform_services.py
  - src/finmind_ui/src/features/settings/i18n.test.ts
adr_refs: []
---

# Feature Specification: Language Preferences

**Feature Branch**: `[003-language-preferences]`

**Created**: 2026-07-11

**Status**: Active

**Input**: Provide a persisted Vietnamese or English product-language preference,
including browser auto-detection and a captured language for workflow-generated
narrative, without translating canonical evidence or rewriting saved output.

## Scope ownership

Phase 03 owns only language preference, FinMind-owned interface localization,
and effective workflow-output-language capture. Shared workflow, conversation,
citation, artifact, and runtime entities remain canonical in `specs/system/`
and the Phase 02 workflow foundation. Mature VN workflows and Gold workflows
require separately merged bounded feature specifications.

Production flexible chatflow language behavior is out of scope and requires a
future bounded feature specification.

## User Scenarios & Testing

### User Story 1 - Choose the product language (Priority: P1)

An authenticated user can select Auto-detect, Vietnamese, or English in Settings
and see FinMind-owned interface copy update to the effective language.

**Why this priority**: A stable, persisted language choice makes the workbench
predictable across sessions and devices.

**Independent Test**: Select each option, reload the application, and verify the
saved selection and effective UI language, including browser-order resolution
and English fallback for Auto-detect.

**Acceptance Scenarios**:

1. **Given** no saved preference, **When** the user opens Settings, **Then** the
   persisted selection is Auto-detect.
2. **Given** Vietnamese or English is selected, **When** the save succeeds,
   **Then** FinMind-owned interface copy updates immediately and the selection
   is restored for the authenticated user in later sessions and devices.
3. **Given** Auto-detect and ordered browser languages, **When** the interface
   resolves its language, **Then** it selects the first supported entry after
   normalizing `vi-*` to `vi` and `en-*` to `en`, or English if none is
   supported.
4. **Given** an unsupported selection, **When** it reaches the API, **Then** the
   request is rejected without changing the saved preference.
5. **Given** a missing Vietnamese presentation key, **When** the UI renders it,
   **Then** English copy is used without changing the underlying record or
   evidence payload.

---

### User Story 2 - Capture workflow output language (Priority: P1)

An authenticated user receives workflow-generated narrative in the effective
Vietnamese or English language captured when that workflow is submitted.

**Why this priority**: Capturing language at submission keeps generated output
reproducible even when preferences later change.

**Independent Test**: Resolve and submit both `vi` and `en`, verify backend
validation and model instruction, then change the preference and confirm earlier
saved output is unchanged.

**Acceptance Scenarios**:

1. **Given** an effective `vi` or `en` language, **When** a workflow is
   submitted, **Then** the UI sends that resolved value and the backend captures
   it as the conversation output language.
2. **Given** a captured language, **When** narrative is generated, **Then** the
   model receives an explicit language instruction and titles, sections,
   limitations, and research framing use that language.
3. **Given** a workflow language outside `vi` and `en`, **When** submission is
   validated, **Then** it is rejected before generated output is accepted.
4. **Given** generated narrative does not honor the captured language, **When**
   output validation runs, **Then** the response fails safely rather than
   silently switching language.
5. **Given** the user changes the preference later, **When** an earlier
   conversation is reopened, **Then** its saved output language and content are
   unchanged.

---

### User Story 3 - Preserve canonical evidence (Priority: P1)

An authenticated user can rely on evidence integrity regardless of the selected
interface or workflow-output language.

**Why this priority**: Localization must never appear to translate or mutate a
source record.

**Independent Test**: Render the same saved evidence in Vietnamese and English
UI chrome and compare canonical fields and citation snapshots byte-for-byte.

**Acceptance Scenarios**:

1. **Given** a language change, **When** records and citations render, **Then**
   record field names/content, citation titles and excerpts, publisher names,
   URLs, source identifiers, timestamps, numeric values, symbols, and saved
   evidence remain in their canonical representation.
2. **Given** Vietnamese UI chrome around English source evidence, **When** it is
   displayed, **Then** the interface does not imply that the source evidence was
   translated.
3. **Given** stable workflow stage and status codes, **When** they render in
   either language, **Then** presentation resolves typed locale keys without
   changing API or workflow contract identifiers.

## Edge Cases

- The browser language list is empty, missing, malformed, or contains only
  unsupported languages.
- A browser lists English before Vietnamese, or Vietnamese before English.
- Preference loading or saving fails while the application is already open.
- The user changes the language while a workflow is running.
- A locale key exists only in English.
- Canonical source content contains a mixture of Vietnamese and English.
- An unauthenticated caller requests or updates a preference.

## Requirements

### Functional Requirements

- **FR-001**: The application MUST offer exactly Auto-detect, Vietnamese, and
  English as authenticated-user language selections.
- **FR-002**: The initial persisted selection MUST be Auto-detect, and the
  server-side selection MUST persist across browser sessions and devices for the
  authenticated user.
- **FR-003**: Auto-detect MUST examine the browser's ordered language list,
  normalize `vi-*` to `vi` and `en-*` to `en`, use the first supported entry,
  and fall back to `en` when none is supported.
- **FR-004**: An explicit Vietnamese or English selection MUST override browser
  language detection and save immediately from the authenticated Settings
  surface without adding a primary navigation item.
- **FR-005**: FinMind-owned web-visible copy MUST use the effective language,
  including navigation, controls, validation and failure messages, workflow
  catalog copy, deterministic progress labels, status labels, and artifact and
  citation chrome.
- **FR-006**: Presentation code MUST resolve stable typed keys or codes through
  English and Vietnamese locale catalogs. A missing presentation key MUST fall
  back to English.
- **FR-007**: `GET /api/preferences/language` MUST return the authenticated
  user's saved selection and initialize `auto` when none exists.
- **FR-008**: `PUT /api/preferences/language` MUST accept only `auto`, `vi`, or
  `en`, update only the authenticated user's preference, and reject other
  values.
- **FR-009**: At workflow submission the UI MUST send only the resolved `vi` or
  `en` value; the backend MUST reject other values and capture the accepted
  value as the conversation's `output_language`.
- **FR-010**: Generated workflow narrative MUST receive an explicit instruction
  for the captured language and use it for generated titles, sections,
  limitations, and research framing.
- **FR-011**: A generated response that does not honor the captured language
  MUST fail safely rather than silently fall back to another language.
- **FR-012**: A later preference change MUST NOT rewrite or relabel the output
  language of a previously saved conversation.
- **FR-013**: Language selection MUST NOT translate, alter, or obscure canonical
  record fields/content, citation titles or excerpts, publisher names, URLs,
  source identifiers, timestamps, numeric values, market symbols, or saved
  evidence snapshots.
- **FR-014**: API and workflow contracts MUST retain language-neutral stable
  identifiers and codes; localized display strings MUST NOT become contract
  values.
- **FR-015**: Preference APIs and Settings MUST require an authenticated session
  and MUST NOT expose another user's preference.
- **FR-016**: User-facing language behavior MUST NOT expose raw prompts, hidden
  reasoning, provider secrets, or raw diagnostics.

### Key Entities

- **UserLanguagePreference**: The authenticated user's persisted selection
  (`auto`, `vi`, or `en`). Its canonical definition is in
  `../system/state-model.md`.
- **Effective UI Language**: The resolved `vi` or `en` value used to render
  FinMind-owned presentation copy in the current browser.
- **Conversation output language**: The immutable effective `vi` or `en` value
  captured when a workflow-created conversation is submitted.
- **Locale catalog**: Typed mapping from stable presentation keys to English and
  Vietnamese display strings, with English fallback.

## Success Criteria

- **SC-001**: 100% of preference API acceptance tests default, save, restore,
  isolate, and reject selections according to FR-001 through FR-008 and FR-015.
- **SC-002**: 100% of browser-resolution tests select the first supported
  language or English fallback exactly as defined by FR-003.
- **SC-003**: 100% of workflow-language acceptance tests capture only `vi` or
  `en` and validate generated narrative against that captured language.
- **SC-004**: 100% of evidence-preservation acceptance tests keep canonical
  records and citation snapshots unchanged across language choices.
- **SC-005**: All supported FinMind-owned UI surfaces resolve typed locale keys
  in Vietnamese and English, with deterministic English fallback for a missing
  key.
- **SC-006**: Previously saved workflow output remains unchanged after a later
  language preference update in all history-reinspection acceptance tests.

## Assumptions and dependencies

- V1 has one authenticated internal account, while persistence and authorization
  still use user ownership boundaries.
- Vietnamese and English are the only supported effective languages.
- The browser resolves Auto-detect; the server persists the selection and
  validates the effective workflow language.
- Phase 02 and `specs/system/` provide conversation, workflow, citation,
  artifact, authentication, and persistence contracts.

## Out of scope

- Translating provider or publisher source content and canonical evidence.
- Adding languages other than Vietnamese and English.
- Automatic language detection from arbitrary user chat messages.
- Defining production flexible chatflow behavior.
- Owning VN workflow analysis, Gold workflows, market-data collection, or
  conversation-history lifecycle.
