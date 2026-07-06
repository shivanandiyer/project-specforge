# ADR-0001: ODCS as the spec foundation, not a bespoke DSL

**Status:** Accepted

## Context
specforge needs a contract language. Options: (a) invent a DSL tailored to our
lifecycle, (b) adopt ODCS (Bitol/Linux Foundation) and extend it, (c) adopt the
older Data Contract Specification, (d) adopt DPDS (product-level descriptor).

## Decision
Adopt **ODCS v3** as the base, with a single namespaced `x-specforge` extension
block for build/operations concerns ODCS intentionally omits.

## Rationale
- ODCS is the converging open standard (successor to the Data Contract
  Specification), governed by the Linux Foundation — the safest neutrality bet.
- Ecosystem leverage: editors, the datacontract CLI test tooling, and marketplace
  platforms already speak ODCS. A bespoke DSL forfeits all of it.
- **Agent familiarity is a feature.** Coding agents have seen ODCS; they have never
  seen our invention. Spec-format familiarity measurably improves generation quality.
- Extension via `x-` keys is the OpenAPI-proven pattern for exactly this situation.

## Consequences
- We accept ODCS's modeling opinions and version cadence; where the standard evolves,
  we track it.
- Anything we put in `x-specforge` is ours to maintain and document (the DSL spec).
- DPDS-style product-level concerns (ports, composition) are deferred; if needed,
  they layer above per-contract specs rather than replacing them.
