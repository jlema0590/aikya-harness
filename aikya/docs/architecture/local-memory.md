# Local code memory and the HTML viewer

## Scope

Aikya maintains a regenerable per-project/worktree code index and a read-only HTML
projection of that index, reviewed project notes and project documentation. The
index/exporter/observer do not call a model, create embeddings, run project code
or send data to a remote memory service. They use local CPU, RAM and disk. Later
assistant invocations and selected AI context retain their normal token usage.

Python declarations use the standard-library AST. The optional pinned
`code-index` package extra adds Java, JavaScript/JSX, TypeScript/TSX, C# and Go.
Only the reviewed package versions are loaded; missing/incompatible grammars
retain `file_only` inventory. Aikya never downloads or compiles them itself.
Install the optional extra explicitly into the same interpreter selected for
Aikya, using a build that includes this feature and binary wheels where available.
Other languages, runtime-created objects, resolved call graphs, Spring bindings,
Maven dependency resolution, LSP and observed request traces are outside this
delivery. A folder hierarchy is not evidence of a runtime architecture or flow.

## Commands

```text
/aikya-memory
/aikya-memory --refresh --open
/aikya-memory --watch
/aikya-memory --watch --open
/aikya-memory --dry-run
```

The package equivalent is `python -B -m aikya memory --target <project>` with the
same options and optional `--docs-lang en|es` / `--session <id>`. Copied runtimes
use their existing generated `aikya_cli.py` entry point with the selected Python.
No new source-root adapter is required.

In watch mode, `--docs-lang` selects the live client's interface language. The
shared background observer keeps automatic HTML/Markdown artifacts in the
project's configured documentation language. One-shot exports can use an
explicit language override without changing project policy.

- Default: export current notes/documents and the available index generation.
- `--refresh`: synchronize the already-enabled index before export. It cannot
  enable a disabled policy or approve/rewrite a note.
- `--watch`: keep a local observer running until interrupted. It regenerates the
  offline report and stops on interruption or a disabled watch policy.
- `--watch --open`: also open a temporary `127.0.0.1` live viewer. The browser
  requests a new snapshot when publication changes; filters, selection, zoom and
  expanded directories survive updates when their source still exists.
- `--open` without watch: open the exported `file://` snapshot. A tab already
  holding this file needs reload to see a later export.
- `--dry-run`: preview sources/destinations without documents, cache, browser,
  listener or execution-state writes. Incompatible with refresh/watch/open.

Exit status is 0 for complete/preview, 4 for a useful partial export and 2 for an
error. Inspect coverage and omissions before assuming all declarations exist.
English execution phases report actual local operations; no model is inferred.

## Project policy and lifecycle

Approved `/aikya-init` and `/aikya-analyze` install `.aikya/code-index.json`:

```json
{
  "schema": 1,
  "generated_by": "aikya-code-index",
  "enabled": true,
  "max_files": 12000,
  "max_file_bytes": 1048576,
  "max_sync_bytes": 104857600,
  "watch": true,
  "auto_export": true,
  "scope": "."
}
```

`enabled` controls code indexing; `watch` controls automatic observation;
`auto_export` controls automatic HTML regeneration. These switches do not approve
notes or expand task permissions. `scope` retains the selected component for a
first scoped adoption. Existing reviewed policy is preserved; change it explicitly
to alter scope. Limits can be reduced, not increased beyond supported bounds.

SessionStart/UserPromptSubmit/successful-write hooks maintain project-local leases
and start one session-owned observer. SessionEnd releases its lease; observation
stops after the last session ends. A lease expires after six hours without a host
event to bound abandoned processes. Use explicit `--watch` for long standalone
editor sessions. No OS service, login task or scheduled job is installed. Native
host event delivery must still be verified in the actual host environment.

Explicit watch clients acquire their own project-local lease and reuse the same
background observer. Closing a viewer releases only that client's lease; an
active host or another explicit client keeps observation running. A standalone
client renews its lease every 30 seconds and stops the observer when it closes
if no other session remains. The observer acquires its singleton lock before its
initial indexing/export work.

The observer checks eligible metadata every two seconds, groups changes for
750 ms with a three-second maximum batching delay, and verifies content on a
change. A full hash reconciliation runs on startup and at least every 60 seconds,
within per-batch limits, to catch edits preserving file size/timestamps. Deferred
batches rotate fairly; partial coverage is explicit. Query results independently
verify the selected source hashes before returning context.

Stopped observers cannot see edits. Restart reconciles changes made offline.
Parse errors remove old current declarations; deleted/renamed paths lose their
old locations. TTL transitions can refresh note eligibility without file edits.
The status reports `Updating`, `Up to date`, `Partial` or `Stopped`; a disconnected
live browser shows `Disconnected`. Verification time defines freshness.

## Storage and publication

| Path | Responsibility |
|---|---|
| `.aikya/code-index.json` | Reviewed local policy |
| `.harness/state/code-index/index.sqlite` | Derived declarations and file hashes; checkout-bound |
| `.harness/state/code-index/dirty.json` | Bounded write hint, not a second index |
| `.harness/state/memory-view/` | Local leases, observer status and publication ownership/recovery |
| `aikya/docs/memory/<id>.md` | Existing reviewed notes; observer never edits their bodies/review state |
| `aikya/docs/memory/view/index.html` | Regenerable offline HTML, embedded data/styles/scripts |
| `aikya/docs/memory/view/report.md` | Auditable coverage, generation and matching HTML SHA-256 |

An export publishes one confirmed index generation and validated source hashes.
The report follows the matching HTML; a bounded local intent permits recovery
after an interrupted publication. A live request refuses a mismatched pair.
Custom HTML/report/policy or changed owned artifacts are preserved for review.
Unchanged projections do not rewrite HTML/report files.

Viewer outputs and `aikya/docs/indice.md` are excluded as collection inputs and
watch triggers to avoid self-generated loops. The index document still lists the
actual Markdown report. No commits, pushes or publication occur automatically.

New-project initialization adds precise ignore patterns. Existing-project adoption
preserves the current ignore file; add the following if local cache/HTML should
be excluded from version control and they are not already ignored:

```gitignore
.harness/state/
aikya/docs/memory/view/index.html
```

The HTML includes eligible project knowledge; apply the project's sharing policy
before sharing it. Private/global notes, transcripts, credentials, ignored inputs,
symlinks, nested Git roots and external paths are excluded from this projection.

## Bounds and correctness

Index limits: 12,000 eligible files, 1 MiB per source, 100 MiB per synchronization
batch. Queries return at most 20 matches within a default 6,000-character context
budget, with a 16,000-character ceiling, and respect the agent loop's file allowlist.
An unavailable index does not broaden scope or prevent ordinary file tools.

Viewer limits: 5,000 notes/documents each, 1 MiB per document, 100 MiB of collected
source/document input and a separate cumulative 100 MiB note/source-inspection
budget, 50,000 nodes, 200,000 edges and 20 MiB serialized UTF-8 data.
The graph draws at most 500 nodes; inventory pages contain 100 entries. A smaller
useful projection reports its limits. Pending/rejected/expired notes remain
inspectable with their original review state; inspection does not make them
eligible for recall. Changed/missing sources invalidate eligibility.

The static export has no network connections, CDN or external library. Live mode
only serves allowlisted read-only routes on loopback with a random per-session
capability, Host/origin checks, no open CORS and no credential persistence in the
export. Source content is rendered as text, with escaped embedded JSON and hashed
CSP. Graph relations represent explicit syntax/paths/links, not inferred execution.

Internal maintenance commands:

```text
python -B -m aikya.code_index status --root <project>
python -B -m aikya.code_index sync --root <project>
python -B -m aikya.code_index query --root <project> --query UserService --allowed-file src/service.py
python -B -m aikya.code_index clear --root <project> --approved
```

Stop the observer before clearing a cache. Clearing validates cache ownership and
preserves policy and reviewed notes; custom/corrupt databases require review.

## Executable example

Generated reports use the approved version 2 Java preview's navy theme by default,
independently of OS appearance, with an explicit light/dark theme action. The
three-column layout contains a source overview/tree, central explorer and source
inspector. Blue files, peach declarations, teal folders and gold documents/notes
use separate light-theme values. The graph shows bounded explicit relationships;
Architecture arranges source paths from parent to descendant. Inventory retains
100-entry pagination and search. No illustrated request flow is promoted to
execution evidence. Theme selection is local to the open page and survives live
snapshot refreshes; it is not written into project policy.

The [generated HTML fixture](../examples/aikya-memory-generated.html) is produced
by the actual exporter, with 23 nodes and 27 explicit relationships. Its Java and
Python source fixture lives under `tests/fixtures/memory-viewer/aikya-java-validation/`.
It demonstrates declarations and paths, not an analyzed user application or
successful runtime tests. The [desktop](../examples/aikya-memory-live-desktop.png)
and [mobile](../examples/aikya-memory-live-mobile.png) captures show the real live viewer.

GENERATED BY AIKYA HARNESS
