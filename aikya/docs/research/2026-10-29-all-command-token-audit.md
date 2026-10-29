# Token exposure audit of all public Harness commands

Date: 2026-10-29. Source revision: `512dea2`.
This extends the [jourpass_app investigation](2026-10-29-token-efficiency-jourpass.md).
The scope is the 28 canonical names in `aikya.cli.commands.BOOTSTRAP_COMMANDS`.
Commands supplied by Mods have a separate registry and are not silently included.

## What was checked

- Read the shipped instructions of every command, its default phase recipe and
  relevant local support paths. Verify optional model-execution entry points.
- Run the existing `scripts/ci/command_acceptance.py` Battery in disposable synthetic
  projects, measuring each support invocation's stdout/stderr size and elapsed time.
  Results: **28/28 commands, 52 subprocess checks passed**, including 17 expected
  negative cases. These exercise local support contracts, not end-to-end AI tasks.
- Run `scripts/ci/smoke_profiles.py`: **14/14** example profiles passed.
- Validate shipped Agent Skills and Claude agent metadata: **VALID**.
- Reuse the already-authorized jourpass_app usage receipt; do not scan unrelated
  projects, run Claude requests, install third-party skills or deploy infrastructure.

No production code, private application files, user settings or model selections
were changed. The temporary measurement wrapper subclasses the existing Battery;
its script fingerprint and per-check receipts are recorded in the companion JSON.

## Three rankings that must remain separate

### 1. Observed session windows: cumulative model usage

| Window beginning with | Main + subagent messages | Recorded tokens including cache |
|---|---:|---:|
| Memory, until the first mobile marker | 89 | 19,570,855 |
| Three Analyze markers, before Memory | 64 + 76 | 13,389,086 |
| Two Mobile Feature markers, before architecture review | 9 | 2,704,540 |
| Architecture Review, until the session ends | 6 | 1,950,839 |

These are chronological windows, not causal billing per command. They include
follow-up work and plugin activity. The 89-message Memory window includes edits,
monitoring and documentation blockers; **the local exporter did not issue those
89 model requests**. Its CLI can maintain/export memory without a model.

Across the selected session and subagents, 97.36% of recorded tokens are cache
reads. Main-request input averages 192,734 tokens and peaks at 336,173. The first
mobile window has a single usage-bearing message with 247,483 cache-creation
input tokens, 44,948 cache reads and five uncached input tokens. That demonstrates
a large request boundary when mobile work began; the exact cause of cache creation
cannot be assigned to expiration or another invalidation without further evidence.

This points to accumulated context, delegated investigation, scope changes and
repeat work as important observed factors. The lack of Dart symbol retrieval and
normal-command index integration is verified separately in the original report.
The optional SDK loop was not established as the executor of this session.

Exact per-command provider usage is unavailable for all 28 commands. Four command
names have chronological window evidence, while the other 24 have no such evidence
in the selected session. Unmeasured usage remains null, never zero. No account
quota delta can be calculated from the token totals.

### 2. Largest local support responses

Analyze returned **48,637 bytes** in its approved adoption fixture. Init peaked at
**48,477 bytes** in one invocation; 191,409 bytes is the sum across five Init
checks and must not be advertised as one invocation. Answers peaked at 2,929 bytes.
The measurements include stderr as well as stdout, including expected failures.

Analyze serializes complete `actions` and `analysis_operations`; Init reports
requirements and installation actions. This is local deterministic work, but
returning full lists to an assistant expands its next request context. At the
same coarse character proxy, the largest responses are approximately 13.9K units,
substantially above the selected Analyze/Init instruction bodies themselves.

These response sizes are particular to the fixtures, path lengths and tested
submodes. They are not worst-case bounds, tokenizer measurements or task token
estimates. Feature's small local writer response does not measure implementation,
and Install Skill's approval-denial check does not measure an actual installation.
Real test/build logs and SDK execution may return much larger results.

### 3. Selected instruction bodies and workflow factors

The instruction proxy is `round(shipped_characters / 3.5)`. It excludes host system
instructions, tools, current history, task input and subsequent source/results.
All command bodies are not assumed to be loaded at once. Peak response is one
measured support invocation, not a complete AI workflow.

| Command | Instruction proxy | Peak local response, bytes | Why context can grow |
|---|---:|---:|---|
| `/aikya-implement` | 2,362 | 222 | Largest selected workflow body; ODD/SDD records, implementation, checks and optional SDK Review. |
| `/aikya-feature` | 2,171 | 522 | Source implementation, tests, documentation, optional bounded SDK loop and review. |
| `/aikya-bugfix` | 2,124 | 58 | Reproduction, hypotheses, source reading and test/review retries; optional SDK loop. |
| `/aikya-analyze` | 1,667 | 48,637 | Discovery/adoption and complete operation lists; deep architectural/security work may add agents. |
| `/aikya-mobile-feature` | 1,657 | 532 | Platform-specific source/tests and specialist work; Dart/Kotlin/Swift symbol gaps matter. |
| `/aikya-sdd-status` | 1,632 | 799 | Local status/lint/completion records; template/drafting guidance is disproportionate for a simple status. |
| `/aikya-init` | 1,591 | 48,477 | Interview, toolchain report and complete managed-asset lists; local install output is large. |
| `/aikya-docs` | 1,536 | 58 | Affected-source reading and substantive documentation drafting; avoid the full library. |
| `/aikya-specify` | 1,525 | 100 | Requirement drafting and questions; local specification writer does not run a model. |
| `/aikya-tests` | 1,523 | 310 | Focused test execution, failure diagnostics and reruns; avoid returning all passing output. |
| `/aikya-plan` | 1,432 | 223 | Design/source investigation and justified planner use; avoid restating the full specification. |
| `/aikya-tasks` | 1,428 | 235 | Requirement coverage/dependency graph and reviewed task authoring; avoid reopening completed discovery. |
| `/aikya-arc-review` | 1,417 | 383 | Cross-module inspection and architectural review; output scope can expand widely. |
| `/aikya-quality` | 1,228 | 72 | Local check output and analysis of failures; full real-world logs can exceed the small fixture. |
| `/aikya-verify` | 1,197 | 222 | Checks, diff and documentation inspection; reuse current-candidate evidence rather than duplicate work. |
| `/aikya-clarify` | 1,115 | 211 | Only outstanding questions and reviewed answers; preserve approval separation. |
| `/aikya-docs-sync` | 1,061 | 0 | Affected pages and REQ audit; documentation blockers may induce additional assistant turns. |
| `/aikya-tokens` | 954 | 1,376 | Local authorized transcript aggregation; report category totals rather than transcript text. |
| `/aikya-scaffold` | 948 | 376 | Generator planning and guarded execution; dependency/toolchain logs when approved. |
| `/aikya-infra` | 940 | 1,188 | Infrastructure plans and local validation; external execution is separately authorized. |
| `/aikya-answers` | 911 | 2,929 | Reviewed declarative profile and adoption preview; no technical interview is required. |
| `/aikya-install-skill` | 875 | 68 | Explicit source review and installation permission; fixture exercises denial, not third-party install. |
| `/aikya-project` | 864 | 376 | Boundary/design planning; source inspection and justified planning delegation. |
| `/aikya-models` | 807 | 248 | Local policy inspection/configuration; no provider inference is needed just to inspect. |
| `/aikya-skills-status` | 782 | 1,174 | Local registry inspection; should not expand into third-party audits or installation. |
| `/aikya-memory` | 777 | 324 | Local indexing/export/watch has no model request; later assistant edits/monitoring are separate work. |
| `/aikya-skills-plan` | 757 | 333 | Source/license/permission planning; avoid unsolicited vendor surveys. |
| `/aikya-doctor` | 753 | 1,132 | Local requirements inspection; common observation instructions exceed the task-specific body. |

## Verified disproportionate overhead

The same **1,658-character** execution-observer body occurs in 27 commands; Memory
has separate concise local-operation instructions. The common body is 62.90% of
Doctor, 62.57% of Skills Plan, 60.58% of Skills Status and 58.67% of Models. Reducing
it can improve a selected invocation; multiplying it by all 27 commands does not
measure one session's initial context or establish a saving percentage.

SDD Status is the sixth-largest selected body at about 1,632 proxy units despite
having a local read-only status path. It includes specification/plan/task approval,
template and document-composition guidance that a simple status need not traverse.
Implement is the largest at about 2,362 proxy units; its optional loop instructions
and ODD/SDD continuity contribute. Feature and Bugfix follow at 2,171 and 2,124.
None of these sizes alone explains multi-million cumulative input processing.

The default phase recipe also includes Implement/Security for Models, Quality,
Tests and Verify, although some actions only inspect policy or run checks. The
recipe currently lacks an explicit action argument. This is a confirmed design
limitation, not evidence that those phases consumed a specific number of tokens
in the selected session. Read-only and writing submodes need separate contracts.

The code-level model-execution paths reviewed are the explicitly approved SDK
loop and optional memory-note extraction. Model-policy inspection itself is local.
The host assistant can still spend tokens analyzing source, drafting documents,
reading logs and invoking agents while following any slash command.

## Priorities added to the implementation plan

1. Compact native Init/Analyze results, preserving complete plans as explicitly
   requested/reviewable output. Add a summary mode with a proposed 2,000-character
   response budget, counts, status, blockers and links/omission counts. A dry-run
   must remain write-free. Never truncate away a blocking result or silently pass.
2. Make local inspection paths thin: Doctor, Skills Status, Models inspection,
   Tokens and SDD Status must not cause a new discovery interview, template survey,
   implementation phase or automatic delegation. Preserve separately approved
   write/evidence modes of hybrid commands.
3. Reuse current-candidate test/security/documentation evidence when applicable;
   do not repeat Quality, Tests and Verify just because their names differ.
   A changed source hash, check definition, environment or relevant configuration
   invalidates reuse. Failure and missing evidence remain visible.
4. Keep Memory on the canonical CLI for export/watch. Browser design changes,
   runtime repairs and plugin troubleshooting are distinct tasks with their own
   acceptance and usage, not routine memory maintenance.
5. For coding commands, use the shared bounded context packet, language coverage
   and cumulative SDK limits already planned. Restrict documentation to affected
   records. Preserve SDD approvals and security/review for risk-relevant changes.
6. Remove unsolicited named-vendor surveys from Skills Plan/Install Skill while
   retaining installation of the source selected by the user. This also matches
   the user's earlier requirement to retain installation without vendor promotion.
7. Extend the benchmark to every canonical command and compatible action/profile.
   Record instruction size, local stdout/stderr, actual model request categories,
   observed model/effort, subagent share, check retries and attribution confidence.
   A read-only contract pass is not a model-performance measurement.

A real 28-command model benchmark still needs controlled accepted tasks, valid
prerequisites, fixed model/effort/cache conditions, isolation and a reviewed usage
budget. For external installation/deployment, use fixtures or denied/mock paths;
never perform the external action simply to obtain a token measurement. Record
unsupported modes and unavailable provider data honestly. Compare equivalent
results, not an onboarding run against an unrelated implementation task.

## Evidence and verification

[All-command receipt](2026-10-29-all-command-token-audit.json) contains each command's
instruction size, common-body share, phase recipe, factors, support invocations,
expected/actual exits, stdout/stderr sizes, elapsed times and output hashes. It
contains synthetic fixture paths, no application code or transcript text.

The measurement wrapper was run again to include stderr explicitly; only the final
complete measurement is retained. All 52 expected exits match, including the 17
negative checks. No models were called during the backend battery.

The [Spanish implementation plan](../plan/2026-10-29-token-efficiency.es.md) now
includes the 28-command matrix alongside the 29-extension language matrix.

GENERATED BY AIKYA HARNESS
