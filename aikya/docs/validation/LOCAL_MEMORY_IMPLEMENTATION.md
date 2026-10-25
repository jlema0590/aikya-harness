# Local memory, automatic updates and HTML validation

Date: 2026-10-25.
Branch: `feat/automatic-local-memory`, created from fetched `origin/develop`
at `34ca30a53bbb04b61a8e243805bb5a4820b33c86`.

## Delivered behavior

- Project-local incremental SQLite declarations, source hashes and deterministic
  bounded retrieval. Python works without extra dependencies; reviewed optional
  grammars cover Java, JavaScript/JSX, TypeScript/TSX, C# and Go.
- One observer per worktree, project-local session leases, successful-write hints,
  external-change reconciliation and TTL-driven note eligibility updates.
- `/aikya-memory` is the 28th public command. Offline HTML and its matching Markdown
  report use the same verified publication. Explicit live clients share the
  observer and release only their own lease when closed.
- HTML graph, source hierarchy, inventory, search, type/folder filters, inspection,
  themes, reduced motion and preservation of filters/zoom/selection during updates.
- Existing reviewed notes, approvals, custom artifacts, hooks, scopes and adopted
  ignore files are preserved. No model, embedding service or external skill is
  invoked for maintenance. Assistant invocations/context remain separately billed
  according to their normal provider usage.

Implementation details and limits are in [local memory architecture](../architecture/local-memory.md).
The generated [HTML example](../examples/aikya-memory-generated.html) contains
23 nodes and 27 explicit relationships from a controlled fixture. Fifteen source
fingerprints were checked against the retained fixture under
`tests/fixtures/memory-viewer/aikya-java-validation/`. It is not a user application
or an observed runtime trace.

## Local environment and scope

Observed local platform: macOS 27.0.1 arm64, Python 3.13.2.
The default environment has no optional parser requirement. Pinned parser wheels
were separately installed into a temporary directory for language acceptance.
No user application environment, global memory store or provider credentials were
used for those checks.

Native GitHub jobs are configured for Linux, Windows and macOS with Python 3.10
and 3.13; existing regression jobs retain 3.10–3.13. Those remote jobs have not run
for this local branch. Authenticated model/Claude Code host-session validation
remains assigned to the developer's other environment. Local hooks were tested
with actual processes and controlled host-event payloads, not an authenticated
model session. No measured model-token-savings claim is made.

## Regression and command checks

The final complete run passed **593 tests**, with three environment-specific
skips, in **904.246 seconds**. It includes shared-client reuse and the final
HTML-safe JSON transport-budget regression. The focused viewer suite also passes
all 13 tests. The skipped optional-language checks were separately exercised
with the pinned grammar packages in the temporary parser environment.

New behavioral coverage is distributed across:

| Test file | Coverage |
|---|---|
| `tests/test_code_index.py` | Incremental replacement, unchanged generations, rename/delete/syntax errors, same metadata changes, scoped context, UTF-8 positions, ignores, secrets/symlinks, ownership, rollback and rotating byte budgets |
| `tests/test_code_index_languages.py` | Six language/dialect fixtures, invalid syntax, missing grammar fallback and project-module impersonation |
| `tests/test_memory_viewer.py` | Matching artifacts, read-only preview, reviewed/unreviewed/expired notes, hostile document text, source limits, protected custom outputs, interrupted publication recovery and byte limits after HTML-safe JSON escaping |
| `tests/test_memory_watch.py` | Real external edits, atomic saves, rename/delete, restart, no self-export loop, singleton ownership, policy disable and expiry without source edits |
| `tests/test_memory_live.py` | Actual loopback responses, latest publication, capability/Host/origin/path restrictions and mismatched reports |
| `tests/test_memory_integration.py` | Public CLI, copied runtimes, approved onboarding, source-scoped loop context, real local phases, disabled export policy and shared observer/client leases |

The existing executable command battery now exercises `/aikya-memory` alongside
the other 27 commands, including read-only preview and incompatible-option failure.
Source Agent Skills/subagent metadata and the 120-template catalog both validate.

## Distribution

The final wheel and source distribution build successfully without isolation.
The isolated-wheel smoke test covers eight combinations:
`global`/`project` × `odd`/`sdd` × `init`/`analyze`. Each scenario exports a real
Python declaration through its copied runtime and verifies its HTML/report.
All eight scenarios passed again for the final rebuilt wheel, including the
client-lease correction and transport-budget guard, with no SDK installed.
The final archive was also inspected for the canonical index entry point, client
module, viewer script and new public skill.

No release, tag or remote publication is created by this validation. `VERSION`
remains the existing 7.0.1 build identifier; feature changes are recorded under
Unreleased until a release is selected.

## Real-browser acceptance

Eighteen checks passed using an isolated Chromium browser against the actual
local server and generated offline files:

- Verified Java declarations, keyboard selection/focus, search and inventory.
- A newly saved class appears without manually reloading the live page.
- Selection survives declaration-position changes; type filter and zoom persist.
- Architecture view shows source hierarchy, with no inferred execution trace.
- Motion can be disabled; reduced-motion removes transitions.
- No horizontal overflow at 390 × 844; desktop checked at 1560 × 1050.
- Exported HTML opens independently with `file://`.
- A 10,000-symbol snapshot respects the 500-node drawing cap and finds a late
  declaration; the fixture opens within the ten-second acceptance timeout.
- No page errors or external page traffic were observed.

The [desktop](../examples/aikya-memory-live-desktop.png) and
[mobile](../examples/aikya-memory-live-mobile.png) captures are retained.
The shared-client integration test also opens the real loopback server through a
stubbed OS browser launcher, verifies Spanish UI selection, checks the observer
PID stays unchanged and confirms closing the client preserves the host session.

## Measured local performance

Controlled Python fixtures contain the stated number of class/method declarations,
split into modules. These measurements are local observations, not cross-platform
latency guarantees or authenticated model measurements.

| Symbols | Initial sync | Unchanged sync | Parsers on unchanged sync | HTML export | HTML bytes |
|---|---|---|---|---|---|
| 100 | 0.0101 s | 0.0027 s | 0 | 0.0130 s | 157,671 |
| 1,000 | 0.0557 s | 0.0060 s | 0 | 0.0480 s | 1,028,714 |
| 10,000 | 0.5028 s | 0.0433 s | 0 | 0.4475 s | 10,083,177 |

Hashes may read source bytes locally; zero unchanged parsers does not mean zero
disk inspection. No model was invoked by these indexing/export benchmarks.

## Source quality and boundaries

The changed-source gate reports **zero errors and zero duplicate groups**. Four
cohesion warnings remain: existing/extended CLI dispatch, task-loop coordinator,
installation preview, and the new multi-source snapshot coordinator (127 lines).
They are review diagnostics, not exceptions to the 1,000-line source-file limit.
No source-size exception was added.

Java/Spring resolved request flows, Maven/Gradle semantic resolution, LSP and the
later language cohorts remain separate roadmap work. The illustrative earlier
Java preview retains its illustration label. External-skill preset retirement
has its own reviewed plan and is not coupled to this observer implementation.
Existing private-memory functionality remains available through its explicit API;
the HTML viewer only inspects project notes.

GENERATED BY AIKYA HARNESS
