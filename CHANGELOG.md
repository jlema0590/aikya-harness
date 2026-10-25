# Changelog

## Unreleased

## v7.0.1 — 2026-10-25

- Verify the PowerShell bootstrap checksum through the already-selected Python interpreter so installation does not depend on `Get-FileHash` module availability. Stream checksum code through stdin to preserve quoting in Windows PowerShell 5.1 and retain SHA-256 failure blocking; cover legacy argument passing, unavailable cmdlets and corrupt bootstrap payloads.
- Fix default SDK worker startup for the task loop and model-assisted memory extraction after root adapter removal. Launch the canonical package module with the current interpreter and a pinned, isolated import root; preserve copied global/project/initialized runtimes and explicit custom worker commands.
- Add behavioral source, isolated-wheel and copied-runtime worker startup/protocol checks with an offline SDK stand-in and hostile working-directory/PYTHONPATH shadows. Clarify same-interpreter Aikya/SDK setup and explicit memory recall configuration; preserve loop opt-in, approvals and execution limits.
- Select the latest published stable GitHub release by default for clean installation and updates on Linux, macOS and Windows. Resolve the release once before downloading version-pinned, SHA-256-verified assets; reject malformed metadata, drafts, prereleases and failed lookups without provisioning or silently falling back.
- Simplify both README quick starts with permanent latest-release download links. Keep optional numeric version selection (`--version` / PowerShell `-Version`), explicit registration scopes and deterministic offline installation using the entry script's release version.
- Add release-selection and executable entry-script regressions to native installer CI; retain standalone bootstrap integrity and existing installation ownership/recovery controls.
- Generate installed compatibility adapters from one validated mapping/template and remove 51 obsolete source-root launchers, the root bootstrap and five prebuilt helper copies. Keep installed filenames and source `setup.py`; repository consumers use canonical package APIs and commands.
- Add a standard-library clean installer with Linux/macOS and Windows entry scripts, version-pinned bootstrap integrity, isolated per-user environments, SHA-256 release verification, explicit global/project registration, offline installation, diagnostic state, serialized updates and ownership-aware uninstall.
- Retain interpreters referenced by initialized projects and record generated settings deltas without copying unrelated user credentials. Preserve edited files, custom hooks and project documentation during recovery/removal.
- Render managed startup, observer, project hooks and statusline invocations with the chosen Python and platform quoting. Keep ODD/SDD choices and the 27 slash commands intact.
- Extend release artifacts with wheel/sdist, standalone bootstrap and platform scripts; verify immutable asset recovery and gate publication on native and Linux distribution installer jobs. Update English/Spanish installation and contributor instructions. Scripts become downloadable when v7.0.1 is published.

## v7.0.0 — 2026-10-24

### Upgrade notes

- This major release renames public commands, relocates the offline template library and restructures Python source/resources. Use the canonical command names and documentation paths below. Existing root Python adapters remain compatible; known managed assets upgrade with backups, while customized coupled runtimes require review before migration.

### Methodologies and commands

- Integrate Spec-Driven Development for development, infrastructure and DevOps, with a portable lifecycle engine, localized living documents and versioned requirement/task/evidence records. The initial SDD integration was recorded on 2026-10-21; this entry includes the subsequent changes delivered on this branch.
- Require an explicit ODD/SDD choice during `/aikya-init` and `/aikya-analyze`. Preserve confirmed choices, normalize legacy `standard` inputs to `odd`, and retain managed profile/answers backups and existing SDD approvals.
- Add proportional ODD worklists, acceptance criteria, task dependencies, recorded evidence, versioned continuity and reviewed invalidation of stale outcomes.
- Keep `/aikya-init` for new projects and `/aikya-analyze` for approved existing-project adoption, with deterministic discovery, scoped previews and preservation of custom project files, infrastructure, CI/CD and ignore rules.
- Add six SDD commands: `/aikya-specify`, `/aikya-clarify`, `/aikya-plan`, `/aikya-tasks`, `/aikya-implement` and `/aikya-sdd-status`. Bind implementation/generation to the active approved specification and task; distinguish structural lint from recorded completion readiness.
- Rename `/aikya-project-init` to `/aikya-project`, `/aikya-infra-project` to `/aikya-infra`, `/aikya-architecture-review` to `/aikya-arc-review` and `/aikya-documentation-sync` to `/aikya-docs-sync`. Consolidate external skill installation in `/aikya-install-skill`.
- Register 27 canonical public commands. Retire verified old wrappers with backups, preserve customized commands for manual review and prevent compatibility aliases from being regenerated.

### Execution, memory and safety

- Add an explicit optional agent loop for feature, bugfix and implement, using a separately installed Claude Agent SDK, scoped tools, ODD/SDD gates, local process checks and an independent read-only runtime review contract.
- Persist execution limits, usage, effect intents and recoverable checkpoints. Stop on uncertain effects, stale candidates, changed approvals or unknown cost data rather than silently retrying.
- Add reviewed typed project memories with source fingerprints, expiry and globally budgeted lexical recall; share permission controls with the existing runtime.
- Add six English execution phases: Explore, Plan, Implement, Validate, Security and Review. Keep status separate and correlate private concurrent session/run snapshots, local CLI/check observations and the protocol used by all public commands.
- Register execution hooks and status views without replacing custom commands. Display observed models, context, optional provider 5-hour/7-day windows and explicitly cached session aggregates; show unavailable data as N/D.
- Preserve explicit approvals, source-size diagnostics, evidence-path validation and dependency checks as separate controls. Recorded evidence, a phase transition or a planning document does not independently certify security, passing tests or deployment readiness.

### Python structure, packaging and upgrades

- Package implementations under `src/aikya/`, grouped into core, tools, middleware, memory, installation, discovery, workflows, documentation, catalogs, routing and quality. Keep existing root scripts/imports as compatibility adapters.
- Add `pyproject.toml`, Python 3.10+ metadata, console entry points, wheel/source-distribution packaging and an optional agent-loop SDK extra; the ordinary runtime has no new mandatory dependencies.
- Split the oversized installer into focused contextual preflight, asset, configuration, migration and documentation stages while preserving its public callable contracts.
- Use one runtime asset inventory for global/project registration and initialized ODD/SDD projects. Preserve predecessor hashes and custom files; reject coupled customizations, detect stale previews, retain backups and restore previous bytes after tested copy failures.
- Move canonical source assets under package resources and load migration hashes from a checksummed JSON resource. Retain immutable predecessor signatures and retired-command records needed for safe upgrades.
- Split the 658-line SDD engine into a 282-line transition facade plus contracts, validation, state, rendering and CLI modules. Preserve its 34 exported function/class names and 78 pre-refactor lifecycle/document fingerprints; the largest implementation module is now 404 lines.
- Close the bounded Terraform discovery file read to eliminate its ResourceWarning. Correct the inherited symbolic-link regression test and normalize migrated Python whitespace without changing function semantics.

### Documentation, templates and cleanup

- Keep new plans, bugs, features, research and validation records under `aikya/docs/`. Normalize plan inputs to `plan/`, lowercase feature folders under `features/`, architecture to `architecture/architecture-overview.md`, test plans to `plan/testing.md` and agent/token policies to `tools/`.
- Consolidate initialization and toolchain guidance in `overview.md`. Generate an exact `indice.md` inventory, append actual bugs to `bugs/bugs.md` and omit unsupported or empty documents, including unused SDD clarification/verification reports.
- Apply the terminal `GENERATED BY AIKYA HARNESS` footer to generated Markdown, including analysis reports and first-party instruction assets. Retain English engineering instructions, configurable English/Spanish living documentation and the bilingual README.
- Validate generated-record locations even for documentation-only changes. Preserve root project contracts, project-owned custom documents and verified functional/runtime reference assets in their required installation paths.
- Bundle 120 offline reference templates and supporting guides, with nine SDD role adaptations and contextual composition by command, methodology and project type. Retain Aikya acceptance IDs, approvals and traceability; create documents only from reviewed supplied facts.
- Rename the reference-library directory to `aikya-template/docs` and update active template references. Preserve original copyright, MIT license, upstream provenance and historical evidence; back up and retire verified old catalogs, block customized catalogs and restore retired files after a tested write failure.
- Create `tools/skill-comparison.md` only for explicitly requested external skill installation attempts; do not fabricate it after a rejected installation.
- Preserve the checksummed historical generated-example gallery in source while excluding it from registered runtimes and distributions. Archive reviewed historical plans, validation records and media under `aikya/docs/`; remove the duplicate root image and update navigation.
- Update the English/Spanish README, contributor instructions, CI source/resource paths and isolated package acceptance checks.

### Validation and research

- Record 496 passing regression tests on each Python version 3.10, 3.11, 3.12 and 3.13 after the SDD split, including adversarial loop/memory cases, approval scope, malformed state, recovery, migration, runtime isolation, locale and document-path checks.
- Exercise executable support for all 27 public commands through 49 local process checks and inventory generated Markdown paths. Cover missing approvals, unsafe paths, duplicate bug IDs, failing/unconfigured checks and incomplete SDD workflows.
- Validate 48 onboarding combinations across two scopes, three project types, two methodologies, two locales and init/analyze; validate all 14 versioned example profiles and bundled agent/skill/command metadata.
- Verify the offline template hashes, eight isolated wheel onboarding cases, 96 importable modules in two independent orders, and upgrades from the published predecessor in both registration scopes and initialized ODD/SDD projects.
- Record detailed results and the corrected historical/current size measurements in `aikya/docs/validation/COMMAND_ACCEPTANCE.md` and `aikya/docs/validation/SDD_MODULARIZATION.md`. Live authenticated-model execution remains assigned to the other environment; local results do not claim a live external-skill installation or infrastructure deployment.
- Document source-pinned OpenHarness and Gentle Shell comparisons. The Gentle Shell adoption plan for risk-based review, candidate receipts, state views and optional integrations remains pending; comparisons do not install or execute those external runtimes.

## v6.1.1 — 2026-10-21

- Integrated opt-in Spec-Driven Development for development, infrastructure and DevOps while retaining the standard workflow and new/existing onboarding separation.
- Added six SDD commands, a portable specification lifecycle engine and localized living documentation with versioned state and requirement/task/evidence records.
- Bound generation to the active approved specification and task, revalidated persisted references and dependencies, and separated structural lint from recorded completion readiness.
- Added reviewed adoption through --methodology sdd, conservative known-asset upgrades with backups, custom-asset blocking, and global/project runtime support.
- Preserved current analysis, model and token commands; updated the bilingual README, workflow documentation and catalog inventory for 27 public commands.
- Added regression coverage for approval scope, malformed state, migration, runtime isolation, documentation languages and quality-manifest safety; corrected the inherited symbolic-link test.

## v6.0.1 — 2026-10-21

- Removed README links to deleted onboarding and model-policy documents.
- Replaced the hard-coded release-version test with SemVer and matching release-note validation.
- Restructured the English README and added a Spanish README with language navigation.
- Simplified installation instructions to use the default branch and clarified global/project registration scope and supported CLI syntax.
- Separated new-project onboarding with /aikya-init from existing-repository adoption with /aikya-analyze, including documented analysis options.
- Added verified component, recursion and documentation traceability diagrams, with conceptual workflows explicitly labeled.
- Promoted living documentation, audit evidence and Git history to a dedicated section; clarified optional external skills and the Aikya safety approach.

## v6.0.0 — Token Efficiency & Observability (in development)

- Conservative validated per-role model policy: Opus for planning/orchestration, inherit for routine work, and user-approved optional Haiku.
- /aikya-models and /aikya-tokens for explicit selection and local usage reports, without changing global configuration.
- v5.9.1 profile compatibility, customized-asset preservation and regression coverage.
- Context hygiene rules for CLI output, diffs and logs.
- Separate public commands: /aikya-init for new projects and /aikya-analyze for interview-free existing-project adoption.
- Deterministic multistack discovery, compatible profile projection, reviewable file plan, ownership hashes and approved read-only analysis.
- Restrictive adopt_existing policy preserves infrastructure, scripts, CI/CD and .gitignore during onboarding; idempotence and migration tests.
- Optional Haiku 5.5 for bounded extraction, classification, routing and documentation drafts; Haiku 4.5 policy compatibility.
- Deterministic hybrid router with advisory suggestions and Planner/Orchestrator only for genuinely complex tasks.
- Clearly labeled Haiku 5.5 estimated API costs, without inventing measured token savings.

## v5.9.1 — GitHub Actions fixes and automation

- Automated tags and GitHub Releases after merging an approved version into main.
- SemVer VERSION contract, auditable release notes and tag-to-merge-commit validation.
- Separate tests, reproducible ZIP packaging, SHA-256 checksums and idempotent publishing.
- Version validation for pull requests targeting main, with controlled preparation on develop.
- Expanded CI and regression tests for publishing workflows and release scripts.
- Catalog and profile workflows remain read-only; no remote deployments.

## v5.9.0 — 2026-10-19

- Fixed /aikya-infra-project validate with Helm on symlinked project roots (for example macOS /var pointing to /private/var). Out-of-project linked charts remain rejected as NOT_CONFIGURED.
- Reorganized README with quick start, command reference, technical catalog and security.
- Merged INSTALL_FROM_CLAUDE.md into README and moved audits into docs/audits/.
- Removed obsolete repository-local command copies and unused examples/existing-api.json.

## v5.8.0 — 2026-10-18

- Introduced project_type selection for development, infrastructure and devops; originally also supported a new/existing interview choice.
- Infrastructure-only support without application SDKs, using Terraform/OpenTofu/Ansible independently or together.
- DevOps-only workflows with Docker/Compose from source or image, Kubernetes YAML, Helm and Kustomize.
- Existing Helm chart or image does not require local Docker; historical profiles without project_type remain development.
- Infrastructure quality gates and documentation without invented applications or tests; specialist selection by stack.
- Read-only plans, approved artifact generation and local validation; no automatic deployment.
- New example profiles and regressions for all three project types.

## v5.7.0 — 2026-10-18

- Corrected Node version parsing for v25.9.0 and other v-prefixed versions.
- Safe runtime requirements updates with managed-file migration and preservation of v5.6 backups and custom content.
- Optional infrastructure profile: provider, Terraform/OpenTofu, Ansible, Docker/Compose, Kubernetes, environments, image and port.
- Four infrastructure agents and three engineering skills added, activated by explicit selection.
- Infrastructure generator with plan, generate --approved and validate modes and no automatic deployment.
- Dockerfile derived from actual application code; Kubernetes requires a versioned image and confirmed port.
- Living docs, quality checks and examples for Terraform/Helm and Ansible/Kustomize.

## v5.6.0 — 2026-10-18

- Explicit monorepo/singlerepo selection during technical intake and in JSON answers.
- Monorepos alone create apps/, packages/ and contracts/; singlerepos stage a single root application.
- Consolidated Aikya documentation, tests and scripts under aikya/docs/, aikya/test/ and aikya/scripts/.
- Global welcome in new and existing projects without duplicate local hooks.
- Conservative historical-document migration and quality-gate updates.

## v5.5.0 — 2026-10-18

- Integrated 11 additional technical agents and 11 Agent Skills for languages and architectural patterns.
- At this historical version, the catalog held 23 agents and 26 skills, selected by backend/frontend/mobile and architecture.
- Added Python and Angular to the technical interview and stack detection; framework scaffolding remained guided.
- Added seven stack-specific examples with answers.json and Claude Code usage guides.
- Expanded documented responsibilities, selective activation and traceability.

## v5.4.0 — 2026-10-18 — Aikya command organization

- Renamed bootstrap_skills/ to aikya-skills/ without changing public /aikya-* command identities.
- Updated global/project bootstrap, installer and documentation paths.
- Conservatively migrated known managed legacy runtimes; customized files were preserved.
- Added fresh-install, scope-upgrade and unrelated-content protection tests.

## v5.2.0 — 2026-10-18

- Renamed /aikya-infra-project, /aikya-skills-status, /aikya-skills-plan and /aikya-skills-install.
- Allowed additional GitHub skills with source, path, name and optional commit verification, avoiding overwrite.
- Added the project skills availability inventory in aikya/docs/skills.md.
- Conservatively migrated renamed commands while preserving customizations.

## v5.1.0 — 2026-10-18 — Claude-native commands

- Added /aikya-scaffold, /aikya-skills-status, /aikya-quality, /aikya-docs and /aikya-tests alongside development commands.
- Global/project bootstrap exposed 16 conversational Aikya skills with approval for external actions and protection of user skills.
- README described installation and use from Claude Code without mandatory manual scripts.
- Preserved internal scripts and living documentation, with SDK checks before scaffolding.

## v5.0.0 — 2026-10-18

- Claude Code conversational global/project install and /aikya-init, /aikya-answers, /aikya-doctor.
- Added Aikya command prefixes without breaking previous aliases.
- Non-destructive JDK, .NET SDK, Node, web package manager and mobile SDK checks.
- Non-intrusive SessionStart reminders in uninitialized directories without automatic downloads.
- Reused JSON profiles and preserved user projects during global onboarding.
- Added bootstrap and toolchain regression tests.

## v4.1.0 — 2026-10-18

- Claude Code session welcome with local name, repository and Aikya URL.
- Non-intrusive SessionStart hook with visible message, no network or compaction notifications.
- Added --display-name and local welcome_name; identity state ignored by Git.
- Expanded command/skill examples and welcome preview in README.
- Supported welcome hooks for Aikya itself and installed projects.

## v4.0.0 — 2026-10-18

- Preserved v3 interview/bootstrap for Java, .NET, Node, Next, Vue, React, Android, iOS and cross-platform.
- User-approved Ponytail, Graphify CLI (without MCP) and conditional UI UX Pro Max integrations.
- Offline SessionStart skill checks, external skill plan/install/status management.
- Basic Agent Skills validation and progressive context-loading policies.
- Conditional design-system docs and UI change-validation gates.
- Backed up original v3 managed files; preserved customized files.
- Local suite originally contained 32 tests; networked team validation remained necessary.

## v3.0.0 — 2026-10-18

- Engineering bootstrap, technical interview, assisted scaffolding, infrastructure and
  living documentation with traceability hooks.

GENERATED BY AIKYA HARNESS
