# Vision

## The problem

Data products today are built code-first. The contract — what the data means, what
quality it guarantees, who owns it, how fresh it is — exists, if at all, as
documentation written *after* the pipeline, drifting from reality the moment it's
published. Every data team re-derives the same scaffolding (DDL, tests, deployment
config, docs) by hand, and every AI coding assistant bolted onto this workflow
inherits its central flaw: the code is the truth, and the truth is unreviewable,
unqueryable, and unenforceable.

Meanwhile, the software world solved this pattern twice. Infrastructure went
declarative: Terraform and Kubernetes made *desired state* the artifact and turned
implementation into reconciliation. APIs went spec-first: OpenAPI made the interface
definition the source from which servers, clients, tests, and docs are generated.
Data engineering has the standards to do the same — ODCS gives us the contract
format — but no platform that closes the loop from contract to running, monitored,
evolving product.

## The thesis

**A data product should be fully determined by its specification.** Given a contract
that declares the schema, quality rules, SLAs, sources, and build shape, everything
else — the pipeline code, the catalog objects, the tests, the deployment bundle, the
monitors, the documentation — is *derived*. Some of that derivation is mechanical
(a compiler's job). Some requires judgment (an agent's job). None of it should be
hand-authored, and none of it should be the source of truth.

This inverts the current relationship between AI and data engineering. Instead of an
assistant helping a human write code that then becomes the truth, the human (or an
agent, with review) writes the *contract*, and machinery — deterministic where
possible, agentic where necessary — keeps reality converged to it.

## Principles

1. **Specification first.** The spec is the only authored artifact. If a piece of
   information matters, it belongs in the spec, not in generated code.
2. **AI orchestrates; it does not own the truth.** Agents generate, propose, and
   repair. They never define what "correct" means — the contract does, and the
   verification gate that enforces it is deterministic.
3. **Determinism wherever possible.** Every artifact that can be mechanically derived
   is derived by the compiler, reproducibly. The agentic surface is deliberately
   minimal: transformation logic and evolution proposals.
4. **GitOps native.** Specs live in git. Changes are PRs. Deploys are reconciliations
   of git state. Everything the AI produces — generated implementations and evolution
   proposals alike — arrives as a PR a human can review; nothing agent-written
   reaches production unmerged.
5. **Standards over invention.** ODCS for contracts, Databricks Asset Bundles for
   deployment, MCP for agent tooling, established quality frameworks for testing.
   specforge invents only the connective tissue.
6. **Vendor extensible.** Builders, targets, verifiers, and publishers are plugin
   interfaces. Databricks is the first-class runtime, not a hard dependency of the
   architecture.
7. **Secure and governed by default.** Unity Catalog governs every produced object;
   the published spec sits under the same governance as the data it describes; agents
   operate with scoped, auditable credentials and every build is logged.
8. **Observable and evolvable.** Deploy is the midpoint of the lifecycle, not the
   end. The platform watches what it shipped and proposes how it should change.

## What success looks like

- A data engineer writes (or asks an agent to draft) a ~100-line contract, opens a
  PR, and after two quick reviews — the contract, then the agent's implementation
  PR with its verification evidence attached — has a tested, documented, governed
  data product running in Databricks, without writing pipeline code.
- A consumer discovers the product in Unity Catalog and finds the *actual contract*
  next to the data — not stale documentation.
- Six months later a source schema shifts. The reconciler detects contract drift,
  the agent opens a PR with the corrected transformation and an updated spec minor
  version, and the owner merges it. The product evolved without an incident ticket.
- A second organization adopts specforge with a different coding agent and a
  different test engine, changing configuration — not architecture.

## What specforge is not

- **Not a data catalog.** Unity Catalog (and tools like Ontos, DataHub, OpenMetadata)
  own discovery. specforge publishes into them.
- **Not another orchestrator.** Lakeflow Jobs / Workflows run the pipelines. specforge
  produces what they run.
- **Not a bet on one AI vendor.** The builder SPI exists precisely so the agent is a
  replaceable component.
- **Not a no-code tool.** It's an engineering platform: the spec is code-reviewed,
  version-controlled, and testable. It removes *undifferentiated* engineering, not
  engineering.
