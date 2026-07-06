# project-specforge

*A specification-driven framework for autonomous data product engineering on Databricks.*

**The specification — not the code — is the product.** You author a declarative data
contract; specforge compiles, generates, verifies, deploys, observes, and evolves the
data product it describes. AI agents do the implementation work, but they never own
the truth. The spec does.

```
   spec.yaml ──► compile ──► generate ──► verify ──► review ──► deploy ──► observe
      ▲                                                                       │
      └─────────────────────────  evolve (drift → PR)  ◄─────────────────────┘
```

## The idea in one table

| Borrowed from | What specforge takes |
|---|---|
| **Terraform** | Declarative desired state, `plan` before `apply`, drift detection |
| **OpenAPI** | Spec-first code generation — the interface definition drives implementation |
| **GitOps** | Git is the source of truth; changes flow through PRs; deploys are reconciliations |
| **Kubernetes operators** | A control loop that continuously compares observed vs desired state |
| **dbt** | Tests as declarations, docs from metadata, environment-aware builds |
| **ODCS (Bitol / Linux Foundation)** | The open contract standard as the spec's foundation — not a bespoke DSL |
| **MCP** | Every platform capability exposed as a tool any AI agent can call |

## How it works

1. **Author** a data contract in [ODCS](https://bitol.io) YAML plus a small `x-buildspec`
   extension block — schema, quality rules, SLAs, build hints. It lives in git and goes
   through PR review like any other engineering artifact.
2. **Compile.** The deterministic compiler derives everything mechanically derivable
   from the spec: Unity Catalog DDL, a contract-test suite, a Databricks Asset Bundle
   manifest, documentation scaffolding, and a *generation brief* for the agent.
   Same spec in, same artifacts out, every time.
3. **Generate.** A single builder agent (Claude Code or Genie Code — pluggable, chosen
   per spec) fills in the one thing that requires judgment: the transformation logic
   (SQL / PySpark / Lakeflow Declarative Pipelines or dbt models) that maps declared
   sources to the contracted schema.
4. **Verify.** The generated implementation must pass the compiler-derived contract
   tests. The agent doesn't grade its own homework — the gate is deterministic.
5. **Review.** The verified implementation arrives as a pull request — code, brief,
   build log, and verification report together. A human merges it; no agent-written
   code reaches production unreviewed, and production always reflects merged git state.
6. **Deploy.** Databricks Asset Bundles promote the product through dev → staging → prod.
   The resulting Unity Catalog objects are tagged with the spec version and the agent
   that built them, and the resolved spec is published into UC next to the data.
7. **Observe & evolve.** Lakehouse Monitoring watches the SLAs the spec declared. A
   reconciler compares live state against the spec; drift produces a report, and the
   agent proposes a corrective PR. Humans approve. The loop closes.

## What makes this different

- **Determinism wherever possible, agents only where judgment is required.** The
  compiler/generator split keeps the non-deterministic surface small and auditable.
- **The quality gate is derived from the contract, not written by the agent.** Tests
  come from the spec's own quality block, so "does it satisfy the contract" is a
  mechanical question.
- **No agent-written code reaches production unreviewed.** Implementations arrive as
  pull requests carrying the brief, build log, and verification evidence; deploy
  follows merge, so production always reflects reviewed git state.
- **Evolution is a first-class phase, not an afterthought.** Most codegen tools stop
  at deploy. specforge treats the deployed product as observed state to reconcile.
- **Agent-agnostic by construction.** The builder SPI means swapping Claude Code for
  Genie Code — or adding a third agent — is configuration, not architecture.

## Repository layout

```
project-specforge/
├── specs/                 # ODCS contracts — one per data product (+ examples/)
├── compiler/              # deterministic spec → artifact derivation
├── engine/                # lifecycle orchestration (plan/apply, phase sequencing)
├── builders/              # builder SPI implementations
│   ├── claude_code/       #   headless Claude Code CLI builder
│   └── genie_code/        #   Databricks Genie Code builder
├── targets/               # build-target adapters
│   ├── lakeflow/          #   Lakeflow Declarative Pipelines
│   └── dbt/               #   dbt on Databricks
├── verifiers/             # contract-test execution engines (GX / Soda / DQX)
├── publishers/            # UC spec publishing, tagging, lineage links
├── bundles/               # Databricks Asset Bundle templates
├── docs/
│   ├── architecture/      # overview, compiler, agents, runtime
│   ├── spec/              # the DSL specification
│   └── adr/               # architecture decision records
├── VISION.md
├── ROADMAP.md
└── CONTRIBUTING.md
```

## Documentation map

| Document | What it covers |
|---|---|
| [VISION.md](VISION.md) | North star, principles, what success looks like |
| [docs/architecture/overview.md](docs/architecture/overview.md) | The full system: planes, lifecycle, data flow |
| [docs/architecture/compiler.md](docs/architecture/compiler.md) | The deterministic compiler |
| [docs/architecture/agents.md](docs/architecture/agents.md) | Builder SPI, agent contract, MCP surface |
| [docs/architecture/runtime.md](docs/architecture/runtime.md) | Deploy, observe, and the reconciliation loop |
| [docs/spec/dsl-specification.md](docs/spec/dsl-specification.md) | The spec format: ODCS + `x-buildspec` |
| [docs/adr/](docs/adr/) | Why the architecture is the way it is |
| [docs/GLOSSARY.md](docs/GLOSSARY.md) | Reference for jargon and acronyms (ODCS, DSL, DAB, SPI, MCP, etc.) |
| [ARCHITECTURE_REVIEW.md](ARCHITECTURE_REVIEW.md) | Lead-architect review: strengths, gaps, adopted changes (ADR 0008/0009), prioritized recommendations |
| [ROADMAP.md](ROADMAP.md) | Phased delivery plan |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to extend the platform |

## Status

Pre-implementation. The architecture and specification are being finalized before code.
See the [roadmap](ROADMAP.md) for the build sequence.

## License

TBD (Apache-2.0 recommended for an open framework).
