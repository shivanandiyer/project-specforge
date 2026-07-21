# ADR-0011: Quarantine as a compiler-owned transformation concern

**Status:** Accepted

## Context
The ODCS `quality` block gives two outcomes for a failing rule: `error` (blocks
deploy) or `warn` (monitored only). Neither expresses a third outcome that real
pipelines routinely need: *keep running, but don't let this row through — capture
it, with a reason, somewhere queryable.* A referenced
[PoC](https://github.com/shivanandiyer/dbrx-spec-driven-development) built exactly
this: a silver layer with hard row-level validation (order ID pattern, valid
enums, positive quantities, discount bounds) where failing rows are written to a
`quarantined_orders` table carrying a `quarantine_reason`, while valid rows flow
through untouched. This is a standard production pattern (the data-engineering
analogue of a dead-letter queue), and specforge's DSL has no way to declare it.

Extending ODCS's native `severity` enum with a third value (e.g. `quarantine`)
was considered and rejected: it would produce documents that other ODCS-consuming
tools can't correctly interpret, undermining the entire rationale for adopting
ODCS in the first place ([ADR-0001](0001-odcs-as-base.md) — ecosystem
interoperability). The `quality` block stays ODCS-pure.

## Decision
Add `x-buildspec.transformation.quarantine`, an optional object declaring
row-level validity checks and where their failures go:

```yaml
transformation:
  quarantine:
    enabled: true
    sink: orders_daily_quarantine        # optional; default <table>_quarantine
    reason_column: quarantine_reason     # optional; default quarantine_reason
    rules:
      - name: missing_order_id
        check: "commerce_orders.order_id IS NOT NULL"
        reason: "order_id missing"
      - name: negative_quantity
        check: "commerce_orders.quantity > 0"
        reason: "non-positive quantity"
```

Each rule is a single-row boolean expression, same shape and same validation
constraints as [`derivations`](0007-derivations-vs-intent.md) (no joins, no
aggregation). The compiler emits: a filter on the curated output (rows failing any
rule are excluded), and a `sink` table containing the failing rows plus a
`reason_column` capturing which rule(s) failed, in a stable readable format. This
is compiler territory — no agent involved, and it is a strictly *additive* sibling
to `quality`: `quality` still gates the build and feeds monitors; `quarantine`
governs row-level disposition of what actually ships into the curated table.

## Rationale
- Preserves ODCS conformance exactly — `quality` semantics are untouched; the new
  capability lives entirely in the extension block, same discipline as
  `derivations` and `deduplication`.
- Matches how the mechanical/semantic split already works elsewhere in this
  architecture ([ADR-0006](0006-reconciliation-via-pr.md)): "which rows are
  individually invalid, and why" is a mechanical question once the check is
  written down; "should we accept a higher malformed-row rate this week" is not,
  and stays a `quality`/monitoring/human question.
- Silent row-dropping is a common, hard-to-debug production failure mode. Making
  quarantine a named, compiler-emitted concept means every specforge product gets
  a queryable answer to "what got rejected, and why" without an author having to
  hand-roll it in `intent` and hope the agent gets the sink table right.

## Consequences
- Authors get a fifth rule of thumb (alongside ADR-0007 and ADR-0010): *if a
  row-level validity check has a clear boolean condition and an exclude-don't-fail
  disposition, it's a `quarantine` rule; if failing it should mean the whole build
  fails or gets a monitored warning, it stays in `quality`.*
- The compiler needs a new emitter (`quarantine`, alongside `catalog`, `tests`,
  `derivations`) that produces both the filtered curated-output logic and the
  sink table's DDL — see [compiler.md](../architecture/compiler.md).
- `quarantine.rules[].check` expressions share the same semantic-validation pass as
  `derivations` and `deduplication` (known columns only, no aggregates).
- Does not cover cross-row quarantine triggers (e.g., "quarantine every record from
  a source batch if the batch's error rate exceeds 5%") — that remains a judgment
  call for `intent` or a future DSL extension, not solved here.
