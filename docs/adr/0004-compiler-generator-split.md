# ADR-0004: Deterministic compiler / agentic generator split

**Status:** Accepted

## Context
The naive architecture hands the whole spec to an agent that "builds everything."
That makes the entire output non-deterministic, lets the agent write the tests it is
then graded by, and makes every build review a full-surface review.

## Decision
A deterministic compiler derives everything mechanically derivable (UC DDL, contract
tests, DAB manifest, monitors, docs, and the generation brief). The agent produces
only transformation logic, against the brief, gated by compiler-emitted tests it
cannot modify.

## Rationale
- Shrinks the non-deterministic surface to the one artifact that genuinely needs
  judgment.
- Separates the gate from the graded: tests derive from the contract, not from the
  agent.
- Compiled outputs are pure functions of (spec, compiler version, environment) —
  cacheable, diffable, CI-testable without an LLM.
- Direct precedent: OpenAPI generators, Terraform providers, dbt compilation.

## Consequences
- The compiler is real software with an IR and emitter suite — the largest
  deterministic engineering investment in the project.
- The brief becomes a versioned interface between compiler and builders; changes to
  it are breaking changes for the builder SPI.
