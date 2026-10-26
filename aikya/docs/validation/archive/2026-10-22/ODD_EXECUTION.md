# ODD and execution visibility validation

> Historical acceptance evidence. Original results and baselines are preserved; this is not a new execution report.

Date: 2026-10-23. Version: 6.1.1. Base reviewed: c419faa.
Implementation is local on feat/sdd-spec-coding-templates; no publication is part
of this change. Product instructions are English; living documentation remains en/es.

## Automated evidence

| Check | Result |
|---|---|
| Full regression suite, Python 3.10–3.13 | 407 tests per interpreter; all pass. |
| Onboarding matrix | 48 cases: three project types × ODD/SDD × en/es × global/project × new/existing. |
| Public command protocol | All 28 commands have recipes and scoped fixture execution-state coverage. These are not 28 real LLM task executions. |
| Previous-version upgrades | Six known predecessors upgraded and reinstalled; existing CLAUDE.md and SDD state bytes retained. |
| Installed SDD lifecycle | Six isolated complete lifecycles: development/infrastructure/DevOps × en/es. |
| Milkeles library | 120 templates, 155 reference files; pinned commit and checksums valid. |
| Agent/skill contracts | 30 engineering agents, 29 engineering skills, 28 Aikya commands; metadata valid. |
| Profile smoke | 14/14 example profiles plan successfully without external execution. |
| Static context | 2,566 proxy tokens for template against the existing 6,000 limit; not measured model tokens. |
| Release contract | 6.1.1 retained; no release tag created. |

Reproduce the main suite with `python3 -B -m unittest discover -s tests`.
New coverage lives in test_methodology_migration.py, test_odd_engine.py,
test_execution_state.py, test_execution_ui.py, test_execution_integration.py,
test_odd_observability_integration.py and test_runtime_metrics.py.
CI retains Python 3.10–3.13 and compiles the new runtime modules.

## Acceptance mapping

| Requirement | Evidence |
|---|---|
| AC-01 / AC-02 / AC-13 | Initial choice, legacy standard/missing-field migration, preserved technical decisions, profile/answers backups, SDD retained, unsafe backup preflight. |
| AC-03 / AC-04 / AC-11 | All registered recipes; phase/status separation, read-only previews, compact/narrow/details output. |
| AC-05 / AC-06 | Observed actor model versus configured/inherit; Python has no model; context, recorded tokens and provider windows remain distinct. |
| AC-07 | Streaming maxima, repeated/rotated messages, session and interval filters, missing timestamp/usage coverage and explicit local budgets. |
| AC-08 | Session/worktree isolation, optimistic revisions, duplicate/late events, prompt identity, interruption, atomic writes and process-owned locks. |
| AC-09 | Cache-only adapters and display; no network, credentials, OAuth or LLM invocation in these modules. |
| AC-10 | Customized bars/hooks and unknown coupled runtime assets preserved; SDD gates and locale retained; exact footer and actual-file index. |
| AC-12 | Security success requires scoped successful evidence; missing/failed checks prevent closure; rework invalidates prior checks. |

## Independent review

One independent read-only review found two P2 defects. Both were reproduced with
regression tests and corrected:

- A delayed check could complete Validate after Implement changed the candidate.
  Candidate generations now bind asynchronous results; the quality recorder uses
  distinct check actors and rejects completion from the old generation. Regressions:
  test_old_check_completion_cannot_validate_a_changed_candidate and
  test_quality_completion_after_rework_cannot_certify_the_new_candidate.
- Compact output could attribute the main model to a reviewer or local process.
  It now selects the active phase actor; missing child models stay N/D and Python
  remains a local executor. Regression:
  test_compact_uses_the_active_actor_model_and_never_assigns_main_to_python.

The final full suite was repeated after these corrections. Focused renderer tests
were repeated on all four interpreters after the final live-main-model refresh
adjustment. Additional regressions cover fresh-checkout ODD locks and preservation
of complete preexisting skill instructions.

## Boundaries of the evidence

Runtime field fixtures follow the published Claude Code status-line and hook
contracts. They include missing, zero, expired and invalid data, plus multiple
actors. They are synthetic contract fixtures, not captured billing/account data.
The actual bar and optional subagent rows have not been exercised inside a live
Claude Code session here. A real client/account smoke remains a rollout check;
missing provider fields are valid N/D results, never grounds to inspect credentials.

Recorded session totals update only from developer-authorized transcript paths;
no unrelated projects are scanned and the renderer does not rescan history.
Unprovided subagent transcripts remain outside coverage. Provider quota fields
are optional and are never estimated from token logs or prices. Local interval
reports and budgets are implemented separately and labeled by their own scope.
No phase-level token attribution or automatic provider billing measurement is claimed.

The onboarding Security inspection checks managed paths and the installed .env
permission policy. It does not scan the application or certify it as secure.
Recorded evidence does not mean the ODD/SDD recorder independently executed tests.
The synthetic lookup example contains two assertions actually run outside the recorder.

No SDK installation, deployment, remote write, push or extra model call is needed
to render the status line. This validation reports no provider bill or equivalent
human implementation time.

GENERATED BY AIKYA HARNESS
