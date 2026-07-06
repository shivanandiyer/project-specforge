# Roadmap

Sequencing principle: prove the deterministic spine first, add the agentic surface
second, close the loop last. Every phase ends with something demonstrable.

## Phase 0 — Specification (current)
- Finalize DSL v0.1 (ODCS + `x-specforge`), JSON Schema for CI validation
- One real example contract in `specs/examples/`
- **Exit:** a spec PR fails CI when invalid, passes when valid

## Phase 1 — Compiler spine
- Parse → validate → resolve → IR
- Emitters: UC DDL, contract tests, DAB manifest, generation brief
- `specforge plan` (diff-only, no side effects)
- **Exit:** one spec compiles to a deployable-shaped bundle + runnable test suite, deterministically

## Phase 2 — First build loop (single agent, single target)
- Builder SPI + one implementation (whichever of Claude Code / Genie Code is faster
  to stand up headless — see ADR-0002; no quality preference implied)
- Target adapter: dbt
- Verifier: pick one engine (GX / Soda / DQX) and wire compiled tests through it
- `specforge apply` through verify
- **Exit:** spec → generated dbt model → passing contract tests, unattended

## Phase 3 — Deploy and publish
- DAB deploy per environment; UC tagging; resolved-spec publish to UC Volume
- Review databrickslabs/ontos before building the publisher — integrate if it fits
- **Exit:** full spec → production loop, discoverable contract in Catalog Explorer

## Phase 4 — Observe and reconcile
- Monitor emission from SLA block; reconciler with mechanical/semantic drift split
- Mechanical auto-repair; semantic drift reports
- **Exit:** deleting a tag self-heals; breaking a source produces a drift report

## Phase 5 — Evolution agent
- Drift report → PR proposals; plan-output diff classification (major/minor/patch)
- **Exit:** a simulated source schema change yields a mergeable corrective PR

## Phase 6 — Second builder + platform surface
- Second builder implementation proves the SPI; MCP server exposing engine verbs
- Lakeflow target adapter + `auto` routing live
- **Exit:** agent swap is a one-line spec change; a chat agent can drive plan/apply via MCP

## Later / explicitly deferred
- Side-by-side builder comparison (feature-flagged experiment)
- Product composition (`derived_from`), consumer declarations, impact analysis
- Additional verifier/publisher plugins (DataHub, OpenMetadata)
