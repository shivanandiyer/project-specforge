# ADR-0009: Append-only deployment ledger in Unity Catalog

**Status:** Accepted

## Context
specforge borrowed plan/apply from Terraform without Terraform's state. `specforge
plan` claims to diff desired state against "what's currently deployed" — but nothing
durable records what was deployed where, from which spec commit, with which artifact
hashes. UC object tags are mutable, partial, and live inside the very system being
reconciled. Without a baseline, plan cannot distinguish "never deployed" from
"deleted out-of-band," the reconciler has no last-converged reference for drift
classification, and audit questions ("what was running in prod on March 3, built by
which agent, from which contract version?") have no queryable answer.

## Decision
Every build and deploy appends a record to a **deployment ledger**: a Delta table in
a platform-owned Unity Catalog schema. Records are immutable and append-only.

Per record (illustrative, not exhaustive): product id, environment, spec commit,
spec version, resolved-spec hash, compiled artifact hashes (per emitter),
implementation commit, brief hash, builder id + version, iteration/token budget
spent, verification report reference, deploy status and DAB run reference,
reconciler status (last-converged heartbeat), timestamps.

Consumers of the ledger:
- **`plan`** anchors its diff on the latest successful record per (product, env).
- **The reconciler** baselines drift detection on the last-converged record and
  writes heartbeat/status records — the Kubernetes `status` subresource, adapted.
- **Auditors** query it directly; it is the flight recorder's index.
- **The eval harness** (roadmap) replays recorded briefs against builders and
  scores against recorded verification outcomes.
- **FinOps** reads budget-spent columns for cost-per-product attribution.

## Rationale
- Terraform's lesson is that plan/apply without state is re-deriving the world every
  run — expensive, and ambiguous under partial failure. But a *mutable* state file
  imports Terraform's locking and corruption pain. An append-only ledger avoids
  both: truth remains git (desired) + UC (observed); the ledger is **provenance,
  not authority**. Losing it loses history, not correctness.
- Delta in UC rather than files: queryable by auditors and the reconciler with SQL,
  time-travel for free, governed by the same UC permissions as everything else,
  and no new storage system to operate.
- The ledger makes the reconciler incremental (diff only products whose spec commit
  or observed signals changed since last-converged) — the scaling chokepoint fix.
- "Stale implementation" (ADR-0008) becomes a mechanical comparison of recorded
  brief hash vs. current spec's brief hash.

## Consequences
- The engine takes a write dependency on one UC table; bootstrap (`specforge init`)
  must create it. CI runners need INSERT on the ledger schema — a narrow, auditable
  grant.
- Ledger schema changes are versioned like the brief: additive freely, breaking
  only with a migration path, because downstream consumers (reconciler, eval
  harness, dashboards) read it.
- The reconciler still verifies against live UC state — the ledger tells it what
  *should* be true and what changed; it never replaces observation.
- Multi-workspace/multi-region estates need a ledger-placement convention
  (per-workspace ledger vs. central); deferred until the need is real, noted here
  so it isn't designed against.
