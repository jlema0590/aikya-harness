# Global command reuse and workspace policy validation — 7.2.2

## Scope

Branch fix/global-commands-no-worktrees starts at develop 7ac1ef9 (7.2.1).
The implementation preserves project policies, Memory and existing runtimes while
avoiding duplicate public command copies when the global installation verifies.
Tests use disposable homes/projects. No actual user registration was reconciled,
no worktree was created, no model was called and no release was published.

## Reproduction and focused checks

Initial executable tests reproduced duplicate registration and onboarding, then
verified both use the global commands after correction. Upgrade testing exposed loss
of old provenance during bundle replacement; preflight now retains that provenance.
A legacy wrapper could not retire without a local replacement; retirement now accepts
the verified global replacement. Analyze preview incorrectly described new local
command writes; it now reports reuse, managed backups or preserved review conflicts.

The command-scope battery checks local-only fallback, mixed scopes, selected-project
upgrade/backup, customized and extended folders, unrelated-project preservation,
missing global provenance, legacy aliases and read-only preview. Additional protection
cases cover conflicting backups and symlinked commands before any retirement.

The workspace battery checks recognized Git/Claude creation, Agent/Task isolation,
EnterWorktree, ordinary edits, branch creation and read-only queries. The installed
adapter runs outside the source checkout; custom hooks/settings and repeat registration
remain intact. The hook requests native host permission and supplies no blanket allow.

## Packaging and command evidence

- Built wheel and source distribution successfully for 7.2.2.
- Installed-wheel acceptance passed 11 cases, including global/project reuse, independent
  local/global registrations, mobile hook/phase and ODD/SDD init/analyze. No source
  checkout imports or Claude SDK dependency were used.
- Clean macOS installer passed global and project registration/update, ODD initialization,
  SDD analysis, startup, uninstall and preservation of referenced project interpreters
  and user documents/settings. This run used default dependency-free parser selection;
  it did not rerun optional parser provisioning.
- Offline public-command acceptance passed all 28 commands and 52 subprocess checks,
  including expected denials. This validates executable support contracts; it does not
  claim that a model completed every workflow.
- Agent/skill metadata and asset checks passed: 30 agents, 29 engineering skills and
  28 public commands. The offline documentation catalog validated 120 templates.
- Release contract accepts VERSION 7.2.2 / tag v7.2.2 and the changelog increment
  against origin/develop. No release tag was created.

## Full regression and focused corrections

The isolated full run executed 704 tests in 1,054.802 seconds: 700 passed, two
skipped and two failed on outdated test expectations. One template test assumed
global setup must be followed by a redundant local runtime. Its standalone scope
fixtures now have separate homes; mixed registration is tested separately. The other
test expected two PreToolUse hook groups and now needs three. It also verifies
unique hook commands and exactly one workspace guard after repeat registration.

After those fixture-only corrections, the complete affected modules passed:

| Battery | Tests | Result |
|---|---:|---|
| Command scopes and data protection | 13 | Passed |
| Workspace policy | 3 | Passed |
| Documentation templates | 12 | Passed |
| Startup and v5 compatibility | 12 | Passed |

The two new backup/symlink protection cases were added after full-suite discovery
and are included in the 13-case focused run. No implementation source changed after
the full run began. The entire 704-case run was not repeated after the fixture-only
adjustments; the two failing modules were rerun completely and have no remaining
observed failures.

The two skips were dependency-free parser fallback (the test interpreter has the
optional grammars) and a native PowerShell executable unavailable on this machine.
The full run includes successful optional-parser tests and both extensive onboarding
matrices (new/existing, development/infrastructure/DevOps, ODD/SDD, en/es, global/local).
Native Windows execution and an interactive Claude permission prompt remain separate.

## Review limits and rollout

Source quality has no errors. Its existing installation_preview long-function warning
remains (137 lines after the focused extraction); the new modules are below the
1,000-line limit. Exact diagnostics and artifact hashes are in the [JSON receipt](2026-11-05-global-command-workspace-policy.json).

Windows/Linux and alternate Python executions are configured in native installer CI
but were not executed on this macOS machine. Live Claude command-discovery refresh and
the actual permission prompt still need real-host confirmation. Recognition is best
effort and does not sandbox arbitrary encoded scripts, external terminals or other
tool paths. No provider-token or account-quota savings are claimed.

After publication, update global Aikya and reconcile each affected project through
reviewed aikya-setup --scope project --target <project>, or approved
/aikya-analyze --refresh using the updated command. Restart Claude if discovery is
cached. Customized command folders remain for explicit review and can still appear
in both scopes until resolved. Global update does not scan all projects.
The earlier pending uninstall-skills plan is preserved separately.

## PR #30 CI follow-up

The first PR checks at 7d5ce56 exposed two environment-sensitive expectations beyond
the original local validation. All four native Windows versions (Python 3.10–3.13)
failed the legacy-alias fixture; Ubuntu/macOS installer jobs and Linux distro jobs
passed. Windows clean install/update completed successfully before the fixture check.
Python 3.11 and 3.13 full-suite jobs failed only the stale installer hook count;
their 706-case runs had seven skips each. Other initial unit jobs were still running
when this correction was prepared.

A real Git CRLF checkout reproduced fixture corruption locally before the attribute
fix (one test failed, then passed). Resolving the macOS temporary root reproduced the
same installer 3 != 4 assertion seen on Linux. The replacement assertions verify
unchanged settings on repeat installation, preservation of the user hook/permissions,
unique commands and one workspace guard. No migration hash or runtime guard changed.

Focused verification passed 33 tests: checkout conversion (1), installer (12) and
command acceptance/renames/scopes (20). The command-acceptance case executes all
28 public command support contracts. A fresh complete isolated regression and native
CI reruns were pending when this corrective commit was prepared; their outcome is
available in the PR checks. Do not treat this record as an all-green CI claim.

See [bug details](../bugs/2026-11-05-pr30-ci-regressions.md) and the
[initial installer run](https://github.com/jlema0590/aikya-harness/actions/runs/42044602558)
and [Python run](https://github.com/jlema0590/aikya-harness/actions/runs/42044602707).

GENERATED BY AIKYA HARNESS
