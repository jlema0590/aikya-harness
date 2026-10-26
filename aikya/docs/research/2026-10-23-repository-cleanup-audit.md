# Aikya repository cleanup audit

Date: 2026-10-23. Baseline: 19111a1e749d1d058000240c492e49e164abbb27.
Scope: all 823 tracked files at that commit, plus ignored local Python cache
metadata. No synced sources, other checkouts, private user stores or Git objects
were inspected. This audit writes evidence and a plan; candidate deletions have
not been applied.

[Per-file inventory and decisions](2026-10-23-repository-cleanup-inventory.json)
contains path, size, SHA-256, role, action, confidence and reference evidence for
all 823 baseline files. New audit artifacts are deliberately outside that baseline.

## Result

One tracked file is a high-confidence redundant removal candidate. A unique
unreferenced image needs archival review; a small prompt file records manual
provenance. Seven unlinked plans should be classified and archived rather than
silently erased. No complete executable Python module was established as dead.
Dynamic catalogs, manual CLIs, hook commands and distribution lists explain many
false positives from a simple import search.

| Baseline category | Files | Bytes |
|---|---:|---:|
| docs/ | 36 | 10,313,209 |
| Root contracts, modules and image | 64 | 1,730,397 |
| Pinned documentation templates | 157 | 1,451,551 |
| Examples | 335 | 436,763 |
| Tests and fixtures | 58 | 426,434 |
| Engineering catalog | 59 | 172,615 |
| Canonical Aikya documentation | 15 | 169,594 |
| Public command skills | 27 | 123,064 |
| Installed template assets | 36 | 97,410 |
| CI scripts | 8 | 36,179 |
| GitHub workflows/contracts | 12 | 26,033 |
| SDD role templates | 9 | 9,986 |
| Legacy migration sources | 3 | 3,214 |
| CLAUDE profile templates | 3 | 1,444 |
| Repository session configuration | 1 | 380 |
| **Total** | **823** | **14,998,273** |

## Concrete candidates

| Candidate | Recommended action | Evidence and boundary |
|---|---|---|
| Aikya-Harness.png, 1,057,227 bytes | Remove redundant root copy during cleanup | Byte-identical to docs/images/aikya-harness.png; both READMEs use the latter. No incoming tracked reference; the root image is not part of the runtime distribution inventory. |
| docs/images/trazabilidad-documental.png, 1,473,743 bytes | Archive or retire after preserving the unique asset | No tracked reference found; both READMEs use documentation-traceability-en.png. It remains a distinct user-generated graphic, not an exact duplicate. |
| docs/images/aikya-components.prompt.txt, 344 bytes | Archive manual image provenance | No executable consumer or link. It records the edit that updated the current component infographic and can help future maintenance. |
| docs/plans/, seven files, 22,070 bytes | Move into canonical indexed history/backlog | Zero incoming links and filename references. Some describe superseded template providers; MULTIPLATFORM_CODEX_COPILOT.md is an explicitly unimplemented future proposal, so preserve it as backlog. |
| docs/validation/, ten files, 39,882 bytes | Relocate evidence with provenance | Historical test/review results are audit material. Absence of an incoming link does not make that evidence disposable. |
| Ignored __pycache__/*.pyc, 318 files, 5,123,972 bytes at audit capture | Optional local cache purge after verification | Already ignored by Git and reproducible; a new Python run can recreate it. These bytes are not part of the branch or release archive. |

Removing the root duplicate saves 1.06 MB from the working tree and future source
archives. Removing both image candidates would save about 2.53 MB, but the second
is a unique artifact and is not classified as automatically disposable. Git
history is retained; these operations would not purge historical Git objects.

## Keep: active and compatibility assets

- Fifty of the 51 root Python modules are explicitly distributed through CORE_FILES;
  context_budget.py is the remaining CI tool. Check imports, CLI entry points and
  hooks together rather than treating no production import as proof of non-use.
- aikya_router.py is a standalone routing-preview CLI; agent_memory_extract.py is
  an explicit optional CLI; the subagent statusline is registered as a command
  string. These are examples of false positives from an import-only audit.
- All 30 engineering agents, 29 engineering skills, 27 public slash commands,
  nine SDD roles and three CLAUDE profile adapters have registry/template roles.
- Keep the 120 Milkeles templates and 155 reference files with their catalog and
  license. Explicit optional selection is valid use even when onboarding does not
  generate every template.
- Keep tests, manual SDK/live acceptance tools, legacy wrappers and the nine fixture
  files. The three migrations/v55/hooks files are read as predecessor byte signatures.
- Five ASSETS records retain the old command names and source paths after their
  source files were removed. command_retirement_plan reads their known hashes to
  recognize and back up old installed commands; these records are not dead assets.
- Root README/CHANGELOG/VERSION/LICENSE/SECURITY/contribution contracts and GitHub's
  location-discovered workflows and issue templates remain functional metadata.

Two small helpers have no runtime caller found: aikya_layout.module_root and
runtime_metrics.resolve_actor_model. The latter is exercised by tests and retained
in the historical design. Evaluate integration, compatibility and deprecation
within their owning refactors; do not delete either containing module.

## Duplicates and generated snapshots

Exact-byte comparison finds 13 groups: the root logo copy plus 12 repeated-output
patterns within different synthetic example scenarios. The example copies have
separate scenario paths and manifest entries; collapsing them would change the
example contract. Python AST diagnostics find three repeated bodies, all involving
historical regression fixtures, which must remain available to migration tests.

examples/documentation/generated/ contains 265 files and 379,588 bytes. The gallery
is linked from examples/documentation/README.md; all 253 checksummed Markdown entries
exist and match the manifest. It is explicitly labelled as a snapshot before the
standard-to-ODD transition. Its guide still contains the retired
/aikya-architecture-review command; current commands use /aikya-arc-review.
Archive or refresh the gallery coherently with its manifest and historical label;
do not mistake old snapshots for active command instructions or erase them merely
because they repeat generated text.

The registration copier currently ships 679 files (2,909,925 bytes), with no duplicate
destination paths. It copies the entire examples tree, including all 265 historical
gallery files: about 39% of entries and 13% of payload bytes. They are not required
for the tested runtime flows. A temporary in-memory distribution filter omitted
only that gallery and passed eight installed development scenarios: ODD/SDD ×
global/project × init/analyze, with no repository code changes or model calls.
This supports a lean-runtime proposal while retaining the gallery in the source
repository. Before shipping that packaging change, expand acceptance to all project
types/locales and update any runtime-local reference that expects the gallery.

## Document integrity diagnostics

The local-link scan finds three unresolved sample destinations:

1. Two Milkeles template links contain illustrative ADR filenames. Preserve pinned
   upstream bytes and checksums; substitute real data only when rendering project
   documents. These are template examples, not missing runtime modules.
2. The historical gallery's standard/summary.md points at fixture-evidence.log from
   its original synthetic project. The gallery already declares that it is not an
   executable project. Include real synthetic evidence or explain that link when
   refreshing the gallery; do not fabricate executed application checks.

Seventy-one raw first-party Markdown assets do not end with the current footer.
Fifty-nine are engineering source assets that receive the footer through the
existing asset_bytes installation wrapper. The other twelve are historical/root
contracts and example guides. This is a normalization review, not evidence of
unused files; never rewrite the pinned upstream library to satisfy a broad rule.

The source-size audit still reports install.py at 1,309 lines. Its dedicated
[modularization plan](../plan/2026-10-23-installer-modularization.md) remains the
appropriate refactor; deleting supporting modules would make that problem worse.
The broader [document consolidation plan](../plan/2026-10-23-document-path-consolidation.md)
handles guide/image relocation separately from deletion decisions.

## Verified checks and limits

- Full unittest discovery: 472 tests OK with Python 3.13, 95.704 seconds. The
  preexisting non-failing project_discovery ResourceWarning remains visible.
- Assets/frontmatter: 30 agents, 29 engineering skills and 27 commands valid.
- Pinned catalog: 120 templates, 155 reference files and checksums valid.
- Gallery: 253 manifest Markdown entries, zero missing files or hash mismatches.
- Registration inventory: 679 entries, zero destination collisions.
- Lean-gallery distribution experiment: eight of eight installed scenarios pass.
- Example-profile smoke: 14 of 14 pass. Release contract: 6.1.1, no tag.
- Source quality: 138 inspected files; one known size error (install.py) and
  three expected fixture clone groups. This check is not reported as globally green.

Static reference evidence cannot prove every possible externally invoked Python
API is unused. No provider calls, dependency downloads, cloud operations, tracked
file removals or ignored-cache deletions were performed. The
[cleanup execution plan](../plan/2026-10-23-repository-cleanup.md) separates safe
removal, historical organization and runtime payload optimization.

GENERATED BY AIKYA HARNESS
