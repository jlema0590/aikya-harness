# Optional bounded agent loop

Aikya can execute one explicitly authorized ODD or SDD task through the optional
Claude Agent SDK. Aikya controls scope, dependencies, iterations, checks and task
closure; Claude Code owns model/tool execution, conversation storage and context.
The SDK is not installed automatically. The existing 27 slash commands remain.

## Prepare and authorize

Use /aikya-feature, /aikya-bugfix or /aikya-implement with an explicit request to use
the agent loop. First initialize an ODD worklist or approve the active SDD
specification, plan and tasks. Every task dependency must be complete. Small ODD
work can continue through the ordinary inline workflow without creating a dossier.
/aikya-init and /aikya-analyze never start this loop automatically.

Install both Aikya and the optional SDK in the same separate Python environment
when you choose to use the loop. Use Python 3.10–3.13 and the verified wheel from
your selected Aikya release; replace `X.Y.Z` below with that release version.
The tested SDK is pinned to 0.2.173.

Linux/macOS:

```bash
python3 -m venv .venv-aikya-loop
.venv-aikya-loop/bin/python -m pip install /path/to/aikya_harness-X.Y.Z-py3-none-any.whl
.venv-aikya-loop/bin/python -m pip install 'claude-agent-sdk==0.2.173'
.venv-aikya-loop/bin/python -m aikya.core.runtime check
```

Windows PowerShell:

```powershell
py -3 -m venv .venv-aikya-loop
.\.venv-aikya-loop\Scripts\python.exe -m pip install 'C:\downloads\aikya_harness-X.Y.Z-py3-none-any.whl'
.\.venv-aikya-loop\Scripts\python.exe -m pip install 'claude-agent-sdk==0.2.173'
.\.venv-aikya-loop\Scripts\python.exe -m aikya.core.runtime check
```

For contributors, install the checkout into that environment with
`python -m pip install --no-build-isolation --no-deps -e /path/to/aikya`
after installing its documented build prerequisites, then install the pinned SDK.
`requirements-agent-loop.txt` remains the equivalent pinned SDK requirements file
in the distribution. Installing only that file does not install the Aikya package.

Use this same environment's Python for the commands below; `python` is shorthand
for its executable and does not require activation. SDK availability is local to
that interpreter. The clean installer intentionally creates a base environment
without the SDK, so an SDK installed elsewhere does not enable its interpreter.
The `check` command confirms SDK import/version only; it does not authenticate,
call a model or prove that a task is authorized.

Authenticate Claude in that environment using your organization's supported
method. Do not put credentials in the reviewed JSON, task files or audit records.
The SDK's API estimate is not a subscription quota or authoritative bill.

Review a configuration like this, adapting the files and checks to your project:

```json
{
  "schema": 1,
  "command": "aikya-feature",
  "work_id": "value",
  "task_id": "TASK-001",
  "files": ["src/value.py"],
  "context_files": ["tests/test_value.py"],
  "max_iterations": 3,
  "max_turns": 8,
  "timeout_seconds": 120,
  "max_cost_usd": 0.25,
  "memory_budget_chars": 4000,
  "hooks_approved": false,
  "checks": [
    {
      "name": "value-tests",
      "phase": "validate",
      "argv": ["python3", "-m", "unittest", "discover", "-s", "tests"],
      "timeout_seconds": 30
    },
    {
      "name": "project-security",
      "phase": "security",
      "argv": ["python3", "scripts/check_security.py"],
      "timeout_seconds": 30
    }
  ]
}
```

Checks must actually exist and be appropriate to the change. Their exact argv are
part of the authorization: they run locally with the selected environment and can
have side effects. Aikya does not certify arbitrary check scripts as safe or turn
them into a sandbox. Validation and scoped Security checks are both required.

The model can only Read approved files/context and Edit/Write approved task files.
Bash, Skill, subagents, network/MCP tools and writes to Aikya controls are not
available as child tools. In SDD, use work_id=SPEC-NNN; the loop checks the real
stage approvals before execution and never creates them. The SDK loads user,
project and local settings, preserving deny/ask rules. Configured hooks execute
under those settings and need separate review with hooks_approved=true; their
settings hashes are bound to the invocation. This is an application policy layer,
not protection against a hostile OS user concurrently replacing filesystem paths.

## Execute, observe and stop

Use the Python environment containing both Aikya and the optional SDK:

```bash
python -m aikya feature --target . --agent-loop --loop-input reviewed-loop.json --approved
```

Installed project/global compatibility adapters remain supported. The default
worker launches the canonical package module with the current interpreter and
pins its package import root, including when invoked through a copied adapter.
It does not rely on root source launchers or the project's current directory.

The JSON command must match the requested feature, bugfix or implement command.
Explore, Plan, Implement, Validate, Security and Review remain English; status is
separate. The local process observer and the durable summary record outcomes.
Review uses a separate read-only model invocation. A model's claim of success
cannot replace process checks or approve SDD stages.

The loop handles one task per invocation and reports its outcome; select a new
task explicitly instead of silently expanding the approved files/checks. It runs
at most three implementation iterations, stops after two unchanged candidates
with no accepted outcome, and applies the reviewed runtime turn/time limits.
The same time/cost ledger survives resume. max_turns applies to each SDK query;
iteration, elapsed-time and cumulative estimate limits bound the enclosing loop.
Estimated-cost limits can overshoot by an in-flight provider request; they are not
hard billing guarantees. Missing cost data blocks further execution. Missing token
counts stay unknown, and provider weekly limits are never inferred from them.

## Audit and recovery

The loop creates only substantive records:

```text
aikya/docs/loops/<run-id>/
  state.json
  summary.md
  evidence.json    # only after checks and review accept the current candidate
```

summary.md follows the configured en/es documentation language and has the exact
Aikya footer; indice.md includes it. JSON holds control metadata, not conversation
prompts, credentials or raw tool output. Evidence contains check exit codes,
command hashes, candidate fingerprints and the review invocation reference.
Writes use temporary files, fsync and atomic replacement; files are separate
checkpoints, not a multi-file ACID transaction or a tamper-proof signed receipt.
Custom summaries, changed approvals/context, symlinks and another checkout require
review instead of being silently overwritten. Do not manually edit state to reset
budgets or mark outcomes complete.

```bash
python -m aikya.core.loop status --root . --run-id RUN_ID
python -m aikya feature --target . --agent-loop --loop-input reviewed-loop.json --loop-run-id RUN_ID --approved
```

An effect intent is durably acknowledged before the child writes. If a process
stops before its matching result arrives, automatic resume refuses to replay it.
Inspect the files and checkpoints, then explicitly reconcile when appropriate:

```bash
python -m aikya.core.loop reconcile --root . --run-id RUN_ID --approved
```

Reconciliation does not replay tools or erase history. An unfinished model query
has unknown usage and blocks further model calls; it does not become a free retry.
Exhausted limits remain exhausted. A separately reviewed new run is a new budget
and authorization decision. Successful closure updates the ODD task or SDD task;
it does not perform requirement-level SDD verification or certify an application
as secure. External installation, publication and deployment retain their own
permissions.

## Selective project memory

Reviewed notes are optional references. Project notes live under aikya/docs/memory/;
private notes live outside Git under ~/.aikya/memory/<project-identity>/ by default.
Private directories use mode 0700 and files 0600 on POSIX; this is not encryption or
a cross-user collaboration service. --private-root selects an alternative external
store. A private root inside the project or a symlinked store is rejected.

Schema-2 notes record type (user, feedback, project or reference), scope, project
and checkout identity, source fingerprint, creation time, TTL, origin, extraction
reference and pending/approved/rejected review state with review time. Model
proposals always start pending. Existing custom notes are preserved; pending,
rejected, stale, moved and expired notes are excluded from recall. Schema-1 notes
remain on disk but require explicit review to bind them to the current checkout.
MEMORY.md is a generated index, not authority to approve work.

The same lexical retrieval engine handles both scopes, selects at most five unique
notes, and applies one total character budget. Project-only retrieval is the
default. To include private notes in a loop, explicitly set memory_scopes to
["project", "private"] in its reviewed configuration; memory_budget_chars still
limits the combined content. Team synchronization and a second conversation
compactor are not implemented.

Loop recall is disabled when `memory_budget_chars` is omitted or zero. A positive
budget enables retrieval during implementation iterations; it does not create or
approve notes. Startup/visibility hooks and ordinary slash commands do not inject
this memory automatically. Direct local note and recall commands do not need the
optional SDK; model-assisted extraction does.

```bash
python -m aikya.memory.knowledge add --root . --input reviewed-memory.json --approved
python -m aikya.memory.knowledge recall --root . --query "value lookup" --budget-chars 4000
python -m aikya.memory.knowledge propose --root . --input candidate.json
python -m aikya.memory.knowledge review --root . --id NOTE_ID --decision approved --approved
python -m aikya.memory.knowledge recall --root . --query "value lookup" --include-private --budget-chars 4000
python -m aikya.memory.knowledge migrate --root . --scope project --from-identity PREVIOUS_IDENTITY --approved
python -m aikya.memory.knowledge migrate --root . --scope private --from-identity PREVIOUS_IDENTITY --approved
```

Input requires kind, text, source and ttl_days (1–365), with optional scope
(project/private). The source must be a current regular project file. Duplicate
proposals do not promote pending or rejected notes; use review explicitly. Identity
migration validates current sources, preserves old private stores and records a
Markdown receipt. It is a sequence of durable file updates; after interruption,
inspect the receipt and explicitly repeat the migration. It never migrates task
loop approvals or authorizations. Memory never completes tasks or replaces actual
files/evidence. Recovered notes are labelled as untrusted reference material.

### Optional model-assisted extraction

Run `python -m aikya.memory.extraction` only after reviewing the source files and model budget.
It reuses the existing ProcessRuntime with read-only scoped tools and one model
query. It creates up to three pending candidates, never automatically approving
or consolidating them. The supplied file contents are disclosed to the configured
runtime/provider. No model invocation occurs during installation or onboarding.

```json
{
  "schema": 1,
  "files": ["src/value.py"],
  "scope": "project",
  "max_turns": 3,
  "timeout_seconds": 60,
  "max_cost_usd": 0.02
}
```

```bash
python -m aikya.memory.extraction --root . --input reviewed-extraction.json --approved
```

The optional hooks_approved flag has the same meaning as in the task loop. Limits
are 10 input files, 16,000 bytes per file and 32,000 bytes of supplied context,
20 turns, 600 seconds and USD 10 maximum configured estimate. Receipts persist a
query intent before calling the runtime and record available metering afterwards.
An interrupted query remains uncertain with unknown usage; there is no automatic
retry or resume. A new invocation is a new explicit authorization and budget.
Private extraction keeps notes and receipts in the private store. Project receipts
live under aikya/docs/memory-extractions/. Receipts omit prompts and raw output.

## Source quality before task completion

The shared code_quality.py checks candidate source files before Review. Source
files above 1,000 physical lines fail unless a current content-bound exception
exists. Python functions above 100 lines and exact nontrivial repeated Python AST
bodies produce review warnings. Missing files count as deletions, not empty code.
All reported checks remain bound to the current candidate. A model must request a
scope change if modularization requires files outside its approved allowlist.

```bash
python -m aikya.quality.source --root . src/service.py src/other.py
python -m aikya.quality.source --root . --changed --base HEAD
```

Normal edit hooks supply feedback after writes; the checker can also be configured
as a required harness.json/CI check. See [security and quality controls](SECURITY_CONTROLS.md)
for the enforcement boundaries. Large pre-existing files are not automatically
rewritten, and an all-repository audit can expose unrelated historical findings.

## Verify in another environment

Local tests exercise process behavior, installation and failure boundaries without
calling a model. The optional SDK contract check constructs real SDK options and
runs its callbacks without authentication:

```bash
python tests/sdk_agent_loop_contract.py
python -m unittest discover -s tests -p 'test_agent_loop*.py'
python -m unittest discover -s tests -p 'test_agent_memory.py'
```

For the controlled live smoke, use scripts/ci/agent_loop_smoke.py with --live,
--approved and an explicit --max-cost-usd. It creates an isolated synthetic project,
allows only its value file, executes real validation/Security checks and requires
read-only model review. It never deploys or installs SDKs. A successful fixture
suite alone is not a successful live SDK run.

Official references: [Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview),
[permissions](https://code.claude.com/docs/en/agent-sdk/permissions),
[usage estimates](https://code.claude.com/docs/en/agent-sdk/cost-tracking).

GENERATED BY AIKYA HARNESS
