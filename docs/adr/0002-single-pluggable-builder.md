# ADR-0002: One builder agent per run, behind an SPI

**Status:** Accepted

## Context
Early design ran two agents (Claude Code, Genie Code) on every spec and compared
results. The project owner directed a simpler model: one agent per run, no current
preference between the two.

## Decision
Exactly one builder executes per build, selected by `x-buildspec.build.agent`.
All builders implement a fixed SPI (brief in → implementation + build log out) so
the engine is agent-blind.

## Rationale
- Halves cost and latency per build; removes an entire pipeline stage (compare/select)
  whose scoring design was speculative.
- The SPI preserves everything valuable about the dual-agent idea: swapping agents is
  config, adding agents is additive, and side-by-side comparison can return later as
  a flag — because the interface forced both implementations to stay symmetric.
- "No preference yet" is only a real option if the architecture doesn't quietly
  develop one; the SPI is that guarantee.

## Consequences
- v1 must ship both builder implementations to prove the SPI isn't a fiction, even
  though only one runs per build.
- Comparison/scoring is explicitly out of scope until the single-agent loop is proven.
