# Aikya Harness

[English](README.md) | [Español](README.es.md)

**One engineering workflow. Multiple AI agents. Consistent quality.**

![Aikya Harness](docs/images/aikya-harness.png)

Aikya Harness is a Claude Code engineering environment combining safe project
onboarding, application scaffolding, infrastructure-as-code planning, curated
subagents, Agent Skills, quality gates, observability and living documentation.

Supported stacks include Java, .NET, Node.js, Next.js and Python backends;
React, Vue, Angular and Astro frontends; Android, iOS, Flutter and React Native
applications; and standalone infrastructure and DevOps repositories.

**All interactions are initiated through Claude Code.** The harness maintains
its supporting Python scripts internally and requests approval before writes,
third-party downloads, SDK installation or external operations.

## 1. Quick start

Install the **latest published stable release** without cloning the repository or entering a version number. These installers become available when v7.0.1 is published.

**Linux and macOS** — Python 3.10–3.13 with `venv`/pip is required:

```sh
curl --fail --location --proto '=https' --proto-redir '=https' \
  "https://github.com/jlema0590/aikya-harness/releases/latest/download/install.sh" \
  -o install-aikya.sh
sh ./install-aikya.sh --scope global
# Project registration: sh ./install-aikya.sh --scope project --target /absolute/path/to/project
```

**Windows** — PowerShell 5.1+ or 7 and Python 3.10–3.13 with `venv`/pip:

```powershell
Invoke-WebRequest -Uri 'https://github.com/jlema0590/aikya-harness/releases/latest/download/install.ps1' -OutFile install-aikya.ps1
.\install-aikya.ps1 -Scope global
# Project registration: .\install-aikya.ps1 -Scope project -Target 'C:\work\project'
```

Download and inspect the script before running it. Each online run selects GitHub's latest published stable release, including when reusing a previously downloaded script. Drafts and prereleases are excluded. It verifies its pinned bootstrap and the selected release wheel, creates an isolated application environment and prints the command directory to add to your user PATH. No Git clone, administrator privileges or environment activation is required. Missing Python prerequisites are reported; the installer does not install Python or change system package managers or execution policy.

| Scope | Registration | When to choose it |
|---|---|---|
| `global` | Current user's Claude configuration and shared runtime. | Make commands available across your projects. |
| `project` | Explicit target's Claude configuration and `.aikya/runtime/`. | Limit registration to one repository. |

Both scopes store the application per user. Scope is separate from `/aikya-analyze --scope <relative-path>`, which selects a directory to inspect. Installation does not initialize a project or choose ODD/SDD.

Use `aikya-manage update --scope global` to update to the latest stable release, `aikya-manage doctor` for local installation state, and `aikya-manage uninstall --scope global` to remove unchanged owned registration assets. Add `--target` with project scope. To select a specific release, pass `--version X.Y.Z` to the shell installer or manager, or `-Version X.Y.Z` to the Windows installer. A failed latest-release lookup stops installation without falling back to an older version.

For offline installation, download one release's entry script, wheel, `SHA256SUMS` and bootstrap, then pass `--offline-dir` (`-OfflineDir` on Windows). The entry script uses its own release version offline; direct bootstrap/manager calls also require `--version X.Y.Z`. Edited assets are preserved; environments referenced by initialized projects are retained. On Windows, use the standalone bootstrap to finish cleanup of an in-use management executable.

**Contributors:** from a source checkout, create a virtual environment, install `build`, `setuptools>=77` and `wheel`, then run `python -m pip install --no-build-isolation --no-deps -e .`. Use `aikya`, `aikya-setup` or `python -m aikya`; source-root scripts such as `python install.py` are retired. This contributor path is separate from the release installation above.

Start a new Claude Code session, then choose the onboarding command below. Native host-session compatibility and authenticated model execution are separate from installer smoke tests.

## 2. Onboarding

| Starting point | Command | How it works |
|---|---|---|
| **New project** | **`/aikya-init`** | Interview, technical decisions and approved initialization. |
| **Existing repository** | **`/aikya-analyze`** | Discover the stack from repository evidence and preview safe adoption. |

### New projects → `/aikya-init`

```text
/aikya-init
```

Use an empty project directory. The command always selects `mode=new` and guides
you through the required choices. If existing code is detected, use `/aikya-analyze`.

| Project type | Choices covered during onboarding |
|---|---|
| `development` | Stack, repository layout, architecture, testing and optional infrastructure/platform support. |
| `infrastructure` | Terraform/OpenTofu, Ansible, provider, environments and constraints. |
| `devops` | Docker, image/source, existing Helm chart, Kubernetes and YAML/Kustomize. |

The interview also asks for the living documentation language. Review the file
plan before approving changes. Then check prerequisites and plan scaffolding:

```text
/aikya-doctor
/aikya-scaffold plan
```

For infrastructure or DevOps generation, start with `/aikya-infra plan`.
Generators, downloads and external operations require their applicable approvals.

### Existing projects → `/aikya-analyze`

Start with a read-only preview:

```text
/aikya-analyze --dry-run --methodology odd --docs-lang en
```

Aikya detects the existing stack and architecture without a technical interview.
It previews Aikya-owned changes before adoption. Ambiguous repositories return
`PARTIAL` or `NEEDS_REVIEW` and require review before proceeding.

| Option | Purpose |
|---|---|
| `--dry-run` | Preview detection and planned changes without installing. |
| `--report-only` | Return an analysis report without writing artifacts. |
| `--focus general` | General analysis; the default focus. |
| `--focus security` | Focus on security evidence. |
| `--focus architecture` | Focus on architecture evidence. |
| `--focus infrastructure` | Focus on infrastructure evidence. |
| `--focus operations` | Focus on operational evidence. |
| `--scope <relative-path>` | Limit discovery to a component, such as a monorepo workspace. |
| `--methodology odd` or `--methodology sdd` | Choose Organic Driven Development or Spec-Driven Development before initial adoption. |
| `--refresh` | Refresh only verifiably managed analysis assets. |
| `--docs-lang en` or `--docs-lang es` | Choose the living documentation language. |

Examples—run each separately as needed:

```text
/aikya-analyze --report-only --focus security
/aikya-analyze --dry-run --focus architecture --scope apps/api --docs-lang en
/aikya-analyze --refresh
```

Discovery does not build applications, execute application scripts or deploy
infrastructure. Adoption preserves application code and customized configurations.

### Choose ODD or SDD

**Both `/aikya-init` and `/aikya-analyze` offer ODD and SDD.** ODD is recommended;
the initial choice is required before writing project files. ODD keeps contained
changes in the existing request audit and adds a reviewed, resumable worklist for
substantial work. SDD uses separate specification, plan and task approvals.
For an existing repository, preview the selected methodology first:

```text
/aikya-analyze --dry-run --methodology sdd --docs-lang en
```

Review the file plan, generator upgrades and quality-gate backup before approving
adoption. Without an initial choice the CLI returns `NEEDS_METHODOLOGY` and writes
nothing. Confirmed profiles retain their methodology on refresh; legacy `standard`
inputs normalize to `odd` with conservative managed-file backups. Disabling SDD
requires a separately reviewed migration. See [ODD continuity](docs/ODD.md).

The SDD workflow is:

```text
/aikya-specify
/aikya-clarify
/aikya-plan
/aikya-tasks
/aikya-implement
/aikya-sdd-status
```

Specification, plan and tasks each need their own approval. Implementation and
generation require an active **SPEC-NNN + TASK-NNN**, plus consent for the actual
changes. An old approved specification does not authorize a different task.
SDD works with development, infrastructure and DevOps; it is a methodology, not
a fourth project type or a replacement application architecture.

See [the SDD workflow](docs/SDD.md) for input schemas, migration and evidence limits.

### Documentation language

`en` is the default; `es` is also available **only for living Markdown documents
under `aikya/docs/`**. The preference is stored in `.aikya/docs-policy.json`.
All agents, skills, rules, source and documentation outside that directory remain
in English. Changing an existing documentation language requires a separately
reviewed migration.

## 3. Components and project structure

![Aikya components: commands, agents, skills, templates, model policies and GitHub Actions](docs/images/aikya-components.png)

### Harness source

| Path | Purpose |
|---|---|
| `src/aikya/resources/commands/` | Source of the 28 public Claude Code slash commands. |
| `src/aikya/resources/engineering/agents/` | Curated specialist agent definitions. |
| `src/aikya/resources/engineering/skills/` | Curated technical skills. |
| `src/aikya/resources/project_template/` | Base project agents, skills, rules and harness utilities. |

Python code lives in `src/aikya/`, grouped into core, tools, middleware, memory, installation, discovery, workflows, documentation, catalogs, routing and quality. `pyproject.toml` defines the package; installed script entry points remain compatible and are generated from one template. Only `setup.py` remains as a root Python build file.

All Aikya-generated plans, bugs and features stay inside `aikya/docs/`: `plan/`, `bugs/` and `features/`. SDD plans remain in their authoritative specification dossier under `aikya/docs/specs/`.

### Project artifacts

| Path | Purpose |
|---|---|
| `.aikya/answers.json` | Technical decisions for compatible profiles. |
| `.aikya/docs-policy.json` | Living documentation language. |
| `.aikya/model-policy.json` | Optional per-role model policy. |
| `.aikya/analysis/` | Evidence-based inventory for existing repositories. |
| `.harness/project-profile.json` | Normalized, legacy-compatible technical profile. |
| `.harness/engineering-catalog.json` | Managed skill and agent provenance. |
| `.claude/agents/` and `.claude/skills/` | Specialists and capabilities selected for the actual stack. |
| `.claude/rules/` and `CLAUDE.md` | Engineering contracts and project instructions. |
| `aikya/docs/` | Living documentation and per-request change records. |
| `aikya/scripts/` and `aikya/test/` | Internal harness utilities and tests. |
| `harness.json` | Configured quality checks and `NOT_CONFIGURED` behavior. |

New monorepos can plan application workspaces under `apps/`, with shared
`packages/` and `contracts/`. A singlerepo keeps its application at the root.
Existing projects are not reorganized automatically.

## 4. Claude Code commands

| Command | Purpose |
|---|---|
| /aikya-init | Interview and initialize a brand-new project |
| /aikya-analyze | Discover and adopt an existing repository |
| /aikya-answers | Apply a validated declarative technical profile |
| /aikya-doctor | Diagnose SDK and runtime prerequisites locally |
| /aikya-project | Plan a new project or module |
| /aikya-infra | Plan, generate with approval and validate infrastructure |
| /aikya-scaffold | Plan and execute approved application generators for new projects |
| /aikya-feature | Implement a scoped feature with tests |
| /aikya-bugfix | Investigate defects and add regression evidence |
| /aikya-arc-review | Review architecture and propose ADRs |
| /aikya-mobile-feature | Deliver validated mobile features |
| /aikya-skills-status | Inspect registered Agent Skills |
| /aikya-skills-plan | Assess external skill sources and installation impact |
| /aikya-install-skill | Install reviewed external skills after explicit approval and record actual comparisons |
| /aikya-quality | Run available quality gates |
| /aikya-docs | Maintain evidence-backed living documentation |
| /aikya-tests | Run focused and regression tests |
| /aikya-docs-sync | Synchronize impacted docs and request traceability |
| /aikya-verify | Validate technical changes and results |
| /aikya-models | Review optional model routing policy |
| /aikya-tokens | Inspect token usage and estimated API costs |
| /aikya-memory | Browse project-local memory and code in an offline HTML graph, or watch changes live |
| /aikya-specify | Create a draft specification and acceptance criteria |
| /aikya-clarify | Resolve specification questions and record explicit approval |
| /aikya-plan | Draft a technical design and testing plan |
| /aikya-tasks | Define requirement-linked tasks and dependencies |
| /aikya-implement | Execute the active approved specification/task with scoped consent |
| /aikya-sdd-status | Inspect SDD state, traceability and recorded evidence |

Managed upgrades back up verified old commands and retire them only after their
replacements are available. Customized legacy commands are preserved and reported
for review.

The project-local skills architecture also includes base feature, bugfix,
verification, documentation and architecture-review workflows. Do not invoke
optional external tools automatically.

## 5. Documentation, audits and Git history

![Documentation traceability in Aikya](docs/images/documentation-traceability-en.png)

SDD adds versioned specifications under `aikya/docs/specs/<project_type>/SPEC-NNN/`,
including Markdown documents and a machine-readable `state.json`. The latter stores
workflow state; documentation does not consist exclusively of Markdown.

Material technical changes update the affected `.md` pages under `aikya/docs/`
and create a `changes/REQ-*.md` record with **Changes**, **Evidence** and
**Updated documents**. `docs_guard` checks documentation requirements.
When committed with the project, these files provide reviewable history and diffs
for audits and version tracking. Read-only consultations do not require artificial
records; full prompts, secrets and private data must not be recorded.

Every Markdown document generated by Aikya ends with the exact line
`GENERATED BY AIKYA HARNESS`, wherever it is saved. This includes analysis reports,
infrastructure README files, `CLAUDE.md`, agents and skills. `indice.md` lists the
Markdown files that actually exist; reports without supporting data are omitted.
Initialization guidance and toolchain findings belong in `overview.md`.

| Path under `aikya/docs/` | Content |
|---|---|
| `features/<lowercase-feature>/` | Actual feature scope and implementation records |
| `architecture/architecture-overview.md` | Main architecture for both init and analyze |
| `plan/testing.md` | Selected test plan or observed testing evidence |
| `tools/agents.md` | Agents actually available in the project |
| `tools/token-policy.md` | Context and token policy |
| `tools/skill-comparison.md` | Actual external installation results; created only through `/aikya-install-skill` |

Existing managed documents migrate with backups under `.harness/backup-docs-layout/`.
Customized conflicts require review. Runtime `.harness/` and `aikya/scripts/harness/`
retain their existing names.

### Local code memory and HTML

Approved initialization/adoption configures a project-local incremental index and
automatic updates. Session hooks start the local observer for configured projects;
session end stops it when no other session remains. For editors outside Claude Code,
keep an explicit observer running:

```text
/aikya-memory
/aikya-memory --refresh --open
/aikya-memory --watch --open
/aikya-memory --dry-run
```

The observer detects saved code, new classes, renames and deletions. It updates
SQLite in `.harness/state/code-index/`, then regenerates
`aikya/docs/memory/view/index.html` and its matching `report.md`. `--watch --open`
also refreshes the open page through a temporary loopback viewer. The exported
HTML remains a self-contained offline snapshot. No system service is installed.

Indexing and export call no model and consume no API tokens; they use local CPU
and disk. Later AI queries retain their normal context usage. Python declarations
work without dependencies; the optional pinned `code-index` extra adds Java,
JavaScript/JSX, TypeScript/TSX, C# and Go. Other languages retain file inventory.
Source changes invalidate note eligibility without rewriting decisions or approvals.
Existing-project adoption preserves custom ignore files. See
[configuration, limits and lifecycle](aikya/docs/architecture/local-memory.md).

## 6. Engineering agents and Agent Skills

Aikya selects specialists according to the actual stack: architecture, backend,
frontend, mobile, cloud, infrastructure, CI/CD, security, testing and code review.
**Planner** and **Orchestrator** support complex cross-stack work when needed.
Reviewers operate within their defined permissions; modifying specialists stay
within the approved scope. An installed agent is not proof that it has run.

### Optional external skills

| External integration | Registered source | Availability in Aikya |
|---|---|---|
| Ponytail | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | Optional; included in the external integration plan. |
| Graphify CLI | [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) | Optional; CLI and project skill integration. |
| UI UX Pro Max | [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | Optional; included in the plan for frontend or mobile profiles. |

Review availability and installation impact from Claude Code:

```text
/aikya-skills-status
/aikya-skills-plan
```

After reviewing the plan, use `/aikya-install-skill` with explicit approval.
Review source provenance, license, tools, network access and version/commit before
installation. Third-party installer hooks must not run silently.

### Recursion: conceptual workflow views

The following diagrams explain two levels of refinement. They are conceptual
views grounded in task review and harness maintenance, not additional Aikya
commands or a claim of autonomous self-modification.

**Task-level recursion** refines implementation within one task using verification
findings and acceptance criteria.

![Task-level recursion](docs/images/task-level-recursion.png)

**Harnessing-level recursion** improves reusable agents, skills, templates and
rules through reviewed source changes and validation for future tasks.

![Harnessing-level recursion](docs/images/harnessing-level-recursion.png)

The next diagram extends that conceptual model: **parallel recursion** explores
candidate harnesses and composes refinements from execution evidence;
**sequential recursion** carries the refined harness and accumulated evidence
through successive **Propose → Probe → Compose** steps. These are explanatory
patterns, not verified built-in execution modes.

![Scaling task-level recursion through parallel and sequential refinement](docs/images/scale-task-level-recursion.png)

## 7. Our safety approach with Aikya

Aikya's documented workflow centers on scoped changes, explicit approvals and
verifiable evidence:

- Preserve customized project files, agents, skills, instructions and secrets.
- Ask for approval before SDK installation, dependency downloads and external operations.
- Require separate authorization for deployments, Terraform apply/destroy, remote cluster writes and destructive migrations.
- Report actual `PASS`, `FAIL`, `SKIPPED` and `NOT_CONFIGURED` outcomes.
- Distinguish source manifests and plans from verified live infrastructure state.
- Enforce applicable documentation requirements and retain change traceability.
- Review optional third-party sources before installation and protect credentials.

These controls guide Aikya's behavior; they do not certify an application as
secure or replace project-specific security review.

## 8. Further documentation

- [Changelog](CHANGELOG.md)
- [Contribution guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Code of conduct](CODE_OF_CONDUCT.md)
- [GitHub workflow contracts](.github/workflows.md)


### Aikya templates for SDD

SDD composes nine roles from the pinned [Aikya template library](src/aikya/resources/aikya-template/docs/README.md): feature, API, database, specification, design, tasks, evidence, review and engineering rules. Aikya retains its acceptance criteria, traceability and separate approvals. Only supplied reviewed content creates documents. See [SDD template usage](docs/SDD_TEMPLATES.md) and the [complete generated-example gallery](examples/documentation/generated/README.es.md).

## Project-specific CLAUDE.md

Aikya selects English instructions for development, infrastructure or DevOps, then adds only the recorded stack, layout and methodology guidance. Existing CLAUDE.md files are preserved. See [template selection and examples](docs/CLAUDE_TEMPLATES.md).

## Documentation template library

120 pinned Aikya templates are available offline; Upstream attribution is retained in THIRD_PARTY_LICENSES.md. Architecture uses `aikya/docs/architecture/architecture-overview.md`; actual bugs append to `aikya/docs/bugs/bugs.md`. Documents require reviewed facts and authorization. See [selection, examples, license and compatibility](docs/DOCUMENTATION_TEMPLATES.md).

Aikya now combines its generated documents with selected Aikya reference templates foundations by command, methodology and project profile. ODD features include observable acceptance criteria; optional design/test sections use actual supplied facts. See [contextual template composition](docs/CONTEXTUAL_TEMPLATE_COMPOSITION.md).


## Execution phases and usage

All public commands share **Explore → Plan → Implement → Validate → Security → Review**,
with proportional applicability and separate English status labels. The local bar
shows the active action, observed model/executor, context and optional account
5h/7d limits. Missing data stays N/D. Recorded session tokens use explicitly selected
transcripts; account quotas are never inferred from them. Read-only queries write
no project documents. Custom bars/hooks are preserved with a reviewable proposal.
See [visibility, evidence and configuration](docs/EXECUTION_VISIBILITY.md) and the
[complete Spanish implementation plan](aikya/docs/plan/archive/harness-development/2026-10-23-odd-observabilidad.es.md).

## Optional agent loop

Explicitly enable bounded execution for /aikya-feature, /aikya-bugfix or
/aikya-implement. The optional Claude Agent SDK runs the task; Aikya enforces the
reviewed file scope, ODD/SDD gates, local checks, read-only review and durable limits.
It never starts during onboarding or installs the SDK automatically. See
[setup, permissions, recovery and controlled live testing](docs/AGENT_LOOP.md).

Optional project/private memory supports explicit review, checkout migration and
bounded model proposals that remain pending until approved. The source-quality
gate requires modularization above 1,000 lines per changed source file; Python
long functions and repeated bodies receive review warnings. See the
[security and quality controls](docs/SECURITY_CONTROLS.md) for what is enforced.

GENERATED BY AIKYA HARNESS
