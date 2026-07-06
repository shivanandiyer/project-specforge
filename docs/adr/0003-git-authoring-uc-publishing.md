# ADR-0003: Git authors contracts; Unity Catalog publishes them

**Status:** Accepted

## Context
Should contracts live in git or in Unity Catalog? UC has no native contract object
today; Databricks' own guidance is YAML files in a UC-enabled workspace. UC does
offer Volumes (governed files), Delta tables (queryable, time-travel versioned), and
tags (small metadata). databrickslabs/ontos manages ODCS specs on UC as an app.

## Decision
**Hybrid.** Git is the authoring source of truth (PRs, diffs, CI, agent repo
context). On successful deploy, the *resolved* spec is published to a UC Volume next
to the product, and the product's objects are tagged with spec version + commit +
building agent.

## Rationale
- The write path needs review, diffing, CI triggers, and agent-native context — git's
  home turf, UC's weakness.
- The read path needs discovery and governance where consumers already look — UC's
  home turf, git's weakness.
- Publishing the *resolved* spec (environment bindings included) means consumers see
  what actually shipped, not what was authored.

## Consequences
- Two copies exist; the publisher owns keeping UC eventually consistent with deploys,
  and the reconciler flags divergence.
- Start with a Volume; move to a Delta table only if SQL-querying spec history proves
  necessary. Review ontos before building the publisher — integrate rather than
  duplicate if it fits.
