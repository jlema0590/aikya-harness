# Python Project Structure Implementation Plan

> **For Aikya contributors:** Implement this plan task by task through the approved Aikya workflow. The user subsequently approved this structural implementation and the canonical location of plans, bugs and features. Preserve explicit user authorization and record observed results.

**Goal:** Adopt the user's core/tools/middleware/memory separation inside one installable Python package, retaining the existing command, installation, methodology, safety and documentation contracts.

**Architecture:** Place production Python under src/aikya/, grouped by actual responsibility. Keep Claude entry points as thin adapters, durable data outside importable code, and one authoritative asset registry for source, registered and initialized runtimes. Migrate incrementally with compatible root launchers until upgrades and source-checkout usage have passed acceptance.

**Tech Stack:** Python 3.10–3.13 standard library, unittest, pyproject.toml with setuptools as build backend, importlib.resources and optional claude-agent-sdk. Build tooling is a development dependency; ordinary registration/onboarding must not install dependencies.

**Spec:** The user's proposed directory tree; the source import inventory captured during repository cleanup; [cleanup evidence](../validation/REPOSITORY_CLEANUP.md); [installer modularization](2026-10-23-installer-modularization.md); [documentation path consolidation](2026-10-23-document-path-consolidation.md).

## Findings and decisions

- 51 root Python modules currently mix executable entry points, business rules, document rendering, installation, observation, catalogs and storage. Five additional runtime helpers live in template/scripts/harness/ and seven Claude hooks in template/.claude/hooks/.
- install.py has 1,309 physical lines. Its earlier extraction plan remains valid, but its proposed temporary aikya_installer package is folded into src/aikya/installation/. Do not build two installer implementations.
- docs_migration_hashes.py has 981 lines of compatibility data. Move the data into a packaged JSON resource with a small loader, preserving every trusted byte signature and the ASSETS mapping contract. Never delete a record merely because its source command was retired.
- Syntactic dependency components include runtime_metrics ↔ token_report and a larger group involving registration, methodology, execution state and documentation rendering. Some imports are deliberately local; these are refactoring seams, not evidence that current imports fail.
- There is no pyproject.toml today. Current registration copies Python scripts and declarative assets into global/project runtimes; initialization copies a separate managed project harness. Moving files alone would break these deployments.
- agent_runtime.py already implements a scoped optional Claude Agent SDK subprocess adapter. Do not introduce another Anthropic API client or a second agent loop.
- Memory is reviewed, scoped file-backed knowledge with TTL/provenance and a private store outside Git. There is no vector store. The proposal does not add semantic search or automatic consolidation.
- context_budget.py is a static instruction-size proxy and token_policy.py sets budgets. Neither is a conversation-history compression engine. Do not describe a new context_manager.py as an existing capability.

## Comparison with the user's example

| Proposed element | Adaptation for Aikya |
|---|---|
| .claude/config.json | Use the existing Claude Code .claude/settings.json, with rules, skills and agents. Local settings remain private. |
| core/client.py and agent_loop.py | Reuse the SDK runtime adapter, bounded loop, checkpoints and state; extract existing permission functions into core/permissions.py. No second provider client. |
| core/context_manager.py | Preserve actual routing, token policy and reports under routing/. Real history compression would require a separate feature proposal. |
| tools/registry.py, file_tools.py, bash_tools.py | Group the existing scaffold, infrastructure, check runner and skill-lint tools. Keep the existing catalog registries under catalogs/. SDK Read/Edit/Write permissions remain in core/permissions.py; no new general Bash tool. |
| middleware/hooks.py and logger.py | Group existing observers, lifecycle, hook configuration and status reporting. Claude executable hook adapters keep their host-required installed paths. Do not introduce a duplicate logging subsystem. |
| memory/persistent and vector_store | Package memory logic only. Store project evidence under aikya/docs/ and preserve the existing private store outside Git. No empty vector_store directory. |
| tests/ | Keep all fixtures and historical signatures; gradually organize tests by behavior, not a wholesale rename during the package move. |
| .env | Optional ignored local configuration; no real secrets in Git and no new dotenv loader requirement. Add .env.example only if a documented provider setup actually needs it. |
| main.py | Use python -m aikya and console entry points; preserve existing script launchers as compatibility adapters during migration. |
| pyproject.toml | Add package/build metadata, Python floor, optional SDK extra and explicit package/resource inclusion. VERSION remains the release version authority. |

The user's separation is retained. src/ isolates Python imports from repository documents and tests; it is a packaging choice layered over the proposed responsibilities.

## Implemented source tree

```text
aikya-harness/
├── .claude/                         # Repository-local Claude configuration
│   └── settings.json
├── src/
│   └── aikya/
│       ├── __init__.py
│       ├── __main__.py              # python -m aikya
│       ├── cli/                     # Command parsing and session entry points
│       ├── core/                    # Bounded loop, checkpoints, runtime and permissions
│       ├── tools/                   # Existing scaffold, infra, checks and skill lint
│       ├── middleware/              # Observation, lifecycle, hooks configuration, metrics
│       ├── memory/                  # Review, retrieval, storage policy and extraction logic
│       ├── installation/            # Profile validation, migration, copying and registration
│       ├── discovery/               # Bounded project scanning and profile construction
│       ├── workflows/               # ODD, SDD and methodology choices
│       ├── documentation/           # Layout, language, rendering and template composition
│       ├── catalogs/                # Engineering and external skill registries
│       ├── routing/                 # Model capabilities, budgets, usage and routing
│       ├── quality/                 # Existing source-quality diagnostics
│       ├── storage.py               # Shared durable atomic writer
│       └── resources/               # One canonical source of distributable assets
│           ├── project_template/    # CLAUDE.md, .claude rules/hooks and project assets
│           ├── commands/            # The existing 27 public Aikya skills
│           ├── engineering/         # Existing agents/skills, registry and metadata
│           ├── sdd_templates/
│           ├── claude_templates/
│           ├── documentation_templates/  # Pinned Milkeles catalog and license
│           └── migrations/          # Predecessor hooks, hashes and path manifests
├── aikya/
│   └── docs/                        # First-party docs, plans, research and validation
├── tests/                           # Existing tests and immutable historical fixtures
├── examples/                        # Profile inputs and historical generated gallery
├── scripts/ci/                      # CI/release utilities; no runtime business rules
├── docs/                            # Transitional guides/images; separate path plan governs
├── aikya_cli.py                     # Transitional compatible launcher
├── aikya_setup.py                   # Transitional compatible registration launcher
├── install.py                       # Transitional installer facade
├── pyproject.toml
├── VERSION
├── README.md
└── README.es.md
```

Directories shown as transitional are not permanent duplicate sources. Move each resource once its explicit source-to-destination manifest and all consumers pass. Required installed locations such as .claude/skills/, .claude/hooks/, .claude/rules/, aikya/scripts/harness/ and aikya/docs/ remain unchanged. Source resource names do not determine installed locations by string concatenation.

## Python module ownership

Names below are proposed destination modules. This table maps all 51 root modules once; additional permission extraction and the installer split are deliberate refactors of existing code.

| Current sources | Proposed owner |
|---|---|
| aikya_cli.py, aikya_session.py | cli/main.py, cli/session.py; __main__.py delegates to main |
| agent_loop.py, agent_loop_state.py, agent_runtime.py, execution_state.py | core/loop.py, core/checkpoints.py, core/runtime.py, core/state.py |
| tool_allowed and settings approval/fingerprint functions in agent_runtime.py and agent_loop.py | core/permissions.py; reused by loop and memory extraction |
| check_events.py, command_workflows.py, execution_config.py, execution_lifecycle.py, execution_observer.py, runtime_metrics.py, aikya_statusline.py, aikya_subagent_statusline.py | middleware/events.py, commands.py, configuration.py, lifecycle.py, observer.py, metrics.py, statusline.py, subagent_statusline.py |
| agent_memory.py, memory_store.py, agent_memory_extract.py | memory/knowledge.py, store.py, extraction.py |
| install.py | installation/context.py, profile.py, discovery.py, interview.py, checks.py, documents.py, io.py, migrations.py, assets.py, pipeline.py; root CLI/facade retained temporarily |
| aikya_setup.py, aikya_requirements.py | installation/registration.py, requirements.py |
| aikya_analyze.py, project_discovery.py, profile_builder.py, analysis_manifest.py, aikya_layout.py, infrastructure_profile.py | discovery/analyze.py, scanner.py, profiles.py, manifest.py, layout.py, infrastructure.py |
| methodology.py, odd_engine.py | workflows/methodology.py, odd.py |
| sdd_engine.py, sdd_assets.py, sdd_localization.py, sdd_templates.py | workflows/sdd/engine.py, assets.py, localization.py, templates.py |
| doc_bootstrap.py, docs_language.py, docs_layout.py, docs_templates_en.py, docs_templates_es.py, docs_migration_hashes.py, claude_templates.py, documentation_templates.py, documentation_workflows.py | documentation/bootstrap.py, language.py, layout.py, pages_en.py, pages_es.py, migration_hashes.py, claude.py, templates.py, composition.py |
| engineering_catalog.py, external_skills.py, skills_registry.py | catalogs/engineering.py, external.py, skills.py |
| aikya_router.py, model_capabilities.py, token_policy.py, token_report.py | routing/router.py, models.py, policy.py, usage.py |
| context_budget.py | scripts/ci/context_budget.py, with a compatible root launcher until CI and imports are updated |
| code_quality.py, durable_io.py | quality/source.py, storage.py |
| template/scripts/harness/{scaffold,infrastructure,run_checks,skills_lint}.py | tools/scaffold.py, infrastructure.py, checks.py, skills_lint.py, retaining installed CLI adapters |
| template/scripts/harness/docs_guard.py | documentation/guard.py, retaining installed CLI adapter |

Repository execution config is distinct from the distributable project template. Existing .claude hook scripts become thin adapters only after their import contracts are characterized. Existing functional SKILL.md/rule paths remain available during transition; pinned content and historical fixtures are not rewritten to fit package names.

## Storage outside the Python package

| Data | Preserved destination |
|---|---|
| Living docs, audit receipts, ODD features, SDD dossiers, loop summaries | aikya/docs/ at their current canonical paths |
| Project configuration and managed profiles | Current harness.json, .harness/ and .aikya/ contracts |
| Project registration runtime | .aikya/runtime/ |
| Global registration runtime | Current ~/.claude/aikya-harnes/ contract, including its historical spelling |
| Initialized project runtime | aikya/scripts/harness/ |
| Private memory | Existing memory_store-resolved directory outside the repository; preserve POSIX modes |
| Disposable visibility/cache state | Existing external cache contract; not importable package resources |

## Global constraints

- Python 3.10–3.13; preserve 27 public commands, exit codes, explicit approvals and English source/instructions with en/es living documents.
- Core remains standard-library-only. The SDK is optional and imported lazily. No network/model call, dependency install, deployment, push or package publication is implicit in this plan.
- Preserve init/analyze, ODD/SDD, all three project types, global/project scopes, dry-run behavior and custom-file ownership.
- Preserve legacy root module APIs and HERE/TEMPLATE overrides during the compatibility window; do not replace test monkeypatch contracts accidentally with frozen imported aliases.
- Preserve all pinned catalog checksums/licenses, migration hashes, historical fixtures and gallery outputs. Exclude the historical gallery from runtime distribution, as implemented by the cleanup.
- Do not put credentials, private memory or runtime-generated state under src/. Do not create empty feature folders for unimplemented capabilities.
- No source file over 1,000 physical lines; review functions over 100 lines by cohesion. This maintainability rule does not itself prove security.
- Every new authored Markdown uses the canonical writer and exact Aikya footer; refresh indice.md.

## Review focus

- A working checkout can conceal missing installed assets: exercise source launchers, wheel installation, both registration scopes and initialized projects from an unrelated cwd without PYTHONPATH.
- A facade importing a package must not replace an upgraded runtime whose package dependencies were preserved as custom old files; preflight the complete managed upgrade before writing coupled imports.
- Import direction can change when lazy functions move: test cold imports in independent processes, and remove dependency cycles through narrow shared policy/state interfaces rather than sys.path patches in business modules.
- A renamed module path can affect worker subprocesses, hook commands, migration hashes and saved configuration; characterize these consumers before moving their implementation.
- Source templates and project-owned content have different ownership. Resource migration cannot move user docs or silently modify private state, custom settings, catalog pins or unapproved SDD records.

### Task 1: Freeze observable contracts and centralize asset inventory

**Files:** Add tests/test_package_contracts.py; extend tests/test_runtime_payload.py, tests/test_agent_loop_installation.py and tests/test_installer.py; introduce runtime_assets.py temporarily, later owned by installation/assets.py.

**Interfaces:** AssetRecord(source: Path, destination: Path, kind: str); runtime_assets(source_root: Path, target_kind: str) -> tuple[AssetRecord, ...], with target_kind one of registration or initialized. Existing CORE_FILES becomes a compatibility view rather than an independently maintained list.

- [x] Record the current 27 command names, entry-point argv/exit codes, runtime-relative destinations and checksums; capture dry-run/repeat-install/custom-file behavior as subprocess outcomes, not assertions on source text.
- [x] Add a failing test requiring one inventory to resolve and copy an isolated staged package plus all selected catalogs for both target kinds. Include the gallery omission and guide link transformation.
- [x] Implement the shared inventory and deterministic destination collision check. Keep distinct registration/initialized payload selection; do not blindly distribute every example to both.
- [x] Run installer, runtime payload and migration tests; require passing output before adding package imports.

### Task 2: Add pyproject and package/resource resolution

**Files:** Create pyproject.toml, src/aikya/__init__.py, src/aikya/__main__.py, src/aikya/resource_paths.py, and tests/test_package_distribution.py. Update VERSION readers and build manifests as needed.

**Interfaces:** resource_path(name: str) -> Path resolves registered logical assets through importlib.resources and an explicit source fallback; cli.main(argv: list[str] | None = None) -> int; metadata version equals VERSION. Console scripts: aikya and aikya-setup, preserving script entry points.

- [x] Add failing acceptance for an isolated wheel installation that invokes --help outside the checkout and resolves a template/license without importing from the repository. Include an SDK-absent environment.
- [x] Configure explicit src package discovery, Python >=3.10, dynamic VERSION metadata and the optional agent-loop extra pinned to the existing SDK requirement. Keep existing requirements-agent-loop.txt compatible until its consumers can derive it from the same declaration.
- [x] Implement the package entry points and resource resolver. Stage resources from one authoritative source per asset; never maintain edited copies in both old and new trees.
- [x] Build wheel and sdist in a disposable build environment with reviewed build tools; install the wheel without optional dependencies, inspect contents and run the subprocess acceptance. Do not publish.

### Task 3: Extract the installer into installation/

**Files:** Create the installation modules listed above; keep install.py as wrappers; update registration, CLI, profile building and corresponding tests.

**Interfaces:** Follow InstallerContext(source_root: Path, template_root: Path) and the existing public signatures in the earlier installer plan. Its target package is replaced by src/aikya/installation/; its safety and acceptance requirements remain binding.

- [x] Characterize profile validation, discovery, checks, rendering and write/migration behavior before each extraction. Verify facade monkeypatches still influence source roots as before.
- [x] Extract pure functions first, then IO/migrations, then pipeline helpers; split the 344-line install coordinator along preflight, assets, configuration, documentation and infrastructure responsibilities.
- [x] Add a failing upgrade case where a customized coupled dependency prevents a new facade/package from becoming active. Apply the smallest preflight change that preserves the old runtime and reports the conflict.
- [x] Run full installer/locale/methodology compatibility and cold entry-point tests; require install.py below 1,000 lines without hiding its former body in another oversized file.

### Task 4: Move core, memory and middleware with explicit dependency direction

**Files:** Create the mapped core/, memory/, middleware/ and routing/ modules; add tests/test_package_imports.py and extend existing loop, memory, recovery, metrics and routing tests.

**Interfaces:** Preserve ProcessRuntime.execute(request, event_callback), tool_allowed(request, tool, tool_input), settings fingerprint/approval semantics, current state schemas and memory proposal/review/retrieval signatures. Policy modules must not import the CLI, registration or orchestration modules.

- [x] Add cold-import and worker-subprocess tests, bounded loop interruption/resume tests and memory extraction tests using the existing controlled fake provider. Keep authenticated SDK acceptance opt-in in the separate environment chosen by the user.
- [x] Extract existing permission functions into core/permissions.py so memory extraction no longer imports loop orchestration solely to validate settings.
- [x] Break the metrics/usage cycle by keeping normalized observed fields and pure aggregation in middleware/metrics.py; orchestration in routing/usage.py may consume them, not the reverse.
- [x] Move implementations and update owned imports to package-qualified paths. Compatibility facades re-export only; no new SDK/tool implementation, state schema, quota inference or vector dependency.
- [x] Run loop adversarial/recovery, memory lifecycle/extraction, observability and command routing tests with the optional SDK absent.

### Task 5: Move methodology, documentation, discovery, catalogs and tools

**Files:** Create the remaining mapped packages; update tests by behavior and package-qualified imports, preserving tests/fixtures/ byte contents.

**Interfaces:** Retain current write_document, canonical/index operations, catalog selection, init/analyze result structures, ODD and SDD approval/task contracts, and actual tool CLIs. Reuse one storage.atomic_write implementation.

- [x] Add a failing installed-package scenario for ODD feature preparation and the SDD spec/plan/tasks lifecycle, including denial without approvals and exact canonical dossier paths.
- [x] Separate methodology normalization/command metadata from observation and registration imports. Pass event sinks into workflows; document writers must not depend on workflow orchestration.
- [x] Move English/Spanish renderers and convert migration hash data to a checksummed JSON resource with a small ASSETS-compatible loader. Verify all five retired-command records and predecessor hooks.
- [x] Move the four existing tools and document guard implementations; keep thin CLI adapters at paths embedded in user settings. Preserve standalone CLI behavior and no-source-change guard behavior unless the separate path-policy change is explicitly included and tested.
- [x] Run catalog checksums, generated-document, SDD/ODD, discovery, tools and architecture-language tests. Retain module_root and resolve_actor_model as compatibility helpers unless a separately characterized removal is approved.

### Task 6: Migrate declarative resources and installed runtime upgrades

**Files:** Move source assets through an explicit manifest into src/aikya/resources/; update installation/assets.py, template adapters, build inclusion, CI validators and tests/test_package_distribution.py.

**Interfaces:** Resolve logical asset names independent of source paths. Public installed commands, hooks, rules, catalogs and harness locations remain unchanged. Backup/retirement compares actual predecessor bytes and supports interrupted retries.

- [x] Add failing cases for fresh global/project/init runtimes, actual pre-migration upgrades, custom asset conflicts, symlinks, backup collisions and interrupted copying. Verify missing package modules cannot leave active half-upgraded launchers.
- [x] Move each source tree once, preserving pinned catalog bytes, license, manifest and historical signature data. Keep compatibility aliases only where a tested consumer requires them; no symlink-dependent distribution.
- [x] Teach existing root launchers and installed adapters to use one bounded bootstrap resolver for the bundled src/ package. Normal installed console scripts use standard imports. Business modules must not alter sys.path.
- [x] Run all 48 onboarding combinations from an unrelated cwd with PYTHONPATH empty and optional SDK absent; repeat direct initialized-runtime tools and source-checkout launchers.
- [x] Build and inspect wheel/sdist; verify gallery omission, required resource inclusion and no credentials, caches, tests or local evidence accidentally entering the wheel.

### Task 7: Update contributors, CI and the independent documentation path plan

**Files:** Update README.md/README.es.md, CONTRIBUTING.md, CI workflows, source-quality discovery and the canonical documentation index. Integrate the existing document-path plan without relocating project-owned docs.

**Interfaces:** Supported developer commands include an explicit editable install and the existing unittest discovery. Root compatibility launchers remain documented until a separately reviewed deprecation window ends.

- [x] Make CI build/install a wheel and run subprocess acceptance outside the source checkout as well as normal regression discovery on Python 3.10–3.13.
- [x] Make syntax/quality checks inspect src/ and adapters, eliminating hardcoded parallel source inventories. Keep checksums for historical data and tests scoped appropriately.
- [x] Update command examples, resource provenance and the project tree. Keep all generated docs under aikya/docs/; implement the separate path guard before claiming it prevents misplaced model-authored reports.
- [x] Verify all first-party local links, image paths, exact index contents and package/source import isolation. Preserve third-party illustrative links and labelled snapshot provenance.

### Task 8: Final acceptance and staged delivery

**Files:** Write aikya/docs/validation/PYTHON_PROJECT_STRUCTURE.md and its machine-readable migration receipt; update this plan and indice.md.

- [x] Run full regression discovery on all four supported Python versions, 14 example profiles, 48 onboarding combinations, catalog/agent checks, source quality and isolated wheel/sdist acceptance.
- [x] Verify actual baseline upgrades in both scopes, custom-file preservation, interrupted retries and stable ODD/SDD IDs/approvals. Show old launchers and hooks still work after a cold restart.
- [x] Record before/after module sizes, destination manifests, package imports and resource sizes. Security checks and live provider acceptance are separate evidence, not conclusions inferred from directory names.
- [x] Review each incremental diff. Commit/push or release only under the applicable user authorization; package publication and real provider testing are not implied by this plan.

## Delivery sequence and effort

1. Contracts, inventory and package scaffolding: 1–2 working days.
2. Installer extraction and compatibility facade: 1–2 days.
3. Core/memory/middleware and remaining domain modules: 2–3 days.
4. Resource/runtime upgrades, packaging, CI and docs: 2–3 days.

Estimate: 6–10 engineering working days for one contributor, including local regression work and migration repairs. This is a planning estimate, not measured execution time or an API/cloud cost quote. Keep each increment independently runnable; do not reset Aikya or merge a wholesale file move before its corresponding runtime acceptance. The currently executed cleanup is a separate completed increment and does not establish package-migration acceptance.

## Primary references

- [PyPA: src versus flat layouts](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/) explains import isolation and the installation step required by src layout.
- [PyPA: writing pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) defines project/build metadata and optional dependencies.
- [Claude Code settings](https://code.claude.com/docs/en/settings) documents settings.json scopes. This proposal preserves the host's actual configuration locations.

## Execution result

Implemented locally; see [validation](../validation/PYTHON_PROJECT_STRUCTURE.md)
and [machine-readable results](../validation/PYTHON_PROJECT_STRUCTURE_RESULTS.json).
Contract coverage lives in tests/test_package_contracts.py,
tests/test_package_runtime_transaction.py, tests/test_document_path_policy.py,
tests/test_discovery_resources.py, the existing owning suites and
scripts/ci/package_smoke.py; planned extra test filenames were consolidated into
these owners rather than duplicated. Cold import orders were also exercised in
independent installed-wheel processes. The static context proxy remains in
quality/context_budget.py with its root and CI adapters. Broader historical guide
relocation remains the separate document-path plan; its generated-record guard
is implemented here. No commit/push/publication or live provider call occurred.

GENERATED BY AIKYA HARNESS
