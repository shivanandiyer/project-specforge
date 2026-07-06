# Contributing

specforge is structured as a set of small deterministic components around plugin
interfaces. The highest-leverage contributions are new SPI implementations and
compiler emitters.

## Ground rules
1. **The spec is the truth.** No feature may introduce authored artifacts that
   bypass the contract. If information matters, it goes in the DSL (via proposal).
2. **Determinism is load-bearing.** Nothing in `compiler/`, `engine/`, `verifiers/`,
   or `publishers/` may call an LLM. Agentic code lives in `builders/` only.
3. **Decisions get ADRs.** Anything that changes an interface or a principle needs a
   decision record in `docs/adr/` in the same PR.

## Extension points
| To add | Implement | Register |
|---|---|---|
| A builder agent | the Builder SPI (`docs/architecture/agents.md`) | `builders/<name>/` |
| A build target | the Target adapter (IR → scaffold shape) | `targets/<name>/` |
| A test engine | the Verifier SPI (compiled tests → results) | `verifiers/<name>/` |
| A governance sink | the Publisher SPI | `publishers/<name>/` |
| A policy rule | compiler policy-validation plugin | `compiler/policies/` |

## Workflow
- Spec/DSL changes: PR against `docs/spec/dsl-specification.md` +
  [`schema/x-buildspec.schema.json`](schema/x-buildspec.schema.json) + an ADR if
  semantics change. DSL is versioned; breaking changes need a major bump. CI
  ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs
  `scripts/validate_spec.py` against every spec under `specs/` on every PR.
- Docs changes: CI runs `scripts/check_doc_links.py` — a moved or renamed file that
  breaks a cross-reference fails the build, not a future reader.
- Code: conventional PR flow; CI must show `specforge plan` output for any change
  touching emitters (golden-file tests keep outputs reviewable as diffs).
- Every builder PR must pass the builder conformance suite (headless run, scratch-only
  writes, budget respected, build log emitted on failure).

## What we will say no to
- Direct-to-production mutation paths (see ADR-0005/0006)
- Free-text spec fields that carry enforceable meaning (see DSL §4)
- Vendor lock-in above the runtime layer
