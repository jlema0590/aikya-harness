# Installer size and documentation path audit

Date: 2026-10-23. Source baseline: 40bce205969fb71e8436c2e85777212a9e18893c.
This records a read-only runtime investigation and its planning documents. A later
document-only cleanup relocates ten external-workflow artifacts and removes their
former namespace; see [cleanup evidence](../validation/DOCUMENT_WORKFLOW_CLEANUP.md).
The installer refactor, runtime path enforcement and broader guide migration remain
pending.

## Requirements and boundaries

Split install.py by responsibility while preserving public interfaces, approval
boundaries, dry-run, custom files and existing project structures. Store new
first-party generated plans, research and validation reports under aikya/docs/.
Use aikya/docs/plan/ (singular) for general implementation plans. Existing SDD
plan.md stays within its authoritative SPEC dossier; do not create a competing plan.
Keep root README, CHANGELOG, LICENSE, SECURITY, AGENTS and CLAUDE contracts, technical
instruction assets and pinned third-party templates at their functional locations.
Private memory remains in its explicitly selected external store.

## Verified installer size

install.py contains 1,309 physical lines and 28 top-level functions. The install
function spans lines 828–1171: 344 lines, with 76 If nodes and 13 For nodes.
The file began at 654 lines in the earliest available history and first exceeded
1,000 at commit 96b2016, which introduced selectable Development, Infrastructure
and DevOps initialization modes. Later additions include localization, SDD,
documentation migrations and ODD/visibility. It did not grow in the memory/quality
commit 40bce20.

| Responsibility | Function-span lines |
|---|---:|
| Installation coordinator | 344 |
| Interview helpers and interviews | 149 |
| Profile validation | 64 |
| Technical context and EN/ES bootstrap rendering | 181 |
| Migration, legacy documents and path checks | 129 |
| Manifest-based discovery and helpers | 67 |
| Project check construction | 81 |
| File writing and settings merge | 60 |
| CLI and bootstrap-only directory guard | 131 |

These spans total 1,206; imports, constants, spacing and entry-point statements
account for the remaining lines. Maintainability comes from explicit boundaries,
not removing whitespace or compressing statements.

## Locations and causes observed before the document-only cleanup

| Observed location | Verified cause |
|---|---|
| Repository docs/ | Tracked first-party guides, README image assets, research, validation and historical implementation plans. |
| Repository docs/plans/ | Seven tracked historical plans. Introduced by documentation and SDD implementation commits. |
| Repository docs/superpowers/plans/ | Five tracked implementation plans; the external writing-plans skill defaults to this location. Earlier assistant work used that default rather than the user's canonical location. |
| Workspace docs/superpowers/plans/ | Three SDD integration planning documents outside the Git checkout. They are authoring artifacts, not output from an installed Aikya command. |
| Repository plans/ or plan/ at root | Neither exists in this checkout. A root plans/ folder in another project has not been inspected. |
| Project .aikya/runtime/docs/ or global runtime docs/ | Bundled static runtime guides selected by aikya_setup.EXECUTION_FILES. These are runtime assets, not a root project documentation directory. |
| Initialized project aikya/scripts/harness/docs/ | The same bundled guides, inside the aikya tree. |

The external skill's default is documented at
/Users/jlema/.agents/skills/writing-plans/SKILL.md, line 16. No change to the
user's global skill is required or proposed. Repository instructions must override
that default for this project. This audit's new plans use the canonical directory.

## Clean-target reproduction

An offline temporary-project experiment ran the installed CLI for all 48 cases:
three project types × ODD/SDD × en/es × global/project registration × init/analyze.
All 48 exited successfully, produced aikya/docs/indice.md and created neither
root docs/ nor root plans/. External skill installation was disabled; no model,
SDK installation, infrastructure operation or application generator was invoked.

The evidence script and raw results are temporary investigation artifacts:
/tmp/aikya-doc-path-probe.py and /tmp/aikya-doc-path-audit.json. This matrix does
not exercise discretionary Markdown writes by a live model or an external skill.

## Legacy preservation and the enforcement gap

install.copy_legacy_docs (install.py:709) reads an already existing target/docs,
copies substantive Markdown into canonical paths and preserves the originals.
It returns immediately if source docs/ is absent; it does not create source docs/.
Therefore an existing docs tree can remain after installation intentionally.

Canonical Python writers use docs_layout.safe and write_document to write under
root/aikya/docs. The guard is weaker for arbitrary external writes:

- docs_guard.file_map records aikya/docs documents and recognized source paths;
  a root plans/aikya-probe.md does not match either condition.
- docs_guard.validate_ci returns success when no recognized source file changed,
  before checking an outside generated Markdown document.
- docs_layout.validate_layout examines the aikya/docs subtree only.

A temporary generated Markdown probe, ending with the exact Aikya footer, at
plans/aikya-probe.md was accepted by validate_ci and omitted from file_map.
The result is saved at /tmp/aikya-doc-guard-audit.json. This is a reproduced
validation gap, not evidence that the Python installer created that folder.

## Approved planning scope and acceptance targets

There are two independently deliverable workstreams:

1. [Installer modularization](../plan/2026-10-23-installer-modularization.md):
   preserve behavior while extracting responsibilities and packaging dependencies.
2. [Canonical document paths](../plan/2026-10-23-document-path-consolidation.md):
   correct authoring instructions, detect outside generated reports and migrate
   known historical artifacts through an inspectable mapping.

The initial deliverable wrote only plans and this audit. The separately requested
document-only cleanup subsequently relocates the ten external-workflow artifacts
and adds local authoring instructions. It leaves the external skill and runtime
code unchanged. The broader plans remain pending; no commit or push is included
in the cleanup.

GENERATED BY AIKYA HARNESS
