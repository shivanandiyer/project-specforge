# Roadmap

Sequencing principle: prove the deterministic spine first, add the agentic surface
second, close the loop last. Every phase ends with something demonstrable.

## Phase 0 — Specification (current)
- Finalize DSL v0.1 (ODCS + `x-buildspec`), JSON Schema for CI validation
- One real example contract in `specs/examples/`
- **Exit:** a spec PR fails CI when invalid, passes when valid

## Phase 1 — Compiler spine
- Parse → validate → resolve → IR
- Emitters: UC DDL, contract tests, DAB manifest, generation brief
- Deployment ledger: schema + bootstrap + engine writes (ADR-0009)
- `specforge plan` (diff-only, anchored on the ledger, no side effects)
- **Exit:** one spec compiles to a deployable-shaped bundle + runnable test suite,
  deterministically; plan distinguishes "never deployed" from "changed"

## Phase 2 — First build loop (single agent, single target)
- Builder SPI + one implementation (whichever of Claude Code / Genie Code is faster
  to stand up headless — see ADR-0002; no quality preference implied)
- Target adapter: dbt
- Verifier: pick one engine (GX / Soda / DQX) and wire compiled tests through it;
  evaluate Lakeflow expectations as the native backend for the lakeflow target
- Sampling policy: classification-aware masking in `specforge-context`
  (`none | masked | full`), external builders default to `masked`
- `specforge apply` through verify → **implementation PR** (ADR-0008); deploy-on-merge wiring
- **Exit:** spec → generated dbt model → passing contract tests → reviewable
  implementation PR, unattended up to the merge gate

## Phase 3 — Deploy and publish
- DAB deploy per environment on implementation-PR merge; UC tagging;
  resolved-spec publish to UC Volume; ledger records per deploy
- Migration/backfill ADR: `operations.migration` block (backfill | dual-run |
  forward-only) and engine-run backfill step — designed here, before the deploy
  path hardens around "create-only"
- Review databrickslabs/ontos before building the publisher — integrate if it fits
- **Exit:** full spec → production loop, discoverable contract in Catalog Explorer,
  every deploy queryable in the ledger

## Phase 4 — Observe and reconcile
- Monitor emission from SLA block; reconciler with mechanical/semantic drift split
- Reconciler baselines on ledger records; consumes UC system tables (lineage,
  audit, billing) rather than polling APIs; writes convergence heartbeats
- Mechanical auto-repair; semantic drift reports
- **Exit:** deleting a tag self-heals; breaking a source produces a drift report

## Phase 5 — Evolution agent
- Drift report → PR proposals; plan-output diff classification (major/minor/patch)
- Builder evaluation harness: replay ledger briefs against builders, score against
  verification outcomes, pin builder versions — makes "agent-agnostic" measurable
  and catches silent model regressions
- **Exit:** a simulated source schema change yields a mergeable corrective PR

## Phase 6 — Second builder + platform surface
- Second builder implementation proves the SPI; MCP server exposing engine verbs
- Lakeflow target adapter + `auto` routing live
- **Exit:** agent swap is a one-line spec change; a chat agent can drive plan/apply via MCP

## Phase 7 — Estate features (adoption at scale)
- Consumer/dependency declarations (`x-buildspec.consumers`) + impact analysis on
  major bumps; dependency-ordered deploy waves
- Brownfield import: `specforge import` drafts a contract from an existing UC table
  + pipeline, arriving as a spec PR — the adoption path for existing estates
- Reconciliation-check conventions: compiler-recognized completeness/conservation
  quality rules, highlighted in the generation brief
- **Exit:** a breaking change lists its affected consumers before merge; an existing
  production table can be onboarded without hand-writing its contract

## Later / explicitly deferred
- Side-by-side builder comparison (feature-flagged experiment, on the eval harness)
- Product composition (`derived_from`) — the data-mesh growth path
- Auto-merge policies for regeneration PRs (ADR-0008)
- Additional verifier/publisher plugins (DataHub, OpenMetadata)
- Multi-workspace/multi-region ledger placement (ADR-0009)
