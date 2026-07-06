# ADR-0006: Reconciliation actuates via PR, not auto-mutation

**Status:** Accepted

## Context
Kubernetes operators auto-remediate drift by mutating live state. Applied naively to
data products, an agent would silently rewrite production pipelines when sources
drift — powerful, and terrifying.

## Decision
Split drift into two classes. **Mechanical drift** (missing tags/grants/monitors —
fixes that are exactly "re-apply the compiled artifact") auto-repairs, logged.
**Semantic drift** (schema breaks, persistent quality failures, SLA breaches)
produces a drift report; the evolution agent's only actuator is a **pull request**
against spec and/or implementation.

## Rationale
- Semantic drift has multiple correct responses (fix code? change contract? change
  ops?) — choosing is judgment, and judgment routes through review.
- GitOps stays invariant: production always reflects merged git state, even when the
  author of a change was an AI.
- Auto-repairing mechanical drift keeps the loop genuinely useful without expanding
  the trust surface — the repair is deterministic re-application, not generation.

## Consequences
- Time-to-heal for semantic drift includes human review latency; this is accepted
  and, for contracts, correct.
- Drift-report → PR quality becomes an important agent evaluation surface.
