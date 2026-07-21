# ADR-0010: Declarative deduplication

**Status:** Accepted

## Context
A [PoC](https://github.com/shivanandiyer/dbrx-spec-driven-development) written
directly as a Genie Code prompt (not through specforge) needed to deduplicate CDC
source rows: "use `order_id` as the business key; for duplicates, keep the record
with the latest `source_updated_at`." That prompt-spec left the rule as prose for
the agent to implement — but the rule itself has no judgment in it. Business key,
tiebreaker column, keep-latest-or-earliest: three facts fully determine the logic.
Today, `transformation.intent` is the only place to say this, which means an agent
re-derives (and could subtly mis-derive) the same mechanical window function on
every regeneration.

## Decision
Add `x-buildspec.transformation.deduplication`, an optional object:

```yaml
transformation:
  deduplication:
    key: order_id                    # business key (one or more columns)
    order_by: commerce_orders.source_updated_at
    keep: latest                     # latest | earliest
```

The compiler compiles this directly into a window-function dedup (`ROW_NUMBER()
OVER (PARTITION BY key ORDER BY order_by DESC/ASC) = 1`) in the target's generated
code. No agent involved. `intent` is no longer the place to describe dedup logic
that fits this shape — only dedup requiring actual judgment (e.g., "prefer the
source with the more complete record" — a rule with no single deterministic
tiebreaker) stays in `intent`.

## Rationale
- Same bet as [ADR-0007](0007-derivations-vs-intent.md): dedup-by-key-and-tiebreaker
  is a mechanical operation once you have the three inputs, so it belongs in the
  compiler for the same reasons derivations do — visible, diffable, testable
  without an LLM in the loop.
- Real-world evidence, not speculation: the pattern this ADR formalizes is exactly
  what a working PoC needed, expressed as a one-line business rule.
- Narrows the agentic surface further without adding DSL complexity disproportionate
  to the value — three fields cover the overwhelmingly common case.

## Consequences
- Authors get a fourth rule of thumb alongside ADR-0007's: *if dedup reduces to "one
  business key, one tiebreaker column, keep latest or earliest," it's
  `deduplication`; if choosing the surviving row needs judgment beyond a single
  column, it's `intent`.*
- The compiler's semantic validation layer checks `key` and `order_by` reference
  known input columns, the same check already required for `derivations`
  ([ADR-0007](0007-derivations-vs-intent.md)).
- Does not attempt multi-column tiebreakers, custom merge logic (e.g., coalescing
  fields across duplicate versions), or dedup across multiple sources — those stay
  in `intent` until real demand justifies more DSL surface.
