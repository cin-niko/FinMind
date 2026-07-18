---
id: RESEARCH-FEAT-003
feature: language-preferences
status: active
implements: []
validated_by: []
adr_refs: []
---

# Research: Language Preferences

## Persist selection; resolve effective language per browser

Decision: persist `auto`, `vi`, or `en` for the authenticated user. Resolve
`auto` from the current browser's ordered language list, normalizing regional
variants and falling back to English.

Rationale: persisting only the last resolved value would make Auto-detect stop
adapting across devices. Persisting the selection preserves intent while each
browser supplies its local context.

Rejected alternative: infer language from each workflow prompt. It is ambiguous,
does not cover interface copy, and makes repeated reports unpredictable.

## Capture effective workflow language at submission

Decision: submit and store only `vi` or `en` for each workflow-created
conversation, then provide that value as an explicit generation instruction and
validate the result language.

Rationale: the captured value makes historical output stable even if the saved
preference or browser changes later.

Rejected alternative: read the current preference when rendering history. That
would relabel old output and misrepresent the language used during generation.

## Localize presentation, not evidence

Decision: use typed keys for FinMind-owned copy with English fallback. Keep
canonical records, source text, citations, identifiers, timestamps, numbers,
symbols, and saved snapshots unchanged.

Rationale: translating evidence can change meaning and sever the visible link
between a claim and its source. Localized chrome may surround source-language
evidence as long as the UI does not imply that evidence was translated.

Rejected alternative: translate citation titles and excerpts for visual
consistency. This would create derived source text without a separate provenance
contract.
