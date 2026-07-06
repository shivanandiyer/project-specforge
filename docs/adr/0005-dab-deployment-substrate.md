# ADR-0005: Databricks Asset Bundles as the only deploy path

**Status:** Accepted

## Context
Deployment options on Databricks: raw REST/Terraform provider, notebook-based
promotion, or Databricks Asset Bundles (DABs). Agents could also deploy directly.

## Decision
All deployment flows through compiler-emitted DAB manifests executed by the engine.
Agents never deploy. No direct API mutation path exists in the platform.

## Rationale
- DABs are Databricks' own declarative, environment-aware IaC surface — aligned with
  the platform's direction and with specforge's declarative thesis.
- One deploy path means one permission model: builders hold scratch-only credentials;
  production writes happen solely under the engine's identity.
- Rollback becomes re-apply of a prior commit — the same mechanism, not a special case.

## Consequences
- Anything DABs can't express is a feature gap we escalate to Databricks or work
  around in the bundle emitter — not a license for side-channel deploys.
- Engine requires DAB CLI availability in CI runners.
