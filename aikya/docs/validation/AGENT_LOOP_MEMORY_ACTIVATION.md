# Agent Loop and Memory Activation Audit

Date: 2026-10-25. Audited source: `de512aa6066d7e75232c62c485f267681b2c48a1`; repository VERSION 7.0.1. This audit validates repository behavior; it does not identify which version or Python interpreter was used in the developer's external test environment.

Follow-up: the developer authorized the worker correction after this audit. The original findings below describe the audited revision; see [correction validation](AGENT_WORKER_STARTUP_FIX.md) for the subsequent implementation and startup coverage. Registered/initialized runtimes retaining their copied adapter were not subject to the source/wheel missing-file failure.

## Findings

| Observation | Verified behavior |
|---|---|
| The Aikya agent loop does not start automatically | Intentional. Only feature, bugfix and implement support the explicit loop route; init/analyze reject loop activation. Command instructions require an explicit user request. |
| Enabling the loop requires more than installing Aikya | Verified. The selected interpreter needs the optional SDK, approved ODD/SDD task context and reviewed JSON with scoped files, validation/security checks and turn/time/cost limits. The clean installer deliberately creates a dependency-free base environment without the SDK. |
| Manual SDK execution can still fail | Confirmed default-worker startup defect: `ProcessRuntime` resolves a root adapter that no longer exists in either the checkout or wheel. See the [bug record](../bugs/2026-10-25-agent-loop-worker-launch.md). |
| Memory is not learned from every interaction | Verified. Direct approved notes and pending proposals are explicit operations. Optional model extraction is also an explicitly approved invocation and only publishes pending candidates. |
| Saved notes are not injected into all slash commands | Verified. In-repository automatic prompt injection occurs inside the optional task loop only; session discovery and visibility hooks do not call the knowledge recall engine. Direct recall is available separately. |
| Even a running loop may ignore saved notes | Verified. `memory_budget_chars` defaults to **0**; a positive budget enables recall. The default scope is project only; private scope must be selected explicitly. |
| Existing memory can be used automatically after configuration | Verified within the loop. With a positive budget, each implementation iteration retrieves relevant approved, current, unexpired notes under one total character budget. Individual recall calls need not be issued manually. |

These are Aikya's bounded SDK loop and reviewed reference memories. This audit does not evaluate the host's own conversation/tool execution or host-managed memory.

## Reproductions and fresh checks

- `python -m unittest discover -s tests -p 'test_agent_loop*.py' -q`: **36 passed** in 18.895 seconds.
- `python -m unittest discover -s tests -p 'test_*memory*.py' -q`: **18 passed** in 1.850 seconds.
- Direct default-worker `check`: missing selected file and exit 2 in the source checkout and in an independently installed local 7.0.1 wheel. No model or SDK installation was required.
- Three full local fixture loops captured their actual implementation request context. All completed their reviewed task:

| Controlled case | Effective character budget | Note in implementation prompt |
|---|---:|---|
| Approved relevant note; budget omitted | 0 | No |
| Approved relevant note; recall enabled | 4000 | Yes |
| Pending relevant note; recall enabled | 4000 | No |

The local fixture is a controlled subprocess, not a provider/model call. Passing these tests does not establish default-worker startup or authenticated SDK acceptance.

## Memory eligibility and storage

Project notes live in `aikya/docs/memory/`; private notes default to the external per-project store under `~/.aikya/memory/`. `MEMORY.md` indexes notes and grants no approvals. The recall engine checks review state, checkout identity, source fingerprint, TTL, lexical relevance and selected scopes. It selects at most five unique notes under the total character budget. Therefore, a note can remain on disk while being correctly excluded from context.

`aikya/docs/loops/<run-id>/` contains loop state, summary and accepted evidence; these records do not automatically become reference memories. Execution visibility, workflow continuity, conversation context and reviewed memory are separate mechanisms.

## Recommended order

1. Repair the confirmed default-worker entry point and add missing source/wheel startup coverage before attempting automatic activation.
2. Clarify optional SDK/interpreter setup and expose useful preflight reasons, including missing SDK, invalid task/configuration and broken worker startup.
3. If automatic behavior is desired, design an explicit project-level policy for loop activation and reviewed-memory retrieval. Automatic reading of approved reference notes can be considered separately from creating, approving or disclosing new notes. Such a policy is a proposed enhancement, not a currently implemented option.

No production code, installed user environment, release version or remote branch was changed by this audit. Native authenticated Claude execution remains untested here.

GENERATED BY AIKYA HARNESS
