# ADR-0008: Generated implementations land via pull request

**Status:** Accepted

## Context
The lifecycle as originally designed ran author → compile → generate → verify →
deploy, unattended. The evolution loop (ADR-0006) routes agent output through PRs,
but the *initial* build — where the agent writes the most code with the least
history — went from generation straight to production, gated only by the
compiler-emitted contract tests. Those tests assert properties of the output
(uniqueness, ranges, row-count deltas), not correctness of the logic: a join that
silently drops 3% of qualifying orders can pass every declared assertion. The
platform's own GitOps principle ("production always reflects merged git state")
was being violated precisely where trust was lowest.

## Decision
`specforge apply` drives to the **next gate**, not to production. When
implementation is missing or stale relative to the spec, apply's terminal act is an
**implementation pull request** containing:

- the generated implementation (dbt models / Lakeflow source),
- the generation brief it was built against,
- the structured build log,
- the verifier's report, attached as evidence — verification runs *before* the PR
  opens, so reviewers see code that already passes the gate.

Merging the implementation PR is what triggers deploy, exactly as merging a spec PR
triggers compile. One reviewed path serves both the initial build and evolution
(ADR-0006 PRs become the same mechanism with a different trigger).

Organizations may configure **auto-merge policies** later (e.g., regeneration diffs
below a size threshold with all tests green, for non-first builds). The v1 default
is human merge.

## Rationale
- Closes the platform's largest trust gap using its own stated principle. No
  enterprise platform team accepts unreviewed LLM-generated code writing production
  data; with this ADR none is asked to.
- Direct precedent: OpenAPI generators emit code that is committed and reviewed,
  never deployed straight from the generator. Terraform's plan/apply separation
  exists for the same reason — a human sees the change before the world does.
- Makes the verification report a *review artifact* rather than a silent gate:
  the reviewer's question shifts from "is this code plausible?" to "do these
  passing tests actually cover the contract's intent?" — a much better question.
- Review burden is managed by the compiler's incrementality: regeneration PRs show
  diffs against the previously approved implementation, and unchanged artifact
  hashes tell reviewers what they can skip.

## Consequences
- Time-to-production for a new product now includes one implementation-PR review.
  This is accepted; trust is the product.
- The repo (or a designated implementations repo) becomes the home of generated
  code — generated code is versioned, diffable, and owned like any other code,
  and "stale implementation" is now a mechanical question (implementation commit's
  brief hash vs. current spec's brief hash, recorded in the ledger, ADR-0009).
- `apply` semantics are two-step convergence: apply on an unimplemented spec ends
  at an implementation PR; apply on a merged, verified implementation ends at
  deploy. The engine must make current position in that sequence obvious in plan
  output.
- Auto-merge policy design (thresholds, first-build exclusion, required
  reviewers) becomes org configuration, validated by the policy layer.
