# Known Risks and Mitigations

Canonical register for **product and engineering risks** that are not fully captured
in specs. Normative requirements remain in [`specs/`](../../specs/).

Use this register for:

- Free-data provider fragility and coverage gaps
- Security and compliance concerns
- Operational gaps before production
- Scope or timeline risks

## Risk register

| ID | Risk | Impact | Likelihood | Mitigation | Owner | Status |
|----|------|--------|------------|------------|-------|--------|
| R-001 | **VN free-provider depth** — `vnstock` 1h history is shallow; long intraday backfill is unreliable | Chat/workflow answers lack intraday depth; user expectations vs. reality | High | V1 daily-canonical (`vn_prices_daily`); 1h best-effort with explicit freshness/coverage diagnostics; lazy fetch for VN100 | Phase 002 | open |
| R-002 | **Single-market V1** — no US/gold coverage in product surfaces | Limited vs. Perplexity-style global finance tools | Medium | Deliberate VN100 focus; roadmap adapters dormant; see [`docs/research/perplexity-finance.md`](../research/perplexity-finance.md) | Product | accepted |
| R-003 | **Evidence tables not fully normalized in runs** — workflow output may embed evidence in run JSON vs. `evidence_objects` rows | Reload/cross-run citation integrity before Phase 003 chat | Medium | Persist lineage tables before 003.M1 ships; see `specs/system/state-model.md` | Phase 003 | open |
| R-004 | **Secrets in logs/diagnostics** — provider keys or raw scraped content leak | Security incident | Low | Fail-closed config; non-secret diagnostics only; see `runtime-config-security.md` | Platform | monitoring |
| R-005 | **No production deployment doc maturity** — `DEPLOYMENT.md` is a stub | Ops mistakes at launch | Medium | Expand runbook when target environment is chosen | Ops | open |

## Adding a risk

1. Assign the next `R-NNN` id.
2. Add a row to the table above.
3. Link to spec, ADR, or research doc when applicable.
4. Close or mark `accepted` when mitigated or explicitly accepted.

## Related documents

- Deployment: [`DEPLOYMENT.md`](../../DEPLOYMENT.md)
- ADRs: [`docs/adr/`](adr/)
- Research: [`docs/research/`](research/)
