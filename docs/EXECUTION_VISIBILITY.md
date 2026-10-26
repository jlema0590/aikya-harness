# Execution visibility

Aikya separates the workflow phase, its status, the executor and the available
usage data. All 27 public commands share this protocol. Initial onboarding and
configured quality checks publish local process observations automatically;
semantic actions in skills publish explicit transitions through the observer.
A hook seeing a tool or an agent stop never certifies a successful phase.

| Phase | Purpose |
|---|---|
| Explore | Inspect the request, project evidence and relevant risks. |
| Plan | Resolve scope, methodology, acceptance, tasks and authorizations. |
| Implement | Make authorized changes; onboarding installs the harness and documentation. |
| Validate | Record actual functional or structural checks. |
| Security | Check affected permissions, secrets, dependencies or trust boundaries. |
| Review | Record an applicable review of the current candidate with an identified reviewer. |

Labels stay English with en/es living documentation. Status is **Pending,
Running, Waiting, Done, Failed, Skipped, Blocked or Interrupted**. Done and Waiting
are not extra phases. Applicability is proportional: a token report does not
implement application code or require an independent review. Skipping a phase
needs a reason. Security Done describes the named checks and their scope; it is
not a security certification. The onboarding inspection covers managed paths and
the installed permission policy, not application vulnerabilities.

## Display and configuration

Global/project registration adds a local status line and execution hooks.
Installation preserves custom status commands and hooks. Conflicting bar values
are proposed in `.aikya/visibility-proposed.json` (or the global
`~/.claude/visibility-proposed.json`); activation requires review. User commands
are never concatenated into a shell pipeline. Existing permission and REQ gates
remain authoritative even when visibility is unavailable.

Optional subagent rows require a supporting client. Enable them during registration
with `aikya_setup.py --scope project --subagent-statusline` or the global equivalent.
The adapter follows the official JSON-lines row contract. Missing actor models
stay N/D; the main model is never assigned to a child. Supporting fields are
capability-dependent; a client version alone does not prove account access.

For a text fallback, use the CLI beside the resolved Aikya runtime:

```sh
python3 .aikya/runtime/aikya_cli.py status --target . --session <session-id> --execution-details
```

The compact bar shows the active command/phase/status, observed main model or a
local Python executor, activity and metrics. Details include all phases, reasons,
actors and the run/revision. No phase-position percentage is fabricated. Task
counts only refer to a real worklist.

## Sources and uncertainty

| Display | Source and limits |
|---|---|
| Model | Runtime `model.id` or a resolved model on that actor's task row. Configured/inherit is not observation. Local Python checks have no model. |
| Context % | Runtime `context_window.used_percentage`; a window occupancy, not accumulated session usage. |
| Session tokens | Explicitly selected session transcripts, deduplicated by message identity and streaming maxima. N/D until an aggregate is supplied; coverage excludes unprovided child transcripts. |
| Account 5h / 7d % | Optional `rate_limits` runtime windows with future reset times. Account scope, not this project or command. |
| Local budget % | Only a developer-supplied token denominator, separately labeled. |

Missing data stays **N/D**, distinct from a measured zero. Expired account windows
are removed; old snapshots are flagged. No quotas are inferred from token counts,
prices, plan names or model policy. No credentials or private endpoints are used.
The status-line renderer does not rescan transcripts or call a model/API.

Refresh a recorded session aggregate outside that frequent render path:

```sh
python3 aikya/scripts/harness/token_report.py --path <authorized-transcript-path> --session-id <session-id> --root . --cache-session
```

Include only authorized files for this project. For a project interval, use
`--start-utc <inclusive-ISO>` and `--end-utc <exclusive-ISO>`; a seven-day aggregate
is not an account weekly allowance. `--budget-tokens N` opts into a local budget.
Input, output and both cache categories remain separate in JSON. Missing usage or
timestamps yield partial coverage. Session-cache updates use an unfiltered session
aggregate; interval reports do not replace the all-session display.

## Explicit transitions and failure handling

Use the observer alongside the resolved CLI. Hooks recognize anchored invocations,
correlate nested skills, and record actor start/stop metadata. Pass the real
`session_id` and returned `run_id`; separate worktrees and sessions have isolated
caches. Direct CLI runs can use `--session`; shell environment inference is only a
fallback. An init/analyze preview never creates project documentation.

```sh
python3 <runtime>/execution_observer.py status --root . --session <session-id>
python3 <runtime>/execution_observer.py phase --root . --session <session-id> --run <run-id> --phase validate --status completed --generation <captured-generation> --input reviewed-evidence.json
```

The evidence file is an array of metadata, for example a process `kind`, check
name and actual `exit_code`, or an inspection `result=passed` and check scope.
Review also requires `kind=review`, `reviewer`, `result=passed` and the current
candidate SHA-256. Metadata is a caller's record, not a cryptographic attestation.
A tool exit or checklist cannot independently establish semantic correctness.

Failures and blocked required checks prevent successful closure. Re-entering
Explore/Plan/Implement invalidates affected later results while retaining history.
Each check/review binds to the candidate_generation observed at its start; use
`--generation N` for asynchronous completion. A result from before rework cannot
complete the new candidate. Concurrent actor completion cannot hide another actor
still running or failed.
Superseded invocation events are rejected. Interrupted sessions do not auto-close
successfully. Locks release on process exit; snapshots are atomically replaced.

Private, bounded cache files are outside the repository under the system temporary
folder by default (`AIKYA_EXECUTION_CACHE` can select another private location).
They contain phase metadata, observed models, check names/results and aggregate
usage, not prompts, source code, secrets or raw tool output. Useful reviewed change
results belong in the existing REQ audit and versioned ODD/SDD records, not one
Markdown document per display refresh. Delete only the selected cache directory
when no corresponding session is active to reset local visibility.

The field contracts come from the official
[Claude Code status-line documentation](https://code.claude.com/docs/en/statusline)
and [hook reference](https://code.claude.com/docs/en/hooks). These platform references
supply no documentation templates; Aikya reference collection remains the sole external template provider.

GENERATED BY AIKYA HARNESS
