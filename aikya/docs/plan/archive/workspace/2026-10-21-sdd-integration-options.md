# SDD Integration Options and Delivery Plan

Date: 2026-10-21.

## Recommendation

Use a new branch from current develop and selectively reuse the reviewed SDD engine, fixtures and tests. Rebuild the integration adapters against develop's current interfaces. Do not wholesale merge the historical feature branch, replace develop's installer, or implement a new engine solely to avoid Git conflicts.

A fresh implementation reduces inherited implementation coupling, but introduces new state-machine, migration and approval defects. Neither approach guarantees no breakage. Isolation protects develop while work is reviewed; compatibility tests, explicit opt-in and acceptance gates protect behavior when the result is eventually merged.

## Current state

- New local branch created: `feat/sdd-integration-v2`.
- Base: `origin/develop`, commit `3e35e7f84558dc2a6b3c8033c52e17c978bf284c`.
- No source changes, commits, pushes, implementation or merges have been performed in the new branch.
- Original SDD source remains unchanged at `68cb4e3b1dada6e1a0d2c4c9005cab1de44bde28`.
- Previous validation: develop 223 tests passed; SDD 146 passed and one test errored; historical merge produced 19 conflicted files.
- Scope/evidence: [assessment](../../../../../../sdd-branch-audit/ASSESSMENT.md).
- Detailed implementation tasks for the reuse option: [integration plan](2026-10-21-sdd-develop-integration.md).

## Options with equivalent acceptance scope

| Dimension | A — Selective integration of existing SDD (recommended) | B — New SDD implementation on develop |
|---|---|---|
| Starting point | Current develop, reuse isolated SDD behavior and fixtures | Current develop, treat the old branch only as a requirements reference |
| Engine | Retain useful lifecycle/traceability code, repair state validation | Design and implement the lifecycle, schema and persistence again |
| Integrations | Adapt installer, six wrappers, generator gates and docs to current APIs | Write the same integrations and compatibility rules from the start |
| Tests | Preserve baseline and reuse/extend existing SDD tests; fix defective symlink test | Preserve baseline, re-author engine tests; reuse old scenarios as independent acceptance tests |
| Conflict exposure | Avoid the wholesale merge; reconcile overlapping behavior intentionally | No historical merge conflicts, but current installer and generators still require changes |
| Main risk | Accidentally carrying old assumptions into modern adapters | Omitting edge cases and protections already learned in the old branch |
| Audit issues | Explicit fixes for scope-bound approval, persisted references and completion policy | The same requirements must be newly designed and proven |
| Migration | Preserve standard profiles and support explicit opt-in and repeat installations | Same compatibility requirements; existing SDD records also need an import/migration decision |
| Effort including uncertainty margin | 28–44 engineering hours | 52–80 engineering hours |
| Schedule at about 7 focused hours/day | Approximately 4–6 working days | Approximately 8–12 working days |
| Illustrative labor cost at EUR 75/h | EUR 2,100–3,300 | EUR 3,900–6,000 |

Effort estimates have medium-low confidence. They assume one engineer familiar with this repository and include approximately 20% uncertainty allowance, rounded. Calendar estimates exclude waiting for approvals, provider quotas or CI availability. The from-scratch estimate is an engineering judgment, not a measured implementation result. It includes decisions, persistence, migration and acceptance work that reuse already partially supplies.

The cost figures are illustrative labor budgets, not a quote or measured API bill. Tax, subscriptions and model/API usage are excluded. No market rate or token savings is assumed. Provider/model and actual token records are needed to estimate API charges separately.

A direct merge followed by accepting whole files from one branch is not recommended as a third shortcut. The earlier 4–8-hour conflict-only experiment would not satisfy the acceptance scope of either option.

## Shared scope and boundaries

- Explicit `methodology=standard|sdd`; standard remains the default.
- Project types remain development, infrastructure and DevOps.
- Preserve new-project `/aikya-init` and existing-project `/aikya-analyze` separation.
- Preserve current analysis ownership protections, installer signatures and language policy.
- Add the six SDD commands without removing analyze/models/tokens: intended catalog union is 27 commands.
- Require actual spec/task context for SDD mutation; approvals never authorize remote operations implicitly.
- Validate persisted requirements, dependency graphs, coverage and strict approval values.
- Distinguish structurally valid drafts, recorded evidence and completion readiness.
- Keep engine and engineering instructions in English; living docs support configured en/es.
- Support fresh installations and upgrades without losing customized files or checks.
- No real cloud deployment, SDK installation, release publication or multi-platform product expansion.
- Single-writer local workflow is the initial scope. Concurrent transactions and stronger evidence/commit binding add an estimated 8–16 hours if required; do not describe the initial records as immutable or authenticated audit logs.

## Plan A — Selectively reuse SDD

### Phase A1: Baseline and contracts — included in the 4–6-hour engine/port package

- [x] Create `feat/sdd-integration-v2` from current develop.
- [ ] Pin refs and baseline checks at implementation start; reassess if develop changed.
- [ ] Preserve current install/adopt/docs APIs, command registry and public permissions.
- [ ] Port `sdd_engine.py`, `examples/sdd/` and useful SDD tests as a coherent change.

### Phase A2: Engine/state and active approval context — 6–10 hours

- [ ] Add failing regressions for unknown references/cycles, false approvals and historical approved spec versus current pending spec.
- [ ] Implement one state validator used by load, lint, status and mutation paths.
- [ ] Bind generators and delivery to explicit active spec/task; retain independent generation consent.
- [ ] Separate draft validity from completion readiness and declared evidence from independently executed checks.

### Phase A3: Current installation and command adapters — 6–10 hours

- [ ] Extend current `install.py` and `aikya_setup.py`; retain analysis/model/token runtime utilities.
- [ ] Implement explicit SDD opt-in and preservation across analyze/refresh and reinstalls.
- [ ] Update six new wrappers and affected delivery commands without circular redirects.
- [ ] Render SDD living docs through current en/es template modules; preserve custom checks, backups and preview fidelity.

### Phase A4: Integrated validation — 4–6 hours

- [ ] Repair the existing symlink test without weakening the path safety assertion.
- [ ] Run the complete legacy and new SDD suites, catalog, metadata and smoke checks.
- [ ] Exercise supported Python CI versions and new/existing, global/project, standard/SDD scenarios.
- [ ] Run reviewed lifecycle acceptance for development, infrastructure and DevOps in safe fixtures.

### Phase A5: Documentation and review — 3–4 hours

- [ ] Update both README files and catalog imagery/counts to reflect final behavior.
- [ ] Agree a new candidate version above 6.0.1; 6.1.0 is a proposal, not an already approved release.
- [ ] Review final diff, passing CI and behavior evidence before merging.

Subtotal 23–36 hours; plan for **28–44 hours** with the uncertainty margin. Phases can be reordered by dependency, but no implementation is authorized merely by checking the branch-creation step.

## Plan B — Implement anew

### Phase B1: Contracts and new engine design — 8–12 hours

- [ ] Freeze the same acceptance matrix as Plan A.
- [ ] Specify schema, lifecycle, approval invariants, error behavior and existing-record compatibility before implementation.
- [ ] Preserve the standard workflow and the current public installer interfaces.

### Phase B2: Fresh engine and installation — 12–18 hours

- [ ] Implement new persisted state, spec/plan/tasks, clarifications, dependency checks and approval transitions with failing-first tests.
- [ ] Add explicit opt-in, runtime packaging, installation previews and idempotent upgrade handling.
- [ ] Decide and test import of existing schema-1 SDD records, or document that the old preview format is unsupported before users depend on it.

### Phase B3: Commands and gates — 10–16 hours

- [ ] Implement six current-format command adapters and active-spec/task generator/delivery enforcement.
- [ ] Preserve new/existing routing and external-operation permissions.
- [ ] Implement draft validation and completion readiness independently.

### Phase B4: Regression and acceptance — 8–12 hours

- [ ] Add independent state-machine, malformed input, path, approval, upgrade and retention tests.
- [ ] Use existing SDD fixtures as comparison scenarios without copying its assumptions uncritically.
- [ ] Run the same CI and three project-type acceptance gates as Plan A.

### Phase B5: Documentation and review — 5–8 hours

- [ ] Document the new schema and migration policy, commands, examples, bilingual README and evidence limits.
- [ ] Complete candidate versioning and final human review.

Subtotal 43–66 hours; plan for **52–80 hours** with the uncertainty margin.

## Merge criteria for both options

1. Current develop behavior remains covered and green; all new SDD checks pass.
2. Standard mode is unchanged; SDD activates only explicitly.
3. Wrong/missing/currently unapproved spec/task fails before mutation.
4. Edited or merged persisted state cannot bypass reference, graph or approval checks.
5. User customizations and checks survive upgrades and repeated runs.
6. Language policy and installation preview match actual approved writes.
7. Drafts, failed checks and missing evidence cannot be reported as completed work.
8. Final CI and human review approve the integration before develop changes.

Use small reversible commits and retain the original feature branch for reference. After merge, revert the integration commit(s) if necessary; do not rewrite shared develop history. Reverting source does not automatically undo users' generated project artifacts, so backups and migration tests remain necessary.

## When to choose a rewrite

Choose Plan B if the intended requirements materially change—for example a multi-user transactional service, authenticated approvals, an incompatible schema, or a different assistant-independent API. Those larger requirements also invalidate the single-writer estimates above and require their own scope. The current evidence does not establish a need to discard the existing engine.

## Execution boundary

This document compares options and records branch preparation. Implementation awaits the user's choice. The preferred next action is Plan A on `feat/sdd-integration-v2`, beginning with failing regression tests for the reproduced findings. No push, merge or release is included in this preparation.

GENERATED BY AIKYA HARNESS
