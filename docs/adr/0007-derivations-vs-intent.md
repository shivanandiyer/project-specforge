# ADR-0007: Split calculated-column derivations out of `intent`

**Status:** Accepted

## Context
`transformation.intent` was the only place to express business logic beyond schema
and quality rules — a single free-text field covering everything from join keys and
row-exclusion filters down to simple per-row arithmetic (e.g. "net amount is gross
amount times the FX rate minus the discount"). That conflates two very different
kinds of logic:

- Logic that genuinely requires judgment: which rows qualify, which source wins in a
  conflict, how to join and deduplicate.
- Logic that is a plain deterministic expression over already-resolved fields: a
  calculated column defined by arithmetic, string, or conditional operations.

The second kind doesn't need an agent at all — it's mechanically compilable, the same
way the `quality` and `schema` blocks are. Leaving it in free-text `intent` means it's
neither enforced nor visible in the contract itself; the only way to catch a wrong
formula is an after-the-fact `quality` assertion on the result, if someone thought to
write one.

## Decision
Add `x-buildspec.transformation.derivations`: an optional map of `<output column>:
<expression>`, where the expression is a single-row SQL expression over resolved
input fields (post-join, pre-aggregation). The compiler compiles derivations directly
into the target's generated code — no agent involved. `intent` remains, narrowed to
the logic that still requires judgment: which rows, which join, which exclusions,
which source wins on conflict.

```yaml
transformation:
  derivations:
    net_amount: "commerce_orders.gross_amount * fx_rates.rate_to_aud - commerce_orders.discount_amount"
  intent: |
    One row per successful order per day, keyed by order_id. Join fx_rates on order
    currency to resolve rate_to_aud. Exclude test orders (customer_segment = 'internal').
```

## Rationale
- Consistent with [ADR-0004](0004-compiler-generator-split.md)'s core bet: shrink the
  agentic surface wherever a mechanical alternative exists, rather than working around
  it with better prompting.
- A derivation is visible, diffable, and testable in the same way `schema` and
  `quality` are — a formula change is a spec PR, not a hope that the agent regenerates
  the same logic on the next build.
- Cheap escape hatch: anything that doesn't fit a single-row expression (one-to-many
  joins, aggregation, dedup, conflicting-source resolution) stays exactly where it is
  today, in `intent`, built by the agent.

## Consequences
- Authors must learn one more rule: *if it's a per-row expression — even one that
  reaches across a 1:1 lookup already set up by `intent` (e.g. resolving an FX rate
  per order) — it's a `derivation`; if it requires aggregation, window functions, or
  a one-to-many/fan-out join, it's `intent`.* Source-table count alone isn't the
  signal — a derivation may legitimately reference fields from more than one source
  once `intent` has established how they resolve to a single row.
- The compiler's parser and IR need a small expression-validation step (does the
  expression only reference known input/source columns? is it free of
  aggregate/window functions?) before treating it as compilable rather than agent
  work.
- Does not attempt to cover joins, aggregations, or conditional row-selection
  declaratively — that remains a deliberately deferred, larger DSL question, not
  something this ADR tries to solve.
