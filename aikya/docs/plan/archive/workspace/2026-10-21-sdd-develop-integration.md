# SDD and Develop Integration Implementation Plan

> **For Aikya contributors:** Implement this plan task by task using the approved Aikya workflow. Verify each change and preserve explicit user approvals. Use the checkboxes to record observed completion.

**Goal:** Integrate explicit, traceable SDD into current develop while preserving standard onboarding, installed customizations and approval boundaries.

**Architecture:** Keep develop as the baseline and port the isolated SDD engine and six public command adapters. Use shared persisted-state validation and spec/task-specific gates; retain independent user approval for generation and remote operations. SDD is a methodology layered over the three existing project types, not an application architecture.

**Tech Stack:** Python standard library, unittest, Claude Code file-based skills, GitHub Actions Python 3.10–3.13, Markdown and JSON.

**Spec:** `../../../deliverables/sdd-branch-audit/ASSESSMENT.md` (frozen source revisions, observed defects, scope and acceptance criteria).

## Global Constraints

- Baseline: origin/develop at `3e35e7f`; SDD source at `68cb4e3`; refresh and reassess if either changes.
- `project_type`: `development`, `infrastructure`, `devops`; `methodology`: `standard` default or explicit `sdd`.
- `/aikya-init` remains new-only; `/aikya-analyze` remains existing-only.
- Existing `install(..., adopt_existing=False, docs_lang=None)` keyword interfaces remain compatible.
- Engineering core is English; only living documentation under `aikya/docs/` follows configured en/es.
- Preserve custom files, safe adoption rules, check configuration and versioned backup behavior.
- No downloads, deployment, publication, force-push or unrelated cleanup is authorized by this plan.
- `EVIDENCE_RECORDED` is a local evidence record, not an independently executed check.
- The implementation skills mentioned in the standard plan header must be discovered and read if that execution method is later selected; this audit does not start execution or dispatch agents.

## Review Focus

1. A historical approved spec must not authorize a different current change.
2. Edited/merged state must not bypass requirement, dependency or approval checks.
3. Analyze/refresh must not silently enable SDD or erase an existing methodology choice.
4. Upgrading managed installations must retain user checks and local modifications.
5. Draft/failed records must never be confused with verified completion; en/es selection must remain intact.

---

### Task 1: Shared validated state and engine baseline — 4–6 hours

**Files:** Create `sdd_engine.py`; port `tests/test_sdd_v60.py` and `examples/sdd/**`; add `tests/test_sdd_state_integrity.py`.

**Interfaces:** Retain existing engine CLI verbs and JSON schema 1 for compatible records. Add `validate_state(data: dict) -> list[str]`; keep `load(root, ident)` returning `(folder, data)` but reject invalid persisted state with `SddError`.

- [ ] Add failing tests `test_loaded_state_rejects_unknown_requirement`, `test_loaded_state_rejects_unknown_dependency`, `test_loaded_state_rejects_cycle`, and `test_false_or_malformed_approval_is_not_approved`. Assert controlled failure for each probe captured in the assessment.
- [ ] Run the new tests on the ported engine and confirm the observed failures.
- [ ] Implement shared schema/reference/coverage/DAG and strict approval validation; use it from load and lint. Validate draft stage shapes without demanding completed work.
- [ ] Correct `is_directory=True` to `target_is_directory=True` in the symlink test; retain the path-escape rejection assertion.
- [ ] Run `python3 -B -m unittest discover -s tests -p 'test_sdd*.py' -v`; expect all ported and new tests green. Commit the isolated engine change.

### Task 2: Installation, onboarding and migration — 6–10 hours

**Files:** Modify `install.py`, `aikya_setup.py`, `aikya_cli.py`, `aikya_analyze.py`, `profile_builder.py`, `doc_bootstrap.py`, `docs_templates_en.py`, `docs_templates_es.py`; port the six new `aikya-skills/*/SKILL.md`; modify `aikya-init` and `aikya-answers` adapters; add `tests/test_sdd_install_compatibility.py`.

**Interfaces:** Preserve `install(..., adopt_existing=False, docs_lang=None)`. Validate/default the `methodology` field in `install.validated`. Register the union of 21 develop commands and six SDD additions; copy `sdd_engine.py` into the runtime and opted-in project. Render SDD overview through `pages(profile, modules, language='en')` and localized template modules.

- [ ] Add failing tests for standard default, new SDD profile, opted-in existing adoption, analysis refresh preserving SDD, no implicit SDD from detected stack, and all three project types in both documentation languages.
- [ ] Add tests verifying install preview includes engine, SDD docs and traceability gate; repeated upgrades preserve custom files/checks and add the gate once with backup.
- [ ] Implement the minimum compatible changes using current develop's ownership and adoption rules. Define explicit existing-project activation via reviewed declarative profile rather than silently inferring methodology.
- [ ] Keep `/aikya-init` new-only and the single language question in `/aikya-analyze`; translate ported engineering instructions to English.
- [ ] Run all onboarding, docs-language, migration and SDD installation tests. Run `python3 -B scripts/ci/check_assets.py`; expect 27 registered commands and no inconsistent source assets. Commit this compatible installation increment.

### Task 3: Bind generators and delivery to active SDD context — 6–10 hours

**Files:** Modify `sdd_engine.py`, `template/scripts/harness/scaffold.py`, `template/scripts/harness/infrastructure.py`; modify adapters `aikya-feature`, `aikya-bugfix`, `aikya-project-init`, `aikya-infra-project`, `aikya-scaffold`, `aikya-implement`, `aikya-quality`, `aikya-tests`, `aikya-verify`, `aikya-docs`; add `tests/test_sdd_active_context.py`.

**Interfaces:** Add `require_approved_task(root: Path, spec_id: str, task_id: str) -> dict` to the shared engine, validating profile type, approved stages, task existence and ready dependencies. Add optional `spec_id`/`task_id` keyword context to generator functions and `--spec-id`/`--task-id` CLI options. Require them only for SDD mutation; preserve standard behavior.

- [ ] Add failing tests with valid approved SPEC-001 and pending SPEC-002: mutation under SPEC-002 or without active context must fail even when SPEC-001 exists.
- [ ] Add tests for wrong task/type, false approval, incomplete dependencies and missing/corrupt state; standard mode remains compatible.
- [ ] Replace project-wide any-spec scans with the shared context validator and explicit argument propagation. Resolve feature/implement adapter handoff as one task execution path, avoiding circular command redirection.
- [ ] Keep structural lint distinct from completion checks. Add `validate_completion(root: Path, spec_id: str) -> list[str]` to require completed tasks and recorded passing requirement evidence without pretending to execute tests.
- [ ] Add failing-then-passing tests for incomplete tasks, missing evidence, failed declared verification and acceptable draft lint; require separate technical check evidence for completion reporting.
- [ ] Run new gate and legacy generator tests. Confirm denial occurs before any supplied runner is invoked or manifest written. Commit the scope enforcement increment.

### Task 4: Integrated acceptance and CI — 4–6 hours

**Files:** Modify `.github/workflows/tests.yml`, `tests/test_v51.py` and relevant catalog expectations; add `tests/test_sdd_end_to_end.py`; retain release and token-budget workflows from develop.

**Interfaces:** No new product API; CI must exercise source/runtime imports, catalog and both methodologies.

- [ ] Add end-to-end local fixtures for development, infrastructure and DevOps: onboarding → specify → clarify → approve → plan → approve → tasks → approve → task progress → evidence record → readiness check.
- [ ] Cover standard-to-SDD upgrade and already-SDD reinstall with custom files/checks, plus global/project runtime packaging.
- [ ] Run the full suite, asset checks, smoke profiles and metadata validation on Python 3.10–3.13. Expect no regressions against the 223-test develop baseline; test count can grow or be reorganized.
- [ ] Run reviewed manual Claude Code acceptance sessions for new and existing projects; record actual tool executions and skipped toolchain checks. Do not claim stack builds or deployments that were not performed.
- [ ] Commit CI and acceptance evidence after all mandatory checks pass.

### Task 5: Documentation, candidate version and final review — 3–4 hours

**Files:** Modify `README.md`, `README.es.md`, `CHANGELOG.md`, `VERSION`, component image or its snapshot caption, and SDD plan/status docs.

**Interfaces:** Public commands and documented opt-in must match tested behavior; no obsolete init/existing route.

- [ ] Document six commands, explicit methodology choice, approvals and evidence limits in both README files. Update live catalog counts and English engineering docs.
- [ ] Propose an unused version above 6.0.1; use 6.1.0 if approved by maintainers, with notes matching final scope. Do not revive the old 6.0.0 candidate heading as the integration release.
- [ ] Check relative links, images, catalog counts and version contract; re-run changed checks after final edits.
- [ ] Review final diff for lost develop behavior and unresolved markers; require green CI and human review before a merge.
- [ ] Deliver branch/PR and evidence summary only when execution/publication is subsequently authorized. Keep rollback as reverting the integration commit; do not rewrite shared history.

## Estimate and execution boundary

Subtotal 23–36 engineering hours; rounded planning budget **28–44 hours** with approximately 20% uncertainty allowance. At an illustrative EUR 75/h this is **EUR 2,100–3,300**, excluding tax, API and subscriptions. Approximately **4–6 working days** for one engineer; review waits may extend elapsed time. Additional concurrent-writer transactional audit support is outside that scope and adds an estimated 8–16 hours.

This plan is saved for review. The requested assessment is complete; implementation, merging and release are not performed or authorized by this document.

GENERATED BY AIKYA HARNESS
