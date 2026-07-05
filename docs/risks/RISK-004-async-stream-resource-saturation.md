---
id: RISK-004
status: open
severity: high
likelihood: medium
owner: engineering
created: 2026-07-04
last_reviewed: 2026-07-04
related_specs:
  - specs/002-workflow/spec.md
  - specs/002-workflow/plan.md
  - specs/002-workflow/contracts/api-contract.md
related_adrs:
  - docs/adr/ADR-002-direct-async-sse-streaming.md
---

# RISK-004: Async Stream Resource Saturation

## Summary

Async-native SSE endpoints can keep many workflow or chatflow streams open, but
downstream resources remain finite. Unbounded streams can saturate provider API
quotas, model budgets, database pools, memory, file descriptors, CPU, or sync
offload workers.

## Impact

If this risk materializes, one user or workload can degrade service for others,
increase provider/model cost, exhaust database connections, delay stream events,
or make the UI appear stuck. Blocking sync code inside async paths can also stall
the event loop and defeat the multi-user streaming design.

## Triggers

- Large numbers of concurrent workflow/chatflow streams.
- Slow model responses or provider calls holding streams open.
- Sync-only provider libraries called directly from async request handlers.
- Database pool exhaustion during final run persistence.
- Provider rate limits or model quota errors.
- CPU-heavy parsing, chart generation, or normalization on the event loop.

## Mitigation

- Enforce process-local global stream, per-user stream, and sync-offload
  concurrency limits in Phase 02.
- Use process-local configurable semaphores in Phase 02, with an internal
  limiter interface that can later move to Redis-backed leases/counters.
- Defer Redis until multi-worker or multi-instance deployment requires
  distributed coordination.
- Return safe `429` responses before stream start when capacity is exhausted.
- Prefer native async provider/model/database clients.
- Run unavoidable sync-only libraries through bounded thread/process offload with
  timeouts and cancellation handling.
- Emit heartbeat and safe failure events for long-running streams.
- Persist final completed, partial, or failed output for history where possible.
- Add stream/concurrency tests before implementation is marked complete.

## Residual Risk

Provider and model latency can still vary even with limits. Some sync libraries
may not cancel promptly once offloaded. Process-local semaphores do not protect
capacity across multiple API workers or app instances. This remains open until
production traffic and provider behavior are measured, limits are tuned, and a
Redis or equivalent distributed limiter is introduced before multi-worker
deployment.

## Validation

- Tests hold at least 10 authenticated workflow/chatflow streams concurrently.
- Tests assert capacity exhaustion returns `429` with a safe error body.
- Tests assert process-local limiter behavior for global and per-user stream
  limits plus sync-offload limits where practical.
- Tests assert sync-only provider paths do not run directly on the event loop.
- Tests assert stream events continue or fail safely during slow provider/model
  responses.
- Review checks confirm no raw provider payloads, secrets, or unsafe diagnostics
  appear in stream frames.

## References

- `specs/002-workflow/spec.md`
- `specs/002-workflow/plan.md`
- `specs/002-workflow/contracts/api-contract.md`
- `docs/adr/ADR-002-direct-async-sse-streaming.md`
