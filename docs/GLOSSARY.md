# Glossary

A quick reference for the standards, acronyms, and specforge-specific terms used
throughout these docs. If you hit an unfamiliar term in the architecture or spec
docs, it's probably here.

## Standards and external tools

| Term | Meaning |
|---|---|
| **ODCS** | Open Data Contract Standard — the [Bitol](https://bitol.io) / Linux Foundation open standard for describing a data product's schema, quality rules, and SLAs. specforge specs are ODCS documents; specforge doesn't invent its own contract language. See [ADR-0001](adr/0001-odcs-as-base.md). |
| **Bitol** | The Linux Foundation AI & Data project that stewards ODCS. |
| **DAB** | Databricks Asset Bundles — Databricks' infrastructure-as-code format (`databricks.yml`) for defining and deploying jobs, pipelines, and other workspace resources. specforge's sole deployment mechanism ([ADR-0005](adr/0005-dab-deployment-substrate.md)). |
| **UC** | Unity Catalog — Databricks' governance layer for data and AI assets (catalogs, schemas, tables, grants, lineage). Where specforge publishes resolved specs and tags built objects. |
| **Lakeflow** | Databricks Lakeflow Declarative Pipelines (formerly Delta Live Tables) — a declarative framework for building batch/streaming pipelines. One of the two v1 build targets. |
| **Genie Code** | Databricks' own coding-agent product ("define a skill, describe a task, review a plan, execute it"). One of the two v1 pluggable builder agents. |
| **Claude Code** | Anthropic's headless-capable coding agent CLI. The other v1 pluggable builder agent. |
| **GX** | Great Expectations — an open-source data quality/testing framework. One candidate verifier backend. |
| **Soda** | Soda Core — another open-source data quality/testing framework. One candidate verifier backend. |
| **DQX** | Databricks Labs DQX — a Databricks-native data quality framework. One candidate verifier backend. specforge picks one of GX/Soda/DQX in Phase 2 (see [ROADMAP.md](../ROADMAP.md)). |
| **MCP** | Model Context Protocol — the open protocol for exposing tools/context to AI agents. specforge exposes both live build context (`specforge-context` server) and the engine's own lifecycle commands (`plan`, `apply`, `compile`, `verify`, `drift`) as MCP tools. See [agents.md](architecture/agents.md). |
| **GitOps** | The practice of using git as the source of truth for desired state, with changes flowing through PRs and deploys as reconciliations toward what's committed. specforge borrows this model wholesale. |

## Acronyms used structurally

| Term | Meaning |
|---|---|
| **DSL** | Domain-Specific Language — here, the spec format itself: ODCS plus the `x-buildspec` extension block. See [dsl-specification.md](spec/dsl-specification.md). |
| **SPI** | Service Provider Interface — a plugin boundary. specforge has four: **builder** (Claude Code / Genie Code), **target** (Lakeflow / dbt), **verifier** (GX / Soda / DQX), **publisher** (UC / others). See [overview.md](architecture/overview.md#component-boundaries-and-extension-points). |
| **IR** | Intermediate Representation — the compiler's normalized, target-independent model of a product (entities, columns, constraints, quality assertions, SLAs) that all emitters consume instead of raw YAML. See [compiler.md](architecture/compiler.md). |
| **CDC** | Change Data Capture — a source `expectation` value meaning the source streams row-level inserts/updates/deletes rather than full snapshots. Routes builds toward Lakeflow. |
| **SLA / SLAs** | Service Level Agreement(s) — the ODCS `slaProperties` block (freshness, availability, etc.), compiled into Lakehouse Monitoring configs. |
| **ADR** | Architecture Decision Record — a short document capturing a specific design decision and its rationale. See [docs/adr/](adr/). |
| **PR** | Pull Request — how every change reaches `main`, whether authored by a human or proposed by the evolution agent. |
| **CLI** | Command-Line Interface — the `specforge plan` / `specforge apply` workflow verbs. |

## specforge-specific terms

| Term | Meaning |
|---|---|
| **Spec** / **contract** | The single authored artifact: an ODCS document plus `x-buildspec` block, one per data product, living in git. The only place truth lives. |
| **`x-buildspec`** | The namespaced ODCS extension block carrying everything ODCS doesn't cover — build routing, source bindings, transformation intent, operations, governance. See [dsl-specification.md](spec/dsl-specification.md). |
| **Engine** | The deterministic orchestrator that sequences the lifecycle (`plan`/`apply`) and invokes the compiler, builder, verifier, and publisher in order. |
| **Compiler** | The deterministic component that derives every mechanically-derivable artifact from a spec: DDL, tests, DAB manifest, docs, monitors, and the generation brief. Contains no LLM calls. See [compiler.md](architecture/compiler.md). |
| **Generation brief** | The compiler's self-contained instruction package handed to the builder agent — inputs, target schema, acceptance tests, constraints. The agent never reads the raw spec, only the brief. |
| **Builder agent** | The pluggable coding agent (Claude Code or Genie Code) that writes transformation logic against a generation brief. The system's deliberately small non-deterministic surface. |
| **Verifier** | The component that executes the compiler-emitted contract-test suite against a build and produces the pass/fail deploy gate. |
| **Publisher** | The component that writes governance records — UC tags, the published resolved spec — after a successful deploy. |
| **Reconciler** | The component that compares live/observed state (UC + monitoring + runs) against desired state (spec, compiled) and produces either an auto-repair (mechanical drift) or a drift report (semantic drift). |
| **Evolution agent** | The builder SPI reused with a different trigger: takes a drift report as input, proposes a PR against the spec and/or implementation as output. Never mutates directly. |
| **Resolved spec** | The spec after the compiler's resolve stage — environment bindings filled in, build target resolved from `auto`. What's actually published to UC; what actually shipped. |

## See also

- [README.md](../README.md) — project overview and documentation map
- [VISION.md](../VISION.md) — north star and principles
- [docs/architecture/overview.md](architecture/overview.md) — the full system, planes, and lifecycle
