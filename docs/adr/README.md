# Architecture decision records

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-odcs-as-base.md) | ODCS as the spec foundation, not a bespoke DSL | Accepted |
| [0002](0002-single-pluggable-builder.md) | One builder agent per run, behind an SPI | Accepted |
| [0003](0003-git-authoring-uc-publishing.md) | Git authors contracts; Unity Catalog publishes them | Accepted |
| [0004](0004-compiler-generator-split.md) | Deterministic compiler / agentic generator split | Accepted |
| [0005](0005-dab-deployment-substrate.md) | Databricks Asset Bundles as the only deploy path | Accepted |
| [0006](0006-reconciliation-via-pr.md) | Reconciliation actuates via PR, not auto-mutation | Accepted |
| [0007](0007-derivations-vs-intent.md) | Split calculated-column derivations out of `intent` | Accepted |
| [0008](0008-implementation-via-pr.md) | Generated implementations land via pull request | Accepted |
| [0009](0009-deployment-ledger.md) | Append-only deployment ledger in Unity Catalog | Accepted |

Format: context → decision → consequences. New ADRs are numbered sequentially and
never deleted; superseded ADRs are marked as such and linked forward.
