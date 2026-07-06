# Architecture Review — project-specforge

**Reviewer:** Lead Architect
**Date:** 2026-07-06
**Scope:** Full design corpus at review time (VISION, README, architecture docs, DSL spec, ADR 0001–0007, ROADMAP, CONTRIBUTING)
**Verdict:** The core bet is right and the trust architecture is unusually well-conceived. Four gaps would block enterprise adoption as designed; all four are fixable without disturbing the core. This review accepts the core architecture, adds two ADRs (0008, 0009), amends the agent context policy, and rebalances the roadmap.

---

## Executive Summary

specforge bets that a data product should be fully determined by its contract, with a deterministic compiler deriving everything mechanical and a tightly-bounded AI agent supplying only the judgment-requiring transformation logic. That bet is correct, timely, and well-differentiated: no current platform closes the loop from ODCS contract to running, monitored, *evolving* product, and the compiler/generator split is a genuinely better trust model than the "agent builds everything" pattern the industry is currently shipping.

The review found the specification plane and control-plane *concepts* strong, but the control plane's *operational reality* under-specified in four places that enterprise adoption will hit immediately:

1. **The initial build path deploys agent-generated code that no human has reviewed.** The evolution loop routes through PRs; the first build does not. This inverts the platform's own GitOps principle exactly where trust is lowest. → **ADR-0008**: generated implementations land as PRs; deploy follows merge.
2. **plan/apply is borrowed from Terraform without Terraform's state.** Nothing durable records what was deployed where, from which spec commit, with which artifact hashes. `plan` has no anchor and the reconciler has no baseline. → **ADR-0009**: an append-only deployment ledger in Unity Catalog.
3. **The agent samples production data with no egress policy.** `sample_source` can move real rows — including PII and financial data the schema itself classifies — to an external LLM. This is a security-review blocker at any regulated enterprise. → classification-aware masking, org-level sampling policy, and an explicit in-workspace vs. external builder distinction.
4. **The dependency graph is deferred to "later."** Real estates are DAGs of products; impact analysis on breaking changes, promotion ordering, and cross-product scheduling all need it. dbt's entire success is the DAG. Deferring it past ~10 products is deferring it past the point of retrofit. → promoted into the numbered roadmap.

Secondary findings — verification depth (contract tests can't catch a silently-wrong join), the absent backfill/migration lifecycle, brownfield adoption, and the missing agent evaluation harness — are recorded with recommendations below.

---

## What is strong

**The compiler/generator split (ADR-0004).** The single best decision in the design. It shrinks the non-deterministic surface to two artifacts, separates the gate from the graded, and makes everything else diffable and CI-testable without an LLM. ADR-0007 (derivations) extended it in exactly the right direction — shrinking the agentic surface further when a mechanical alternative appears. This principle should keep absorbing work from the agent over time; it is the platform's compounding advantage.

**The generation brief as a versioned interface.** The agent never reads the raw spec. This is quietly excellent: spec-format evolution can't break builders, the compiler can enrich context deterministically, and every agentic build is reproducible-in-intent. It matches where agent engineering has landed industry-wide (context construction as a first-class deterministic artifact) and most competing designs don't have it.

**PR-actuated reconciliation with the mechanical/semantic split (ADR-0006).** Adopting the Kubernetes level-triggered control loop while replacing auto-mutation with pull requests is the correct adaptation for data, where "remediation" has multiple correct answers. Auto-repairing only drift whose fix is literally "re-apply the compiled artifact" is a precise, defensible trust boundary.

**Standards discipline (ADR-0001, 0005; MCP).** ODCS rather than a bespoke DSL, DABs as the only deploy path, MCP as the agent tool surface. Each choice trades control for ecosystem leverage, and each is right. The "agent familiarity is a feature" rationale in ADR-0001 is an insight most spec-first projects miss.

**The security posture on identity.** Scratch-only credentials for builders, production writes solely through the engine's deploy identity, full flight-recorder audit per build. This is the right shape and most agentic platforms don't have it.

**Honest scope boundaries.** "What specforge is not" (VISION) and "What we will say no to" (CONTRIBUTING) are unusually crisp. The single-builder simplification (ADR-0002) shows the project can kill its own speculative complexity.

## What is weak

**W1 — No human gate on generated code before production (critical).** The lifecycle is author → compile → generate → verify → deploy. The verifier gates on compiler-emitted tests — but tests derived from the quality block assert *properties of the output*, not *correctness of the logic*. A join that silently drops 3% of orders can pass uniqueness, row-count-change, and non-negativity checks while being wrong. The evolution path routes agent output through PRs; the initial build — where the agent writes the most code with the least history — does not. No enterprise platform team will (or should) accept unreviewed LLM-generated code writing production data. Resolved by ADR-0008.

**W2 — No state (critical).** `specforge plan` claims to "diff derived artifacts and target state against what's currently deployed." Against what record? UC tags are mutable, partial, and live in the system being reconciled. Terraform without a state file re-derives the world every run and cannot distinguish "never deployed" from "deleted out-of-band." The reconciler has the same problem: it needs a durable "last converged" baseline to classify drift. Resolved by ADR-0009.

**W3 — Verification depth is oversold (high).** The docs repeatedly say "the gate is deterministic," which is true — but the gate's *coverage* is only as good as the quality block, and nothing in the DSL or docs pushes authors toward source-to-target reconciliation checks (completeness: every qualifying source row is represented; conservation: sums/counts tie out between source and target). These are expressible today as ODCS `sql` quality rules; the platform should treat them as a named category the compiler encourages (and the generation brief highlights), not an accident of author diligence. Recommendation R3.

**W4 — Agent data egress unaddressed (high).** `sample_source` gives the builder real rows. The schema block already carries classifications (`financial`, PII tags) — the sampling layer must consume them. Without masking policy, the platform's own example (financial order data) leaks to an external model on the first build. Resolved by the agents.md context-policy amendment.

**W5 — No dependency graph until "later" (high).** Consumers, `derived_from`, impact analysis — all deferred. But version-bump classification (major/minor/patch) is already in the plan output, and its entire value is *warning the affected*. With no consumer declarations there is nobody to warn. Promotion ordering across dependent products in one deploy wave is similarly unanswerable. Resolved partially by roadmap rebalance (declarations first, composition later).

**W6 — Backfill and migration are a "note" (medium).** A major version bump "requires a migration note in the spec PR." Schema evolution on tables holding data is the hardest operational problem in this domain: backfill strategy, dual-run windows, ALTER vs. recreate, reprocessing history when derivation logic changes. The platform doesn't need to solve all of it in v1, but the architecture must name where it will live (an `operations.migration` block and an engine-run backfill phase) so it isn't designed around later. Recommendation R6.

**W7 — The control plane's own runtime is unstated (medium).** Where does specforge run? A CLI in CI? A service? Who runs the reconciler on what cadence? The honest v1 answer — CLI + scheduled CI/Databricks jobs, no long-running service to operate — is also the *right* answer (it keeps the platform adoptable without an ops team), but it's nowhere written down. Now stated in runtime.md.

**W8 — Streaming products break the batch-shaped verify phase (medium).** CDC sources route to Lakeflow, but "run the contract tests after the build" has no clean meaning for a continuously-running pipeline. Lakeflow expectations exist precisely for in-flight enforcement; the verifier SPI should treat "compile quality rules to Lakeflow expectations" as a first-class verifier backend for the lakeflow target, not force everything through batch GX/Soda runs. Recommendation R7.

**W9 — No agent evaluation harness (medium).** ADR-0006 itself says drift-report → PR quality "becomes an important agent evaluation surface," and ADR-0002 preserves side-by-side comparison as a future flag — but nothing in the roadmap builds the eval capability either depends on. Every build already persists brief → diff → verification report; that corpus is the eval dataset. Recommendation R8.

## Hidden assumptions

1. **"Passing contract tests ≈ correct product."** The design's language quietly upgrades "satisfies declared assertions" to "correct." W1/W3 exist because of this assumption. The fix is not more machinery but honesty: the gate is *necessary*, review is what makes it *sufficient*.
2. **Greenfield authoring is the adoption path.** Every flow starts from a new contract. Enterprises start from 500 existing pipelines. Without a brownfield on-ramp (draft a contract *from* an existing UC table + pipeline), the addressable surface is new products only — a small fraction of any real estate. Recommendation R5.
3. **One product = one spec = one output table.** Multi-model contracts are deferred (reasonable), but the assumption leaks into the IR and brief design. Keep the IR ready for a one-spec/many-entities world even while the DSL restricts it.
4. **The builder can be swapped without quality cliff.** The SPI guarantees interface symmetry, not outcome symmetry. Until the eval harness (R8) exists, "agent-agnostic" is an untested claim.
5. **ODCS stays stable and converging.** Reasonable bet, correctly hedged in ADR-0001, but the conformance clause ("accepts any valid ODCS v3") is a real maintenance commitment as v3 evolves.
6. **Human review latency is acceptable healing time for semantic drift.** Accepted explicitly in ADR-0006 — correct for contracts, but worth re-validating for SLA-breach drift where hours matter; the mechanical/semantic line may need a third class (pre-approved remediations) eventually.

## Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Unreviewed agent code reaches production (W1) | Critical | ADR-0008 |
| Silent logic errors pass property-based gates (W3) | High | R3 reconciliation-check category; ADR-0008 review |
| PII/financial data egress via sampling (W4) | High | Context policy: classification-aware masking |
| Plan/reconcile ambiguity without state (W2) | High | ADR-0009 ledger |
| Platform stalls at ~10 products without a DAG (W5) | High | Roadmap rebalance |
| Breaking change ships with only a "migration note" (W6) | Medium | R6 migration block |
| ODCS version churn breaks conformance promise | Medium | Pin per-spec `apiVersion`; compiler supports N and N−1 |
| Builder vendor behavior shifts under the SPI (model updates change generation quality silently) | Medium | R8 eval harness; pin builder versions in build records |
| DAB expressiveness gaps force side-channel pressure | Low-Med | ADR-0005 already handles: escalate, never bypass |

## Scalability concerns

- **Contract count.** Compile is a pure function and content-addressed (already designed) — compiling 1,000 specs is embarrassingly parallel CI. This scales fine.
- **The reconciler is the scaling chokepoint.** Naïve implementation re-interrogates every product's live state every cycle. With the ledger (ADR-0009) it becomes incremental: diff only products whose desired state (spec commit) or observed signals (monitoring events) changed since last converged record. Design it event-nudged, level-triggered — Kubernetes' lesson.
- **Review throughput becomes the human bottleneck** once ADR-0008 lands. This is intentional (trust is the product), but the mitigation must be designed: regeneration PRs show *diffs against the previously approved implementation*, not whole files; unchanged-artifact hashes let reviewers skip what didn't change. The compiler's incrementality already provides the mechanism.
- **Agent cost scales linearly with builds.** Iteration budgets exist per build; the ledger should record token/compute cost per build so platform teams can see cost-per-product and cost-per-evolution — the FinOps question arrives with the first invoice.
- **The DAG (W5), once added, makes promotion a topological problem.** Deploy waves must order by dependency. Designing consumer declarations now (data model only) costs little; retrofitting ordering into a flat deploy model later costs a lot.

## Governance concerns

- **Data egress to external models (W4)** is the sharpest gap: schema classifications must drive sampling masking, and orgs must be able to set `sampling: none` and force metadata-only briefs. In-workspace builders (Genie Code) and external builders (Claude Code) have categorically different egress profiles; the docs must say so and the policy layer must distinguish them.
- **The policy validation layer is underused.** It's positioned as naming conventions and mandatory fields, but it is the natural home for real computational governance: "products in domain `finance` require `classification` on every column," "external builders forbidden for specs containing PII," "grants must come from an approved principal list." The hook exists; the examples should teach its real power.
- **Provenance is strong** (spec commit + agent + build ID tags, published resolved spec) — genuinely ahead of industry practice. The ledger strengthens it further: an append-only, queryable record of every build and deploy, which is precisely what an auditor asks for.
- **The published-spec copy in UC can drift from git between deploys.** ADR-0003 accepts this (reconciler flags divergence); acceptable, but the reconciler check must actually ship in Phase 4, not slip.

## AI architecture assessment

The agent design is ahead of the curve in structure: brief-as-interface, deterministic external gate, scratch-scoped identity, budgets, full flight recording, MCP-standardized context. These match or exceed current best practice for production agent systems.

Three gaps against the current state of the art:

1. **No evaluation loop (W9).** Modern agent platforms treat evals as infrastructure. specforge already captures the perfect eval corpus per build; it needs a harness that replays briefs against builders and scores against verification outcomes. This also makes ADR-0002's "side-by-side later" actually executable, and detects silent model-version regressions.
2. **The build loop is described but not contracted.** "Read brief → plan → implement → run tests → iterate" lives in prose. The SPI should require builders to emit a *structured* build log (steps, tool calls, test iterations, token spend) so the flight recorder is machine-analyzable — the difference between having logs and having an eval dataset.
3. **Sampling policy (W4)** — the only place the agent touches raw data, and currently ungoverned. Fixed in this review.

The single-agent-per-run decision (ADR-0002) remains correct. Resist the multi-agent-orchestration temptation; the compiler absorbing more work (ADR-0007 pattern) is the better investment than agents coordinating with agents.

## Databricks alignment

Strong and current: DABs as deploy substrate, UC as governance plane, Lakeflow Declarative Pipelines and dbt as targets, Lakehouse Monitoring for observation, Genie Code as an in-workspace builder, DQX in the verifier shortlist, MCP where Databricks' own managed MCP surface is heading.

Alignment improvements:

- **Lakeflow expectations as a native verifier backend (W8/R7).** For the lakeflow target, compiling quality rules into pipeline expectations gives in-flight, per-row enforcement — more Databricks-native than bolting a batch GX run onto a streaming pipeline. The verifier SPI already permits this; name it in the docs and shortlist.
- **The reconciler should consume UC system tables** (lineage, audit, billing) rather than polling APIs — cheaper, and billing system tables answer the cost-attribution question (Scalability) almost for free.
- **Ontos** is already flagged for publisher review (ADR-0003) — keep that discipline; don't rebuild contract-management UI.

## Novel ideas

Worth naming, because they are the platform's defensible substance:

1. **The compiler/generator split as a trust architecture** — not just a code-organization choice; the gate/graded separation is the claim competitors can't easily copy without rebuilding.
2. **The generation brief as a compiler-emitted, versioned artifact** — reproducible-in-intent agentic builds.
3. **The mechanical/semantic drift taxonomy with PR actuation** — Kubernetes reconciliation made governable for data.
4. **The derivation/intent boundary (ADR-0007)** — a ratchet that moves logic from fuzzy to deterministic over time.
5. **Contract-as-deployed publication** — resolving and publishing the spec that actually shipped, next to the data, under the data's own governance.

## Existing patterns that should be reused

- **Terraform:** the *state* half of plan/apply (adopted as the ledger, ADR-0009 — append-only rather than mutable, because git + UC remain truth). Also provider-style versioned plugin interfaces for the SPIs.
- **Kubernetes:** level-triggered, event-nudged reconciliation; a recorded `status` (last-converged) per product — lands in the ledger.
- **OpenAPI codegen:** generated code is *committed and reviewed*, never deployed straight from the generator — the direct precedent for ADR-0008.
- **dbt:** the DAG as the estate-level primitive (W5); golden-file testing of compiler emitters (already in CONTRIBUTING — keep); `state:modified`-style selective builds (the ledger enables this).
- **GitHub-flow bots (Renovate/Dependabot):** the exact UX shape for evolution PRs — small, explained, mergeable proposals with the evidence attached. Evolution PRs should read like Renovate PRs, not like diffs.

## Recommended architectural changes

**Adopted in this review (docs updated, ADRs added):**

- **ADR-0008 — Generated implementations land via pull request.** `apply` drives to the next gate, not to production: when implementation is missing or stale, apply's terminal act is an *implementation PR* carrying the generated code, the brief, the build log, and the verification report. Merge triggers deploy (GitOps invariant preserved: production always reflects merged git state). Orgs may enable auto-merge policies later (e.g., regeneration diffs under a threshold with all tests green); v1 default is human merge. *Why:* closes the platform's largest trust gap using its own stated principle; makes the verification report a review artifact instead of a silent gate; aligns initial-build and evolution flows into one reviewed path.
- **ADR-0009 — Append-only deployment ledger in Unity Catalog.** A Delta table recording every build and deploy: product, environment, spec commit, artifact hashes, implementation commit, builder + version, budgets spent, verification report reference, deploy status, timestamps. `plan` anchors on it; the reconciler baselines on it; auditors query it; the eval harness (R8) reads it. *Why:* gives plan/apply and reconciliation a durable, queryable anchor without a mutable state file's locking problems — truth stays in git and UC; the ledger is provenance, not authority.
- **Agent context policy (agents.md).** `sample_source` becomes classification-aware: columns tagged PII/sensitive are masked per org policy; per-source and org-level `sampling: none | masked | full`; external builders default to `masked`, and policy validation can forbid external builders for classified specs. *Why:* converts the platform's sharpest governance liability into a demonstrable control, using metadata the spec already carries.
- **Control-plane runtime statement (runtime.md).** v1 is a CLI invoked by CI plus scheduled jobs for the reconciler — no long-running service. *Why:* zero-ops adoptability is a feature; saying it out loud prevents accidental service-shaped design.
- **Roadmap rebalance.** Consumer/dependency declarations and brownfield import promoted from "later" into numbered phases; ledger into Phase 1; implementation-PR flow into Phase 2; eval harness into Phase 5; migration/backfill ADR scheduled.

**Recommended, not yet doc-changing (tracked in roadmap/open questions):**

- **R3 — Named reconciliation-check category.** Compiler-recognized completeness/conservation quality rules (expressible in ODCS `sql` today); the brief highlights them to the agent; docs teach them as the default for silver/gold products. *Why:* raises verification from property-checking toward correctness-checking with zero new DSL surface.
- **R5 — Brownfield import (`specforge import`).** Agent-assisted drafting of a contract from an existing UC table + pipeline, arriving (naturally) as a PR. *Why:* converts the platform's addressable market from "new products" to "any product," which is the difference between a tool and a migration path.
- **R6 — Migration/backfill as a named lifecycle concern.** An `operations.migration` block (strategy: backfill | dual-run | forward-only) and an engine-run backfill step, design via ADR before Phase 3 hardening. *Why:* major-version evolution is where data platforms actually break; a "note" is not a mechanism.
- **R7 — Lakeflow expectations as a verifier backend.** *Why:* native in-flight enforcement for streaming targets; resolves the batch-shaped-verify mismatch (W8).
- **R8 — Builder evaluation harness.** Replay ledger briefs against builders; score against verification outcomes; pin and compare builder versions. *Why:* makes "agent-agnostic" a measured claim, catches silent model regressions, and is the prerequisite for ADR-0002's deferred comparison.

## Prioritized recommendations

| # | Recommendation | Priority | Status |
|---|---|---|---|
| 1 | ADR-0008: implementation PRs — no unreviewed agent code in production | P0 | **Adopted** |
| 2 | ADR-0009: deployment ledger — durable anchor for plan/reconcile/audit | P0 | **Adopted** |
| 3 | Classification-aware sampling & egress policy | P0 | **Adopted** |
| 4 | Consumer/dependency declarations into the numbered roadmap | P1 | **Adopted (roadmap)** |
| 5 | Reconciliation-check category (completeness/conservation) | P1 | Roadmap |
| 6 | Control-plane runtime statement | P1 | **Adopted** |
| 7 | Migration/backfill ADR before Phase 3 | P1 | Roadmap |
| 8 | Brownfield import | P2 | Roadmap |
| 9 | Lakeflow-expectations verifier backend | P2 | Roadmap |
| 10 | Builder eval harness on ledger corpus | P2 | Roadmap |

**Is it solving the right problem?** Yes. Contract-first, agent-built, deterministically-gated data products is the correct synthesis of where infrastructure (Terraform/K8s), interfaces (OpenAPI), and AI engineering have each individually landed — and nobody has assembled it for data yet. The adjustments above don't change the destination; they make the trust story real enough for an enterprise platform team to say yes, and the operational story real enough for them to still be saying yes six months in.
