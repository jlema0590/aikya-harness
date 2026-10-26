# Optional agent loop validation

> Historical acceptance evidence. Original results and baselines are preserved; this is not a new execution report.

Date: 2026-10-23. Version: 6.1.1. Base: 0d99950.
Implementation remains local on feat/sdd-spec-coding-templates; no push or release.

## Delivered behavior

An explicit --agent-loop option routes feature, bugfix and implement through a
bounded sequential controller. The separately installed Claude Agent SDK owns its
agent/tool loop; Aikya checks ODD/SDD readiness, scoped files, validation/Security
argv, read-only review and task closure. Normal onboarding does not start a loop
and normal installation does not import or install the SDK.

Checkpoints preserve iteration/time/cost limits, session accounting, candidate
fingerprints and effect intent/result pairs. Uncertain queries cannot be retried
for free. The authoritative JSON checkpoint precedes its Markdown projection;
a known prior managed projection can be recovered, while custom reports remain
protected. Project memories are explicit typed Markdown references with TTL,
source fingerprints and a total lexical recall budget.

## Verification evidence

| Check | Result |
|---|---|
| Full unittest suite, Python 3.10 | 452 tests, OK. |
| Full unittest suite, Python 3.11 | 452 tests, OK. |
| Full unittest suite, Python 3.12 | 452 tests, OK. |
| Full unittest suite, Python 3.13 | 452 tests, OK. |
| New regression methods | 39; includes the 12-case project-type × methodology × locale matrix and hostile input subcases. |
| SDK options/callback characterization | Installed claude-agent-sdk 0.2.173; actual option construction, scoped hooks, acknowledgement IDs, internal StructuredOutput formatting, denied shell, read-only review and explicit settings sources. No model call. |
| Upgrade from actual 0d99950 source | Global/project registration and project initialization; optional modules, requirements and guide available, 27 commands retained, customized CLAUDE.md preserved. |
| Agent/skill assets | 30 agents, 29 engineering skills, 27 public commands; metadata valid. |
| Pinned documentation catalog | 120 templates, 155 reference files; checksums valid. |
| Example profiles | 14/14 plan successfully without external execution. |
| Static instruction proxy | 2,566 against 6,000; not measured billable tokens. |
| Release contract | 6.1.1 retained; no tag. |

The full suite contains deliberate negative-test diagnostics and the preexisting
non-failing ResourceWarning in project_discovery.py. Final unittest results above
are OK. Synthetic worker costs are fixtures, not real provider usage or bills.

## Attempts to break the controller

- Model claims completion while process checks fail: task stays unfinished;
  unchanged unsuccessful candidates stop after two attempts.
- Path traversal, absolute context escapes, secret/control files, symlinks,
  readonly commands, unknown options, Boolean/nonnumeric/non-finite limits:
  rejected before an executor starts.
- Denied child tools, malformed/flooded protocol, process crash, timeout and user
  interruption: stop without accepting a model success claim.
- Descendant process writes after its parent times out: the process group is
  terminated, and the marker is not written.
- Two callers race the same task: only one completes; the other detects changed
  task state after acquiring the project lock.
- Missing SDK and required usage: blocked; missing usage is never treated as zero.
- Duplicate/conflicting result IDs and cumulative resumed-session totals: no
  double charging; malformed usage cannot partially mutate the durable ledger.
- Exhausted iteration/cost/time budgets: resume does not reset them. An unfinished
  effect requires reconciliation instead of replay.
- Changed task/context/approvals, source mutation during checks/review or between
  completion intent and task commit: no accepted completion with stale evidence.
- Another checkout, customized summary, altered evidence and checkpoint symlinks:
  rejected or require review; user data is preserved.
- Interrupted state/summary publication: the authoritative state can still be
  loaded and its managed projection rewritten without accepting a custom report.
- Expired, stale, cross-project or malformed project memory: excluded. Recall
  stays within the total character budget and notes never grant task approval.

## Independent review and corrections

One bounded independent read-only review reproduced two P1 defects, both fixed
with failing regressions before the correction:

1. Candidate mutation after the pending completion checkpoint could close the
   task against older evidence. Completion now rechecks the candidate and approval
   bindings at the task commit boundary and rejects stale work.
2. Writing the summary before its state could make crash recovery permanently
   fail. State is now authoritative and stores the current/prior managed summary
   hashes; an interrupted projection remains recoverable without clobbering custom
   content.

Additional adversarial regressions fixed a late approval check, non-finite memory
creation time, partial ledger updates, unknown SDK hook IDs, missing installed
guidance, user interruption and the SDK-owned StructuredOutput formatter being
mistaken for an unauthorized effectful tool.

## Live acceptance boundary

The user chose to execute the real Claude test in another environment. No model,
provider account or API billing was exercised here. The local SDK contract checks
are not an end-to-end authenticated run. The opt-in live smoke is prepared:

```bash
python scripts/ci/agent_loop_smoke.py --live --approved --max-cost-usd 0.25 --timeout-seconds 120
```

Use an environment with the optional SDK and supported Claude authentication.
Configured hooks require separate inspection before --approve-configured-hooks.
The script works on an isolated synthetic project; it never deploys or installs
SDKs. Report its actual result before treating provider behavior as validated.

Application policy checks are not an OS sandbox or protection against a hostile
local user rewriting code/state. Receipts are not cryptographic signatures, cost
caps use provider/client estimates and can overshoot an in-flight request, and a
completed task is not full SDD requirement verification or a security certificate.

## Gentle Shell comparison

The static comparison and adoption plan are separate requested artifacts, based on
Gentle Shell commit 05065e7a0437d13eb158191681ce672319b9a8e0. No Gentle Shell
code, postinstall, dependencies, runtime or test suite was executed or integrated.
The proposed next stages remain pending.

GENERATED BY AIKYA HARNESS
