# Repository Cleanup Validation

Baseline: 08db4879ae3a8697c91adb0cc46bd76e333c693b. Cleanup was applied locally on feat/sdd-spec-coding-templates. The Python package restructuring is proposed separately and has not been implemented.

## Applied changes

- Removed only the verified redundant root Aikya-Harness.png (1,057,227 bytes). The referenced docs/images/aikya-harness.png and both README image links remain intact.
- Archived seven historical plans under plan/archive/docs-plans/, ten validation artifacts under validation/archive/2026-10-22/, and the unique Spanish image plus manual edit recipe under images/archive/. Nineteen paths moved; unique assets and historical results were preserved. Historical plan/evidence status is explicit; original bytes are recoverable from the recorded baseline and local backup.
- Normalized the twelve legacy/root/example Markdown footer cases without changing pinned third-party bytes or historical fixtures.
- Retained all 265 source gallery files and all 253 checksummed outputs. The Spanish guide now explains old command names and the unavailable synthetic fixture log. Snapshot output hashes remain unchanged.
- New registered runtimes omit the 265-file historical gallery. The runtime-local example guide links to the immutable source snapshot. Source gallery navigation remains local.
- Upgrades retire only unchanged gallery files listed in the previous manifest, retain verified backups, preserve custom/untracked files and symlinks, and stop on conflicting backups. A customized guide retaining a local gallery link conservatively preserves that gallery. No user project documentation or private state was migrated.
- Retained module_root and resolve_actor_model byte-for-byte after compatibility review. Their modules are active; absence of a production caller is insufficient to remove public helpers.

## Observed acceptance

| Python | Tests | Result | Seconds |
|---|---:|---|---:|
| 3.10 | 478 | OK | 133.594 |
| 3.11 | 478 | OK | 130.453 |
| 3.12 | 478 | OK | 142.637 |
| 3.13 | 478 | OK | 137.696 |

All four full unittest runs passed. The runs emit the pre-existing project_discovery ResourceWarning; this is not a newly verified resource-management fix.

- Six new runtime-payload tests cover the 48 onboarding combinations and upgrade retention, repeatability, backup collisions, symlinked files/directories, manifest traversal and customized guide preservation. The initial behavioral tests failed on the baseline; they pass with the implemented distribution policy.
- The 48 init/analyze cases cover development/infrastructure/DevOps × ODD/SDD × en/es × global/project. Installed CLIs execute from an unrelated cwd with PYTHONPATH empty; no root docs/, plans/ or plan/ is created by those cases. This does not establish a general model-authoring path enforcement policy.
- Actual upgrades from the Git baseline passed in both scopes: 265 old gallery files, 264 verified files backed up and retired, one intentionally modified file preserved, repeated upgrade safe, and installed onboarding successful. Controlled old-version setup and new-version execution ran in temporary isolated directories.
- All 14 example profiles passed offline smoke checks. Catalog integrity passed for 120 templates and 155 reference files. Agent/skill metadata passed for 30 agents, 29 skills and 27 public commands.
- All 253 gallery document checksums passed; all five retired-command hash records and historical fixtures remain unchanged. Shared document layout/index validation passed.
- The current working-tree source archive omits the duplicate root image, retains the canonical image and resolves both README image references. This was a local archive inspection, not a new published Git release.
- Source-quality checks for the two changed Python files passed with no errors or warnings. The full source audit still reports install.py at 1,309 lines, above the 1,000-line limit. Its separate modularization remains pending; cleanup does not make the entire quality audit green.
- Release contract remains 6.1.1, without a v6.1.1 tag or publication. The static instruction proxy remains 3,107/6,000; it is not billable model usage.

## Distribution and local cache measurements

Registered inventory: 679 → 414 entries (265 fewer; 39.0%). Raw selected source bytes: 2,909,925 → 2,533,312 (12.9% smaller including the updated setup code). The rendered new payload is 2,535,073 bytes; no destination collisions. Existing upgrade backups intentionally consume space for recovery.

After the test matrix, 334 ignored __pycache__ .pyc files (5,355,128 bytes) were removed from this checkout. Symlinks and all other ignored user data were excluded. Cache cleanup is local and regenerable, not a release-payload reduction.

## Preserved boundaries and remaining work

Two illustrative ADR paths inside pinned upstream templates remain unresolved by design. The historical gallery summary still refers to its original synthetic fixture-evidence.log; the guide now explicitly identifies that unavailable provenance. No log or executed application result was invented. Other first-party local links must resolve after the migration.

The remaining first-party guides and active images under root docs/ are referenced and retained. Their broader relocation and generated-report path guard belong to the existing documentation-path plan. The installer and package refactors are also separate, proposed work. The user assigned real authenticated Claude SDK testing to another environment; this cleanup did not call a live provider, install dependencies, deploy, push or publish.

## Reproducible checks

- python3.X -m unittest discover -s tests -p 'test_*.py' -q, for X = 10, 11, 12, 13.
- python3 scripts/ci/smoke_profiles.py
- python3 scripts/ci/validate_agent_assets.py
- python3 documentation_templates.py check
- python3 scripts/ci/release_contract.py check
- python3 context_budget.py
- python3 code_quality.py aikya_setup.py tests/test_runtime_payload.py
- python3 code_quality.py --all (known install.py size error remains)

See [operation manifest](REPOSITORY_CLEANUP_MANIFEST.json), [observed results](REPOSITORY_CLEANUP_RESULTS.json), [original audit](../research/2026-10-23-repository-cleanup-audit.md), [historical inventory](../research/2026-10-23-repository-cleanup-inventory.json) and the [proposed Python structure](../plan/2026-10-23-python-project-structure.md). The original inventory remains an unapplied audit baseline; the separate operation receipt records what was actually done.

GENERATED BY AIKYA HARNESS
