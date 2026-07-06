# The specforge DSL specification

**Version:** 0.1 (draft)

specforge does not invent a contract language. The spec is an
**ODCS (Open Data Contract Standard) document** — the Bitol / Linux Foundation
open standard — extended with one namespaced block, `x-buildspec`, carrying the
information ODCS deliberately doesn't: *how the product should be built and
operated*. ODCS answers "what is promised"; `x-buildspec` answers "how specforge
should realize the promise."

Rationale for building on ODCS rather than a bespoke DSL:
[ADR-0001](../adr/0001-odcs-as-base.md). In short — collaborative authoring tooling,
CLI test tooling, and (crucially) agent familiarity all already exist for ODCS;
a proprietary DSL would forfeit all three on day one.

## 1. Document anatomy

One file per data product, `specs/<product>.odcs.yaml`:

```yaml
apiVersion: v3.0.2                     # ODCS version
kind: DataContract
id: orders-daily
name: Orders Daily
version: 2.1.0                         # contract semver — see §6
domain: sales
status: active
owner: sales-data-team

description:
  purpose: Daily-grain successful orders for finance and merch analytics.
  usage: Aggregations and joins on order_id; not for real-time operational lookups.

schema:                                # ODCS logical model (abridged)
  - name: orders_daily
    physicalName: orders_daily
    properties:
      - name: order_id
        logicalType: string
        required: true
        unique: true
        description: Natural key from the commerce platform.
      - name: order_date
        logicalType: date
        required: true
      - name: net_amount
        logicalType: number
        required: true
        description: Order total net of tax and discounts, AUD.
        classification: financial

quality:                               # ODCS quality block → compiled to tests
  - rule: uniqueness
    column: order_id
    severity: error                    # error = deploy gate; warn = monitored only
  - rule: rowCountChange
    mustBeLessThan: 30                 # percent day-over-day
    severity: warn
  - type: sql
    description: No negative net amounts
    query: SELECT COUNT(*) FROM {table} WHERE net_amount < 0
    mustBe: 0
    severity: error

slaProperties:                         # ODCS SLA block → compiled to monitors
  - property: freshness
    value: 6
    unit: h
  - property: availability
    value: 99.5
    unit: percent

x-buildspec:                           # everything below is the specforge extension
  build:
    target: auto                       # lakeflow | dbt | auto   (§5)
    hint: batch                        # streaming | batch | dimensional
    agent: claude_code                 # claude_code | genie_code (builder SPI)
    iteration_budget: 20               # max agent build-loop iterations
  sources:
    - name: commerce_orders
      connection: uc:main.bronze.commerce_orders    # UC reference — never credentials
      expectation: cdc                 # cdc | snapshot | append
    - name: fx_rates
      connection: uc:main.reference.fx_rates
      expectation: snapshot
  transformation:
    derivations:                       # compiler-computed calculated columns (§4)
      net_amount: "commerce_orders.gross_amount * fx_rates.rate_to_aud - commerce_orders.discount_amount"
    intent: |                          # natural-language intent — agent guidance,
      One row per successful order per day, keyed by order_id. Join fx_rates on   # never truth
      order currency to resolve rate_to_aud. Exclude test orders
      (customer_segment = 'internal').
  operations:
    environments:
      dev:      { catalog: dev_main,  schema: sales }
      staging:  { catalog: stg_main,  schema: sales }
      prod:     { catalog: main,      schema: sales_gold }
    compute: serverless                # serverless | job_cluster
    schedule: "0 2 * * *"
  governance:
    publish_spec: true                 # publish resolved spec to UC on deploy
    grants:
      - principal: finance-analysts
        privilege: SELECT
```

## 2. Block semantics — who consumes what

| Block | Standard | Consumed by | Becomes |
|---|---|---|---|
| identity / description | ODCS | compiler → docs, UC comments/tags | Product page, catalog metadata |
| `schema` | ODCS | compiler | UC DDL; schema-conformance tests; brief's target schema |
| `quality` | ODCS | compiler | Verifier test suite (`error`) + monitors (`warn`) |
| `slaProperties` | ODCS | compiler | Lakehouse Monitoring configs |
| `x-buildspec.build` | ext | engine | Target routing, builder selection, budgets |
| `x-buildspec.sources` | ext | compiler → brief | Resolved source bindings for the agent |
| `x-buildspec.transformation.derivations` | ext | compiler | Calculated columns, compiled directly — no agent (see §4) |
| `x-buildspec.transformation.intent` | ext | brief only | Agent guidance for join/filter/dedup logic (see §4) |
| `x-buildspec.operations` | ext | compiler | DAB targets, schedule, compute |
| `x-buildspec.governance` | ext | publisher | Grants, spec publication |

## 3. Validation contract

A spec is **valid** when it passes all three compiler validation layers
(schema / semantic / policy — see [compiler.md](../architecture/compiler.md)).
Validation runs in CI on every spec PR with no Databricks connection required for
layers 1–2; layer 3 (policy) may consult org config. A spec that doesn't validate
never reaches an agent.

## 4. Derivations vs. `intent` — where business logic lives

Business logic that maps sources to the contracted schema splits into two blocks,
by whether it needs judgment ([ADR-0007](../adr/0007-derivations-vs-intent.md)):

**`transformation.derivations`** — a map of `<output column>: <expression>`, where
the expression is a single-row SQL expression over already-resolved input fields —
one output row in, one output row out, no aggregates, no window functions. A 1:1
lookup already set up by `intent` (e.g. an FX rate per order) is fine; a one-to-many
join or aggregation is not. This is compiler territory: derivations are compiled
directly into the target's generated code, the same way `schema` becomes DDL and
`quality` becomes tests. No agent is involved, and a wrong formula is a spec diff
away from being fixed, not a build away.

**`transformation.intent`** — the one free-text field, narrowed to logic that
genuinely requires judgment: which rows qualify, which join keys to use, how to
deduplicate, which source wins on conflict. It has exactly one consumer, the
generation brief, and it is *guidance* for the agent, never *truth* — the truth is
the schema + quality + acceptance tests. If intent and tests disagree, tests win, and
the correct fix is a spec PR. This keeps natural language useful (it dramatically
improves first-pass generation quality) without letting it become an unenforceable
side-channel contract.

**Rule of thumb:** if it's a per-row expression — even one that reaches across a
1:1 lookup already set up by `intent` (e.g. resolving an FX rate per order) — it
belongs in `derivations`. If it requires aggregation, window functions, or a
one-to-many/fan-out join, it belongs in `intent`, built by the agent. The compiler's
semantic validation layer rejects a derivation expression containing an aggregate or
window function, since that's a sign the logic needs more than a per-row lookup.

## 5. Build-target routing

`target: auto` resolves via an explicit, org-editable rule table — a config file,
not a classifier — evaluated top-down, first match wins:

| Condition | Target |
|---|---|
| any source `expectation: cdc`, or `hint: streaming` | lakeflow |
| `hint: dimensional` | dbt |
| default | dbt |

Deliberately dumb in v1 so routing is inspectable and overridable (`target: dbt`
always wins over the table). Revisit as a learned decision only with evidence the
table is inadequate.

## 6. Versioning semantics

The contract `version` is semver with API-style meaning; the compiler classifies
every spec diff and the plan output states the classification:

- **major** — breaking interface change (drop/rename/retype column, tightened
  semantics). Requires a `migration` note in the spec PR.
- **minor** — additive, non-breaking.
- **patch** — ops/docs only; no contract surface change.

## 7. Reserved for future versions

- `x-buildspec.consumers` — declared downstream dependents, enabling impact analysis
  on major bumps.
- `x-buildspec.derived_from` — product-to-product composition (a spec whose sources
  are other specforge products), the data-mesh growth path.
- Multi-model contracts (one spec, several related output tables).

## 8. Conformance

An implementation of this DSL conforms if: (a) it accepts any valid ODCS v3 document,
ignoring `x-` extensions it doesn't know; (b) it rejects unknown keys *inside*
`x-buildspec`; (c) compiled outputs for the same (spec, compiler version,
environment) are byte-identical.
